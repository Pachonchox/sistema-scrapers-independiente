# -*- coding: utf-8 -*-
"""
🏪 Hites Chile Scraper v5 MEJORADO - Integración de Selectores PORT
=================================================================

INTEGRA SELECTORES EXACTOS DE scrappers_port/hites_scraper.py que SÍ FUNCIONAN
en la arquitectura V5 con Playwright async, aplicando las mismas optimizaciones
exitosas implementadas para Ripley y Paris.

✅ SELECTORES ESPECÍFICOS MIGRADOS:
- div.product-tile-body (selector principal)
- .product-name--bundle (nombre producto + URL)
- .product-brand (marca)
- .product-sku (código SKU)
- .price-item.sales .value (precio actual)
- .price-item.list .value (precio original)
- .discount-badge (descuento)

✅ LÓGICA DE PARSING MIGRADA:
- Extracción por clases específicas Hites
- Parsing de precios con content attribute
- Manejo de especificaciones (.attribute-values)
- Rating por conteo de estrellas
- Detección de marketplace/vendedor
- Stock y disponibilidad

🎯 OBJETIVO: 100% compatibilidad con scraper PORT que SÍ EXTRAE DATOS
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import Page, ElementHandle

# Importaciones V5 (mantener compatibilidad)
try:
    from portable_orchestrator_v5.core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
    from portable_orchestrator_v5.core.exceptions import *
except ImportError:
    # Fallback para testing independiente
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

# Selector principal (el que SÍ encuentra productos en Hites)
PRODUCT_CONTAINER_SELECTOR = "div.product-tile-body"

# Selectores de datos específicos (del PORT funcional)
HITES_SELECTORS = {
    'brand': '.product-brand',
    'name': '.product-name--bundle', 
    'sku': '.product-sku',
    'seller': '.marketplace-info-plp b',
    'price_current': '.price-item.sales .value',
    'price_original': '.price-item.list .value',
    'discount': '.discount-badge',
    'attributes': '.attribute-values',
    'stars': '.yotpo-icon-star.rating-star',
    'reviews': '.yotpo-total-reviews',
    'shipping': '.shipping-method .method-description span:first-child',
    'out_of_stock': '.outofstock'
}

# Palabras clave para detección de colores (del PORT)
COLOR_KEYWORDS = ['light blue', 'blue', 'azul', 'negro', 'black', 'white', 'blanco', 
                  'red', 'rojo', 'green', 'verde', 'gray', 'gris', 'gold', 'dorado', 
                  'silver', 'plateado', 'purple', 'morado', 'pink', 'rosa']

class HitesScraperV5Improved(BaseScraperV5):
    """🏪 Scraper Hites V5 con selectores PORT integrados y optimizados"""
    
    def __init__(self):
        super().__init__("hites")
        
        # URLs exactas (del PORT)
        self.base_urls = {
            'home': 'https://www.hites.com',
            'celulares': 'https://www.hites.com/celulares/smartphones/',
            'tablets': 'https://www.hites.com/celulares/tablets/',
            'computadores': 'https://www.hites.com/computacion/notebooks/',
            'television': 'https://www.hites.com/television/smart-tv/'
        }
        
        # Configuración específica de Hites (optimizada)
        self.config = {
            'page_timeout': 60000,             # 60 segundos (Hites puede ser lento)
            'load_wait': 10000,                # 10 segundos inicial
            'scroll_step': 200,                # Paso de scroll
            'scroll_delay': 3000,              # 3 segundos entre scrolls (como PORT)
            'post_scroll_wait': 2000,          # Espera post-scroll
            'batch_size': 20,                  # Lotes para procesar
            'element_timeout': 15000,          # Timeout más generoso
            
            # Configuración estándar para Hites (no requiere visible browser como Ripley)
            'requires_visible_browser': False,  
            'scroll_count': 3                  # 3 scrolls como en PORT
        }
        
        self.logger.info("🏪 Hites Scraper V5 MEJORADO inicializado - Selectores PORT configurados")

    async def scrape_category(
        self, 
        category: str = "celulares",
        max_products: int = 500,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper con selectores exactos del PORT optimizados"""
        
        start_time = datetime.now()
        session_id = f"hites_improved_{category}_{int(start_time.timestamp())}"
        
        try:
            # URL de categoría
            category_url = self.base_urls.get(category, self.base_urls['celulares'])
            
            self.logger.info(f"🔍 Scraping Hites MEJORADO - {category}: {category_url}")
            
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
                    'scroll_method': 'hites_style_scroll'
                }
            )
            
            self.logger.info(f"✅ Hites MEJORADO completado: {len(products)} productos en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error Hites MEJORADO categoría {category}: {e}")
            
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
        """📦 Scraping usando lógica exacta del PORT pero optimizada"""
        
        all_products = []
        
        try:
            # Navegar a la página
            self.logger.info(f"📄 Navegando a: {url}")
            
            # Configurar headers específicos para Hites
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-CL,es;q=0.8,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br'
            })
            
            await page.goto(url, wait_until='networkidle', timeout=self.config['page_timeout'])
            
            # Esperar carga inicial (como PORT)
            await page.wait_for_timeout(self.config['load_wait'])
            
            # Scroll progresivo para cargar productos (método PORT exacto)
            await self._hites_style_scroll(page)
            
            # Esperar post-scroll
            await page.wait_for_timeout(self.config['post_scroll_wait'])
            
            # Extraer productos con selectores PORT optimizados
            products = await self._extract_products_port_optimized(page)
            
            self.logger.info(f"📦 Productos extraídos con método PORT optimizado: {len(products)}")
            
            # Limitar a max_products
            return products[:max_products]
            
        except Exception as e:
            self.logger.error(f"❌ Error en scraping PORT logic optimizado: {e}")
            return []

    async def _hites_style_scroll(self, page: Page):
        """📜 Scroll específico para Hites (método exacto del PORT)"""
        
        try:
            self.logger.info("📜 Realizando scroll para cargar productos (método PORT)...")
            
            # Scroll progresivo exacto del PORT (3 etapas)
            for i in range(self.config['scroll_count']):
                scroll_position = f"document.body.scrollHeight * {(i+1)/3}"
                await page.evaluate(f"window.scrollTo(0, {scroll_position});")
                
                self.logger.debug(f"📜 Scroll {i+1}/3 completado")
                await page.wait_for_timeout(self.config['scroll_delay'])  # 3s como PORT
            
            self.logger.info("✅ Scroll Hites completado")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en scroll Hites: {e}")

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
        """📋 Extraer producto individual con TODOS los campos del scrapers_port/hites_scraper.py"""
        
        try:
            # ==========================================
            # EXTRACCIÓN COMPLETA - TODOS LOS CAMPOS DEL PORT
            # ==========================================
            
            # 1. Marca - selector exacto PORT: .product-brand
            brand = ""
            try:
                brand_element = await container.query_selector(HITES_SELECTORS['brand'])
                if brand_element:
                    brand = await brand_element.inner_text()
                    brand = brand.strip()
            except:
                pass
            
            # 2. Nombre del producto y URL - selector exacto PORT: .product-name--bundle
            product_name = ""
            product_url = ""
            try:
                name_element = await container.query_selector(HITES_SELECTORS['name'])
                if name_element:
                    product_name = await name_element.inner_text()
                    product_name = product_name.strip()
                    
                    # URL desde el mismo elemento (como en PORT)
                    href = await name_element.get_attribute('href')
                    if href and href.startswith('/'):
                        product_url = f"https://www.hites.com{href}"
                    else:
                        product_url = href or ""
            except:
                pass
            
            if not product_name:
                return None
            
            # 3. SKU - selector exacto PORT: .product-sku
            sku = ""
            try:
                sku_element = await container.query_selector(HITES_SELECTORS['sku'])
                if sku_element:
                    sku_text = await sku_element.inner_text()
                    # Procesamiento exacto como PORT: .replace("SKU: ", "")
                    sku = sku_text.replace("SKU: ", "").strip()
            except:
                pass
            
            if not sku:
                return None
            
            # 4. Vendedor/Marketplace - selector exacto PORT: .marketplace-info-plp b
            seller = "Hites"  # Default como en PORT
            try:
                seller_element = await container.query_selector(HITES_SELECTORS['seller'])
                if seller_element:
                    seller = await seller_element.inner_text()
                    seller = seller.strip()
            except:
                pass
            
            # ==========================================
            # 5. ATRIBUTOS ESPECÍFICOS - EXACTO COMO PORT
            # ==========================================
            storage = ""
            screen_size = ""
            front_camera = ""
            
            try:
                attribute_elements = await container.query_selector_all(HITES_SELECTORS['attributes'])
                for attr_element in attribute_elements:
                    attr_text = await attr_element.inner_text()
                    attr_text = attr_text.strip()
                    
                    # Procesamiento exacto como PORT
                    if "Almacenamiento:" in attr_text:
                        storage = attr_text.replace("Almacenamiento:", "").strip()
                    elif "Tamaño De Pantalla:" in attr_text:
                        screen_size = attr_text.replace("Tamaño De Pantalla:", "").strip()
                    elif "Cámara Frontal:" in attr_text:
                        front_camera = attr_text.replace("Cámara Frontal:", "").strip()
            except:
                pass
            
            # ==========================================
            # 6. PRECIOS - EXACTO COMO PORT CON CONTENT ATTRIBUTE
            # ==========================================
            current_price_text = ""
            original_price_text = ""
            current_price_numeric = None
            original_price_numeric = None
            
            # Precio actual - selector: .price-item.sales .value
            try:
                current_element = await container.query_selector(HITES_SELECTORS['price_current'])
                if current_element:
                    current_price_text = await current_element.inner_text()
                    current_price_text = current_price_text.strip()
                    
                    # Intentar extraer del atributo content primero (lógica PORT)
                    price_content = await current_element.get_attribute('content')
                    if price_content:
                        try:
                            current_price_numeric = int(price_content)
                        except:
                            pass
                    else:
                        # Fallback: regex como PORT
                        price_match = re.search(r'\$?([0-9.,]+)', current_price_text.replace('.', ''))
                        if price_match:
                            try:
                                current_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
            except:
                pass
            
            # Precio original - selector: .price-item.list .value
            try:
                original_element = await container.query_selector(HITES_SELECTORS['price_original'])
                if original_element:
                    original_price_text = await original_element.inner_text()
                    original_price_text = original_price_text.strip()
                    
                    # Intentar extraer del atributo content primero (lógica PORT)
                    price_content = await original_element.get_attribute('content')
                    if price_content:
                        try:
                            original_price_numeric = int(price_content)
                        except:
                            pass
                    else:
                        # Fallback: regex como PORT
                        price_match = re.search(r'\$?([0-9.,]+)', original_price_text.replace('.', ''))
                        if price_match:
                            try:
                                original_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
            except:
                pass
            
            # 7. Descuento - selector exacto PORT: .discount-badge
            discount_percent = ""
            try:
                discount_element = await container.query_selector(HITES_SELECTORS['discount'])
                if discount_element:
                    discount_percent = await discount_element.inner_text()
                    discount_percent = discount_percent.strip()
            except:
                pass
            
            # ==========================================
            # 8. RATING Y REVIEWS - MÉTODO EXACTO PORT
            # ==========================================
            
            # Rating por conteo de estrellas - selector: .yotpo-icon-star.rating-star
            rating = 0
            try:
                star_elements = await container.query_selector_all(HITES_SELECTORS['stars'])
                rating = len(star_elements)  # Conteo directo como PORT
            except:
                pass
            
            # Número de reviews - selector: .yotpo-total-reviews + regex
            reviews_count = ""
            try:
                reviews_element = await container.query_selector(HITES_SELECTORS['reviews'])
                if reviews_element:
                    reviews_text = await reviews_element.inner_text()
                    # Regex exacto como PORT: r'\((\d+)\)'
                    reviews_match = re.search(r'\((\d+)\)', reviews_text)
                    if reviews_match:
                        reviews_count = reviews_match.group(1)
            except:
                pass
            
            # ==========================================
            # 9. OPCIONES DE ENVÍO - EXACTO COMO PORT
            # ==========================================
            shipping_options = []
            try:
                shipping_elements = await container.query_selector_all(HITES_SELECTORS['shipping'])
                for shipping_element in shipping_elements:
                    shipping_text = await shipping_element.inner_text()
                    if shipping_text.strip():
                        shipping_options.append(shipping_text.strip())
            except:
                pass
            
            # ==========================================
            # 11. COLOR - EXTRACCIÓN EXACTA COMO PORT
            # ==========================================
            color = ""
            # Palabras clave exactas del PORT
            color_keywords = COLOR_KEYWORDS
            product_name_lower = product_name.lower()
            for keyword in color_keywords:
                if keyword in product_name_lower:
                    color = keyword.title()
                    break
            
            # ==========================================
            # 12. VALIDACIÓN FINAL - EXACTO COMO PORT
            # ==========================================
            # Solo agregar productos válidos (condición del PORT)
            if not (product_name and sku):
                return None
            
            # ==========================================
            # CREAR PRODUCTO CON ESTRUCTURA EXACTA DEL PORT
            # ==========================================
            
            # Construir título completo
            title_parts = []
            if brand:
                title_parts.append(brand)
            if product_name:
                title_parts.append(product_name)
            title = " ".join(title_parts)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Determinar precio principal
            current_price = float(current_price_numeric or 0)
            original_price = float(original_price_numeric or current_price)
            
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
                availability="out_of_stock" if out_of_stock else "in_stock",
                product_url=product_url,
                image_urls=[],
                brand=brand,
                sku=sku,
                rating=float(rating),
                retailer=self.retailer,
                extraction_timestamp=datetime.now(),
                additional_info={
                    'extraction_method': 'port_complete_fields',
                    'container_index': index,
                    
                    # ==== TODOS LOS CAMPOS DEL PORT ORIGINAL ====
                    'sku': sku,
                    'brand': brand,
                    'name': product_name,
                    'seller': seller,
                    'storage': storage,
                    'screen_size': screen_size,
                    'front_camera': front_camera,
                    'color': color,
                    
                    # Precios con texto y numérico (exacto como PORT)
                    'current_price_text': current_price_text,
                    'current_price': current_price_numeric,
                    'original_price_text': original_price_text,
                    'original_price': original_price_numeric,
                    'discount_percent': discount_percent,
                    
                    # Rating y reviews
                    'rating': rating,
                    'reviews_count': reviews_count,
                    
                    # Otros campos PORT
                    'shipping_options': ', '.join(shipping_options),
                    'out_of_stock': out_of_stock,
                    'product_url': product_url,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return product
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo producto individual: {e}")
            return None

    async def _extract_hites_attributes(self, container: ElementHandle) -> Dict[str, str]:
        """🔧 Extraer atributos específicos de Hites (método PORT)"""
        
        attributes = {
            'storage': '',
            'screen_size': '',
            'front_camera': ''
        }
        
        try:
            # Buscar todos los elementos de atributos
            attr_elements = await container.query_selector_all(HITES_SELECTORS['attributes'])
            
            for attr_element in attr_elements:
                attr_text = await attr_element.inner_text()
                attr_text = attr_text.strip()
                
                # Parsear según tipo de atributo (método PORT)
                if "Almacenamiento:" in attr_text:
                    attributes['storage'] = attr_text.replace("Almacenamiento:", "").strip()
                elif "Tamaño De Pantalla:" in attr_text:
                    attributes['screen_size'] = attr_text.replace("Tamaño De Pantalla:", "").strip()
                elif "Cámara Frontal:" in attr_text:
                    attributes['front_camera'] = attr_text.replace("Cámara Frontal:", "").strip()
                    
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo atributos: {e}")
        
        return attributes

    def _extract_color_from_name(self, product_name: str) -> str:
        """🎨 Extraer color del nombre del producto (método PORT)"""
        
        if not product_name:
            return ""
        
        product_name_lower = product_name.lower()
        for keyword in COLOR_KEYWORDS:
            if keyword in product_name_lower:
                return keyword.title()
        
        return ""

    def _parse_price_hites_method(self, price_text: str) -> float:
        """💰 Parsear precio con método exacto del PORT"""
        
        if not price_text:
            return 0.0
        
        try:
            # Limpiar precio (método PORT)
            price_match = re.search(r'\$?([0-9.,]+)', price_text.replace('.', ''))
            if price_match:
                try:
                    return float(price_match.group(1).replace(',', ''))
                except:
                    return 0.0
            return 0.0
            
        except (ValueError, AttributeError):
            return 0.0

    async def validate_extraction(self, products: List[ProductData]) -> Tuple[bool, List[str]]:
        """✅ Validación PORT compatible para Hites"""
        
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
                
            if not product.sku:
                issues.append(f"{product_id}: SKU faltante")
                continue
                
            if product.product_url and 'hites.com' not in product.product_url:
                issues.append(f"{product_id}: URL no es de Hites")
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

async def test_hites_improved_scraper():
    """🧪 Test del scraper Hites mejorado"""
    
    print("🧪 TEST HITES SCRAPER V5 MEJORADO")
    print("=" * 50)
    
    scraper = HitesScraperV5Improved()
    
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
                stock_text = " [SIN STOCK]" if product.additional_info.get('out_of_stock') else ""
                
                print(f"{i}. {product.title}{stock_text}")
                print(f"   Precio: {current_price}{original_price}")
                print(f"   SKU: {product.sku}")
                print(f"   Vendedor: {product.additional_info.get('seller')}")
                print(f"   Rating: {product.rating} estrellas ({product.additional_info.get('reviews_count')} reviews)")
                
                # Mostrar especificaciones si están disponibles
                specs = []
                if product.additional_info.get('storage'):
                    specs.append(product.additional_info['storage'])
                if product.additional_info.get('screen_size'):
                    specs.append(product.additional_info['screen_size'])
                if product.additional_info.get('front_camera'):
                    specs.append(product.additional_info['front_camera'])
                    
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
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    asyncio.run(test_hites_improved_scraper())