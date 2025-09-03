#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis de Problemas de Configuración en Scrapers V5
======================================================

Este script analiza todos los problemas encontrados en los scrapers v5
y genera un reporte detallado con soluciones.
"""

import sys
import os
import importlib
import traceback
from datetime import datetime
from pathlib import Path

# Añadir paths necesarios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portable_orchestrator_v5'))

def check_dependencies():
    """Verificar dependencias necesarias"""
    dependencies = {
        'playwright': False,
        'beautifulsoup4': False,
        'pandas': False,
        'aiohttp': False,
        'psycopg2': False,
        'python-dotenv': False
    }
    
    for dep in dependencies:
        try:
            if dep == 'beautifulsoup4':
                importlib.import_module('bs4')
            elif dep == 'python-dotenv':
                importlib.import_module('dotenv')
            else:
                importlib.import_module(dep)
            dependencies[dep] = True
        except ImportError:
            dependencies[dep] = False
    
    return dependencies

def analyze_scraper_imports():
    """Analizar problemas de imports en cada scraper"""
    scrapers = [
        'ripley_scraper_v5',
        'falabella_scraper_v5', 
        'paris_scraper_v5',
        'mercadolibre_scraper_v5',
        'hites_scraper_v5',
        'abcdin_scraper_v5'
    ]
    
    import_status = {}
    
    for scraper in scrapers:
        try:
            module = importlib.import_module(f'portable_orchestrator_v5.scrapers.{scraper}')
            
            # Verificar clase principal
            class_name = f"{scraper.split('_')[0].capitalize()}ScraperV5"
            if hasattr(module, class_name):
                scraper_class = getattr(module, class_name)
                
                # Verificar métodos principales
                methods = {
                    'scrape_category': hasattr(scraper_class, 'scrape_category'),
                    'search_products': hasattr(scraper_class, 'search_products'),
                    '__init__': hasattr(scraper_class, '__init__')
                }
                
                import_status[scraper] = {
                    'status': 'OK',
                    'class_found': True,
                    'methods': methods
                }
            else:
                import_status[scraper] = {
                    'status': 'ERROR',
                    'error': f"Clase {class_name} no encontrada"
                }
                
        except Exception as e:
            import_status[scraper] = {
                'status': 'ERROR',
                'error': str(e)[:100]
            }
    
    return import_status

def test_scraper_initialization():
    """Probar inicialización de cada scraper"""
    from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
    from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
    from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
    from portable_orchestrator_v5.scrapers.mercadolibre_scraper_v5 import MercadoLibreScraperV5
    from portable_orchestrator_v5.scrapers.hites_scraper_v5 import HitesScraperV5
    from portable_orchestrator_v5.scrapers.abcdin_scraper_v5 import AbcdinScraperV5
    
    scrapers_config = [
        (RipleyScraperV5, 'ripley'),
        (FalabellaScraperV5, 'falabella'),
        (ParisScraperV5, 'paris'),
        (MercadoLibreScraperV5, 'mercadolibre'),
        (HitesScraperV5, 'hites'),
        (AbcdinScraperV5, 'abcdin')
    ]
    
    init_status = {}
    
    for scraper_class, name in scrapers_config:
        try:
            scraper = scraper_class()
            
            # Verificar atributos necesarios
            attributes = {
                'name': hasattr(scraper, 'name'),
                'base_urls': hasattr(scraper, 'base_urls'),
                'selectors': hasattr(scraper, 'selectors'),
                'config': hasattr(scraper, 'config'),
                'field_mapper': hasattr(scraper, 'field_mapper')
            }
            
            init_status[name] = {
                'status': 'OK',
                'instance_created': True,
                'attributes': attributes
            }
            
        except Exception as e:
            init_status[name] = {
                'status': 'ERROR',
                'error': str(e),
                'traceback': traceback.format_exc()[:500]
            }
    
    return init_status

def analyze_browser_config():
    """Analizar configuración del browser"""
    issues = []
    
    # Verificar si Playwright está instalado
    try:
        from playwright.async_api import async_playwright
        issues.append({
            'component': 'Playwright',
            'status': 'OK',
            'message': 'Playwright importado correctamente'
        })
    except ImportError:
        issues.append({
            'component': 'Playwright',
            'status': 'ERROR',
            'message': 'Playwright no está instalado',
            'solution': 'pip install playwright && playwright install'
        })
    
    # Verificar browsers instalados
    try:
        import subprocess
        result = subprocess.run(['playwright', 'show-trace'], capture_output=True, text=True)
        if 'command not found' not in result.stderr:
            issues.append({
                'component': 'Playwright Browsers',
                'status': 'OK',
                'message': 'Browsers de Playwright instalados'
            })
        else:
            raise Exception("Playwright CLI no encontrado")
    except:
        issues.append({
            'component': 'Playwright Browsers',
            'status': 'WARNING',
            'message': 'No se pudo verificar instalación de browsers',
            'solution': 'playwright install chromium'
        })
    
    return issues

def analyze_specific_errors():
    """Analizar errores específicos encontrados"""
    errors = [
        {
            'error': "'dict' object has no attribute 'user_agents'",
            'location': 'Browser configuration',
            'cause': 'ScrapingConfig no está siendo inicializado correctamente',
            'solution': 'Verificar que ScrapingConfig se inicialice con user_agents lista'
        },
        {
            'error': "'NoneType' object has no attribute 'set_viewport_size'",
            'location': 'Page initialization',
            'cause': 'El browser/page no se está creando correctamente',
            'solution': 'Verificar que Playwright esté instalado y los browsers descargados'
        },
        {
            'error': "Categoría no soportada",
            'location': 'Category mapping',
            'cause': 'Las categorías no coinciden con las esperadas por el scraper',
            'solution': 'Usar categorías válidas: computacion, celulares, electrohogar, etc.'
        },
        {
            'error': "scraper pendiente de adaptación",
            'location': 'MercadoLibre, Hites, AbcDin',
            'cause': 'Estos scrapers son placeholders sin implementación real',
            'solution': 'Implementar la lógica de scraping o usar scrapers v3/v4 existentes'
        }
    ]
    
    return errors

def generate_report():
    """Generar reporte completo"""
    print("="*80)
    print("REPORTE DE PROBLEMAS DE CONFIGURACIÓN - SCRAPERS V5")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Verificar dependencias
    print("1. VERIFICACIÓN DE DEPENDENCIAS")
    print("-"*40)
    deps = check_dependencies()
    for dep, installed in deps.items():
        status = "[OK]" if installed else "[FALTA]"
        print(f"  {status} {dep}")
    
    missing = [d for d, i in deps.items() if not i]
    if missing:
        print(f"\n  [ACCIÓN REQUERIDA] Instalar dependencias faltantes:")
        print(f"  pip install {' '.join(missing)}")
    
    # 2. Analizar imports de scrapers
    print("\n2. ANÁLISIS DE IMPORTS DE SCRAPERS")
    print("-"*40)
    imports = analyze_scraper_imports()
    for scraper, status in imports.items():
        if status['status'] == 'OK':
            print(f"  [OK] {scraper}")
            for method, exists in status.get('methods', {}).items():
                symbol = "✓" if exists else "✗"
                print(f"      {symbol} {method}")
        else:
            print(f"  [ERROR] {scraper}: {status.get('error', 'Unknown')}")
    
    # 3. Probar inicialización
    print("\n3. PRUEBA DE INICIALIZACIÓN")
    print("-"*40)
    init_results = test_scraper_initialization()
    for scraper, result in init_results.items():
        if result['status'] == 'OK':
            print(f"  [OK] {scraper} - Instancia creada")
            missing_attrs = [a for a, e in result['attributes'].items() if not e]
            if missing_attrs:
                print(f"      [AVISO] Atributos faltantes: {', '.join(missing_attrs)}")
        else:
            print(f"  [ERROR] {scraper}")
            print(f"      Error: {result.get('error', 'Unknown')[:100]}")
    
    # 4. Configuración del browser
    print("\n4. CONFIGURACIÓN DEL BROWSER")
    print("-"*40)
    browser_issues = analyze_browser_config()
    for issue in browser_issues:
        status = f"[{issue['status']}]"
        print(f"  {status} {issue['component']}: {issue['message']}")
        if 'solution' in issue:
            print(f"      Solución: {issue['solution']}")
    
    # 5. Errores específicos encontrados
    print("\n5. ERRORES ESPECÍFICOS IDENTIFICADOS")
    print("-"*40)
    errors = analyze_specific_errors()
    for i, error in enumerate(errors, 1):
        print(f"\n  Error #{i}: {error['error']}")
        print(f"    Ubicación: {error['location']}")
        print(f"    Causa: {error['cause']}")
        print(f"    Solución: {error['solution']}")
    
    # 6. Resumen y recomendaciones
    print("\n6. RESUMEN Y RECOMENDACIONES")
    print("-"*40)
    
    print("\nPROBLEMAS PRINCIPALES:")
    print("1. Playwright no está configurado correctamente")
    print("2. ScrapingConfig tiene problemas de inicialización")
    print("3. Algunos scrapers (MercadoLibre, Hites, AbcDin) no están implementados")
    print("4. Las categorías no coinciden con las esperadas por los scrapers")
    
    print("\nSOLUCIONES PROPUESTAS:")
    print("1. Instalar y configurar Playwright:")
    print("   pip install playwright")
    print("   playwright install chromium")
    print("")
    print("2. Verificar que ScrapingConfig se inicialice con todos los campos")
    print("")
    print("3. Implementar scrapers faltantes o usar versiones v3/v4 existentes")
    print("")
    print("4. Usar categorías válidas:")
    print("   - Ripley: computacion, celulares, electrohogar")
    print("   - Falabella: tecnologia, electrohogar, muebles")
    print("   - Paris: computacion, celulares, electrodomesticos")
    
    print("\nESTADO GENERAL:")
    if not missing and all(r['status'] == 'OK' for r in init_results.values()):
        print("  [OK] Sistema listo para funcionar")
    else:
        print("  [REQUIERE ACCIÓN] Se necesitan correcciones antes de ejecutar")
    
    print("\n" + "="*80)
    print("FIN DEL REPORTE")
    print("="*80)

if __name__ == "__main__":
    generate_report()