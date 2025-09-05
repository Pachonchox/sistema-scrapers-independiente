# -*- coding: utf-8 -*-
"""
🏪 AbcDin Chile Scraper v5 MEJORADO - Integración de Selectores PORT
===================================================================

INTEGRA SELECTORES EXACTOS DE scrappers_port/abc_scraper.py que SÍ FUNCIONAN
en la arquitectura V5 con Playwright async, aplicando las mismas optimizaciones
exitosas implementadas para Ripley, Paris y Hites.

✅ SELECTORES ESPECÍFICOS MIGRADOS:
- div.lp-product-tile.js-lp-product-tile (selector principal)
- data-gtm-click (extracción de ID por JSON parsing)
- .brand-name (marca)
- .pdp-link a (nombre + URL)
- .la-polar.price .price-value (precio tarjeta La Polar)
- .internet.price .price-value (precio internet)
- .normal.price .price-value (precio normal)

✅ LÓGICA DE PARSING MIGRADA:
- Extracción por data-value attributes para precios
- JSON parsing de data-gtm-click para product ID
- Manejo de precios múltiples (La Polar, Internet, Normal)
- Rating por Power Reviews (.pr-snippet-rating-decimal)
- Especificaciones técnicas (.prices-actions__destacados__items)
- Badges flotantes y promocionales

🎯 OBJETIVO: 100% compatibilidad con scraper PORT que SÍ EXTRAE DATOS
Incluye optimizaciones específicas para evitar timeout y bloqueos anti-bot
"""

import asyncio
import logging
import re
import json
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

# Selector principal (el que SÍ encuentra productos en AbcDin)
PRODUCT_CONTAINER_SELECTOR = "div.lp-product-tile.js-lp-product-tile"

# Selectores de datos específicos (del PORT funcional)
ABCDIN_SELECTORS = {
    'brand': '.brand-name',
    'name': '.pdp-link a',
    'image': '.tile-image',
    'price_la_polar': '.la-polar.price .price-value',
    'price_internet': '.internet.price .price-value',
    'price_normal': '.normal.price .price-value',
    'discount': '.promotion-badge',
    'rating': '.pr-snippet-rating-decimal',
    'reviews': '.pr-category-snippet__total',
    'specs': '.prices-actions__destacados__items li span',
    'badges': '.floating-badge img, .outstanding-container img'
}

# Palabras clave para detección de colores (del PORT)
COLOR_KEYWORDS = {
    'medianoche': 'Medianoche',
    'negro': 'Negro', 'black': 'Negro',
    'blanco': 'Blanco', 'white': 'Blanco',
    'azul': 'Azul', 'blue': 'Azul',
    'rojo': 'Rojo', 'red': 'Rojo',
    'verde': 'Verde', 'green': 'Verde',
    'dorado': 'Dorado', 'gold': 'Dorado',
    'plateado': 'Plateado', 'silver': 'Plateado'
}

