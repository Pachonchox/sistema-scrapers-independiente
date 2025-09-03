# -*- coding: utf-8 -*-
"""
🚀 Portable Orchestrator v5 - Sistema de Scraping de Nueva Generación
=====================================================================

Sistema de scraping avanzado con Machine Learning integrado para
e-commerce chileno. Proyecto completamente independiente con arquitectura
robusta, escalable y profesional.

Características principales:
- 🧠 ML integrado para detección de fallos y optimización
- 🌐 Gestión inteligente de proxies
- 🏪 Scrapers especializados por retailer (adaptados del v3)
- 🔧 Sistema de testing integrado
- ⚖️ Orquestador con sistema de tiers
- 📊 ETL con reducción inteligente de campos
- 🛡️ Manejo robusto de excepciones

Retailers soportados:
- Ripley Chile ✅ (Completamente funcional)
- Falabella Chile ✅ (Adaptado del v3)
- Paris Chile ✅ (Adaptado del v3)
- Hites Chile 🔜 (En desarrollo)
- AbcDin Chile 🔜 (En desarrollo)
- MercadoLibre Chile 🔜 (En desarrollo)

Autor: Sistema Scraper v5 🚀
Versión: 1.0.0
Fecha: 2025-01-03
Proyecto: Completamente independiente
"""

__version__ = "1.0.0"
__author__ = "Sistema Scraper v5"
__email__ = "scraper-v5@example.com"
__status__ = "Production Ready"
__project__ = "Portable Orchestrator v5"
__description__ = "Sistema de scraping ML integrado independiente"

# Importaciones principales del sistema
from .core.orchestrator import ScraperV5Orchestrator
from .core.base_scraper import BaseScraperV5
from .testing.test_runner import RetailerTestRunner
from .testing.maintenance_tools import MaintenanceToolkit

# Registry de scrapers disponibles
from .scrapers import SCRAPER_REGISTRY, get_scraper_class

__all__ = [
    'ScraperV5Orchestrator',
    'BaseScraperV5', 
    'RetailerTestRunner',
    'MaintenanceToolkit',
    'SCRAPER_REGISTRY',
    'get_scraper_class'
]