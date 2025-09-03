# -*- coding: utf-8 -*-
"""
🏪 HITES SCRAPER V5 - BASADO EN MÉTODO PORTABLE
==============================================
Scraper para Hites implementado con método portable verificado
Integrado con sistema V5 usando Playwright

Extrae productos de:
- Smartphones: /celulares/smartphones/ 
- Tablets: /celulares/tablets/
- Computadores: /computacion/notebooks/
- TV: /television/smart-tv/

Método de extracción:
- Contenedores: div.product-tile-body
- Scroll progresivo para cargar productos
- Extracción completa de specs y precios
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import Page

from ..core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
from ..core.exceptions import *


class HitesScraperV5(BaseScraperV5):
    """🏪 Scraper Hites V5 usando método portable verificado"""
    
    def __init__(self):
        super().__init__("hites")
        
        self.base_urls = {
            'home': 'https://www.hites.com',
            'smartphones': 'https://www.hites.com/celulares/smartphones/',
            'tablets': 'https://www.hites.com/celulares/tablets/', 
            'computadores': 'https://www.hites.com/computacion/notebooks/',
            'television': 'https://www.hites.com/television/smart-tv/'
        }
        
        # Mapa de categorías V5
        self.category_mapping = {
            'celulares': 'smartphones',
            'computadores': 'computadores', 
            'televisores': 'television',
            'tablets': 'tablets'
        }
        
        self.logger.info("🏪 Hites Scraper V5 inicializado con método portable")

    async def scrape_category(self, category: str, max_products: int = 30, filters: Dict[str, Any] = None) -> ScrapingResult:
        """🎯 Scraper principal usando método portable"""
        
        # Mapear categoría
        hites_category = self.category_mapping.get(category, category)
        
        if hites_category not in self.base_urls:
            raise CategoryNotSupportedError(f"Hites categoría no soportada: {category}")
        
        url = self.base_urls[hites_category]
        
        self.logger.info(f"🏪 Scrapeando Hites - {category} (max: {max_products})")
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
            await asyncio.sleep(5)
            
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
                retailer="Hites",
                category=category,
                source_url=url
            )
            
            # Añadir metadata manualmente
            result.metadata = {
                'method': 'portable_extraction',
                'containers_found': len(soup.find_all('div', class_='product-tile-body'))
            }
            
            self.logger.info(f"✅ Hites {category}: {len(products)} productos extraídos")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error scrapeando Hites {category}: {e}")
            return ScrapingResult(
                success=False,
                products=[],
                error_message=str(e),
                retailer="Hites",
                category=category
            )
    
    async def _extract_products_portable(self, soup: BeautifulSoup, max_products: int, category: str) -> List[ProductData]:
        """🔍 Extractor usando método portable verificado"""
        
        products = []
        
        # Buscar contenedores de productos (método portable exacto)
        product_containers = soup.find_all('div', class_='product-tile-body')
        
        self.logger.info(f"🔍 Contenedores encontrados: {len(product_containers)}")
        
        for i, container in enumerate(product_containers[:max_products]):
            try:
                # Extraer marca (método portable)
                brand_elem = container.select_one('.product-brand')
                brand = brand_elem.get_text(strip=True) if brand_elem else ""
                
                # Extraer nombre del producto (método portable)
                name_elem = container.select_one('.product-name--bundle')
                product_name = ""
                product_url = ""
                if name_elem:
                    product_name = name_elem.get_text(strip=True)
                    product_url = name_elem.get('href', '')
                    if product_url.startswith('/'):
                        product_url = f"https://www.hites.com{product_url}"
                
                # Extraer SKU (método portable)
                sku_elem = container.select_one('.product-sku')
                sku = ""
                if sku_elem:
                    sku_text = sku_elem.get_text(strip=True)
                    sku = sku_text.replace("SKU: ", "")
                
                # Extraer vendedor/marketplace (método portable)
                seller_elem = container.select_one('.marketplace-info-plp b')
                seller = seller_elem.get_text(strip=True) if seller_elem else "Hites"
                
                # Extraer especificaciones técnicas (método portable)
                storage, screen_size, front_camera = self._extract_specs_portable(container)
                
                # Extraer precios (método portable)
                current_price, original_price, discount_percent = self._extract_prices_portable(container)
                
                # Extraer rating y reviews (método portable)
                rating, reviews_count = self._extract_rating_portable(container)
                
                # Extraer opciones de envío (método portable)
                shipping_options = self._extract_shipping_portable(container)
                
                # Verificar disponibilidad (método portable)
                out_of_stock = bool(container.select_one('.outofstock'))
                
                # Extraer color del nombre (método portable)
                color = self._extract_color_from_name(product_name)
                
                # Validar producto mínimo
                if not product_name or not sku:
                    continue
                
                # Crear ProductData V5 con campos correctos
                product = ProductData(
                    title=product_name,
                    sku=sku,
                    brand=brand,
                    current_price=float(current_price) if current_price else 0.0,
                    original_price=float(original_price) if original_price else 0.0,
                    discount_percentage=int(self._clean_discount(discount_percent) or 0),
                    rating=rating,
                    reviews_count=self._parse_reviews_count(reviews_count),
                    category=category,
                    retailer="Hites",
                    availability="in_stock" if not out_of_stock else "out_of_stock",
                    product_url=product_url,
                    
                    # Información adicional en additional_info
                    additional_info={
                        'storage': storage,
                        'screen_size': screen_size,
                        'ram': "",  # No disponible en Hites
                        'color': color,
                        'seller': seller,
                        'shipping_options': shipping_options,
                        'front_camera': front_camera,
                        'extraction_method': 'portable'
                    }
                )
                
                products.append(product)
                
                # Debug para primeros productos
                if len(products) <= 3:
                    self.logger.info(f"✅ [{len(products)}] {brand} {product_name[:40]}...")
                    self.logger.info(f"   💰 ${current_price:,} | SKU: {sku}" if current_price else f"   💰 Sin precio | SKU: {sku}")
                    if rating > 0:
                        self.logger.info(f"   ⭐ {rating} estrellas ({reviews_count} reviews)")
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando producto Hites [{i+1}]: {e}")
                continue
        
        return products
    
    def _extract_specs_portable(self, container) -> Tuple[str, str, str]:
        """📱 Extraer especificaciones técnicas (método portable)"""
        storage = ""
        screen_size = ""
        front_camera = ""
        
        attribute_items = container.select('.attribute-values')
        for attr in attribute_items:
            attr_text = attr.get_text(strip=True)
            if "Almacenamiento:" in attr_text:
                storage = attr_text.replace("Almacenamiento:", "").strip()
            elif "Tamaño De Pantalla:" in attr_text:
                screen_size = attr_text.replace("Tamaño De Pantalla:", "").strip()
            elif "Cámara Frontal:" in attr_text:
                front_camera = attr_text.replace("Cámara Frontal:", "").strip()
        
        return storage, screen_size, front_camera
    
    def _extract_prices_portable(self, container) -> Tuple[Optional[int], Optional[int], str]:
        """💰 Extraer precios (método portable)"""
        current_price = None
        original_price = None
        discount_percent = ""
        
        # Precio actual (sales) - método portable
        current_price_elem = container.select_one('.price-item.sales .value')
        if current_price_elem:
            current_price_text = current_price_elem.get_text(strip=True)
            price_content = current_price_elem.get('content', '')
            
            if price_content:
                try:
                    current_price = int(price_content)
                except:
                    pass
            else:
                # Extraer de texto
                price_match = re.search(r'\$?([0-9.,]+)', current_price_text.replace('.', ''))
                if price_match:
                    try:
                        current_price = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
        
        # Precio original (list) - método portable  
        original_price_elem = container.select_one('.price-item.list .value')
        if original_price_elem:
            original_price_text = original_price_elem.get_text(strip=True)
            price_content = original_price_elem.get('content', '')
            
            if price_content:
                try:
                    original_price = int(price_content)
                except:
                    pass
            else:
                # Extraer de texto
                price_match = re.search(r'\$?([0-9.,]+)', original_price_text.replace('.', ''))
                if price_match:
                    try:
                        original_price = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
        
        # Descuento - método portable
        discount_elem = container.select_one('.discount-badge')
        if discount_elem:
            discount_percent = discount_elem.get_text(strip=True)
        
        return current_price, original_price, discount_percent
    
    def _extract_rating_portable(self, container) -> Tuple[float, str]:
        """⭐ Extraer rating y reviews (método portable)"""
        rating = 0
        reviews_count = ""
        
        # Contar estrellas llenas - método portable
        star_elements = container.select('.yotpo-icon-star.rating-star')
        rating = len(star_elements)
        
        # Número de reviews - método portable
        reviews_elem = container.select_one('.yotpo-total-reviews')
        if reviews_elem:
            reviews_text = reviews_elem.get_text(strip=True)
            reviews_match = re.search(r'\((\d+)\)', reviews_text)
            if reviews_match:
                reviews_count = reviews_match.group(1)
        
        return float(rating), reviews_count
    
    def _extract_shipping_portable(self, container) -> str:
        """🚚 Extraer opciones de envío (método portable)"""
        shipping_options = []
        shipping_elements = container.select('.shipping-method .method-description span:first-child')
        
        for shipping in shipping_elements:
            shipping_text = shipping.get_text(strip=True)
            if shipping_text:
                shipping_options.append(shipping_text)
        
        return ', '.join(shipping_options)
    
    def _extract_color_from_name(self, product_name: str) -> str:
        """🎨 Extraer color del nombre del producto (método portable)"""
        color_keywords = [
            'light blue', 'blue', 'azul', 'negro', 'black', 'white', 'blanco',
            'red', 'rojo', 'green', 'verde', 'gray', 'gris', 'gold', 'dorado',
            'silver', 'plateado', 'purple', 'morado', 'pink', 'rosa'
        ]
        
        product_name_lower = product_name.lower()
        for keyword in color_keywords:
            if keyword in product_name_lower:
                return keyword.title()
        
        return ""
    
    def _clean_discount(self, discount_text: str) -> Optional[float]:
        """🏷️ Limpiar texto de descuento a porcentaje"""
        if not discount_text:
            return None
        
        # Extraer número del descuento
        import re
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
        """🔍 Búsqueda de productos (no implementada para Hites)"""
        raise NotImplementedError("🚧 Búsqueda directa no disponible en Hites")

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