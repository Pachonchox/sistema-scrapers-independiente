# -*- coding: utf-8 -*-
"""
Master Prices System
====================
Sistema de gestión del Master de Precios con snapshot diario inteligente.
Integrado con alertas automáticas para scraping 24/7.

Características:
- Snapshot diario: 1 registro por SKU por día
- Solo actualiza si precio cambia durante el día  
- Alertas automáticas integradas con Telegram
- Histórico completo para análisis min/max
- Cierre automático a medianoche
"""

import logging
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import pandas as pd
import duckdb
import asyncio
import json

# Importar sistemas usando adapters V5 (mantiene ML V5 avanzado)
try:
    from ..utils.ml_adapters import GlitchDetectionAdapter as GlitchDetectionSystem
    GLITCH_DETECTION_AVAILABLE = True
    logger.info("✅ Sistema de detección de anomalías V5 conectado via adapter")
except ImportError:
    GlitchDetectionSystem = None
    GLITCH_DETECTION_AVAILABLE = False
    logger.warning("⚠️ Sistema de detección no disponible")

# Importar sistema de alertas integrado
try:
    from .alerts_bridge import get_alerts_bridge, send_price_change_alert
    ALERTS_SYSTEM_AVAILABLE = True
    logger.info("✅ Sistema de alertas integrado disponible")
except ImportError:
    ALERTS_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Sistema de alertas no disponible")

# Mantener compatibilidad con configuración legacy
try:
    from .alerts_config import get_alerts_config, should_send_alert, get_price_threshold
    ALERTS_CONFIG_AVAILABLE = True
