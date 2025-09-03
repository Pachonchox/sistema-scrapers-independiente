# -*- coding: utf-8 -*-
"""
OutputManager - Gestor de salida que mantiene formato Excel/CSV exacto
Compatible 100% con el sistema actual
"""

import pandas as pd
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
import os

logger = logging.getLogger(__name__)

class OutputManager:
    """
    Gestor de salida de datos
    
    Mantiene exactamente el mismo formato que los scrapers actuales
    para garantizar compatibilidad total con DataLoader
    """
    
    def __init__(self, config: Any):
        """Inicializar output manager"""
        self.config = config
        self.excel_path = config.output_path
        self.csv_path = config.csv_path
        # Opcional: salidas portables/analíticas
        self.parquet_enabled = str(os.getenv('OUTPUT_PARQUET', '0')).lower() in ('1', 'true', 'yes')
        self.duckdb_enabled = str(os.getenv('OUTPUT_DUCKDB', '0')).lower() in ('1', 'true', 'yes')
        self.parquet_path = Path(os.getenv('PARQUET_PATH', str((self.config.data_path / 'parquet').resolve())))
        self.duckdb_path = Path(os.getenv('DUCKDB_PATH', str((self.config.data_path / 'warehouse_master.duckdb').resolve())))
        # Política de exclusión: reacondicionados/refurbished
        self.exclude_refurbished = str(os.getenv('EXCLUDE_REFURBISHED', '1')).lower() in ('1', 'true', 'yes')
        
        # Asegurar que existan los directorios
        self.excel_path.mkdir(parents=True, exist_ok=True)
        self.csv_path.mkdir(parents=True, exist_ok=True)
        if self.parquet_enabled:
            self.parquet_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("OutputManager inicializado")
    
    def consolidate_results(self, results: List[Dict]) -> Dict:
        """
        Consolidar resultados de múltiples categorías
        
        Args:
            results: Lista de resultados por categoría
            
        Returns:
            Datos consolidados
        """
        all_products = []
        categories_processed = 0
        errors = []
        
        for result in results:
            if result.get('success'):
                products = result.get('products', [])
                all_products.extend(products)
                categories_processed += 1
            else:
                errors.append({
                    'category': result.get('category'),
                    'error': result.get('error')
                })
        
        # Filtro: excluir reacondicionados si está habilitado
        filtered_products = self._filter_refurbished(all_products) if self.exclude_refurbished else all_products

        # Eliminar duplicados manteniendo el formato
        unique_products = self._deduplicate_products(filtered_products)
        
        return {
            'products': unique_products,
            'total_products': len(unique_products),
            'categories_processed': categories_processed,
            'errors': errors
        }

    def _is_refurbished_text(self, text: str) -> bool:
        try:
            import re
            if not text:
                return False
            txt = str(text).lower()
            # Patrón amplio: 'reacond' (es/en), 'refurb', 'renewed', 'reparado' (cautela), 'remanufact'
            patterns = [
                r"reacond", r"refurb", r"renewed", r"remanufact", r"re-furb"
            ]
            return any(re.search(p, txt) for p in patterns)
        except Exception:
            return False

    def _filter_refurbished(self, products: List[Dict]) -> List[Dict]:
        if not products:
            return products
        kept = []
        dropped = 0
        for p in products:
            fields = [
                p.get('nombre'), p.get('title') or p.get('titulo'), p.get('descripcion'),
                p.get('link') or p.get('url')
            ]
            if any(self._is_refurbished_text(f or '') for f in fields):
                dropped += 1
                continue
            kept.append(p)
        if dropped:
            logger.info(f"Filtered refurbished items: {dropped} dropped, {len(kept)} kept")
        return kept
    
    def _deduplicate_products(self, products: List[Dict]) -> List[Dict]:
        """
        Eliminar duplicados basado en SKU
        
        Args:
            products: Lista de productos
            
        Returns:
            Lista sin duplicados
        """
        seen_skus = set()
        unique = []
        
        for product in products:
            sku = (product.get('sku') or '').strip()
            link = (product.get('link') or product.get('url') or '').strip()
            retailer = (product.get('retailer') or '').strip()

            if sku:
                key = f"sku::{sku}"
            elif link:
                key = f"link::{link}"
            else:
                # Fallback estable por retailer+título
                title = (product.get('title') or product.get('nombre') or '').strip()
                key = f"hash::{hashlib.md5((retailer + '|' + title).encode('utf-8', errors='ignore')).hexdigest()[:12]}"

            if key not in seen_skus:
                seen_skus.add(key)
                unique.append(product)
        
        return unique
    
    async def save_results(self, retailer: str, products: List[Dict]) -> Dict:
        """
        Guardar resultados en Excel y CSV
        
        IMPORTANTE: Mantiene exactamente el mismo formato que los scrapers actuales
        
        Args:
            retailer: Nombre del retailer
            products: Lista de productos
            
        Returns:
            Paths de archivos generados
        """
        if not products:
            logger.warning(f"No hay productos para guardar de {retailer}")
            return {}
        
        # Generar timestamp para nombre de archivo
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        
        # Crear DataFrame con el formato exacto esperado
        df = self._create_dataframe(products, retailer)
        
        # Validar formato antes de persistir
        try:
            ok = self.validate_output(df)
            if not ok:
                logger.warning("Validación de output falló; se guardará igualmente para diagnóstico")
        except Exception as e:
            logger.debug(f"Error validando output: {e}")

        # Guardar Excel
        excel_filename = f"{retailer}_{timestamp}.xlsx"
        excel_path = self.excel_path / excel_filename
        
        # Ejecutar operaciones bloqueantes en hilo aparte
        await asyncio.to_thread(df.to_excel, excel_path, index=False, engine='openpyxl')
        logger.info(f"Excel guardado: {excel_path}")
        
        # Guardar CSV
        csv_filename = f"{retailer}_{timestamp}.csv"
        csv_path = self.csv_path / csv_filename
        
        await asyncio.to_thread(df.to_csv, csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"CSV guardado: {csv_path}")

        result_paths: Dict[str, Any] = {
            'excel': str(excel_path),
            'csv': str(csv_path),
            'products_count': len(products)
        }

        # Opcional: Guardar Parquet y/o DuckDB (habilitar con env)
        try:
            if self.parquet_enabled:
                pq_path = await self._write_parquet(df, retailer, timestamp)
                if pq_path:
                    result_paths['parquet'] = str(pq_path)
        except Exception as e:
            logger.warning(f"Error guardando Parquet: {e}")

        try:
            if self.duckdb_enabled:
                rows = await self._write_duckdb(df, retailer)
                result_paths['duckdb_rows'] = rows
                result_paths['duckdb'] = str(self.duckdb_path)
        except Exception as e:
            logger.warning(f"Error escribiendo en DuckDB: {e}")
        
        # 🆕 NUEVO: Trigger normalización usando sistema V5 avanzado via adapter
        normalization_enabled = str(os.getenv('NORMALIZATION_ENABLED', 'false')).lower() in ('1', 'true', 'yes')
        if normalization_enabled:
            try:
                # Usar adapter que conecta con sistema V5 avanzado
                from ...utils.ml_adapters import NormalizationHubAdapter as NormalizationHub
                logger.info("🌟 Sistema de normalización V5 conectado via adapter")
            except ImportError:
                logger.warning("⚠️ Sistema de normalización no disponible - continuando sin normalización")
                normalization_enabled = False
            
            if normalization_enabled:
                try:
                
                # Preparar productos para normalización
                products_for_norm = []
                for product in products:
                    # Agregar retailer y timestamp si no están
                    product_copy = product.copy()
                    product_copy['retailer'] = retailer
                    product_copy['fecha_captura'] = datetime.now()
                    products_for_norm.append(product_copy)
                
                # Procesar con normalización
                hub = NormalizationHub()
                norm_results = await hub.process_batch(products_for_norm)
                
                # Guardar resultados en el response
                result_paths['normalization'] = {
                    'skus_generated': norm_results.get('skus_generated', 0),
                    'matches_found': norm_results.get('matches_found', 0),
                    'opportunities': len(norm_results.get('opportunities', [])),
                    'alerts': len(norm_results.get('alerts', []))
                }
                
                logger.info(
                    f"Normalización completada: "
                    f"{norm_results['skus_generated']} SKUs, "
                    f"{norm_results['matches_found']} matches, "
                    f"{len(norm_results.get('opportunities', []))} oportunidades"
                )
                
                # Cerrar conexiones del hub
                await hub.close()
                
            except Exception as e:
                logger.error(f"Error en normalización: {e}", exc_info=True)
                # No fallar el proceso principal si normalización falla
                result_paths['normalization_error'] = str(e)

        return result_paths
    
    def _create_dataframe(self, products: List[Dict], retailer: str) -> pd.DataFrame:
        """
        Crear DataFrame con formato exacto del sistema actual
        
        CRÍTICO: Este formato debe ser idéntico al actual para DataLoader
        Los scrapers v3 ahora generan los mismos campos que los originales
        """
        # Estructura exacta que espera DataLoader
        data = []
        
        import re
        def clean_title(t: str) -> str:
            if not t:
                return ''
            try:
                txt = str(t)
                txt = re.sub(r"(?i)env[íi]o\s+gratis(\s+app)?", " ", txt)
                txt = re.sub(r"(?i)agregar\s+al\s+carro", " ", txt)
                txt = re.sub(r"(?i)por\s+[^$\n]+", " ", txt)
                txt = re.sub(r"\s+", " ", txt)
                return txt.strip()
            except Exception:
                return str(t)

        for product in products:
            # Los scrapers ahora generan campos con los nombres originales
            # precio_normal_num, precio_oferta_num, precio_tarjeta_num
            # PERO también generan normal_num para compatibilidad
            normal_num = product.get('precio_normal_num', product.get('normal_num', 0))
            oferta_num = product.get('precio_oferta_num', product.get('oferta_num', 0))
            tarjeta_num = product.get('precio_tarjeta_num', product.get('tarjeta_num', 0))
            plp_num = product.get('precio_plp_num', 0)
            
            # Usar precio_min_num si existe, sino calcularlo
            if 'precio_min_num' in product:
                precio_principal = product['precio_min_num'] or 0
            else:
                prices = [p for p in [normal_num, oferta_num, tarjeta_num, plp_num] if p > 0]
                precio_principal = min(prices) if prices else 0
            
            row = {
                # Campos principales - ahora usando los nombres originales
                'sku': product.get('sku', ''),
                'nombre': clean_title(product.get('nombre', '')),
                'titulo': clean_title(product.get('nombre', '')),
                'marca': str(product.get('brand', '') or ''),
                'precio': precio_principal,
                
                # Precios texto
                'precio_normal': product.get('precio_normal', ''),
                'precio_oferta': product.get('precio_oferta', ''),
                'precio_tarjeta': product.get('precio_tarjeta', ''),
                'precio_plp': product.get('precio_plp', ''),
                
                # Precios numéricos 
                'precio_normal_num': normal_num,
                'precio_oferta_num': oferta_num,
                'precio_tarjeta_num': tarjeta_num,
                'precio_plp_num': plp_num,
                'precio_min_num': product.get('precio_min_num'),
                'tipo_precio_min': product.get('tipo_precio_min', ''),
                
                # Para retrocompatibilidad con formato anterior
                'normal_num': normal_num,
                'oferta_num': oferta_num,
                'tarjeta_num': tarjeta_num,
                
                # URLs e imágenes
                'link': product.get('link', ''),
                'url': product.get('link', ''),  # Duplicar para compatibilidad
                'imagen': product.get('image', ''),
                
                # Metadata
                'retailer': retailer,
                'categoria': product.get('category', ''),
                'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                # Campos adicionales que algunos scrapers incluyen
                'disponible': product.get('disponible', True),
                'descripcion': product.get('descripcion', ''),
                
                # Para compatibilidad
                'vendedor': product.get('vendedor', retailer),
                'envio': product.get('envio', ''),
                'rating': float(product.get('rating', 0)) if product.get('rating') else 0.0,
                'reviews': int(product.get('reviews', 0)) if product.get('reviews') else 0,
                # Extras MercadoLibre / extensibles
                'descuento_pct': product.get('descuento_pct', ''),
                'precio_anterior': product.get('precio_anterior', ''),
                'cuotas_texto': product.get('cuotas_texto', ''),
                'cuota_monto': product.get('cuota_monto', ''),
                'promocionado': product.get('promocionado', ''),
                'posicion': product.get('posicion', ''),
                'ml_item_id': product.get('ml_item_id', ''),
                'ml_product_id': product.get('ml_product_id', ''),
            }
            
            data.append(row)
        
        # Crear DataFrame con columnas en orden específico (como los scrapers originales)
        column_order = [
            'link', 'nombre', 'titulo', 'sku', 'precio',
            'precio_normal', 'precio_oferta', 'precio_tarjeta', 'precio_plp',
            'precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num', 'precio_plp_num',
            'precio_min_num', 'tipo_precio_min',
            # Retrocompatibilidad (duplicados numéricos)
            'normal_num', 'oferta_num', 'tarjeta_num',
            'marca', 'imagen', 'retailer', 'categoria',
            'fecha_captura', 'disponible', 'descripcion',
            'vendedor', 'envio', 'rating', 'reviews',
            # Extras opcionales
            'descuento_pct', 'precio_anterior', 'cuotas_texto', 'cuota_monto',
            'promocionado', 'posicion', 'ml_item_id', 'ml_product_id',
        ]
        
        df = pd.DataFrame(data)
        
        # Asegurar que todas las columnas existan
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        # Reordenar columnas
        df = df[column_order]
        
        # Limpiar valores NaN
        df = df.fillna('')
        
        # Convertir precios a int donde sea posible
        # Usar los nombres de columnas correctos del nuevo formato
        price_columns = ['precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num', 'precio_plp_num', 'precio_min_num']
        for col in price_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        return df

    async def _write_parquet(self, df: pd.DataFrame, retailer: str, timestamp: str) -> Optional[Path]:
        """Guardar resultados en formato Parquet particionado por retailer/fecha.

        No falla el flujo si pyarrow/fastparquet no están instalados: registra warning.
        """
        try:
            date_part = datetime.now().strftime('%Y-%m-%d')
            base = self.parquet_path / f"retailer={retailer}" / f"date={date_part}"
            base.mkdir(parents=True, exist_ok=True)

            dfp = df.copy()
            dfp['retailer'] = retailer
            dfp['export_ts'] = timestamp

            pq_file = base / f"{retailer}_{timestamp}.parquet"
            await asyncio.to_thread(dfp.to_parquet, pq_file, index=False)
            logger.info(f"Parquet guardado: {pq_file}")
            return pq_file
        except ImportError as e:
            logger.warning(f"pyarrow/fastparquet no disponible para Parquet: {e}")
            return None
        except Exception as e:
            logger.warning(f"Fallo guardando Parquet: {e}")
            return None

    async def _write_duckdb(self, df: pd.DataFrame, retailer: str) -> int:
        """Insertar resultados en archivo DuckDB local.

        Crea la base si no existe. Inserta todo el DataFrame.
        """
        try:
            import duckdb  # type: ignore
        except Exception as e:
            raise RuntimeError(f"DuckDB no disponible: {e}")

        dfd = df.copy()
        dfd['retailer'] = retailer
        dfd['ingest_ts'] = datetime.now().isoformat()

        rows = int(dfd.shape[0])

        def _insert():
            con = duckdb.connect(str(self.duckdb_path))
            try:
                con.register('df', dfd)
                con.execute("CREATE TABLE IF NOT EXISTS prices AS SELECT * FROM df WHERE 1=0;")
                con.execute("INSERT INTO prices SELECT * FROM df;")
            finally:
                con.close()

        await asyncio.to_thread(_insert)
        logger.info(f"DuckDB actualizado: {self.duckdb_path} (+{rows} filas)")
        return rows
    
    def validate_output(self, df: pd.DataFrame) -> bool:
        """Validar contra lo que espera el loader (Fase 2)."""
        loader_required = [
            'link', 'nombre', 'sku',
            'precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num', 'precio_plp_num',
            'precio_min_num', 'tipo_precio_min', 'marca', 'retailer', 'categoria', 'fecha_captura'
        ]
        missing = [c for c in loader_required if c not in df.columns]
        if missing:
            logger.error("Faltan columnas requeridas por loader: " + ", ".join(missing))
            return False

        if len(df) == 0:
            logger.error("DataFrame vacío")
            return False

        # Columnas opcionales útiles (no bloqueantes)
        optional_nice = ['titulo', 'precio', 'normal_num', 'oferta_num', 'tarjeta_num']
        for col in optional_nice:
            if col not in df.columns:
                logger.debug(f"Columna opcional ausente: {col}")

        return True
