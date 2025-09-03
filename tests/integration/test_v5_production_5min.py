#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Productivo V5 - Flujo Completo 5 Minutos
==============================================
Ejecuta los 3 scrapers principales con todas las integraciones
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Configurar paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'test_production_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_production_flow():
    """Ejecutar test productivo completo"""
    
    print("\n" + "="*80)
    print("TEST PRODUCTIVO V5 - FLUJO COMPLETO")
    print("="*80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Duración objetivo: 5 minutos")
    print("-"*80)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=5)
    
    # Importar scrapers
    from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
    from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
    from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
    
    # Inicializar scrapers
    scrapers = {
        'paris': ParisScraperV5(),
        'ripley': RipleyScraperV5(),
        'falabella': FalabellaScraperV5()
    }
    
    # Categorías a probar
    categories = {
        'paris': ['celulares', 'computadores'],
        'ripley': ['computacion', 'smartphones'],
        'falabella': ['smartphones', 'computadores']
    }
    
    # Estadísticas globales
    stats = {
        'total_products': 0,
        'total_time': 0,
        'retailers_success': [],
        'retailers_failed': [],
        'products_by_retailer': {},
        'errors': []
    }
    
    all_products = []
    
    print("\n=== INICIANDO SCRAPERS ===")
    
    try:
        # Inicializar todos los scrapers
        for retailer, scraper in scrapers.items():
            print(f"\nInicializando {retailer.upper()}...")
            await scraper.initialize()
            print(f"✓ {retailer.upper()} inicializado")
        
        print("\n=== EJECUTANDO CICLOS DE SCRAPING ===")
        
        cycle = 1
        while datetime.now() < end_time:
            cycle_start = datetime.now()
            print(f"\n--- CICLO {cycle} - {cycle_start.strftime('%H:%M:%S')} ---")
            
            # Ejecutar cada scraper
            for retailer, scraper in scrapers.items():
                if datetime.now() >= end_time:
                    break
                    
                retailer_categories = categories[retailer]
                
                for category in retailer_categories:
                    if datetime.now() >= end_time:
                        break
                    
                    try:
                        print(f"\nScraping {retailer.upper()} - {category}...")
                        
                        result = await scraper.scrape_category(
                            category=category,
                            max_products=20  # Límite por categoría para prueba rápida
                        )
                        
                        if result.success:
                            products_count = len(result.products)
                            stats['total_products'] += products_count
                            
                            if retailer not in stats['products_by_retailer']:
                                stats['products_by_retailer'][retailer] = 0
                            stats['products_by_retailer'][retailer] += products_count
                            
                            if retailer not in stats['retailers_success']:
                                stats['retailers_success'].append(retailer)
                            
                            # Guardar productos
                            for product in result.products:
                                all_products.append({
                                    'retailer': retailer,
                                    'category': category,
                                    'title': product.title,
                                    'brand': product.brand,
                                    'sku': product.sku,
                                    'price': product.current_price,
                                    'original_price': product.original_price,
                                    'discount': product.discount_percentage,
                                    'rating': product.rating,
                                    'url': product.product_url,
                                    'timestamp': product.extraction_timestamp
                                })
                            
                            print(f"  ✓ {products_count} productos extraídos")
                            print(f"  Tiempo: {result.execution_time:.1f}s")
                            
                            # Mostrar algunos productos
                            if result.products:
                                print(f"  Muestra: {result.products[0].title[:60]}...")
                                
                        else:
                            print(f"  ✗ Error: {result.error_message}")
                            stats['errors'].append(f"{retailer}-{category}: {result.error_message}")
                            
                    except Exception as e:
                        print(f"  ✗ Error crítico: {e}")
                        stats['errors'].append(f"{retailer}-{category}: {str(e)}")
            
            # Verificar tiempo restante
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = (end_time - datetime.now()).total_seconds()
            
            print(f"\nTiempo transcurrido: {elapsed:.0f}s / Restante: {remaining:.0f}s")
            print(f"Total productos hasta ahora: {stats['total_products']}")
            
            # Pausa entre ciclos
            if remaining > 30:
                print("Esperando 10 segundos antes del siguiente ciclo...")
                await asyncio.sleep(10)
            
            cycle += 1
        
        print("\n=== LIMPIEZA ===")
        
        # Cerrar scrapers
        for retailer, scraper in scrapers.items():
            print(f"Cerrando {retailer.upper()}...")
            await scraper.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n¡Test interrumpido por usuario!")
    except Exception as e:
        logger.error(f"Error general: {e}", exc_info=True)
        stats['errors'].append(f"Error general: {str(e)}")
    
    # Calcular estadísticas finales
    stats['total_time'] = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    
    print(f"\nTiempo total de ejecución: {stats['total_time']:.1f} segundos")
    print(f"Total de productos extraídos: {stats['total_products']}")
    
    print("\nProductos por retailer:")
    for retailer, count in stats['products_by_retailer'].items():
        print(f"  {retailer.upper()}: {count} productos")
    
    print(f"\nRetailers exitosos: {', '.join([r.upper() for r in stats['retailers_success']])}")
    
    if stats['errors']:
        print(f"\nErrores encontrados ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:  # Mostrar solo primeros 5 errores
            print(f"  - {error}")
    
    # Guardar resultados en Excel
    if all_products:
        filename = f"test_production_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df = pd.DataFrame(all_products)
        df.to_excel(filename, index=False)
        print(f"\nResultados guardados en: {filename}")
        
        # Estadísticas adicionales
        print("\nEstadísticas de productos:")
        print(f"  Precio promedio: ${df['price'].mean():,.0f}")
        print(f"  Precio mínimo: ${df['price'].min():,.0f}")
        print(f"  Precio máximo: ${df['price'].max():,.0f}")
        print(f"  Descuento promedio: {df['discount'].mean():.1f}%")
        
        # Top marcas
        top_brands = df['brand'].value_counts().head(5)
        print("\nTop 5 marcas:")
        for brand, count in top_brands.items():
            print(f"  {brand}: {count} productos")
    
    # Verificación de sistemas
    print("\n=== VERIFICACIÓN DE SISTEMAS ===")
    
    # Verificar ML
    try:
        from portable_orchestrator_v5.ml.failure_detector import FailureDetector
        print("✓ Sistema ML de detección de fallos: OK")
    except:
        print("✗ Sistema ML de detección de fallos: No disponible")
    
    # Verificar Field Mapper
    try:
        from portable_orchestrator_v5.core.field_mapper import FieldMapperV5
        print("✓ Field Mapper ETL: OK")
    except:
        print("✗ Field Mapper ETL: No disponible")
    
    # Verificar Tier System
    try:
        from portable_orchestrator_v5.core.tier_manager import TierManager
        print("✓ Sistema de Tiers: OK")
    except:
        print("✗ Sistema de Tiers: No disponible")
    
    print("\n" + "="*80)
    print("TEST COMPLETADO")
    print(f"Hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return stats

if __name__ == "__main__":
    print("Iniciando test productivo de 5 minutos...")
    print("Presiona Ctrl+C para detener en cualquier momento")
    
    try:
        stats = asyncio.run(test_production_flow())
        
        if stats['total_products'] > 0:
            print(f"\n✅ TEST EXITOSO - {stats['total_products']} productos en {stats['total_time']:.0f}s")
        else:
            print("\n⚠️ TEST SIN PRODUCTOS - Revisar logs para más detalles")
            
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()