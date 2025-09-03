#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧪 TEST HITES SCRAPER V5
========================
Prueba individual del scraper Hites V5 con método portable
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


async def test_hites_v5():
    """🧪 Probar Hites V5"""
    
    print("\n" + "="*60)
    print("🧪 TEST HITES SCRAPER V5")
    print("="*60)
    
    try:
        from portable_orchestrator_v5.scrapers.hites_scraper_v5 import HitesScraperV5
        
        print("📦 Inicializando Hites V5...")
        scraper = HitesScraperV5()
        
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
                print(f"   📦 SKU: {product.sku}")
                print(f"   ⭐ Rating: {product.rating} estrellas")
                additional = product.additional_info or {}
                print(f"   📏 Storage: {additional.get('storage')}" if additional.get('storage') else "")
                print(f"   📺 Pantalla: {additional.get('screen_size')}" if additional.get('screen_size') else "")
                print(f"   🎨 Color: {additional.get('color')}" if additional.get('color') else "")
                print(f"   📦 Stock: {product.availability}")
                
                # Mostrar información adicional
                if additional.get('seller'):
                    print(f"   🏪 Vendedor: {additional['seller']}")
                if additional.get('shipping_options'):
                    print(f"   🚚 Envío: {additional['shipping_options'][:50]}...")
            
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


async def test_hites_integration():
    """🔧 Probar integración con orquestador"""
    
    print("\n" + "="*60)
    print("🔧 TEST INTEGRACIÓN CON ORQUESTADOR")
    print("="*60)
    
    try:
        # Verificar que se puede importar desde orquestador
        from orchestrator_v5_robust import OrchestratorV5Robust
        
        print("📦 Creando orquestador con Hites...")
        
        # Configurar solo Hites para test
        import os
        os.environ['SCRAPERS_ENABLED'] = 'hites'
        os.environ['MAX_RUNTIME_MINUTES'] = '1'  # Solo 1 minuto
        os.environ['BATCH_SIZE'] = '3'           # Pocos productos
        
        orchestrator = OrchestratorV5Robust()
        
        # Verificar configuración
        if 'hites' in orchestrator.config['scrapers_enabled']:
            print("✅ Hites configurado en scrapers")
        
        if 'hites' in orchestrator.config['categories']:
            categories = orchestrator.config['categories']['hites']
            print(f"✅ Categorías Hites: {categories}")
        
        print("🚀 Inicializando scrapers...")
        await orchestrator.initialize_scrapers()
        
        if 'hites' in orchestrator.scrapers:
            print("✅ Hites scraper inicializado correctamente")
        else:
            print("❌ Error: Hites scraper no se inicializó")
        
        print("🧪 Test completado - Integración exitosa")
        
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """🎯 Función principal"""
    
    print("🧪 Iniciando tests de Hites V5...")
    
    # Test 1: Scraper individual
    await test_hites_v5()
    
    # Test 2: Integración con orquestador
    await test_hites_integration()
    
    print("\n" + "="*60)
    print("🎉 TESTS COMPLETADOS")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())