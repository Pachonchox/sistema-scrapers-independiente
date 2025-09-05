#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 Scraping Orchestrator - Sistema Central de Orquestación
===========================================================

Sistema central que conecta TODOS los scrapers existentes con el
ProductProcessor sin necesidad de modificar los scrapers.

Arquitectura:
    Scrapers (sin cambios) → Orchestrator → ProductProcessor → DB
                                    ↓
                              Excel Backup

Características:
- No requiere modificar scrapers existentes
- Procesa ScrapingResult de cualquier scraper
- Conversión automática de ProductData a formato DB
- Procesamiento en batch para eficiencia
- Manejo de errores robusto
- Estadísticas en tiempo real

Autor: Sistema Optimizado V5
Fecha: Diciembre 2024
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
from collections import defaultdict

from .product_processor import ProductProcessor
from .sku_generator import SKUGenerator

# Imports de scrapers V5 existentes
try:
    from portable_orchestrator_v5.scrapers import (
        FalabellaScraperV5,
        RipleyScraperV5, 
        ParisScraperV5,
        MercadoLibreScraperV5,
        HitesScraperV5,
        AbcdinScraperV5
    )
    SCRAPERS_AVAILABLE = True
except ImportError as e:
    SCRAPERS_AVAILABLE = False
    # logger no está disponible aún
    print(f"⚠️ Algunos scrapers no disponibles: {e}")

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationStats:
    """📊 Estadísticas de orquestación"""
    scrapers_executed: int = 0
    total_products_scraped: int = 0
    total_products_processed: int = 0
    total_products_inserted: int = 0
    total_duplicates: int = 0
    total_errors: int = 0
    execution_time: float = 0.0
    retailer_stats: Dict[str, Dict] = field(default_factory=dict)
    
    def add_retailer_stats(self, retailer: str, stats: Dict):
        """Agrega estadísticas de un retailer"""
        self.retailer_stats[retailer] = stats
    
    def get_summary(self) -> str:
        """Genera resumen de estadísticas"""
        summary = [
            "=" * 70,
            "📊 RESUMEN DE ORQUESTACIÓN",
            "=" * 70,
            f"Scrapers ejecutados: {self.scrapers_executed}",
            f"Productos scrapeados: {self.total_products_scraped:,}",
            f"Productos procesados: {self.total_products_processed:,}",
            f"Productos insertados: {self.total_products_inserted:,}",
            f"Duplicados detectados: {self.total_duplicates:,}",
            f"Errores: {self.total_errors}",
            f"Tiempo total: {self.execution_time:.1f} segundos",
            ""
        ]
        
        if self.retailer_stats:
            summary.append("📈 Por Retailer:")
            for retailer, stats in self.retailer_stats.items():
                summary.append(f"  {retailer}:")
                summary.append(f"    Productos: {stats.get('products', 0):,}")
                summary.append(f"    Insertados: {stats.get('inserted', 0):,}")
                summary.append(f"    Duplicados: {stats.get('duplicates', 0):,}")
                summary.append(f"    Tiempo: {stats.get('time', 0):.1f}s")
        
        return "\n".join(summary)


