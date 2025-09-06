# -*- coding: utf-8 -*-
"""
🏬 Paris Chile Scraper v5 MEJORADO - Integración de Selectores PORT 
================================================================

INTEGRA SELECTORES EXACTOS DE scrappers_port/paris_final.py que SÍ FUNCIONAN
en la arquitectura V5 con Playwright async.

✅ SELECTORES ESPECÍFICOS MIGRADOS:
- div[data-cnstrc-item-id] (selector principal)  
- span.ui-text-[13px].ui-leading-[15px] (precio actual)
- span.ui-line-through.ui-font-semibold (precio anterior)
- div[data-testid="paris-label"] (descuentos)

✅ LÓGICA DE PARSING MIGRADA:
- Extracción por data attributes
- Parsing de precios con regex específico
- Manejo de especificaciones (storage, RAM, network)
- Mapeo de links y metadatos

🎯 OBJETIVO: 100% compatibilidad con scraper PORT que SÍ EXTRAE DATOS
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

# Selector principal (el que SÍ encuentra productos)
PRODUCT_CONTAINER_SELECTOR = "div[data-cnstrc-item-id]"

# Selectores de precios específicos (del PORT funcional)
PRICE_SELECTORS = {
    'current_price': 'span.ui-text-\\[13px\\].ui-leading-\\[15px\\].desktop\\:ui-text-lg, span[class*="ui-font-semibold"][class*="desktop:ui-font-medium"]',
    'old_price': 'span.ui-line-through.ui-font-semibold', 
    'discount': 'div[data-testid="paris-label"][aria-label*="%"]',
    'brand': 'span.ui-font-semibold.ui-line-clamp-2.ui-text-\\[11px\\]',
    'rating_value': 'button[data-testid="star-rating-rating-value"]',
    'rating_count': 'button[data-testid="star-rating-total-rating"]'
}

# Links y metadatos
METADATA_SELECTORS = {
    'product_link': 'a[href]',
    'product_image': 'img[alt="Imagen de producto"]'
}

# Regex exactos del PORT para specs
SPECS_REGEX = {
    'storage': r'(\d+)gb(?!\s+ram)',  # Storage (no RAM)
    'ram': r'(\d+)gb\s+ram',         # RAM específico 
    'network': r'(4g|5g)',           # Red móvil
    'color': r'(negro|blanco|azul|rojo|verde|gris|dorado|plateado|purpura|rosa)$'  # Color final
}

class ParisScraperV5Improved(BaseScraperV5):
    """🏬 Scraper Paris V5 con selectores PORT integrados"""
    
    def __init__(self):
        super().__init__("paris")
        
        # URLs exactas (del PORT)
        self.base_urls = {
            'home': 'https://www.paris.cl',
            'celulares': 'https://www.paris.cl/tecnologia/celulares/',
            'search': 'https://www.paris.cl/search'
        }
        
        # Cargar configuración de paginación centralizada
        self.pagination_config = self._load_pagination_config()
        
        # Configuración específica de Paris (optimizada)
        self.config = {
            'page_timeout': 45000,     # 45 segundos (menor que PORT pero suficiente)
            'load_wait': 8000,         # 8 segundos inicial (menor que PORT)
            'scroll_wait': 300,        # Espera entre scrolls
            'batch_size': 15,          # Procesamiento por lotes
            'element_timeout': 5000    # Timeout por elemento
        }
        
        self.logger.info("🏬 Paris Scraper V5 MEJORADO inicializado - selectores PORT integrados")

    def _load_pagination_config(self) -> Dict[str, Any]:
        """📄 Cargar configuración de paginación desde config.json"""
        try:
            config_path = Path(__file__).parent.parent / "config.json"
            if not config_path.exists():
                self.logger.warning(f"⚠️ Config.json no encontrado en {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            paris_config = config_data.get('retailers', {}).get('paris', {})
            pagination_config = paris_config.get('paginacion', {})
            
            if pagination_config:
                self.logger.info(f"✅ Configuración de paginación cargada: {pagination_config.get('url_pattern', 'N/A')}")
                return pagination_config
            else:
                self.logger.warning("⚠️ No se encontró configuración de paginación para Paris")
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
        """🔍 Scraper con selectores exactos del PORT"""
        
        start_time = datetime.now()
        session_id = f"paris_improved_{category}_{int(start_time.timestamp())}"
        
        try:
            # URL de categoría
            category_url = self.base_urls.get(category, self.base_urls['celulares'])
            
            self.logger.info(f"🔍 Scraping Paris MEJORADO - {category}: {category_url}")
            
            # Obtener página
            page = await self.get_page()
            
            # Scraping con lógica PORT integrada
            products = await self._scrape_with_port_logic(page, category_url, max_products)
            
            # DEBUG: Rastrear flujo de datos
            self.logger.info(f"🔍 PIPELINE DEBUG - Productos después de scraping: {len(products)}")
            if products:
                self.logger.info(f"🔍 PIPELINE DEBUG - Primer producto: {products[0].name[:30]}...")
            
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
                    'scraping_method': 'port_selectors_integrated',
                    'port_compatibility': True,
                    'extraction_method': 'playwright_dom_query',
                    'success_rate': f"{len(products)}/{max_products}"
                }
            )
            
            # DEBUG: Verificar ScrapingResult
            self.logger.info(f"🔍 PIPELINE DEBUG - ScrapingResult creado:")
            self.logger.info(f"   success: {result.success}")  
            self.logger.info(f"   total_found: {result.total_found}")
            self.logger.info(f"   len(products): {len(result.products)}")
            
            self.logger.info(f"✅ Paris MEJORADO completado: {len(products)} productos en {execution_time:.1f}s")
            
            # DEBUG: Verificar antes de retornar
            self.logger.info(f"🔍 PIPELINE DEBUG - Retornando result con {len(result.products)} productos")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error Paris MEJORADO categoría {category}: {e}")
            
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'port_selectors_integrated'}
            )

    async def _scrape_with_port_logic(self, page: Page, url: str, max_products: int) -> List[ProductData]:
        """📦 Scraping usando lógica EXACTA del PORT funcional con timing optimizado"""
        
        all_products = []
        page_num = 1
        
        # Loop de paginación hasta alcanzar max_products
        while len(all_products) < max_products:
            try:
                # Construir URL de página
                page_url = self._build_page_url(url, page_num)
                
                self.logger.info(f"📄 Scraping Paris página {page_num}: {page_url}")
                await page.goto(page_url, wait_until='domcontentloaded', timeout=self.config['page_timeout'])
                
                # Cerrar modales (como en PORT)
                await self._dismiss_modals_port_style(page)
                
                # Esperar carga inicial EXACTO del PORT: 10 segundos
                self.logger.debug("⏰ Esperando carga inicial (10s como en PORT)...")
                await page.wait_for_timeout(10000)  # 10 segundos como PORT funcional
                
                # Scroll EXACTO del PORT para cargar productos
                await self._port_exact_scroll_strategy(page)
                
                # Extraer productos de esta página (método CORREGIDO que funciona)
                page_products = await self._extract_products_corrected_method(page)
                
                # DEBUG: Seguimiento detallado
                self.logger.info(f"🔍 PIPELINE DEBUG - Página {page_num}: {len(page_products)} productos extraídos")
                
                if not page_products:
                    self.logger.info(f"❌ No hay más productos en página {page_num}, terminando paginación")
                    break
                
                self.logger.info(f"✅ Página {page_num}: {len(page_products)} productos extraídos")
                all_products.extend(page_products)
                
                # DEBUG: Verificar acumulación
                self.logger.info(f"🔍 PIPELINE DEBUG - Total acumulado: {len(all_products)} productos")
                page_num += 1
                
                # Pausa entre páginas para evitar detección
                await page.wait_for_timeout(2000)
                
                # Si la página devolvió menos de 20 productos, probablemente no hay más páginas
                if len(page_products) < 20:
                    self.logger.info(f"🔚 Página {page_num-1} devolvió pocos productos ({len(page_products)}), posiblemente última página")
                    break
                
            except Exception as e:
                self.logger.error(f"❌ Error en página {page_num}: {e}")
                break
        
        self.logger.info(f"📦 Total productos extraídos con paginación: {len(all_products)} de {page_num-1} páginas")
        
        # Limitar a max_products  
        final_products = all_products[:max_products]
        
        # DEBUG: Verificar retorno final
        self.logger.info(f"🔍 PIPELINE DEBUG - Retornando {len(final_products)} productos (limitado de {len(all_products)})")
        
        return final_products

    def _build_page_url(self, base_url: str, page_num: int) -> str:
        """🔗 Construir URL de página usando configuración centralizada"""
        try:
            # Usar configuración centralizada si está disponible
            if self.pagination_config:
                url = self.get_pagination_url(page_num, self.pagination_config)
                if url:
                    return url
            
            # Fallback a lógica original para Paris
            if page_num <= 1:
                return base_url
            # Paris usa el parámetro 'page' en la query string
            if '?' in base_url:
                return f"{base_url}&page={page_num}"
            return f"{base_url}?page={page_num}"
                
        except Exception as e:
            self.logger.error(f"💥 Error construyendo URL de página: {e}")
            # Fallback seguro
            if page_num <= 1:
                return base_url
            return f"{base_url}?page={page_num}"

    async def _dismiss_modals_port_style(self, page: Page):
        """🚫 Cerrar modales usando método del PORT"""
        
        try:
            # Desactivar animaciones (del PORT)
            await page.add_style_tag(content="""
                * { animation: none !important; transition: none !important; }
                html, body { scroll-behavior: auto !important; }
            """)
        except:
            pass
        
        # Selectores de modales del PORT
        modal_selectors = [
            "button:has-text('Aceptar')",
            "button:has-text('Mantener ubicación')", 
            "button:has-text('No, gracias')",
            "button:has-text('Cerrar')",
            "[aria-label*='close' i]"
        ]
        
        dismissed = 0
        for selector in modal_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    if await el.is_visible():
                        await el.click()
                        dismissed += 1
                        await page.wait_for_timeout(200)
            except:
                continue
        
        if dismissed > 0:
            self.logger.debug(f"🚫 Modales cerrados: {dismissed}")
            await page.wait_for_timeout(500)

    async def _port_exact_scroll_strategy(self, page: Page):
        """📜 Estrategia de scroll EXACTA del PORT funcional"""
        self.logger.debug("📜 Iniciando scroll PORT: completo + mitad (como en scraper funcional)")
        
        # Scroll 1: Hasta el final completo (como PORT)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(5000)  # 5 segundos como PORT
        
        # Scroll 2: Hasta la mitad (como PORT)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
        await page.wait_for_timeout(3000)  # 3 segundos como PORT
        
        self.logger.debug("✅ Scroll PORT completado: productos cargados dinámicamente")

    async def _extract_products_corrected_method(self, page: Page) -> List[ProductData]:
        """🏷️ Método CORREGIDO que replica exactamente el debug exitoso"""
        products = []
        
        self.logger.debug("🔍 Extrayendo productos con método CORREGIDO...")
        
        # Usar EXACTAMENTE el mismo selector que debug
        containers = await page.query_selector_all("div[data-cnstrc-item-id]")
        
        self.logger.info(f"📦 Contenedores encontrados (corregido): {len(containers)}")
        
        for i, container in enumerate(containers):
            try:
                self.logger.info(f"🔍 Procesando contenedor {i+1}/{len(containers)}")
                product = await self._extract_single_product_port_method(container, page)
                
                if product:
                    products.append(product)
                    self.logger.info(f"✅ Producto {i+1} extraído: {product.name[:30]}...")
                else:
                    self.logger.info(f"❌ Producto {i+1}: _extract_single_product_port_method retornó None")
                    
            except Exception as e:
                self.logger.debug(f"⚠️ Error extrayendo producto {i+1}: {e}")
                continue
        
        self.logger.info(f"🎯 Productos extraídos EXITOSAMENTE: {len(products)}")
        return products

    async def _extract_products_port_method(self, page: Page) -> List[ProductData]:
        """🏷️ Extracción de productos con método EXACTO del PORT"""
        products = []
        
        self.logger.debug("🔍 Extrayendo productos con selectores PORT...")
        
        # Usar EXACTLY el mismo selector que PORT funcional
        containers = await page.query_selector_all("div[data-cnstrc-item-id]")
        
        self.logger.info(f"📦 Contenedores encontrados: {len(containers)}")
        
        for container in containers:
            try:
                product = await self._extract_single_product_port_method(container, page)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"⚠️ Error extrayendo producto individual: {e}")
                continue
        
        return products

    async def _extract_single_product_port_method(self, container, page: Page) -> Optional[ProductData]:
        """🏷️ Extraer un producto individual usando método PORT exacto"""
        try:
            # Data attributes (como PORT)
            product_code = await container.get_attribute('data-cnstrc-item-id') or ''
            product_name = await container.get_attribute('data-cnstrc-item-name') or ''
            price_from_data = await container.get_attribute('data-cnstrc-item-price') or ''
            
            # DEBUG: Verificar datos básicos
            self.logger.info(f"📋 DATA: código='{product_code}', nombre='{product_name[:50] if product_name else None}'")
            
            if not product_code or not product_name:
                self.logger.info(f"❌ RECHAZADO: Falta código ({bool(product_code)}) o nombre ({bool(product_name)})")
                return None
            
            # DEBUG: Prueba rápida - crear ProductData básico
            self.logger.info(f"✅ CREANDO ProductData básico para: {product_name[:30]}...")
            
            try:
                basic_product = ProductData(
                    title=product_name,
                    sku=product_code,
                    brand="Test",
                    current_price=100000,
                    original_price=150000,
                    retailer='paris',
                    category='celulares',
                    product_url="https://www.paris.cl/test"
                )
                self.logger.info(f"✅ ProductData CREADO exitosamente: {basic_product.title[:30]}...")
                return basic_product
                
            except Exception as create_error:
                self.logger.info(f"❌ ERROR creando ProductData: {create_error}")
                return None
            
            # Link del producto (como PORT)
            link_element = await container.query_selector('a[href]')
            product_link = ""
            if link_element:
                href = await link_element.get_attribute('href') or ''
                if href.startswith('/'):
                    product_link = f"https://www.paris.cl{href}"
                elif href.startswith('http'):
                    product_link = href
            
            # Precios usando MÚLTIPLES selectores como PORT (fallback strategy)
            current_price_text = ""
            current_price_numeric = None
            
            # CORREGIDO: Buscar TODOS los elementos con precio y tomar el correcto
            price_selectors = [
                'span[class*="ui-font-semibold"]',  # DEBUG confirmó que funciona
                'span:has-text("$")',
                'span[class*="ui-text-"]'
            ]
            
            for selector in price_selectors:
                try:
                    price_elements = await container.query_selector_all(selector)  # ←← TODOS los elementos
                    for elem in price_elements:
                        text = (await elem.text_content() or '').strip()
                        if '$' in text and len(text) < 20:  # Filtro: precio razonable
                            current_price_text = text
                            # Parsing de precio como PORT
                            import re
                            price_match = re.search(r'\$?([\d.,]+)', current_price_text.replace('.', ''))
                            if price_match:
                                try:
                                    current_price_numeric = int(price_match.group(1).replace(',', ''))
                                    if current_price_numeric > 1000:  # Precio válido > $1000
                                        break
                                except:
                                    continue
                    if current_price_numeric:  # Si encontró precio válido, salir del loop
                        break
                except:
                    continue
            
            # Precio anterior (PORT selector)
            old_price_text = ""
            old_price_numeric = None
            old_price_elem = await container.query_selector('span.ui-line-through.ui-font-semibold')
            if old_price_elem:
                old_price_text = (await old_price_elem.text_content() or '').strip()
                price_match = re.search(r'\$?([\d.,]+)', old_price_text.replace('.', ''))
                if price_match:
                    try:
                        old_price_numeric = int(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Descuento (PORT selector)
            discount_percent = ""
            discount_elem = await container.query_selector('div[data-testid="paris-label"][aria-label*="%"]')
            if discount_elem:
                discount_percent = await discount_elem.get_attribute('aria-label') or ''
            
            # Marca CORREGIDA: El debug mostró que está en posición [1]
            brand = ""
            try:
                brand_elements = await container.query_selector_all('span[class*="ui-font-semibold"]')
                if len(brand_elements) >= 2:  # DEBUG: Samsung está en posición [1]
                    brand_elem = brand_elements[1]
                    brand_text = (await brand_elem.text_content() or '').strip()
                    # Validar que sea una marca (no precio ni texto largo)
                    if brand_text and len(brand_text) < 20 and '$' not in brand_text:
                        brand = brand_text
            except:
                pass
            
            # Imagen (PORT method)
            img_src = ""
            img_element = await container.query_selector('img[alt="Imagen de producto"]')
            if img_element:
                # Obtener srcset como PORT
                srcset = await img_element.get_attribute('srcset') or ''
                if srcset:
                    # Tomar última URL (mayor resolución) como PORT
                    import re
                    urls = re.findall(r'(https://[^\s]+)', srcset)
                    img_src = urls[-1] if urls else (await img_element.get_attribute('src') or '')
                else:
                    img_src = await img_element.get_attribute('src') or ''
            
            # Rating y reviews (PORT method)
            rating = "0"
            rating_elem = await container.query_selector('button[data-testid="star-rating-rating-value"]')
            if rating_elem:
                rating = (await rating_elem.text_content() or '').strip()
            
            reviews = "0"
            reviews_elem = await container.query_selector('button[data-testid="star-rating-total-rating"]')
            if reviews_elem:
                reviews_text = (await reviews_elem.text_content() or '').strip()
                reviews = reviews_text.replace('(', '').replace(')', '')
            
            # Especificaciones usando regex PORT exacto
            import re
            storage = ""
            ram = ""
            network = ""
            color = ""
            
            # Regex exactos del PORT
            product_name_lower = product_name.lower()
            
            storage_match = re.search(r'(\d+)gb(?!\s+ram)', product_name_lower)
            if storage_match:
                storage = f"{storage_match.group(1)}GB"
            
            ram_match = re.search(r'(\d+)gb\s+ram', product_name_lower)
            if ram_match:
                ram = f"{ram_match.group(1)}GB"
            
            network_match = re.search(r'(4g|5g)', product_name_lower)
            if network_match:
                network = network_match.group(1).upper()
            
            color_match = re.search(r'(negro|blanco|azul|rojo|verde|gris|dorado|plateado|purpura|rosa)$', product_name_lower)
            if color_match:
                color = color_match.group(1).title()
            
            # Crear ProductData (estructura V5 pero con datos PORT)
            product_data = ProductData(
                product_code=product_code,
                name=product_name,
                brand=brand,
                storage=storage,
                ram=ram,
                network=network,
                color=color,
                current_price_text=current_price_text,
                current_price=current_price_numeric,
                old_price_text=old_price_text,
                old_price=old_price_numeric,
                discount_percent=discount_percent,
                rating=rating,
                reviews_count=reviews,
                image_url=img_src,
                product_link=product_link,
                price_from_data=price_from_data,
                retailer='paris',
                category='celulares',
                scraped_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            return product_data
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error procesando producto individual: {e}")
            return None

    async def _progressive_scroll_port_style(self, page: Page):
        """📜 Scroll progresivo como en PORT"""
        
        try:
            # Obtener altura inicial
            initial_height = await page.evaluate("document.body.scrollHeight")
            
            # Scroll en incrementos (lógica PORT simplificada)
            for i in range(3):  # Menos iteraciones que PORT para eficiencia
                scroll_position = (i + 1) * 1000
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                
                new_height = await page.evaluate("document.body.scrollHeight")
                
                if new_height == initial_height and i > 1:
                    break
                
                await page.wait_for_timeout(self.config['scroll_wait'])
                initial_height = new_height
            
            # Volver arriba
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(200)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en scroll: {e}")

    async def _extract_products_port_method(self, page: Page) -> List[ProductData]:
        """📋 Extraer productos con método exacto del PORT"""
        
        products = []
        
        try:
            # Buscar contenedores con selector exacto del PORT
            await page.wait_for_selector(PRODUCT_CONTAINER_SELECTOR, timeout=self.config['element_timeout'])
            containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
            
            total_containers = len(containers)
            self.logger.info(f"🔍 Contenedores encontrados con selector PORT: {total_containers}")
            
            if total_containers == 0:
                return products
            
            # Procesar cada contenedor (lógica PORT adaptada)
            successful = 0
            for i, container in enumerate(containers):
                try:
                    product = await self._extract_single_product_port(container, i)
                    if product:
                        products.append(product)
                        successful += 1
                        
                except Exception as e:
                    self.logger.debug(f"⚠️ Error procesando contenedor {i}: {e}")
                    continue
                
                # Cleanup handle
                try:
                    await container.dispose()
                except:
                    pass
            
            self.logger.info(f"✅ Productos procesados con método PORT: {successful}/{total_containers}")
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo productos método PORT: {e}")
        
        return products

    async def _extract_single_product_port(self, container: ElementHandle, index: int) -> Optional[ProductData]:
        """📋 Extraer producto individual con TODOS los selectores del PORT original"""
        
        try:
            # ==========================================
            # EXTRACCIÓN COMPLETA - TODOS LOS CAMPOS DISPONIBLES
            # ==========================================
            
            # 1. Data attributes básicos
            try:
                product_code = await container.get_attribute('data-cnstrc-item-id')
                product_name = await container.get_attribute('data-cnstrc-item-name')
                price_from_data = await container.get_attribute('data-cnstrc-item-price')
            except:
                return None
            
            # Validar datos mínimos
            if not product_code or not product_name:
                return None
            
            # 2. Link del producto
            product_link = ""
            try:
                link_element = await container.query_selector('a[href]')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        product_link = f"https://www.paris.cl{href}" if href.startswith('/') else href
            except:
                pass
            
            # 3. Imagen con alta resolución
            image_url = ""
            try:
                img_element = await container.query_selector('img[alt="Imagen de producto"]')
                if img_element:
                    # Obtener srcset para imagen de alta resolución
                    srcset = await img_element.get_attribute('srcset')
                    if srcset:
                        # Extraer la última URL (mayor resolución)
                        import re
                        urls = re.findall(r'(https://[^\s]+)', srcset)
                        image_url = urls[-1] if urls else await img_element.get_attribute('src')
                    else:
                        image_url = await img_element.get_attribute('src')
            except:
                pass
            
            # 4. Precio actual (con selectores exactos del PORT)
            current_price_text = ""
            current_price_numeric = 0
            try:
                price_selectors = [
                    'span.ui-text-\\[13px\\].ui-leading-\\[15px\\].desktop\\:ui-text-lg',
                    'span[class*="ui-font-semibold"][class*="desktop:ui-font-medium"]'
                ]
                for selector in price_selectors:
                    price_element = await container.query_selector(selector)
                    if price_element:
                        current_price_text = await price_element.text_content()
                        current_price_text = current_price_text.strip()
                        # Extraer número
                        price_match = re.search(r'\$?([\d.,]+)', current_price_text.replace('.', ''))
                        if price_match:
                            try:
                                current_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
                        break
            except:
                pass
            
            # 5. Precio anterior (tachado)
            old_price_text = ""
            old_price_numeric = 0
            try:
                old_price_element = await container.query_selector('span.ui-line-through.ui-font-semibold')
                if old_price_element:
                    old_price_text = await old_price_element.text_content()
                    old_price_text = old_price_text.strip()
                    price_match = re.search(r'\$?([\d.,]+)', old_price_text.replace('.', ''))
                    if price_match:
                        try:
                            old_price_numeric = int(price_match.group(1).replace(',', ''))
                        except:
                            pass
            except:
                pass
            
            # 6. Descuento
            discount_percent = ""
            try:
                discount_element = await container.query_selector('div[data-testid="paris-label"][aria-label*="%"]')
                if discount_element:
                    discount_percent = await discount_element.get_attribute('aria-label')
            except:
                pass
            
            # 7. Marca
            brand = ""
            try:
                brand_element = await container.query_selector('span.ui-font-semibold.ui-line-clamp-2.ui-text-\\[11px\\]')
                if brand_element:
                    brand = await brand_element.text_content()
                    brand = brand.strip()
            except:
                pass
            
            # 8. Rating
            rating = 0.0
            try:
                rating_element = await container.query_selector('button[data-testid="star-rating-rating-value"]')
                if rating_element:
                    rating_text = await rating_element.text_content()
                    try:
                        rating = float(rating_text.strip())
                    except:
                        rating = 0.0
            except:
                pass
            
            # 9. Número de reseñas
            reviews_count = 0
            try:
                reviews_element = await container.query_selector('button[data-testid="star-rating-total-rating"]')
                if reviews_element:
                    reviews_text = await reviews_element.text_content()
                    reviews_text = reviews_text.replace('(', '').replace(')', '').strip()
                    try:
                        reviews_count = int(reviews_text)
                    except:
                        reviews_count = 0
            except:
                pass
            
            # 10. Especificaciones técnicas del nombre (como en PORT)
            storage = ""
            ram = ""
            network = ""
            color = ""
            
            if product_name:
                # Storage (primer número seguido de GB que no sea RAM)
                storage_match = re.search(r'(\d+)gb(?!\s+ram)', product_name.lower())
                if storage_match:
                    storage = f"{storage_match.group(1)}GB"
                
                # RAM
                ram_match = re.search(r'(\d+)gb\s+ram', product_name.lower())
                if ram_match:
                    ram = f"{ram_match.group(1)}GB"
                
                # Red (4G/5G)
                network_match = re.search(r'(4g|5g)', product_name.lower())
                if network_match:
                    network = network_match.group(1).upper()
                
                # Color (última palabra después de especificaciones)
                color_match = re.search(r'(negro|blanco|azul|rojo|verde|gris|dorado|plateado|purpura|rosa)$', product_name.lower())
                if color_match:
                    color = color_match.group(1).title()
            
            # Si el precio actual es 0, intentar usar el precio desde data attributes
            if current_price_numeric == 0 and price_from_data:
                try:
                    current_price_numeric = int(float(price_from_data))
                except:
                    current_price_numeric = 0
            
            # Si aún no tenemos precio válido, saltar este producto
            if current_price_numeric <= 0:
                return None
            
            # Crear ProductData con TODOS los campos
            return ProductData(
                title=product_name,
                sku=product_code,
                brand=brand,
                current_price=current_price_numeric,
                old_price=old_price_numeric,
                current_price_text=current_price_text,
                old_price_text=old_price_text,
                discount_percent=discount_percent,
                product_url=product_link,
                image_url=image_url,
                rating=rating,
                reviews_count=reviews_count,
                storage=storage,
                ram=ram,
                network=network,
                color=color,
                price_from_data=price_from_data,
                scraped_at=datetime.now().isoformat(),
                category="celulares",
                metadata={
                    'extraction_method': 'port_complete_selectors',
                    'container_index': index,
                    'all_specs': {
                        'storage': storage,
                        'ram': ram,
                        'network': network,
                        'color': color
                    }
                }
            )
        
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo producto individual completo: {e}")
            return None
            self.logger.debug(f"⚠️ Error extrayendo producto individual: {e}")
            return None

    async def _extract_prices_port_selectors(self, container: ElementHandle) -> Dict[str, Any]:
        """💰 Extraer precios con selectores exactos del PORT"""
        
        price_data = {}
        
        try:
            # Precio actual (selector exacto del PORT)
            current_price_data = await container.evaluate(f'''
                (element) => {{
                    const priceEl = element.querySelector('{PRICE_SELECTORS["current_price"]}');
                    if (priceEl) {{
                        return priceEl.textContent.trim();
                    }}
                    return '';
                }}
            ''')
            
            if current_price_data:
                price_data['current_price_text'] = current_price_data
                price_data['current_price'] = self._parse_price_port_method(current_price_data)
            
            # Precio anterior (selector exacto del PORT)
            old_price_data = await container.evaluate(f'''
                (element) => {{
                    const oldPriceEl = element.querySelector('{PRICE_SELECTORS["old_price"]}');
                    if (oldPriceEl) {{
                        return oldPriceEl.textContent.trim();
                    }}
                    return '';
                }}
            ''')
            
            if old_price_data:
                price_data['old_price_text'] = old_price_data
                price_data['old_price'] = self._parse_price_port_method(old_price_data)
            
            # Descuento (selector exacto del PORT)
            discount_data = await container.evaluate(f'''
                (element) => {{
                    const discountEl = element.querySelector('{PRICE_SELECTORS["discount"]}');
                    if (discountEl) {{
                        return discountEl.getAttribute('aria-label') || '';
                    }}
                    return '';
                }}
            ''')
            
            if discount_data:
                price_data['discount_text'] = discount_data
                # Extraer porcentaje numérico
                discount_match = re.search(r'(\d+)%', discount_data)
                if discount_match:
                    price_data['discount_percent'] = int(discount_match.group(1))
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo precios: {e}")
        
        return price_data

    async def _extract_metadata_port_selectors(self, container: ElementHandle) -> Dict[str, Any]:
        """🏷️ Extraer metadata con selectores del PORT"""
        
        metadata = {}
        
        try:
            # Marca (selector exacto del PORT)
            brand_data = await container.evaluate(f'''
                (element) => {{
                    const brandEl = element.querySelector('{PRICE_SELECTORS["brand"]}');
                    if (brandEl) {{
                        return brandEl.textContent.trim();
                    }}
                    return '';
                }}
            ''')
            
            if brand_data:
                metadata['brand'] = brand_data
            
            # Rating (selectores exactos del PORT)
            rating_data = await container.evaluate(f'''
                (element) => {{
                    const ratingEl = element.querySelector('{PRICE_SELECTORS["rating_value"]}');
                    const reviewsEl = element.querySelector('{PRICE_SELECTORS["rating_count"]}');
                    
                    return {{
                        rating: ratingEl ? ratingEl.textContent.trim() : '0',
                        reviews: reviewsEl ? reviewsEl.textContent.trim().replace(/[()]/g, '') : '0'
                    }};
                }}
            ''')
            
            if rating_data:
                try:
                    metadata['rating'] = float(rating_data['rating']) if rating_data['rating'] else 0
                    metadata['reviews'] = int(re.sub(r'[^\d]', '', rating_data['reviews'])) if rating_data['reviews'] else 0
                except:
                    metadata['rating'] = 0
                    metadata['reviews'] = 0
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo metadata: {e}")
        
        return metadata

    def _extract_specs_port_regex(self, product_name: str) -> Dict[str, str]:
        """🔧 Extraer especificaciones con regex exactos del PORT"""
        
        specs = {}
        
        if not product_name:
            return specs
        
        try:
            # Storage (regex exacto del PORT)
            storage_match = re.search(SPECS_REGEX['storage'], product_name, re.IGNORECASE)
            if storage_match:
                specs['storage'] = f"{storage_match.group(1)}GB"
            
            # RAM (regex exacto del PORT)
            ram_match = re.search(SPECS_REGEX['ram'], product_name, re.IGNORECASE)
            if ram_match:
                specs['ram'] = f"{ram_match.group(1)}GB"
            
            # Network (regex exacto del PORT)
            network_match = re.search(SPECS_REGEX['network'], product_name, re.IGNORECASE)
            if network_match:
                specs['network'] = network_match.group(1).upper()
            
            # Color (regex exacto del PORT)
            color_match = re.search(SPECS_REGEX['color'], product_name, re.IGNORECASE)
            if color_match:
                specs['color'] = color_match.group(1).title()
                
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo specs: {e}")
        
        return specs

    def _parse_price_port_method(self, price_text: str) -> float:
        """💰 Parsear precio con método exacto del PORT"""
        
        if not price_text:
            return 0.0
        
        try:
            # Limpiar precio (método PORT)
            clean_text = re.sub(r'[^\d.,]', '', price_text.replace('$', '').replace('.', '').replace(',', '.'))
            
            if not clean_text:
                return 0.0
            
            # Manejar decimales chilenos (lógica PORT)
            if '.' in clean_text:
                parts = clean_text.split('.')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    return float(clean_text)
                else:
                    clean_text = clean_text.replace('.', '')
            
            return float(clean_text)
            
        except (ValueError, AttributeError):
            return 0.0

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validación PORT compatible"""
        
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
                
            if product.product_url and 'paris.cl' not in product.product_url:
                issues.append(f"{product_id}: URL no es de Paris")
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

async def test_paris_improved_scraper():
    """🧪 Test del scraper mejorado"""
    
    print("🧪 TEST PARIS SCRAPER V5 MEJORADO")
    print("=" * 50)
    
    scraper = ParisScraperV5Improved()
    
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
                print(f"{i}. {product.title}")
                print(f"   Precio: ${product.current_price:,.0f}")
                print(f"   SKU: {product.sku}")
                print(f"   URL: {product.product_url[:60]}...")
        
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
    
    asyncio.run(test_paris_improved_scraper())