#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA COMPLETO DE SCRAPERS INDEPENDIENTE 
=============================================

Sistema completo de scrapers con TODOS los campos de datos extraídos
de los scrapers originales (scrapers_port) integrados en arquitectura V5.

✅ SCRAPERS INCLUIDOS CON CAMPOS COMPLETOS:
- Paris: 15+ campos (brand, storage, ram, network, color, ratings, etc.)
- Ripley: 18+ campos (screen_size, camera, colors, emblems, precios múltiples)
- Hites: 16+ campos (seller, specs, shipping_options, stock status)  
- AbcDin: 17+ campos (product_id, badges, power reviews, precios múltiples)

🎯 FUNCIONALIDADES:
- Extracción de datos COMPLETA por retailer
- Paginación automática para obtener más productos
- Generación de archivos Excel con todos los campos
- Sistema robusto con manejo de errores

📋 USO:
python run_complete_system.py
python run_complete_system.py --retailer paris --max-products 200
python run_complete_system.py --all-retailers --max-products 100
"""

import asyncio
import argparse
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - 📋 %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scrapers_system.log')
    ]
)

logger = logging.getLogger(__name__)

# Importar scrapers actualizados con campos completos
try:
    from scrapers.paris_scraper_v5_improved import ParisScraperV5Improved
    from scrapers.ripley_scraper_v5_improved import RipleyScraperV5Improved  
    from scrapers.hites_scraper_v5_improved import HitesScraperV5Improved
    from scrapers.abcdin_scraper_v5_improved import AbcdinScraperV5Improved
    from scrapers.falabella_scraper_v5_improved import FalabellaScraperV5Improved
    
    SCRAPERS_AVAILABLE = True
    logger.info("✅ Todos los scrapers con campos completos cargados exitosamente (incluyendo Falabella)")
    
except ImportError as e:
    logger.error(f"❌ Error importando scrapers: {e}")
    SCRAPERS_AVAILABLE = False

class CompleteScrapingSystem:
    """🚀 Sistema completo de scrapers independiente"""
    
    def __init__(self):
        self.scrapers = {
            'paris': ParisScraperV5Improved,
            'ripley': RipleyScraperV5Improved, 
            'hites': HitesScraperV5Improved,
            'abcdin': AbcdinScraperV5Improved,
            'falabella': FalabellaScraperV5Improved
        }
        
        # Configuración por defecto
        self.config = {
            'max_products': 100,
            'timeout_seconds': 300,
            'concurrent_scrapers': 2,
            'save_to_excel': True,
            'save_to_json': True
        }
        
        # Crear carpeta de resultados
        self.results_dir = Path('resultados')
        self.results_dir.mkdir(exist_ok=True)
        
    async def run_single_scraper(self, retailer_name: str, max_products: int = 100) -> Dict:
        """🕷️ Ejecutar un scraper individual con campos completos"""
        
        if retailer_name not in self.scrapers:
            raise ValueError(f"Retailer '{retailer_name}' no disponible. Opciones: {list(self.scrapers.keys())}")
        
        logger.info(f"🚀 Iniciando scraper {retailer_name.upper()} - Extracción completa de campos")
        
        try:
            scraper_class = self.scrapers[retailer_name]
            scraper = scraper_class()
            
            # Ejecutar scraper con cantidad específica
            results = await scraper.scrape_products(max_products=max_products)
            
            # Procesar resultados
            products_data = []
            if hasattr(results, 'products'):
                for product in results.products:
                    product_dict = {
                        'retailer': retailer_name,
                        'title': product.title,
                        'current_price': product.current_price,
                        'original_price': product.original_price,
                        'discount_percentage': product.discount_percentage,
                        'brand': product.brand,
                        'sku': product.sku,
                        'rating': product.rating,
                        'product_url': product.product_url,
                        'image_urls': product.image_urls,
                        'extraction_timestamp': product.extraction_timestamp.isoformat(),
                        **product.additional_info  # TODOS los campos adicionales del PORT
                    }
                    products_data.append(product_dict)
            
            result_summary = {
                'retailer': retailer_name,
                'products_found': len(products_data),
                'products_data': products_data,
                'extraction_time': datetime.now().isoformat(),
                'status': 'success'
            }
            
            logger.info(f"✅ {retailer_name.upper()}: {len(products_data)} productos extraídos con campos completos")
            return result_summary
            
        except Exception as e:
            logger.error(f"❌ Error en scraper {retailer_name}: {e}")
            return {
                'retailer': retailer_name,
                'products_found': 0,
                'products_data': [],
                'error': str(e),
                'status': 'error'
            }
    
    async def run_all_scrapers(self, max_products: int = 100) -> List[Dict]:
        """🕸️ Ejecutar todos los scrapers con campos completos"""
        
        logger.info("🚀 Iniciando TODOS los scrapers con extracción completa")
        
        # Ejecutar scrapers concurrentemente
        tasks = []
        for retailer_name in self.scrapers.keys():
            task = self.run_single_scraper(retailer_name, max_products)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Error en ejecución: {result}")
                continue
            valid_results.append(result)
        
        return valid_results
    
    def save_results(self, results: List[Dict], filename_prefix: str = "scrapers_complete"):
        """💾 Guardar resultados en Excel y JSON"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar JSON completo
        json_file = self.results_dir / f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Resultados JSON guardados: {json_file}")
        
        # Guardar Excel por retailer
        try:
            import pandas as pd
            
            for result in results:
                if result['products_found'] > 0:
                    retailer = result['retailer']
                    products_df = pd.DataFrame(result['products_data'])
                    
                    excel_file = self.results_dir / f"{retailer}_complete_{timestamp}.xlsx"
                    products_df.to_excel(excel_file, index=False)
                    
                    logger.info(f"📊 Excel {retailer.upper()}: {excel_file} - {len(products_df)} productos")
        
        except ImportError:
            logger.warning("⚠️ pandas no disponible, solo guardando JSON")

