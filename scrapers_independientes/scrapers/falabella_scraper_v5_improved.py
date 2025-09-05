# -*- coding: utf-8 -*-
"""
🛒 Falabella Chile Scraper v5 MEJORADO - Integración de Selectores PORT
=====================================================================

INTEGRA SELECTORES EXACTOS DE scrappers_port/falabella_scraper.py que SÍ FUNCIONAN
en la arquitectura V5 con Playwright async, aplicando las mismas optimizaciones
exitosas implementadas para Paris, Ripley, Hites y AbcDin.

✅ SELECTORES ESPECÍFICOS MIGRADOS:
- div[class*="search-results"][class*="grid-pod"] (selector principal)
- a[data-key] (identificador producto)
- b[class*="pod-title"] (marca)
- b[class*="pod-subTitle"] (nombre producto)
- b[class*="pod-sellerText"] (vendedor)
- li[data-cmr-price] (precio tarjeta CMR)
- li[data-internet-price] (precio internet)

✅ LÓGICA DE PARSING MIGRADA:
- Extracción por data attributes (data-key, data-cmr-price, data-internet-price)
- Parsing de precios múltiples (CMR vs Internet)
- Manejo de especificaciones (storage, RAM, color)
- Detección de productos patrocinados
- Rating y reviews con contadores
- Badges promocionales y envío

🎯 OBJETIVO: 100% compatibilidad con scraper PORT que SÍ EXTRAE DATOS
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import Page, ElementHandle

# Importaciones para sistema independiente
try:
    from core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
    from core.utils import *
except ImportError:
    # Fallback para testing independiente sin core
    class BaseScraperV5:
        def __init__(self, retailer): 
            self.retailer = retailer
            self.logger = logging.getLogger(__name__)
        async def get_page(self): pass
    
    class ProductData:
        def __init__(self, **kwargs): 
            for k, v in kwargs.items(): 
                setattr(self, k, v)
    
    class ScrapingResult:
        def __init__(self, **kwargs): 
            for k, v in kwargs.items(): 
                setattr(self, k, v)

logger = logging.getLogger(__name__)

# ======================================
# SELECTORES EXACTOS DEL PORT (FUNCIONALES) 
# ======================================

# Selector principal (el que SÍ encuentra productos en Falabella)
PRODUCT_CONTAINER_SELECTOR = "div[class*='search-results'][class*='grid-pod']"

# Selectores de datos específicos (del PORT funcional)
FALABELLA_SELECTORS = {
    'main_link': 'a[data-key]',
    'brand': 'b[class*="pod-title"]',
    'name': 'b[class*="pod-subTitle"]', 
    'seller': 'b[class*="pod-sellerText"]',
    'image': 'img',
    'price_cmr': 'li[data-cmr-price]',
    'price_internet': 'li[data-internet-price]',
    'rating': 'div[data-rating]',
    'reviews': 'span[class*="reviewCount"]',
    'badges': 'span[class*="pod-badges-item"]',
    'sponsored': 'div[class*="patrocinado"]'
}

# Palabras clave para detección de colores (del PORT)
COLOR_KEYWORDS = ['negro', 'blanco', 'azul', 'rojo', 'verde', 'gris', 'dorado', 'plateado', 'purple', 'rosa']

class FalabellaScraperV5Improved(BaseScraperV5):
    """🛒 Scraper Falabella V5 con selectores PORT integrados y optimizados"""
    
    def __init__(self):
        super().__init__("falabella")
        
        # URLs exactas (del PORT)
        self.base_urls = {
            'home': 'https://www.falabella.com/falabella-cl',
            'celulares': 'https://www.falabella.com/falabella-cl/category/cat720161/Smartphones',
            'search': 'https://www.falabella.com/falabella-cl/search'
        }
        
        # Configuración específica de Falabella
        self.config = {
            'batch_size': 10,
            'element_timeout': 15000,
            'scroll_delay': 200,
            'scroll_step': 300,
            'page_timeout': 30000
        }

    async def scrape_products(self, max_products: int = 100) -> ScrapingResult:
        """🚀 Scraper principal con método PORT optimizado"""
        
        logger.info(f"🛒 Iniciando Falabella scraper V5 mejorado - max_products: {max_products}")
        
        page = None
        try:
            page = await self.get_page()
            
            # URL de celulares
            url = self.base_urls['celulares']
            logger.info(f"📱 Navegando a: {url}")
            
            await page.goto(url, timeout=self.config['page_timeout'])
            await page.wait_for_timeout(3000)  # Esperar carga inicial
            
            # Scroll para cargar productos dinámicamente
            await self._scroll_to_load_products(page)
            
            # Extraer productos con método PORT optimizado
            products = await self._extract_products_port_optimized(page)
            
            # Limitar resultados
            if len(products) > max_products:
                products = products[:max_products]
            
            logger.info(f"✅ Falabella: {len(products)} productos extraídos con campos completos")
            
            return ScrapingResult(
                success=True,
                products=products,
                total_found=len(products),
                retailer=self.retailer,
                extraction_time=datetime.now(),
                metadata={'method': 'port_optimized', 'url': url}
            )
            
        except Exception as e:
            logger.error(f"❌ Error crítico en Falabella scraper: {e}")
            return ScrapingResult(
                success=False,
                products=[],
                error=str(e),
                retailer=self.retailer
            )
        finally:
            if page:
                await page.close()

    async def _scroll_to_load_products(self, page: Page):
        """📜 Scroll para cargar productos dinámicamente"""
        
        try:
            logger.info("📜 Scrolling para cargar productos...")
            
            # Obtener altura inicial
            initial_height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            # Hacer scroll gradual (3 pantallas como PORT)
            for i in range(3):
                scroll_to = int(initial_height * ((i + 1) / 3))
                await page.evaluate(f'window.scrollTo(0, {scroll_to})')
                await page.wait_for_timeout(3000)  # 3s como PORT
                
                logger.debug(f"📜 Scroll {i+1}/3: {scroll_to}px")
            
            # Esperar carga final
            await page.wait_for_timeout(2000)
            logger.info("✅ Scroll completado")
            
        except Exception as e:
            logger.error(f"❌ Error en scroll: {e}")

    async def _extract_products_port_optimized(self, page: Page) -> List[ProductData]:
        """📋 Extraer productos con selectores PORT optimizados"""
        
        products = []
        
        try:
            # Buscar contenedores con selector exacto del PORT
            await page.wait_for_selector(PRODUCT_CONTAINER_SELECTOR, timeout=self.config['element_timeout'])
            containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
            
            total_containers = len(containers)
            logger.info(f"🔍 Contenedores encontrados con selector PORT: {total_containers}")
            
            if total_containers == 0:
                return products
            
            # Procesar cada contenedor (lógica PORT adaptada y optimizada)
            successful = 0
            batch_size = self.config['batch_size']
            
            for i in range(0, total_containers, batch_size):
                batch = containers[i:min(i + batch_size, total_containers)]
                
                for j, container in enumerate(batch):
                    try:
                        product = await self._extract_single_product_port_optimized(container, i + j)
                        if product:
                            products.append(product)
                            successful += 1
                            
                    except Exception as e:
                        logger.debug(f"⚠️ Error procesando contenedor {i + j}: {e}")
                        continue
                
                # Cleanup handles del batch
                for container in batch:
                    try:
                        await container.dispose()
                    except:
                        pass
                
                # Delay entre batches
                if i + batch_size < total_containers:
                    await page.wait_for_timeout(100)
            
            logger.info(f"✅ Productos procesados con método PORT optimizado: {successful}/{total_containers}")
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo productos método PORT optimizado: {e}")
        
        return products

    async def _extract_single_product_port_optimized(self, container: ElementHandle, index: int) -> Optional[ProductData]:
        """📋 Extraer producto individual con TODOS los campos del scrapers_port/falabella_scraper.py"""
        
        try:
            # ==========================================
            # EXTRACCIÓN COMPLETA - TODOS LOS CAMPOS DEL PORT
            # ==========================================
            
            # 1. Link principal y product_id - exacto como PORT: a[data-key]
            product_id = ""
            product_url = ""
            try:
                main_link = await container.query_selector(FALABELLA_SELECTORS['main_link'])
                if main_link:
                    product_id = await main_link.get_attribute('data-key')
                    product_url = await main_link.get_attribute('href')
                    
                    if not product_id:
                        return None
            except:
                return None
            
            # 2. Marca - selector exacto PORT: b[class*="pod-title"]
            brand = ""
            try:
                brand_element = await container.query_selector(FALABELLA_SELECTORS['brand'])
                if brand_element:
                    brand = await brand_element.inner_text()
                    brand = brand.strip()
            except:
                pass
            
            # 3. Nombre del producto - selector exacto PORT: b[class*="pod-subTitle"]
            product_name = ""
            try:
                name_element = await container.query_selector(FALABELLA_SELECTORS['name'])
                if name_element:
                    product_name = await name_element.inner_text()
                    product_name = product_name.strip()
            except:
                pass
            
            if not product_name:
                return None
            
            # 4. Vendedor - selector exacto PORT: b[class*="pod-sellerText"]
            seller = ""
            try:
                seller_element = await container.query_selector(FALABELLA_SELECTORS['seller'])
                if seller_element:
                    seller = await seller_element.inner_text()
                    seller = seller.strip()
            except:
                pass
            
            # ==========================================
            # 5. IMAGEN - EXACTO COMO PORT
            # ==========================================
            image_url = ""
            image_alt = ""
            try:
                img_element = await container.query_selector(FALABELLA_SELECTORS['image'])
                if img_element:
                    src = await img_element.get_attribute('src')
                    alt = await img_element.get_attribute('alt')
                    if src:
                        image_url = src
                    if alt:
                        image_alt = alt
            except:
                pass
            
            # ==========================================
            # 6. PRECIOS - EXACTO COMO PORT CON DATA ATTRIBUTES
            # ==========================================
            
            # Precio CMR - selector: li[data-cmr-price]
            cmr_price = ""
            cmr_price_numeric = None
            try:
                cmr_element = await container.query_selector(FALABELLA_SELECTORS['price_cmr'])
                if cmr_element:
                    cmr_price = await cmr_element.get_attribute('data-cmr-price')
                    if cmr_price:
                        # Procesamiento exacto como PORT
                        try:
                            cmr_price_numeric = int(float(cmr_price.replace(',', '')))
                        except:
                            pass
            except:
                pass
            
            # Precio Internet - selector: li[data-internet-price]
            internet_price = ""
            internet_price_numeric = None
            try:
                internet_element = await container.query_selector(FALABELLA_SELECTORS['price_internet'])
                if internet_element:
                    internet_price = await internet_element.get_attribute('data-internet-price')
                    if internet_price:
                        # Procesamiento exacto como PORT
                        try:
                            internet_price_numeric = int(float(internet_price.replace(',', '')))
                        except:
                            pass
            except:
                pass
            
            # ==========================================
            # 7. RATING Y REVIEWS - EXACTO COMO PORT
            # ==========================================
            
            # Rating - selector: div[data-rating]
            rating = "0"
            try:
                rating_element = await container.query_selector(FALABELLA_SELECTORS['rating'])
                if rating_element:
                    rating = await rating_element.get_attribute('data-rating')
                    if not rating:
                        rating = "0"
            except:
                pass
            
            # Reviews - selector: span[class*="reviewCount"] + regex
            reviews = "0"
            try:
                reviews_element = await container.query_selector(FALABELLA_SELECTORS['reviews'])
                if reviews_element:
                    reviews_text = await reviews_element.inner_text()
                    # Regex exacto como PORT: r'\((\d+)\)'
                    reviews_match = re.search(r'\((\d+)\)', reviews_text)
                    if reviews_match:
                        reviews = reviews_match.group(1)
            except:
                pass
            
            # ==========================================
            # 8. BADGES PROMOCIONALES - EXACTO COMO PORT
            # ==========================================
            badges = []
            try:
                badge_elements = await container.query_selector_all(FALABELLA_SELECTORS['badges'])
                for badge_element in badge_elements:
                    badge_text = await badge_element.inner_text()
                    if badge_text.strip():
                        badges.append(badge_text.strip())
            except:
                pass
            
            # ==========================================
            # 9. PRODUCTO PATROCINADO - EXACTO COMO PORT
            # ==========================================
            is_sponsored = False
            try:
                sponsored_element = await container.query_selector(FALABELLA_SELECTORS['sponsored'])
                is_sponsored = sponsored_element is not None  # bool() como PORT
            except:
                pass
            
            # ==========================================
            # 10. ESPECIFICACIONES - REGEX EXACTOS DEL PORT
            # ==========================================
            storage = ""
            ram = ""
            color = ""
            
            if product_name:
                # Storage - regex PORT: r'(\d+)gb'
                storage_match = re.search(r'(\d+)gb', product_name.lower())
                if storage_match:
                    storage = f"{storage_match.group(1)}GB"
                
                # RAM - regex PORT: r'(\d+)\+(\d+)gb' (formato específico)
                ram_match = re.search(r'(\d+)\+(\d+)gb', product_name.lower())
                if ram_match:
                    ram = f"{ram_match.group(1)}GB"
                    if not storage:  # Si no encontramos storage antes, usar el segundo número
                        storage = f"{ram_match.group(2)}GB"
                
                # Color - lista exacta del PORT
                for color_name in COLOR_KEYWORDS:
                    if color_name in product_name.lower():
                        color = color_name.title()
                        break
            
            # ==========================================
            # 11. VALIDACIÓN FINAL - EXACTO COMO PORT
            # ==========================================
            # Solo agregar productos válidos (condición del PORT)
            if not (product_id and product_name):
                return None
            
            # ==========================================
            # 12. CREAR PRODUCTO CON ESTRUCTURA EXACTA DEL PORT
            # ==========================================
            
            # Construir título completo
            title_parts = []
            if brand:
                title_parts.append(brand)
            if product_name:
                title_parts.append(product_name)
            title = " ".join(title_parts)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Determinar precio principal (CMR o internet, el menor disponible)
            available_prices = [p for p in [cmr_price_numeric, internet_price_numeric] if p and p > 0]
            if not available_prices:
                return None
                
            current_price = float(min(available_prices))
            original_price = float(internet_price_numeric or max(available_prices))
            
            # Calcular descuento si hay diferencia
            discount_percentage = 0
            if original_price and current_price and original_price > current_price:
                discount_percentage = int(((original_price - current_price) / original_price) * 100)
            
            product = ProductData(
                title=title,
                current_price=current_price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                currency="CLP",
                availability="in_stock",
                product_url=product_url,
                image_urls=[image_url] if image_url else [],
                brand=brand,
                sku=product_id,
                rating=float(rating) if rating and rating.replace('.', '').isdigit() else 0.0,
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info={
                    'extraction_method': 'port_complete_fields',
                    'container_index': index,
                    
                    # ==== TODOS LOS CAMPOS DEL PORT ORIGINAL ====
                    'product_id': product_id,
                    'brand': brand,
                    'name': product_name,
                    'seller': seller,
                    'storage': storage,
                    'ram': ram,
                    'color': color,
                    
                    # Precios con string y numérico (exacto como PORT)
                    'cmr_price': cmr_price,
                    'cmr_price_numeric': cmr_price_numeric,
                    'internet_price': internet_price,
                    'internet_price_numeric': internet_price_numeric,
                    
                    # Rating y reviews
                    'rating': rating,
                    'reviews_count': reviews,
                    
                    # Otros campos PORT
                    'is_sponsored': is_sponsored,
                    'badges': ', '.join(badges) if badges else "",
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'product_url': product_url,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return product
            
        except Exception as e:
            logger.debug(f"⚠️ Error extrayendo producto individual: {e}")
            return None

# Test function
async def test_falabella_scraper():
    """🧪 Test del scraper Falabella independiente"""
    scraper = FalabellaScraperV5Improved()
    result = await scraper.scrape_products(max_products=20)
    
    print(f"✅ Productos encontrados: {len(result.products)}")
    for i, product in enumerate(result.products[:3], 1):
        print(f"{i}. {product.title}")
        print(f"   Precio: ${product.current_price:,.0f}")
        print(f"   Marca: {product.brand}")

if __name__ == "__main__":
    asyncio.run(test_falabella_scraper())