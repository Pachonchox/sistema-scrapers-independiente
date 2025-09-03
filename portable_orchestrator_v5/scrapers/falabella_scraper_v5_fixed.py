# -*- coding: utf-8 -*-
"""
Falabella Chile Scraper v5 - Versión Corregida con Método del Portable
======================================================================

Scraper para Falabella basado exactamente en el método del portable scraper
que funciona correctamente y extrae 56 productos.

Características:
- Usa selectores verificados del portable scraper
- Busca contenedores div[class*="search-results"][class*="grid-pod"]
- Extrae productos usando a[data-key] como identificador principal
- Maneja precios con data-cmr-price y data-internet-price
- Extrae vendedor, badges, ratings y especificaciones

Autor: Sistema Scraper v5 (Migrado del portable scraper funcional)
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import Page, ElementHandle

from ..core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
from ..core.exceptions import *

logger = logging.getLogger(__name__)

# Patterns del portable scraper
PRICE_RE = re.compile(r'\$\s*([\d.,]+)')
WHITESPACE_RE = re.compile(r'\s+')

class FalabellaScraperV5(BaseScraperV5):
    """Scraper Falabella v5 - Con método del portable funcional"""
    
    def __init__(self):
        super().__init__("falabella")
        
        # URLs base
        self.base_urls = {
            'home': 'https://www.falabella.com/falabella-cl',
            'search': 'https://www.falabella.com/falabella-cl/search'
        }
        
        # Configuración específica
        self.falabella_config = {
            'page_timeout': 60000,
            'initial_wait': 10000,  # 10 segundos como el portable
            'scroll_wait': 3000,     # 3 segundos entre scrolls
            'scroll_steps': 3,       # 3 pasos de scroll como el portable
            'batch_size': 10
        }
        
        # Mapeo de categorías
        self.category_mapping = {
            'smartphones': 'https://www.falabella.com/falabella-cl/category/cat720161/Smartphones',
            'computadores': 'https://www.falabella.com/falabella-cl/category/cat40052/Computadores',
            'smart_tv': 'https://www.falabella.com/falabella-cl/category/cat7190148/Smart-TV',
            'tablets': 'https://www.falabella.com/falabella-cl/category/cat7230007/Tablets'
        }
        
        self.logger.info("Falabella Scraper v5 inicializado con método del portable")

    async def scrape_category(
        self, 
        category: str,
        max_products: int = 100,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """Scraper categoría con método del portable"""
        
        start_time = datetime.now()
        session_id = f"falabella_v5_{category}_{int(start_time.timestamp())}"
        
        try:
            # Obtener URL de categoría
            category_url = self.category_mapping.get(category)
            if not category_url:
                raise ValueError(f"Categoría no soportada: {category}")
            
            self.logger.info(f"Scraping Falabella categoría {category}: {category_url}")
            
            # Configurar página
            page = await self.get_page()
            
            # Navegar a la URL
            self.logger.info(f"Navegando a: {category_url}")
            await page.goto(category_url, wait_until='domcontentloaded', timeout=self.falabella_config['page_timeout'])
            
            # Esperar carga inicial (10 segundos como el portable)
            self.logger.info("Esperando carga de productos...")
            await page.wait_for_timeout(self.falabella_config['initial_wait'])
            
            # Hacer scroll progresivo como el portable
            self.logger.info("Haciendo scroll para cargar productos...")
            for i in range(self.falabella_config['scroll_steps']):
                scroll_position = (i + 1) / self.falabella_config['scroll_steps']
                await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {scroll_position})")
                await page.wait_for_timeout(self.falabella_config['scroll_wait'])
            
            # Extraer productos
            products = await self._extract_products_portable_method(page, max_products)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = ScrapingResult(
                success=True,
                products=products,
                total_found=len(products),
                execution_time=execution_time,
                session_id=session_id,
                source_url=category_url,
                retailer=self.retailer,
                category=category,
                timestamp=datetime.now(),
                metadata={
                    'scraping_method': 'portable_method',
                    'scroll_steps': self.falabella_config['scroll_steps']
                }
            )
            
            self.logger.info(f"Falabella scraping completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"Error scraping Falabella: {e}")
            
            return ScrapingResult(
                success=False,
                products=[],
                total_found=0,
                execution_time=execution_time,
                session_id=session_id,
                source_url=category_url if 'category_url' in locals() else '',
                retailer=self.retailer,
                category=category,
                timestamp=datetime.now(),
                error_message=str(e),
                metadata={'error_type': type(e).__name__}
            )

    async def _extract_products_portable_method(self, page: Page, max_products: int) -> List[ProductData]:
        """Extraer productos usando método exacto del portable scraper"""
        
        products = []
        
        self.logger.info("=== BUSCANDO PRODUCTOS FALABELLA ===")
        
        # Buscar contenedores de productos (método del portable)
        # Primero buscar divs con clase search-results y grid-pod
        product_containers = await page.query_selector_all('div[class*="search-results"][class*="grid-pod"]')
        
        self.logger.info(f"Contenedores de productos encontrados: {len(product_containers)}")
        
        for container in product_containers[:max_products]:
            try:
                # Buscar el link principal con data-key
                main_link = await container.query_selector('a[data-key]')
                if not main_link:
                    continue
                
                # Extraer data-key como ID
                product_id = await main_link.get_attribute('data-key')
                product_url = await main_link.get_attribute('href')
                
                self.logger.debug(f"Analizando producto ID: {product_id}")
                
                # Extraer todos los datos en una evaluación
                product_data = await container.evaluate('''
                    (element) => {
                        // Extraer marca
                        const brandEl = element.querySelector('b[class*="pod-title"]');
                        const brand = brandEl ? brandEl.textContent.trim() : '';
                        
                        // Extraer nombre del producto
                        const nameEl = element.querySelector('b[class*="pod-subTitle"]');
                        const productName = nameEl ? nameEl.textContent.trim() : '';
                        
                        // Extraer vendedor
                        const sellerEl = element.querySelector('b[class*="pod-sellerText"]');
                        const seller = sellerEl ? sellerEl.textContent.trim() : '';
                        
                        // Extraer imagen
                        const imgEl = element.querySelector('img');
                        const imageUrl = imgEl ? imgEl.src : '';
                        const imageAlt = imgEl ? imgEl.alt : '';
                        
                        // Extraer precio CMR
                        const cmrPriceEl = element.querySelector('li[data-cmr-price]');
                        const cmrPrice = cmrPriceEl ? cmrPriceEl.getAttribute('data-cmr-price') : '';
                        
                        // Extraer precio Internet
                        const internetPriceEl = element.querySelector('li[data-internet-price]');
                        const internetPrice = internetPriceEl ? internetPriceEl.getAttribute('data-internet-price') : '';
                        
                        // Extraer rating
                        const ratingEl = element.querySelector('div[data-rating]');
                        const rating = ratingEl ? ratingEl.getAttribute('data-rating') : '0';
                        
                        // Extraer reviews
                        const reviewsEl = element.querySelector('span[class*="reviewCount"]');
                        const reviewsText = reviewsEl ? reviewsEl.textContent.trim() : '(0)';
                        const reviewsMatch = reviewsText.match(/\\((\\d+)\\)/);
                        const reviewsCount = reviewsMatch ? reviewsMatch[1] : '0';
                        
                        // Extraer badges
                        const badges = [];
                        const badgeElements = element.querySelectorAll('span[class*="pod-badges-item"]');
                        badgeElements.forEach(badge => {
                            const text = badge.textContent.trim();
                            if (text) badges.push(text);
                        });
                        
                        // Verificar si es patrocinado
                        const sponsoredEl = element.querySelector('div[class*="patrocinado"]');
                        const isSponsored = !!sponsoredEl;
                        
                        // Extraer especificaciones del nombre
                        const nameToSearch = productName.toLowerCase();
                        
                        // Storage
                        let storage = '';
                        const storageMatch = nameToSearch.match(/(\\d+)gb/);
                        if (storageMatch) {
                            storage = storageMatch[1] + 'GB';
                        }
                        
                        // RAM
                        let ram = '';
                        const ramMatch = nameToSearch.match(/(\\d+)\\+(\\d+)gb/);
                        if (ramMatch) {
                            ram = ramMatch[1] + 'GB';
                            if (!storage) {
                                storage = ramMatch[2] + 'GB';
                            }
                        }
                        
                        // Color
                        let color = '';
                        const colors = ['negro', 'blanco', 'azul', 'rojo', 'verde', 'gris', 
                                      'dorado', 'plateado', 'purple', 'rosa'];
                        for (const colorName of colors) {
                            if (nameToSearch.includes(colorName)) {
                                color = colorName.charAt(0).toUpperCase() + colorName.slice(1);
                                break;
                            }
                        }
                        
                        return {
                            brand: brand,
                            productName: productName,
                            seller: seller,
                            imageUrl: imageUrl,
                            imageAlt: imageAlt,
                            cmrPrice: cmrPrice,
                            internetPrice: internetPrice,
                            rating: rating,
                            reviewsCount: reviewsCount,
                            badges: badges,
                            isSponsored: isSponsored,
                            storage: storage,
                            ram: ram,
                            color: color
                        };
                    }
                ''')
                
                # Procesar precios
                cmr_price_numeric = 0
                internet_price_numeric = 0
                
                if product_data['cmrPrice']:
                    try:
                        cmr_price_numeric = int(float(product_data['cmrPrice'].replace(',', '')))
                    except:
                        pass
                
                if product_data['internetPrice']:
                    try:
                        internet_price_numeric = int(float(product_data['internetPrice'].replace(',', '')))
                    except:
                        pass
                
                # Determinar precio actual
                current_price = cmr_price_numeric if cmr_price_numeric > 0 else internet_price_numeric
                original_price = internet_price_numeric if internet_price_numeric > current_price else current_price
                
                # Calcular descuento
                discount_percentage = 0
                if original_price > current_price > 0:
                    discount_percentage = int(((original_price - current_price) / original_price) * 100)
                
                # Construir URL completa
                full_url = ""
                if product_url:
                    full_url = urljoin(self.base_urls['home'], product_url)
                
                # Crear ProductData
                product = ProductData(
                    title=f"{product_data['brand']} {product_data['productName']}".strip(),
                    current_price=float(current_price),
                    original_price=float(original_price),
                    discount_percentage=discount_percentage,
                    currency="CLP",
                    availability="in_stock",
                    product_url=full_url,
                    image_urls=[product_data['imageUrl']] if product_data['imageUrl'] else [],
                    brand=product_data['brand'],
                    sku=product_id,
                    rating=float(product_data['rating']),
                    retailer=self.retailer,
                    extraction_timestamp=datetime.now(),
                    additional_info={
                        'extraction_method': 'portable_method',
                        'seller': product_data['seller'],
                        'storage': product_data['storage'],
                        'ram': product_data['ram'],
                        'color': product_data['color'],
                        'reviews_count': int(product_data['reviewsCount']),
                        'is_sponsored': product_data['isSponsored'],
                        'badges': product_data['badges'],
                        'cmr_price': product_data['cmrPrice'],
                        'internet_price': product_data['internetPrice'],
                        'image_alt': product_data['imageAlt']
                    }
                )
                
                products.append(product)
                
                self.logger.info(f"  [OK] ID: {product_id}")
                self.logger.info(f"  [OK] Marca: {product_data['brand']}")
                self.logger.info(f"  [OK] Nombre: {product_data['productName'][:50]}...")
                self.logger.info(f"  [OK] Precio CMR: ${product_data['cmrPrice']}")
                self.logger.info(f"  [OK] Precio Internet: ${product_data['internetPrice']}")
                
            except Exception as e:
                self.logger.error(f"  [ERROR] procesando contenedor: {e}")
                continue
        
        self.logger.info(f"=== RESULTADOS FALABELLA ===")
        self.logger.info(f"Total productos encontrados: {len(products)}")
        
        return products

    async def search_products(
        self,
        query: str,
        max_products: int = 50,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """Búsqueda de productos"""
        
        start_time = datetime.now()
        session_id = f"falabella_search_v5_{query[:20]}_{int(start_time.timestamp())}"
        
        try:
            # URL de búsqueda
            search_url = f"{self.base_urls['search']}?q={query}"
            
            self.logger.info(f"Búsqueda Falabella: '{query}' - {search_url}")
            
            # Usar misma lógica que categoría
            page = await self.get_page()
            
            # Navegar
            await page.goto(search_url, wait_until='domcontentloaded', timeout=self.falabella_config['page_timeout'])
            
            # Esperar y scroll
            await page.wait_for_timeout(self.falabella_config['initial_wait'])
            
            for i in range(self.falabella_config['scroll_steps']):
                scroll_position = (i + 1) / self.falabella_config['scroll_steps']
                await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {scroll_position})")
                await page.wait_for_timeout(self.falabella_config['scroll_wait'])
            
            # Extraer productos
            products = await self._extract_products_portable_method(page, max_products)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = ScrapingResult(
                success=True,
                products=products,
                total_found=len(products),
                execution_time=execution_time,
                session_id=session_id,
                source_url=search_url,
                retailer=self.retailer,
                category=f"search_{query}",
                timestamp=datetime.now(),
                metadata={'search_query': query}
            )
            
            self.logger.info(f"Búsqueda completada: {len(products)} productos para '{query}'")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ScrapingResult(
                success=False,
                products=[],
                total_found=0,
                execution_time=execution_time,
                session_id=session_id,
                source_url=search_url if 'search_url' in locals() else '',
                retailer=self.retailer,
                category=f"search_{query}",
                timestamp=datetime.now(),
                error_message=str(e),
                metadata={'search_query': query, 'error_type': type(e).__name__}
            )