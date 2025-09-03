# -*- coding: utf-8 -*-
"""
⚙️ Configuración Unificada del Sistema de Alertas
================================================

Configuración centralizada para integración de alertas entre:
- Master Prices System
- V5 Arbitrage System  
- Telegram Bot (alerts_bot)

Maneja configuración, umbrales y habilitación de alertas.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AlertsIntegrationConfig:
    """
    🔧 Configuración integrada del sistema de alertas
    
    Centraliza configuración para todos los sistemas:
    - Master System → Telegram
    - V5 Arbitrage → Telegram
    - Bot standalone
    """
    
    # === HABILITACIÓN GENERAL ===
    enabled: bool = True                         # Master switch
    telegram_enabled: bool = True               # Envío por Telegram
    local_logging_enabled: bool = True         # Logs locales como fallback
    
    # === CONFIGURACIÓN DE CONEXIÓN ===
    telegram_token: str = ""                   # Token del bot
    redis_url: str = ""                       # URL de Redis
    database_url: str = ""                    # URL de PostgreSQL
    
    # === UMBRALES DE PRECIO (Master System) ===
    price_change_threshold: float = 5.0      # % mínimo para alertar
    flash_sale_threshold: float = 15.0       # % para flash sales
    volatility_threshold: float = 10.0       # % para alta volatilidad
    
    # === UMBRALES DE ARBITRAJE (V5 System) ===
    arbitrage_min_margin_clp: float = 15000   # Margen mínimo en CLP
    arbitrage_min_roi: float = 12.0           # ROI mínimo %
    arbitrage_confidence_threshold: float = 0.75  # ML confidence mínima
    
    # === CONFIGURACIÓN DE ENVÍO ===
    max_alerts_per_hour: int = 50             # Límite anti-spam
    cooldown_minutes: int = 30                # Cooldown entre alertas del mismo producto
    broadcast_to_admins: bool = True          # Enviar a superusuarios
    
    # === CONFIGURACIÓN POR RETAILER ===
    retailer_settings: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "falabella": {
            "enabled": True,
            "price_change_threshold": 5.0,
            "arbitrage_priority": "high"
        },
        "ripley": {
            "enabled": True, 
            "price_change_threshold": 6.0,
            "arbitrage_priority": "high"
        },
        "paris": {
            "enabled": True,
            "price_change_threshold": 7.0,
            "arbitrage_priority": "medium"
        },
        "hites": {
            "enabled": True,
            "price_change_threshold": 8.0,
            "arbitrage_priority": "medium" 
        },
        "abcdin": {
            "enabled": True,
            "price_change_threshold": 10.0,
            "arbitrage_priority": "low"
        },
        "mercadolibre": {
            "enabled": False,  # Muy volátil
            "price_change_threshold": 15.0,
            "arbitrage_priority": "low"
        }
    })
    
    # === TIPOS DE ALERTA HABILITADOS ===
    alert_types_enabled: Dict[str, bool] = field(default_factory=lambda: {
        # Master System
        "price_drop": True,
        "flash_sale": True, 
        "price_increase": False,  # No alertar subidas
        "high_volatility": True,
        
        # V5 Arbitrage
        "arbitrage_opportunity": True,
        "high_value_arbitrage": True,
        "premium_arbitrage": True,
        
        # Sistema general
        "system_errors": True,
        "daily_summary": True
    })
    
    def __post_init__(self):
        """Inicializar configuración desde variables de entorno"""
        # Cargar desde .env si no están configuradas
        if not self.telegram_token:
            self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        if not self.redis_url:
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6380/0")
        
        if not self.database_url:
            self.database_url = os.getenv("DATABASE_URL", "")
        
        # Validaciones
        if self.enabled and self.telegram_enabled and not self.telegram_token:
            logger.warning("⚠️ Alertas habilitadas pero TELEGRAM_BOT_TOKEN no configurado")
            self.telegram_enabled = False
    
    def get_retailer_threshold(self, retailer: str, alert_type: str = "price_change") -> float:
        """
        Obtener umbral específico para un retailer
        
        Args:
            retailer: Nombre del retailer
            alert_type: Tipo de alerta
            
        Returns:
            Umbral configurado o por defecto
        """
        retailer_config = self.retailer_settings.get(retailer.lower(), {})
        
        if alert_type == "price_change":
            return retailer_config.get("price_change_threshold", self.price_change_threshold)
        elif alert_type == "flash_sale":
            return self.flash_sale_threshold
        elif alert_type == "volatility":
            return self.volatility_threshold
        else:
            return self.price_change_threshold
    
    def is_retailer_enabled(self, retailer: str) -> bool:
        """Verificar si un retailer está habilitado para alertas"""
        return self.retailer_settings.get(retailer.lower(), {}).get("enabled", True)
    
    def is_alert_type_enabled(self, alert_type: str) -> bool:
        """Verificar si un tipo de alerta está habilitado"""
        return self.alert_types_enabled.get(alert_type, False)
    
    def should_send_alert(self, alert_type: str, retailer: str = None) -> bool:
        """
        Determinar si se debe enviar una alerta
        
        Args:
            alert_type: Tipo de alerta
            retailer: Retailer (opcional)
            
        Returns:
            True si debe enviarse la alerta
        """
        # Verificar si las alertas están habilitadas globalmente
        if not self.enabled:
            return False
        
        # Verificar si el tipo de alerta está habilitado
        if not self.is_alert_type_enabled(alert_type):
            return False
        
        # Verificar retailer si se proporciona
        if retailer and not self.is_retailer_enabled(retailer):
            return False
        
        return True
    
    def get_arbitrage_priority(self, retailer: str) -> str:
        """Obtener prioridad de arbitraje para un retailer"""
        return self.retailer_settings.get(retailer.lower(), {}).get("arbitrage_priority", "medium")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario"""
        return {
            "enabled": self.enabled,
            "telegram_enabled": self.telegram_enabled,
            "price_change_threshold": self.price_change_threshold,
            "arbitrage_min_margin_clp": self.arbitrage_min_margin_clp,
            "arbitrage_min_roi": self.arbitrage_min_roi,
            "max_alerts_per_hour": self.max_alerts_per_hour,
            "retailer_count": len(self.retailer_settings),
            "alert_types_count": len([k for k, v in self.alert_types_enabled.items() if v]),
            "last_updated": datetime.now().isoformat()
        }

