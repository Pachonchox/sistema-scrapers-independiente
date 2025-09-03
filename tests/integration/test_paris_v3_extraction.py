#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Paris V5 con extracción idéntica a V3
==========================================
Prueba el scraper de Paris V5 usando el método exacto de V3 con data attributes
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Agregar paths al sistema
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_paris_extraction():
    """Probar extracción de Paris con método V3"""
    
    print("\n" + "="*80)
    print("TEST PARIS V5 - EXTRACCIÓN IDÉNTICA A V3")
    print("="*80 + "\n")
    
    try:
        from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
        from portable_orchestrator_v5.core.browser_manager import BrowserManagerV5
        
        # Inicializar browser manager
        browser_manager = BrowserManagerV5()
        await browser_manager.initialize()
        
        # Inicializar scraper
        scraper = ParisScraperV5()
        scraper.browser_manager = browser_manager
        
        # Probar con categoría celulares (30 productos)
        print("Iniciando scraping de Paris - Categoría: celulares")
        print("-" * 40)
        
        result = await scraper.scrape_category(
            category='celulares',
            max_products=30
        )
        
        print(f"\nResultado del scraping:")
        print(f"- Éxito: {result.success}")
        print(f"- Productos extraídos: {result.total_found}")
        print(f"- Tiempo de ejecución: {result.execution_time:.2f}s")
        
        if result.products:
            print(f"\nPrimeros 5 productos extraídos:")
            print("-" * 40)
            
            for i, product in enumerate(result.products[:5], 1):
                print(f"\n{i}. {product.title[:80]}")
                print(f"   SKU: {product.sku}")
                print(f"   Marca: {product.brand}")
                print(f"   Precio: ${product.current_price:,.0f}")
                print(f"   URL: {product.product_url[:80] if product.product_url else 'N/A'}")
                
                # Mostrar info adicional si existe
                if product.additional_info:
                    if product.additional_info.get('storage'):
                        print(f"   Storage: {product.additional_info['storage']}")
                    if product.additional_info.get('ram'):
                        print(f"   RAM: {product.additional_info['ram']}")
        else:
            print("\nNo se extrajeron productos")
            if result.error_message:
                print(f"Error: {result.error_message}")
        
        # Guardar resultados
        if result.products:
            filename = f"paris_test_v3_method_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("PRODUCTOS EXTRAÍDOS CON MÉTODO V3\n")
                f.write("="*50 + "\n\n")
                
                for i, product in enumerate(result.products, 1):
                    f.write(f"{i}. {product.title}\n")
                    f.write(f"   SKU: {product.sku}\n")
                    f.write(f"   Precio: ${product.current_price:,.0f}\n")
                    f.write(f"   Marca: {product.brand}\n")
                    f.write("-"*30 + "\n")
            
            print(f"\nResultados guardados en: {filename}")
        
        # Cerrar browser
        await browser_manager.close()
        
    except Exception as e:
        logger.error(f"Error en test: {e}", exc_info=True)
        print(f"\nError: {e}")

if __name__ == "__main__":
    print("Iniciando test de Paris V5 con método V3...")
    asyncio.run(test_paris_extraction())