class ScrapingOrchestrator:
    """🎯 Orquestador central de scraping"""
    
    def __init__(self,
                 db_config: Optional[Dict] = None,
                 enable_excel_backup: bool = True,
                 batch_size: int = 100):
        """
        Inicializa el orquestador
        
        Args:
            db_config: Configuración de base de datos
            enable_excel_backup: Habilitar backup en Excel
            batch_size: Tamaño del batch para procesamiento
        """
        # Procesador central
        self.processor = ProductProcessor(
            db_config=db_config,
            enable_excel_backup=enable_excel_backup,
            batch_size=batch_size
        )
        
        # Scrapers disponibles
        self.scrapers = self._initialize_scrapers()
        
        # Estadísticas
        self.stats = OrchestrationStats()
        
        # Cola de productos para procesar
        self.product_queue = []
        
        logger.info(f"🎯 Orchestrator inicializado con {len(self.scrapers)} scrapers")
    
    def _initialize_scrapers(self) -> Dict:
        """Inicializa los scrapers disponibles"""
        scrapers = {}
        
        if not SCRAPERS_AVAILABLE:
            logger.warning("⚠️ Scrapers no disponibles, usando modo mock")
            return scrapers
        
        # Inicializar cada scraper disponible
        scraper_classes = [
            ('falabella', FalabellaScraperV5),
            ('ripley', RipleyScraperV5),
            ('paris', ParisScraperV5),
            ('mercadolibre', MercadoLibreScraperV5),
            ('hites', HitesScraperV5),
            ('abcdin', AbcdinScraperV5)
        ]
        
        for name, scraper_class in scraper_classes:
            try:
                scrapers[name] = scraper_class()
                logger.info(f"✅ Scraper {name} inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando scraper {name}: {e}")
        
        return scrapers
    
    async def scrape_retailer(self,
                              retailer: str,
                              category: str = "smartphones",
                              max_products: int = 100) -> Dict:
        """
        Ejecuta scraping para un retailer específico
        
        Args:
            retailer: Nombre del retailer
            category: Categoría a scrapear
            max_products: Máximo de productos
            
        Returns:
            Dict con resultados y estadísticas
        """
        start_time = datetime.now()
        result = {
            'retailer': retailer,
            'success': False,
            'products_scraped': 0,
            'products_processed': 0,
            'products_inserted': 0,
            'duplicates': 0,
            'errors': []
        }
        
        # Verificar si el scraper existe
        if retailer not in self.scrapers:
            error_msg = f"Scraper {retailer} no disponible"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        try:
            # Ejecutar scraping
            logger.info(f"🕷️ Iniciando scraping de {retailer} - {category}")
            scraper = self.scrapers[retailer]
            
            # Ejecutar scraper (asumiendo que devuelve ScrapingResult)
            scraping_result = await scraper.scrape_category(
                category=category,
                max_products=max_products
            )
            
            if scraping_result.success:
                result['success'] = True
                result['products_scraped'] = len(scraping_result.products)
                
                # Procesar productos
                processed_count = await self._process_scraping_result(
                    scraping_result,
                    retailer
                )
                
                result['products_processed'] = processed_count
                
                logger.info(f"✅ {retailer}: {result['products_scraped']} productos scrapeados, {processed_count} procesados")
            else:
                error_msg = f"Scraping falló: {scraping_result.error_message}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"Error ejecutando scraper {retailer}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            self.stats.total_errors += 1
        
        # Calcular tiempo
        result['execution_time'] = (datetime.now() - start_time).total_seconds()
        
        return result
    
    async def _process_scraping_result(self,
                                      scraping_result: Any,
                                      retailer: str) -> int:
        """
        Procesa el resultado del scraping
        
        Args:
            scraping_result: Resultado del scraper (ScrapingResult)
            retailer: Nombre del retailer
            
        Returns:
            Número de productos procesados
        """
        processed_count = 0
        
        for product in scraping_result.products:
            try:
                # Convertir ProductData a formato para DB
                product_dict = self._convert_product_to_dict(product, retailer)
                
                # Procesar con ProductProcessor
                sku = await self.processor.process_product(product_dict, retailer)

                if sku:
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"Error procesando producto: {e}")
                self.stats.total_errors += 1
        
        # Flush batch pendiente
        await self.processor.flush_batch()
        
        return processed_count
    
    def _convert_product_to_dict(self, product: Any, retailer: str) -> Dict:
        """
        Convierte ProductData del scraper a diccionario para procesamiento
        
        Args:
            product: Objeto ProductData del scraper
            retailer: Nombre del retailer
            
        Returns:
            Dict con datos del producto
        """
        # Manejar diferentes formatos de ProductData
        if hasattr(product, 'to_dict'):
            # Si tiene método to_dict, usarlo
            product_dict = product.to_dict()
        elif hasattr(product, '__dict__'):
            # Si no, convertir atributos a dict
            product_dict = vars(product)
        else:
            # Si es dict, usarlo directamente
            product_dict = product if isinstance(product, dict) else {}
        
        # Mapear campos comunes
        normalized = {
            'nombre': product_dict.get('title') or product_dict.get('nombre', ''),
            'marca': product_dict.get('brand') or product_dict.get('marca', ''),
            'sku': product_dict.get('sku', ''),
            'link': product_dict.get('product_url') or product_dict.get('link', ''),
            'categoria': product_dict.get('category') or product_dict.get('categoria', 'general'),
            
            # Precios
            'original_price': product_dict.get('original_price', 0),
            'current_price': product_dict.get('current_price', 0),
            'card_price': product_dict.get('card_price', 0),
            
            # Alternativas de precios
            'precio_normal': product_dict.get('precio_normal', 0),
            'precio_oferta': product_dict.get('precio_oferta', 0),
            'precio_tarjeta': product_dict.get('precio_tarjeta', 0),
            
            # Otros campos
            'rating': product_dict.get('rating', 0),
            'reviews_count': product_dict.get('reviews_count', 0),
            
            # Additional info
            'additional_info': product_dict.get('additional_info', {})
        }
        
        return normalized
    
    async def scrape_all_retailers(self,
                                   category: str = "smartphones",
                                   max_products_per_retailer: int = 100) -> OrchestrationStats:
        """
        Ejecuta scraping para todos los retailers
        
        Args:
            category: Categoría a scrapear
            max_products_per_retailer: Máximo por retailer
            
        Returns:
            Estadísticas de orquestación
        """
        start_time = datetime.now()
        
        logger.info("=" * 70)
        logger.info("🚀 INICIANDO ORQUESTACIÓN COMPLETA")
        logger.info("=" * 70)
        logger.info(f"Categoría: {category}")
        logger.info(f"Max productos por retailer: {max_products_per_retailer}")
        logger.info(f"Retailers disponibles: {list(self.scrapers.keys())}")
        logger.info("")
        
        # Ejecutar scrapers en paralelo
        tasks = []
        for retailer in self.scrapers.keys():
            task = self.scrape_retailer(
                retailer=retailer,
                category=category,
                max_products=max_products_per_retailer
            )
            tasks.append(task)
        
        # Esperar resultados
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Error en tarea: {result}")
                self.stats.total_errors += 1
            elif isinstance(result, dict):
                retailer = result.get('retailer', 'unknown')
                
                # Actualizar estadísticas globales
                self.stats.scrapers_executed += 1 if result['success'] else 0
                self.stats.total_products_scraped += result['products_scraped']
                self.stats.total_products_processed += result['products_processed']
                
                # Estadísticas por retailer
                self.stats.add_retailer_stats(retailer, {
                    'products': result['products_scraped'],
                    'processed': result['products_processed'],
                    'inserted': result.get('products_inserted', 0),
                    'duplicates': result.get('duplicates', 0),
                    'time': result.get('execution_time', 0)
                })
        
        # Finalizar procesamiento
        await self.processor.finish_processing()
        
        # Obtener estadísticas del processor
        processor_stats = self.processor.stats.get_summary()
        self.stats.total_products_inserted = processor_stats['products_inserted']
        self.stats.total_duplicates = processor_stats['duplicates_found']
        
        # Tiempo total
        self.stats.execution_time = (datetime.now() - start_time).total_seconds()
        
        # Mostrar resumen
        print(self.stats.get_summary())
        
        return self.stats
    
    async def scrape_with_config(self, config: Dict) -> OrchestrationStats:
        """
        Ejecuta scraping con configuración específica
        
        Args:
            config: Configuración de scraping
                {
                    'retailers': ['falabella', 'ripley'],
                    'categories': ['smartphones', 'notebooks'],
                    'max_products': 50,
                    'parallel': True
                }
        
        Returns:
            Estadísticas de orquestación
        """
        retailers = config.get('retailers', list(self.scrapers.keys()))
        categories = config.get('categories', ['smartphones'])
        max_products = config.get('max_products', 100)
        parallel = config.get('parallel', True)
        
        start_time = datetime.now()
        
        logger.info("🎯 Scraping con configuración personalizada")
        logger.info(f"Retailers: {retailers}")
        logger.info(f"Categorías: {categories}")
        
        tasks = []
        
        for retailer in retailers:
            for category in categories:
                if parallel:
                    # Ejecutar en paralelo
                    task = self.scrape_retailer(retailer, category, max_products)
                    tasks.append(task)
                else:
                    # Ejecutar secuencialmente
                    await self.scrape_retailer(retailer, category, max_products)
        
        if parallel and tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Finalizar
        await self.processor.finish_processing()
        self.stats.execution_time = (datetime.now() - start_time).total_seconds()
        
        return self.stats
    
    async def close(self):
        """Cierra el orquestador y libera recursos"""
        await self.processor.close()
        logger.info("🔒 Orchestrator cerrado")


