# -*- coding: utf-8 -*-
"""
🏪 Scrapers por Retailer - Adaptados del Sistema v3 Original
===========================================================

Scrapers adaptados mínimamente del sistema v3 existente para
integración con el sistema v5. Mantiene la lógica de scraping
original con nuevas capacidades v5.

Retailers soportados (adaptados del v3):
- Ripley Chile - Con scroll lento y selectores v3
- Falabella Chile - Lógica original mantenida
- Paris Chile - Selectores originales
- Hites Chile - Comportamiento v3 preservado
- AbcDin Chile - Funcionalidad original
- MercadoLibre Chile - Adaptación mínima

Autor: Sistema Scraper v5 🚀 (Basado en v3 existente)
"""

from .ripley_scraper_v5 import RipleyScraperV5
from .falabella_scraper_v5 import FalabellaScraperV5
from .paris_scraper_v5 import ParisScraperV5
from .hites_scraper_v5 import HitesScraperV5
from .abcdin_scraper_v5 import AbcdinScraperV5
from .mercadolibre_scraper_v5 import MercadoLibreScraperV5

__all__ = [
    'RipleyScraperV5',
    'FalabellaScraperV5', 
    'ParisScraperV5',
    'HitesScraperV5',
    'AbcdinScraperV5',
    'MercadoLibreScraperV5'
]

# Mapping de retailers a clases (compatibilidad v5)
SCRAPER_REGISTRY = {
    'ripley': RipleyScraperV5,
    'falabella': FalabellaScraperV5,
    'paris': ParisScraperV5,
    'hites': HitesScraperV5,
    'abcdin': AbcdinScraperV5,
    'mercadolibre': MercadoLibreScraperV5
}

def get_scraper_class(retailer: str):
    """🔍 Obtener clase de scraper por nombre de retailer"""
    return SCRAPER_REGISTRY.get(retailer.lower())

__version__ = "1.0.0"