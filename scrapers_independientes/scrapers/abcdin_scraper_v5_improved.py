# -*- coding: utf-8 -*-
"""
🏪 AbcDin Chile Scraper v5 PARALELO - PORT Integrado + Optimizaciones de Velocidad
===================================================================================

INTEGRA MEJORAS DE VELOCIDAD DE PARIS/FALABELLA + SELECTORES PORT FUNCIONALES
- 🚀 SCRAPING PARALELO: 5 páginas simultáneas (igual que Paris/Falabella)
- ⚡ TIMEOUTS OPTIMIZADOS: 30s total, 3s por elemento (ultra-rápido)
- 🎯 DETECCIÓN AUTO-STOP: Páginas vacías automáticas
- 📊 CONFIGURACIÓN CENTRALIZADA: Desde config.json

✅ SELECTORES ESPECÍFICOS MIGRADOS:
- div.lp-product-tile.js-lp-product-tile (selector principal)
- data-gtm-click (extracción de ID por JSON parsing)
- .brand-name (marca)
- .pdp-link a (nombre + URL)
- .la-polar.price .price-value (precio tarjeta La Polar)
- .internet.price .price-value (precio internet)
- .normal.price .price-value (precio normal)

✅ OPTIMIZACIONES DE VELOCIDAD INTEGRADAS:
- 📦 Paginación paralela con batch_size=5
- ⏰ Timeouts ultra-rápidos (30s total vs 90s anterior)
- 🔄 Auto-stop inteligente con detección de páginas vacías
- 📜 Scroll optimizado (2s inicial, 1s scroll, 0.5s mid-scroll)
- 🎛️ Configuración desde config.json (como Paris/Falabella)

🎯 OBJETIVO: Máxima velocidad con 100% compatibilidad scraper PORT funcional
"""

import asyncio
import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin
from pathlib import Path

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

# Selector principal (EXACTO del PORT funcional)
PRODUCT_CONTAINER_SELECTOR = "div.lp-product-tile.js-lp-product-tile"

