# -*- coding: utf-8 -*-
"""
🏪 ABCDIN SCRAPER V5 - BASADO EN MÉTODO PORTABLE
===============================================
Scraper para AbcDin implementado con método portable verificado
Integrado con sistema V5 usando Playwright

Extrae productos de:
- Smartphones: /tecnologia/celulares/smartphones/
- Tablets: /tecnologia/tablets/
- Computadores: /tecnologia/computadores/notebooks/
- TV: /tecnologia/television/

Método de extracción:
- Contenedores: div.lp-product-tile.js-lp-product-tile
- Extracción de datos GTM para IDs
- Múltiples tipos de precios: La Polar, Internet, Normal
- Especificaciones técnicas detalladas
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import Page

from ..core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
from ..core.exceptions import *


class AbcdinScraperV5(BaseScraperV5):
    """🏪 Scraper AbcDin V5 usando método portable verificado"""
    
    def __init__(self):
        super().__init__("abcdin")
        
        self.base_urls = {
            'home': 'https://www.abc.cl',
            'smartphones': 'https://www.abc.cl/tecnologia/celulares/smartphones/',
            'tablets': 'https://www.abc.cl/tecnologia/tablets/',
            'computadores': 'https://www.abc.cl/tecnologia/computadores/notebooks/',
            'television': 'https://www.abc.cl/tecnologia/television/'
        }
        
        # Mapa de categorías V5
        self.category_mapping = {
            'celulares': 'smartphones',
            'computadores': 'computadores',
            'televisores': 'television',
            'tablets': 'tablets'
        }
        
        self.logger.info("🏪 AbcDin Scraper V5 inicializado con método portable")

    async def scrape_category(self, category: str, max_products: int = 30, filters: Dict[str, Any] = None) -> ScrapingResult:
        """🎯 Scraper principal usando método portable"""
        
        # Mapear categoría
        abcdin_category = self.category_mapping.get(category, category)
        
        if abcdin_category not in self.base_urls:
            raise CategoryNotSupportedError(f"AbcDin categoría no soportada: {category}")
        
        url = self.base_urls[abcdin_category]
        
        self.logger.info(f"🏪 Scrapeando AbcDin - {category} (max: {max_products})")
        self.logger.info(f"📍 URL: {url}")
        
        try:
            page = await self.get_page()
            
            # Configurar página anti-detección
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-CL,es;q=0.8,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br'
            })
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Esperar carga inicial
            await asyncio.sleep(10)
            
            # Scroll progresivo para cargar productos (método portable)
            self.logger.info("📜 Realizando scroll para cargar productos...")
            for i in range(3):
                scroll_position = f"document.body.scrollHeight * {(i+1)/3}"
                await page.evaluate(f"window.scrollTo(0, {scroll_position});")
                await asyncio.sleep(3)
            
            # Obtener contenido HTML final
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extraer productos usando método portable
            products = await self._extract_products_portable(soup, max_products, category)
            
            result = ScrapingResult(
                success=True,
                products=products,
                total_found=len(products),
                retailer="AbcDin",
                category=category,
                source_url=url
            )
            
            # Añadir metadata manualmente
            result.metadata = {
                'method': 'portable_extraction',
                'containers_found': len(soup.find_all('div', class_='lp-product-tile js-lp-product-tile'))
            }
            
            self.logger.info(f"✅ AbcDin {category}: {len(products)} productos extraídos")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error scrapeando AbcDin {category}: {e}")
            return ScrapingResult(
                success=False,
                products=[],
                error_message=str(e),
                retailer="AbcDin",
                category=category
            )
    
    async def _extract_products_portable(self, soup: BeautifulSoup, max_products: int, category: str) -> List[ProductData]:
        """🔍 Extractor usando método portable verificado"""
        
        products = []
        
        # Buscar contenedores de productos (método portable exacto)
        product_containers = soup.find_all('div', class_='lp-product-tile js-lp-product-tile')
        
        self.logger.info(f"🔍 Contenedores encontrados: {len(product_containers)}")
        
        for i, container in enumerate(product_containers[:max_products]):
            try:
                # Extraer ID del producto desde data-gtm (método portable)
                product_id = self._extract_product_id_from_gtm(container)
                
                # Extraer marca (método portable)
                brand_elem = container.select_one('.brand-name')
                brand = brand_elem.get_text(strip=True) if brand_elem else ""
                
                # Extraer nombre del producto (método portable)
                name_elem = container.select_one('.pdp-link a')
                product_name = ""
                product_url = ""
                if name_elem:
                    product_name = name_elem.get_text(strip=True)
                    product_url = name_elem.get('href', '')
                    if product_url.startswith('/'):
                        product_url = f"https://www.abc.cl{product_url}"
                
                # Extraer imagen (método portable)
                img_elem = container.select_one('.tile-image')
                image_url = img_elem.get('src', '') if img_elem else ""
                image_alt = img_elem.get('alt', '') if img_elem else ""
                
                # Extraer precios múltiples (método portable)
                la_polar_price, internet_price, normal_price = self._extract_prices_portable(container)
                
                # Extraer descuento (método portable)
                discount_elem = container.select_one('.promotion-badge')
                discount_percent = discount_elem.get_text(strip=True) if discount_elem else ""
                
                # Extraer especificaciones técnicas (método portable)
                screen_size, internal_memory, camera_info = self._extract_specs_portable(container)
                
                # Extraer rating y reviews (método portable)
                rating, reviews_count = self._extract_rating_portable(container)
                
                # Extraer badges flotantes (método portable)
                floating_badges = self._extract_floating_badges(container)
                
                # Extraer color del nombre (método portable)
                color = self._extract_color_from_name(product_name)
                
                # Validar producto mínimo
                if not product_name or not product_id:
                    continue
                
                # Usar precio más relevante como precio principal
                main_price = la_polar_price or internet_price or normal_price
                
                # Crear ProductData V5 con campos correctos
                product = ProductData(
                    title=product_name,
                    sku=product_id,
                    brand=brand,
                    current_price=float(main_price) if main_price else 0.0,
                    original_price=float(normal_price) if normal_price else 0.0,
                    card_price=float(la_polar_price) if la_polar_price else 0.0,
                    discount_percentage=int(self._clean_discount(discount_percent) or 0),
                    rating=rating,
                    reviews_count=self._parse_reviews_count(reviews_count),
                    category=category,
                    retailer="AbcDin",
                    availability="in_stock",  # AbcDin no muestra stock en listado
                    product_url=product_url,
                    image_urls=[image_url] if image_url else [],
                    
                    # Información adicional en additional_info
                    additional_info={
                        'screen_size': screen_size,
                        'internal_memory': internal_memory,
                        'camera_info': camera_info,
                        'color': color,
                        'floating_badges': floating_badges,
                        'image_alt': image_alt,
                        'la_polar_price': la_polar_price,
                        'internet_price': internet_price,
                        'normal_price': normal_price,
                        'extraction_method': 'portable'
                    }
                )
                
                products.append(product)
                
                # Debug para primeros productos
                if len(products) <= 3:
                    self.logger.info(f"✅ [{len(products)}] {brand} {product_name[:40]}...")
                    self.logger.info(f"   💰 LP: ${la_polar_price:,} | INT: ${internet_price:,} | NOR: ${normal_price:,}" if main_price else f"   💰 Sin precios | ID: {product_id}")
                    if rating > 0:
                        self.logger.info(f"   ⭐ {rating} estrellas ({reviews_count} reviews)")
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando producto AbcDin [{i+1}]: {e}")
                continue
        
        return products
    
    def _extract_product_id_from_gtm(self, container) -> str:
        """🆔 Extraer ID desde datos GTM (método portable)"""
        product_id = ""
        gtm_click = container.get('data-gtm-click', '')
        if gtm_click:
            try:
                gtm_data = json.loads(gtm_click)
                products_data = gtm_data.get('ecommerce', {}).get('click', {}).get('products', [])
                if products_data:
                    product_id = products_data[0].get('id', '')
            except:
                pass
        return product_id
    
    def _extract_prices_portable(self, container) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """💰 Extraer múltiples precios (método portable)"""
        la_polar_price = None
        internet_price = None
        normal_price = None
        
        # Precio La Polar (con tarjeta) - método portable
        la_polar_elem = container.select_one('.la-polar.price .price-value')
        if la_polar_elem:
            price_value = la_polar_elem.get('data-value', '')
            if price_value:
                try:
                    la_polar_price = int(float(price_value))
                except:
                    pass
        
        # Precio Internet - método portable
        internet_elem = container.select_one('.internet.price .price-value')
        if internet_elem:
            price_value = internet_elem.get('data-value', '')
            if price_value:
                try:
                    internet_price = int(float(price_value))
                except:
                    pass
        
        # Precio Normal - método portable
        normal_elem = container.select_one('.normal.price .price-value')
        if normal_elem:
            price_value = normal_elem.get('data-value', '')
            if price_value:
                try:
                    normal_price = int(float(price_value))
                except:
                    pass
        
        return la_polar_price, internet_price, normal_price
    
    def _extract_specs_portable(self, container) -> Tuple[str, str, str]:
        """📱 Extraer especificaciones técnicas (método portable)"""
        screen_size = ""
        internal_memory = ""
        camera_info = ""
        
        spec_items = container.select('.prices-actions__destacados__items li span')
        for spec in spec_items:
            spec_text = spec.get_text(strip=True)
            if "Tamaño de la pantalla:" in spec_text:
                screen_size = spec_text.replace("Tamaño de la pantalla:", "").strip()
            elif "Memoria interna:" in spec_text:
                internal_memory = spec_text.replace("Memoria interna:", "").strip()
            elif "Cámara posterior:" in spec_text:
                camera_info = spec_text.replace("Cámara posterior:", "").strip()
        
        return screen_size, internal_memory, camera_info
    
    def _extract_rating_portable(self, container) -> Tuple[float, str]:
        """⭐ Extraer rating y reviews (método portable)"""
        rating = 0.0
        reviews_count = ""
        
        # Rating desde Power Reviews - método portable
        rating_elem = container.select_one('.pr-snippet-rating-decimal')
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            try:
                rating = float(rating_text)
            except:
                pass
        
        # Número de reviews - método portable
        reviews_elem = container.select_one('.pr-category-snippet__total')
        if reviews_elem:
            reviews_text = reviews_elem.get_text(strip=True)
            reviews_match = re.search(r'(\d+)', reviews_text)
            if reviews_match:
                reviews_count = reviews_match.group(1)
        
        return rating, reviews_count
    
    def _extract_floating_badges(self, container) -> str:
        """🏷️ Extraer badges flotantes (método portable)"""
        floating_badges = []
        badge_elements = container.select('.floating-badge img, .outstanding-container img')
        
        for badge in badge_elements:
            badge_alt = badge.get('alt', '').strip()
            badge_title = badge.get('title', '').strip()
            if badge_alt and badge_alt not in ['', 'Rosen']:
                floating_badges.append(badge_alt)
            elif badge_title:
                floating_badges.append(badge_title)
        
        return ', '.join(floating_badges)
    
    def _extract_color_from_name(self, product_name: str) -> str:
        """🎨 Extraer color del nombre del producto (método portable)"""
        color_map = {
            "medianoche": "Medianoche",
            "negro": "Negro", "black": "Negro",
            "blanco": "Blanco", "white": "Blanco", 
            "azul": "Azul", "blue": "Azul",
            "rojo": "Rojo", "red": "Rojo",
            "verde": "Verde", "green": "Verde",
            "dorado": "Dorado", "gold": "Dorado",
            "plateado": "Plateado", "silver": "Plateado"
        }
        
        product_name_lower = product_name.lower()
        for keyword, color in color_map.items():
            if keyword in product_name_lower:
                return color
        
        return ""
    
    def _clean_discount(self, discount_text: str) -> Optional[float]:
        """🏷️ Limpiar texto de descuento a porcentaje"""
        if not discount_text:
            return None
        
        # Extraer número del descuento
        match = re.search(r'(\d+)', discount_text)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        
        return None
    
    def _parse_reviews_count(self, reviews_text: str) -> int:
        """📝 Convertir texto de reviews a número"""
        if not reviews_text:
            return 0
        
        try:
            return int(reviews_text)
        except:
            return 0
    
    async def search_products(self, query: str, max_products: int = 50, filters: Dict[str, Any] = None) -> ScrapingResult:
        """🔍 Búsqueda de productos (no implementada para AbcDin)"""
        raise NotImplementedError("🚧 Búsqueda directa no disponible en AbcDin")

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validar extracción de productos"""
        issues = []
        
        if not products:
            issues.append("No se extrajeron productos")
        
        # Validar campos esenciales
        for i, product in enumerate(products[:5]):  # Validar primeros 5
            if not product.title:
                issues.append(f"Producto {i+1}: título vacío")
            if not product.sku:
                issues.append(f"Producto {i+1}: SKU vacío") 
            if not product.current_price:
                issues.append(f"Producto {i+1}: precio vacío")
        
        return len(issues) == 0, issues