# Función de conveniencia para ejecución simple
async def orchestrate_scraping(
    retailers: Optional[List[str]] = None,
    category: str = "smartphones",
    max_products: int = 100
) -> Dict:
    """
    Función de conveniencia para orquestar scraping
    
    Args:
        retailers: Lista de retailers a scrapear (None = todos)
        category: Categoría a scrapear
        max_products: Máximo de productos por retailer
        
    Returns:
        Dict con estadísticas
    """
    orchestrator = ScrapingOrchestrator()
    
    try:
        if retailers:
            # Configuración específica
            config = {
                'retailers': retailers,
                'categories': [category],
                'max_products': max_products,
                'parallel': True
            }
            stats = await orchestrator.scrape_with_config(config)
        else:
            # Todos los retailers
            stats = await orchestrator.scrape_all_retailers(category, max_products)
        
        return stats.__dict__
        
    finally:
        await orchestrator.close()


# Testing
if __name__ == "__main__":
    import asyncio
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    print("=" * 70)
    print("🎯 TESTING SCRAPING ORCHESTRATOR")
    print("=" * 70)
    
    async def test_orchestrator():
        """Test del orquestador"""
        
        # Crear orquestador
        orchestrator = ScrapingOrchestrator(
            enable_excel_backup=True,
            batch_size=50
        )
        
        # Test 1: Un solo retailer
        print("\n📋 Test 1: Scraping de Falabella")
        result = await orchestrator.scrape_retailer(
            retailer='falabella',
            category='smartphones',
            max_products=10
        )
        print(f"Resultado: {result}")
        
        # Test 2: Múltiples retailers
        print("\n📋 Test 2: Scraping de múltiples retailers")
        config = {
            'retailers': ['falabella', 'ripley'],
            'categories': ['smartphones'],
            'max_products': 5,
            'parallel': True
        }
        stats = await orchestrator.scrape_with_config(config)
        
        # Test 3: Todos los retailers (si tienes tiempo)
        # print("\n📋 Test 3: Todos los retailers")
        # stats = await orchestrator.scrape_all_retailers(
        #     category='smartphones',
        #     max_products_per_retailer=3
        # )
        
        # Cerrar
        await orchestrator.close()
        
        print("\n✅ Testing completado")

    # Ejecutar tests
    asyncio.run(test_orchestrator())
