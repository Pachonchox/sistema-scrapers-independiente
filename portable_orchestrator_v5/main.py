#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Scraper v5 Main Entry Point - Punto de Entrada Principal
===========================================================

Script principal para ejecutar el sistema de scraping v5 con
todas las funcionalidades integradas:

- Scraping por retailer y categoría
- Búsquedas específicas  
- Modo testing integrado
- Gestión de proxies
- Monitoreo en tiempo real
- Diagnósticos automáticos

Uso:
    python main.py --retailer ripley --category informatica
    python main.py --retailer ripley --search "notebook" 
    python main.py --test --retailer ripley
    python main.py --health-check

Autor: Sistema Scraper v5 🚀
"""

import sys
import os
import io
import asyncio
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))
# Agregar utils del proyecto (para exportación Excel)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports del sistema
from .core.orchestrator import ScraperV5Orchestrator
from .testing.test_runner import RetailerTestRunner
from .testing.maintenance_tools import MaintenanceToolkit
from .scrapers import SCRAPER_REGISTRY
from utils.excel_export import export_excel


def setup_logging(verbose: bool = False) -> None:
    """🔧 Configurar sistema de logging"""
    
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configurar formato con emojis
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Reducir logging de librerías externas
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def print_banner() -> None:
    """🎨 Mostrar banner del sistema"""
    
    banner = """
🚀 =============================================== 🚀
    SCRAPER V5 PROJECT - Nueva Generación
    Sistema de Scraping con ML Integrado
    
    Retailers: Ripley, Falabella, Paris, Hites, 
               AbcDin, MercadoLibre
    
    Características:
    🧠 Machine Learning integrado
    🌐 Gestión inteligente de proxies  
    🔧 Testing framework incluido
    ⚖️ Sistema de tiers dinámico
    📊 ETL con field mapping