async def main():
    """🎯 Función principal del sistema completo"""
    
    parser = argparse.ArgumentParser(description="Sistema Completo de Scrapers Independiente")
    parser.add_argument('--retailer', choices=['paris', 'ripley', 'hites', 'abcdin', 'falabella'], 
                       help='Ejecutar scraper específico')
    parser.add_argument('--all-retailers', action='store_true',
                       help='Ejecutar todos los scrapers')
    parser.add_argument('--max-products', type=int, default=100,
                       help='Máximo productos por scraper (default: 100)')
    
    args = parser.parse_args()
    
    if not SCRAPERS_AVAILABLE:
        logger.error("❌ Scrapers no disponibles - revisar imports")
        return
    
    system = CompleteScrapingSystem()
    
    logger.info("🚀 === SISTEMA COMPLETO DE SCRAPERS INDEPENDIENTE ===")
    logger.info(f"🎯 Configuración: max_products={args.max_products}")
    
    try:
        if args.retailer:
            # Ejecutar scraper específico
            results = [await system.run_single_scraper(args.retailer, args.max_products)]
        elif args.all_retailers:
            # Ejecutar todos los scrapers
            results = await system.run_all_scrapers(args.max_products)
        else:
            # Por defecto ejecutar todos
            results = await system.run_all_scrapers(args.max_products)
        
        # Guardar resultados
        system.save_results(results)
        
        # Mostrar resumen
        total_products = sum(r.get('products_found', 0) for r in results)
        successful_scrapers = len([r for r in results if r.get('status') == 'success'])
        
        logger.info("🎉 === RESUMEN FINAL ===")
        logger.info(f"✅ Scrapers exitosos: {successful_scrapers}/{len(results)}")
        logger.info(f"📦 Total productos extraídos: {total_products}")
        logger.info("💾 Archivos guardados en carpeta 'resultados/'")
        
        for result in results:
            if result.get('status') == 'success':
                logger.info(f"  📊 {result['retailer'].upper()}: {result['products_found']} productos")
            else:
                logger.error(f"  ❌ {result['retailer'].upper()}: ERROR")
                
    except KeyboardInterrupt:
        logger.info("⏹️ Ejecución interrumpida por usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico del sistema: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())