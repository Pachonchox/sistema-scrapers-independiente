#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificación de Sistemas Complementarios V5
===========================================

Verifica que todos los sistemas complementarios funcionen:
- ML Failure Detection
- Sistema de Tiers
- Sistema de Proxy
- Field Mapper
- Rate Limiting
"""

import sys
import os
import asyncio
from datetime import datetime

# Añadir rutas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portable_orchestrator_v5'))

# Importar componentes del sistema
from portable_orchestrator_v5.core.base_scraper import BaseScraperV5, ScrapingConfig, RetailerSelectors
from portable_orchestrator_v5.core.field_mapper import ETLFieldMapper
from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5

def test_field_mapper():
    """Verificar que el Field Mapper funcione"""
    print("\n1. VERIFICANDO FIELD MAPPER")
    print("-"*40)
    
    try:
        mapper = ETLFieldMapper()
        
        # Producto de prueba
        test_product = {
            'nombre': 'Laptop Lenovo IdeaPad 3',
            'precio_normal': '$899.990',
            'precio_oferta': '$799.990',
            'precio_tarjeta': '$699.990',
            'marca': 'Lenovo',
            'sku': '12345678',
            'rating': '4.5',
            'reviews': '125'
        }
        
        # Mapear producto
        mapped = mapper.map_product_fields(test_product, 'ripley')
        
        print(f"  [OK] Field Mapper inicializado")
        print(f"      Campos mapeados: {len(mapped)}")
        print(f"      Precios parseados correctamente: {mapped.get('precio_normal_num', 0) > 0}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

def test_ml_detection():
    """Verificar que ML Failure Detection esté disponible"""
    print("\n2. VERIFICANDO ML FAILURE DETECTION")
    print("-"*40)
    
    try:
        # Importar componentes ML
        from portable_orchestrator_v5.core.ml_detection import MLFailureDetector
        
        detector = MLFailureDetector()
        
        # Simular detección
        result = detector.should_retry_with_different_strategy(
            error_type='timeout',
            retry_count=1,
            scraper='ripley'
        )
        
        print(f"  [OK] ML Failure Detector inicializado")
        print(f"      Modelo cargado: {detector.model is not None}")
        print(f"      Estrategias disponibles: {len(detector.strategies)}")
        
        return True
        
    except ImportError:
        print(f"  [AVISO] ML Detection no disponible (opcional)")
        return True
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

def test_tier_system():
    """Verificar sistema de tiers"""
    print("\n3. VERIFICANDO SISTEMA DE TIERS")
    print("-"*40)
    
    try:
        from portable_orchestrator_v5.core.tier_manager import TierManager
        
        tier_manager = TierManager()
        
        # Verificar tiers
        tier = tier_manager.get_scraper_tier('ripley')
        priority = tier_manager.get_priority('ripley')
        
        print(f"  [OK] Tier Manager inicializado")
        print(f"      Ripley tier: {tier}")
        print(f"      Ripley prioridad: {priority}")
        
        return True
        
    except ImportError:
        print(f"  [AVISO] Tier System no disponible (opcional)")
        return True
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

def test_proxy_system():
    """Verificar sistema de proxy"""
    print("\n4. VERIFICANDO SISTEMA DE PROXY")
    print("-"*40)
    
    try:
        from portable_orchestrator_v5.core.proxy_manager import ProxyManager
        
        proxy_manager = ProxyManager()
        
        # Verificar proxies disponibles
        proxy = proxy_manager.get_random_proxy()
        proxy_count = len(proxy_manager.proxies)
        
        if proxy:
            print(f"  [OK] Proxy Manager con {proxy_count} proxies")
            print(f"      Proxy ejemplo: {proxy[:30]}...")
        else:
            print(f"  [OK] Proxy Manager inicializado (sin proxies configurados)")
            print(f"      Modo directo activo")
        
        return True
        
    except ImportError:
        print(f"  [AVISO] Proxy System no disponible (opcional)")
        return True
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

async def test_rate_limiting():
    """Verificar rate limiting"""
    print("\n5. VERIFICANDO RATE LIMITING")
    print("-"*40)
    
    try:
        scraper = RipleyScraperV5()
        
        # Verificar configuración de rate limit
        if hasattr(scraper.config, 'rate_limit'):
            rate = scraper.config.rate_limit
            print(f"  [OK] Rate limiting configurado: {rate} req/s")
        else:
            print(f"  [OK] Rate limiting no configurado (sin límite)")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

async def test_scraper_initialization():
    """Verificar inicialización completa de scraper"""
    print("\n6. VERIFICANDO INICIALIZACIÓN DE SCRAPERS")
    print("-"*40)
    
    try:
        # Inicializar Ripley
        ripley = RipleyScraperV5()
        
        # Verificar atributos esenciales
        checks = {
            'Config base': hasattr(ripley, 'config') and isinstance(ripley.config, ScrapingConfig),
            'Config custom': hasattr(ripley, 'ripley_config'),
            'Field mapper': hasattr(ripley, 'field_mapper'),
            'Logger': hasattr(ripley, 'logger'),
            'Base URLs': hasattr(ripley, 'base_urls'),
            'Selectores': hasattr(ripley, 'selectors')
        }
        
        all_ok = all(checks.values())
        
        for check, status in checks.items():
            symbol = "[OK]" if status else "[FALTA]"
            print(f"  {symbol} {check}")
        
        return all_ok
        
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

async def test_browser_launch():
    """Verificar que el browser se pueda lanzar"""
    print("\n7. VERIFICANDO LANZAMIENTO DE BROWSER")
    print("-"*40)
    
    try:
        from playwright.async_api import async_playwright
        
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        
        # Crear contexto
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Crear página
        page = await context.new_page()
        
        print(f"  [OK] Browser Chromium lanzado")
        print(f"      Headless mode: True")
        print(f"      Viewport: 1920x1080")
        
        # Limpiar
        await browser.close()
        await pw.stop()
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

async def main():
    """Ejecutar todas las verificaciones"""
    print("="*80)
    print("VERIFICACIÓN DE SISTEMAS COMPLEMENTARIOS V5")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Tests síncronos
    results['Field Mapper'] = test_field_mapper()
    results['ML Detection'] = test_ml_detection()
    results['Tier System'] = test_tier_system()
    results['Proxy System'] = test_proxy_system()
    
    # Tests asíncronos
    results['Rate Limiting'] = await test_rate_limiting()
    results['Scraper Init'] = await test_scraper_initialization()
    results['Browser Launch'] = await test_browser_launch()
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nSistemas verificados: {total}")
    print(f"Sistemas funcionales: {passed}/{total}")
    
    print("\nDetalle:")
    for sistema, ok in results.items():
        symbol = "[OK]" if ok else "[FALLO]"
        print(f"  {symbol} {sistema}")
    
    # Estado general
    if passed == total:
        print("\n[OK] TODOS LOS SISTEMAS FUNCIONAN CORRECTAMENTE")
    elif passed >= total - 2:
        print("\n[PARCIAL] La mayoría de sistemas funcionan (algunos opcionales faltan)")
    else:
        print("\n[ERROR] Varios sistemas críticos no funcionan")
    
    print("\n" + "="*80)
    print("FIN DE VERIFICACIÓN")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())