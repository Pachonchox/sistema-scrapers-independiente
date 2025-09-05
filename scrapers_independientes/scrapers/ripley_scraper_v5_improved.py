# -*- coding: utf-8 -*-
"""
🛍️ Ripley Chile Scraper v5 MEJORADO - Integración de Selectores PORT
=================================================================

INTEGRA SELECTORES EXACTOS DE scrappers_port/ripley_scraper.py que SÍ FUNCIONAN
en la arquitectura V5 con Playwright async, aplicando las mismas optimizaciones
exitosas implementadas para Paris.

✅ SELECTORES ESPECÍFICOS MIGRADOS:
- a[data-partnumber] (selector principal)
- .catalog-product-details__name (nombre producto)
- .catalog-prices__offer-price (precio internet)
- .catalog-prices__list-price.catalog-prices__line_thru (precio normal)
- .catalog-prices__card-price (precio tarjeta Ripley)

✅ LÓGICA DE PARSING MIGRADA:
- Extracción por data attributes
- Parsing de precios múltiples (normal, internet, tarjeta)
- Manejo de especificaciones (storage, RAM, pantalla, cámara)
- Mapeo de colores y badges

🎯 OBJETIVO: 100% compatibilidad con scraper PORT que SÍ EXTRAE DATOS
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

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

# Selector principal (el que SÍ encuentra productos en Ripley)
PRODUCT_CONTAINER_SELECTOR = "a[data-partnumber]"

# Selectores de datos específicos (del PORT funcional)
RIPLEY_SELECTORS = {
    'brand': '.brand-logo span, .catalog-product-details__logo-container span',
    'name': '.catalog-product-details__name',
    'price_normal': '.catalog-prices__list-price.catalog-prices__line_thru',
    'price_internet': '.catalog-prices__offer-price', 
    'price_card': '.catalog-prices__card-price',
    'discount': '.catalog-product-details__discount-tag',
    'colors': '.catalog-colors-option-outer',
    'badges': '.emblem',
    'image': 'img'
}

# Regex exactos del PORT para specs
RIPLEY_SPECS_REGEX = {
    'storage': r'(\d+)\s*gb(?!\s+ram)',     # Storage (no RAM)
    'ram': r'(\d+)\s*gb\s+ram',             # RAM específico
    'screen_size': r'(\d+\.?\d*)"',         # Tamaño pantalla
    'camera': r'(\d+)mp'                    # Cámara
}

class RipleyScraperV5Improved(BaseScraperV5):
    """🛍️ Scraper Ripley V5 con selectores PORT integrados y optimizados"""
    
    def __init__(self):
        super().__init__("ripley")
        
        # URLs exactas (del PORT)
        self.base_urls = {
            'home': 'https://simple.ripley.cl',
            'celulares': 'https://simple.ripley.cl/tecno/celulares',
            'search': 'https://simple.ripley.cl/search'
        }
        
        # Configuración específica de Ripley (CRÍTICA - NAVEGADOR VISIBLE)
        self.config = {
            'page_timeout': 45000,         # 45 segundos
            'load_wait': 8000,             # 8 segundos inicial (Ripley es lento)
            'scroll_step': 150,            # Paso de scroll más pequeño para simular humano
            'scroll_delay': 150,           # Delay entre scrolls más realista
            'post_scroll_wait': 2000,      # Espera post-scroll
            'batch_size': 15,              # Lotes más pequeños
            'element_timeout': 10000,      # Timeout más generoso
            
            # 🚨 CONFIGURACIÓN CRÍTICA PARA RIPLEY
            'requires_visible_browser': True,   # OBLIGATORIO para Ripley
            'browser_position': (-2000, 0),     # Posición fuera de pantalla
            'window_size': (1920, 1080),        # Tamaño completo
            'simulate_human_behavior': True,     # Comportamiento humano
            'mandatory_scroll_down': True       # Scroll hacia abajo obligatorio
        }
        
        self.logger.info("🛍️ Ripley Scraper V5 MEJORADO inicializado - NAVEGADOR VISIBLE configurado")

    async def get_page(self):
        """🌐 Crear página con navegador VISIBLE posicionado fuera de pantalla (CRÍTICO para Ripley)"""
        
        try:
            if not self.browser:
                from playwright.async_api import async_playwright
                
                # Lanzar Playwright
                self.pw = await async_playwright().start()
                
                # 🚨 CONFIGURACIÓN ESPECÍFICA PARA RIPLEY - NAVEGADOR VISIBLE
                launch_kwargs = {
                    'headless': False,  # ¡CRÍTICO! Ripley detecta headless
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-extensions',
                        '--no-first-run',
                        '--disable-default-apps',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection',
                        f'--window-position={self.config["browser_position"][0]},{self.config["browser_position"][1]}',
                        f'--window-size={self.config["window_size"][0]},{self.config["window_size"][1]}'
                    ]
                }
                
                self.logger.info("🚨 Lanzando navegador VISIBLE para Ripley (fuera de pantalla)")
                self.browser = await self.pw.chromium.launch(**launch_kwargs)
                
                # Crear contexto con configuración anti-detección específica para Ripley
                context_options = {
                    'viewport': {'width': self.config["window_size"][0], 'height': self.config["window_size"][1]},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'locale': 'es-CL',
                    'timezone_id': 'America/Santiago',
                    'geolocation': {'latitude': -33.4489, 'longitude': -70.6693},
                    'permissions': ['geolocation']
                }
                
                self.context = await self.browser.new_context(**context_options)
                
                # Crear página
                self.page = await self.context.new_page()
                
                # Configuración adicional anti-detección para Ripley
                await self.page.add_init_script("""
                    // Ocultar webdriver
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    
                    // Simular plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Simular idiomas
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['es-CL', 'es', 'en']
                    });
                """)
                
                # Headers específicos para Ripley (como en PORT)
                await self.page.set_extra_http_headers({
                    'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Cache-Control': 'no-cache',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document'
                })
                
                self.logger.info("✅ Navegador VISIBLE configurado correctamente para Ripley")
            
            return self.page
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando navegador VISIBLE para Ripley: {e}")
            raise

    async def scrape_category(
        self, 
        category: str = "celulares",
        max_products: int = 500,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper con selectores exactos del PORT optimizados"""
        
        start_time = datetime.now()
        session_id = f"ripley_improved_{category}_{int(start_time.timestamp())}"
        
        try:
            # URL de categoría
            category_url = self.base_urls.get(category, self.base_urls['celulares'])
            
            self.logger.info(f"🔍 Scraping Ripley MEJORADO - {category}: {category_url}")
            
            # Obtener página
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
                    'scroll_method': 'smooth_scroll_ripley'
                }
            )
            
            self.logger.info(f"✅ Ripley MEJORADO completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error Ripley MEJORADO categoría {category}: {e}")
            
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
        """📦 Scraping usando lógica exacta del PORT con PAGINACIÓN"""
        
        all_products = []
        page_num = 1
        
        # Loop de paginación hasta alcanzar max_products
        while len(all_products) < max_products:
            try:
                # Construir URL de página (lógica específica de Ripley)
                page_url = self._build_page_url_ripley(url, page_num)
                
                self.logger.info(f"📄 Scraping Ripley página {page_num}: {page_url}")
                await page.goto(page_url, wait_until='domcontentloaded', timeout=self.config['page_timeout'])
                
                # Esperar carga inicial (optimizado del PORT)
                await page.wait_for_timeout(self.config['load_wait'])
                
                # Scroll suave para cargar productos (crítico para Ripley)
                await self._smooth_scroll_ripley_style(page)
                
                # Esperar post-scroll
                await page.wait_for_timeout(self.config['post_scroll_wait'])
                
                # Extraer productos de esta página
                page_products = await self._extract_products_port_optimized(page)
                
                if not page_products:
                    self.logger.info(f"❌ No hay más productos en página {page_num}, terminando paginación")
                    break
                
                self.logger.info(f"✅ Página {page_num}: {len(page_products)} productos extraídos")
                all_products.extend(page_products)
                page_num += 1
                
                # Pausa entre páginas para evitar detección
                await page.wait_for_timeout(3000)
                
                # Si la página devolvió menos de 15 productos, probablemente no hay más páginas
                if len(page_products) < 15:
                    self.logger.info(f"🔚 Página {page_num-1} devolvió pocos productos ({len(page_products)}), posiblemente última página")
                    break
                
            except Exception as e:
                self.logger.error(f"❌ Error en página {page_num}: {e}")
                break
        
        self.logger.info(f"📦 Total productos extraídos con paginación: {len(all_products)} de {page_num-1} páginas")
        
        # Limitar a max_products
        return all_products[:max_products]

    def _build_page_url_ripley(self, base_url: str, page_num: int) -> str:
        """🔗 Construir URL con paginación específica de Ripley"""
        if page_num <= 1:
            return base_url
        
        # Lógica específica de Ripley (del V5 original)
        parts = urlsplit(base_url)
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        
        # Parámetros específicos para páginas 2+ (del v3)
        new_q_dict = {
            's': 'mdco',
            'source': 'menu',
            'page': str(page_num),
            'type': 'catalog'
        }
        
        # Preservar parámetros existentes
        for key in q:
            if key not in new_q_dict:
                new_q_dict[key] = q[key]
        
        new_query = urlencode(new_q_dict)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    async def _smooth_scroll_ripley_style(self, page: Page):
        """📜 Scroll OBLIGATORIO hacia abajo para Ripley - NAVEGADOR VISIBLE fuera de pantalla"""
        
        try:
            self.logger.info("🚨 Ejecutando scroll OBLIGATORIO hacia abajo (Ripley requiere navegador visible)")
            
            # Obtener dimensiones iniciales
            initial_height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            current_position = 0
            scroll_step = self.config['scroll_step']  # 150px para simular humano
            total_scrolled = 0
            
            # 🚨 SCROLL OBLIGATORIO HACIA ABAJO (requerimiento crítico)
            self.logger.info("📜 Scroll hacia abajo OBLIGATORIO iniciado (navegador visible fuera de pantalla)")
            
            # Hacer al menos 5 pantallas de scroll hacia abajo OBLIGATORIAMENTE
            min_scroll_distance = viewport_height * 5
            
            while total_scrolled < min_scroll_distance:
                # Scroll hacia abajo
                new_position = current_position + scroll_step
                await page.evaluate(f'window.scrollTo(0, {new_position})')
                
                current_position = new_position
                total_scrolled += scroll_step
                
                # Delay para simular comportamiento humano
                await page.wait_for_timeout(self.config['scroll_delay'])  # 150ms
                
                # Actualizar altura total por si se cargó contenido
                current_height = await page.evaluate('document.body.scrollHeight')
                
                # Si llegamos al final antes del mínimo, continuar hasta el final
                if current_position >= current_height - viewport_height:
                    break
                
                # Log progreso cada 10 scrolls
                if (total_scrolled // scroll_step) % 10 == 0:
                    self.logger.debug(f"📜 Scroll progreso: {total_scrolled}px de mínimo {min_scroll_distance}px")
            
            # Scroll final hasta el fondo (OBLIGATORIO)
            self.logger.info("📜 Ejecutando scroll final hasta el fondo (OBLIGATORIO)")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(800)  # Esperar más tiempo al final
            
            # Verificar que realmente scrolleamos hacia abajo
            final_height = await page.evaluate('document.body.scrollHeight')
            final_position = await page.evaluate('window.pageYOffset')
            
            self.logger.info(f"📜 Scroll completado: {total_scrolled}px scrolleado, posición final: {final_position}px")
            
            # Pequeño scroll de vuelta hacia arriba para activar lazy loading
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(500)
            
            # Confirmar que el scroll obligatorio se ejecutó
            if total_scrolled >= min_scroll_distance or final_position > viewport_height:
                self.logger.info("✅ Scroll OBLIGATORIO hacia abajo completado exitosamente")
            else:
                self.logger.warning(f"⚠️ Scroll insuficiente: {total_scrolled}px < {min_scroll_distance}px requeridos")
            
        except Exception as e:
            self.logger.error(f"❌ ERROR CRÍTICO en scroll obligatorio: {e}")
            # Incluso con error, intentar scroll básico
            try:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)
                await page.evaluate('window.scrollTo(0, 0)')
                self.logger.warning("⚠️ Scroll básico de emergencia ejecutado")
            except:
                pass

    async def _extract_products_port_optimized(self, page: Page) -> List[ProductData]:
        """📋 Extraer productos con selectores PORT optimizados"""
        
        products = []
        
        try:
            # Buscar contenedores con selector exacto del PORT
            await page.wait_for_selector(PRODUCT_CONTAINER_SELECTOR, timeout=self.config['element_timeout'])
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
                
                # Delay entre batches
                if i + batch_size < total_containers:
                    await page.wait_for_timeout(100)
            
            self.logger.info(f"✅ Productos procesados con método PORT optimizado: {successful}/{total_containers}")
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo productos método PORT optimizado: {e}")
        
        return products

    async def _extract_single_product_port_optimized(self, container: ElementHandle, index: int) -> Optional[ProductData]:
        """📋 Extraer producto individual con TODOS los campos del scrapers_port/ripley_scraper.py"""
        
        try:
            # ==========================================
            # EXTRACCIÓN COMPLETA - TODOS LOS CAMPOS DEL PORT
            # ==========================================
            
            # 1. Data attributes básicos (exacto del PORT)
            try:
                product_code = await container.get_attribute('data-partnumber')
                product_url = await container.get_attribute('href')
            except:
                return None
            
            # Validar datos mínimos
            if not product_code:
                return None
            
            # URL completa (igual que PORT)
            full_link = f"https://simple.ripley.cl{product_url}" if product_url and product_url.startswith('/') else (product_url or "")
            
            # 2. Marca (selector exacto PORT: .brand-logo span, .catalog-product-details__logo-container span)
            brand = ""
            try:
                brand_element = await container.query_selector(RIPLEY_SELECTORS['brand'])
                if brand_element:
                    brand = await brand_element.inner_text()
                    brand = brand.strip()
            except:
                pass
            
            # 3. Nombre del producto (selector exacto PORT: .catalog-product-details__name)
            product_name = ""
            try:
                name_element = await container.query_selector(RIPLEY_SELECTORS['name'])
                if name_element:
                    product_name = await name_element.inner_text()
                    product_name = product_name.strip()
            except:
                pass
            
            if not product_name:
                return None
            
            # ==========================================
            # 4. PRECIOS COMPLETOS - EXACTO COMO PORT
            # ==========================================
            
            # Precio normal (tachado) - selector: .catalog-prices__list-price.catalog-prices__line_thru
            normal_price_text = ""
            normal_price_numeric = None
            try:
                normal_element = await container.query_selector(RIPLEY_SELECTORS['price_normal'])
                if normal_element:
                    normal_price_text = await normal_element.inner_text()
                    normal_price_text = normal_price_text.strip()
                    # Parsing exacto como PORT
                    price_match = re.search(r'\$?([0-9.,]+)', normal_price_text.replace('.', ''))
                    if price_match:
                        try:
                            normal_price_numeric = int(price_match.group(1).replace(',', ''))
                        except:
                            pass
            except:
                pass
            
            # Precio internet - selector: .catalog-prices__offer-price
            internet_price_text = ""
            internet_price_numeric = None
            try:
                internet_element = await container.query_selector(RIPLEY_SELECTORS['price_internet'])
                if internet_element:
                    internet_price_text = await internet_element.inner_text()
                    internet_price_text = internet_price_text.strip()
                    # Parsing exacto como PORT
                    price_match = re.search(r'\$?([0-9.,]+)', internet_price_text.replace('.', ''))
                    if price_match:
                        try:
                            internet_price_numeric = int(price_match.group(1).replace(',', ''))
                        except:
                            pass
            except:
                pass
            
            # Precio tarjeta Ripley - selector: .catalog-prices__card-price
            ripley_price_text = ""
            ripley_price_numeric = None
            try:
                card_element = await container.query_selector(RIPLEY_SELECTORS['price_card'])
                if card_element:
                    card_text = await card_element.inner_text()
                    # Extracción exacta como PORT: .split('$')[1].split(' ')[0]
                    if '$' in card_text:
                        ripley_price_text = card_text.split('$')[1].split(' ')[0] if len(card_text.split('$')) > 1 else ""
                        if ripley_price_text:
                            # Parsing exacto como PORT
                            price_match = re.search(r'([0-9.,]+)', ripley_price_text.replace('.', ''))
                            if price_match:
                                try:
                                    ripley_price_numeric = int(price_match.group(1).replace(',', ''))
                                except:
                                    pass
            except:
                pass
            
            # 5. Descuento - selector: .catalog-product-details__discount-tag
            discount_percent = ""
            try:
                discount_element = await container.query_selector(RIPLEY_SELECTORS['discount'])
                if discount_element:
                    discount_percent = await discount_element.inner_text()
                    discount_percent = discount_percent.strip()
            except:
                pass
            
            # ==========================================
            # 6. IMAGEN - COMPLETA COMO PORT
            # ==========================================
            image_url = ""
            image_alt = ""
            try:
                img_element = await container.query_selector(RIPLEY_SELECTORS['image'])
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
            # 7. COLORES - EXACTO COMO PORT (selector: .catalog-colors-option-outer)
            # ==========================================
            colors = []
            try:
                color_elements = await container.query_selector_all(RIPLEY_SELECTORS['colors'])
                for color_element in color_elements:
                    color_title = await color_element.get_attribute('title')
                    if color_title:
                        colors.append(color_title)
            except:
                pass
            
            # ==========================================
            # 8. EMBLEMAS/BADGES - EXACTO COMO PORT (selector: .emblem)
            # ==========================================
            emblems = []
            try:
                emblem_elements = await container.query_selector_all(RIPLEY_SELECTORS['badges'])
                for emblem_element in emblem_elements:
                    emblem_text = await emblem_element.inner_text()
                    if emblem_text:
                        emblems.append(emblem_text.strip())
            except:
                pass
            
            # ==========================================
            # 9. ESPECIFICACIONES - REGEX EXACTOS DEL PORT
            # ==========================================
            storage = ""
            ram = ""
            screen_size = ""
            camera = ""
            
            if product_name:
                # Storage - regex PORT: r'(\d+)\s*gb(?!\s+ram)'
                storage_match = re.search(RIPLEY_SPECS_REGEX['storage'], product_name.lower())
                if storage_match:
                    storage = f"{storage_match.group(1)}GB"
                
                # RAM - regex PORT: r'(\d+)\s*gb\s+ram'
                ram_match = re.search(RIPLEY_SPECS_REGEX['ram'], product_name.lower())
                if ram_match:
                    ram = f"{ram_match.group(1)}GB"
                
                # Tamaño de pantalla - regex PORT: r'(\d+\.?\d*)"'
                screen_match = re.search(RIPLEY_SPECS_REGEX['screen_size'], product_name)
                if screen_match:
                    screen_size = f"{screen_match.group(1)}\""
                
                # Cámara - regex PORT: r'(\d+)mp'
                camera_match = re.search(RIPLEY_SPECS_REGEX['camera'], product_name.lower())
                if camera_match:
                    camera = f"{camera_match.group(1)}MP"
            
            # ==========================================
            # CREAR PRODUCTO CON ESTRUCTURA EXACTA DEL PORT
            # ==========================================
            
            # Solo agregar productos válidos (condición del PORT)
            if not (product_code and product_name):
                return None
            
            # Construir título completo
            title_parts = []
            if brand:
                title_parts.append(brand)
            if product_name:
                title_parts.append(product_name)
            title = " ".join(title_parts)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Determinar precio principal (internet o el menor disponible)
            current_price = internet_price_numeric or ripley_price_numeric or normal_price_numeric or 0
            original_price = normal_price_numeric or current_price
            
            # Calcular descuento si hay diferencia
            discount_percentage = 0
            if original_price and current_price and original_price > current_price:
                discount_percentage = int(((original_price - current_price) / original_price) * 100)
            
            product = ProductData(
                title=title,
                current_price=float(current_price) if current_price else 0.0,
                original_price=float(original_price) if original_price else 0.0,
                discount_percentage=discount_percentage,
                currency="CLP",
                availability="in_stock",
                product_url=full_link,
                image_urls=[image_url] if image_url else [],
                brand=brand,
                sku=product_code,
                rating=0.0,
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info={
                    'extraction_method': 'port_complete_fields',
                    'container_index': index,
                    
                    # ==== TODOS LOS CAMPOS DEL PORT ORIGINAL ====
                    'product_code': product_code,
                    'name': product_name,
                    'screen_size': screen_size,
                    'storage': storage,
                    'ram': ram,
                    'camera': camera,
                    'colors': ', '.join(colors) if colors else "",
                    
                    # Precios con texto y numérico (exacto como PORT)
                    'normal_price_text': normal_price_text,
                    'normal_price': normal_price_numeric,
                    'internet_price_text': internet_price_text,
                    'internet_price': internet_price_numeric,
                    'ripley_price_text': ripley_price_text,
                    'ripley_price': ripley_price_numeric,
                    'discount_percent': discount_percent,
                    
                    # Emblemas y otros
                    'emblems': ', '.join(emblems) if emblems else "",
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'product_url': full_link,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return product
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo producto individual: {e}")
            return None

    def _extract_specs_ripley_regex(self, product_name: str) -> Dict[str, str]:
        """🔧 Extraer especificaciones con regex exactos del PORT"""
        
        specs = {}
        
        if not product_name:
            return specs
        
        try:
            # Storage (regex exacto PORT)
            storage_match = re.search(RIPLEY_SPECS_REGEX['storage'], product_name, re.IGNORECASE)
            if storage_match:
                specs['storage'] = f"{storage_match.group(1)}GB"
            
            # RAM (regex exacto PORT)
            ram_match = re.search(RIPLEY_SPECS_REGEX['ram'], product_name, re.IGNORECASE)
            if ram_match:
                specs['ram'] = f"{ram_match.group(1)}GB"
            
            # Screen size (regex exacto PORT)
            screen_match = re.search(RIPLEY_SPECS_REGEX['screen_size'], product_name)
            if screen_match:
                specs['screen_size'] = f"{screen_match.group(1)}\""
            
            # Camera (regex exacto PORT)
            camera_match = re.search(RIPLEY_SPECS_REGEX['camera'], product_name, re.IGNORECASE)
            if camera_match:
                specs['camera'] = f"{camera_match.group(1)}MP"
                
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo specs: {e}")
        
        return specs

    def _parse_price_ripley_method(self, price_text: str) -> float:
        """💰 Parsear precio con método exacto del PORT"""
        
        if not price_text:
            return 0.0
        
        try:
            # Limpiar precio (método PORT)
            price_match = re.search(r'([0-9.,]+)', price_text.replace('$', '').replace('.', ''))
            if price_match:
                try:
                    return float(price_match.group(1).replace(',', ''))
                except:
                    return 0.0
            return 0.0
            
        except (ValueError, AttributeError):
            return 0.0

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validación PORT compatible para Ripley"""
        
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
                
            if product.product_url and 'ripley.cl' not in product.product_url:
                issues.append(f"{product_id}: URL no es de Ripley")
                continue
            
            valid_products += 1
        
        # Criterio PORT: al menos 80% válidos
        success_rate = valid_products / len(products) if products else 0
        if success_rate < 0.8:
            issues.append(f"Tasa de éxito baja: {success_rate:.1%} (mínimo 80%)")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info(f"✅ Validación PORT exitosa: {valid_products}/{len(products)} productos válidos")
        else:
            self.logger.warning(f"⚠️ Validación PORT con issues: {len(issues)} problemas")
        
        return is_valid, issues

# ==========================================
# TESTING Y MAIN EXECUTION
# ==========================================

async def test_ripley_improved_scraper():
    """🧪 Test del scraper Ripley mejorado"""
    
    print("🧪 TEST RIPLEY SCRAPER V5 MEJORADO")
    print("=" * 50)
    
    scraper = RipleyScraperV5Improved()
    
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
                print(f"   SKU: {product.sku}")
                print(f"   URL: {product.product_url[:60]}...")
                
                # Mostrar especificaciones si están disponibles
                specs = []
                if product.additional_info.get('storage'):
                    specs.append(product.additional_info['storage'])
                if product.additional_info.get('ram'):
                    specs.append(product.additional_info['ram'])
                if product.additional_info.get('screen_size'):
                    specs.append(product.additional_info['screen_size'])
                    
                if specs:
                    print(f"   Specs: {' | '.join(specs)}")
        
        # Test de validación
        is_valid, issues = await scraper.validate_extraction(result.products)
        print(f"\n🔍 Validación: {'✅ EXITOSA' if is_valid else '❌ CON PROBLEMAS'}")
        if issues:
            for issue in issues[:3]:
                print(f"   - {issue}")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")

if __name__ == "__main__":
    # Configurar logging para test
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    asyncio.run(test_ripley_improved_scraper())