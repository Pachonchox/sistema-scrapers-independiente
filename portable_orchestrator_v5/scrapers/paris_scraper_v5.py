# -*- coding: utf-8 -*-
"""
🏬 Paris Chile Scraper v5 - Adaptado del Sistema v3 Original
===========================================================

Scraper para Paris Chile adaptado del ParisScraperV3 original.
Mantiene exactamente los selectores y lógica del sistema v3.

Características v3 preservadas:
- Selectores exactos del paris_final.py funcional
- Timeouts específicos de Paris (60 segundos)
- Sistema de modales propio de Paris
- Scroll progresivo para lazy loading
- Procesamiento por lotes de productos
- Element handles para extracción robusta

Integraciones v5 mínimas:
- Compatibilidad con BaseScraperV5
- ProductData format
- ML failure detection integration

Autor: Sistema Scraper v5 🚀 (Adaptado del ParisScraperV3)
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

# Patterns exactos del v3 (de paris_final.py)
WHITESPACE_RE = re.compile(r'\s+')

# Selectores EXACTOS del v3 (de paris_final.py)  
CARD_SELECTORS = {
    'primary': "div[data-cnstrc-item-id]",
    'fallback': "[data-testid='paris-vertical-pod'], [data-testid='product-card']"
}

class ParisScraperV5(BaseScraperV5):
    """🏬 Scraper Paris v5 - Lógica v3 completa preservada"""
    
    def __init__(self):
        super().__init__("paris")
        
        # URLs exactas del v3
        self.base_urls = {
            'home': 'https://www.paris.cl',
            'search': 'https://www.paris.cl/search'
        }
        
        # Configuración específica de Paris (del v3)
        self.paris_config = {
            'page_timeout': 60000,  # 60 segundos como paris_final
            'after_load_first': 2000,  # Espera después de primera página
            'after_load': 800,  # Espera después de páginas siguientes  
            'batch_size': 10,
            'element_wait_timeout': 5000
        }
        
        # Mapeo de categorías del v3 original
        self.category_mapping = {
            'celulares': 'https://www.paris.cl/tecnologia/celulares/',
            'computadores': 'https://www.paris.cl/tecnologia/computadores/',
            'television': 'https://www.paris.cl/tecnologia/television/',
            'smartwatches': 'https://www.paris.cl/tecnologia/wearables/smartwatches/',
            'gaming': 'https://www.paris.cl/tecnologia/gaming/',
            'audio': 'https://www.paris.cl/tecnologia/audio/',
            'accesorios_celulares': 'https://www.paris.cl/tecnologia/accesorios-celulares/',
            'fotografia': 'https://www.paris.cl/tecnologia/fotografia/'
        }
        
        self.logger.info("🏬 Paris Scraper v5 inicializado (lógica v3 completa)")

    async def scrape_category(
        self, 
        category: str,
        max_products: int = 100,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper categoría con lógica exacta del v3"""
        
        start_time = datetime.now()
        session_id = f"paris_v5_{category}_{int(start_time.timestamp())}"
        
        try:
            # Obtener URL de categoría del mapeo v3
            category_url = self._get_category_url_v3(category)
            
            self.logger.info(f"🔍 Scraping Paris categoría {category}: {category_url}")
            
            # Configurar página
            page = await self.get_page()
            
            # Scraping usando lógica exacta del v3
            products = await self._scrape_category_v3_logic(page, category_url, max_products)
            
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
                    'scraping_method': 'v3_adapted_paris',
                    'modal_handling': True,
                    'progressive_scroll': True,
                    'batch_processing': True,
                    'timeout_60s': True
                }
            )
            
            self.logger.info(f"✅ Paris scraping completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error scraping Paris categoría {category}: {e}")
            
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'v3_adapted_paris'}
            )

    def _get_category_url_v3(self, category: str) -> str:
        """🔗 Obtener URL de categoría del mapeo v3 original"""
        
        url = self.category_mapping.get(category)
        if not url:
            raise ValueError(f"Categoría no soportada para Paris: {category}")
        
        return url

    def _build_page_url_v3(self, base_url: str, page_num: int) -> str:
        """🔗 Construir URL con paginación (lógica exacta del v3)"""
        
        if page_num <= 1:
            return base_url
        # Paris usa el parámetro 'page' en la query string
        if '?' in base_url:
            return f"{base_url}&page={page_num}"
        return f"{base_url}?page={page_num}"

    async def _scrape_category_v3_logic(self, page: Page, base_url: str, max_products: int) -> List[ProductData]:
        """📦 Scraping usando lógica exacta del ParisScraperV3"""
        
        all_products = []
        page_num = 1
        
        while len(all_products) < max_products:
            try:
                # Construir URL de página (v3)
                page_url = self._build_page_url_v3(base_url, page_num)
                
                self.logger.info(f"📄 Scraping Paris página {page_num}: {page_url[:80]}...")
                
                # Navegar con timeouts de paris_final (60 segundos)
                await page.goto(page_url, wait_until='domcontentloaded', timeout=self.paris_config['page_timeout'])
                
                # Cerrar modales (exacto v3)
                await self._dismiss_all_modals_v3(page)
                
                # Esperar después de cerrar modales (timeouts exactos del v3)
                wait_time = self.paris_config['after_load_first'] if page_num == 1 else self.paris_config['after_load']
                await page.wait_for_timeout(wait_time)
                
                # Scroll progresivo específico para Paris (exacto v3)
                await self._progressive_scroll_v3(page)
                
                # Extraer productos de la página (exacto v3)
                page_products = await self._extract_products_v3_logic(page, page_num)
                
                if not page_products:
                    self.logger.info(f"❌ No hay más productos en página {page_num}")
                    break
                
                self.logger.info(f"✅ Extraídos {len(page_products)} productos de página {page_num}")
                
                all_products.extend(page_products)
                page_num += 1
                
                # Pausa entre páginas
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error en página {page_num}: {e}")
                break
        
        # Limitar a max_products solicitados
        return all_products[:max_products]

    async def _dismiss_all_modals_v3(self, page: Page):
        """🚫 Cerrar modales usando lógica exacta del v3 (paris_final)"""
        
        try:
            # Agregar CSS para desactivar animaciones (exacto v3)
            await page.add_style_tag(content="""
                * { animation: none !important; transition: none !important; }
                html, body { scroll-behavior: auto !important; }
            """)
        except:
            pass
        
        # Lista de selectores exacta de paris_final
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
                    try:
                        if await el.is_visible():
                            await el.click()
                            dismissed += 1
                            await page.wait_for_timeout(200)
                    except:
                        continue
            except:
                continue
        
        if dismissed > 0:
            await page.wait_for_timeout(500)
            self.logger.debug(f"🚫 Modales cerrados: {dismissed}")
        
        # Scroll anti-trampa (Paris lo necesita)
        await page.evaluate("window.scrollBy(0, 300); setTimeout(() => window.scrollTo(0, 0), 200);")

    async def _progressive_scroll_v3(self, page: Page):
        """📜 Scroll progresivo EXACTO de paris_final (específico para Paris)"""
        
        try:
            # Obtener altura inicial (igual que paris_final)
            initial_height = await page.evaluate("document.body.scrollHeight")
            
            # Scroll progresivo (exacto de paris_final - 5 iteraciones)
            for i in range(5):
                await page.evaluate(f"window.scrollTo(0, {(i+1) * 1000})")
                new_height = await page.evaluate("document.body.scrollHeight")
                
                if new_height == initial_height and i > 2:
                    # No hay más contenido para cargar
                    await page.wait_for_timeout(100)
                else:
                    # scroll_step delay de paris_final = 300ms
                    await page.wait_for_timeout(300)
                    initial_height = new_height
            
            # Volver arriba (igual que paris_final)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(200)
        except Exception as e:
            self.logger.warning(f"⚠️ Error en scroll: {e}")

    async def _extract_products_v3_logic(self, page: Page, page_num: int) -> List[ProductData]:
        """📦 Extraer productos con lógica exacta del v3"""
        
        products = []
        
        try:
            # Buscar selector de productos que funcione (exacto v3)
            card_selector = None
            for sel_type, selector in CARD_SELECTORS.items():
                count = await page.locator(selector).count()
                if count > 0:
                    card_selector = selector
                    self.logger.debug(f"🔍 Selector {sel_type}: {count} elementos")
                    break
            
            if not card_selector:
                self.logger.warning(f"❌ No se encontraron productos en página {page_num}")
                return products
            
            # Esperar primer elemento (exacto v3)
            cards_locator = page.locator(card_selector)
            try:
                await cards_locator.first.wait_for(state='attached', timeout=self.paris_config['element_wait_timeout'])
            except:
                self.logger.warning(f"⏰ Timeout esperando productos en página {page_num}")
                return products
            
            # Obtener element handles (exacto v3)
            card_handles = await cards_locator.element_handles()
            total_cards = len(card_handles)
            self.logger.info(f"🔍 Encontradas {total_cards} tarjetas de producto")
            
            if total_cards == 0:
                return products
            
            # Procesar por lotes (exacto v3)
            successful = 0
            batch_size = self.paris_config['batch_size']
            
            for batch_start in range(0, total_cards, batch_size):
                batch_end = min(batch_start + batch_size, total_cards)
                batch = card_handles[batch_start:batch_end]
                
                for handle in batch:
                    try:
                        product = await self._extract_product_from_handle_v3(handle)
                        if product:
                            products.append(product)
                            successful += 1
                    except asyncio.TimeoutError:
                        self.logger.warning(f"⏰ Timeout extrayendo producto {batch_start}")
                    except Exception as e:
                        self.logger.debug(f"⚠️ Error extrayendo producto: {e}")
                
                # Limpiar handles (v3)
                for handle in batch:
                    try:
                        await handle.dispose()
                    except:
                        pass
                
                # Delay entre lotes (v3)
                if batch_end < total_cards:
                    await page.wait_for_timeout(200)
            
            self.logger.info(f"📄 Página {page_num}: {successful} productos extraídos de {total_cards}")
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo productos Paris: {e}")
        
        return products

    async def _extract_product_from_handle_v3(self, handle: ElementHandle) -> Optional[ProductData]:
        """📋 Extraer producto usando element handle con data attributes (método simplificado V3)"""
        
        try:
            # Extraer datos usando principalmente data attributes (más confiables) - EXACTO DE V3
            data = await handle.evaluate('''
                (element) => {
                    const result = {
                        sku: element.getAttribute('data-cnstrc-item-id') || '',
                        title: element.getAttribute('data-cnstrc-item-name') || '',
                        price_data: element.getAttribute('data-cnstrc-item-price') || '',
                        url: '',
                        brand: '',
                        display_price: ''
                    };
                    
                    // Buscar link del producto
                    const linkEl = element.querySelector('a[href]');
                    if (linkEl) {
                        const href = linkEl.getAttribute('href') || '';
                        result.url = href.startsWith('/') ? 'https://www.paris.cl' + href : href;
                    }
                    
                    // Extraer marca de spans (método simple)
                    const spans = element.querySelectorAll('span');
                    for (const span of spans) {
                        const text = span.textContent.trim();
                        if (text && text.length < 50 && !text.includes('$') && !text.includes('%') && text !== 'Vista Previa') {
                            result.brand = text;
                            break;
                        }
                    }
                    
                    // Precio visible (fallback)
                    const priceEl = element.querySelector('span[class*="font"]');
                    if (priceEl) {
                        result.display_price = priceEl.textContent.trim();
                    }
                    
                    return result;
                }
            ''')
            
            # Validar datos mínimos (EXACTO V3)
            if not data.get('sku') or not data.get('title'):
                return None
            
            # Procesar precio numérico (EXACTO V3)
            price_num = 0
            if data.get('price_data'):
                try:
                    price_num = int(float(data['price_data']))
                except:
                    pass
            
            # Si no hay precio de data attribute, intentar parsear el display price
            if price_num == 0 and data.get('display_price'):
                price_num = self._parse_price_v3(data['display_price'])
            
            # Extraer especificaciones del título (EXACTO V3)
            title = data.get('title', '')
            storage = ''
            ram = ''
            
            storage_match = re.search(r'(\d+)GB(?!\s+RAM)', title, re.IGNORECASE)
            if storage_match:
                storage = storage_match.group(1) + 'GB'
            
            ram_match = re.search(r'(\d+)GB\s+RAM', title, re.IGNORECASE)
            if ram_match:
                ram = ram_match.group(1) + 'GB'
            
            # Crear ProductData (formato v5 con datos V3)
            product = ProductData(
                title=WHITESPACE_RE.sub(' ', title).strip(),
                current_price=float(price_num) if price_num else 0.0,
                original_price=float(price_num) if price_num else 0.0,  # V3 no diferencia precios
                discount_percentage=0,  # V3 no calcula descuento en este método
                currency="CLP",
                availability="in_stock",  # Paris no muestra sin stock
                product_url=data.get('url', ''),
                image_urls=[],  # V3 no extrae imágenes en este método simplificado
                brand=data.get('brand', '').strip(),
                sku=data['sku'],
                rating=0.0,  # V3 no extrae rating en este método
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info={
                    'extraction_method': 'v3_data_attributes',
                    'display_price': data.get('display_price', ''),
                    'price_data_attribute': data.get('price_data', ''),
                    'storage': storage,
                    'ram': ram
                }
            )
            
            return product
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo producto de handle: {e}")
            return None

    def _parse_price_v3(self, price_text: str) -> float:
        """💰 Parsear precio con lógica exacta del v3"""
        
        if not price_text:
            return 0.0
        
        try:
            # Limpiar texto de precio (lógica v3)
            clean_text = re.sub(r'[^\d.,]', '', price_text.replace('$', '').replace('.', '').replace(',', '.'))
            
            if not clean_text:
                return 0.0
            
            # Manejar decimales chilenos
            if '.' in clean_text:
                parts = clean_text.split('.')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Es decimal
                    return float(clean_text)
                else:
                    # Son separadores de miles
                    clean_text = clean_text.replace('.', '')
            
            return float(clean_text)
            
        except (ValueError, AttributeError):
            return 0.0

    async def search_products(
        self,
        query: str,
        max_products: int = 50,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔎 Búsqueda usando lógica v3"""
        
        start_time = datetime.now()
        session_id = f"paris_search_v5_{query[:20]}_{int(start_time.timestamp())}"
        
        try:
            # URL de búsqueda
            search_url = f"{self.base_urls['search']}?q={query}"
            
            self.logger.info(f"🔎 Búsqueda Paris: '{query}' - {search_url}")
            
            # Usar misma lógica que categoría
            page = await self.get_page()
            products = await self._scrape_category_v3_logic(page, search_url, max_products)
            
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
                    'scraping_method': 'v3_adapted_search'
                }
            )
            
            self.logger.info(f"✅ Búsqueda Paris completada: {len(products)} productos para '{query}'")
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

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validación usando criterios v3 + mejoras v5"""
        
        issues = []
        
        if not products:
            issues.append("No se extrajeron productos")
            return False, issues
        
        # Validaciones v3 mantenidas
        valid_products = 0
        for i, product in enumerate(products):
            product_id = f"Producto {i+1}"
            
            # Validar título (v3)
            if not product.title or len(product.title) < 3:
                issues.append(f"{product_id}: Título inválido")
                continue
            
            # Validar precio (v3)
            if product.current_price <= 0:
                issues.append(f"{product_id}: Precio inválido")
                continue
                
            # Validar URL (v3)
            if product.product_url and 'paris.cl' not in product.product_url:
                issues.append(f"{product_id}: URL no es de Paris")
                continue
            
            valid_products += 1
        
        # Criterio v3: al menos 70% de productos válidos
        success_rate = valid_products / len(products)
        if success_rate < 0.7:
            issues.append(f"Baja tasa de éxito: {success_rate:.1%} (mínimo 70%)")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info(f"✅ Validación exitosa: {valid_products}/{len(products)} productos válidos")
        else:
            self.logger.warning(f"⚠️ Validación con problemas: {len(issues)} issues")
        
        return is_valid, issues
    
    async def _process_test_products(self, page, category: str) -> List[Dict]:
        """🧪 Procesar productos para testing (sin navegación real)"""
        products = []
        
        # Simular producto de prueba con todos los campos requeridos del Excel original
        test_product = {
            'link': 'https://www.paris.cl/gaming-laptop-test.html',
            'nombre': 'Laptop Gamer ASUS ROG Strix 16GB RAM RTX 4060',
            'sku': 'PPARIS789012',
            'precio_normal': '$1.599.990',
            'precio_oferta': 'Internet $1.399.990',
            'precio_tarjeta': 'Tarjeta Cencosud $1.299.990',
            'precio_normal_num': 1599990,
            'precio_oferta_num': 1399990,
            'precio_tarjeta_num': 1299990,
            'precio_min_num': 1299990,
            'tipo_precio_min': 'tarjeta',
            'retailer': 'paris',
            'category': category,
            'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Campos opcionales
            'marca': 'ASUS',
            'imagen': 'https://imagenes.paris.cl/test.jpg',
            'disponibilidad': 'available',
            'rating': 4.7,
            'reviews': 89
        }
        
        products.append(test_product)
        return products