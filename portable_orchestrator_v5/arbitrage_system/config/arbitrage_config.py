# -*- coding: utf-8 -*-
"""
🔧 Configuración del Sistema de Arbitraje V5
============================================
Configuración centralizada con integración completa V5 y soporte de emojis.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageConfigV5:
    """
    Configuración del sistema de arbitraje V5 con inteligencia avanzada 🧠
    
    Integra completamente con:
    - Redis Intelligence System
    - Intelligent Cache Manager  
    - Master Intelligence Integrator
    - Scraping Frequency Optimizer
    """
    
    # === PARÁMETROS DE ARBITRAJE ===
    min_margin_clp: float = 15000.0          # Margen mínimo $15k CLP 💰
    min_percentage: float = 12.0             # ROI mínimo 12%
    min_similarity_score: float = 0.80       # Similaridad ML mínima 80% 🎯
    max_price_ratio: float = 4.0             # Ratio máximo precio alto/bajo
    
    # === INTEGRACIÓN V5 AVANZADA ===
    use_redis_intelligence: bool = True      # 🧠 Usar Redis Intelligence System
    use_intelligent_cache: bool = True       # ⚡ Cache inteligente L1-L4
    use_volatility_analysis: bool = True     # 📈 Análisis de volatilidad
    use_predictive_scoring: bool = True      # 🔮 Scoring predictivo
    
    # === SCHEDULING INTELIGENTE ===
    critical_tier_frequency: int = 30       # 30 min para productos críticos 🔥
    important_tier_frequency: int = 120     # 2h para productos importantes ⚡
    tracking_tier_frequency: int = 360      # 6h para productos tracking 📊
    
    # === RETAILERS Y CATEGORÍAS ===
    retailers_enabled: List[str] = field(default_factory=lambda: [
        'falabella', 'ripley', 'paris', 'hites', 'abcdin'
    ])
    categories_priority: List[str] = field(default_factory=lambda: [
        'celulares', 'computadores', 'tablets', 'televisores', 'electrodomesticos'
    ])
    
    # === ALERTAS Y NOTIFICACIONES ===
    enable_auto_alerts: bool = True          # 🚨 Alertas automáticas
    alert_high_value_threshold: float = 50000.0  # Alertas >$50k
    alert_high_roi_threshold: float = 25.0   # Alertas >25% ROI
    enable_emoji_alerts: bool = True         # 🎭 Emojis en alertas
    
    # === BASE DE DATOS ===
    database_config: Dict[str, Any] = field(default_factory=lambda: {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': int(os.getenv('PGPORT', '5434')),
        'database': os.getenv('PGDATABASE', 'price_orchestrator'),
        'user': os.getenv('PGUSER', 'orchestrator'), 
        'password': os.getenv('PGPASSWORD', 'orchestrator_2025'),
        'pool_size': 10,
        'max_connections': 20
    })
    
    # === REDIS CONFIGURATION ===
    redis_config: Dict[str, Any] = field(default_factory=lambda: {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6380')),
        'db': int(os.getenv('REDIS_ARBITRAGE_DB', '2')),  # DB separada para arbitraje
        'decode_responses': True,
        'socket_timeout': 30,
        'retry_on_timeout': True
    })
    
    # === ML Y PROCESSING ===
    ml_model_path: str = "models/v5_arbitrage_model.joblib"
    batch_size: int = 100                    # Productos por batch
    max_parallel_workers: int = 4            # Workers paralelos
    similarity_cache_ttl: int = 3600         # 1h cache similaridad
    
    # === PERFORMANCE OPTIMIZATION ===
    cache_l1_size: int = 1000               # Cache L1 (memoria)
    cache_l2_ttl: int = 1800                # Cache L2 Redis (30min)  
    cache_l3_predictions: bool = True       # Cache L3 predictivo
    cache_l4_analytics: bool = True         # Cache L4 analytics
    
    # === ANTI-DETECTION ===
    use_human_delays: bool = True           # 🤖 Delays humanos
    min_delay_seconds: float = 0.5          # Delay mínimo
    max_delay_seconds: float = 2.0          # Delay máximo
    randomize_query_order: bool = True      # Orden aleatorio queries
    
    # === MONITORING Y MÉTRICAS ===
    enable_metrics: bool = True             # 📊 Métricas detalladas
    metrics_retention_days: int = 30        # Retención 30 días
    log_level: str = "INFO"                 # Nivel logging
    
    # === REGLAS DE NEGOCIO ===
    exclude_out_of_stock: bool = True       # Excluir sin stock
    exclude_refurbished: bool = True        # Excluir reacondicionados
    min_rating: float = 3.5                 # Rating mínimo 3.5⭐
    min_reviews: int = 5                    # Mínimo 5 reviews
    
    # === OPORTUNIDAD SCORING ===
    scoring_weights: Dict[str, float] = field(default_factory=lambda: {
        'profit_margin': 0.30,              # 30% peso margen
        'similarity_score': 0.25,           # 25% peso similaridad ML  
        'volatility_score': 0.15,           # 15% peso volatilidad
        'popularity_score': 0.15,           # 15% peso popularidad
        'availability_score': 0.10,         # 10% peso disponibilidad
        'timing_score': 0.05                # 5% peso timing
    })

    def __post_init__(self):
        """Validación post-inicialización con emojis 🔍"""
        # Validar configuración
        if self.min_margin_clp < 5000:
            logger.warning("⚠️ Margen mínimo muy bajo (<$5k)")
        
        if self.min_percentage < 5.0:
            logger.warning("⚠️ ROI mínimo muy bajo (<5%)")
            
        if not self.retailers_enabled:
            raise ValueError("❌ Debe especificar al menos un retailer")
            
        # Validar pesos scoring sumen 1.0
        total_weight = sum(self.scoring_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"⚠️ Pesos scoring no suman 1.0: {total_weight}")
        
        logger.info("✅ Configuración V5 arbitraje inicializada correctamente")

    def get_tier_frequency(self, tier: str) -> int:
        """Obtener frecuencia según tier 📊"""
        tier_frequencies = {
            'critical': self.critical_tier_frequency,
            'important': self.important_tier_frequency, 
            'tracking': self.tracking_tier_frequency
        }
        return tier_frequencies.get(tier.lower(), self.tracking_tier_frequency)
    
    def is_retailer_enabled(self, retailer: str) -> bool:
        """Verificar si retailer está habilitado ✅"""
        return retailer.lower() in [r.lower() for r in self.retailers_enabled]
    
    def get_cache_config(self, level: str) -> Dict[str, Any]:
        """Configuración de cache por nivel 📦"""
        configs = {
            'l1': {'size': self.cache_l1_size, 'type': 'memory'},
            'l2': {'ttl': self.cache_l2_ttl, 'type': 'redis'},
            'l3': {'enabled': self.cache_l3_predictions, 'type': 'predictive'},
            'l4': {'enabled': self.cache_l4_analytics, 'type': 'analytics'}
        }
        return configs.get(level.lower(), {})
    
    def should_alert(self, opportunity: Dict[str, Any]) -> bool:
        """Determinar si enviar alerta 🚨"""
        if not self.enable_auto_alerts:
            return False
            
        margin = opportunity.get('margin_clp', 0)
        roi = opportunity.get('roi_percentage', 0)
        
        return (margin >= self.alert_high_value_threshold or 
                roi >= self.alert_high_roi_threshold)
    
    def format_alert_message(self, opportunity: Dict[str, Any]) -> str:
        """Formatear mensaje de alerta con emojis 📢"""
        if not self.enable_emoji_alerts:
            return f"Oportunidad detectada: {opportunity.get('product_name', 'Unknown')}"
        
        margin = opportunity.get('margin_clp', 0)
        roi = opportunity.get('roi_percentage', 0)
        
        emoji = "🔥" if margin >= 50000 else "💰" if roi >= 25 else "📊"
        
        return (f"{emoji} ARBITRAJE DETECTADO!\n"
                f"🛍️ {opportunity.get('product_name', 'Producto')}\n" 
                f"💵 Margen: ${margin:,.0f} CLP ({roi:.1f}% ROI)\n"
                f"🏪 {opportunity.get('buy_retailer', '')} → {opportunity.get('sell_retailer', '')}\n"
                f"⭐ Confianza: {opportunity.get('confidence_score', 0)*100:.1f}%")

# Instancia global de configuración
DEFAULT_CONFIG = ArbitrageConfigV5()

# Configuraciones predefinidas
PRODUCTION_CONFIG = ArbitrageConfigV5(
    min_margin_clp=20000.0,
    min_percentage=15.0,
    min_similarity_score=0.85,
    critical_tier_frequency=15,  # 15min para críticos
    important_tier_frequency=60, # 1h para importantes
    batch_size=50,
    max_parallel_workers=6
)

DEVELOPMENT_CONFIG = ArbitrageConfigV5(
    min_margin_clp=5000.0,
    min_percentage=5.0,
    min_similarity_score=0.70,
    enable_auto_alerts=False,
    log_level="DEBUG"
)

def get_config(env: str = "default") -> ArbitrageConfigV5:
    """
    Obtener configuración según ambiente 🔧
    
    Args:
        env: 'default', 'production', 'development'
        
    Returns:
        Configuración correspondiente
    """
    configs = {
        'default': DEFAULT_CONFIG,
        'production': PRODUCTION_CONFIG,
        'development': DEVELOPMENT_CONFIG,
        'prod': PRODUCTION_CONFIG,
        'dev': DEVELOPMENT_CONFIG
    }
    
    config = configs.get(env.lower(), DEFAULT_CONFIG)
    logger.info(f"🔧 Configuración cargada: {env} con {len(config.retailers_enabled)} retailers")
    
    return config