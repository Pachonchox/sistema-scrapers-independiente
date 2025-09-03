# -*- coding: utf-8 -*-
"""
🛍️ Ripley Chile Scraper - Scraper Especializado para Ripley
==========================================================

Scraper específico para Ripley Chile con selectores optimizados,
manejo de lazy loading y detección de variantes de productos.

Características específicas de Ripley:
- Sistema de lazy loading con scroll infinito
- Variantes de color/talla en modales
- Precios con descuentos y ofertas especiales
- Sistema de filtros por categoría
- Geolocalización para stock por tienda

Autor: Sistema Scraper v5 🚀
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import Page, Locator
from bs4 import BeautifulSoup

from ..core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
from ..core.exceptions import *


class RipleyScraper(BaseScraperV5):
    """🛍️ Scraper especializado para Ripley Chile"""
    
    def __init__(self):
        super().__init__("ripley")
        
        # URLs base de Ripley
        self.base_urls = {
            'home': 'https://simple.ripley.cl',
            'search': 'https://simple.ripley.cl/search',
            'category': 'https://simple.ripley.cl'
        }
        
        # Selectores específicos de Ripley
        self.selectors = {
            # Contenedores de productos
            'product_grid': '.catalog-container',
            'product_items': '.catalog-product-item',
            'product_card': '[data-testid="product"]',
            
            # Información del producto
            'product_title': '.catalog-product-item__name, .product-title, [data-testid="product-title"]',
            'product_price': '.catalog-product-item__price, .price, [data-testid="product-price"]',
            'original_price': '.catalog-product-item__price--original, .original-price',
            'discount_price': '.catalog-product-item__price--discount, .discount-price',
            'discount_percentage': '.catalog-product-item__discount, .discount-badge',
            'product_link': 'a.catalog-product-item__link, a[data-testid="product-link"]',
            'product_image': '.catalog-product-item__image img, .product-image img',
            'product_brand': '.catalog-product-item__brand, .brand-name',
            'product_rating': '.catalog-product-item__rating, .rating',
            'product_sku': '[data-sku], [data-product-id]',
            
            # Filtros y navegación
            'filters_container': '.filters-container, .sidebar-filters',
            'category_filter': '.filter-category',
            'brand_filter': '.filter-brand',
            'price_filter': '.filter-price',
            'load_more_btn': '.load-more, .show-more, [data-testid="load-more"]',
            'pagination': '.pagination',
            
            # Modal y detalles
            'product_modal': '.product-modal, .modal-product',
            'variant_selector': '.variant-selector, .color-selector',
            'size_selector': '.size-selector',
            'stock_info': '.stock-info, .availability',
            
            # Lazy loading
            'loading_spinner': '.loading, .spinner',
            'infinite_scroll_trigger': '.infinite-scroll-trigger',
            
            # Ofertas especiales
            'flash_sale': '.flash-sale, .oferta-flash',
            'special_offer': '.special-offer, .oferta-especial',
            'ripley_puntos': '.ripley-puntos, .puntos-ripley'
        }
        
        # Patrones de extracción
        self.patterns = {
            'price': [
                r'\$\s*([\d.,]+)',
                r'precio.*?(\d+(?:\.\d{3})*)',
                r'(\d+(?:\.\d{3})*)\s*pesos'
            ],
            'discount': [
                r'(\d+)%\s*desc',
                r'descuento\s*(\d+)%',
                r'-(\d+)%'
            ],
            'sku': [
                r'SKU\s*:?\s*(\w+)',
                r'código\s*:?\s*(\w+)',
                r'ref\s*:?\s*(\w+)'
            ],
            'brand': [
                r'marca\s*:?\s*([^,\n]+)',
                r'fabricante\s*:?\s*([^,\n]+)'
            ]
        }
        
        # Configuración específica de Ripley
        self.config = {
            'scroll_pause_time': 2,
            'max_scroll_attempts': 10,
            'product_load_timeout': 15,
            'lazy_load_delay': 3,
            'modal_timeout': 10,
            'images_per_product': 3,
            'max_variants': 5
        }
        
        # Categorías principales de Ripley
        self.categories = {
            'informatica': '/informatica',
            'electrohogar': '/electrohogar',
            'television': '/television-y-video',
            'audio': '/audio-y-musica',
            'telefonia': '/telefonia-y-gps',
            'videojuegos': '/videojuegos',
            'hogar': '/hogar',
            'dormitorio': '/dormitorio',
            'cocina': '/cocina',
            'baño': '/bano',
            'muebles': '/muebles',
            'decoracion': '/decoracion',
            'iluminacion': '/iluminacion'
        }
        
        self.logger.info("🛍️ Ripley Scraper inicializado correctamente")

    async def scrape_category(
        self, 
        category: str,
        max_products: int = 100,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper categoría específica de Ripley"""
        
        start_time = datetime.now()
        session_id = f"ripley_cat_{category}_{int(start_time.timestamp())}"
        
        try:
            # Construir URL de categoría
            category_path = self.categories.get(category, f'/{category}')
            category_url = urljoin(self.base_urls['home'], category_path)
            
            self.logger.info(f"🔍 Iniciando scraping de categoría {category}: {category_url}")
            
            # Navegar a la página
            page = await self.get_page()
            await page.goto(category_url, wait_until='domcontentloaded', timeout=30000)
            
            # Esperar que carguen los productos iniciales
            await self._wait_for_products_to_load(page)
            
            # Aplicar filtros si se especificaron
            if filters:
                await self._apply_filters(page, filters)
                await self._wait_for_products_to_load(page)
            
            # Realizar scroll para cargar más productos
            await self._perform_infinite_scroll(page, max_products)
            
            # Extraer productos
            products = await self._extract_products_from_page(page, max_products)
            
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
                    'filters_applied': filters or {},
                    'scroll_attempts': getattr(self, '_scroll_count', 0),
                    'lazy_loads_triggered': getattr(self, '_lazy_load_count', 0)
                }
            )
            
            self.logger.info(f"✅ Scraping completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error en scraping de categoría {category}: {e}")
            
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

    async def search_products(
        self,
        query: str,
        max_products: int = 50,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔎 Buscar productos por término de búsqueda"""
        
        start_time = datetime.now()
        session_id = f"ripley_search_{query[:20]}_{int(start_time.timestamp())}"
        
        try:
            # Construir URL de búsqueda
            search_url = f"{self.base_urls['search']}?q={query}"
            
            self.logger.info(f"🔎 Buscando productos: '{query}' en {search_url}")
            
            page = await self.get_page()
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            
            # Verificar si hay resultados
            await self._check_search_results(page, query)
            
            # Esperar carga de productos
            await self._wait_for_products_to_load(page)
            
            # Aplicar filtros adicionales
            if filters:
                await self._apply_filters(page, filters)
                await self._wait_for_products_to_load(page)
            
            # Scroll para más resultados
            await self._perform_infinite_scroll(page, max_products)
            
            # Extraer productos
            products = await self._extract_products_from_page(page, max_products)
            
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
                metadata={
                    'search_query': query,
                    'filters_applied': filters or {},
                    'search_results_count': await self._get_search_results_count(page)
                }
            )
            
            self.logger.info(f"✅ Búsqueda completada: {len(products)} productos para '{query}'")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error en búsqueda '{query}': {e}")
            
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

    async def _wait_for_products_to_load(self, page: Page, timeout: int = None) -> None:
        """⏳ Esperar que los productos se carguen completamente"""
        
        timeout = timeout or self.config['product_load_timeout']
        
        try:
            # Esperar por contenedor de productos
            await page.wait_for_selector(
                self.selectors['product_grid'], 
                timeout=timeout * 1000,
                state='visible'
            )
            
            # Esperar que desaparezca el spinner de carga
            try:
                await page.wait_for_selector(
                    self.selectors['loading_spinner'],
                    timeout=5000,
                    state='hidden'
                )
            except:
                pass  # No hay spinner o ya desapareció
            
            # Esperar un poco más para lazy loading
            await asyncio.sleep(self.config['lazy_load_delay'])
            
            # Verificar que hay productos visibles
            product_count = await page.locator(self.selectors['product_items']).count()
            
            if product_count == 0:
                self.logger.warning("⚠️ No se encontraron productos después de la carga")
            else:
                self.logger.debug(f"✅ {product_count} productos cargados inicialmente")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Timeout esperando productos: {e}")

    async def _apply_filters(self, page: Page, filters: Dict[str, Any]) -> None:
        """🔧 Aplicar filtros de búsqueda/categoría"""
        
        try:
            # Esperar por contenedor de filtros
            await page.wait_for_selector(self.selectors['filters_container'], timeout=10000)
            
            for filter_type, filter_value in filters.items():
                await self._apply_single_filter(page, filter_type, filter_value)
                await asyncio.sleep(1)  # Pausa entre filtros
            
            # Esperar que se apliquen los filtros
            await asyncio.sleep(3)
            
            self.logger.info(f"🔧 Filtros aplicados: {filters}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error aplicando filtros: {e}")

    async def _apply_single_filter(self, page: Page, filter_type: str, filter_value: Any) -> None:
        """🔧 Aplicar un filtro específico"""
        
        try:
            if filter_type == 'brand':
                brand_selector = f"{self.selectors['brand_filter']} input[value='{filter_value}']"
                await page.click(brand_selector)
                
            elif filter_type == 'price_min':
                price_input = f"{self.selectors['price_filter']} input[name='price_min']"
                await page.fill(price_input, str(filter_value))
                
            elif filter_type == 'price_max':
                price_input = f"{self.selectors['price_filter']} input[name='price_max']"
                await page.fill(price_input, str(filter_value))
                
            elif filter_type == 'rating':
                rating_selector = f"{self.selectors['filters_container']} [data-rating='{filter_value}']"
                await page.click(rating_selector)
                
            else:
                self.logger.warning(f"⚠️ Tipo de filtro no reconocido: {filter_type}")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error aplicando filtro {filter_type}: {e}")

    async def _perform_infinite_scroll(self, page: Page, max_products: int) -> None:
        """📜 Realizar scroll infinito para cargar más productos"""
        
        self._scroll_count = 0
        self._lazy_load_count = 0
        
        try:
            last_product_count = 0
            no_change_count = 0
            
            while self._scroll_count < self.config['max_scroll_attempts']:
                # Contar productos actuales
                current_product_count = await page.locator(self.selectors['product_items']).count()
                
                # Si ya tenemos suficientes productos, parar
                if current_product_count >= max_products:
                    self.logger.info(f"📜 Suficientes productos cargados: {current_product_count}")
                    break
                
                # Scroll hacia abajo
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Buscar y clickear botón "cargar más" si existe
                load_more_btn = page.locator(self.selectors['load_more_btn'])
                if await load_more_btn.count() > 0 and await load_more_btn.is_visible():
                    await load_more_btn.click()
                    self._lazy_load_count += 1
                    self.logger.debug("🔄 Botón 'cargar más' clickeado")
                
                # Esperar que carguen nuevos productos
                await asyncio.sleep(self.config['scroll_pause_time'])
                
                # Verificar si se cargaron nuevos productos
                new_product_count = await page.locator(self.selectors['product_items']).count()
                
                if new_product_count == last_product_count:
                    no_change_count += 1
                    if no_change_count >= 3:
                        self.logger.info("📜 No se cargan más productos, terminando scroll")
                        break
                else:
                    no_change_count = 0
                    self.logger.debug(f"📜 Productos cargados: {new_product_count}")
                
                last_product_count = new_product_count
                self._scroll_count += 1
            
            self.logger.info(f"📜 Scroll completado: {self._scroll_count} intentos, {self._lazy_load_count} cargas lazy")
            
        except Exception as e:
            self.logger.error(f"❌ Error en scroll infinito: {e}")

    async def _extract_products_from_page(self, page: Page, max_products: int) -> List[ProductData]:
        """📦 Extraer productos de la página actual"""
        
        products = []
        
        try:
            # Obtener todos los elementos de producto
            product_elements = page.locator(self.selectors['product_items'])
            product_count = await product_elements.count()
            
            self.logger.info(f"📦 Extrayendo datos de {min(product_count, max_products)} productos")
            
            for i in range(min(product_count, max_products)):
                try:
                    product_element = product_elements.nth(i)
                    
                    # Extraer datos básicos del producto
                    product_data = await self._extract_product_data(product_element, page)
                    
                    if product_data:
                        products.append(product_data)
                        
                        if len(products) % 10 == 0:
                            self.logger.debug(f"📦 Extraídos {len(products)} productos...")
                    
                except Exception as e:
                        self.logger.warning(f"⚠️ Error extrayendo producto {i}: {e}")
                        continue
            
            self.logger.info(f"📦 Extracción completada: {len(products)} productos válidos")
            
        except Exception as e:
            self.logger.error(f"❌ Error en extracción de productos: {e}")
        
        return products

    async def _extract_product_data(self, product_element: Locator, page: Page) -> Optional[ProductData]:
        """📋 Extraer datos de un producto individual"""
        
        try:
            # Título del producto
            title = await self._extract_text_with_fallbacks(
                product_element, 
                self.selectors['product_title']
            )
            
            if not title:
                return None
            
            # Precio principal
            price_text = await self._extract_text_with_fallbacks(
                product_element,
                self.selectors['product_price']
            )
            
            current_price = self._parse_price(price_text) if price_text else 0
            
            # Precio original (sin descuento)
            original_price_text = await self._extract_text_with_fallbacks(
                product_element,
                self.selectors['original_price']
            )
            
            original_price = self._parse_price(original_price_text) if original_price_text else current_price
            
            # Porcentaje de descuento
            discount_text = await self._extract_text_with_fallbacks(
                product_element,
                self.selectors['discount_percentage']
            )
            
            discount_percentage = self._parse_discount(discount_text) if discount_text else 0
            
            # URL del producto
            product_url = await self._extract_product_url(product_element)
            
            # Imagen del producto
            image_url = await self._extract_image_url(product_element)
            
            # Marca del producto
            brand = await self._extract_text_with_fallbacks(
                product_element,
                self.selectors['product_brand']
            )
            
            # SKU del producto
            sku = await self._extract_sku(product_element)
            
            # Rating del producto
            rating = await self._extract_rating(product_element)
            
            # Información adicional específica de Ripley
            ripley_info = await self._extract_ripley_specific_info(product_element)
            
            # Crear objeto ProductData
            product = ProductData(
                title=title.strip(),
                current_price=current_price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                currency="CLP",
                availability="in_stock",  # Ripley no muestra productos sin stock
                product_url=product_url,
                image_urls=[image_url] if image_url else [],
                brand=brand.strip() if brand else "",
                sku=sku,
                rating=rating,
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info=ripley_info
            )
            
            return product
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error extrayendo datos de producto: {e}")
            return None

    async def _extract_product_url(self, product_element: Locator) -> str:
        """🔗 Extraer URL del producto"""
        
        try:
            # Intentar extraer el href del link
            link_element = product_element.locator(self.selectors['product_link']).first
            
            if await link_element.count() > 0:
                href = await link_element.get_attribute('href')
                if href:
                    return urljoin(self.base_urls['home'], href)
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo URL: {e}")
            return ""

    async def _extract_image_url(self, product_element: Locator) -> str:
        """🖼️ Extraer URL de imagen del producto"""
        
        try:
            img_element = product_element.locator(self.selectors['product_image']).first
            
            if await img_element.count() > 0:
                # Intentar src primero
                src = await img_element.get_attribute('src')
                if src and src.startswith('http'):
                    return src
                
                # Intentar data-src (lazy loading)
                data_src = await img_element.get_attribute('data-src')
                if data_src and data_src.startswith('http'):
                    return data_src
                
                # Si es relativa, convertir a absoluta
                if src and not src.startswith('http'):
                    return urljoin(self.base_urls['home'], src)
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo imagen: {e}")
            return ""

    async def _extract_sku(self, product_element: Locator) -> str:
        """🏷️ Extraer SKU del producto"""
        
        try:
            # Buscar en atributos data-*
            for attr in ['data-sku', 'data-product-id', 'data-id']:
                sku = await product_element.get_attribute(attr)
                if sku:
                    return sku
            
            # Buscar en texto del elemento
            element_html = await product_element.inner_html()
            
            for pattern in self.patterns['sku']:
                match = re.search(pattern, element_html, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo SKU: {e}")
            return ""

    async def _extract_rating(self, product_element: Locator) -> float:
        """⭐ Extraer rating del producto"""
        
        try:
            rating_element = product_element.locator(self.selectors['product_rating']).first
            
            if await rating_element.count() > 0:
                # Buscar en atributos
                for attr in ['data-rating', 'data-score', 'title']:
                    rating_text = await rating_element.get_attribute(attr)
                    if rating_text:
                        # Extraer número de rating (ej: "4.5 de 5 estrellas")
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            return float(match.group(1))
                
                # Contar estrellas llenas/medias
                stars_filled = await rating_element.locator('.star-filled, .star-full').count()
                stars_half = await rating_element.locator('.star-half').count()
                
                if stars_filled > 0 or stars_half > 0:
                    return stars_filled + (stars_half * 0.5)
            
            return 0.0
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo rating: {e}")
            return 0.0

    async def _extract_ripley_specific_info(self, product_element: Locator) -> Dict[str, Any]:
        """🛍️ Extraer información específica de Ripley"""
        
        ripley_info = {}
        
        try:
            # Puntos Ripley
            ripley_puntos_element = product_element.locator(self.selectors['ripley_puntos']).first
            if await ripley_puntos_element.count() > 0:
                puntos_text = await ripley_puntos_element.inner_text()
                match = re.search(r'(\d+)\s*puntos?', puntos_text, re.IGNORECASE)
                if match:
                    ripley_info['ripley_puntos'] = int(match.group(1))
            
            # Oferta Flash
            flash_sale_element = product_element.locator(self.selectors['flash_sale']).first
            if await flash_sale_element.count() > 0:
                ripley_info['oferta_flash'] = True
                flash_text = await flash_sale_element.inner_text()
                ripley_info['oferta_flash_texto'] = flash_text.strip()
            
            # Oferta Especial
            special_offer_element = product_element.locator(self.selectors['special_offer']).first
            if await special_offer_element.count() > 0:
                ripley_info['oferta_especial'] = True
                offer_text = await special_offer_element.inner_text()
                ripley_info['oferta_especial_texto'] = offer_text.strip()
            
            # Información de envío
            shipping_info = await product_element.locator('.shipping-info, .envio-info').first
            if await shipping_info.count() > 0:
                shipping_text = await shipping_info.inner_text()
                if 'gratis' in shipping_text.lower():
                    ripley_info['envio_gratis'] = True
                ripley_info['info_envio'] = shipping_text.strip()
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo info específica de Ripley: {e}")
        
        return ripley_info

    async def _check_search_results(self, page: Page, query: str) -> None:
        """🔍 Verificar resultados de búsqueda"""
        
        try:
            # Esperar a que cargue la página de resultados
            await asyncio.sleep(2)
            
            # Buscar mensaje de "sin resultados"
            no_results_selectors = [
                '.no-results', '.sin-resultados', '.empty-results',
                ':text("No se encontraron")', ':text("Sin resultados")'
            ]
            
            for selector in no_results_selectors:
                try:
                    no_results = page.locator(selector).first
                    if await no_results.count() > 0 and await no_results.is_visible():
                        raise NoProductsFoundException(f"No se encontraron productos para '{query}' en Ripley")
                except:
                    continue
            
            # Verificar si hay productos
            product_count = await page.locator(self.selectors['product_items']).count()
            if product_count == 0:
                raise NoProductsFoundException(f"No se encontraron productos para '{query}' en Ripley")
            
            self.logger.info(f"✅ Resultados encontrados para '{query}': {product_count} productos iniciales")
            
        except NoProductsFoundException:
            raise
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando resultados de búsqueda: {e}")

    async def _get_search_results_count(self, page: Page) -> int:
        """📊 Obtener número total de resultados de búsqueda"""
        
        try:
            # Buscar contador de resultados
            count_selectors = [
                '.results-count', '.total-results', '.search-results-count',
                ':text-matches("\\d+ resultados?", "i")'
            ]
            
            for selector in count_selectors:
                try:
                    count_element = page.locator(selector).first
                    if await count_element.count() > 0:
                        count_text = await count_element.inner_text()
                        match = re.search(r'(\d+)', count_text)
                        if match:
                            return int(match.group(1))
                except:
                    continue
            
            # Fallback: contar productos visibles
            return await page.locator(self.selectors['product_items']).count()
            
        except Exception as e:
            self.logger.debug(f"Error obteniendo conteo de resultados: {e}")
            return 0

    def _parse_price(self, price_text: str) -> float:
        """💰 Parsear texto de precio a número"""
        
        if not price_text:
            return 0.0
        
        try:
            # Remover texto no numérico excepto puntos y comas
            clean_price = re.sub(r'[^\d.,]', '', price_text)
            
            # Manejar formato chileno (punto como separador de miles, coma como decimal)
            if ',' in clean_price and '.' in clean_price:
                # Formato: 1.234.567,89
                if clean_price.rfind('.') > clean_price.rfind(','):
                    # El punto está después de la coma, es separador decimal
                    clean_price = clean_price.replace(',', '').replace('.', ',')
                else:
                    # La coma está después del punto, es separador decimal normal
                    clean_price = clean_price.replace('.', '')
            
            elif '.' in clean_price:
                # Solo puntos - pueden ser separadores de miles o decimal
                parts = clean_price.split('.')
                if len(parts[-1]) <= 2:  # Última parte tiene 1-2 dígitos, es decimal
                    clean_price = '.'.join(parts[:-1]).replace('.', '') + '.' + parts[-1]
                else:  # Son separadores de miles
                    clean_price = clean_price.replace('.', '')
            
            # Convertir coma decimal a punto
            clean_price = clean_price.replace(',', '.')
            
            return float(clean_price)
            
        except (ValueError, AttributeError) as e:
            self.logger.debug(f"Error parseando precio '{price_text}': {e}")
            return 0.0

    def _parse_discount(self, discount_text: str) -> int:
        """🏷️ Parsear texto de descuento a porcentaje"""
        
        if not discount_text:
            return 0
        
        try:
            for pattern in self.patterns['discount']:
                match = re.search(pattern, discount_text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            # Fallback: buscar cualquier número seguido de %
            match = re.search(r'(\d+)%', discount_text)
            if match:
                return int(match.group(1))
            
            return 0
            
        except (ValueError, AttributeError) as e:
            self.logger.debug(f"Error parseando descuento '{discount_text}': {e}")
            return 0

    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """📋 Obtener detalles completos de un producto específico"""
        
        try:
            self.logger.info(f"📋 Obteniendo detalles de producto: {product_url}")
            
            page = await self.get_page()
            await page.goto(product_url, wait_until='domcontentloaded', timeout=30000)
            
            # Esperar que cargue la página de producto
            await page.wait_for_selector('.product-detail, .product-info', timeout=15000)
            
            # Extraer detalles completos
            details = {
                'url': product_url,
                'retailer': self.retailer,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # Información básica
            details['title'] = await self._extract_text_safe(page, 'h1.product-title, .product-name h1')
            details['description'] = await self._extract_text_safe(page, '.product-description, .description')
            details['brand'] = await self._extract_text_safe(page, '.brand-name, .product-brand')
            details['sku'] = await self._extract_text_safe(page, '.product-sku, [data-sku]')
            
            # Precios
            details['current_price'] = await self._extract_text_safe(page, '.current-price, .price')
            details['original_price'] = await self._extract_text_safe(page, '.original-price, .was-price')
            
            # Imágenes
            details['images'] = await self._extract_product_images(page)
            
            # Especificaciones
            details['specifications'] = await self._extract_specifications(page)
            
            # Stock y disponibilidad
            details['stock_info'] = await self._extract_stock_info(page)
            
            # Variantes (colores, tallas, etc.)
            details['variants'] = await self._extract_variants(page)
            
            # Reviews y rating
            details['reviews'] = await self._extract_reviews_summary(page)
            
            self.logger.info(f"✅ Detalles extraídos para: {details.get('title', 'Producto sin título')}")
            
            return details
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo detalles de producto: {e}")
            return None

    async def _extract_specifications(self, page: Page) -> Dict[str, str]:
        """📋 Extraer especificaciones técnicas del producto"""
        
        specs = {}
        
        try:
            # Buscar tabla de especificaciones
            specs_table = page.locator('.specifications-table, .specs-table, .product-specs')
            
            if await specs_table.count() > 0:
                rows = specs_table.locator('tr, .spec-row')
                row_count = await rows.count()
                
                for i in range(row_count):
                    row = rows.nth(i)
                    
                    # Extraer clave y valor
                    key_elem = row.locator('td:first-child, .spec-key, .spec-name').first
                    value_elem = row.locator('td:last-child, .spec-value').first
                    
                    if await key_elem.count() > 0 and await value_elem.count() > 0:
                        key = (await key_elem.inner_text()).strip()
                        value = (await value_elem.inner_text()).strip()
                        
                        if key and value:
                            specs[key] = value
            
            # Buscar lista de características
            features_list = page.locator('.features-list, .characteristics-list')
            
            if await features_list.count() > 0:
                items = features_list.locator('li, .feature-item')
                item_count = await items.count()
                
                for i in range(item_count):
                    item = items.nth(i)
                    text = (await item.inner_text()).strip()
                    
                    # Intentar separar clave: valor
                    if ':' in text:
                        key, value = text.split(':', 1)
                        specs[key.strip()] = value.strip()
                    else:
                        specs[f"Característica {i+1}"] = text
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo especificaciones: {e}")
        
        return specs

    async def _extract_variants(self, page: Page) -> List[Dict[str, Any]]:
        """🎨 Extraer variantes del producto (colores, tallas, etc.)"""
        
        variants = []
        
        try:
            # Variantes de color
            color_variants = page.locator('.color-selector .color-option, .variant-color')
            color_count = await color_variants.count()
            
            for i in range(min(color_count, self.config['max_variants'])):
                color_elem = color_variants.nth(i)
                
                variant = {
                    'type': 'color',
                    'name': await color_elem.get_attribute('title') or await color_elem.get_attribute('alt') or f"Color {i+1}",
                    'value': await color_elem.get_attribute('data-color') or await color_elem.get_attribute('data-value'),
                    'image_url': await color_elem.get_attribute('data-image') or '',
                    'available': not (await color_elem.get_attribute('disabled'))
                }
                
                variants.append(variant)
            
            # Variantes de talla
            size_variants = page.locator('.size-selector .size-option, .variant-size')
            size_count = await size_variants.count()
            
            for i in range(min(size_count, self.config['max_variants'])):
                size_elem = size_variants.nth(i)
                
                variant = {
                    'type': 'size',
                    'name': (await size_elem.inner_text()).strip() or f"Talla {i+1}",
                    'value': await size_elem.get_attribute('data-size') or await size_elem.get_attribute('data-value'),
                    'available': not (await size_elem.get_attribute('disabled'))
                }
                
                variants.append(variant)
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo variantes: {e}")
        
        return variants

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validar productos extraídos específicamente para Ripley"""
        
        issues = []
        
        if not products:
            issues.append("No se extrajeron productos")
            return False, issues
        
        # Validaciones específicas de Ripley
        for i, product in enumerate(products):
            product_id = f"Producto {i+1}"
            
            # Validar título
            if not product.title or len(product.title) < 5:
                issues.append(f"{product_id}: Título inválido o muy corto")
            
            # Validar precio
            if product.current_price <= 0:
                issues.append(f"{product_id}: Precio inválido ({product.current_price})")
            
            # Validar URL
            if not product.product_url or 'ripley.cl' not in product.product_url:
                issues.append(f"{product_id}: URL inválida o no es de Ripley")
            
            # Validar moneda
            if product.currency != "CLP":
                issues.append(f"{product_id}: Moneda incorrecta ({product.currency})")
            
            # Validar precios lógicos
            if product.original_price > 0 and product.current_price > product.original_price:
                issues.append(f"{product_id}: Precio actual mayor que precio original")
            
            # Validar descuento
            if product.discount_percentage > 0:
                if product.original_price <= 0:
                    issues.append(f"{product_id}: Descuento sin precio original")
                else:
                    calculated_discount = ((product.original_price - product.current_price) / product.original_price) * 100
                    if abs(calculated_discount - product.discount_percentage) > 5:  # Tolerancia de 5%
                        issues.append(f"{product_id}: Descuento inconsistente")
        
        # Validaciones generales
        valid_products = len([p for p in products if p.title and p.current_price > 0])
        if valid_products < len(products) * 0.8:  # Al menos 80% válidos
            issues.append(f"Solo {valid_products}/{len(products)} productos son válidos")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info(f"✅ Validación exitosa: {len(products)} productos válidos de Ripley")
        else:
            self.logger.warning(f"⚠️ Validación con problemas: {len(issues)} issues encontrados")
        
        return is_valid, issues