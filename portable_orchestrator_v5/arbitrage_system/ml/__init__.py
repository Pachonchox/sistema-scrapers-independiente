# -*- coding: utf-8 -*-
"""
🧠 ML Module V5 - Sistema ML Autónomo para Arbitraje
==================================================
Módulo completo de Machine Learning para sistema de arbitraje V5.
Completamente autónomo, sin dependencias externas.

Componentes:
- Adaptadores ML para matching, detección de glitches y normalización
- Scoring avanzado con ponderaciones optimizadas
- Detección de anomalías con múltiples niveles
- Normalización inteligente de productos

Compatible con emojis y optimizado para operación continua no supervisada.
"""

from .adapters import (
    MatchScoringAdapter,
    GlitchDetectionAdapter, 
    NormalizationHubAdapter
)

__all__ = [
    'MatchScoringAdapter',
    'GlitchDetectionAdapter',
    'NormalizationHubAdapter'
]

# Configuración ML V5
ML_VERSION = "5.0.0"
ML_COMPONENTS_COUNT = 3

import logging
logger = logging.getLogger(__name__)
logger.info(f"✅ ML Module V5 {ML_VERSION} inicializado - {ML_COMPONENTS_COUNT} componentes")