# -*- coding: utf-8 -*-
"""
🤖 Sistema de Arbitraje V5 Autónomo
===================================
Sistema de arbitraje completamente integrado con inteligencia V5 avanzada.
Compatible con emojis y optimizado para operación continua no supervisada.

Características principales:
- 🧠 Integración completa con Redis Intelligence System
- ⚡ Cache Inteligente multi-nivel (L1-L4)  
- 🎯 Scheduling basado en tiers de volatilidad
- 📊 Análisis predictivo de oportunidades
- 🔄 Aprendizaje continuo de patrones
- 🚨 Sistema de alertas avanzado
- 💰 Detección de arbitraje en tiempo real
"""

__version__ = "5.0.0"
__author__ = "Sistema V5 Autónomo"

from .core.arbitrage_engine import ArbitrageEngineV5
from .core.opportunity_detector import OpportunityDetectorV5
from .core.ml_integration import MLIntegrationV5
from .schedulers.arbitrage_scheduler import ArbitrageSchedulerV5
from .database.db_manager import DatabaseManagerV5
from .config.arbitrage_config import ArbitrageConfigV5

# Exportar componentes principales
__all__ = [
    'ArbitrageEngineV5',
    'OpportunityDetectorV5', 
    'MLIntegrationV5',
    'ArbitrageSchedulerV5',
    'DatabaseManagerV5',
    'ArbitrageConfigV5'
]

# Configuración global con emojis
ARBITRAGE_CONFIG = {
    'emoji_support': True,
    'v5_integration': True,
    'autonomous_mode': True,
    'intelligence_level': 'advanced'
}