# Instancia global de configuración
_alerts_config_instance = None

def get_alerts_config() -> AlertsIntegrationConfig:
    """
    Obtener instancia singleton de la configuración de alertas
    
    Returns:
        Configuración de alertas
    """
    global _alerts_config_instance
    
    if _alerts_config_instance is None:
        _alerts_config_instance = AlertsIntegrationConfig()
        logger.info("⚙️ Configuración de alertas inicializada")
    
    return _alerts_config_instance

def should_send_alert(alert_type: str, retailer: str = None) -> bool:
    """
    Función de conveniencia para verificar si enviar alerta
    
    Args:
        alert_type: Tipo de alerta
        retailer: Retailer (opcional)
        
    Returns:
        True si debe enviarse
    """
    config = get_alerts_config()
    return config.should_send_alert(alert_type, retailer)

def get_price_threshold(alert_type: str, retailer: str = None) -> float:
    """
    Función de conveniencia para obtener umbral de precio
    
    Args:
        alert_type: Tipo de alerta  
        retailer: Retailer (opcional)
        
    Returns:
        Umbral configurado
    """
    config = get_alerts_config()
    
    if retailer:
        return config.get_retailer_threshold(retailer, alert_type)
    
    # Valores por defecto según tipo
    if alert_type == "flash_sale":
        return config.flash_sale_threshold
    elif alert_type == "volatility":
        return config.volatility_threshold
    else:
        return config.price_change_threshold

