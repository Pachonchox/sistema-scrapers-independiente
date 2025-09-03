# -*- coding: utf-8 -*-
"""
Test de Validación de Campos - Scraper v5
=========================================
Asegura que todos los scrapers generen los mismos campos que el Excel original
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
from unittest.mock import Mock, patch, AsyncMock
import logging

# Agregar rutas al path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'portable_orchestrator_clean'))

from scrapers.ripley_scraper_v5 import RipleyScraperV5
from scrapers.falabella_scraper_v5 import FalabellaScraperV5  
from scrapers.paris_scraper_v5 import ParisScraperV5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 🎯 CAMPOS REQUERIDOS DEL EXCEL ORIGINAL
REQUIRED_FIELDS = {
    'link',           # URL del producto
    'nombre',         # Nombre del producto (no 'title'!)
    'sku',            # SKU/código del producto
    'precio_normal',  # Precio normal como texto
    'precio_oferta',  # Precio oferta como texto
    'precio_tarjeta', # Precio tarjeta como texto
    'precio_normal_num',   # Precio normal numérico
    'precio_oferta_num',   # Precio oferta numérico
    'precio_tarjeta_num',  # Precio tarjeta numérico
    'precio_min_num',      # Precio mínimo calculado
    'tipo_precio_min',     # Tipo del precio mínimo
    'retailer',            # Nombre del retailer
    'category',            # Categoría del producto
    'fecha_captura'        # Fecha de captura
}

# Campos opcionales pero esperados
OPTIONAL_FIELDS = {
    'marca',          # Marca del producto
    'imagen',         # URL de imagen
    'descripcion',    # Descripción
    'disponibilidad', # Estado de disponibilidad
    'rating',         # Calificación
    'reviews'         # Número de reseñas
}

class FieldValidator:
    """🔍 Validador de campos de productos"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_product(self, product: Dict[str, Any], retailer: str) -> bool:
        """Valida que un producto tenga todos los campos requeridos"""
        self.errors.clear()
        self.warnings.clear()
        
        # Verificar campos requeridos
        missing_fields = REQUIRED_FIELDS - set(product.keys())
        if missing_fields:
            self.errors.append(f"❌ Campos faltantes para {retailer}: {missing_fields}")
            return False
            
        # Validar tipos de datos
        if not self._validate_field_types(product, retailer):
            return False
            
        # Validar consistencia de precios
        if not self._validate_price_consistency(product, retailer):
            return False
            
        # Verificar campos opcionales (solo warning)
        missing_optional = OPTIONAL_FIELDS - set(product.keys())
        if missing_optional:
            self.warnings.append(f"⚠️ Campos opcionales faltantes: {missing_optional}")
            
        return True
    
    def _validate_field_types(self, product: Dict, retailer: str) -> bool:
        """Valida tipos de datos de campos críticos"""
        # Verificar que los campos numéricos sean números
        numeric_fields = ['precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num', 'precio_min_num']
        
        for field in numeric_fields:
            value = product.get(field)
            if value is not None and not isinstance(value, (int, float)):
                self.errors.append(f"❌ {field} debe ser numérico, es {type(value).__name__}")
                return False
                
        # Verificar strings requeridos
        string_fields = ['nombre', 'link', 'retailer', 'category', 'fecha_captura']
        for field in string_fields:
            value = product.get(field)
            if not value or not isinstance(value, str):
                self.errors.append(f"❌ {field} debe ser string no vacío")
                return False
                
        return True
    
    def _validate_price_consistency(self, product: Dict, retailer: str) -> bool:
        """Valida consistencia entre precios"""
        # precio_min_num debe ser el menor de los precios disponibles
        prices = []
        
        for field in ['precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num']:
            value = product.get(field)
            if value and value > 0:
                prices.append(value)
                
        if prices:
            expected_min = min(prices)
            actual_min = product.get('precio_min_num', 0)
            
            if abs(actual_min - expected_min) > 0.01:  # Tolerancia para float
                self.errors.append(
                    f"❌ precio_min_num incorrecto: {actual_min} != {expected_min}"
                )
                return False
                
            # Verificar tipo_precio_min
            if actual_min == product.get('precio_tarjeta_num'):
                expected_type = 'tarjeta'
            elif actual_min == product.get('precio_oferta_num'):
                expected_type = 'oferta'
            else:
                expected_type = 'normal'
                
            if product.get('tipo_precio_min') != expected_type:
                self.errors.append(
                    f"❌ tipo_precio_min incorrecto: {product.get('tipo_precio_min')} != {expected_type}"
                )
                return False
                
        return True


