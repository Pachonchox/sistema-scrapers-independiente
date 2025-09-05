#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 ORQUESTADOR INDEPENDIENTE V5 - Sistema Completo de Scrapers
============================================================

Orquestador para ejecutar todos los scrapers con CAMPOS COMPLETOS extraídos
de los scrapers originales (scrapers_port), con arquitectura V5 optimizada.

✅ SCRAPERS INCLUIDOS:
- Paris: 15+ campos completos
- Ripley: 18+ campos completos  
- Hites: 16+ campos completos
- AbcDin: 17+ campos completos
- Falabella: 14+ campos completos

🎯 FUNCIONALIDADES PRINCIPALES:
- Ejecución concurrente de múltiples scrapers
- Paginación automática para maximizar productos
- Generación de archivos Excel individuales por retailer
- Consolidación de datos en archivo único
- Sistema robusto de manejo de errores
- Logging detallado con emojis
- Configuración flexible por retailer

🚀 MODOS DE EJECUCIÓN:
- Individual: Un scraper específico
- Concurrente: Múltiples scrapers en paralelo
- Secuencial: Uno tras otro (más estable)
- Test: Modo prueba con pocos productos

📋 USO:
python orchestrator.py --mode concurrent --max-products 200
python orchestrator.py --retailer paris --max-products 100  
python orchestrator.py --mode test
"""

import asyncio
import argparse
import logging
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import traceback

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - 📋 %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('orchestrator.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Importar todos los scrapers con campos completos
SCRAPERS_MAPPING = {}
try:
    from scrapers.paris_scraper_v5_improved import ParisScraperV5Improved
    from scrapers.ripley_scraper_v5_improved import RipleyScraperV5Improved  
    from scrapers.hites_scraper_v5_improved import HitesScraperV5Improved
    from scrapers.abcdin_scraper_v5_improved import AbcdinScraperV5Improved
    from scrapers.falabella_scraper_v5_improved import FalabellaScraperV5Improved
    
    SCRAPERS_MAPPING = {
        'paris': ParisScraperV5Improved,
        'ripley': RipleyScraperV5Improved, 
        'hites': HitesScraperV5Improved,
        'abcdin': AbcdinScraperV5Improved,
        'falabella': FalabellaScraperV5Improved
    }
    
    logger.info(f"✅ Scrapers cargados exitosamente: {list(SCRAPERS_MAPPING.keys())}")
    
except ImportError as e:
    logger.error(f"❌ Error importando scrapers: {e}")
    traceback.print_exc()

class IndependentOrchestrator:
    """🎯 Orquestador independiente para scrapers con campos completos"""
    
    def __init__(self):
        self.scrapers_config = {
            'paris': {
                'max_products': 200,
                'timeout': 300,
                'priority': 1,
                'expected_fields': 15  # campos completos del PORT
            },
            'ripley': {
                'max_products': 150,
                'timeout': 400,
                'priority': 2,
                'expected_fields': 18  # campos completos del PORT
            },
            'falabella': {
                'max_products': 150,
                'timeout': 300,
                'priority': 3,
                'expected_fields': 14  # campos completos del PORT
            },
            'hites': {
                'max_products': 100,
                'timeout': 350,
                'priority': 4,
                'expected_fields': 16  # campos completos del PORT
            },
            'abcdin': {
                'max_products': 100,
                'timeout': 350,
                'priority': 5,
                'expected_fields': 17  # campos completos del PORT
            }
        }
        
        # Crear carpeta de resultados
        self.results_dir = Path('resultados')
        self.results_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.execution_stats = {
            'start_time': None,
            'end_time': None,
            'total_products': 0,
            'successful_scrapers': 0,
            'failed_scrapers': 0,
            'scrapers_results': {}
        }

    async def execute_single_scraper(self, retailer_name: str, max_products: int = None, timeout: int = None) -> Dict:
        """🕷️ Ejecutar un scraper individual con configuración específica"""
        
        if retailer_name not in SCRAPERS_MAPPING:
            raise ValueError(f"Scraper '{retailer_name}' no disponible. Opciones: {list(SCRAPERS_MAPPING.keys())}")
        
        # Usar configuración específica o parámetros
        config = self.scrapers_config[retailer_name]
        final_max_products = max_products or config['max_products']
        final_timeout = timeout or config['timeout']
        
        logger.info(f"🚀 Ejecutando {retailer_name.upper()} - max_products: {final_max_products}, timeout: {final_timeout}s")
        
        start_time = time.time()
        scraper = None
        
        try:
            scraper_class = SCRAPERS_MAPPING[retailer_name]
            scraper = scraper_class()
            
            # Ejecutar con timeout
            result = await asyncio.wait_for(
                scraper.scrape_products(max_products=final_max_products),
                timeout=final_timeout
            )
            
            # Procesar resultados
            products_data = []
            products_count = 0
            
            if hasattr(result, 'products') and result.products:
                for product in result.products:
                    try:
                        product_dict = {
                            'retailer': retailer_name,
                            'title': getattr(product, 'title', ''),
                            'current_price': getattr(product, 'current_price', 0),
                            'original_price': getattr(product, 'original_price', 0),
                            'discount_percentage': getattr(product, 'discount_percentage', 0),
                            'brand': getattr(product, 'brand', ''),
                            'sku': getattr(product, 'sku', ''),
                            'rating': getattr(product, 'rating', 0),
                            'product_url': getattr(product, 'product_url', ''),
                            'image_urls': getattr(product, 'image_urls', []),
                            'extraction_timestamp': getattr(product, 'extraction_timestamp', datetime.now()).isoformat(),
                        }
                        
                        # Agregar TODOS los campos adicionales del PORT
                        additional_info = getattr(product, 'additional_info', {})
                        if additional_info:
                            product_dict.update(additional_info)
                        
                        products_data.append(product_dict)
                        products_count += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando producto de {retailer_name}: {e}")
                        continue
            
            execution_time = time.time() - start_time
            
            # Validar campos esperados
            expected_fields = config['expected_fields']
            actual_fields = len(products_data[0].keys()) if products_data else 0
            fields_completeness = (actual_fields / expected_fields) * 100 if expected_fields > 0 else 0
            
            result_summary = {
                'retailer': retailer_name,
                'status': 'success',
                'products_found': products_count,
                'products_data': products_data,
                'execution_time': execution_time,
                'extraction_time': datetime.now().isoformat(),
                'config_used': {
                    'max_products': final_max_products,
                    'timeout': final_timeout
                },
                'quality_metrics': {
                    'expected_fields': expected_fields,
                    'actual_fields': actual_fields,
                    'fields_completeness': f"{fields_completeness:.1f}%"
                }
            }
            
            logger.info(f"✅ {retailer_name.upper()}: {products_count} productos, {actual_fields} campos, {execution_time:.1f}s")
            return result_summary
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ {retailer_name.upper()}: Timeout después de {final_timeout}s")
            return {
                'retailer': retailer_name,
                'status': 'timeout',
                'products_found': 0,
                'products_data': [],
                'execution_time': final_timeout,
                'error': f'Timeout después de {final_timeout} segundos'
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {retailer_name.upper()}: Error - {e}")
            return {
                'retailer': retailer_name,
                'status': 'error',
                'products_found': 0,
                'products_data': [],
                'execution_time': execution_time,
                'error': str(e)
            }
        finally:
            if scraper:
                try:
                    # Cleanup si es necesario
                    pass
                except:
                    pass

    async def execute_concurrent(self, retailers: List[str], max_products: int = 100) -> List[Dict]:
        """🕸️ Ejecutar múltiples scrapers concurrentemente"""
        
        logger.info(f"🚀 Ejecución CONCURRENTE: {retailers}")
        
        # Crear tareas concurrentes
        tasks = []
        for retailer in retailers:
            if retailer in SCRAPERS_MAPPING:
                task = self.execute_single_scraper(retailer, max_products)
                tasks.append(task)
            else:
                logger.warning(f"⚠️ Scraper {retailer} no disponible, saltando")
        
        if not tasks:
            logger.error("❌ No hay scrapers válidos para ejecutar")
            return []
        
        # Ejecutar todas las tareas concurrentemente
        logger.info(f"🔄 Ejecutando {len(tasks)} scrapers en paralelo...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Error en tarea {i}: {result}")
                # Crear resultado de error
                retailer = retailers[i] if i < len(retailers) else f"unknown_{i}"
                error_result = {
                    'retailer': retailer,
                    'status': 'exception',
                    'products_found': 0,
                    'products_data': [],
                    'error': str(result)
                }
                valid_results.append(error_result)
            else:
                valid_results.append(result)
        
        return valid_results

    async def execute_sequential(self, retailers: List[str], max_products: int = 100) -> List[Dict]:
        """🔗 Ejecutar scrapers secuencialmente (más estable)"""
        
        logger.info(f"🔗 Ejecución SECUENCIAL: {retailers}")
        
        results = []
        for i, retailer in enumerate(retailers, 1):
            if retailer not in SCRAPERS_MAPPING:
                logger.warning(f"⚠️ Scraper {retailer} no disponible, saltando")
                continue
            
            logger.info(f"📍 Ejecutando {i}/{len(retailers)}: {retailer.upper()}")
            
            try:
                result = await self.execute_single_scraper(retailer, max_products)
                results.append(result)
                
                # Delay entre scrapers para evitar sobrecarga
                if i < len(retailers):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Error ejecutando {retailer}: {e}")
                error_result = {
                    'retailer': retailer,
                    'status': 'exception',
                    'products_found': 0,
                    'products_data': [],
                    'error': str(e)
                }
                results.append(error_result)
        
        return results

    def save_results(self, results: List[Dict], execution_mode: str = "orchestrator"):
        """💾 Guardar resultados en múltiples formatos"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Guardar JSON consolidado
        consolidated_file = self.results_dir / f"orchestrator_results_{timestamp}.json"
        try:
            with open(consolidated_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'execution_mode': execution_mode,
                    'timestamp': timestamp,
                    'statistics': self.execution_stats,
                    'results': results
                }, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Resultados consolidados: {consolidated_file}")
        except Exception as e:
            logger.error(f"❌ Error guardando JSON consolidado: {e}")
        
        # 2. Guardar Excel por retailer
        try:
            import pandas as pd
            
            excel_files = []
            for result in results:
                if result['products_found'] > 0:
                    retailer = result['retailer']
                    
                    try:
                        # Crear DataFrame con todos los campos
                        products_df = pd.DataFrame(result['products_data'])
                        
                        # Archivo individual por retailer
                        excel_file = self.results_dir / f"{retailer}_complete_{timestamp}.xlsx"
                        
                        # Guardar con metadatos
                        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                            # Hoja principal con productos
                            products_df.to_excel(writer, sheet_name='Productos', index=False)
                            
                            # Hoja de metadatos
                            metadata_df = pd.DataFrame([{
                                'retailer': retailer,
                                'productos_encontrados': result['products_found'],
                                'tiempo_ejecucion': f"{result.get('execution_time', 0):.1f}s",
                                'campos_extraidos': len(products_df.columns),
                                'timestamp': timestamp,
                                'status': result['status']
                            }])
                            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                        
                        excel_files.append(excel_file)
                        logger.info(f"📊 Excel {retailer.upper()}: {excel_file.name} - {len(products_df)} productos, {len(products_df.columns)} campos")
                        
                    except Exception as e:
                        logger.error(f"❌ Error creando Excel para {retailer}: {e}")
            
            # 3. Excel consolidado (opcional)
            if len(excel_files) > 1:
                try:
                    all_products = []
                    for result in results:
                        if result['products_found'] > 0:
                            all_products.extend(result['products_data'])
                    
                    if all_products:
                        consolidated_excel = self.results_dir / f"TODOS_RETAILERS_{timestamp}.xlsx"
                        consolidated_df = pd.DataFrame(all_products)
                        consolidated_df.to_excel(consolidated_excel, index=False)
                        logger.info(f"📊 Excel CONSOLIDADO: {consolidated_excel.name} - {len(all_products)} productos totales")
                
                except Exception as e:
                    logger.error(f"❌ Error creando Excel consolidado: {e}")
        
        except ImportError:
            logger.warning("⚠️ pandas no disponible, solo guardando JSON")

    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """📋 Generar reporte resumen de la ejecución"""
        
        total_products = sum(r.get('products_found', 0) for r in results)
        successful_scrapers = len([r for r in results if r.get('status') == 'success'])
        failed_scrapers = len(results) - successful_scrapers
        
        execution_time = (self.execution_stats['end_time'] - self.execution_stats['start_time']).total_seconds() if self.execution_stats['start_time'] else 0
        
        # Estadísticas por retailer
        retailer_stats = {}
        for result in results:
            retailer = result['retailer']
            retailer_stats[retailer] = {
                'status': result['status'],
                'products': result['products_found'],
                'execution_time': result.get('execution_time', 0),
                'quality': result.get('quality_metrics', {})
            }
        
        summary = {
            'execution_summary': {
                'total_retailers': len(results),
                'successful_scrapers': successful_scrapers,
                'failed_scrapers': failed_scrapers,
                'total_products': total_products,
                'total_execution_time': f"{execution_time:.1f}s"
            },
            'retailer_breakdown': retailer_stats,
            'performance_metrics': {
                'products_per_second': total_products / execution_time if execution_time > 0 else 0,
                'success_rate': f"{(successful_scrapers / len(results)) * 100:.1f}%" if results else "0%"
            }
        }
        
        return summary

