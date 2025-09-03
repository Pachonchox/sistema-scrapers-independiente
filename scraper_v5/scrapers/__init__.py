# -*- coding: utf-8 -*-
"""
🏪 Scrapers por Retailer - Sistema de Scraping Específico
========================================================

Módulo que contiene scrapers especializados para cada retailer chileno.
Cada scraper hereda del BaseScraperV5 y implementa selectores y lógica específica.

Retailers soportados:
- Ripley Chile
- Falabella Chile  
- Paris Chile
- Hites Chile
- AbcDin Chile
- MercadoLibre Chile

Autor: Sistema Scraper v5 🚀
"""

from .ripley_scraper import RipleyScraper
from .falabella_scraper import FalabellaScraper
from .paris_scraper import ParisScraper
from .hites_scraper import HitesScraper
from .abcdin_scraper import AbcdinScraper
from .mercadolibre_scraper import MercadoLibreScraper

__all__ = [
    'RipleyScraper',
    'FalabellaScraper', 
    'ParisScraper',
    'HitesScraper',
    'AbcdinScraper',
    'MercadoLibreScraper'
]

# Mapping de retailers a clases
SCRAPER_REGISTRY = {
    'ripley': RipleyScraper,
    'falabella': FalabellaScraper,
    'paris': ParisScraper,
    'hites': HitesScraper,
    'abcdin': AbcdinScraper,
    'mercadolibre': MercadoLibreScraper
}

def get_scraper_class(retailer: str):
    """🔍 Obtener clase de scraper por nombre de retailer"""
    return SCRAPER_REGISTRY.get(retailer.lower())

__version__ = "1.0.0"