except ImportError:
    ALERTS_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DailyPriceSnapshot:
    """Snapshot diario de precios simplificado - Solo SKU interno + 3 precios + alertas básicas"""
    
    # === IDENTIFICADORES ===
    codigo_interno: str = ""    # SKU interno generado por Master Products
    fecha: date = field(default_factory=date.today)
    retailer: str = ""         # Fuente del precio
    
    # === LOS 3 PRECIOS REQUERIDOS ===
    precio_normal: int = 0     # Precio normal
    precio_oferta: int = 0     # Precio en oferta  
    precio_tarjeta: int = 0    # Precio con tarjeta
    
    # === CÁLCULOS PARA ALERTAS ===
    precio_min_dia: int = 0           # Mínimo de los 3 precios (calculado)
    precio_anterior_dia: int = 0      # Para comparar cambios
    cambio_porcentaje: float = 0.0    # % cambio vs día anterior
    cambio_absoluto: int = 0          # Cambio absoluto en pesos
    
    # === MÉTRICAS DE VOLATILIDAD ===
    volatilidad_dia: float = 0.0     # Volatilidad máxima del día
    cambios_en_dia: int = 0          # Contador de cambios en el día
    timestamp_ultima_actualizacion: datetime = field(default_factory=datetime.now)
    
    # === CONTROL DE ALERTAS ===
    alertas_enviadas: int = 0         # Contador para evitar spam
    
    def __post_init__(self):
        """Cálculos automáticos"""
        if self.precio_min_dia == 0:
            self.precio_min_dia = self._calculate_precio_min()
        
        if self.precio_anterior_dia > 0:
            self.cambio_absoluto = self.precio_min_dia - self.precio_anterior_dia
            if self.precio_anterior_dia > 0:
                self.cambio_porcentaje = (self.cambio_absoluto / self.precio_anterior_dia) * 100
    
    def _calculate_precio_min(self) -> int:
        """Calcula precio mínimo del día"""
        precios = [p for p in [self.precio_normal, self.precio_oferta, self.precio_tarjeta] if p > 0]
        return min(precios) if precios else 0
    
    def update_prices(self, precio_normal: int = None, precio_oferta: int = None, 
                     precio_tarjeta: int = None) -> bool:
        """
        Actualiza precios y determina si hubo cambio significativo
        
        Returns:
            True si hubo cambio y se actualizó
        """
        # Precios actuales
        current_prices = (self.precio_normal, self.precio_oferta, self.precio_tarjeta)
        
        # Nuevos precios (mantener existentes si no se proporciona nuevo)
        new_normal = precio_normal if precio_normal is not None else self.precio_normal
        new_oferta = precio_oferta if precio_oferta is not None else self.precio_oferta  
        new_tarjeta = precio_tarjeta if precio_tarjeta is not None else self.precio_tarjeta
        
        new_prices = (new_normal, new_oferta, new_tarjeta)
        
        # ¿Hubo cambio en algún precio?
        if current_prices == new_prices:
            return False
        
        # Actualizar precios
        self.precio_normal = new_normal
        self.precio_oferta = new_oferta
        self.precio_tarjeta = new_tarjeta
        
        # Recalcular precio mínimo
        old_min = self.precio_min_dia
        self.precio_min_dia = self._calculate_precio_min()
        
        # Actualizar contadores y timestamps
        self.cambios_en_dia += 1
        self.timestamp_ultima_actualizacion = datetime.now()
        
        # Calcular volatilidad si hay múltiples cambios
        if self.cambios_en_dia > 1 and old_min > 0:
            price_change_pct = abs(self.precio_min_dia - old_min) / old_min * 100
            self.volatilidad_dia = max(self.volatilidad_dia, price_change_pct)
        
        return True
    
    async def send_price_alert_if_significant(self, nombre_producto: str = None) -> bool:
        """
        🔔 Enviar alerta de precio usando el sistema integrado si el cambio es significativo
        
        Args:
            nombre_producto: Nombre del producto para la alerta
            
        Returns:
            True si se envió alerta, False si no
        """
        if not ALERTS_SYSTEM_AVAILABLE:
            return False
        
        # Validar que hay cambio significativo
        if abs(self.cambio_porcentaje) < 5.0:  # Umbral mínimo 5%
            return False
        
        if self.precio_anterior_dia <= 0 or self.precio_min_dia <= 0:
            return False
        
        # Determinar tipo de precio que cambió más
        tipo_precio = "oferta"  # Por defecto
        if self.precio_oferta > 0 and self.precio_oferta == self.precio_min_dia:
            tipo_precio = "oferta"
        elif self.precio_tarjeta > 0 and self.precio_tarjeta == self.precio_min_dia:
            tipo_precio = "tarjeta"
        elif self.precio_normal > 0 and self.precio_normal == self.precio_min_dia:
            tipo_precio = "normal"
        
        # Usar nombre del producto o código interno
        nombre_display = nombre_producto or f"Producto {self.codigo_interno.split('-')[1:3]}"
        
        try:
            # Enviar usando la función de conveniencia
            sent = await send_price_change_alert(
                codigo_interno=self.codigo_interno,
                nombre_producto=nombre_display,
                retailer=self.retailer,
                precio_anterior=self.precio_anterior_dia,
                precio_actual=self.precio_min_dia,
                tipo_precio=tipo_precio
            )
            
            if sent:
                self.alertas_enviadas += 1
                logger.info(f"📤 Alerta enviada para {self.codigo_interno}: {self.cambio_porcentaje:+.1f}%")
            
            return sent
            
        except Exception as e:
            logger.error(f"❌ Error enviando alerta para {self.codigo_interno}: {e}")
            return False
    
    async def check_alert_conditions(self, glitch_detector=None) -> List[Dict[str, Any]]:
        """
        Verifica condiciones de alerta para este snapshot incluyendo detección ML de glitches
        
        Args:
            glitch_detector: Instancia de GlitchDetectionSystem (opcional)
            
        Returns:
            Lista de alertas a enviar
        """
        alerts = []
        
        # Validaciones críticas para evitar alertas erróneas:
        # 1. No alertar si precio actual es 0 (promoción agotada, ej: precio tarjeta terminado)
        # 2. No alertar si no hay precio anterior válido
        if self.precio_anterior_dia <= 0 or self.precio_min_dia <= 0:
            return alerts  # No hay precio anterior para comparar o precio actual es 0 (promoción agotada)
        
        # Obtener umbrales dinámicos desde configuración
        if ALERTS_CONFIG_AVAILABLE and hasattr(self, '_master_prices_manager'):
            config = getattr(self._master_prices_manager, 'alerts_config', None)
            flash_sale_threshold = get_price_threshold('flash_sale', self.retailer) if config else -15.0
            price_drop_threshold = get_price_threshold('price_drop', self.retailer) if config else -10.0
            price_increase_threshold = get_price_threshold('price_increase', self.retailer) if config else 15.0
            volatility_threshold = get_price_threshold('volatility', self.retailer) if config else 8.0
        else:
            # Fallback a valores hardcoded
            flash_sale_threshold = -15.0
            price_drop_threshold = -10.0
            price_increase_threshold = 15.0
            volatility_threshold = 8.0
        
        # Calcular cambio porcentual
        change_pct = abs(self.cambio_porcentaje)
        
        # ALERTA: Bajada significativa (oportunidad) con umbrales dinámicos
        if self.cambio_porcentaje <= price_drop_threshold:  # Bajada significativa
            alert_type = "flash_sale" if self.cambio_porcentaje <= flash_sale_threshold else "price_drop"
            
            # Verificar si está habilitada esta alerta
            if should_send_alert(alert_type, self.retailer):
                alerts.append({
                    'type': alert_type,
                    'codigo_interno': self.codigo_interno,
                    'retailer': self.retailer,
                    'precio_anterior': self.precio_anterior_dia,
                    'precio_actual': self.precio_min_dia,
                    'cambio_porcentaje': self.cambio_porcentaje,
                    'cambio_absoluto': self.cambio_absoluto,
                    'umbral_usado': abs(price_drop_threshold) if alert_type == "price_drop" else abs(flash_sale_threshold),
                    'fecha': self.fecha.isoformat(),
                    'priority': 'high' if alert_type == "flash_sale" else 'medium'
                })
        
        # ALERTA: Subida de precio - DESHABILITADA (no tiene sentido alertar subidas)
        # Las subidas de precio no son oportunidades para el usuario
        # elif self.cambio_porcentaje >= price_increase_threshold:  # Subida significativa
        #     if should_send_alert('price_increase', self.retailer):
        #         alerts.append({
        #             'type': 'price_increase',
        #             'codigo_interno': self.codigo_interno,
        #             'retailer': self.retailer,
        #             'precio_anterior': self.precio_anterior_dia,
        #             'precio_actual': self.precio_min_dia,
        #             'cambio_porcentaje': self.cambio_porcentaje,
        #             'cambio_absoluto': self.cambio_absoluto,
        #             'umbral_usado': price_increase_threshold,
        #             'fecha': self.fecha.isoformat(),
        #             'priority': 'low'
        #         })
        
        # ALERTA: Alta volatilidad (múltiples cambios en el día) con umbrales dinámicos
        if self.volatilidad_dia >= volatility_threshold and self.cambios_en_dia >= 3:
            if should_send_alert('high_volatility', self.retailer):
                alerts.append({
                    'type': 'high_volatility',
                    'codigo_interno': self.codigo_interno,
                    'retailer': self.retailer,
                    'volatilidad': self.volatilidad_dia,
                    'cambios_en_dia': self.cambios_en_dia,
                    'umbral_usado': volatility_threshold,
                    'fecha': self.fecha.isoformat(),
                    'priority': 'medium'
                })
        
        # INTEGRACIÓN ML: Detección avanzada de glitches con feature flags
        if glitch_detector and GLITCH_DETECTION_AVAILABLE and should_send_alert('ml_glitch_detection', self.retailer):
            try:
                glitch_alert = await glitch_detector.detect_price_glitches(
                    product_id=self.codigo_interno,
                    retailer=self.retailer,
                    current_price=float(self.precio_min_dia),
                    category="general"
                )
                
                if glitch_alert:
                    ml_alert_type = f'ml_{glitch_alert.glitch_type}'
                    
                    # Verificar feature flags específicos para alertas ML
                    if should_send_alert(ml_alert_type, self.retailer):
                        # Convertir GlitchAlert a formato estándar
                        ml_alert = {
                            'type': ml_alert_type,
                            'codigo_interno': self.codigo_interno,
                            'retailer': self.retailer,
                            'precio_anterior': self.precio_anterior_dia,
                            'precio_actual': self.precio_min_dia,
                            'ml_confidence': glitch_alert.confidence,
                            'ml_severity': glitch_alert.severity,
                            'ml_discount_pct': glitch_alert.discount_percentage,
                            'ml_evidence': glitch_alert.evidence,
                            'ml_action': glitch_alert.action_recommended,
                            'fecha': self.fecha.isoformat(),
                            'priority': 'critical' if glitch_alert.severity == 'critical' else 'high'
                        }
                        alerts.append(ml_alert)
                    
            except Exception as e:
                # Log error pero continuar con alertas básicas
                logger.warning(f"ML Glitch detection failed: {e}")
        
        return alerts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para almacenamiento - Incluye todos los campos de la tabla"""
        data = {
            # ID se genera automáticamente, no lo incluimos
            'id': None,  # Se generará automáticamente
            
            # Identificadores principales
            'codigo_interno': self.codigo_interno,
            'fecha': self.fecha.isoformat() if isinstance(self.fecha, date) else self.fecha,
            'retailer': self.retailer,
            
            # Los 3 precios principales
            'precio_normal': self.precio_normal,
            'precio_oferta': self.precio_oferta,
            'precio_tarjeta': self.precio_tarjeta,
            
            # Precio mínimo del día y cambios
            'precio_min_dia': self.precio_min_dia,
            'cambios_en_dia': getattr(self, 'cambios_en_dia', 1),
            'precio_anterior_dia': self.precio_anterior_dia,
            'cambio_porcentaje': self.cambio_porcentaje,
            'cambio_absoluto': getattr(self, 'cambio_absoluto', 0),
            
            # Timestamps
            'timestamp_creacion': getattr(self, 'timestamp_creacion', datetime.now()).isoformat(),
            'timestamp_ultima_actualizacion': getattr(self, 'timestamp_ultima_actualizacion', datetime.now()).isoformat(),
            
            # Control de alertas
            'alertas_enviadas': self.alertas_enviadas,
            'tipos_alertas': getattr(self, 'tipos_alertas', '[]'),
            
            # Flags de precio histórico
            'es_precio_historico_min': getattr(self, 'es_precio_historico_min', False),
            'es_precio_historico_max': getattr(self, 'es_precio_historico_max', False),
            
            # Volatilidad
            'volatilidad_dia': getattr(self, 'volatilidad_dia', 0.0),
            
            # Campos adicionales para compatibilidad
            'fecha_captura': datetime.now().isoformat(),
            'internal_sku': self.codigo_interno,  # Alias para compatibilidad
            'metadata': '{}',  # JSON vacío por defecto
            'descuento_porcentaje': self._calculate_discount_percentage()
        }
        return data
    
    def _calculate_discount_percentage(self) -> float:
        """Calcular porcentaje de descuento"""
        if self.precio_normal > 0 and self.precio_min_dia < self.precio_normal:
            return round((self.precio_normal - self.precio_min_dia) / self.precio_normal * 100, 2)
        return 0.0


class MasterPricesManager:
    """Gestor del Master de Precios con snapshot diario y alertas"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.parquet_path = self.base_path / "master" / "precios"  # Particionado por mes
        self.duckdb_path = self.base_path / "warehouse_master.duckdb"
        
        # Asegurar directorios
        self.parquet_path.mkdir(parents=True, exist_ok=True)
        
        # Cache para el día actual (para evitar lecturas constantes)
        self._today_cache: Dict[str, DailyPriceSnapshot] = {}  # codigo_interno -> snapshot
        self._cache_date = date.today()
        
        # Para integrar alertas
        self.alert_callbacks: List[callable] = []
        
        # Integrar ML Glitch Detection System y configuración
        self.glitch_detector = None
        self.alerts_config = None
        self.products_manager = None  # Referencia al manager de productos para enriquecer alertas
        
        if GLITCH_DETECTION_AVAILABLE:
            try:
                # Inicializar con configuración centralizada si está disponible
                if ALERTS_CONFIG_AVAILABLE:
                    self.alerts_config = get_alerts_config()
                    ml_config = self.alerts_config.get_ml_config()
                    self.glitch_detector = GlitchDetectionSystem()
                    # Aplicar configuración ML al detector
                    self.glitch_detector.detection_thresholds.update(ml_config)
                else:
                    self.glitch_detector = GlitchDetectionSystem()
                logger.info("ML Glitch Detection System initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize GlitchDetectionSystem: {e}")
        
        if ALERTS_CONFIG_AVAILABLE and not self.alerts_config:
            try:
                self.alerts_config = get_alerts_config()
                logger.info("Alerts configuration loaded")
            except Exception as e:
                logger.warning(f"Failed to load alerts configuration: {e}")
    
    def add_alert_callback(self, callback: callable):
        """Agregar callback para envío de alertas"""
        self.alert_callbacks.append(callback)
    
    def set_products_manager(self, products_manager):
        """Establecer referencia al manager de productos para enriquecer alertas"""
        self.products_manager = products_manager
        logger.info("Products manager reference set for alert enrichment")
    
    async def _enrich_alert_with_product_data(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer alerta con datos del producto desde Master Products"""
        try:
            if not self.products_manager:
                return alert
            
            codigo_interno = alert.get('codigo_interno')
            if not codigo_interno:
                return alert
            
            # Buscar producto en Master Products
            product = self.products_manager.get_product_by_code(codigo_interno)
            if product:
                # Enriquecer con datos del producto
                alert.update({
                    'product_name': product.nombre or 'Producto sin nombre',
                    'product_link': product.link or '',
                    'brand': product.marca or '',
                    'category': product.categoria or 'Sin categoría',
                    'model': product.model or '',
                    'storage': product.storage or '',
                    'color': product.color or '',
                    'rating': product.rating or 0,
                    'reviews_count': product.reviews_count or 0
                })
                
        except Exception as e:
            logger.warning(f"Failed to enrich alert with product data: {e}")
        
        return alert
    
    def _ensure_table_exists(self):
        """Asegurar que la tabla de precios existe en DuckDB"""
        try:
            conn = duckdb.connect(str(self.duckdb_path))
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS master_precios (
                codigo_interno VARCHAR,
                fecha DATE,
                retailer VARCHAR,
                precio_normal INTEGER,
                precio_oferta INTEGER,
                precio_tarjeta INTEGER,
                precio_min_dia INTEGER,
                cambios_en_dia INTEGER DEFAULT 1,
                precio_anterior_dia INTEGER DEFAULT 0,
                cambio_porcentaje DOUBLE DEFAULT 0.0,
                cambio_absoluto INTEGER DEFAULT 0,
                timestamp_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timestamp_ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alertas_enviadas INTEGER DEFAULT 0,
                tipos_alertas VARCHAR DEFAULT '[]',
                es_precio_historico_min BOOLEAN DEFAULT FALSE,
                es_precio_historico_max BOOLEAN DEFAULT FALSE,
                volatilidad_dia DOUBLE DEFAULT 0.0,
                PRIMARY KEY (codigo_interno, fecha)
            )
            """
            
            conn.execute(create_table_sql)
            
            # Índices para queries comunes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_precios_codigo ON master_precios(codigo_interno)",
                "CREATE INDEX IF NOT EXISTS idx_precios_fecha ON master_precios(fecha)", 
                "CREATE INDEX IF NOT EXISTS idx_precios_retailer ON master_precios(retailer)",
                "CREATE INDEX IF NOT EXISTS idx_precios_min ON master_precios(precio_min_dia)",
                "CREATE INDEX IF NOT EXISTS idx_precios_cambio ON master_precios(cambio_porcentaje)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ensuring prices table exists: {e}")
    
    def _load_today_cache(self):
        """Cargar snapshots del día actual en cache"""
        today = date.today()
        
        # Si ya tenemos el cache del día actual, no recargar
        if self._cache_date == today and self._today_cache:
            return
        
        self._today_cache.clear()
        self._cache_date = today
        
        try:
            # Intentar cargar desde Parquet particionado
            month_path = self.parquet_path / f"year={today.year}" / f"month={today.month:02d}"
            parquet_file = month_path / f"precios_{today.strftime('%Y%m%d')}.parquet"
            
            if parquet_file.exists():
                df = pd.read_parquet(parquet_file)
                df_today = df[df['fecha'] == today.isoformat()]
                
                for _, row in df_today.iterrows():
                    snapshot_dict = row.to_dict()
                    
                    # Convertir strings a tipos correctos
                    if isinstance(snapshot_dict['fecha'], str):
                        snapshot_dict['fecha'] = datetime.fromisoformat(snapshot_dict['fecha']).date()
                    if isinstance(snapshot_dict['timestamp_creacion'], str):
                        snapshot_dict['timestamp_creacion'] = datetime.fromisoformat(snapshot_dict['timestamp_creacion'])
                    if isinstance(snapshot_dict['timestamp_ultima_actualizacion'], str):
                        snapshot_dict['timestamp_ultima_actualizacion'] = datetime.fromisoformat(snapshot_dict['timestamp_ultima_actualizacion'])
                    if isinstance(snapshot_dict['tipos_alertas'], str):
                        snapshot_dict['tipos_alertas'] = json.loads(snapshot_dict['tipos_alertas']) if snapshot_dict['tipos_alertas'] else []
                    
                    # Filtrar campos que no son del constructor
                    constructor_fields = {
                        'codigo_interno', 'fecha', 'retailer', 
                        'precio_normal', 'precio_oferta', 'precio_tarjeta',
                        'precio_anterior_dia'
                    }
                    filtered_dict = {k: v for k, v in snapshot_dict.items() if k in constructor_fields}
                    
                    snapshot = DailyPriceSnapshot(**filtered_dict)
                    self._today_cache[snapshot.codigo_interno] = snapshot
                
                logger.info(f"Loaded {len(self._today_cache)} price snapshots for today")
            
        except Exception as e:
            logger.error(f"Error loading today's price cache: {e}")
    
    def get_snapshot_today(self, codigo_interno: str) -> Optional[DailyPriceSnapshot]:
        """Obtener snapshot del día actual para un producto"""
        self._load_today_cache()
        return self._today_cache.get(codigo_interno)
    
    def get_previous_day_price(self, codigo_interno: str) -> int:
        """Obtener precio mínimo del día anterior"""
        try:
            yesterday = date.today() - timedelta(days=1)
            
            conn = duckdb.connect(str(self.duckdb_path))
            query = """
            SELECT precio_min_dia 
            FROM master_precios 
            WHERE codigo_interno = ? AND fecha = ?
            """
            
            result = conn.execute(query, [codigo_interno, yesterday.isoformat()]).fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting previous day price: {e}")
            return 0
    
    async def update_price(self, codigo_interno: str, retailer: str,
                          precio_normal: int = None, precio_oferta: int = None, 
                          precio_tarjeta: int = None) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Actualizar precio con snapshot diario inteligente
        
        Returns:
            (updated, alerts): Si se actualizó y lista de alertas generadas
        """
        self._load_today_cache()
        
        today = date.today()
        existing_snapshot = self.get_snapshot_today(codigo_interno)
        alerts_generated = []
        
        if existing_snapshot:
            # Actualizar snapshot existente del día
            price_updated = existing_snapshot.update_prices(precio_normal, precio_oferta, precio_tarjeta)
            
            if not price_updated:
                return False, []  # No hubo cambio, no hacer nada
            
            # Pasar referencia del manager para acceso a configuración
            existing_snapshot._master_prices_manager = self
            # Verificar alertas con ML integration
            alerts_generated = await existing_snapshot.check_alert_conditions(self.glitch_detector)
            
            # 🔔 INTEGRACIÓN SISTEMA DE ALERTAS: Enviar alerta si cambio significativo
            if ALERTS_SYSTEM_AVAILABLE and abs(existing_snapshot.cambio_porcentaje) >= 5.0:
                try:
                    # Obtener nombre del producto si está disponible
                    producto_nombre = self._get_product_name(codigo_interno)
                    await existing_snapshot.send_price_alert_if_significant(producto_nombre)
                except Exception as e:
                    logger.warning(f"⚠️ Error enviando alerta integrada: {e}")
            
        else:
            # Crear nuevo snapshot para el día
            precio_anterior = self.get_previous_day_price(codigo_interno)
            
            snapshot = DailyPriceSnapshot(
                codigo_interno=codigo_interno,
                fecha=today,
                retailer=retailer,
                precio_normal=precio_normal or 0,
                precio_oferta=precio_oferta or 0,
                precio_tarjeta=precio_tarjeta or 0,
                precio_anterior_dia=precio_anterior
            )
            
            # Pasar referencia del manager para acceso a configuración
            snapshot._master_prices_manager = self
            # Verificar alertas para nuevo snapshot con ML integration
            alerts_generated = await snapshot.check_alert_conditions(self.glitch_detector)
            
            # 🔔 INTEGRACIÓN SISTEMA DE ALERTAS: Enviar alerta para nuevo snapshot si es significativo
            if ALERTS_SYSTEM_AVAILABLE and abs(snapshot.cambio_porcentaje) >= 5.0:
                try:
                    # Obtener nombre del producto si está disponible
                    producto_nombre = self._get_product_name(codigo_interno)
                    await snapshot.send_price_alert_if_significant(producto_nombre)
                except Exception as e:
                    logger.warning(f"⚠️ Error enviando alerta integrada: {e}")
            
            self._today_cache[codigo_interno] = snapshot
        
        # Enviar alertas si existen callbacks registrados
        if alerts_generated and self.alert_callbacks:
            for alert in alerts_generated:
                # Enriquecer alerta con datos del producto
                enriched_alert = await self._enrich_alert_with_product_data(alert)
                
                for callback in self.alert_callbacks:
                    try:
                        await callback(enriched_alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
                
                # Marcar alerta como enviada
                if existing_snapshot:
                    existing_snapshot.alertas_enviadas += 1
                    existing_snapshot.tipos_alertas.append(alert['type'])
        
        return True, alerts_generated
    
    def save_daily_snapshots(self, target_date: date = None):
        """Guardar snapshots del día a storage permanente"""
        if not target_date:
            target_date = date.today()
        
        # Si no es el día actual, no tenemos nada que guardar
        if target_date != self._cache_date or not self._today_cache:
            return
        
        try:
            # Preparar datos para guardar
            snapshots_data = []
            for snapshot in self._today_cache.values():
                snapshots_data.append(snapshot.to_dict())
            
            if not snapshots_data:
                return
            
            # Crear DataFrame
            df = pd.DataFrame(snapshots_data)
            
            # Debug: Ver columnas del DataFrame
            logger.info(f"DataFrame columns before save: {df.columns.tolist()}")
            logger.info(f"DataFrame shape: {df.shape}")
            if len(df) > 0:
                logger.info(f"First row: {df.iloc[0].to_dict()}")
            
            # Guardar a Parquet particionado por año/mes
            month_path = self.parquet_path / f"year={target_date.year}" / f"month={target_date.month:02d}"
            month_path.mkdir(parents=True, exist_ok=True)
            
            parquet_file = month_path / f"precios_{target_date.strftime('%Y%m%d')}.parquet"
            df.to_parquet(parquet_file, compression='snappy')
            
            # Guardar a DuckDB
            self._ensure_table_exists()
            conn = duckdb.connect(str(self.duckdb_path))
            
            # Registrar el DataFrame y ejecutar operación atómica
            try:
                conn.register("df", df)
            except Exception:
                # Algunos bindings de DuckDB permiten pasar DF sin register, pero garantizamos registro
                pass
            
            # Usar transacción para consistencia del día
            logger.info(f"Starting transaction to save {len(df)} price snapshots")
            conn.execute("BEGIN")
            try:
                # Eliminar registros existentes del día (idempotente)
                conn.execute("DELETE FROM master_precios WHERE fecha = ?", [target_date.isoformat()])
                
                # Obtener el máximo ID actual
                max_id_result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM master_precios").fetchone()
                max_id = max_id_result[0] if max_id_result else 0
                
                # Eliminar columna id si existe con valores None
                if 'id' in df.columns:
                    logger.info(f"Dropping existing 'id' column with values: {df['id'].tolist()[:5]}")
                    df = df.drop('id', axis=1)
                
                # Asignar IDs secuenciales al DataFrame
                new_ids = list(range(max_id + 1, max_id + 1 + len(df)))
                logger.info(f"Assigning new IDs: {new_ids[:5]}... (total: {len(new_ids)})")
                df['id'] = new_ids
                logger.info(f"DataFrame 'id' column after assignment: {df['id'].tolist()[:5]}")
                
                # Verificar que el ID realmente está asignado
                if 'id' not in df.columns:
                    logger.error("'id' column missing after assignment!")
                elif df['id'].isna().any():
                    logger.error(f"Found NaN values in 'id' column: {df['id'].isna().sum()}")
                else:
                    logger.info(f"ID column OK: min={df['id'].min()}, max={df['id'].max()}")
                
                # Reordenar columnas para que coincidan con el esquema de la tabla
                column_order = [
                    'id', 'codigo_interno', 'fecha', 'retailer',
                    'precio_normal', 'precio_oferta', 'precio_tarjeta', 'precio_min_dia',
                    'cambios_en_dia', 'precio_anterior_dia', 'cambio_porcentaje', 'cambio_absoluto',
                    'timestamp_creacion', 'timestamp_ultima_actualizacion',
                    'alertas_enviadas', 'tipos_alertas',
                    'es_precio_historico_min', 'es_precio_historico_max',
                    'volatilidad_dia', 'fecha_captura', 'internal_sku',
                    'metadata', 'descuento_porcentaje'
                ]
                df = df[column_order]
                
                # Verificar DataFrame final antes de insertar
                logger.info(f"Final DataFrame columns: {df.columns.tolist()}")
                logger.info(f"Final DataFrame shape: {df.shape}")
                logger.info(f"First row 'id' value: {df.iloc[0]['id'] if len(df) > 0 else 'N/A'}")
                
                # Re-registrar el DataFrame actualizado
                conn.unregister("df")
                conn.register("df", df)
                
                # Insertar nuevos registros con columnas explícitas (excluyendo id para que use autoincrement)
                columns_without_id = [col for col in column_order if col != 'id']
                columns_str = ', '.join(columns_without_id)
                
                # Crear DataFrame sin la columna id para que DuckDB use autoincrement
                df_without_id = df[columns_without_id]
                conn.unregister("df")
                conn.register("df_insert", df_without_id)
                
                insert_query = f"""
                INSERT INTO master_precios ({columns_str})
                SELECT {columns_str} FROM df_insert
                """
                
                logger.info(f"Executing INSERT with {len(df_without_id)} rows")
                conn.execute(insert_query)
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            finally:
                conn.close()
            
            logger.info(f"Saved {len(snapshots_data)} price snapshots for {target_date}")
            
        except Exception as e:
            logger.error(f"Error saving daily snapshots: {e}")
    
    def get_historical_price_stats(self, codigo_interno: str, days_back: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas históricas de precio"""
        try:
            conn = duckdb.connect(str(self.duckdb_path))
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            query = """
            SELECT 
                MIN(precio_min_dia) as precio_historico_min,
                MAX(precio_min_dia) as precio_historico_max,
                AVG(precio_min_dia) as precio_promedio,
                COUNT(*) as dias_con_datos,
                SUM(cambios_en_dia) as total_cambios,
                AVG(ABS(cambio_porcentaje)) as volatilidad_promedio
            FROM master_precios 
            WHERE codigo_interno = ? 
            AND fecha BETWEEN ? AND ?
            AND precio_min_dia > 0
            """
            
            result = conn.execute(query, [codigo_interno, start_date.isoformat(), end_date.isoformat()]).fetchone()
            conn.close()
            
            if result:
                return {
                    'precio_historico_min': int(result[0] or 0),
                    'precio_historico_max': int(result[1] or 0),
                    'precio_promedio': float(result[2] or 0),
                    'dias_con_datos': int(result[3] or 0),
                    'total_cambios': int(result[4] or 0),
                    'volatilidad_promedio': float(result[5] or 0),
                    'periodo_analizado_dias': days_back
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting historical price stats: {e}")
            return {}
    
    def get_daily_price_evolution(self, codigo_interno: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Obtener evolución de precios últimos N días"""
        try:
            conn = duckdb.connect(str(self.duckdb_path))
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            query = """
            SELECT fecha, precio_min_dia, cambio_porcentaje, cambios_en_dia
            FROM master_precios 
            WHERE codigo_interno = ? 
            AND fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
            """
            
            results = conn.execute(query, [codigo_interno, start_date.isoformat(), end_date.isoformat()]).fetchall()
            conn.close()
            
            evolution = []
            for row in results:
                evolution.append({
                    'fecha': row[0],
                    'precio_min_dia': int(row[1]),
                    'cambio_porcentaje': float(row[2] or 0),
                    'cambios_en_dia': int(row[3] or 0)
                })
            
            return evolution
            
        except Exception as e:
            logger.error(f"Error getting price evolution: {e}")
            return []
    
    async def midnight_closure(self):
        """Proceso automático de cierre diario a medianoche"""
        logger.info("Starting midnight closure process...")
        
        try:
            # Guardar snapshots del día que termina
            yesterday = date.today() - timedelta(days=1)
            self.save_daily_snapshots(yesterday)
            
            # Limpiar cache para el nuevo día
            self._today_cache.clear()
            self._cache_date = date.today()
            
            # Actualizar flags de precios históricos min/max
            await self._update_historical_flags()
            
            logger.info("Midnight closure completed successfully")
            
        except Exception as e:
            logger.error(f"Error in midnight closure: {e}")
    
    async def _update_historical_flags(self):
        """Actualizar flags de precios históricos mínimos/máximos"""
        try:
            conn = duckdb.connect(str(self.duckdb_path))
            
            # Actualizar flags de precio histórico mínimo
            update_min_sql = """
            UPDATE master_precios 
            SET es_precio_historico_min = TRUE
            WHERE (codigo_interno, precio_min_dia) IN (
                SELECT codigo_interno, MIN(precio_min_dia)
                FROM master_precios 
                WHERE precio_min_dia > 0
                GROUP BY codigo_interno
            )
            """
            
            # Actualizar flags de precio histórico máximo
            update_max_sql = """
            UPDATE master_precios 
            SET es_precio_historico_max = TRUE
            WHERE (codigo_interno, precio_min_dia) IN (
                SELECT codigo_interno, MAX(precio_min_dia)
                FROM master_precios 
                WHERE precio_min_dia > 0
                GROUP BY codigo_interno
            )
            """
            
            conn.execute(update_min_sql)
            conn.execute(update_max_sql)
            conn.close()
            
            logger.info("Historical price flags updated")
            
        except Exception as e:
            logger.error(f"Error updating historical flags: {e}")
    
    def _get_product_name(self, codigo_interno: str) -> str:
        """
        🏷️ Obtener nombre del producto desde el master de productos
        
        Args:
            codigo_interno: Código interno del producto
            
        Returns:
            Nombre del producto o código interno como fallback
        """
        try:
            # Intentar obtener desde master de productos si está disponible
            if hasattr(self, 'products_manager') and self.products_manager:
                producto = self.products_manager.get_product_by_code(codigo_interno)
                if producto and hasattr(producto, 'nombre') and producto.nombre:
                    return producto.nombre
            
            # Fallback: construir nombre a partir del código interno
            # Formato: CL-MARCA-MODELO-SPEC-RETAILER-SEQ
            parts = codigo_interno.split('-')
            if len(parts) >= 3:
                marca = parts[1]
                modelo = parts[2]
                return f"{marca} {modelo}".title()
            
            return f"Producto {codigo_interno[:15]}"
            
        except Exception as e:
            logger.debug(f"Error obteniendo nombre para {codigo_interno}: {e}")
            return f"Producto {codigo_interno.split('-')[1] if '-' in codigo_interno else codigo_interno}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del master de precios"""
        try:
            conn = duckdb.connect(str(self.duckdb_path))
            
            # Estadísticas generales
            stats_query = """
            SELECT 
                COUNT(*) as total_snapshots,
                COUNT(DISTINCT codigo_interno) as unique_products,
                COUNT(DISTINCT fecha) as days_with_data,
                MIN(fecha) as earliest_date,
                MAX(fecha) as latest_date,
                SUM(alertas_enviadas) as total_alerts_sent,
                AVG(cambios_en_dia) as avg_changes_per_day
            FROM master_precios
            """
            
            result = conn.execute(stats_query).fetchone()
            conn.close()
            
            if result:
                return {
                    'total_snapshots': int(result[0] or 0),
                    'unique_products': int(result[1] or 0),
                    'days_with_data': int(result[2] or 0),
                    'earliest_date': result[3],
                    'latest_date': result[4],
                    'total_alerts_sent': int(result[5] or 0),
                    'avg_changes_per_day': float(result[6] or 0),
                    'today_cache_size': len(self._today_cache),
                    'cache_date': self._cache_date.isoformat()
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting price stats: {e}")
            return {}


# Helper functions
async def setup_telegram_alerts_integration(prices_manager: MasterPricesManager):
    """Integrar alertas de precios con Telegram"""
    try:
        from core.telegram_logger import (
            send_price_alert,
            get_telegram_logger,
            initialize_telegram_logger,
        )

        # Inicializar logger global si no existe y hay credenciales en entorno
        try:
            if not get_telegram_logger():
                token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
                chat_id = (
                    os.getenv('TELEGRAM_ALERT_CHAT_ID', '').strip()
                    or os.getenv('TELEGRAM_CHAT_ID', '').strip()
                )
                if not chat_id:
                    # usar primer SUPERUSER si est definido
                    su = os.getenv('SUPERUSERS', '')
                    if su:
                        first = next((x.strip() for x in su.split(',') if x.strip()), '')
                        if first.isdigit():
                            chat_id = first
                if token and chat_id:
                    initialize_telegram_logger(token, chat_id)
                    logger.info("TelegramLogger initialized from environment for alerts")
                else:
                    logger.info("Telegram credentials not found in env; alerts will be skipped")
        except Exception as init_e:
            logger.warning(f"Could not initialize Telegram logger: {init_e}")
        
        async def telegram_alert_callback(alert: Dict[str, Any]):
            """Callback para enviar alertas via Telegram"""
            
            if alert['type'] in ['price_drop', 'flash_sale', 'price_increase']:
                alert_data = {
                    'producto': f"Producto {alert['codigo_interno']}",  # Se puede enriquecer con nombre real
                    'retailer': alert['retailer'],
                    'precio_anterior': alert['precio_anterior'],
                    'precio_actual': alert['precio_actual'], 
                    'cambio_porcentaje': alert['cambio_porcentaje'],
                    'sku': alert['codigo_interno'],
                    'categoria': 'producto'  # Se puede enriquecer desde MasterProducts
                }
                
                success = await send_price_alert(alert_data)
                if success:
                    logger.info(f"Alert sent for {alert['codigo_interno']}: {alert['type']}")

        prices_manager.add_alert_callback(telegram_alert_callback)
        logger.info("Telegram alerts integration configured")
        
    except ImportError:
        logger.warning("Telegram integration not available")
    except Exception as e:
        logger.error(f"Error setting up Telegram alerts: {e}")


# Función para integración con scrapers
async def process_price_update_from_scraping(codigo_interno: str, retailer: str,
                                           scraping_data: Dict[str, Any],
                                           prices_manager: MasterPricesManager) -> Dict[str, Any]:
    """Procesar actualización de precio desde datos de scraping"""
    
    # Extraer precios de los datos de scraping
    precio_normal = int(scraping_data.get('precio_normal_num', 0) or 0)
    precio_oferta = int(scraping_data.get('precio_oferta_num', 0) or 0) 
    precio_tarjeta = int(scraping_data.get('precio_tarjeta_num', 0) or 0)
    
    # Si no hay precios, no procesar
    if not any([precio_normal, precio_oferta, precio_tarjeta]):
        return {'updated': False, 'reason': 'no_prices_found'}
    
    # Actualizar en master de precios
    updated, alerts = await prices_manager.update_price(
        codigo_interno=codigo_interno,
        retailer=retailer,
        precio_normal=precio_normal,
        precio_oferta=precio_oferta,
        precio_tarjeta=precio_tarjeta
    )
    
    return {
        'updated': updated,
        'alerts_generated': len(alerts),
        'alerts': alerts
    }
