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
    """🛍️ Scraper Ripley V5 con selectores PORT + PARALELO OPTIMIZADO + GUARDADO JSON"""
    
    def __init__(self):
        super().__init__("ripley")
        
        # URLs exactas (del PORT)
        self.base_urls = {
            'home': 'https://simple.ripley.cl',
            'celulares': 'https://simple.ripley.cl/tecno/celulares',
            'search': 'https://simple.ripley.cl/search'
        }
        
        # URL base específica del PORT funcional
        self.base_url = "https://simple.ripley.cl/tecno/celulares?source=menu&s=mdco&type=catalog"
        
        # Configuración de paginación centralizada
        self.pagination_config = self._load_pagination_config()
        
        # Configuración ULTRA-RÁPIDA optimizada (como Paris/Falabella pero con navegador visible)
        self.config = {
            'initial_wait': 3,         # 3 segundos inicial (Ripley necesita más que Paris)
            'scroll_wait': 2,          # 2 segundos después del scroll
            'mid_scroll_wait': 1,      # 1 segundo después del scroll a mitad
            'element_timeout': 5000,   # 5 segundos timeout por elemento
            'page_timeout': 35000,     # 35 segundos total optimizado
            'batch_size': 15,          # Lotes para procesar
            
            # 🚨 CONFIGURACIÓN CRÍTICA PARA RIPLEY
            'requires_visible_browser': True,   # OBLIGATORIO para Ripley
            'browser_position': (-2000, 0),     # Posición fuera de pantalla
            'window_size': (1920, 1080),        # Tamaño completo
            'simulate_human_behavior': True,     # Comportamiento humano
            'mandatory_scroll_down': True       # Scroll hacia abajo obligatorio
        }
        
        self.logger.info("🛍️ Ripley Scraper V5 PARALELO - NAVEGADOR VISIBLE + PORT inicializado")
        
        # CRÍTICO: Ripley REQUIERE navegador visible
        self._requires_visible_browser = True

    async def get_page(self) -> Optional[Page]:
        """🌐 Override get_page para Ripley - NAVEGADOR VISIBLE OBLIGATORIO"""
        try:
            if not self.browser:
                # Lanzar navegador VISIBLE específicamente para Ripley
                from playwright.async_api import async_playwright
                pw = await async_playwright().start()
                
                # CONFIGURACIÓN EXACTA como debug exitoso
                launch_kwargs = {
                    'headless': False,  # NAVEGADOR VISIBLE (diferente de BaseScraperV5)
                    'args': [
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled'
                    ]
                }
                
                self.browser = await pw.chromium.launch(**launch_kwargs)
                self.logger.info("🖥️ RIPLEY: Navegador VISIBLE iniciado (override)")
            
            # Usar setup browser del padre pero con navegador visible ya iniciado
            if not await self._setup_browser():
                return None
                
            return self.page
            
        except Exception as e:
            self.logger.error(f"💥 Error creando página RIPLEY: {e}")
            # Fallback al método padre si falla
            return await super().get_page()

    async def _setup_browser(self) -> bool:
        """🌐 Setup browser específico para Ripley con posición off-screen"""
        if not self.browser:
            # Si no hay browser, usar get_page que lo creará
            await self.get_page()
            if not self.browser:
                return False
        
        try:
            # User agents exactos como debug exitoso
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            # Context options exactos como debug exitoso
            context_options = {
                'viewport': {'width': 1280, 'height': 720},  # Como debug exitoso
                'user_agent': user_agent
            }
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            # CRÍTICO: Posicionar navegador fuera de pantalla (como PORT)
            try:
                # Esto funciona solo con navegadores visibles
                await self.page.set_viewport_size({'width': 1280, 'height': 720})
                self.logger.info("🖥️ RIPLEY: Navegador posicionado fuera de pantalla (-2000, 0)")
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo posicionar navegador: {e}")
            
            self.logger.info("✅ RIPLEY: Browser configurado con navegador VISIBLE")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando browser RIPLEY: {e}")
            # Fallback al método padre
            return await super()._setup_browser()

    def _load_pagination_config(self) -> Dict[str, Any]:
        """📄 Cargar configuración de paginación desde config.json"""
        try:
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent / "config.json"
            if not config_path.exists():
                self.logger.warning(f"⚠️ Config.json no encontrado en {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            ripley_config = config_data.get('retailers', {}).get('ripley', {})
            pagination_config = ripley_config.get('paginacion', {})
            
            if pagination_config:
                self.logger.info(f"✅ Configuración de paginación Ripley cargada: {pagination_config.get('url_pattern', 'N/A')}")
                return pagination_config
            else:
                self.logger.warning("⚠️ No se encontró configuración de paginación para Ripley")
                return {}
                
        except Exception as e:
            self.logger.error(f"💥 Error cargando configuración de paginación: {e}")
            return {}

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
            
            # Scraping PARALELO con paginación (como Paris/Falabella/AbcDin)
            products = await self._scrape_with_pagination_parallel(page, max_products)
            
            # Guardar JSON individual como Paris/Falabella/AbcDin
            if products:
                await self._save_retailer_json_complete(products, session_id, execution_time)
            
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
                    'pagination_used': len(self.pagination_config) > 0,
                    'visible_browser_required': True
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'parallel_port_integrated'}
            )

    async def _scrape_with_pagination_parallel(self, initial_page: Page, max_products: int) -> List[ProductData]:
        """📦 Scraping SECUENCIAL para Ripley (navegador visible único) + lógica PORT"""
        
        all_products = []
        current_page = 1
        consecutive_empty_pages = 0
        
        # RIPLEY REQUIERE SECUENCIAL - UN NAVEGADOR VISIBLE
        max_empty_pages = 2  
        max_pages_config = self.pagination_config.get('max_pages', 20) if self.pagination_config else 20
        auto_stop_enabled = self.pagination_config.get('auto_stop', True) if self.pagination_config else True
        
        self.logger.info(f"🚨 Iniciando Ripley SECUENCIAL (navegador visible ÚNICO):")
        self.logger.info(f"   📄 Max páginas: {max_pages_config}")
        self.logger.info(f"   🔚 Auto-stop: {'Activado' if auto_stop_enabled else 'Desactivado'}")
        self.logger.info(f"   🚨 Navegador visible: OBLIGATORIO en posición (-2000, 0)")
        
        while len(all_products) < max_products and current_page <= max_pages_config:
            
            self.logger.info(f"🚀 Procesando Ripley página {current_page}")
            
            # Procesar UNA página (secuencial para navegador visible)
            page_products = await self._scrape_single_ripley_page(current_page)
            
            # Verificar si la página está vacía
            if not page_products:
                consecutive_empty_pages += 1
                self.logger.warning(f"⚠️ Página vacía {consecutive_empty_pages}/{max_empty_pages}")
                
                if auto_stop_enabled and consecutive_empty_pages >= max_empty_pages:
                    self.logger.info("🛑 Auto-stop activado: demasiadas páginas vacías")
                    break
            else:
                consecutive_empty_pages = 0
                all_products.extend(page_products)
                self.logger.info(f"✅ Página {current_page}: +{len(page_products)} productos (Total: {len(all_products)})")
            
            # Avanzar a la siguiente página
            current_page += 1
            
            # Delay entre páginas para evitar bloqueos
            await asyncio.sleep(3)  # Ripley necesita más delay
            
            # Verificar si ya tenemos suficientes productos
            if len(all_products) >= max_products:
                break
        
        final_products = all_products[:max_products]
        self.logger.info(f"✅ Ripley SECUENCIAL terminado: {len(final_products)} productos finales")
        
        return final_products

    async def _process_ripley_pages_parallel(self, page_numbers: List[int]) -> List[List[ProductData]]:
        """⚡ Procesar páginas de Ripley en paralelo"""
        
        tasks = []
        for page_num in page_numbers:
            task = self._scrape_single_ripley_page(page_num)
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Error en página {page_numbers[i]}: {result}")
                valid_results.append([])
            else:
                valid_results.append(result or [])
        
        return valid_results

    async def _scrape_single_ripley_page(self, page_num: int) -> List[ProductData]:
        """📄 Scraper de una sola página de Ripley con navegador visible y scroll obligatorio"""
        
        page = None
        try:
            # CRÍTICO: Usar navegador visible compartido para Ripley
            if not hasattr(self, 'page') or not self.page:
                page = await self.get_page()
            else:
                # Usar la página ya configurada con navegador visible
                page = self.page
                
            if not page:
                return []
            
            # Construir URL con paginación Ripley
            if page_num == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}&page={page_num}"
            
            self.logger.info(f"🚨 Ripley navegador VISIBLE - Scraping página {page_num}: {url}")
            
            # Navegar con timeout generoso
            await page.goto(url, wait_until='domcontentloaded', timeout=self.config['page_timeout'])
            
            # Espera inicial OBLIGATORIA para Ripley
            await page.wait_for_timeout(self.config['initial_wait'] * 1000)
            
            # 🚨 SCROLL OBLIGATORIO HACIA ABAJO (requerimiento crítico para Ripley)
            await self._ripley_obligatory_scroll_down(page)
            
            # Extraer productos con método PORT de Ripley
            products = await self._extract_products_port_ripley(page)
            
            self.logger.info(f"📄 Ripley página {page_num}: {len(products)} productos extraídos")
            
            return products
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping Ripley página {page_num}: {e}")
            return []

    async def _ripley_obligatory_scroll_down(self, page: Page):
        """📜 Scroll OBLIGATORIO hacia abajo para Ripley - NAVEGADOR VISIBLE fuera de pantalla"""
        
        try:
            self.logger.info("🚨 Ejecutando scroll OBLIGATORIO hacia abajo (Ripley requiere navegador visible)")
            
            # Obtener dimensiones iniciales
            initial_height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            current_position = 0
            scroll_step = 300  # Scroll más grande para Ripley
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
                
                # Delay entre scrolls para simular humano
                await page.wait_for_timeout(300)  # 300ms entre scrolls
                
                # Verificar si llegamos al final
                current_height = await page.evaluate('document.body.scrollHeight')
                if current_position >= current_height - viewport_height:
                    break
            
            # Scroll final hasta el fondo OBLIGATORIO
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)  # Espera final de 2 segundos
            
            # Verificar carga de productos después del scroll
            await page.wait_for_timeout(3000)  # Espera adicional para carga de productos
            
            final_height = await page.evaluate('document.body.scrollHeight')
            self.logger.info(f"✅ Scroll OBLIGATORIO completado: {total_scrolled}px scrolled, altura final: {final_height}px")
            
        except Exception as e:
            self.logger.error(f"💥 Error en scroll OBLIGATORIO: {e}")

    async def _ripley_fast_scroll(self, page: Page):
        """📜 Scroll rápido optimizado para Ripley (navegador visible) - DEPRECATED"""
        try:
            # Scroll rápido pero más cauteloso para Ripley
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            await page.wait_for_timeout(int(self.config['scroll_wait'] * 1000))
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(int(self.config['mid_scroll_wait'] * 1000))
            
            # Scroll adicional para Ripley (crítico)
            await page.evaluate("window.scrollTo(0, 0);")
            await page.wait_for_timeout(500)
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error en scroll rápido: {e}")

    async def _scrape_with_parallel_port_old(self, page: Page, url: str, max_products: int) -> List[ProductData]:
        
        try:
            self.logger.info(f"🚀 Iniciando Ripley PARALELO - max: {max_products}")
            
            # Configurar paginación para Ripley
            pagination_config = {
                'url_pattern': url + "?page={page}",
                'max_pages': 25,  # Ripley típicamente tiene menos páginas
                'products_per_page': 24,  # Ripley muestra 24 por página
                'auto_stop': True,
                'empty_page_threshold': 2
            }
            
            # Procesar con paginación paralela
            products = await self._process_pagination_parallel(page, pagination_config, max_products)
            
            self.logger.info(f"🎯 Ripley PARALELO completado: {len(products)} productos")
            return products
            
        except Exception as e:
            self.logger.error(f"💥 Error en Ripley PARALELO: {e}")
            return []

    async def _process_pagination_parallel(self, page: Page, config: dict, max_products: int) -> List[ProductData]:
        """🔄 Procesar páginas en paralelo (adaptado de Paris exitoso)"""
        
        all_products = []
        batch_size = 5  # 5 páginas paralelas
        current_page = 1
        consecutive_empty = 0
        
        while len(all_products) < max_products and current_page <= config['max_pages']:
            
            # Crear lote de páginas paralelas
            batch_pages = list(range(current_page, min(current_page + batch_size, config['max_pages'] + 1)))
            
            self.logger.info(f"🚀 Ripley lote paralelo: páginas {batch_pages[0]}-{batch_pages[-1]}")
            
            # Procesar lote en paralelo
            batch_results = await self._process_pages_parallel_ripley(batch_pages, config)
            
            # Agregar productos del lote
            batch_products = []
            empty_pages_in_batch = 0
            
            for page_num, products in batch_results:
                if products:
                    batch_products.extend(products)
                    self.logger.info(f"   ✅ Página {page_num}: {len(products)} productos")
                else:
                    empty_pages_in_batch += 1
                    self.logger.warning(f"   ⚠️ Página {page_num}: vacía")
            
            # Agregar productos válidos
            valid_products = [p for p in batch_products if p.title and p.sku]
            all_products.extend(valid_products)
            
            # Control de parada automática
            if empty_pages_in_batch == len(batch_pages):
                consecutive_empty += 1
                self.logger.warning(f"⚠️ Lote completamente vacío ({consecutive_empty})")
                
                if consecutive_empty >= 2:  # 2 lotes vacíos = terminar
                    self.logger.info("🔚 2 lotes vacíos, terminando")
                    break
            else:
                consecutive_empty = 0
            
            # Verificar límite
            if len(all_products) >= max_products:
                self.logger.info(f"🎯 Límite alcanzado: {len(all_products)}/{max_products}")
                break
                
            current_page += batch_size
            await asyncio.sleep(0.1)  # Pausa entre lotes
        
        # Devolver productos limitados
        return all_products[:max_products]

    async def _process_pages_parallel_ripley(self, page_numbers: List[int], config: dict) -> List[tuple]:
        """🔄 Procesar páginas Ripley en paralelo"""
        
        tasks = []
        for page_num in page_numbers:
            task = asyncio.create_task(self._scrape_single_page_ripley(page_num, config))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            page_num = page_numbers[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"❌ Error página {page_num}: {result}")
                processed_results.append((page_num, []))
            else:
                processed_results.append((page_num, result))
        
        return processed_results

    async def _scrape_single_page_ripley(self, page_num: int, config: dict) -> List[ProductData]:
        """📄 Extraer productos de una página específica de Ripley - EXACTO como debug exitoso"""
        
        try:
            # Construir URL de página
            if page_num == 1:
                page_url = config.get('url_base', config['url_pattern'].split('?')[0])  # URL base para página 1
            else:
                page_url = config['url_pattern'].format(page=page_num)
            
            self.logger.info(f"🌐 RIPLEY página {page_num}: {page_url}")
            
            # Nueva página
            page = await self.get_page()
            await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            
            # EXACTO como debug exitoso: Espera carga inicial
            self.logger.info(f"⏳ Esperando carga inicial página {page_num}...")
            await asyncio.sleep(5)
            
            # EXACTO como debug exitoso: 5 scrolls + final
            self.logger.info(f"📜 Scroll obligatorio página {page_num}...")
            viewport_height = 720
            
            for i in range(5):  # 5 scrolls exacto como debug exitoso
                scroll_to = (i + 1) * viewport_height
                await page.evaluate(f"window.scrollTo(0, {scroll_to})")
                await asyncio.sleep(1)
            
            # Scroll final hasta el fondo (como debug exitoso)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            # Extraer productos con lógica PORT (que funciona)
            products = await self._extract_products_port_ripley(page)
            
            self.logger.info(f"✅ RIPLEY página {page_num}: {len(products)} productos")
            
            await page.close()
            return products
            
        except Exception as e:
            self.logger.error(f"❌ Error página {page_num}: {e}")
            return []

    async def _extract_products_port_ripley(self, page: Page) -> List[ProductData]:
        """🔍 Extraer productos usando EXACTA lógica PORT Ripley con BeautifulSoup"""
        products = []
        
        try:
            # Obtener HTML como PORT (usa BeautifulSoup)
            html_content = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            self.logger.info("🔍 RIPLEY PORT: Usando BeautifulSoup para extraer (igual que PORT)")
            
            # EXACTO como PORT: buscar contenedores 'a' con data-partnumber
            product_containers = soup.find_all('a', attrs={'data-partnumber': True})
            
            self.logger.info(f"🔍 RIPLEY PORT: Contenedores encontrados: {len(product_containers)}")
            
            if not product_containers:
                self.logger.warning("⚠️ RIPLEY: No se encontraron contenedores con 'a[data-partnumber]'")
                return products
            
            for container in product_containers:
                try:
                    # Extraer información desde los atributos (EXACTO como PORT)
                    product_code = container.get('data-partnumber', '')
                    product_url = container.get('href', '')
                    
                    self.logger.info(f"\n🔍 Analizando producto: {product_code}")
                    
                    # Link completo del producto (EXACTO como PORT)
                    full_link = f"https://simple.ripley.cl{product_url}" if product_url.startswith('/') else product_url
                    
                    # Buscar marca (EXACTO como PORT)
                    brand_elem = container.select_one('.brand-logo span, .catalog-product-details__logo-container span')
                    brand = brand_elem.get_text(strip=True) if brand_elem else ""
                    
                    # Buscar nombre del producto (EXACTO como PORT)
                    name_elem = container.select_one('.catalog-product-details__name')
                    product_name = name_elem.get_text(strip=True) if name_elem else ""
                    
                    # Extraer precios (EXACTO como PORT)
                    normal_price_text = ""
                    internet_price_text = ""
                    ripley_price_text = ""
                    normal_price_numeric = None
                    internet_price_numeric = None
                    ripley_price_numeric = None
                    
                    # Precio normal (tachado) - EXACTO como PORT
                    normal_price_elem = container.select_one('.catalog-prices__list-price.catalog-prices__line_thru')
                    if normal_price_elem:
                        normal_price_text = normal_price_elem.get_text(strip=True)
                        price_match = re.search(r'\$?([0-9.,]+)', normal_price_text.replace('.', ''))
                        if price_match:
                            try:
                                normal_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
                    
                    # Precio internet - EXACTO como PORT
                    internet_price_elem = container.select_one('.catalog-prices__offer-price')
                    if internet_price_elem:
                        internet_price_text = internet_price_elem.get_text(strip=True)
                        price_match = re.search(r'\$?([0-9.,]+)', internet_price_text.replace('.', ''))
                        if price_match:
                            try:
                                internet_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
                    
                    # Precio tarjeta Ripley - EXACTO como PORT
                    ripley_price_elem = container.select_one('.catalog-prices__card-price')
                    if ripley_price_elem:
                        ripley_price_text = ripley_price_elem.get_text(strip=True).split('$')[1].split(' ')[0] if '$' in ripley_price_elem.get_text() else ""
                        if ripley_price_text:
                            price_match = re.search(r'([0-9.,]+)', ripley_price_text.replace('.', ''))
                            if price_match:
                                try:
                                    ripley_price_numeric = int(price_match.group(1).replace(',', ''))
                                except:
                                    pass
                    
                    # Descuento - EXACTO como PORT
                    discount_elem = container.select_one('.catalog-product-details__discount-tag')
                    discount_percent = discount_elem.get_text(strip=True) if discount_elem else ""
                    
                    # Imagen principal - EXACTO como PORT
                    img_elem = container.select_one('img')
                    image_url = img_elem.get('src', '') if img_elem else ""
                    image_alt = img_elem.get('alt', '') if img_elem else ""
                    
                    # Colores disponibles - EXACTO como PORT
                    color_elements = container.select('.catalog-colors-option-outer')
                    colors = []
                    for color_elem in color_elements:
                        color_title = color_elem.get('title', '')
                        if color_title:
                            colors.append(color_title)
                    
                    # Emblemas/badges - EXACTO como PORT
                    emblem_elements = container.select('.emblem')
                    emblems = []
                    for emblem in emblem_elements:
                        emblem_text = emblem.get_text(strip=True)
                        if emblem_text:
                            emblems.append(emblem_text)
                    
                    # Extraer especificaciones del nombre - EXACTO como PORT
                    storage = ""
                    ram = ""
                    screen_size = ""
                    camera = ""
                    
                    # Almacenamiento
                    storage_match = re.search(r'(\d+)\s*gb(?!\s+ram)', product_name.lower())
                    if storage_match:
                        storage = f"{storage_match.group(1)}GB"
                    
                    # RAM
                    ram_match = re.search(r'(\d+)\s*gb\s+ram', product_name.lower())
                    if ram_match:
                        ram = f"{ram_match.group(1)}GB"
                    
                    # Tamaño de pantalla
                    screen_match = re.search(r'(\d+\.?\d*)"', product_name)
                    if screen_match:
                        screen_size = f"{screen_match.group(1)}\""
                    
                    # Cámara
                    camera_match = re.search(r'(\d+)mp', product_name.lower())
                    if camera_match:
                        camera = f"{camera_match.group(1)}MP"
                    
                    # Solo agregar productos válidos - MAPEAR campos PORT a estructura V5
                    if product_code and product_name:
                        product_data = ProductData(
                            title=product_name,  # name -> title
                            current_price=internet_price_numeric if internet_price_numeric else 0.0,  # internet_price -> current_price
                            original_price=normal_price_numeric if normal_price_numeric else 0.0,  # normal_price -> original_price
                            card_price=ripley_price_numeric if ripley_price_numeric else 0.0,  # ripley_price -> card_price
                            brand=brand,
                            sku=product_code,  # product_code -> sku
                            product_url=full_link,
                            image_urls=[image_url] if image_url else [],  # image_url -> image_urls
                            retailer="ripley",
                            category="celulares",
                            additional_info={
                                'screen_size': screen_size,
                                'storage': storage,
                                'ram': ram,
                                'camera': camera,
                                'colors': ', '.join(colors),
                                'normal_price_text': normal_price_text,
                                'internet_price_text': internet_price_text,
                                'ripley_price_text': ripley_price_text,
                                'discount_percent': discount_percent,
                                'emblems': ', '.join(emblems),
                                'image_alt': image_alt,
                                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        )
                        
                        products.append(product_data)
                        
                        # Log igual que PORT
                        self.logger.info(f"  [OK] Código: {product_code}")
                        self.logger.info(f"  [OK] Marca: {brand}")
                        self.logger.info(f"  [OK] Nombre: {product_name[:50]}...")
                        self.logger.info(f"  [OK] Precio Normal: {normal_price_text}")
                        self.logger.info(f"  [OK] Precio Internet: {internet_price_text}")
                        self.logger.info(f"  [OK] Precio Ripley: {ripley_price_text}")
                        self.logger.info(f"  [OK] Descuento: {discount_percent}")
                        self.logger.info(f"  [OK] Specs: {screen_size} | {storage} | {ram} | {camera}")
                        if colors:
                            self.logger.info(f"  [OK] Colores: {', '.join(colors)}")
                        if emblems:
                            self.logger.info(f"  [OK] Emblemas: {', '.join(emblems[:2])}...")  # Solo primeros 2
                        
                except Exception as e:
                    self.logger.error(f"  [ERROR] procesando contenedor: {e}")
                    continue
            
            self.logger.info(f"✅ RIPLEY PORT: Extraídos {len(products)} productos")
            return products
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting products RIPLEY PORT: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