class AbcdinScraperV5Improved(BaseScraperV5):
    """🏪 Scraper AbcDin V5 con selectores PORT integrados y optimizados"""
    
    def __init__(self):
        super().__init__("abcdin")
        
        # URLs exactas (del PORT)
        self.base_urls = {
            'home': 'https://www.abc.cl',
            'celulares': 'https://www.abc.cl/tecnologia/celulares/smartphones/',
            'tablets': 'https://www.abc.cl/tecnologia/tablets/',
            'computadores': 'https://www.abc.cl/tecnologia/computadores/notebooks/',
            'television': 'https://www.abc.cl/tecnologia/television/'
        }
        
        # Configuración específica de AbcDin (optimizada para evitar timeouts)
        self.config = {
            'page_timeout': 90000,             # 90 segundos (ABC puede ser muy lento)
            'load_wait': 15000,                # 15 segundos inicial (más tiempo)
            'scroll_step': 300,                # Paso de scroll más grande
            'scroll_delay': 4000,              # 4 segundos entre scrolls (más tiempo)
            'post_scroll_wait': 3000,          # Espera post-scroll
            'batch_size': 15,                  # Lotes para procesar
            'element_timeout': 20000,          # Timeout muy generoso
            
            # Configuración anti-detección específica para ABC
            'requires_visible_browser': False,  # No necesita visible como Ripley
            'scroll_count': 3,                 # 3 scrolls como en PORT
            'wait_until': 'domcontentloaded'   # Cambiar de networkidle para evitar timeout
        }
        
        self.logger.info("🏪 AbcDin Scraper V5 MEJORADO inicializado - Selectores PORT + Anti-timeout")

    async def scrape_category(
        self, 
        category: str = "celulares",
        max_products: int = 500,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper con selectores exactos del PORT optimizados"""
        
        start_time = datetime.now()
        session_id = f"abcdin_improved_{category}_{int(start_time.timestamp())}"
        
        try:
            # URL de categoría
            category_url = self.base_urls.get(category, self.base_urls['celulares'])
            
            self.logger.info(f"🔍 Scraping AbcDin MEJORADO - {category}: {category_url}")
            
            # Obtener página con configuración optimizada
            page = await self.get_page()
            
            # Scraping con lógica PORT integrada y optimizada
            products = await self._scrape_with_port_logic_optimized(page, category_url, max_products)
            
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
                    'scraping_method': 'port_selectors_optimized',
                    'port_compatibility': True,
                    'extraction_method': 'playwright_direct_query',
                    'success_rate': f"{len(products)}/{max_products}",
                    'scroll_method': 'abcdin_style_scroll',
                    'anti_timeout': True
                }
            )
            
            self.logger.info(f"✅ AbcDin MEJORADO completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error AbcDin MEJORADO categoría {category}: {e}")
            
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'port_selectors_optimized'}
            )

    async def _scrape_with_port_logic_optimized(self, page: Page, url: str, max_products: int) -> List[ProductData]:
        """📦 Scraping usando lógica exacta del PORT pero optimizada para evitar timeouts"""
        
        all_products = []
        
        try:
            # Navegar a la página con configuración optimizada
            self.logger.info(f"📄 Navegando a: {url}")
            
            # Configurar headers específicos para AbcDin (más agresivos)
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document'
            })
            
            # Navegar con wait_until optimizado para evitar timeout
            await page.goto(url, wait_until=self.config['wait_until'], timeout=self.config['page_timeout'])
            
            # Esperar carga inicial (tiempo extendido para ABC)
            self.logger.info(f"⏳ Esperando carga inicial ({self.config['load_wait']/1000}s)...")
            await page.wait_for_timeout(self.config['load_wait'])
            
            # Scroll progresivo para cargar productos (método PORT con más tiempo)
            await self._abcdin_style_scroll(page)
            
            # Esperar post-scroll (tiempo extendido)
            await page.wait_for_timeout(self.config['post_scroll_wait'])
            
            # Extraer productos con selectores PORT optimizados
            products = await self._extract_products_port_optimized(page)
            
            self.logger.info(f"📦 Productos extraídos con método PORT optimizado: {len(products)}")
            
            # Limitar a max_products
            return products[:max_products]
            
        except Exception as e:
            self.logger.error(f"❌ Error en scraping PORT logic optimizado: {e}")
            return []

    async def _abcdin_style_scroll(self, page: Page):
        """📜 Scroll específico para AbcDin (método PORT con optimizaciones anti-timeout)"""
        
        try:
            self.logger.info("📜 Realizando scroll para cargar productos (método PORT optimizado)...")
            
            # Scroll progresivo exacto del PORT pero con más tiempo
            for i in range(self.config['scroll_count']):
                scroll_position = f"document.body.scrollHeight * {(i+1)/3}"
                await page.evaluate(f"window.scrollTo(0, {scroll_position});")
                
                self.logger.debug(f"📜 Scroll {i+1}/3 completado - esperando {self.config['scroll_delay']/1000}s")
                await page.wait_for_timeout(self.config['scroll_delay'])  # Tiempo extendido
            
            # Scroll adicional hasta el final para asegurar carga completa
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(2000)
            
            self.logger.info("✅ Scroll AbcDin completado")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en scroll AbcDin: {e}")

    async def _extract_products_port_optimized(self, page: Page) -> List[ProductData]:
        """📋 Extraer productos con selectores PORT optimizados"""
        
        products = []
        
        try:
            # Buscar contenedores con selector exacto del PORT (con timeout extendido)
            self.logger.info(f"🔍 Buscando contenedores con selector: {PRODUCT_CONTAINER_SELECTOR}")
            
            try:
                await page.wait_for_selector(PRODUCT_CONTAINER_SELECTOR, timeout=self.config['element_timeout'])
                containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
            except Exception as e:
                self.logger.warning(f"⚠️ Timeout esperando selector principal, intentando extracción directa...")
                containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
            
            total_containers = len(containers)
            self.logger.info(f"🔍 Contenedores encontrados con selector PORT: {total_containers}")
            
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
                        self.logger.debug(f"⚠️ Error procesando contenedor {i + j}: {e}")
                        continue
                
                # Cleanup handles del batch
                for container in batch:
                    try:
                        await container.dispose()
                    except:
                        pass
                
                # Delay entre batches (más tiempo para ABC)
                if i + batch_size < total_containers:
                    await page.wait_for_timeout(200)
            
            self.logger.info(f"✅ Productos procesados con método PORT optimizado: {successful}/{total_containers}")
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo productos método PORT optimizado: {e}")
        
        return products

    async def _extract_single_product_port_optimized(self, container: ElementHandle, index: int) -> Optional[ProductData]:
        """📋 Extraer producto individual con TODOS los campos del scrapers_port/abc_scraper.py"""
        
        try:
            # ==========================================
            # EXTRACCIÓN COMPLETA - TODOS LOS CAMPOS DEL PORT
            # ==========================================
            
            # 1. Product ID desde data-gtm-click - método exacto PORT
            product_id = ""
            try:
                gtm_click = await container.get_attribute('data-gtm-click')
                if gtm_click:
                    try:
                        # JSON parsing exacto como PORT
                        gtm_data = json.loads(gtm_click)
                        products_data = gtm_data.get('ecommerce', {}).get('click', {}).get('products', [])
                        if products_data:
                            product_id = products_data[0].get('id', '')
                    except:
                        pass
            except:
                pass
            
            if not product_id:
                return None
            
            # 2. Marca - selector exacto PORT: .brand-name
            brand = ""
            try:
                brand_element = await container.query_selector(ABCDIN_SELECTORS['brand'])
                if brand_element:
                    brand = await brand_element.inner_text()
                    brand = brand.strip()
            except:
                pass
            
            # 3. Nombre del producto y URL - selector exacto PORT: .pdp-link a
            product_name = ""
            product_url = ""
            try:
                name_element = await container.query_selector(ABCDIN_SELECTORS['name'])
                if name_element:
                    product_name = await name_element.inner_text()
                    product_name = product_name.strip()
                    
                    # URL desde el mismo elemento (como en PORT)
                    href = await name_element.get_attribute('href')
                    if href and href.startswith('/'):
                        product_url = f"https://www.abc.cl{href}"
                    else:
                        product_url = href or ""
            except:
                pass
            
            if not product_name:
                return None
            
            # ==========================================
            # 4. IMAGEN - EXACTO COMO PORT
            # ==========================================
            image_url = ""
            image_alt = ""
            try:
                img_element = await container.query_selector(ABCDIN_SELECTORS['image'])
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
            # 5. PRECIOS MÚLTIPLES - EXACTO COMO PORT CON DATA-VALUE
            # ==========================================
            
            # Precio La Polar - selector: .la-polar.price .price-value
            la_polar_price_text = ""
            la_polar_price_numeric = None
            try:
                la_polar_element = await container.query_selector(ABCDIN_SELECTORS['price_la_polar'])
                if la_polar_element:
                    la_polar_price_text = await la_polar_element.inner_text()
                    la_polar_price_text = la_polar_price_text.strip()
                    
                    # Extracción exacta como PORT: data-value attribute
                    price_value = await la_polar_element.get_attribute('data-value')
                    if price_value:
                        try:
                            la_polar_price_numeric = int(float(price_value))
                        except:
                            pass
            except:
                pass
            
            # Precio Internet - selector: .internet.price .price-value
            internet_price_text = ""
            internet_price_numeric = None
            try:
                internet_element = await container.query_selector(ABCDIN_SELECTORS['price_internet'])
                if internet_element:
                    internet_price_text = await internet_element.inner_text()
                    internet_price_text = internet_price_text.strip()
                    
                    # Extracción exacta como PORT: data-value attribute
                    price_value = await internet_element.get_attribute('data-value')
                    if price_value:
                        try:
                            internet_price_numeric = int(float(price_value))
                        except:
                            pass
            except:
                pass
            
            # Precio Normal - selector: .normal.price .price-value
            normal_price_text = ""
            normal_price_numeric = None
            try:
                normal_element = await container.query_selector(ABCDIN_SELECTORS['price_normal'])
                if normal_element:
                    normal_price_text = await normal_element.inner_text()
                    normal_price_text = normal_price_text.strip()
                    
                    # Extracción exacta como PORT: data-value attribute
                    price_value = await normal_element.get_attribute('data-value')
                    if price_value:
                        try:
                            normal_price_numeric = int(float(price_value))
                        except:
                            pass
            except:
                pass
            
            # ==========================================
            # 6. DESCUENTO - SELECTOR EXACTO PORT
            # ==========================================
            discount_percent = ""
            try:
                discount_element = await container.query_selector(ABCDIN_SELECTORS['discount'])
                if discount_element:
                    discount_percent = await discount_element.inner_text()
                    discount_percent = discount_percent.strip()
            except:
                pass
            
            # ==========================================
            # 7. ESPECIFICACIONES TÉCNICAS - EXACTO COMO PORT
            # ==========================================
            screen_size = ""
            internal_memory = ""
            camera_info = ""
            
            try:
                spec_elements = await container.query_selector_all(ABCDIN_SELECTORS['specs'])
                for spec_element in spec_elements:
                    spec_text = await spec_element.inner_text()
                    spec_text = spec_text.strip()
                    
                    # Procesamiento exacto como PORT
                    if "Tamaño de la pantalla:" in spec_text:
                        screen_size = spec_text.replace("Tamaño de la pantalla:", "").strip()
                    elif "Memoria interna:" in spec_text:
                        internal_memory = spec_text.replace("Memoria interna:", "").strip()
                    elif "Cámara posterior:" in spec_text:
                        camera_info = spec_text.replace("Cámara posterior:", "").strip()
            except:
                pass
            
            # ==========================================
            # 8. RATING Y REVIEWS - POWER REVIEWS EXACTO COMO PORT
            # ==========================================
            
            # Rating - selector: .pr-snippet-rating-decimal
            rating = ""
            try:
                rating_element = await container.query_selector(ABCDIN_SELECTORS['rating'])
                if rating_element:
                    rating = await rating_element.inner_text()
                    rating = rating.strip()
            except:
                pass
            
            # Reviews - selector: .pr-category-snippet__total + regex
            reviews_count = ""
            try:
                reviews_element = await container.query_selector(ABCDIN_SELECTORS['reviews'])
                if reviews_element:
                    reviews_text = await reviews_element.inner_text()
                    # Regex exacto como PORT: r'(\d+)'
                    reviews_match = re.search(r'(\d+)', reviews_text)
                    if reviews_match:
                        reviews_count = reviews_match.group(1)
            except:
                pass
            
            # ==========================================
            # 9. BADGES FLOTANTES - EXACTO COMO PORT
            # ==========================================
            floating_badges = []
            try:
                badge_elements = await container.query_selector_all(ABCDIN_SELECTORS['badges'])
                for badge_element in badge_elements:
                    badge_alt = await badge_element.get_attribute('alt')
                    badge_title = await badge_element.get_attribute('title')
                    
                    # Lógica exacta como PORT
                    if badge_alt and badge_alt.strip() and badge_alt not in ['', 'Rosen']:
                        floating_badges.append(badge_alt.strip())
                    elif badge_title and badge_title.strip():
                        floating_badges.append(badge_title.strip())
            except:
                pass
            
            # ==========================================
            # 10. COLOR - EXTRACCIÓN EXACTA COMO PORT
            # ==========================================
            color = ""
            # Mapeo exacto del PORT
            color_keywords = COLOR_KEYWORDS
            product_name_lower = product_name.lower()
            
            for keyword, color_name in color_keywords.items():
                if keyword in product_name_lower:
                    color = color_name
                    break
            
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
            
            # Determinar precio principal (La Polar o el menor disponible)
            available_prices = [p for p in [la_polar_price_numeric, internet_price_numeric, normal_price_numeric] if p and p > 0]
            if not available_prices:
                return None
                
            current_price = float(min(available_prices))
            original_price = float(normal_price_numeric or max(available_prices))
            
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
                    'color': color,
                    'screen_size': screen_size,
                    'internal_memory': internal_memory,
                    'camera_info': camera_info,
                    
                    # Precios con texto y numérico (exacto como PORT)
                    'la_polar_price_text': la_polar_price_text,
                    'la_polar_price': la_polar_price_numeric,
                    'internet_price_text': internet_price_text,
                    'internet_price': internet_price_numeric,
                    'normal_price_text': normal_price_text,
                    'normal_price': normal_price_numeric,
                    'discount_percent': discount_percent,
                    
                    # Rating y reviews
                    'rating': rating,
                    'reviews_count': reviews_count,
                    
                    # Otros campos PORT
                    'floating_badges': ', '.join(floating_badges) if floating_badges else "",
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'product_url': product_url,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return product
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo producto individual: {e}")
            return None

    async def _extract_abcdin_specs(self, container: ElementHandle) -> Dict[str, str]:
        """🔧 Extraer especificaciones específicas de AbcDin (método PORT)"""
        
        specs = {
            'screen_size': '',
            'internal_memory': '',
            'camera_info': ''
        }
        
        try:
            # Buscar todos los elementos de especificaciones
            spec_elements = await container.query_selector_all(ABCDIN_SELECTORS['specs'])
            
            for spec_element in spec_elements:
                spec_text = await spec_element.inner_text()
                spec_text = spec_text.strip()
                
                # Parsear según tipo de especificación (método PORT)
                if "Tamaño de la pantalla:" in spec_text:
                    specs['screen_size'] = spec_text.replace("Tamaño de la pantalla:", "").strip()
                elif "Memoria interna:" in spec_text:
                    specs['internal_memory'] = spec_text.replace("Memoria interna:", "").strip()
                elif "Cámara posterior:" in spec_text:
                    specs['camera_info'] = spec_text.replace("Cámara posterior:", "").strip()
                    
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo especificaciones: {e}")
        
        return specs

    def _extract_color_from_name(self, product_name: str) -> str:
        """🎨 Extraer color del nombre del producto (método PORT)"""
        
        if not product_name:
            return ""
        
        product_name_lower = product_name.lower()
        for keyword, color in COLOR_KEYWORDS.items():
            if keyword in product_name_lower:
                return color
        
        return ""

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validación PORT compatible para AbcDin"""
        
        issues = []
        
        if not products:
            issues.append("No se extrajeron productos con selectores PORT")
            return False, issues
        
        valid_products = 0
        for i, product in enumerate(products):
            product_id = f"Producto {i+1}"
            
            # Validar datos críticos (como PORT)
            if not product.title or len(product.title) < 3:
                issues.append(f"{product_id}: Título inválido")
                continue
            
            if product.current_price <= 0:
                issues.append(f"{product_id}: Precio inválido")
                continue
                
            if not product.sku:  # product_id en AbcDin
                issues.append(f"{product_id}: Product ID faltante")
                continue
                
            if product.product_url and 'abc.cl' not in product.product_url:
                issues.append(f"{product_id}: URL no es de ABC")
                continue
            
            valid_products += 1
        
        # Criterio PORT: al menos 70% válidos (más permisivo para ABC por timeouts)
        success_rate = valid_products / len(products) if products else 0
        if success_rate < 0.7:
            issues.append(f"Tasa de éxito baja: {success_rate:.1%} (mínimo 70%)")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info(f"✅ Validación PORT exitosa: {valid_products}/{len(products)} productos válidos")
        else:
            self.logger.warning(f"⚠️ Validación PORT con issues: {len(issues)} problemas")
        
        return is_valid, issues

# ==========================================
# TESTING Y MAIN EXECUTION
# ==========================================

async def test_abcdin_improved_scraper():
    """🧪 Test del scraper AbcDin mejorado"""
    
    print("🧪 TEST ABCDIN SCRAPER V5 MEJORADO")
    print("=" * 50)
    
    scraper = AbcdinScraperV5Improved()
    
    try:
        # Test de scraping
        result = await scraper.scrape_category(
            category="celulares",
            max_products=200
        )
        
        print(f"✅ Test completado:")
        print(f"   Éxito: {result.success}")
        print(f"   Productos: {len(result.products)}")
        print(f"   Tiempo: {result.execution_time:.1f}s")
        
        if result.products:
            print(f"\n📦 Muestra de productos:")
            for i, product in enumerate(result.products[:3], 1):
                current_price = f"${product.current_price:,.0f}" if product.current_price else "N/A"
                original_price = f" (antes: ${product.original_price:,.0f})" if product.original_price > product.current_price else ""
                
                print(f"{i}. {product.title}")
                print(f"   Precio: {current_price}{original_price}")
                print(f"   ID: {product.sku}")
                print(f"   Rating: {product.rating} estrellas ({product.additional_info.get('reviews_count')} reviews)")
                
                # Mostrar especificaciones si están disponibles
                specs = []
                if product.additional_info.get('screen_size'):
                    specs.append(product.additional_info['screen_size'])
                if product.additional_info.get('internal_memory'):
                    specs.append(product.additional_info['internal_memory'])
                if product.additional_info.get('camera_info'):
                    specs.append(product.additional_info['camera_info'])
                    
                if specs:
                    print(f"   Specs: {' | '.join(specs)}")
                    
                # Precios múltiples
                if product.additional_info.get('la_polar_price'):
                    print(f"   Precio La Polar: ${product.additional_info['la_polar_price']:,}")
                if product.additional_info.get('internet_price'):
                    print(f"   Precio Internet: ${product.additional_info['internet_price']:,}")
        
        # Test de validación
        is_valid, issues = await scraper.validate_extraction(result.products)
        print(f"\n🔍 Validación: {'✅ EXITOSA' if is_valid else '❌ CON PROBLEMAS'}")
        if issues:
            for issue in issues[:3]:
                print(f"   - {issue}")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configurar logging para test
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    asyncio.run(test_abcdin_improved_scraper())