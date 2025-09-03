# -*- coding: utf-8 -*-
"""
Scraper v5 - Advanced ML-Driven Web Scraping System
===================================================

Professional, scalable and intelligent scraping framework with:
- 🧪 INTEGRATED TESTING FRAMEWORK
- 🔍 Retailer-specific test suites
- 🛠️ Maintenance and debugging tools
- 🤖 ML-powered failure detection and recovery
- 🌐 Intelligent proxy management with scoring
- ⚡ Dynamic tier optimization system  
- 📂 Smart category management
- 📊 ETL-optimized field reduction
- 📈 Advanced monitoring and debugging

Author: Portable Orchestrator Team
Version: 5.0.0
"""

__version__ = "5.0.0"
__author__ = "Portable Orchestrator Team"

# Import main components
from .core.orchestrator import ScraperV5Orchestrator
from .core.base_scraper import BaseScraperV5
from .testing.test_runner import RetailerTestRunner
from .testing.maintenance_tools import MaintenanceToolkit

__all__ = [
    'ScraperV5Orchestrator',
    'BaseScraperV5',
    'RetailerTestRunner', 
    'MaintenanceToolkit'
]