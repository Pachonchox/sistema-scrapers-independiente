#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
📦 Product Processor - Sistema de Procesamiento Directo Scraper→DB
===================================================================

Procesa productos desde scrapers directamente a la base de datos,
con deduplicación automática y backup opcional en Excel.

Características:
- Inserción directa a PostgreSQL
- Deduplicación por SKU único
- Cache en memoria para sesión
- Backup automático en Excel
- Gestión de precios con lógica diaria
- Batch processing para optimización

Autor: Sistema Optimizado V5
Fecha: Diciembre 2024
"""

import os
import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
try:
    import psycopg2
    from psycopg2.extras import execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None
    execute_values = None
import json
from pathlib import Path

from .sku_generator import SKUGenerator
try:
    from .price_manager import PriceManager
except ImportError:
    # Fallback si no está disponible
    class PriceManager:
        def __init__(self): pass

# Integración con sistema de alertas
try:
    from ..alerts_bridge import send_price_change_alert
    ALERTS_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Sistema de alertas disponible")
except ImportError:
    try:
        from alerts_bridge import send_price_change_alert
        ALERTS_AVAILABLE = True
        logger = logging.getLogger(__name__)
        logger.info("✅ Sistema de alertas disponible (import directo)")
    except ImportError:
        ALERTS_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.warning("⚠️ Sistema de alertas no disponible - funcionando sin alertas")
        def should_update_price(self, fecha): return True
        def get_price_record_date(self): 
            from datetime import date
            return date.today()

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """📊 Estadísticas de procesamiento con protección anti-N/A"""
    products_processed: int = 0
    products_inserted: int = 0
    products_updated: int = 0
    prices_inserted: int = 0
    prices_updated: int = 0
    duplicates_found: int = 0
    invalid_products_rejected: int = 0  # 🛡️ NUEVA: Productos N/A rechazados
    errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    
    def get_summary(self) -> Dict:
        """Obtiene resumen de estadísticas con protección anti-N/A"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            'products_processed': self.products_processed,
            'products_inserted': self.products_inserted,
            'products_updated': self.products_updated,
            'prices_inserted': self.prices_inserted,
            'prices_updated': self.prices_updated,
            'duplicates_found': self.duplicates_found,
            'invalid_products_rejected': self.invalid_products_rejected,  # 🛡️ NUEVA
            'errors_count': len(self.errors),
            'elapsed_seconds': elapsed,
            'products_per_second': self.products_processed / elapsed if elapsed > 0 else 0,
            'rejection_rate': (self.invalid_products_rejected / (self.products_processed + self.invalid_products_rejected) * 100) if (self.products_processed + self.invalid_products_rejected) > 0 else 0  # 🛡️ NUEVA
        }