def update_config_from_env():
    """Actualizar configuración desde variables de entorno"""
    global _alerts_config_instance
    
    if _alerts_config_instance is None:
        _alerts_config_instance = AlertsIntegrationConfig()
    
    # Actualizar desde variables de entorno
    _alerts_config_instance.enabled = os.getenv("ALERTS_ENABLED", "true").lower() in ("true", "1", "yes")
    _alerts_config_instance.price_change_threshold = float(os.getenv("PRICE_CHANGE_THRESHOLD", "5.0"))
    _alerts_config_instance.arbitrage_min_margin_clp = float(os.getenv("ARBITRAGE_MIN_MARGIN", "15000"))
    _alerts_config_instance.arbitrage_min_roi = float(os.getenv("ARBITRAGE_MIN_ROI", "12.0"))
    
    logger.info("⚙️ Configuración actualizada desde variables de entorno")

# Funciones de configuración específica para compatibilidad

def get_master_prices_config() -> Dict[str, Any]:
    """Configuración específica para Master Prices System"""
    config = get_alerts_config()
    return {
        "enabled": config.enabled and config.telegram_enabled,
        "price_change_threshold": config.price_change_threshold,
        "flash_sale_threshold": config.flash_sale_threshold,
        "volatility_threshold": config.volatility_threshold,
        "retailer_settings": config.retailer_settings
    }

def get_v5_arbitrage_config() -> Dict[str, Any]:
    """Configuración específica para V5 Arbitrage System"""
    config = get_alerts_config()
    return {
        "enabled": config.enabled and config.telegram_enabled,
        "min_margin_clp": config.arbitrage_min_margin_clp,
        "min_roi": config.arbitrage_min_roi,
        "confidence_threshold": config.arbitrage_confidence_threshold,
        "max_alerts_per_hour": config.max_alerts_per_hour,
        "broadcast_to_admins": config.broadcast_to_admins
    }

def get_telegram_bot_config() -> Dict[str, Any]:
    """Configuración específica para Telegram Bot"""
    config = get_alerts_config()
    return {
        "token": config.telegram_token,
        "redis_url": config.redis_url,
        "database_url": config.database_url,
        "max_alerts_per_hour": config.max_alerts_per_hour,
        "cooldown_minutes": config.cooldown_minutes
    }

# Función de diagnóstico
def diagnose_alerts_config() -> Dict[str, Any]:
    """
    Diagnóstico completo de la configuración de alertas
    
    Returns:
        Reporte de estado de configuración
    """
    config = get_alerts_config()
    
    diagnosis = {
        "config_status": "✅ OK" if config.enabled else "❌ DISABLED",
        "telegram_status": "✅ OK" if config.telegram_enabled and config.telegram_token else "❌ NO TOKEN",
        "redis_status": "✅ OK" if config.redis_url else "❌ NO URL",
        "database_status": "✅ OK" if config.database_url else "❌ NO URL",
        "retailers_enabled": len([r for r, c in config.retailer_settings.items() if c.get("enabled")]),
        "alert_types_enabled": len([t for t, enabled in config.alert_types_enabled.items() if enabled]),
        "thresholds": {
            "price_change": config.price_change_threshold,
            "arbitrage_margin": config.arbitrage_min_margin_clp,
            "arbitrage_roi": config.arbitrage_min_roi
        },
        "recommendations": []
    }
    
    # Generar recomendaciones
    if not config.enabled:
        diagnosis["recommendations"].append("Habilitar alertas con ALERTS_ENABLED=true")
    
    if config.enabled and not config.telegram_token:
        diagnosis["recommendations"].append("Configurar TELEGRAM_BOT_TOKEN para envío por Telegram")
    
    if config.price_change_threshold < 3.0:
        diagnosis["recommendations"].append("Considerar aumentar price_change_threshold para reducir spam")
    
    return diagnosis