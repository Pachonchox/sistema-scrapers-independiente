# -*- coding: utf-8 -*-
"""
🏪 Falabella Chile Scraper v5 - Adaptado del Sistema v3 Original
===============================================================

Scraper para Falabella Chile adaptado del FalabellaScraperV3 original.
Mantiene exactamente los selectores y lógica del sistema v3.

Características v3 preservadas:
- Selectores exactos del falabella_final.py funcional
- Sistema de modales y cierre automático
- Scroll progresivo para lazy loading
- Procesamiento por lotes de productos
- Element handles para extracción robusta

Integraciones v5 mínimas:
- Compatibilidad con BaseScraperV5
- ProductData format
- ML failure detection integration

Autor: Sistema Scraper v5 🚀 (Adaptado del FalabellaScraperV3)
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

# Patterns exactos del v3 (de falabella_final.py)
SKU_PATH_RE = re.compile(r'/product/(\d+)')
SKU_FALLBACK_RE = re.compile(r'(\d{7,})')
PRICE_RE = re.compile(r'\$\s*([\d.,]+)')
WHITESPACE_RE = re.compile(r'\s+')

# Selectores VERIFICADOS que funcionan (probados con portable scraper)
CARD_SELECTORS = {
    'primary': 'a[data-key]',  # SELECTOR QUE FUNCIONA - encuentra productos
    'fallback': 'div[class*="search-results"][class*="grid-pod"]',  # Contenedores alternativos
    'tertiary': '[class*="pod"]'  # Elementos pod genéricos
}

class FalabellaScraperV5(BaseScraperV5):
    """🏪 Scraper Falabella v5 - Lógica v3 completa preservada"""
    
    def __init__(self):
        super().__init__("falabella")
        
        # URLs exactas del v3
        self.base_urls = {
            'home': 'https://www.falabella.com/falabella-cl',
            'search': 'https://www.falabella.com/falabella-cl/search'
        }
        
        # Configuración específica de Falabella (del v3)
        self.falabella_config = {
            'page_timeout': 45000,
            'modal_wait_time': 1500,
            'page_wait_time': 1000,
            'batch_size': 10,
            'scroll_steps': 3,
            'element_wait_timeout': 5000
        }
        
        # Mapeo de categorías del v3 original
        self.category_mapping = {
            'smartphones': 'https://www.falabella.com/falabella-cl/category/cat720161/Smartphones',
            'computadores': 'https://www.falabella.com/falabella-cl/category/cat40052/Computadores',
            'smart_tv': 'https://www.falabella.com/falabella-cl/category/cat7190148/Smart-TV',
            'smartwatch': 'https://www.falabella.com/falabella-cl/category/cat4290063/SmartWatch',
            'tablets': 'https://www.falabella.com/falabella-cl/category/cat7230007/Tablets',
            'consolas': 'https://www.falabella.com/falabella-cl/category/cat202303/Consolas',
            'parlantes_bluetooth': 'https://www.falabella.com/falabella-cl/category/cat3171/Parlantes-bluetooth',
            'monitores': 'https://www.falabella.com/falabella-cl/category/cat2062/Monitores',
            'accesorios_celulares': 'https://www.falabella.com/falabella-cl/category/cat70014/Accesorios-Celulares',
            'almacenamiento': 'https://www.falabella.com/falabella-cl/category/cat2003/Almacenamiento',
            'routers': 'https://www.falabella.com/falabella-cl/category/cat2082/Routers'
        }
        
        self.logger.info("🏪 Falabella Scraper v5 inicializado (lógica v3 completa)")

    async def scrape_category(
        self, 
        category: str,
        max_products: int = 100,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper categoría con lógica exacta del v3"""
        
        start_time = datetime.now()
        session_id = f"falabella_v5_{category}_{int(start_time.timestamp())}"
        
        try:
            # Obtener URL de categoría del mapeo v3
            category_url = self._get_category_url_v3(category)
            
            self.logger.info(f"🔍 Scraping Falabella categoría {category}: {category_url}")
            
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
                    'scraping_method': 'v3_adapted_falabella',
                    'modal_handling': True,
                    'progressive_scroll': True,
                    'batch_processing': True
                }
            )
            
            self.logger.info(f"✅ Falabella scraping completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error scraping Falabella categoría {category}: {e}")
            
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'v3_adapted_falabella'}
            )

    def _get_category_url_v3(self, category: str) -> str:
        """🔗 Obtener URL de categoría del mapeo v3 original"""
        
        url = self.category_mapping.get(category)
        if not url:
            raise ValueError(f"Categoría no soportada para Falabella: {category}")
        
        return url

    def _build_page_url_v3(self, base_url: str, page_num: int) -> str:
        """🔗 Construir URL con paginación (lógica exacta del v3)"""
        
        if page_num <= 1:
            return base_url
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"

    async def _scrape_category_v3_logic(self, page: Page, base_url: str, max_products: int) -> List[ProductData]:
        """📦 Scraping usando lógica exacta del FalabellaScraperV3"""
        
        all_products = []
        page_num = 1
        
        while len(all_products) < max_products:
            try:
                # Construir URL de página (v3)
                page_url = self._build_page_url_v3(base_url, page_num)
                
                self.logger.info(f"📄 Scraping Falabella página {page_num}: {page_url[:80]}...")
                
                # Navegar con domcontentloaded (exacto v3)
                await page.goto(page_url, wait_until='domcontentloaded', timeout=self.falabella_config['page_timeout'])
                
                # Cerrar modales (exacto v3)
                await self._dismiss_all_modals_v3(page)
                
                # Esperar después de cerrar modales (exacto v3)
                wait_time = self.falabella_config['modal_wait_time'] if page_num == 1 else self.falabella_config['page_wait_time']
                await page.wait_for_timeout(wait_time)
                
                # Scroll progresivo para cargar contenido (exacto v3)
                await self._progressive_scroll_v3(page)
                
                # Extraer productos de la página (exacto v3)
                # Usar extracción con JavaScript como V3
                page_products = await self._extract_products_with_javascript(page)
                
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
        """🚫 Cerrar modales usando lógica exacta del v3"""
        
        try:
            # Desactivar animaciones (v3)
            await page.add_style_tag(content="""
                * { animation: none !important; transition: none !important; }
                html, body { scroll-behavior: auto !important; }
            """)
        except Exception:
            pass

        # Selectores exactos del v3
        selectors = [
            "button:has-text('Aceptar')",
            "button:has-text('ACEPTAR')",
            "button:has-text('Cerrar')",
            "button:has-text('No gracias')",
            "button:has-text('Más tarde')",
            "[data-testid='modal-close']",
            "button[aria-label*='Cerrar' i]",
        ]
        
        dismissed = 0
        for sel in selectors:
            try:
                loc = page.locator(sel)
                count = await loc.count()
                if count:
                    for i in range(min(count, 5)):
                        try:
                            el = loc.nth(i)
                            if await el.is_visible():
                                await el.click()
                                dismissed += 1
                        except Exception:
                            continue
            except Exception:
                continue

        if dismissed:
            await page.wait_for_timeout(300)
            self.logger.debug(f"🚫 Modales cerrados: {dismissed}")

    async def _progressive_scroll_v3(self, page: Page):
        """📜 Scroll progresivo exacto del v3"""
        
        try:
            # Scroll inicial para trigger lazy loading (v3)
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(300)
            
            # Scroll hasta el final progresivamente (v3)
            for i in range(self.falabella_config['scroll_steps']):
                await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3})")
                await page.wait_for_timeout(500)
            
            # Volver arriba (v3)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(200)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en scroll progresivo: {e}")

    async def _extract_products_with_javascript(self, page: Page) -> List[ProductData]:
        """Extraer productos con JavaScript como V3"""
        products_data = await page.evaluate('''() => {
            const cards = document.querySelectorAll('#testId-searchResults-products a.pod-link');
            const results = [];
            
            cards.forEach(card => {
                // Extraer marca y nombre - SELECTORES REALES V3
                const brandEl = card.querySelector('b[class*="pod-title"]');
                const titleEl = card.querySelector('b[class*="pod-subTitle"]');
                
                let brand = brandEl ? brandEl.textContent.trim() : '';
                let title = titleEl ? titleEl.textContent.trim() : '';
                let name = brand && title ? brand + ' ' + title : (brand || title);
                
                // Extraer precios - SELECTORES REALES V3
                let normalPrice = '';
                let offerPrice = '';
                
                const pricesOl = card.querySelector('ol.prices-0');
                if (pricesOl) {
                    const spans = pricesOl.querySelectorAll('span');
                    if (spans.length >= 2) {
                        normalPrice = spans[0].textContent.trim();
                        offerPrice = spans[1].textContent.trim();
                    } else if (spans.length === 1) {
                        offerPrice = spans[0].textContent.trim();
                    }
                }
                
                // Extraer link
                const href = card.getAttribute('href') || '';
                
                if (name && (normalPrice || offerPrice)) {
                    results.push({
                        nombre: name,
                        marca: brand,
                        precio_normal: normalPrice,
                        precio_oferta: offerPrice,
                        link: href
                    });
                }
            });
            
            return results;
        }''')
        
        # Convertir a ProductData
        products = []
        for data in products_data:
            try:
                product = ProductData(
                    title=data.get('nombre', ''),
                    brand=data.get('marca', ''),
                    current_price=self._parse_price(data.get('precio_oferta', '')),
                    original_price=self._parse_price(data.get('precio_normal', '')),
                    product_url=urljoin(self.base_urls['home'], data.get('link', '')),
                    retailer=self.retailer,
                    extraction_timestamp=datetime.now()
                )
                products.append(product)
            except Exception as e:
                self.logger.warning(f"Error convirtiendo producto: {e}")
                
        return products
    
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
                await cards_locator.first.wait_for(state='attached', timeout=self.falabella_config['element_wait_timeout'])
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
            batch_size = self.falabella_config['batch_size']
            
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
            self.logger.error(f"❌ Error extrayendo productos Falabella: {e}")
        
        return products

    async def _extract_product_from_handle_v3(self, handle: ElementHandle) -> Optional[ProductData]:
        """📋 Extraer producto usando element handle (método del portable scraper)"""
        
        try:
            # Extraer todo en una evaluación del DOM (USANDO MÉTODO DEL PORTABLE SCRAPER)
            data = await handle.evaluate('''
                (element) => {
                    // Si es un link con data-key, buscar el contenedor padre
                    const container = element.closest('div') || element.parentElement || element;
                    const href = element.getAttribute('href') || '';
                    
                    // Extraer nombre y marca (SELECTORES DEL PORTABLE SCRAPER)
                    let name = '';
                    let brand = '';
                    const brandEl = container.querySelector('b[class*="pod-title"]');
                    const titleEl = container.querySelector('b[class*="pod-subTitle"]');
                    
                    if (brandEl) brand = brandEl.textContent.trim();
                    if (titleEl) {
                        const titleText = titleEl.textContent.trim();
                        name = brand ? `${brand} ${titleText}`.trim() : titleText;
                    } else if (brandEl) {
                        name = brand;
                    } else {
                        const imgEl = element.querySelector('img[alt]');
                        if (imgEl) {
                            name = imgEl.getAttribute('alt') || '';
                        }
                    }
                    
                    if (!name) {
                        name = element.textContent || '';
                    }
                    
                    // Extraer vendedor/seller (SELECTOR DEL PORTABLE)
                    let seller = '';
                    const sellerEl = container.querySelector('b[class*="pod-sellerText"]');
                    if (sellerEl) {
                        seller = sellerEl.textContent.trim();
                    }
                    
                    // Extraer especificaciones técnicas
                    let storage = '';
                    let ram = '';
                    let color = '';
                    
                    // Buscar en atributos del producto o descripción
                    const specElements = container.querySelectorAll('.product-attributes .attribute-value, .spec-item .spec-value');
                    specElements.forEach(el => {
                        const text = el.textContent.toLowerCase();
                        if (text.includes('gb') && text.includes('almac')) {
                            storage = el.textContent.trim();
                        } else if (text.includes('gb') && text.includes('ram')) {
                            ram = el.textContent.trim();
                        } else if (text.includes('color')) {
                            color = el.textContent.replace(/color:?/i, '').trim();
                        }
                    });
                    
                    // Extraer del nombre si no se encontró en atributos
                    if (!storage) {
                        const storageMatch = name.match(/(\\d+)\\s*GB/i);
                        if (storageMatch) storage = storageMatch[0];
                    }
                    
                    // Extraer color del nombre si no se encontró
                    if (!color) {
                        const colorMatches = name.match(/(Negro|Blanco|Azul|Rojo|Verde|Rosa|Dorado|Plateado|Gris)/i);
                        if (colorMatches) color = colorMatches[0];
                    }
                    
                    // Extraer precios (SELECTORES REALES DE FALABELLA)
                    const prices = { normal: '', internet: '', cmr: '', cmr_numeric: null, internet_numeric: null };
                    
                    // Precio CMR (con tarjeta) - SELECTOR DEL PORTABLE
                    const cmrPriceEl = container.querySelector('li[data-cmr-price]');
                    if (cmrPriceEl) {
                        prices.cmr = cmrPriceEl.getAttribute('data-cmr-price') || '';
                    }
                    
                    // Precio internet (sin tarjeta) - SELECTOR DEL PORTABLE
                    const internetPriceEl = container.querySelector('li[data-internet-price]');
                    if (internetPriceEl) {
                        prices.internet = internetPriceEl.getAttribute('data-internet-price') || '';
                    }
                    
                    // Buscar precios en texto si no hay atributos
                    if (!prices.internet && !prices.cmr) {
                        const pricePattern = /\\$\\s*(\\d{1,3}(?:\\.\\d{3})+)/g;
                        const text = container.textContent || '';
                        const matches = text.match(pricePattern);
                        if (matches && matches.length > 0) {
                            prices.normal = matches[0];
                            if (matches.length > 1) {
                                prices.internet = matches[1];
                            }
                        }
                    }
                    
                    // Imagen
                    let image = '';
                    const imgEl = container.querySelector('img');
                    if (imgEl) {
                        image = imgEl.getAttribute('src') || imgEl.getAttribute('data-src') || '';
                    }
                    
                    // Extraer rating y reviews (SELECTORES REALES DE FALABELLA)
                    let rating = null;
                    let reviews_count = null;
                    
                    // Rating - SELECTOR DEL PORTABLE
                    const ratingEl = container.querySelector('div[data-rating]');
                    if (ratingEl) {
                        const ratingValue = ratingEl.getAttribute('data-rating');
                        if (ratingValue && ratingValue !== '0') {
                            rating = parseFloat(ratingValue);
                        }
                    }
                    
                    // Reviews count - SELECTOR DEL PORTABLE
                    const reviewsEl = container.querySelector('span[class*="reviewCount"]');
                    if (reviewsEl) {
                        const reviewsText = reviewsEl.textContent || '';
                        const reviewsMatch = reviewsText.match(/\\((\\d+)\\)/);
                        if (reviewsMatch) reviews_count = parseInt(reviewsMatch[1]);
                    }
                    
                    // Extraer sponsored status
                    let is_sponsored = false;
                    const sponsoredEl = container.querySelector('div[class*="patrocinado"]');
                    is_sponsored = !!sponsoredEl;
                    
                    // Extraer badges
                    const badges = [];
                    const badgeElements = container.querySelectorAll('span[class*="pod-badges-item"]');
                    badgeElements.forEach(badgeEl => {
                        const badgeText = badgeEl.textContent.trim();
                        if (badgeText && badges.length < 5) { // Limitar a 5 badges
                            badges.push(badgeText);
                        }
                    });
                    
                    // Extraer data-key como SKU alternativo
                    const dataKey = element.getAttribute('data-key') || '';
                    
                    return {
                        href: href,
                        dataKey: dataKey,
                        name: name.replace(/\\s+/g, ' ').trim(),
                        brand: brand,
                        seller: seller,
                        prices: prices,
                        specs: {
                            storage: storage,
                            ram: ram,
                            color: color
                        },
                        social: {
                            rating: rating,
                            reviews_count: reviews_count
                        },
                        marketing: {
                            is_sponsored: is_sponsored,
                            badges: badges
                        },
                        image: image
                    };
                }
            ''')
            
            # Procesar datos (igual que falabella_final)
            
            # URL
            url = ''
            sku = ''
            if data['href']:
                canon = self._canonical_url(data['href'])
                url = urljoin('https://www.falabella.com', canon)
                
                # Extraer SKU
                sku_match = SKU_PATH_RE.search(canon)
                if sku_match:
                    sku = sku_match.group(1)
                else:
                    sku_fallback = SKU_FALLBACK_RE.search(canon)
                    if sku_fallback:
                        sku = sku_fallback.group(1)
            
            # Nombre y marca
            nombre = data['name']
            marca = data['brand'] if data['brand'] else ''
            
            # Si no hay marca, extraer de nombre
            if not marca:
                parts = data['name'].split(' - ', 1)
                if len(parts) == 2:
                    marca = parts[0].strip()
            
            # Procesar precios (lógica V3)
            p_normal = data['prices']['normal'] or ""
            p_internet = data['prices']['internet'] or ""
            p_cmr = data['prices']['cmr'] or ""
            
            # Fallback de precios (igual que falabella_final)
            if not p_internet and p_normal:
                p_internet = p_normal
            if not p_normal and (p_internet or p_cmr):
                p_normal = p_internet or p_cmr
            
            p_plp = p_internet or p_cmr or p_normal
            
            # SKU por defecto si no existe - usar data-key si está disponible
            if not sku:
                if data.get('dataKey'):
                    sku = data['dataKey']
                elif nombre:
                    sku = f"FAL_{abs(hash(nombre))}"
            
            if not sku:
                return None
                
            # Convertir precios a números
            normal_num = self._to_int_clp(p_normal)
            internet_num = self._to_int_clp(p_internet)
            cmr_num = self._to_int_clp(p_cmr)
            plp_num = self._to_int_clp(p_plp)
            
            # Usar el precio más bajo disponible
            current_price = min(filter(lambda x: x > 0, [internet_num, cmr_num, normal_num]), default=0)
            original_price = normal_num if normal_num > current_price else current_price
            
            # Calcular descuento
            discount_percentage = 0
            if original_price > current_price > 0:
                discount_percentage = int(((original_price - current_price) / original_price) * 100)
            
            # Procesar imagen
            image_url = ""
            if data.get('image'):
                image_url = urljoin('https://www.falabella.com', data['image']) if not data['image'].startswith('http') else data['image']
            
            # Crear ProductData (formato v5 con CAMPOS ENRIQUECIDOS V3)
            product = ProductData(
                title=nombre,
                current_price=float(current_price),
                original_price=float(original_price),
                discount_percentage=discount_percentage,
                currency="CLP",
                availability="in_stock",
                product_url=url,
                image_urls=[image_url] if image_url else [],
                brand=marca,
                sku=sku,
                rating=data['social']['rating'] if data['social']['rating'] else 0.0,
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info={
                    'extraction_method': 'v3_dom_evaluation_full',
                    'seller': data['seller'],
                    'storage': data['specs']['storage'],
                    'ram': data['specs']['ram'],
                    'color': data['specs']['color'],
                    'reviews_count': data['social']['reviews_count'],
                    'is_sponsored': data['marketing']['is_sponsored'],
                    'badges': data['marketing']['badges'],
                    'cmr_price': p_cmr,
                    'internet_price': p_internet,
                    'precio_normal': p_normal,
                    'precio_internet': p_internet,
                    'precio_cmr': p_cmr
                }
            )
            
            return product
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo producto de handle: {e}")
            return None

    def _canonical_url(self, url):
        """Canonicalizar URL evitando prefijos duplicados (EXACTO V3)"""
        if not url:
            return ""
        url = url.split('?')[0].split('#')[0]
        try:
            if url.startswith('http://') or url.startswith('https://'):
                from urllib.parse import urlsplit
                parts = urlsplit(url)
                path = parts.path or '/'
                if not path.startswith('/'):
                    path = '/' + path
                return path
        except Exception:
            pass
        if url.startswith('/'):
            return url
        return '/' + url
    
    def _to_int_clp(self, price_str):
        """Convertir precio chileno a entero con manejo robusto (EXACTO V3)"""
        if not price_str:
            return 0
        
        try:
            original_price = str(price_str)
            
            # Detectar formato malformado como "181.500,258.500" 
            if ',' in price_str:
                comma_parts = str(price_str).split(',')
                if len(comma_parts) > 2 or (len(comma_parts) == 2 and len(comma_parts[1]) > 3):
                    # Tomar solo la primera parte antes del patrón extraño
                    price_str = comma_parts[0]
            
            # Formato chileno estándar: $123.456 (puntos para miles)
            # Remover $ y espacios primero
            cleaned = re.sub(r'[\$\s]', '', str(price_str))
            
            # Contar puntos para determinar si son separadores de miles o decimales
            dot_count = cleaned.count('.')
            if dot_count > 1:
                # Múltiples puntos = separadores de miles chilenos: 123.456.789
                cleaned = cleaned.replace('.', '')
            elif dot_count == 1:
                # Un punto: podría ser separador de miles o decimal
                parts = cleaned.split('.')
                if len(parts) == 2 and len(parts[1]) == 3:
                    # 3 dígitos después del punto = separador de miles: 123.456
                    cleaned = cleaned.replace('.', '')
                # Si son 1-2 dígitos, asumir decimal y mantener (pero luego lo eliminamos)
            
            # Remover todos los caracteres no numéricos finales
            cleaned = re.sub(r'[^\d]', '', cleaned)
            
            result = int(cleaned) if cleaned else 0
            
            # Validar que el precio sea razonable (menos de 100 millones de pesos)
            if result > 100000000:
                # Si es demasiado alto, probablemente hay error de parsing
                # Intentar dividir por potencias de 10 hasta encontrar algo razonable
                adjusted = result
                while adjusted > 50000000 and adjusted > 100:
                    adjusted = adjusted // 10
                result = adjusted
            
            return result
            
        except Exception as e:
            return 0
    
    def _parse_price_v3(self, price_text: str) -> float:
        """💰 Parsear precio con lógica exacta del v3"""
        return float(self._to_int_clp(price_text))

    async def search_products(
        self,
        query: str,
        max_products: int = 50,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔎 Búsqueda usando lógica v3"""
        
        start_time = datetime.now()
        session_id = f"falabella_search_v5_{query[:20]}_{int(start_time.timestamp())}"
        
        try:
            # URL de búsqueda
            search_url = f"{self.base_urls['search']}?q={query}"
            
            self.logger.info(f"🔎 Búsqueda Falabella: '{query}' - {search_url}")
            
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
            
            self.logger.info(f"✅ Búsqueda Falabella completada: {len(products)} productos para '{query}'")
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
            if product.product_url and 'falabella.com' not in product.product_url:
                issues.append(f"{product_id}: URL no es de Falabella")
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
            'link': 'https://www.falabella.com.cl/product/123456789',
            'nombre': 'MacBook Air M2 13 pulgadas 8GB RAM 256GB SSD Space Gray',
            'sku': 'MKFAL123456',
            'precio_normal': '$1.299.990',
            'precio_oferta': '$1.099.990',
            'precio_tarjeta': 'CMR $999.990',
            'precio_normal_num': 1299990,
            'precio_oferta_num': 1099990,
            'precio_tarjeta_num': 999990,
            'precio_min_num': 999990,
            'tipo_precio_min': 'tarjeta',
            'retailer': 'falabella',
            'category': category,
            'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Campos opcionales
            'marca': 'Apple',
            'imagen': 'https://falabella.scene7.com/test.jpg',
            'disponibilidad': 'available',
            'rating': 4.8,
            'reviews': 245
        }
        
        products.append(test_product)
        return products