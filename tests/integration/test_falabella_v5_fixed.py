#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Falabella V5 con método del portable
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

async def test_falabella_fixed():
    """Test Falabella V5 corregido"""
    
    try:
        from portable_orchestrator_v5.scrapers.falabella_scraper_v5_fixed import FalabellaScraperV5
        
        print("\n" + "="*60)
        print("TEST FALABELLA V5 - MÉTODO PORTABLE")
        print("="*60)
        
        scraper = FalabellaScraperV5()
        await scraper.initialize()
        
        print("\nScraping Falabella - smartphones...")
        print("Usando método exacto del portable scraper")
        print("-" * 40)
        
        result = await scraper.scrape_category(
            category='smartphones',
            max_products=30
        )
        
        print(f"\n=== RESULTADO ===")
        print(f"Éxito: {result.success}")  
        print(f"Productos extraídos: {result.total_found}")
        print(f"Tiempo: {result.execution_time:.1f}s")
        
        if result.products:
            print(f"\n=== PRIMEROS 5 PRODUCTOS ===")
            for i, p in enumerate(result.products[:5], 1):
                sponsored = "[PATROCINADO] " if p.additional_info.get('is_sponsored') else ""
                print(f"\n{i}. {sponsored}{p.title}")
                print(f"   SKU/ID: {p.sku}")
                print(f"   Marca: {p.brand}")
                print(f"   Precio: ${p.current_price:,.0f}")
                print(f"   Rating: {p.rating} ({p.additional_info.get('reviews_count', 0)} reviews)")
                if p.additional_info.get('seller'):
                    print(f"   Vendedor: {p.additional_info['seller']}")
                if p.additional_info.get('storage'):
                    print(f"   Storage: {p.additional_info['storage']}")
                if p.additional_info.get('badges'):
                    print(f"   Badges: {', '.join(p.additional_info['badges'][:3])}")
        else:
            print("\nNo se extrajeron productos")
            if result.error_message:
                print(f"Error: {result.error_message}")
        
        await scraper.cleanup()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Iniciando test de Falabella V5 con método portable...")
    asyncio.run(test_falabella_fixed())