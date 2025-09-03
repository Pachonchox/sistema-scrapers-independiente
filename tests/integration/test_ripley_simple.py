#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test simplificado de Ripley V5 con método V3
"""

import asyncio
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ripley():
    """Test Ripley con extracción V3"""
    
    try:
        from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
        
        print("\n" + "="*60)
        print("TEST RIPLEY V5 CON MÉTODO V3")
        print("="*60)
        
        # Crear scraper
        scraper = RipleyScraperV5()
        
        # Inicializar browser
        await scraper.initialize()
        
        # Probar categoría computacion
        print("\nScraping Ripley - computacion (30 productos)...")
        
        result = await scraper.scrape_category(
            category='computacion',
            max_products=30
        )
        
        print(f"\nResultado:")
        print(f"- Éxito: {result.success}")  
        print(f"- Productos: {result.total_found}")
        print(f"- Tiempo: {result.execution_time:.1f}s")
        
        if result.products:
            print("\nPrimeros 3 productos:")
            for i, p in enumerate(result.products[:3], 1):
                print(f"\n{i}. {p.title[:60]}")
                print(f"   SKU: {p.sku}")
                print(f"   Marca: {p.brand}")
                print(f"   Precio: ${p.current_price:,.0f}")
                if p.additional_info:
                    if p.additional_info.get('storage'):
                        print(f"   Storage: {p.additional_info['storage']}")
                    if p.additional_info.get('ram'):
                        print(f"   RAM: {p.additional_info['ram']}")
        
        # Cerrar
        await scraper.cleanup()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_ripley())