# -*- coding: utf-8 -*-
"""
🏗️ Core Components - Componentes Centrales del Sistema
======================================================

Módulo core que contiene los componentes fundamentales del
Sistema Scraper v5:

- Orquestador central
- Base scraper con ML
- Sistema de excepciones
- Field mapper para ETL
- Utilitarios comunes

Autor: Sistema Scraper v5 🚀
"""

from .orchestrator import ScraperV5Orchestrator
from .base_scraper import BaseScraperV5, ProductData, ScrapingResult
from .exceptions import *
from .field_mapper import ETLFieldMapper

__all__ = [
    'ScraperV5Orchestrator',
    'BaseScraperV5',
    'ProductData',
    'ScrapingResult',
    'ETLFieldMapper'
]
