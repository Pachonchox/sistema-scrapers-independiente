#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Retailer Test Runner - Sistema de Testing Específico por Retailer
===================================================================

Framework integrado para testing automatizado y validación de scrapers.
Incluye tests específicos por retailer, validación de campos y debugging.

Features:
- 🎯 Tests específicos por retailer
- 📊 Validación de estructura de datos
- 🔍 Testing de selectores CSS
- 📈 Performance benchmarking
- 🛠️ Debugging tools integrados
- 📝 Reportes detallados con emojis

Author: Portable Orchestrator Team
Version: 5.0.0
"""

import sys
import os
import io
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import traceback

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """📊 Resultado de un test individual"""
    test_name: str
    retailer: str
    success: bool
    duration: float
    products_found: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class RetailerTestSuite:
    """🏪 Suite de tests para un retailer específico"""
    retailer: str
    test_url: str
    expected_fields: List[str]
    min_products: int = 5
    max_duration: int = 60  # segundos
    custom_selectors: Dict[str, str] = None
    
    def __post_init__(self):
        if self.custom_selectors is None:
            self.custom_selectors = {}

class RetailerTestRunner:
    """
    🎯 Test Runner Principal para Scrapers por Retailer
    
    Sistema completo de testing automatizado que valida:
    - Funcionalidad básica de scraping
    - Estructura de datos extraídos
    - Performance y velocidad
    - Detección de errores recurrentes
    - Calidad de selectores CSS
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        🚀 Inicializar Test Runner
        
        Args:
            config_path: Ruta al archivo de configuración de tests
        """
        self.config_path = config_path
        self.test_results: List[TestResult] = []
        self.retailer_suites: Dict[str, RetailerTestSuite] = {}
        self.start_time = None
        self.end_time = None
        
        # Configurar directorio de logs de tests
        self.logs_dir = Path("logs/testing")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar directorio de screenshots de fallos
        self.screenshots_dir = Path("logs/testing/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎯 RetailerTestRunner iniciado correctamente")
        
    def load_test_config(self) -> None:
        """
        📋 Cargar configuración de tests desde archivo
        
        Define los tests específicos por retailer incluyendo:
        - URLs de testing
        - Campos esperados
        - Criterios de validación
        """
        # Configuración por defecto para retailers chilenos
        self.retailer_suites = {
            'ripley': RetailerTestSuite(
                retailer='ripley',
                test_url='https://simple.ripley.cl/celulares-y-telefonia/celulares',
                expected_fields=['nombre', 'precio_normal', 'precio_tarjeta', 'marca', 'sku', 'link'],
                min_products=10,
                max_duration=45
            ),
            'falabella': RetailerTestSuite(
                retailer='falabella',
                test_url='https://www.falabella.com/falabella-cl/category/cat40051/Celulares',
                expected_fields=['nombre', 'precio', 'marca', 'sku', 'link'],
                min_products=8,
                max_duration=50
            ),
            'paris': RetailerTestSuite(
                retailer='paris',
                test_url='https://www.paris.cl/tecnologia/celulares-y-telefonia/smartphones/',
                expected_fields=['nombre', 'precio', 'marca', 'link'],
                min_products=5,
                max_duration=40
            ),
            'hites': RetailerTestSuite(
                retailer='hites',
                test_url='https://www.hites.com/tecnologia/celulares-y-telefonia',
                expected_fields=['nombre', 'precio', 'marca', 'link'],
                min_products=5,
                max_duration=35
            ),
            'abcdin': RetailerTestSuite(
                retailer='abcdin',
                test_url='https://www.abcdin.cl/categorias/telefonia/celulares',
                expected_fields=['nombre', 'precio', 'marca', 'link'],
                min_products=5,
                max_duration=30
            ),
            'mercadolibre': RetailerTestSuite(
                retailer='mercadolibre',
                test_url='https://listado.mercadolibre.cl/celulares-telefonia/celulares-smartphones/',
                expected_fields=['nombre', 'precio', 'link'],
                min_products=15,
                max_duration=25
            )
        }
        
        logger.info(f"📋 Cargadas {len(self.retailer_suites)} suites de test")
        
    async def run_retailer_test(self, retailer: str, scraper_instance: Any) -> TestResult:
        """
        🏪 Ejecutar test completo para un retailer específico
        
        Args:
            retailer: Nombre del retailer
            scraper_instance: Instancia del scraper a testear
            
        Returns:
            TestResult: Resultado detallado del test
        """
        if retailer not in self.retailer_suites:
            error_msg = f"❌ Retailer '{retailer}' no tiene suite de test definida"
            logger.error(error_msg)
            return TestResult(
                test_name="retailer_validation",
                retailer=retailer,
                success=False,
                duration=0.0,
                errors=[error_msg]
            )
            
        suite = self.retailer_suites[retailer]
        start_time = datetime.now()
        
        logger.info(f"🧪 Iniciando test para {retailer.upper()}")
        logger.info(f"🔗 URL de test: {suite.test_url}")
        
        try:
            # 1. Test de conectividad básica
            connectivity_result = await self._test_connectivity(retailer, suite)
            
            # 2. Test de extracción de datos
            extraction_result = await self._test_data_extraction(
                retailer, suite, scraper_instance
            )
            
            # 3. Test de validación de campos
            validation_result = await self._test_field_validation(
                retailer, suite, extraction_result.metadata.get('products', [])
            )
            
            # 4. Test de performance
            performance_result = await self._test_performance(retailer, suite)
            
            # Compilar resultado final
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            all_errors = []
            all_warnings = []
            products_found = extraction_result.metadata.get('product_count', 0)
            
            # Consolidar errores y warnings
            for result in [connectivity_result, extraction_result, validation_result, performance_result]:
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
            
            # Determinar éxito general
            success = len(all_errors) == 0 and products_found >= suite.min_products
            
            final_result = TestResult(
                test_name="full_retailer_test",
                retailer=retailer,
                success=success,
                duration=duration,
                products_found=products_found,
                errors=all_errors,
                warnings=all_warnings,
                metadata={
                    'connectivity': connectivity_result.success,
                    'extraction': extraction_result.success,
                    'validation': validation_result.success,
                    'performance': performance_result.success,
                    'products_found': products_found,
                    'test_url': suite.test_url
                }
            )
            
            # Log resultado
            status_emoji = "✅" if success else "❌"
            logger.info(f"{status_emoji} Test {retailer.upper()} completado en {duration:.2f}s")
            logger.info(f"📊 Productos encontrados: {products_found}")
            
            if all_errors:
                logger.error(f"🚨 Errores encontrados: {len(all_errors)}")
                for error in all_errors:
                    logger.error(f"   - {error}")
                    
            if all_warnings:
                logger.warning(f"⚠️  Warnings: {len(all_warnings)}")
                for warning in all_warnings:
                    logger.warning(f"   - {warning}")
            
            return final_result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"💥 Error inesperado en test de {retailer}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            
            return TestResult(
                test_name="full_retailer_test",
                retailer=retailer,
                success=False,
                duration=duration,
                errors=[error_msg]
            )
    
    async def _test_connectivity(self, retailer: str, suite: RetailerTestSuite) -> TestResult:
        """🔗 Test básico de conectividad"""
        try:
            # Implementar test básico de conectividad
            # Por ahora retorna success
            return TestResult(
                test_name="connectivity",
                retailer=retailer,
                success=True,
                duration=1.0
            )
        except Exception as e:
            return TestResult(
                test_name="connectivity",
                retailer=retailer,
                success=False,
                duration=0.0,
                errors=[f"Error de conectividad: {str(e)}"]
            )
    
    async def _test_data_extraction(self, retailer: str, suite: RetailerTestSuite, 
                                  scraper_instance: Any) -> TestResult:
        """📊 Test de extracción de datos"""
        try:
            # Simular extracción de datos
            # En implementación real, usaría scraper_instance
            products = []  # Resultado de scraping
            
            return TestResult(
                test_name="data_extraction", 
                retailer=retailer,
                success=len(products) > 0,
                duration=10.0,
                metadata={'products': products, 'product_count': len(products)}
            )
        except Exception as e:
            return TestResult(
                test_name="data_extraction",
                retailer=retailer,
                success=False,
                duration=0.0,
                errors=[f"Error en extracción: {str(e)}"]
            )
    
    async def _test_field_validation(self, retailer: str, suite: RetailerTestSuite,
                                   products: List[Dict]) -> TestResult:
        """✅ Test de validación de campos"""
        errors = []
        warnings = []
        
        if not products:
            errors.append("No hay productos para validar campos")
            return TestResult(
                test_name="field_validation",
                retailer=retailer, 
                success=False,
                duration=0.1,
                errors=errors
            )
        
        # Validar campos esperados en cada producto
        for i, product in enumerate(products[:5]):  # Solo primeros 5
            for field in suite.expected_fields:
                if field not in product:
                    errors.append(f"Producto {i}: Falta campo '{field}'")
                elif not product[field]:
                    warnings.append(f"Producto {i}: Campo '{field}' está vacío")
        
        return TestResult(
            test_name="field_validation",
            retailer=retailer,
            success=len(errors) == 0,
            duration=0.5,
            errors=errors,
            warnings=warnings
        )
    
    async def _test_performance(self, retailer: str, suite: RetailerTestSuite) -> TestResult:
        """⚡ Test de performance"""
        # Implementar test de performance
        return TestResult(
            test_name="performance",
            retailer=retailer,
            success=True,
            duration=1.0
        )
    
    async def run_all_tests(self, scrapers: Dict[str, Any]) -> Dict[str, TestResult]:
        """
        🚀 Ejecutar todos los tests disponibles
        
        Args:
            scrapers: Diccionario de instancias de scrapers por retailer
            
        Returns:
            Dict con resultados de todos los tests
        """
        self.start_time = datetime.now()
        logger.info("🎯 Iniciando suite completa de tests")
        logger.info(f"📅 Timestamp: {self.start_time.isoformat()}")
        
        # Cargar configuración
        self.load_test_config()
        
        results = {}
        total_retailers = len(self.retailer_suites)
        
        for i, retailer in enumerate(self.retailer_suites.keys(), 1):
            logger.info(f"📊 Progreso: {i}/{total_retailers} - {retailer.upper()}")
            
            scraper_instance = scrapers.get(retailer)
            if not scraper_instance:
                logger.warning(f"⚠️  No hay scraper disponible para {retailer}")
                results[retailer] = TestResult(
                    test_name="full_retailer_test",
                    retailer=retailer,
                    success=False,
                    duration=0.0,
                    errors=["No hay instancia de scraper disponible"]
                )
                continue
            
            # Ejecutar test del retailer
            result = await self.run_retailer_test(retailer, scraper_instance)
            results[retailer] = result
            self.test_results.append(result)
            
            # Pausa entre tests
            if i < total_retailers:
                logger.info("⏱️  Pausa entre tests (3s)")
                await asyncio.sleep(3)
        
        self.end_time = datetime.now()
        
        # Generar reporte final
        await self._generate_test_report(results)
        
        return results
    
    async def _generate_test_report(self, results: Dict[str, TestResult]) -> None:
        """📝 Generar reporte detallado de tests"""
        total_duration = (self.end_time - self.start_time).total_seconds()
        successful_tests = sum(1 for r in results.values() if r.success)
        total_tests = len(results)
        total_products = sum(r.products_found for r in results.values())
        
        logger.info("=" * 60)
        logger.info("📊 REPORTE FINAL DE TESTS")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duración total: {total_duration:.2f}s")
        logger.info(f"✅ Tests exitosos: {successful_tests}/{total_tests}")
        logger.info(f"📦 Productos encontrados: {total_products}")
        logger.info("")
        
        # Detalle por retailer
        for retailer, result in results.items():
            status_emoji = "✅" if result.success else "❌"
            logger.info(f"{status_emoji} {retailer.upper()}: {result.products_found} productos en {result.duration:.2f}s")
            
            if result.errors:
                for error in result.errors:
                    logger.info(f"   🚨 {error}")
            
            if result.warnings:
                for warning in result.warnings:
                    logger.info(f"   ⚠️  {warning}")
        
        # Guardar reporte en archivo
        report_file = self.logs_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'timestamp': self.start_time.isoformat(),
            'duration': total_duration,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'total_products': total_products,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0
            },
            'results': {
                retailer: {
                    'success': result.success,
                    'duration': result.duration,
                    'products_found': result.products_found,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'metadata': result.metadata
                }
                for retailer, result in results.items()
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Reporte guardado: {report_file}")
        logger.info("=" * 60)

# 🎯 FUNCIONES DE UTILIDAD PARA TESTING RÁPIDO

async def quick_retailer_test(retailer: str, scraper_instance: Any = None) -> bool:
    """
    ⚡ Test rápido de un solo retailer
    
    Args:
        retailer: Nombre del retailer a testear
        scraper_instance: Instancia del scraper (opcional)
        
    Returns:
        bool: True si el test fue exitoso
    """
    runner = RetailerTestRunner()
    runner.load_test_config()
    
    if retailer not in runner.retailer_suites:
        logger.error(f"❌ Retailer '{retailer}' no disponible")
        return False
    
    result = await runner.run_retailer_test(retailer, scraper_instance)
    return result.success

async def test_all_retailers(scrapers: Dict[str, Any] = None) -> Dict[str, bool]:
    """
    🚀 Test rápido de todos los retailers
    
    Args:
        scrapers: Diccionario de instancias de scrapers
        
    Returns:
        Dict con resultados de éxito por retailer
    """
    if scrapers is None:
        scrapers = {}
    
    runner = RetailerTestRunner()
    results = await runner.run_all_tests(scrapers)
    
    return {retailer: result.success for retailer, result in results.items()}

if __name__ == "__main__":
    """🧪 Ejecutar tests desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🧪 Scraper v5 Test Runner")
    parser.add_argument('--retailer', help='Testear retailer específico')
    parser.add_argument('--all', action='store_true', help='Testear todos los retailers')
    parser.add_argument('--config', help='Archivo de configuración custom')
    
    args = parser.parse_args()
    
    async def main():
        if args.retailer:
            success = await quick_retailer_test(args.retailer)
            exit(0 if success else 1)
        elif args.all:
            results = await test_all_retailers()
            success_count = sum(results.values())
            logger.info(f"🎯 Resultado final: {success_count}/{len(results)} retailers exitosos")
            exit(0 if success_count == len(results) else 1)
        else:
            parser.print_help()
    
    asyncio.run(main())