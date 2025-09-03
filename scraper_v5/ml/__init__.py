# -*- coding: utf-8 -*-
"""
🤖 Módulo ML del Scraper v5 - Sistema de Machine Learning Integrado
=================================================================

Este módulo contiene todos los componentes de Machine Learning:
- Detector de fallos con screenshots y análisis HTML
- Optimizador de proxies con rotación inteligente
- Sistema de tiers con optimización automática
- Métricas y análisis predictivo

Autor: Sistema Scraper v5 🚀
"""

from .failure_detector import MLFailureDetector
from .proxy_optimizer import IntelligentProxyManager

__all__ = [
    'MLFailureDetector',
    'IntelligentProxyManager'
]

__version__ = "1.0.0"