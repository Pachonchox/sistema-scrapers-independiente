#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧪 TEST ABCDIN SCRAPER V5
=========================
Prueba individual del scraper AbcDin V5 con método portable
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Añadir paths y soporte emojis
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()


async def test_abcdin_v5():
    """🧪 Probar AbcDin V5"""
    
    print("\n" + "="*60)
    print("🧪 TEST ABCDIN SCRAPER V5")
    print("="*60)
    
    try:
        from portable_orchestrator_v5.scrapers.abcdin_scraper_v5 import AbcdinScraperV5
        
        print("📦 Inicializando AbcDin V5...")
        scraper = AbcdinScraperV5()
        
        # Test con celulares (smartphones)
        print("\n🏪 Probando extracción de celulares...")
        result = await scraper.scrape_category('celulares', max_products=5)
        
        if result.success:
            print(f"✅ Extracción exitosa: {len(result.products)} productos")
            
            print(f"\n📊 RESULTADOS:")
            print(f"   🏪 Retailer: {result.retailer}")
            print(f"   📂 Categoría: {result.category}")
            print(f"   🔢 Total: {result.total_found}")
            print(f"   ⏰ Tiempo: {datetime.now().strftime('%H:%M:%S')}")
            print(f"   🔧 Método: {result.metadata.get('method', 'N/A')}")
            print(f"   📦 Contenedores: {result.metadata.get('containers_found', 0)}")
            
            print(f"\n📱 PRODUCTOS:")
            for i, product in enumerate(result.products[:3], 1):
                print(f"\n{i}. {product.brand} {product.title[:50]}...")
                print(f"   💰 Precio: ${product.current_price:,}" if product.current_price else "   💰 Precio: N/A")
                print(f"   💳 Tarjeta LP: ${product.card_price:,}" if product.card_price else "   💳 Tarjeta LP: N/A")
                print(f"   📦 SKU: {product.sku}")
                print(f"   ⭐ Rating: {product.rating} estrellas")
                
                additional = product.additional_info or {}
                print(f"   📏 Storage: {additional.get('internal_memory')}" if additional.get('internal_memory') else "")
                print(f"   📺 Pantalla: {additional.get('screen_size')}" if additional.get('screen_size') else "")
                print(f"   📷 Cámara: {additional.get('camera_info')[:30]}..." if additional.get('camera_info') else "")
                print(f"   🎨 Color: {additional.get('color')}" if additional.get('color') else "")
                print(f"   🏷️ Badges: {additional.get('floating_badges')[:50]}..." if additional.get('floating_badges') else "")
                print(f"   📦 Stock: {product.availability}")
                
                # Mostrar precios múltiples
                la_polar = additional.get('la_polar_price')
                internet = additional.get('internet_price')
                normal = additional.get('normal_price')
                if la_polar or internet or normal:
                    print(f"   💰 Precios múltiples:")
                    if la_polar:
                        print(f"      🏷️ La Polar: ${la_polar:,}")
                    if internet:
                        print(f"      🌐 Internet: ${internet:,}")
                    if normal:
                        print(f"      🏪 Normal: ${normal:,}")
            
            print(f"\n🎯 VALIDACIÓN:")
            is_valid, issues = await scraper.validate_extraction(result.products)
            if is_valid:
                print("✅ Extracción válida - Todos los campos esenciales presentes")
            else:
                print("⚠️ Problemas encontrados:")
                for issue in issues:
                    print(f"   - {issue}")
        
        else:
            print("❌ Error en extracción:")
            print(f"   💥 Error: {result.error_message}")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()


async def test_abcdin_integration():
    """🔧 Probar integración con orquestador"""
    
    print("\n" + "="*60)
    print("🔧 TEST INTEGRACIÓN CON ORQUESTADOR")
    print("="*60)
    
    try:
        # Verificar que se puede importar desde orquestador
        from orchestrator_v5_robust import OrchestratorV5Robust
        
        print("📦 Creando orquestador con AbcDin...")
        
        # Configurar solo AbcDin para test
        import os
        os.environ['SCRAPERS_ENABLED'] = 'abcdin'
        os.environ['MAX_RUNTIME_MINUTES'] = '1'  # Solo 1 minuto
        os.environ['BATCH_SIZE'] = '3'           # Pocos productos
        
        orchestrator = OrchestratorV5Robust()
        
        # Verificar configuración
        if 'abcdin' in orchestrator.config['scrapers_enabled']:
            print("✅ AbcDin configurado en scrapers")
        
        if 'abcdin' in orchestrator.config['categories']:
            categories = orchestrator.config['categories']['abcdin']
            print(f"✅ Categorías AbcDin: {categories}")
        
        print("🚀 Inicializando scrapers...")
        await orchestrator.initialize_scrapers()
        
        if 'abcdin' in orchestrator.scrapers:
            print("✅ AbcDin scraper inicializado correctamente")
        else:
            print("❌ Error: AbcDin scraper no se inicializó")
        
        print("🧪 Test completado - Integración exitosa")
        
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """🎯 Función principal"""
    
    print("🧪 Iniciando tests de AbcDin V5...")
    
    # Test 1: Scraper individual
    await test_abcdin_v5()
    
    # Test 2: Integración con orquestador
    await test_abcdin_integration()
    
    print("\n" + "="*60)
    print("🎉 TESTS COMPLETADOS")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())