async def main():
    """🎯 Función principal del orquestador independiente"""
    
    parser = argparse.ArgumentParser(description="Orquestador Independiente V5 - Scrapers con Campos Completos")
    
    parser.add_argument('--mode', choices=['concurrent', 'sequential', 'test'], default='concurrent',
                       help='Modo de ejecución (default: concurrent)')
    parser.add_argument('--retailer', choices=list(SCRAPERS_MAPPING.keys()),
                       help='Ejecutar scraper específico')
    parser.add_argument('--retailers', nargs='+', choices=list(SCRAPERS_MAPPING.keys()),
                       help='Lista de retailers específicos')
    parser.add_argument('--max-products', type=int, default=100,
                       help='Máximo productos por scraper (default: 100)')
    parser.add_argument('--timeout', type=int,
                       help='Timeout en segundos por scraper')
    
    args = parser.parse_args()
    
    if not SCRAPERS_MAPPING:
        logger.error("❌ No hay scrapers disponibles - revisar imports")
        return
    
    orchestrator = IndependentOrchestrator()
    
    # Configurar estadísticas
    orchestrator.execution_stats['start_time'] = datetime.now()
    
    logger.info("🎯 === ORQUESTADOR INDEPENDIENTE V5 - CAMPOS COMPLETOS ===")
    logger.info(f"🎯 Modo: {args.mode.upper()}")
    logger.info(f"📦 Max productos: {args.max_products}")
    logger.info(f"🕷️ Scrapers disponibles: {list(SCRAPERS_MAPPING.keys())}")
    
    try:
        results = []
        
        if args.retailer:
            # Ejecutar scraper específico
            logger.info(f"🎯 Ejecutando scraper específico: {args.retailer}")
            result = await orchestrator.execute_single_scraper(
                args.retailer, 
                args.max_products,
                args.timeout
            )
            results = [result]
            
        elif args.retailers:
            # Lista específica de retailers
            target_retailers = args.retailers
            if args.mode == 'concurrent':
                results = await orchestrator.execute_concurrent(target_retailers, args.max_products)
            else:
                results = await orchestrator.execute_sequential(target_retailers, args.max_products)
                
        elif args.mode == 'test':
            # Modo test con pocos productos
            logger.info("🧪 Modo TEST - 10 productos por scraper")
            test_retailers = ['paris', 'falabella']  # Scrapers más rápidos para test
            results = await orchestrator.execute_concurrent(test_retailers, 10)
            
        else:
            # Ejecutar todos los scrapers
            all_retailers = list(SCRAPERS_MAPPING.keys())
            if args.mode == 'concurrent':
                results = await orchestrator.execute_concurrent(all_retailers, args.max_products)
            else:
                results = await orchestrator.execute_sequential(all_retailers, args.max_products)
        
        # Finalizar estadísticas
        orchestrator.execution_stats['end_time'] = datetime.now()
        
        # Guardar resultados
        orchestrator.save_results(results, args.mode)
        
        # Generar reporte resumen
        summary = orchestrator.generate_summary_report(results)
        
        # Mostrar resumen en consola
        logger.info("🎉 === REPORTE FINAL ===")
        logger.info(f"✅ Scrapers exitosos: {summary['execution_summary']['successful_scrapers']}/{summary['execution_summary']['total_retailers']}")
        logger.info(f"📦 Total productos: {summary['execution_summary']['total_products']}")
        logger.info(f"⏱️ Tiempo total: {summary['execution_summary']['total_execution_time']}")
        logger.info(f"📈 Tasa éxito: {summary['performance_metrics']['success_rate']}")
        
        print("\n📊 === DETALLE POR RETAILER ===")
        for retailer, stats in summary['retailer_breakdown'].items():
            status_emoji = "✅" if stats['status'] == 'success' else "❌"
            print(f"{status_emoji} {retailer.upper()}: {stats['products']} productos ({stats['execution_time']:.1f}s)")
        
        print(f"\n💾 Archivos guardados en: {orchestrator.results_dir}/")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Ejecución interrumpida por usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico del orquestador: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())