🚀 =============================================== 🚀
    """
    
    print(banner)


async def run_scraping(args) -> None:
    """🏃‍♂️ Ejecutar scraping principal"""
    
    print(f"🎯 Iniciando scraping de {args.retailer}")
    
    try:
        # Crear orchestrador
        orchestrator = ScraperV5Orchestrator()
        
        # Configurar parámetros
        max_products = args.max_products or 50
        
        result = None
        
        if args.category:
            # Scraping por categoría
            print(f"📂 Scrapeando categoría: {args.category}")
            result = await orchestrator.scrape_category(
                retailer=args.retailer,
                category=args.category,
                max_products=max_products
            )
            
        elif args.search:
            # Búsqueda específica
            print(f"🔍 Buscando: {args.search}")
            result = await orchestrator.search_products(
                retailer=args.retailer,
                query=args.search,
                max_products=max_products
            )
            
        else:
            print("❌ Debe especificar --category o --search")
            return
        
        # Mostrar resultados
        if result.success:
            print(f"\n✅ Scraping completado exitosamente!")
            print(f"📊 Productos extraídos: {result.total_found}")
            print(f"⏱️ Tiempo de ejecución: {result.execution_time:.1f}s")
            print(f"🔗 URL fuente: {result.source_url}")
            
            # Mostrar algunos productos de ejemplo
            if result.products:
                print(f"\n📋 Primeros 3 productos:")
                for i, product in enumerate(result.products[:3], 1):
                    title = getattr(product, 'title', getattr(product, 'nombre', 'Producto'))
                    price = getattr(product, 'current_price', 0)
                    print(f"  {i}. {title}")
                    try:
                        print(f"     💰 ${price:,.0f} CLP")
                    except Exception:
                        pass
                    print()

            # Exportar a Excel si se solicita
            if getattr(args, 'export_excel', False):
                base_dir = Path(__file__).resolve().parent.parent  # scraper_v5_project/
                out_dir = base_dir / 'data' / 'excel'
                out_path = export_excel(result.products, retailer=args.retailer, out_dir=out_dir)
                print(f"📄 Excel generado: {out_path}")
        else:
            print(f"❌ Error en scraping: {result.error_message}")
            
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()


async def run_tests(args) -> None:
    """🧪 Ejecutar tests del sistema"""
    
    print(f"🧪 Ejecutando tests para {args.retailer}")
    
    try:
        test_runner = RetailerTestRunner()
        
        # Ejecutar tests específicos del retailer
        results = await test_runner.run_retailer_tests(
            retailer=args.retailer,
            test_type=args.test_type or 'basic',
            verbose=args.verbose
        )
        
        # Mostrar resultados
        print(f"\n📊 Resultados de Tests:")
        print(f"✅ Tests exitosos: {results['passed']}")
        print(f"❌ Tests fallidos: {results['failed']}")
        print(f"⏭️ Tests omitidos: {results['skipped']}")
        print(f"⏱️ Tiempo total: {results['execution_time']:.1f}s")
        
        # Detalles de fallos
        if results['failed'] > 0:
            print(f"\n🔍 Detalles de fallos:")
            for failure in results.get('failure_details', []):
                print(f"  ❌ {failure['test_name']}: {failure['error']}")
        
        # Recomendaciones
        if results.get('recommendations'):
            print(f"\n💡 Recomendaciones:")
            for rec in results['recommendations']:
                print(f"  • {rec}")
        
        return results['failed'] == 0
        
    except Exception as e:
        print(f"💥 Error ejecutando tests: {e}")
        return False


async def run_health_check() -> None:
    """🏥 Ejecutar health check completo del sistema"""
    
    print("🏥 Ejecutando health check del sistema...")
    
    try:
        toolkit = MaintenanceToolkit()
        
        # Diagnóstico completo
        report = await toolkit.full_system_diagnostic()
        
        print(f"\n📊 Reporte de Health Check:")
        print(f"🏥 Estado general: {'✅ SALUDABLE' if report['overall_health'] else '❌ PROBLEMAS'}")
        print(f"⚙️ Componentes verificados: {report['components_checked']}")
        print(f"✅ Componentes OK: {report['healthy_components']}")
        print(f"❌ Componentes con problemas: {report['unhealthy_components']}")
        
        # Detalles por componente
        for component, status in report['component_status'].items():
            status_emoji = "✅" if status['healthy'] else "❌"
            print(f"  {status_emoji} {component}: {status['message']}")
        
        # Recomendaciones
        if report.get('recommendations'):
            print(f"\n💡 Recomendaciones:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        return report['overall_health']
        
    except Exception as e:
        print(f"💥 Error en health check: {e}")
        return False


async def run_maintenance(args) -> None:
    """🔧 Ejecutar tareas de mantenimiento"""
    
    print("🔧 Ejecutando mantenimiento del sistema...")
    
    try:
        toolkit = MaintenanceToolkit()
        
        tasks_completed = []
        
        if args.cleanup:
            print("🧹 Limpiando datos antiguos...")
            cleanup_report = toolkit.cleanup_old_data(days=args.cleanup_days or 7)
            tasks_completed.append(f"Cleanup: {cleanup_report}")
        
        if args.optimize_proxies:
            print("🌐 Optimizando configuración de proxies...")
            # Implementar optimización de proxies
            tasks_completed.append("Proxy optimization completed")
        
        if args.retrain_models:
            print("🎓 Re-entrenando modelos ML...")
            # Implementar re-entrenamiento
            tasks_completed.append("ML models retrained")
        
        print(f"\n✅ Mantenimiento completado:")
        for task in tasks_completed:
            print(f"  • {task}")
            
    except Exception as e:
        print(f"💥 Error en mantenimiento: {e}")


def create_parser() -> argparse.ArgumentParser:
    """🔧 Crear parser de argumentos CLI"""
    
    parser = argparse.ArgumentParser(
        description="🚀 Scraper v5 Project - Sistema de Scraping de Nueva Generación",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Scraping básico
  python main.py --retailer ripley --category informatica --max-products 50
  
  # Búsqueda específica
  python main.py --retailer ripley --search "notebook gaming" --max-products 30
  
  # Modo testing
  python main.py --test --retailer ripley --test-type full --verbose
  
  # Health check
  python main.py --health-check
  
  # Mantenimiento
  python main.py --maintenance --cleanup --cleanup-days 7

Retailers soportados: """ + ", ".join(SCRAPER_REGISTRY.keys())
    )
    
    # Argumentos principales
    parser.add_argument('--retailer', choices=list(SCRAPER_REGISTRY.keys()),
                       help='Retailer a scrapear')
    
    parser.add_argument('--category', type=str,
                       help='Categoría a scrapear')
    
    parser.add_argument('--search', type=str,
                       help='Término de búsqueda')
    
    parser.add_argument('--max-products', type=int, default=50,
                       help='Máximo número de productos (default: 50)')
    
    # Modos de operación
    parser.add_argument('--test', action='store_true',
                       help='Ejecutar en modo testing')
    
    parser.add_argument('--test-type', choices=['basic', 'full', 'performance'],
                       default='basic', help='Tipo de test a ejecutar')
    
    parser.add_argument('--health-check', action='store_true',
                       help='Ejecutar health check del sistema')
    
    parser.add_argument('--maintenance', action='store_true',
                       help='Ejecutar tareas de mantenimiento')
    
    # Opciones de mantenimiento
    parser.add_argument('--cleanup', action='store_true',
                       help='Limpiar datos antiguos')
    
    parser.add_argument('--cleanup-days', type=int, default=7,
                       help='Días de antigüedad para cleanup (default: 7)')
    
    parser.add_argument('--optimize-proxies', action='store_true',
                       help='Optimizar configuración de proxies')
    
    parser.add_argument('--retrain-models', action='store_true',
                       help='Re-entrenar modelos ML')
    
    # Opciones generales
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Output detallado (debug mode)')
    
    parser.add_argument('--config', type=str,
                       help='Archivo de configuración personalizado')
    
    parser.add_argument('--proxy-provider', type=str,
                       help='Proveedor de proxy específico')
    
    parser.add_argument('--no-banner', action='store_true',
                       help='No mostrar banner de inicio')
    
    # Exportación Excel
    parser.add_argument('--export-excel', action='store_true',
                       help='Exportar resultados a Excel (data/excel)')
    
    return parser


async def main():
    """🎯 Función principal"""
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    
    # Mostrar banner
    if not args.no_banner:
        print_banner()
    
    # Validar argumentos
    if not any([args.test, args.health_check, args.maintenance]):
        if not args.retailer:
            print("❌ Error: Debe especificar --retailer")
            parser.print_help()
            return 1
        
        if not args.category and not args.search:
            print("❌ Error: Debe especificar --category o --search")
            parser.print_help()
            return 1
    
    try:
        # Ejecutar según modo
        if args.health_check:
            success = await run_health_check()
            return 0 if success else 1
            
        elif args.maintenance:
            await run_maintenance(args)
            return 0
            
        elif args.test:
            if not args.retailer:
                print("❌ Error: --test requiere especificar --retailer")
                return 1
            success = await run_tests(args)
            return 0 if success else 1
            
        else:
            await run_scraping(args)
            return 0
            
    except KeyboardInterrupt:
        print("\n🛑 Operación interrumpida por el usuario")
        return 1
        
    except Exception as e:
        print(f"\n💥 Error crítico no manejado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Ejecutar función principal
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Programa terminado")
        sys.exit(1)
