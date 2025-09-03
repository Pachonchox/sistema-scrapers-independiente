# -*- coding: utf-8 -*-
"""
🛍️ Ripley Chile Scraper v5 - Adaptado del Sistema v3 Original
============================================================

Scraper para Ripley Chile adaptado mínimamente del sistema v3 existente.
Mantiene la lógica de scraping original con integraciones v5 mínimas.

Características originales mantenidas:
- Scroll lento para simular usuario real (crítico para Ripley)
- Selectores exactos del sistema v3 
- Lógica de paginación específica de Ripley
- Navegador visible (requerido por Ripley)
- Construcción de URLs con parámetros específicos

Nuevas integraciones v5 (mínimas):
- Hereda de BaseScraperV5 para compatibilidad
- Integración con ML failure detection
- Soporte para tier system del v5

Autor: Sistema Scraper v5 🚀 (Adaptado del RipleyScraperV3 original)
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlsplit, parse_qsl, urlunsplit

from playwright.async_api import Page, Locator

from ..core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
from ..core.exceptions import *

logger = logging.getLogger(__name__)

class RipleyScraperV5(BaseScraperV5):
    """🛍️ Scraper Ripley v5 - Mantiene lógica v3 con mejoras mínimas"""
    
    def __init__(self):
        super().__init__("ripley")
        
        # URLs base exactas del v3
        self.base_urls = {
            'home': 'https://simple.ripley.cl',
            'search': 'https://simple.ripley.cl/search'
        }
        
        # Selectores REALES del sistema v3 que FUNCIONAN
        self.selectors = {
            'cards': {
                'primary': '[data-product-id]',  # Selector real V3
                'fallback': '.catalog-product-item'
            },
            'title': {
                'primary': '.catalog-product-details__name',  # REAL V3 VERIFICADO
                'fallback': '[class*="product-name"]'
            },
            'price': {
                'current': '.catalog-prices__offer-price',  # REAL V3 VERIFICADO
                'original': '.catalog-prices__list-price.catalog-prices__line_thru',  # REAL V3 VERIFICADO
                'card': '.catalog-prices__card-price'  # REAL V3 VERIFICADO
            },
            'link': {
                'primary': 'a[href*="/product/"]',
                'fallback': 'a.catalog-product-item'
            },
            'image': {
                'primary': 'img[src*="ripleycl"]',
                'fallback': 'img'
            },
            'brand': '.brand-logo span, .catalog-product-details__logo-container span',  # REAL V3
            'discount': '.catalog-product-details__discount-tag'  # REAL V3
        }
        
        # Configuración específica de Ripley (del v3)
        # Configuración específica de Ripley (preservada del v3)
        self.ripley_config = {
            'requires_visible_browser': True,  # CRÍTICO para Ripley
            'scroll_step': 200,
            'scroll_delay': 100,
            'page_load_timeout': 60000,
            'post_scroll_wait': 2000,
            'smooth_scroll_required': True  # Ripley detecta scroll no humano
        }
        
        self.logger.info("🛍️ Ripley Scraper v5 inicializado (lógica v3 preservada)")

    async def scrape_category(
        self, 
        category: str,
        max_products: int = 100,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper categoría usando lógica v3 adaptada"""
        
        start_time = datetime.now()
        session_id = f"ripley_v5_{category}_{int(start_time.timestamp())}"
        
        try:
            # Obtener URL de categoría (del v3)
            category_url = await self._get_category_url(category)
            
            self.logger.info(f"🔍 Scraping Ripley categoría {category}: {category_url}")
            
            # Configurar página con navegador visible (requerido por Ripley)
            page = await self._get_configured_page()
            
            # Navegar y hacer scraping usando lógica v3
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
                    'scraping_method': 'v3_adapted',
                    'scroll_method': 'smooth_scroll',
                    'visible_browser': True
                }
            )
            
            self.logger.info(f"✅ Ripley scraping completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error scraping Ripley categoría {category}: {e}")
            
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'v3_adapted'}
            )

    async def _get_category_url(self, category: str) -> str:
        """🔗 Obtener URL de categoría (mapeo del v3)"""
        
        # Mapeo de categorías exacto del v3 original
        category_mapping = {
            'celulares': 'https://simple.ripley.cl/tecno/celulares',
            'computacion': 'https://simple.ripley.cl/tecno/computacion',
            'television': 'https://simple.ripley.cl/tecno/television',
            'smartwatches_smartbands': 'https://simple.ripley.cl/tecno/smartwatches-y-smartbands',
            'mundo_bebe': 'https://simple.ripley.cl/jugueteria-y-ninos/mundo-bebe',
            'impresoras_tintas': 'https://simple.ripley.cl/tecno/impresoras-y-tintas'
        }
        
        url = category_mapping.get(category)
        if not url:
            raise ValueError(f"Categoría no soportada para Ripley: {category}")
        
        return url

    async def _get_configured_page(self) -> Page:
        """🔧 Obtener página configurada según requisitos v3 de Ripley"""
        
        page = await self.get_page()
        
        # Configuración específica para Ripley (del v3)
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Headers para parecer más humano
        await page.set_extra_http_headers({
            'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return page

    async def _scrape_category_v3_logic(self, page: Page, base_url: str, max_products: int) -> List[ProductData]:
        """📦 Scraping usando lógica exacta del v3"""
        
        all_products = []
        page_num = 1
        
        while len(all_products) < max_products:
            try:
                # Construir URL de página (lógica v3 exacta)
                page_url = self._build_page_url_v3(base_url, page_num)
                
                self.logger.info(f"📄 Scraping página {page_num}: {page_url[:80]}...")
                
                # Navegar a página
                await page.goto(page_url, wait_until='domcontentloaded', timeout=self.ripley_config['page_load_timeout'])
                
                # Esperar carga inicial
                await page.wait_for_timeout(3000)
                
                # Hacer scroll lento (CRÍTICO para Ripley)
                await self._smooth_scroll_v3(page)
                
                # Esperar después del scroll
                await page.wait_for_timeout(self.ripley_config['post_scroll_wait'])
                
                # Extraer productos de la página
                page_products = await self._extract_products_v3_selectors(page)
                
                if not page_products:
                    self.logger.info(f"❌ No hay más productos en página {page_num}")
                    break
                
                self.logger.info(f"✅ Extraídos {len(page_products)} productos de página {page_num}")
                
                all_products.extend(page_products)
                page_num += 1
                
                # Pausa entre páginas para evitar detección
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error en página {page_num}: {e}")
                break
        
        # Limitar a max_products solicitados
        return all_products[:max_products]

    def _build_page_url_v3(self, base_url: str, page_num: int) -> str:
        """🔗 Construir URL con paginación (lógica exacta del v3)"""
        
        if page_num <= 1:
            return base_url
        
        # Lógica específica de Ripley del v3
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

    async def _smooth_scroll_v3(self, page: Page) -> None:
        """📜 Scroll lento exactamente como en v3 (crítico para Ripley)"""
        
        try:
            # Obtener dimensiones (lógica v3)
            total_height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            current_position = 0
            scroll_step = self.ripley_config['scroll_step']  # 200px del v3
            
            self.logger.debug("🐌 Iniciando scroll lento (requerido por Ripley)")
            
            # Scroll gradual hacia abajo (exacto del v3)
            while current_position < total_height:
                await page.evaluate(f'window.scrollTo(0, {current_position})')
                current_position += scroll_step
                await page.wait_for_timeout(self.ripley_config['scroll_delay'])  # 100ms del v3
                
                # Actualizar altura por si se cargó contenido nuevo
                total_height = await page.evaluate('document.body.scrollHeight')
                
                # Detener si llegamos cerca del final
                if current_position >= total_height - viewport_height:
                    break
            
            # Scroll final hasta el fondo (v3)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(500)
            
            # Volver arriba para que el usuario vea los primeros productos (v3)
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(500)
            
            self.logger.debug("✅ Scroll lento completado")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en scroll lento: {e}")

    async def _extract_products_v3_selectors(self, page: Page) -> List[ProductData]:
        """📦 Extraer productos usando selectores exactos del v3"""
        
        products = []
        
        try:
            # Buscar tarjetas con selector primario (v3)
            primary_selector = self.selectors['cards']['primary']
            product_cards = await page.query_selector_all(primary_selector)
            
            if not product_cards:
                # Selector fallback (v3)
                fallback_selector = self.selectors['cards']['fallback'] 
                product_cards = await page.query_selector_all(fallback_selector)
            
            self.logger.info(f"🔍 Encontradas {len(product_cards)} tarjetas de producto")
            
            # Procesar cada tarjeta (lógica v3)
            for i, card in enumerate(product_cards):
                try:
                    product = await self._extract_single_product_v3(card, i)
                    if product:
                        products.append(product)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando producto {i}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo productos: {e}")
        
        return products

    async def _extract_single_product_v3(self, card: Any, index: int) -> Optional[ProductData]:
        """📋 Extraer producto usando evaluación del DOM (lógica exacta v3)"""
        
        try:
            # Extraer datos con SELECTORES REALES de Ripley (verificados en scraper portable)
            data = await card.evaluate('''
                (element) => {
                    const result = {
                        href: element.getAttribute('href') || '',
                        partnumber: element.getAttribute('data-partnumber') || '',
                        id: element.getAttribute('id') || '',
                        brand: '',
                        detail: '',
                        image: '',
                        prices: {
                            normal: '',
                            internet: '',
                            card: ''
                        },
                        specs: {
                            storage: '',
                            ram: '',
                            screen_size: '',
                            camera: '',
                            colors: []
                        },
                        marketing: {
                            discount_percent: '',
                            emblems: []
                        }
                    };
                    
                    // Extraer marca - SELECTOR REAL VERIFICADO
                    const brandEl = element.querySelector('.brand-logo span, .catalog-product-details__logo-container span');
                    if (brandEl) {
                        result.brand = brandEl.textContent.trim();
                    }
                    
                    // Extraer nombre - SELECTOR REAL VERIFICADO
                    const nameEl = element.querySelector('.catalog-product-details__name');
                    if (nameEl) {
                        result.detail = nameEl.textContent.trim();
                    }
                    
                    // Extraer imagen
                    const imgEl = element.querySelector('img');
                    if (imgEl) {
                        result.image = imgEl.getAttribute('src') || '';
                    }
                    
                    // Extraer precios - SELECTORES REALES VERIFICADOS
                    // Precio normal (tachado)
                    const normalPriceEl = element.querySelector('.catalog-prices__list-price.catalog-prices__line_thru');
                    if (normalPriceEl) {
                        result.prices.normal = normalPriceEl.textContent.trim();
                    }
                    
                    // Precio internet - SELECTOR REAL
                    const internetPriceEl = element.querySelector('.catalog-prices__offer-price');
                    if (internetPriceEl) {
                        result.prices.internet = internetPriceEl.textContent.trim();
                    }
                    
                    // Precio tarjeta Ripley - SELECTOR REAL
                    const cardPriceEl = element.querySelector('.catalog-prices__card-price');
                    if (cardPriceEl) {
                        const cardText = cardPriceEl.textContent.trim();
                        if (cardText.includes('$')) {
                            result.prices.card = cardText.split('$')[1].split(' ')[0];
                        }
                    }
                    
                    // Extraer descuento - SELECTOR REAL
                    const discountEl = element.querySelector('.catalog-product-details__discount-tag');
                    if (discountEl) {
                        result.marketing.discount_percent = discountEl.textContent.trim();
                    }
                    
                    // Extraer colores disponibles - SELECTOR REAL
                    const colorElements = element.querySelectorAll('.catalog-colors-option-outer');
                    colorElements.forEach(colorEl => {
                        const colorTitle = colorEl.getAttribute('title');
                        if (colorTitle) {
                            result.specs.colors.push(colorTitle);
                        }
                    });
                    
                    // Extraer emblemas/badges - SELECTOR REAL
                    const emblemElements = element.querySelectorAll('.emblem');
                    emblemElements.forEach(emblemEl => {
                        const emblemText = emblemEl.textContent.trim();
                        if (emblemText) {
                            result.marketing.emblems.push(emblemText);
                        }
                    });
                    
                    // Extraer especificaciones del nombre del producto
                    const productName = result.detail || '';
                    
                    // Storage - REGEX VERIFICADO
                    const storageMatch = productName.match(/(\\d+)\\s*gb(?!\\s+ram)/i);
                    if (storageMatch) {
                        result.specs.storage = storageMatch[1] + 'GB';
                    }
                    
                    // RAM - REGEX VERIFICADO
                    const ramMatch = productName.match(/(\\d+)\\s*gb\\s+ram/i);
                    if (ramMatch) {
                        result.specs.ram = ramMatch[1] + 'GB';
                    }
                    
                    // Screen size - REGEX VERIFICADO
                    const screenMatch = productName.match(/(\\d+\\.?\\d*)"/); 
                    if (screenMatch) {
                        result.specs.screen_size = screenMatch[1] + '"';
                    }
                    
                    // Camera - REGEX VERIFICADO
                    const cameraMatch = productName.match(/(\\d+)mp/i);
                    if (cameraMatch) {
                        result.specs.camera = cameraMatch[1] + 'MP';
                    }
                    
                    return result;
                }
            ''')
            
            # Procesar datos (igual que ripley_final)
            url = urljoin("https://simple.ripley.cl", data['href'])
            sku = data['partnumber'] or data['id'] or ""
            sku = re.sub(r'\W+', '', sku).strip()  # Limpiar SKU
            
            # Construir nombre (igual que ripley_final)
            name_parts = []
            if data['brand']:
                name_parts.append(data['brand'])
            if data['detail']:
                name_parts.append(data['detail'])
            title = " ".join(name_parts)
            title = re.sub(r'\s+', ' ', title).strip()
            
            if not title:
                return None
                
            # Procesar imagen
            image = data.get('image', '')
            if image and not image.startswith('http'):
                image = urljoin('https://simple.ripley.cl', image)
            
            # Procesar precios (lógica v3)
            p_normal = data['prices']['normal'] or ""
            p_internet = data['prices']['internet'] or ""
            p_card = data['prices']['card'] or ""
            
            # Lógica de fallback (igual que ripley_final)
            if not p_internet and p_normal:
                p_internet = p_normal
            if not p_normal and (p_internet or p_card):
                p_normal = p_internet or p_card
            
            p_plp = p_internet or p_card or p_normal
            
            # Convertir precios a números
            normal_num = self._parse_price_v3(p_normal)
            internet_num = self._parse_price_v3(p_internet)
            card_num = self._parse_price_v3(p_card)
            plp_num = self._parse_price_v3(p_plp)
            
            # Usar el precio más bajo disponible
            current_price = min(filter(lambda x: x > 0, [internet_num, card_num, normal_num]), default=0)
            original_price = normal_num if normal_num > current_price else current_price
            
            # Calcular descuento
            discount_percentage = 0
            if original_price > current_price > 0:
                discount_percentage = int(((original_price - current_price) / original_price) * 100)
            
            # Crear ProductData (formato v5 con datos enriquecidos v3)
            product = ProductData(
                title=title,
                current_price=current_price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                currency="CLP",
                availability="in_stock",
                product_url=url,
                image_urls=[image] if image else [],
                brand=data.get('brand', ''),
                sku=sku,
                rating=0.0,
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info={
                    'extraction_method': 'v3_dom_evaluation',
                    'card_index': index,
                    'precio_normal': p_normal,
                    'precio_internet': p_internet,
                    'precio_tarjeta': p_card,
                    'storage': data['specs']['storage'],
                    'ram': data['specs']['ram'],
                    'screen_size': data['specs']['screen_size'],
                    'camera': data['specs']['camera'],
                    'colors': data['specs']['colors'],
                    'discount_text': data['marketing']['discount_percent'],
                    'badges': data['marketing']['emblems']
                }
            )
            
            return product
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error extrayendo producto {index}: {e}")
            return None

    def _parse_price_v3(self, price_text: str) -> float:
        """💰 Parsear precio con lógica exacta del v3"""
        
        if not price_text:
            return 0.0
        
        try:
            # Limpiar texto (v3)
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
        """🔎 Búsqueda de productos (adaptado del v3)"""
        
        start_time = datetime.now()
        session_id = f"ripley_search_v5_{query[:20]}_{int(start_time.timestamp())}"
        
        try:
            # URL de búsqueda con formato v3
            search_url = f"{self.base_urls['search']}?q={query}"
            
            self.logger.info(f"🔎 Búsqueda Ripley: '{query}' - {search_url}")
            
            # Usar misma lógica que categoría
            page = await self._get_configured_page()
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
            
            self.logger.info(f"✅ Búsqueda Ripley completada: {len(products)} productos para '{query}'")
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
            if product.product_url and 'ripley.cl' not in product.product_url:
                issues.append(f"{product_id}: URL no es de Ripley")
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
            'link': 'https://ripley.cl/notebook-test-123',
            'nombre': 'Notebook Lenovo IdeaPad 3 AMD Ryzen 5 8GB RAM 512GB SSD',
            'sku': 'MPM00123456',
            'precio_normal': '$799.990',
            'precio_oferta': '$599.990',
            'precio_tarjeta': 'CMR $549.990',
            'precio_normal_num': 799990,
            'precio_oferta_num': 599990,
            'precio_tarjeta_num': 549990,
            'precio_min_num': 549990,
            'tipo_precio_min': 'tarjeta',
            'retailer': 'ripley',
            'category': category,
            'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Campos opcionales
            'marca': 'Lenovo',
            'imagen': 'https://ripley.cl/image/test.jpg',
            'disponibilidad': 'available',
            'rating': 4.5,
            'reviews': 127
        }
        
        products.append(test_product)
        return products