class ProductProcessor:
    """📦 Procesador principal de productos con inserción directa a DB"""
    
    def __init__(self, 
                 db_config: Optional[Dict] = None,
                 enable_excel_backup: bool = True,
                 batch_size: int = 100):
        """
        Inicializa el procesador
        
        Args:
            db_config: Configuración de base de datos
            enable_excel_backup: Habilitar backup en Excel
            batch_size: Tamaño del batch para procesamiento
        """
        # Configuración DB
        self.db_config = db_config or self._get_default_db_config()
        self.conn = None
        self.cursor = None
        self._connect_db()
        
        # Componentes
        self.sku_generator = SKUGenerator(enable_cache=True)
        self.price_manager = PriceManager()
        
        # Cache de sesión
        self.sku_cache = {}  # sku -> existe en DB
        self.product_batch = []
        self.price_batch = []
        
        # Excel backup
        self.enable_excel_backup = enable_excel_backup
        self.excel_buffer = []
        self.excel_output_dir = Path("data/excel_backup")
        self.excel_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración
        self.batch_size = batch_size
        
        # Estadísticas
        self.stats = ProcessingStats()
        
        logger.info("📦 Product Processor inicializado")
        logger.info("🛡️ Protección anti-N/A ACTIVADA - Productos basura serán rechazados automáticamente")
    
    def _get_default_db_config(self) -> Dict:
        """Obtiene configuración por defecto de DB"""
        return {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5434'),
            'database': os.getenv('PGDATABASE', 'price_orchestrator'),
            'user': os.getenv('PGUSER', 'orchestrator'),
            'password': os.getenv('PGPASSWORD', 'orchestrator_2025')
        }
    
    def _connect_db(self):
        """Conecta a la base de datos"""
        if not PSYCOPG2_AVAILABLE:
            logger.warning("⚠️ psycopg2 no disponible - modo mock")
            self.conn = None
            self.cursor = None
            return
            
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info("✅ Conectado a PostgreSQL")
        except Exception as e:
            logger.warning(f"⚠️ Error conectando a DB, usando modo mock: {e}")
            self.conn = None
            self.cursor = None
    
    def process_product(self, product_data: Dict, retailer: str) -> Optional[str]:
        """
        Procesa un producto individual con validación anti-N/A
        
        Args:
            product_data: Datos del producto (desde scraper)
            retailer: Nombre del retailer
            
        Returns:
            SKU único generado o None si hay error o datos inválidos
        """
        try:
            # 🛡️ PROTECCIÓN CONTRA PRODUCTOS N/A
            if not self._validate_product_data(product_data, retailer):
                return None
            
            # Generar SKU único
            sku = self.sku_generator.generate_sku(product_data, retailer)
            
            # Agregar a batch
            self.product_batch.append((sku, product_data, retailer))
            
            # Procesar batch si está lleno
            if len(self.product_batch) >= self.batch_size:
                self.flush_batch()
            
            self.stats.products_processed += 1
            
            # Agregar a buffer Excel si está habilitado
            if self.enable_excel_backup:
                self._add_to_excel_buffer(sku, product_data, retailer)
            
            return sku
            
        except Exception as e:
            error_msg = f"Error procesando producto: {str(e)[:100]}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return None
    
    def _validate_product_data(self, product_data: Dict, retailer: str) -> bool:
        """
        🛡️ Validación anti-N/A y datos basura
        
        Args:
            product_data: Datos del producto
            retailer: Nombre del retailer
            
        Returns:
            True si el producto es válido, False si debe ser rechazado
        """
        try:
            # Obtener campos críticos
            nombre = product_data.get('nombre') or product_data.get('title', '')
            precio = product_data.get('precio', '')
            
            # VALIDACIÓN 1: Nombre no puede ser N/A, vacío o solo espacios
            if not nombre or str(nombre).strip().upper() in ['N/A', 'NA', 'NULL', 'NONE', '']:
                logger.debug(f"❌ {retailer}: Producto rechazado - nombre inválido: '{nombre}'")
                self.stats.invalid_products_rejected += 1
                return False
            
            # VALIDACIÓN 2: Nombre muy corto (probable error)
            if len(str(nombre).strip()) < 3:
                logger.debug(f"❌ {retailer}: Producto rechazado - nombre muy corto: '{nombre}'")
                self.stats.invalid_products_rejected += 1
                return False
            
            # VALIDACIÓN 3: Precio no puede ser N/A (al menos que no esté disponible)
            precio_str = str(precio).strip().upper()
            if precio_str in ['N/A', 'NA', 'NULL', 'NONE']:
                logger.debug(f"❌ {retailer}: Producto rechazado - precio N/A: '{nombre}' - precio: '{precio}'")
                self.stats.invalid_products_rejected += 1
                return False
            
            # VALIDACIÓN 4: Nombre con patrones de error comunes
            nombre_clean = str(nombre).strip().lower()
            error_patterns = [
                'error', 'undefined', 'null', 'empty',
                'producto sin nombre', 'sin título',
                'loading', 'cargando'
            ]
            
            if any(pattern in nombre_clean for pattern in error_patterns):
                logger.debug(f"❌ {retailer}: Producto rechazado - patrón de error: '{nombre}'")
                self.stats.invalid_products_rejected += 1
                return False
            
            # VALIDACIÓN 5: Campos precio numéricos válidos si existen
            if hasattr(product_data, 'current_price') and product_data.get('current_price') is not None:
                try:
                    precio_num = float(product_data.get('current_price', 0))
                    if precio_num < 0:
                        logger.debug(f"❌ {retailer}: Producto rechazado - precio negativo: '{nombre}' - precio: {precio_num}")
                        self.stats.invalid_products_rejected += 1
                        return False
                except (ValueError, TypeError):
                    # Si no se puede convertir, no es crítico, pero lo notamos
                    logger.debug(f"⚠️ {retailer}: Precio no numérico, pero permitido: '{nombre}' - precio: '{precio}'")
            
            # ✅ PRODUCTO VÁLIDO
            logger.debug(f"✅ {retailer}: Producto válido: '{nombre[:50]}...'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validando producto {retailer}: {e}")
            # En caso de error de validación, rechazar por seguridad
            return False
    
    async def flush_batch(self):
        """Procesa el batch actual de productos"""
        if not self.product_batch:
            return
        
        # Modo mock sin DB
        if self.conn is None:
            logger.info(f"💾 Modo mock: Procesando {len(self.product_batch)} productos")
            for sku, product_data, retailer in self.product_batch:
                self.stats.products_inserted += 1
            self.product_batch.clear()
            return
        
        try:
            # Separar nuevos vs existentes
            new_products = []
            existing_products = []
            
            for sku, product_data, retailer in self.product_batch:
                if self._check_product_exists(sku):
                    existing_products.append((sku, product_data, retailer))
                    self.stats.duplicates_found += 1
                else:
                    new_products.append((sku, product_data, retailer))
            
            # Insertar nuevos productos
            if new_products:
                self._insert_products_batch(new_products)
            
            # Actualizar productos existentes (solo fecha último visto)
            if existing_products:
                self._update_products_batch(existing_products)
            
            # Procesar todos los precios
            all_products = new_products + existing_products
            await self._process_prices_batch(all_products)
            
            # Commit
            self.conn.commit()
            
            # Limpiar batch
            self.product_batch.clear()
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            error_msg = f"Error en flush_batch: {str(e)}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    def _check_product_exists(self, sku: str) -> bool:
        """
        Verifica si un producto existe en DB (con cache)
        
        Args:
            sku: SKU único del producto
            
        Returns:
            True si existe, False si no
        """
        # Verificar cache primero
        if sku in self.sku_cache:
            return self.sku_cache[sku]
        
        # Consultar DB
        self.cursor.execute(
            "SELECT 1 FROM master_productos WHERE codigo_interno = %s",
            (sku,)
        )
        exists = self.cursor.fetchone() is not None
        
        # Guardar en cache
        self.sku_cache[sku] = exists
        
        return exists
    
    def _insert_products_batch(self, products: List[Tuple]):
        """
        Inserta batch de productos nuevos
        
        Args:
            products: Lista de tuplas (sku, product_data, retailer)
        """
        if not products:
            return
        
        insert_data = []
        
        for sku, product_data, retailer in products:
            # Extraer campos
            nombre = product_data.get('nombre') or product_data.get('title', '')
            marca = product_data.get('marca') or product_data.get('brand', '')
            link = product_data.get('link') or product_data.get('product_url', '')
            categoria = product_data.get('categoria') or product_data.get('category', 'general')
            
            # Extraer specs de additional_info si existe
            additional = product_data.get('additional_info', {})
            storage = additional.get('storage', product_data.get('storage', ''))
            ram = additional.get('ram', product_data.get('ram', ''))
            color = additional.get('color', product_data.get('color', ''))
            
            # Rating y reviews
            rating = product_data.get('rating', 0)
            reviews = product_data.get('reviews_count', 0)
            
            # SKU original del retailer
            sku_original = product_data.get('sku', '')
            
            insert_data.append((
                sku,  # codigo_interno (nuestro SKU único)
                sku_original,  # sku del retailer
                link,
                nombre,
                marca,
                categoria,
                retailer,
                storage,
                ram,
                color,
                float(rating) if rating else None,
                int(reviews) if reviews else 0,
                date.today(),  # fecha_primera_captura
                date.today(),  # fecha_ultima_actualizacion
                date.today(),  # ultimo_visto
                True  # activo
            ))
        
        # Inserción masiva
        query = """
            INSERT INTO master_productos (
                codigo_interno, sku, link, nombre, marca, categoria, retailer,
                storage, ram, color, rating, reviews_count,
                fecha_primera_captura, fecha_ultima_actualizacion, ultimo_visto, activo
            ) VALUES %s
            ON CONFLICT (codigo_interno) DO NOTHING
        """
        
        execute_values(
            self.cursor,
            query,
            insert_data,
            template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        
        inserted = self.cursor.rowcount
        self.stats.products_inserted += inserted
        
        # Actualizar cache
        for sku, _, _ in products:
            self.sku_cache[sku] = True
        
        logger.info(f"✅ Insertados {inserted} productos nuevos")
    
    def _update_products_batch(self, products: List[Tuple]):
        """
        Actualiza batch de productos existentes
        
        Args:
            products: Lista de tuplas (sku, product_data, retailer)
        """
        if not products:
            return
        
        # Solo actualizamos fecha de último visto y algunos campos que pueden cambiar
        update_data = []
        
        for sku, product_data, retailer in products:
            rating = product_data.get('rating', 0)
            reviews = product_data.get('reviews_count', 0)
            
            update_data.append((
                date.today(),  # ultimo_visto
                date.today(),  # fecha_ultima_actualizacion
                float(rating) if rating else None,
                int(reviews) if reviews else 0,
                sku  # WHERE codigo_interno
            ))
        
        # Actualización masiva
        query = """
            UPDATE master_productos
            SET ultimo_visto = %s,
                fecha_ultima_actualizacion = %s,
                rating = %s,
                reviews_count = %s
            WHERE codigo_interno = %s
        """
        
        self.cursor.executemany(query, update_data)
        updated = self.cursor.rowcount
        self.stats.products_updated += updated
        
        logger.debug(f"📝 Actualizados {updated} productos existentes")
    
    async def _process_prices_batch(self, products: List[Tuple]):
        """
        Procesa precios para un batch de productos
        
        Args:
            products: Lista de tuplas (sku, product_data, retailer)
        """
        if not products:
            return
        
        fecha_actual = self.price_manager.get_price_record_date()
        should_update = self.price_manager.should_update_price(fecha_actual)
        
        # Preparar datos de precios
        price_data = []
        
        for sku, product_data, retailer in products:
            # Extraer precios RAW
            precio_original = int(product_data.get('original_price', 0) or 
                                 product_data.get('precio_normal', 0) or 0)
            precio_actual = int(product_data.get('current_price', 0) or 
                               product_data.get('precio_oferta', 0) or 0)
            precio_tarjeta_raw = int(product_data.get('card_price', 0) or 
                                    product_data.get('precio_tarjeta', 0) or 0)
            
            # 🔧 CORREGIR LOGICA PARA CONSTRAINT: precio_oferta <= precio_normal
            # Determinar cual es el precio normal (más alto) y la oferta (más bajo)
            if precio_original > 0 and precio_actual > 0:
                if precio_actual <= precio_original:
                    # Caso normal: precio actual es menor (descuento real)
                    precio_normal = precio_original
                    precio_oferta = precio_actual
                else:
                    # Caso problemático: precio actual > precio original
                    # Usamos el más alto como normal, el más bajo como oferta
                    precio_normal = precio_actual  # El más alto
                    precio_oferta = precio_original  # El más bajo
            elif precio_original > 0:
                # Solo precio original disponible
                precio_normal = precio_original
                precio_oferta = None
            elif precio_actual > 0:
                # Solo precio actual disponible
                precio_normal = precio_actual
                precio_oferta = None
            else:
                # Ningún precio válido
                precio_normal = 0
                precio_oferta = None
            
            # Convertir 0 a NULL para constraint de DB
            precio_oferta = precio_oferta if precio_oferta and precio_oferta > 0 else None
            precio_tarjeta = precio_tarjeta_raw if precio_tarjeta_raw > 0 else None
            
            # Al menos un precio debe ser válido
            if precio_normal or precio_oferta or precio_tarjeta:
                # Calcular precio mínimo (solo precios válidos > 0)
                precios_validos = []
                if precio_normal > 0:
                    precios_validos.append(precio_normal)
                if precio_oferta and precio_oferta > 0:
                    precios_validos.append(precio_oferta)
                if precio_tarjeta and precio_tarjeta > 0:
                    precios_validos.append(precio_tarjeta)
                
                precio_min = min(precios_validos) if precios_validos else precio_normal
                
                price_data.append((
                    sku,
                    fecha_actual,
                    retailer,
                    precio_normal,
                    precio_oferta,
                    precio_tarjeta,
                    precio_min,
                    datetime.now()  # timestamp_creacion
                ))
        
        if not price_data:
            return
        
        # Insertar o actualizar precios según lógica diaria
        if should_update:
            # Intentar actualizar primero
            for data in price_data:
                sku, fecha, retailer, p_normal, p_oferta, p_tarjeta, p_min, timestamp = data
                
                # Verificar si ya existe precio de hoy
                self.cursor.execute("""
                    SELECT precio_normal, precio_oferta, precio_tarjeta
                    FROM master_precios
                    WHERE codigo_interno = %s AND fecha = %s
                """, (sku, fecha))
                
                existing = self.cursor.fetchone()
                
                if existing:
                    # Existe precio de hoy - actualizar solo si cambió
                    if (existing[0] != p_normal or 
                        existing[1] != p_oferta or 
                        existing[2] != p_tarjeta):
                        
                        self.cursor.execute("""
                            UPDATE master_precios
                            SET precio_normal = %s,
                                precio_oferta = %s,
                                precio_tarjeta = %s,
                                precio_min_dia = %s,
                                timestamp_ultima_actualizacion = %s
                            WHERE codigo_interno = %s AND fecha = %s
                        """, (p_normal, p_oferta, p_tarjeta, p_min, timestamp, sku, fecha))
                        
                        if self.cursor.rowcount > 0:
                            self.stats.prices_updated += 1
                            
                            # 📢 Enviar alerta de cambio de precio
                            if ALERTS_AVAILABLE:
                                await self._send_price_change_alert(
                                    sku, product_data.get('name', ''), retailer,
                                    existing, (p_normal, p_oferta, p_tarjeta)
                                )
                else:
                    # No existe precio de hoy - insertar
                    self.cursor.execute("""
                        INSERT INTO master_precios (
                            codigo_interno, fecha, retailer, precio_normal,
                            precio_oferta, precio_tarjeta, precio_min_dia,
                            timestamp_creacion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (sku, fecha, retailer, p_normal, p_oferta, p_tarjeta, p_min, timestamp))
                    
                    if self.cursor.rowcount > 0:
                        self.stats.prices_inserted += 1
        else:
            # Después de las 23:00 - no actualizar precios de hoy
            logger.info("⏰ Después de las 23:00 - precios en modo histórico")
    
    def _add_to_excel_buffer(self, sku: str, product_data: Dict, retailer: str):
        """
        Agrega producto al buffer de Excel
        
        Args:
            sku: SKU único generado
            product_data: Datos del producto
            retailer: Nombre del retailer
        """
        # Preparar registro para Excel
        excel_record = {
            'sku_unico': sku,
            'retailer': retailer,
            'nombre': product_data.get('nombre') or product_data.get('title', ''),
            'marca': product_data.get('marca') or product_data.get('brand', ''),
            'sku_original': product_data.get('sku', ''),
            'link': product_data.get('link') or product_data.get('product_url', ''),
            'precio_normal': product_data.get('original_price', 0),
            'precio_oferta': product_data.get('current_price', 0),
            'precio_tarjeta': product_data.get('card_price', 0),
            'rating': product_data.get('rating', 0),
            'reviews': product_data.get('reviews_count', 0),
            'timestamp': datetime.now()
        }
        
        # Agregar specs si existen
        additional = product_data.get('additional_info', {})
        excel_record.update({
            'storage': additional.get('storage', ''),
            'ram': additional.get('ram', ''),
            'color': additional.get('color', '')
        })
        
        self.excel_buffer.append(excel_record)
        
        # Flush si buffer está lleno
        if len(self.excel_buffer) >= 1000:
            self.flush_excel_backup()
    
    def flush_excel_backup(self):
        """Guarda buffer de Excel a archivo"""
        if not self.excel_buffer:
            return
        
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if PANDAS_AVAILABLE:
                # Usar pandas si está disponible
                import pandas as pd
                df = pd.DataFrame(self.excel_buffer)
                filename = self.excel_output_dir / f"backup_{timestamp}.xlsx"
                df.to_excel(filename, index=False, engine='openpyxl')
            else:
                # Fallback a CSV
                import csv
                filename = self.excel_output_dir / f"backup_{timestamp}.csv"
                
                if self.excel_buffer:
                    keys = self.excel_buffer[0].keys()
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=keys)
                        writer.writeheader()
                        writer.writerows(self.excel_buffer)
            
            logger.info(f"💾 Backup guardado: {filename} ({len(self.excel_buffer)} productos)")
            
            # Limpiar buffer
            self.excel_buffer.clear()
            
        except Exception as e:
            logger.error(f"❌ Error guardando backup: {e}")
    
    def finish_processing(self):
        """Finaliza el procesamiento y limpia recursos"""
        # Procesar batches pendientes
        self.flush_batch()
        
        # Guardar Excel pendiente
        if self.enable_excel_backup:
            self.flush_excel_backup()
        
        # Mostrar estadísticas
        stats = self.stats.get_summary()
        logger.info("=" * 70)
        logger.info("📊 RESUMEN DE PROCESAMIENTO")
        logger.info("=" * 70)
        logger.info(f"Productos procesados: {stats['products_processed']:,}")
        logger.info(f"Productos insertados: {stats['products_inserted']:,}")
        logger.info(f"Productos actualizados: {stats['products_updated']:,}")
        logger.info(f"Precios insertados: {stats['prices_inserted']:,}")
        logger.info(f"Precios actualizados: {stats['prices_updated']:,}")
        logger.info(f"Duplicados encontrados: {stats['duplicates_found']:,}")
        logger.info(f"Errores: {stats['errors_count']}")
        logger.info(f"Tiempo total: {stats['elapsed_seconds']:.1f} segundos")
        logger.info(f"Velocidad: {stats['products_per_second']:.1f} productos/segundo")
        
        # Estadísticas del generador SKU
        sku_stats = self.sku_generator.get_stats()
        logger.info("=" * 70)
        logger.info("🔑 ESTADÍSTICAS SKU")
        logger.info("=" * 70)
        logger.info(f"SKUs generados: {sku_stats['generated']:,}")
        logger.info(f"Cache hits: {sku_stats['cache_hits']:,}")
        logger.info(f"Cache hit rate: {sku_stats.get('cache_hit_rate', 0):.1f}%")
        logger.info(f"Colisiones verificadas: {sku_stats['collisions_checked']}")
    
    async def _send_price_change_alert(self, sku: str, nombre_producto: str, 
                                      retailer: str, precios_anteriores: tuple, 
                                      precios_nuevos: tuple):
        """
        📢 Enviar alerta de cambio de precio via Telegram
        
        Args:
            sku: SKU del producto
            nombre_producto: Nombre del producto
            retailer: Retailer
            precios_anteriores: (normal_anterior, oferta_anterior, tarjeta_anterior)
            precios_nuevos: (normal_nuevo, oferta_nuevo, tarjeta_nuevo)
        """
        try:
            # Determinar qué precio cambió más significativamente
            precio_anterior = None
            precio_nuevo = None
            tipo_precio = "oferta"  # Por defecto
            
            # Comparar precio de oferta (principal)
            if precios_anteriores[1] and precios_nuevos[1]:
                precio_anterior = precios_anteriores[1]
                precio_nuevo = precios_nuevos[1]
                tipo_precio = "oferta"
            # Si no hay oferta, usar precio normal
            elif precios_anteriores[0] and precios_nuevos[0]:
                precio_anterior = precios_anteriores[0]
                precio_nuevo = precios_nuevos[0]
                tipo_precio = "normal"
            # Si no hay normal, usar tarjeta
            elif precios_anteriores[2] and precios_nuevos[2]:
                precio_anterior = precios_anteriores[2]
                precio_nuevo = precios_nuevos[2]
                tipo_precio = "tarjeta"
            
            # Solo enviar alerta si hay cambio significativo
            if precio_anterior and precio_nuevo and precio_anterior != precio_nuevo:
                cambio_pct = ((precio_nuevo - precio_anterior) / precio_anterior) * 100
                
                # Solo alertar si el cambio es >= 5%
                if abs(cambio_pct) >= 5.0:
                    await send_price_change_alert(
                        codigo_interno=sku,
                        nombre_producto=nombre_producto,
                        retailer=retailer,
                        precio_anterior=precio_anterior,
                        precio_actual=precio_nuevo,
                        tipo_precio=tipo_precio
                    )
                    
                    logger.info(f"📢 Alerta enviada: {sku} {cambio_pct:+.1f}% ({retailer})")
                    
        except Exception as e:
            logger.debug(f"⚠️ Error enviando alerta para {sku}: {e}")

    def close(self):
        """Cierra conexiones y limpia recursos con resumen de protección anti-N/A"""
        self.finish_processing()
        
        # 🛡️ MOSTRAR RESUMEN DE PROTECCIÓN ANTI-N/A
        summary = self.stats.get_summary()
        if summary['invalid_products_rejected'] > 0:
            logger.info(f"🛡️ PROTECCIÓN ANTI-N/A: {summary['invalid_products_rejected']} productos basura rechazados")
            logger.info(f"🛡️ Tasa de rechazo: {summary['rejection_rate']:.1f}% del total")
        else:
            logger.info("🛡️ PROTECCIÓN ANTI-N/A: ✅ No se detectaron productos basura")
        
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        
        logger.info("🔒 Product Processor cerrado")


# Testing
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("📦 TESTING PRODUCT PROCESSOR")
    print("=" * 70)
    
    # Crear procesador
    processor = ProductProcessor(enable_excel_backup=True, batch_size=2)
    
    # Productos de prueba
    test_products = [
        {
            'product': {
                'title': 'iPhone 15 Pro 256GB',
                'brand': 'Apple',
                'sku': 'IPH15P256',
                'product_url': 'https://falabella.com/iphone-15-pro',
                'original_price': 1299990,
                'current_price': 1199990,
                'rating': 4.8,
                'reviews_count': 156,
                'additional_info': {
                    'storage': '256GB',
                    'color': 'Negro'
                }
            },
            'retailer': 'falabella'
        },
        {
            'product': {
                'title': 'Samsung Galaxy S24 Ultra',
                'brand': 'Samsung',
                'sku': 'SAMS24U512',
                'product_url': 'https://ripley.cl/samsung-galaxy-s24',
                'original_price': 1399990,
                'current_price': 1399990,
                'card_price': 1259990,
                'rating': 4.7,
                'reviews_count': 89,
                'additional_info': {
                    'storage': '512GB',
                    'ram': '12GB',
                    'color': 'Titanio'
                }
            },
            'retailer': 'ripley'
        },
        {
            'product': {
                'nombre': 'Notebook HP Pavilion 15',
                'marca': 'HP',
                'link': 'https://paris.cl/notebook-hp-pavilion',
                'precio_normal': 799990,
                'precio_oferta': 699990,
                'rating': 4.5,
                'reviews_count': 34
            },
            'retailer': 'paris'
        }
    ]
    
    print("\n📋 Procesando productos de prueba...\n")
    
    skus = []
    for i, test in enumerate(test_products, 1):
        print(f"Producto {i}: {test['product'].get('title') or test['product'].get('nombre')}")
        sku = processor.process_product(test['product'], test['retailer'])
        if sku:
            skus.append(sku)
            print(f"  ✅ SKU generado: {sku}")
        else:
            print(f"  ❌ Error procesando producto")
        print()
    
    # Finalizar procesamiento
    processor.finish_processing()
    
    # Cerrar
    processor.close()
    
    print("\n✅ Testing completado")