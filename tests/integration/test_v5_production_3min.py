#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Productivo V5 - 3 Minutos
===============================
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# Configurar logging sin emojis
logging.basicConfig(
    level=logging.WARNING,  # Reducir nivel de logging
    format='%(asctime)s - %(name)s - %(message)s'
)

async def test_production():
    """Test productivo de 3 minutos"""
    
    print("\n" + "="*60)
    print("TEST PRODUCTIVO V5 - 3 MINUTOS")
    print("="*60)
    print(f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=3)
    
    # Importar scrapers
    from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
    from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
    from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
    
    # Configuración
    scrapers_config = [
        ('paris', ParisScraperV5(), 'celulares'),
        ('ripley', RipleyScraperV5(), 'computacion'),
        ('falabella', FalabellaScraperV5(), 'smartphones')
    ]
    
    stats = {
        'total_products': 0,
        'results_by_retailer': {}
    }
    
    all_products = []
    
    print("\n=== INICIALIZANDO SCRAPERS ===")
    
    # Inicializar
    for retailer, scraper, _ in scrapers_config:
        print(f"Inicializando {retailer}...")
        await scraper.initialize()
        print(f"[OK] {retailer} listo")
    
    print("\n=== EJECUTANDO SCRAPERS ===")
    
    cycle = 1
    while datetime.now() < end_time:
        print(f"\n--- CICLO {cycle} ---")
        
        for retailer, scraper, category in scrapers_config:
            if datetime.now() >= end_time:
                break
            
            try:
                print(f"\n{retailer.upper()} - {category}:")
                
                result = await scraper.scrape_category(
                    category=category,
                    max_products=15
                )
                
                if result.success:
                    products_count = len(result.products)
                    stats['total_products'] += products_count
                    
                    if retailer not in stats['results_by_retailer']:
                        stats['results_by_retailer'][retailer] = []
                    
                    stats['results_by_retailer'][retailer].append({
                        'category': category,
                        'count': products_count,
                        'time': result.execution_time
                    })
                    
                    # Guardar productos
                    for product in result.products:
                        all_products.append({
                            'retailer': retailer,
                            'category': category,
                            'title': product.title[:100],
                            'brand': product.brand,
                            'sku': product.sku,
                            'price': product.current_price,
                            'discount': product.discount_percentage,
                            'timestamp': datetime.now()
                        })
                    
                    print(f"  Productos: {products_count}")
                    print(f"  Tiempo: {result.execution_time:.1f}s")
                    
                    # Mostrar muestra
                    if result.products:
                        sample = result.products[0]
                        print(f"  Ejemplo: {sample.title[:50]}...")
                        print(f"  Precio: ${sample.current_price:,.0f}")
                else:
                    print(f"  Error: {result.error_message}")
                    
            except Exception as e:
                print(f"  Error critico: {e}")
        
        # Tiempo restante
        elapsed = (datetime.now() - start_time).total_seconds()
        remaining = (end_time - datetime.now()).total_seconds()
        
        print(f"\nProgreso: {elapsed:.0f}s transcurridos, {remaining:.0f}s restantes")
        print(f"Total productos: {stats['total_products']}")
        
        if remaining > 20:
            print("Esperando 10 segundos...")
            await asyncio.sleep(10)
        else:
            break
        
        cycle += 1
    
    print("\n=== CERRANDO SCRAPERS ===")
    
    for retailer, scraper, _ in scrapers_config:
        print(f"Cerrando {retailer}...")
        await scraper.cleanup()
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\nTiempo total: {total_time:.1f} segundos")
    print(f"Total productos: {stats['total_products']}")
    
    print("\nPor retailer:")
    for retailer, results in stats['results_by_retailer'].items():
        total = sum(r['count'] for r in results)
        avg_time = sum(r['time'] for r in results) / len(results) if results else 0
        print(f"  {retailer.upper()}: {total} productos, {avg_time:.1f}s promedio")
    
    # Guardar Excel
    if all_products:
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df = pd.DataFrame(all_products)
        df.to_excel(filename, index=False)
        print(f"\nResultados guardados en: {filename}")
        
        # Estadísticas
        print("\nEstadísticas de precios:")
        print(f"  Promedio: ${df['price'].mean():,.0f}")
        print(f"  Mínimo: ${df['price'].min():,.0f}")
        print(f"  Máximo: ${df['price'].max():,.0f}")
        
        # Top marcas
        if 'brand' in df.columns:
            top_brands = df['brand'].value_counts().head(3)
            print("\nTop 3 marcas:")
            for brand, count in top_brands.items():
                if brand:
                    print(f"  {brand}: {count}")
    
    # Verificar sistemas
    print("\n=== SISTEMAS COMPLEMENTARIOS ===")
    
    try:
        from portable_orchestrator_v5.core.field_mapper import FieldMapperV5
        print("[OK] Field Mapper ETL")
    except:
        print("[--] Field Mapper ETL no disponible")
    
    try:
        from portable_orchestrator_v5.ml.failure_detector import FailureDetector
        print("[OK] ML Failure Detector")
    except:
        print("[--] ML Failure Detector no disponible")
    
    print("\n" + "="*60)
    print(f"TEST COMPLETADO - {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    return stats

if __name__ == "__main__":
    print("Iniciando test productivo de 3 minutos...")
    
    try:
        stats = asyncio.run(test_production())
        
        if stats['total_products'] > 0:
            print(f"\nRESULTADO: EXITOSO")
            print(f"Total: {stats['total_products']} productos extraidos")
        else:
            print("\nRESULTADO: SIN PRODUCTOS")
            
    except Exception as e:
        print(f"\nERROR: {e}")