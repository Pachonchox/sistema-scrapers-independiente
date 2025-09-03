#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Falabella V5 con smartphones
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def test_falabella():
    """Test Falabella con smartphones"""
    
    try:
        from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
        
        print("\n" + "="*60)
        print("TEST FALABELLA V5 - SMARTPHONES")
        print("="*60)
        
        scraper = FalabellaScraperV5()
        await scraper.initialize()
        
        print("\nScraping Falabella - smartphones (20 productos)...")
        
        result = await scraper.scrape_category(
            category='smartphones',
            max_products=20
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
                print(f"   Precio: ${p.current_price:,.0f}")
        
        await scraper.cleanup()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_falabella())