# Selectores de datos específicos (EXACTOS del PORT funcional)
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
        
        # URL base exacta del PORT funcional
        self.base_url = "https://www.abc.cl/tecnologia/celulares/smartphones/"
        
        # URLs por categoría (del PORT)
        self.base_urls = {
            'home': 'https://www.abc.cl',
            'celulares': 'https://www.abc.cl/tecnologia/celulares/smartphones/',
            'smartphones': 'https://www.abc.cl/tecnologia/celulares/smartphones/',
            'tablets': 'https://www.abc.cl/tecnologia/tablets/',
            'computadores': 'https://www.abc.cl/tecnologia/computadores/notebooks/',
            'television': 'https://www.abc.cl/tecnologia/television/'
        }
        
        # Configuración de paginación centralizada
        self.pagination_config = self._load_pagination_config()
        
        # Configuración ULTRA-RÁPIDA optimizada (igual que Paris/Falabella)
        self.config = {
            'initial_wait': 2,         # 2 segundos mínimos
            'scroll_wait': 1,          # 1 segundo después del scroll
            'mid_scroll_wait': 0.5,    # 0.5 segundos después del scroll a mitad
            'element_timeout': 3000,   # 3 segundos timeout por elemento
            'page_timeout': 30000,     # 30 segundos total optimizado
            'batch_size': 15,          # Lotes para procesar
            'requires_visible_browser': False,  # No necesita visible como Ripley
            'scroll_count': 3,         # 3 scrolls como en PORT
            'wait_until': 'domcontentloaded'   # Cambiar de networkidle para evitar timeout
        }
        
        self.logger.info("🏪 AbcDin Scraper V5 - PARALELO + PORT inicializado")

    def _load_pagination_config(self) -> Dict[str, Any]:
        """📄 Cargar configuración de paginación desde config.json"""
        try:
            config_path = Path(__file__).parent.parent / "config.json"
            if not config_path.exists():
                self.logger.warning(f"⚠️ Config.json no encontrado en {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            abcdin_config = config_data.get('retailers', {}).get('abcdin', {})
            pagination_config = abcdin_config.get('paginacion', {})
            
            if pagination_config:
                self.logger.info(f"✅ Configuración de paginación AbcDin cargada: {pagination_config.get('url_pattern', 'N/A')}")
                return pagination_config
            else:
                self.logger.warning("⚠️ No se encontró configuración de paginación para AbcDin")
                return {}
                
        except Exception as e:
            self.logger.error(f"💥 Error cargando configuración de paginación: {e}")
            return {}

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
            
            # Scraping PARALELO con paginación (como Paris/Falabella)
            products = await self._scrape_with_pagination_parallel(page, max_products)
            
            # Guardar JSON individual como Paris/Falabella
            if products:
                await self._save_retailer_json_complete(products, self.session_id, execution_time)
            
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
                    'scraping_method': 'parallel_port_integrated',
                    'parallel_pages': 5,
                    'port_compatibility': True,
                    'extraction_method': 'playwright_parallel',
                    'success_rate': f"{len(products)}/{max_products}",
                    'pagination_used': len(self.pagination_config) > 0
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'parallel_port_integrated'}
            )

    async def _scrape_with_pagination_parallel(self, initial_page: Page, max_products: int) -> List[ProductData]:
        """📦 Scraping PARALELO con 5 páginas simultáneas + lógica AbcDin optimizada"""
        
        all_products = []
        current_batch_start = 0  # AbcDin usa start=0, not page=1
        consecutive_empty_batches = 0
        
        # Configuración de paralelismo y detección (como Paris/Falabella)
        batch_size = 5  # 5 páginas simultáneas
        max_empty_batches = 2
        max_pages_config = self.pagination_config.get('max_pages', 50) if self.pagination_config else 50
        auto_stop_enabled = self.pagination_config.get('auto_stop', True) if self.pagination_config else True
        page_increment = self.pagination_config.get('page_increment', 36) if self.pagination_config else 36
        sz_param = self.pagination_config.get('sz_param', 36) if self.pagination_config else 36
        
        self.logger.info(f"🚀 Iniciando AbcDin PARALELO:")
        self.logger.info(f"   📄 Max páginas: {max_pages_config}")
        self.logger.info(f"   ⚡ Páginas paralelas: {batch_size}")
        self.logger.info(f"   🔚 Auto-stop: {'Activado' if auto_stop_enabled else 'Desactivado'}")
        self.logger.info(f"   📏 Increment: {page_increment}, Size: {sz_param}")
        
        while len(all_products) < max_products and current_batch_start < (max_pages_config * page_increment):
            # Preparar lote de páginas
            batch_pages = []
            for i in range(batch_size):
                start_value = current_batch_start + (i * page_increment)
                if start_value >= (max_pages_config * page_increment):
                    break
                batch_pages.append(start_value)
            
            if not batch_pages:
                break
            
            self.logger.info(f"🚀 Procesando lote AbcDin páginas start={batch_pages[0]} a start={batch_pages[-1]}")
            
            # Procesar páginas en paralelo
            batch_results = await self._process_abcdin_pages_parallel(batch_pages, sz_param)
            
            # Consolidar resultados del lote
            batch_products = []
            empty_pages_in_batch = 0
            
            for page_result in batch_results:
                if page_result:
                    batch_products.extend(page_result)
                else:
                    empty_pages_in_batch += 1
            
            # Verificar si el lote está vacío
            if not batch_products:
                consecutive_empty_batches += 1
                self.logger.warning(f"⚠️ Lote vacío {consecutive_empty_batches}/{max_empty_batches}")
                
                if auto_stop_enabled and consecutive_empty_batches >= max_empty_batches:
                    self.logger.info("🛑 Auto-stop activado: demasiados lotes vacíos")
                    break
            else:
                consecutive_empty_batches = 0
                all_products.extend(batch_products)
                self.logger.info(f"✅ Lote completado: +{len(batch_products)} productos (Total: {len(all_products)})")
            
            # Avanzar al siguiente lote
            current_batch_start += (batch_size * page_increment)
            
            # Delay entre lotes para evitar sobrecarga
            await asyncio.sleep(1)
            
            # Verificar si ya tenemos suficientes productos
            if len(all_products) >= max_products:
                break
        
        final_products = all_products[:max_products]
        self.logger.info(f"✅ AbcDin PARALELO terminado: {len(final_products)} productos finales")
        
        return final_products

    async def _process_abcdin_pages_parallel(self, start_values: List[int], sz_param: int) -> List[List[ProductData]]:
        """⚡ Procesar páginas de AbcDin en paralelo"""
        
        tasks = []
        for start_value in start_values:
            task = self._scrape_single_abcdin_page(start_value, sz_param)
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Error en página start={start_values[i]}: {result}")
                valid_results.append([])
            else:
                valid_results.append(result or [])
        
        return valid_results

    async def _scrape_single_abcdin_page(self, start_value: int, sz_param: int) -> List[ProductData]:
        """📄 Scraper de una sola página de AbcDin con lógica PORT"""
        
        page = None
        try:
            # Crear nueva página para este hilo paralelo
            page = await self.get_page()
            if not page:
                return []
            
            # Construir URL con paginación AbcDin (PORT usa abc.cl)
            url = f"https://www.abc.cl/tecnologia/celulares/smartphones?start={start_value}&sz={sz_param}"
            
            # Navegar con timeout optimizado
            await page.goto(url, wait_until=self.config['wait_until'], timeout=self.config['page_timeout'])
            
            # Espera inicial mínima (optimizada)
            await page.wait_for_timeout(self.config['initial_wait'] * 1000)
            
            # Scroll rápido
            await self._abcdin_fast_scroll(page)
            
            # Extraer productos con método PORT optimizado
            products = await self._extract_products_port_optimized(page)
            
            self.logger.debug(f"📄 Página start={start_value}: {len(products)} productos")
            
            return products
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping página start={start_value}: {e}")
            return []
            
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def _abcdin_fast_scroll(self, page: Page):
        """📜 Scroll rápido optimizado para AbcDin"""
        try:
            # Scroll rápido a la mitad y al final
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            await page.wait_for_timeout(int(self.config['scroll_wait'] * 1000))
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(int(self.config['mid_scroll_wait'] * 1000))
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error en scroll rápido: {e}")

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

    async def _save_retailer_json_complete(self, products: List[ProductData], session_id: str, execution_time: float):
        """💾 Guardar resultados COMPLETOS en JSON específico por retailer con timestamp"""
        try:
            # Crear timestamp para el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Crear directorio específico por retailer
            retailer_dir = Path(__file__).parent.parent / "resultados_json" / self.retailer
            retailer_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre del archivo con timestamp
            filename = f"{self.retailer}_productos_{timestamp}.json"
            filepath = retailer_dir / filename
            
            # Convertir ProductData a diccionarios serializables
            products_data = []
            for product in products:
                product_dict = {
                    'title': product.title,
                    'sku': product.sku,
                    'brand': product.brand,
                    'current_price': product.current_price,
                    'original_price': product.original_price,
                    'product_url': product.product_url,
                    'image_urls': product.image_urls,
                    'rating': product.rating,
                    'reviews_count': product.reviews_count,
                    'retailer': product.retailer,
                    'category': product.category,
                    'extraction_timestamp': product.extraction_timestamp.isoformat() if hasattr(product.extraction_timestamp, 'isoformat') else str(product.extraction_timestamp),
                    'additional_info': product.additional_info
                }
                products_data.append(product_dict)
            
            # Crear estructura JSON completa
            json_data = {
                'retailer': self.retailer,
                'extraction_timestamp': timestamp,
                'session_id': session_id,
                'execution_time_seconds': execution_time,
                'total_products': len(products),
                'extraction_method': 'parallel_port_integrated_v5',
                'pagination_config': self.pagination_config,
                'source_url': self.base_url,
                'products': products_data,
                'extraction_summary': {
                    'brands_found': list(set(p.get('brand', '') for p in products_data if p.get('brand'))),
                    'price_range': {
                        'min_price': min((p.get('current_price', 0) for p in products_data if p.get('current_price', 0) > 0), default=0),
                        'max_price': max((p.get('current_price', 0) for p in products_data if p.get('current_price', 0) > 0), default=0),
                        'avg_price': sum(p.get('current_price', 0) for p in products_data if p.get('current_price', 0) > 0) / len([p for p in products_data if p.get('current_price', 0) > 0]) if len([p for p in products_data if p.get('current_price', 0) > 0]) > 0 else 0
                    },
                    'products_with_rating': len([p for p in products_data if p.get('rating', 0) > 0]),
                    'products_with_discount': len([p for p in products_data if p.get('original_price', 0) > p.get('current_price', 0)])
                }
            }
            
            # Guardar archivo JSON con encoding UTF-8
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 AbcDin JSON guardado: {filepath}")
            self.logger.info(f"📊 Resumen: {len(products)} productos, {execution_time:.1f}s")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando JSON AbcDin: {e}")
            return None


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
        
        # Mostrar productos encontrados
        for i, product in enumerate(result.products[:3], 1):
            print(f"\n{i}. {product.title}")
            print(f"   💰 ${product.current_price:,} | Original: ${product.original_price or 0:,}")
            print(f"   🏷️ {product.brand}")
            print(f"   🔗 {product.product_url}")
        
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
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    asyncio.run(test_abcdin_improved_scraper())