class ScraperFieldTester:
    """🧪 Tester de campos de scrapers"""
    
    def __init__(self):
        self.validator = FieldValidator()
        self.results = {}
        
    async def test_ripley_scraper(self) -> Dict[str, Any]:
        """Test del scraper de Ripley"""
        logger.info("\n🏪 TESTEANDO RIPLEY SCRAPER")
        logger.info("="*50)
        
        scraper = RipleyScraperV5()
        
        # Mock de Playwright
        with patch('scrapers.ripley_scraper_v5.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            
            # Configurar mocks
            mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            
            # Simular HTML de producto Ripley
            mock_page.content = AsyncMock(return_value=self._get_ripley_test_html())
            mock_page.query_selector_all = AsyncMock(return_value=[
                self._create_mock_element_ripley()
            ])
            
            # Ejecutar scraping simulado
            products = await scraper._process_test_products(mock_page, 'computacion-notebooks')
            
            # Validar productos
            test_result = {
                'retailer': 'Ripley',
                'products_found': len(products),
                'validation_passed': True,
                'errors': [],
                'warnings': []
            }
            
            for i, product in enumerate(products):
                logger.info(f"\nValidando producto {i+1}/{len(products)}")
                if self.validator.validate_product(product, 'Ripley'):
                    logger.info(f"✅ Producto válido: {product.get('nombre', 'Sin nombre')[:50]}...")
                else:
                    test_result['validation_passed'] = False
                    test_result['errors'].extend(self.validator.errors)
                    logger.error(f"❌ Producto inválido")
                    for error in self.validator.errors:
                        logger.error(f"  {error}")
                        
                test_result['warnings'].extend(self.validator.warnings)
                
            # Mostrar campos del primer producto como ejemplo
            if products:
                logger.info("\n📋 Campos del primer producto:")
                for field in sorted(products[0].keys()):
                    value = products[0][field]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    logger.info(f"  {field}: {value}")
                    
            return test_result
            
    async def test_falabella_scraper(self) -> Dict[str, Any]:
        """Test del scraper de Falabella"""
        logger.info("\n🏬 TESTEANDO FALABELLA SCRAPER")
        logger.info("="*50)
        
        scraper = FalabellaScraperV5()
        
        with patch('scrapers.falabella_scraper_v5.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            
            # Simular HTML de Falabella
            mock_page.content = AsyncMock(return_value=self._get_falabella_test_html())
            mock_page.query_selector_all = AsyncMock(return_value=[
                self._create_mock_element_falabella()
            ])
            
            products = await scraper._process_test_products(mock_page, 'tecnologia-notebooks')
            
            test_result = {
                'retailer': 'Falabella',
                'products_found': len(products),
                'validation_passed': True,
                'errors': [],
                'warnings': []
            }
            
            for i, product in enumerate(products):
                logger.info(f"\nValidando producto {i+1}/{len(products)}")
                if self.validator.validate_product(product, 'Falabella'):
                    logger.info(f"✅ Producto válido: {product.get('nombre', '')[:50]}...")
                else:
                    test_result['validation_passed'] = False
                    test_result['errors'].extend(self.validator.errors)
                    
                test_result['warnings'].extend(self.validator.warnings)
                
            return test_result
            
    async def test_paris_scraper(self) -> Dict[str, Any]:
        """Test del scraper de Paris"""
        logger.info("\n🛍️ TESTEANDO PARIS SCRAPER")
        logger.info("="*50)
        
        scraper = ParisScraperV5()
        
        with patch('scrapers.paris_scraper_v5.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.content = AsyncMock(return_value=self._get_paris_test_html())
            mock_page.query_selector_all = AsyncMock(return_value=[
                self._create_mock_element_paris()
            ])
            
            products = await scraper._process_test_products(mock_page, 'tecnologia-computadores')
            
            test_result = {
                'retailer': 'Paris',
                'products_found': len(products),
                'validation_passed': True,
                'errors': [],
                'warnings': []
            }
            
            for i, product in enumerate(products):
                logger.info(f"\nValidando producto {i+1}/{len(products)}")
                if self.validator.validate_product(product, 'Paris'):
                    logger.info(f"✅ Producto válido: {product.get('nombre', '')[:50]}...")
                else:
                    test_result['validation_passed'] = False
                    test_result['errors'].extend(self.validator.errors)
                    
                test_result['warnings'].extend(self.validator.warnings)
                
            return test_result
    
    def _get_ripley_test_html(self) -> str:
        """HTML de prueba para Ripley"""
        return '''
        <div class="catalog-product-item">
            <a href="/notebook-test-123" class="catalog-product-item__name">
                Notebook Lenovo IdeaPad 3 AMD Ryzen 5 8GB RAM 512GB SSD
            </a>
            <div class="catalog-prices">
                <li class="catalog-prices__offer-price">$599.990</li>
                <li class="catalog-prices__list-price">$799.990</li>
                <li class="catalog-prices__card-price">CMR $549.990</li>
            </div>
        </div>
        '''
    
    def _get_falabella_test_html(self) -> str:
        """HTML de prueba para Falabella"""
        return '''
        <div class="pod-item">
            <a href="/product/123456" class="pod-link">
                <span class="pod-title">MacBook Air M2 13" 8GB RAM 256GB SSD</span>
            </a>
            <div class="prices">
                <span class="price-0">$ 1.099.990</span>
                <span class="price-1">Normal: $ 1.299.990</span>
            </div>
        </div>
        '''
        
    def _get_paris_test_html(self) -> str:
        """HTML de prueba para Paris"""
        return '''
        <div class="product-item">
            <a href="/producto/gaming-laptop" class="product-link">
                <h3>Laptop Gamer ASUS ROG 16GB RAM RTX 4060</h3>
            </a>
            <div class="product-prices">
                <span class="price-normal">$1.599.990</span>
                <span class="price-internet">Internet $1.399.990</span>
                <span class="price-card">Tarjeta Cencosud $1.299.990</span>
            </div>
        </div>
        '''
        
    def _create_mock_element_ripley(self):
        """Crear elemento mock de Ripley"""
        element = Mock()
        element.query_selector = Mock(side_effect=lambda selector: {
            'a[href]': Mock(get_attribute=Mock(return_value='/notebook-test-123')),
            '.catalog-product-item__name': Mock(text_content=Mock(return_value='Notebook Lenovo IdeaPad')),
            '.catalog-prices__offer-price': Mock(text_content=Mock(return_value='$599.990')),
            '.catalog-prices__list-price': Mock(text_content=Mock(return_value='$799.990')),
            '.catalog-prices__card-price': Mock(text_content=Mock(return_value='CMR $549.990')),
        }.get(selector))
        return element
        
    def _create_mock_element_falabella(self):
        """Crear elemento mock de Falabella"""
        element = Mock()
        element.query_selector = Mock(side_effect=lambda selector: {
            'a[href]': Mock(get_attribute=Mock(return_value='/product/123456')),
            '.pod-title': Mock(text_content=Mock(return_value='MacBook Air M2')),
            '.price-0': Mock(text_content=Mock(return_value='$ 1.099.990')),
            '.price-1': Mock(text_content=Mock(return_value='Normal: $ 1.299.990')),
        }.get(selector))
        return element
        
    def _create_mock_element_paris(self):
        """Crear elemento mock de Paris"""
        element = Mock()
        element.query_selector = Mock(side_effect=lambda selector: {
            'a[href]': Mock(get_attribute=Mock(return_value='/producto/gaming-laptop')),
            'h3': Mock(text_content=Mock(return_value='Laptop Gamer ASUS')),
            '.price-normal': Mock(text_content=Mock(return_value='$1.599.990')),
            '.price-internet': Mock(text_content=Mock(return_value='Internet $1.399.990')),
            '.price-card': Mock(text_content=Mock(return_value='Tarjeta Cencosud $1.299.990')),
        }.get(selector))
        return element


async def run_all_tests():
    """🚀 Ejecutar todos los tests de campos"""
    logger.info("\n" + "="*60)
    logger.info("🧪 INICIANDO TESTS DE VALIDACIÓN DE CAMPOS v5")
    logger.info("="*60)
    
    tester = ScraperFieldTester()
    results = {}
    
    # Test cada scraper
    try:
        results['ripley'] = await tester.test_ripley_scraper()
    except Exception as e:
        logger.error(f"Error en test Ripley: {e}")
        results['ripley'] = {'error': str(e), 'validation_passed': False}
        
    try:
        results['falabella'] = await tester.test_falabella_scraper()
    except Exception as e:
        logger.error(f"Error en test Falabella: {e}")
        results['falabella'] = {'error': str(e), 'validation_passed': False}
        
    try:
        results['paris'] = await tester.test_paris_scraper()
    except Exception as e:
        logger.error(f"Error en test Paris: {e}")
        results['paris'] = {'error': str(e), 'validation_passed': False}
    
    # Resumen final
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMEN DE RESULTADOS")
    logger.info("="*60)
    
    all_passed = True
    for retailer, result in results.items():
        status = "✅ PASÓ" if result.get('validation_passed') else "❌ FALLÓ"
        logger.info(f"\n{retailer.upper()}: {status}")
        
        if 'error' in result:
            logger.error(f"  Error: {result['error']}")
        else:
            logger.info(f"  Productos encontrados: {result.get('products_found', 0)}")
            if result.get('errors'):
                logger.error(f"  Errores: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Mostrar primeros 3
                    logger.error(f"    - {error}")
            if result.get('warnings'):
                logger.warning(f"  Advertencias: {len(result['warnings'])}")
                
        all_passed = all_passed and result.get('validation_passed', False)
    
    logger.info("\n" + "="*60)
    if all_passed:
        logger.info("🎉 TODOS LOS TESTS PASARON - CAMPOS COMPATIBLES CON EXCEL")
    else:
        logger.error("⚠️ ALGUNOS TESTS FALLARON - REVISAR CAMPOS")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    # Ejecutar tests
    results = asyncio.run(run_all_tests())
    
    # Guardar resultados
    output_file = Path(__file__).parent / 'field_validation_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Resultados guardados en: {output_file}")
    
    # Exit code basado en resultados
    sys.exit(0 if all(r.get('validation_passed') for r in results.values()) else 1)