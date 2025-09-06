# -*- coding: utf-8 -*-
"""
🛒 Falabella Chile Scraper v5 - PARALELO + PORT INTEGRADO
========================================================

SCRAPER PARALELO DE FALABELLA CON MEJORAS DE PARIS:
- Scraping de 5 páginas simultáneas
- Detección automática de fin de páginas  
- Paginación corregida específica para Falabella
- Selectores exactos del PORT funcional
- Velocidad ultra-optimizada

🎯 OBJETIVO: Máxima velocidad con 100% funcionalidad PORT
"""

import asyncio
import logging
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import Page

# Importaciones del sistema V5
try:
    from core.base_scraper import BaseScraperV5, ProductData, ScrapingResult
    from core.utils import *
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

# ==========================================
# SELECTORES EXACTOS DEL PORT (FUNCIONALES)
# ==========================================

# Selector principal: contenedor de productos (del PORT scraper que funciona)
# El PORT usa búsqueda por clases con regex: 'search-results.*grid-pod'
PRODUCT_CONTAINER_SELECTOR = 'div[class*="search-results"][class*="grid-pod"], div[class*="grid-pod"], div[data-key]'

# Selectores específicos de Falabella del PORT (usando los patterns del PORT)
FALABELLA_SELECTORS = {
    # Del PORT: container.find('b', class_=re.compile(r'pod-subTitle'))
    'product_name': 'b[class*="pod-subTitle"], b[class*="pod-title"]',
    # Del PORT: container.find('li', attrs={'data-internet-price': True})
    'cmr_price': 'li[data-cmr-price]',
    'internet_price': 'li[data-internet-price]', 
    # Del PORT: container.find('a', attrs={'data-key': True})
    'product_link': 'a[data-key]',
    # Del PORT: container.find('img')
    'product_image': 'img',
    # Del PORT: container.find('b', class_=re.compile(r'pod-title'))
    'brand': 'b[class*="pod-title"]',
    # Del PORT: container.find('div', attrs={'data-rating': True})
    'rating': 'div[data-rating]',
    # Del PORT: container.find_all('span', class_=re.compile(r'pod-badges-item'))
    'badges': 'span[class*="pod-badges-item"]',
    # Del PORT: container.find('b', class_=re.compile(r'pod-sellerText'))
    'seller': 'b[class*="pod-sellerText"]'
}

# Regex para especificaciones
SPECS_REGEX = {
    'storage': r'(\d+)gb(?!\s+ram)',
    'ram': r'(\d+)gb\s+ram', 
    'network': r'(4g|5g)',
    'color': r'(negro|blanco|azul|rojo|verde|gris|dorado|plateado|purpura|rosa)$'
}


class FalabellaScraperV5Parallel(BaseScraperV5):
    """🛒 Scraper Falabella V5 - PARALELO + PORT INTEGRADO"""
    
    def __init__(self):
        super().__init__("falabella")
        
        # URL base de Falabella
        self.base_url = "https://www.falabella.com/falabella-cl/category/cat2018/Celulares-y-Telefonos"
        
        # Configuración de paginación centralizada
        self.pagination_config = self._load_pagination_config()
        
        # Configuración ULTRA-RÁPIDA
        self.config = {
            'initial_wait': 2,
            'scroll_wait': 1,
            'mid_scroll_wait': 0.5,
            'element_timeout': 3000,
            'page_timeout': 30000,
        }
        
        self.logger.info("🛒 Falabella Scraper V5 - PARALELO inicializado")

    def _load_pagination_config(self) -> Dict[str, Any]:
        """📄 Cargar configuración de paginación desde config.json"""
        try:
            config_path = Path(__file__).parent.parent / "config.json"
            if not config_path.exists():
                self.logger.warning(f"⚠️ Config.json no encontrado")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            falabella_config = config_data.get('retailers', {}).get('falabella', {})
            pagination_config = falabella_config.get('paginacion', {})
            
            if pagination_config:
                self.logger.info(f"✅ Configuración Falabella cargada: {pagination_config.get('url_pattern', 'N/A')}")
                return pagination_config
            else:
                self.logger.warning("⚠️ No se encontró configuración de paginación para Falabella")
                return {}
                
        except Exception as e:
            self.logger.error(f"💥 Error cargando configuración: {e}")
            return {}

    async def scrape_category(
        self, 
        category: str = "celulares",
        max_products: int = 500,
        filters: Dict[str, Any] = None
    ) -> ScrapingResult:
        """🔍 Scraper PARALELO con lógica PORT integrada"""
        
        start_time = datetime.now()
        session_id = f"falabella_parallel_{category}_{int(start_time.timestamp())}"
        
        page = None
        try:
            self.logger.info(f"🔍 Scraping Falabella PARALELO - {category}: {self.base_url}")
            
            # Obtener página inicial
            page = await self.get_page()
            if not page:
                raise Exception("No se pudo obtener la página")
            
            # Scraping paralelo con paginación
            products = await self._scrape_with_pagination_parallel(page, max_products)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = ScrapingResult(
                success=True,
                products=products,
                total_found=len(products),
                execution_time=execution_time,
                session_id=session_id,
                source_url=self.base_url,
                retailer=self.retailer,
                category=category,
                timestamp=datetime.now(),
                metadata={
                    'scraping_method': 'parallel_port_integrated',
                    'parallel_pages': 5,
                    'extraction_method': 'playwright_parallel',
                    'success_rate': f"{len(products)}/{max_products}",
                    'pagination_used': len(self.pagination_config) > 0
                }
            )
            
            # Guardar JSON en background
            asyncio.create_task(self._save_retailer_json(products, session_id, execution_time))
            
            self.logger.info(f"✅ Falabella PARALELO completado: {len(products)} productos en {execution_time:.1f}s")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error Falabella PARALELO: {e}")
            
            return ScrapingResult(
                success=False,
                products=[],
                total_found=0,
                execution_time=execution_time,
                session_id=session_id,
                source_url=self.base_url,
                retailer=self.retailer,
                category=category,
                timestamp=datetime.now(),
                error_message=str(e),
                metadata={'error_type': type(e).__name__, 'scraping_method': 'parallel_port_integrated'}
            )
        
        finally:
            # Limpiar recursos
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def _scrape_with_pagination_parallel(self, initial_page: Page, max_products: int) -> List[ProductData]:
        """📦 Scraping PARALELO con 5 páginas simultáneas"""
        
        all_products = []
        current_batch_start = 1
        consecutive_empty_batches = 0
        
        # Configuración de paralelismo y detección
        batch_size = 5  # 5 páginas simultáneas
        max_empty_batches = 2
        max_pages_config = self.pagination_config.get('max_pages', 999) if self.pagination_config else 999
        auto_stop_enabled = self.pagination_config.get('auto_stop', True) if self.pagination_config else True
        
        self.logger.info(f"🚀 Iniciando Falabella PARALELO:")
        self.logger.info(f"   📄 Max páginas: {max_pages_config}")
        self.logger.info(f"   ⚡ Páginas paralelas: {batch_size}")
        self.logger.info(f"   🔚 Auto-stop: {'Activado' if auto_stop_enabled else 'Desactivado'}")
        
        while len(all_products) < max_products and current_batch_start <= max_pages_config:
            # Preparar lote de páginas
            batch_pages = []
            for i in range(batch_size):
                page_num = current_batch_start + i
                if page_num > max_pages_config:
                    break
                batch_pages.append(page_num)
            
            if not batch_pages:
                break
            
            self.logger.info(f"🚀 Procesando lote Falabella páginas {batch_pages[0]} a {batch_pages[-1]}")
            
            # Procesar páginas en paralelo
            batch_results = await self._process_pages_parallel(batch_pages)
            
            # Procesar resultados del lote
            batch_total_products = 0
            empty_pages_in_batch = 0
            
            for page_num, page_result in batch_results:
                if page_result is None:
                    empty_pages_in_batch += 1
                    continue
                
                page_products, page_status = page_result
                
                if page_status == "empty":
                    empty_pages_in_batch += 1
                    continue
                elif page_status == "error":
                    continue
                elif page_status == "success":
                    batch_total_products += len(page_products)
                    all_products.extend(page_products)
                    self.logger.info(f"✅ Falabella página {page_num}: {len(page_products)} productos")
            
            self.logger.info(f"📊 Lote Falabella completado: {batch_total_products} productos de {len(batch_pages)} páginas")
            
            # Verificar condiciones de fin
            if auto_stop_enabled:
                if empty_pages_in_batch == len(batch_pages):
                    consecutive_empty_batches += 1
                    self.logger.warning(f"⚠️ Lote Falabella completamente vacío ({consecutive_empty_batches})")
                    
                    if consecutive_empty_batches >= max_empty_batches:
                        self.logger.info("🔚 2 lotes vacíos consecutivos, terminando")
                        break
                else:
                    consecutive_empty_batches = 0
                
                if len(all_products) >= max_products:
                    self.logger.info(f"🎯 Límite alcanzado: {len(all_products)}/{max_products}")
                    break
            
            # Siguiente lote
            current_batch_start += batch_size
            
            # Pausa mínima entre lotes
            await asyncio.sleep(0.1)
        
        # Limitar resultados finales
        final_products = all_products[:max_products]
        
        self.logger.info(f"📦 Falabella PARALELO completado:")
        self.logger.info(f"   📄 Páginas procesadas: hasta {current_batch_start - 1}")
        self.logger.info(f"   ⚡ Lotes procesados: {(current_batch_start - 1) // batch_size}")
        self.logger.info(f"   🎯 Productos extraídos: {len(final_products)}")
        
        return final_products

    async def _process_pages_parallel(self, page_numbers: List[int]) -> List[tuple]:
        """🚀 Procesar páginas Falabella en paralelo"""
        
        # Crear tareas para cada página
        tasks = []
        for page_num in page_numbers:
            task = asyncio.create_task(self._scrape_single_page(page_num))
            tasks.append(task)
        
        # Ejecutar en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        processed_results = []
        for i, result in enumerate(results):
            page_num = page_numbers[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"❌ Error Falabella página {page_num}: {result}")
                processed_results.append((page_num, None))
            else:
                processed_results.append((page_num, result))
        
        return processed_results

    async def _scrape_single_page(self, page_num: int) -> tuple:
        """📄 Scraper una página Falabella individual"""
        
        page = None
        try:
            # Crear nueva página
            page = await self.get_page()
            if not page:
                return ([], "error")
            
            # Construir URL específica para Falabella
            page_url = self._build_page_url_falabella(page_num)
            
            # Navegar
            response = await page.goto(page_url, wait_until='domcontentloaded', timeout=self.config['page_timeout'])
            if response and response.status >= 400:
                return ([], "error")
            
            # Verificar redirección a página principal
            current_url = page.url
            if page_num > 1 and current_url == self.base_url:
                self.logger.info(f"🔚 Falabella página {page_num} redirigió a principal")
                return ([], "empty")
            
            # Aplicar timing optimizado
            await self._apply_fast_timing(page)
            
            # Extraer productos usando lógica PORT
            page_products = await self._extract_products_falabella(page)
            
            if len(page_products) == 0:
                return ([], "empty")
            
            return (page_products, "success")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error Falabella página {page_num}: {e}")
            return ([], "error")
        
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    def _build_page_url_falabella(self, page_num: int) -> str:
        """🔗 Construir URL específica para Falabella"""
        try:
            # LÓGICA ESPECÍFICA PARA FALABELLA:
            # Página 1: https://www.falabella.com/falabella-cl/category/cat2018/Celulares-y-Telefonos
            # Página 2+: https://www.falabella.com/falabella-cl/category/cat2018/Celulares-y-Telefonos?page=2
            
            if page_num <= 1:
                return self.base_url
            else:
                return f"{self.base_url}?page={page_num}"
            
        except Exception as e:
            self.logger.error(f"💥 Error construyendo URL Falabella: {e}")
            if page_num <= 1:
                return self.base_url
            else:
                return f"{self.base_url}?page={page_num}"

    async def _apply_fast_timing(self, page: Page):
        """⚡ Timing ultra-rápido para Falabella"""
        try:
            # Espera mínima para contenedores
            for _ in range(6):  # 3 segundos máximo
                containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
                if len(containers) >= 3:
                    self.logger.info(f"⚡ Falabella: {len(containers)} contenedores detectados")
                    break
                await asyncio.sleep(0.5)
            
            # Scroll rápido
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
            await asyncio.sleep(0.5)
            
        except Exception as e:
            self.logger.error(f"💥 Error timing Falabella: {e}")
            await asyncio.sleep(2)

    async def _extract_products_falabella(self, page: Page) -> List[ProductData]:
        """📊 Extraer productos Falabella usando selectores PORT"""
        products = []
        
        try:
            # Debug inicial - verificar selectores múltiples (como en PORT)
            debug_selectors = [
                'div[class*="search-results"][class*="grid-pod"]',
                'div[class*="grid-pod"]', 
                'div[data-key]',
                'div[class*="pod"]'
            ]
            
            for selector in debug_selectors:
                test_containers = await page.query_selector_all(selector)
                self.logger.info(f"🔍 Debug selector '{selector}': {len(test_containers)} elementos")
            
            # Buscar contenedores usando múltiples patrones (como PORT)
            containers = []
            for selector in debug_selectors:
                found_containers = await page.query_selector_all(selector)
                if found_containers:
                    containers = found_containers
                    self.logger.info(f"✅ Usando selector '{selector}': {len(containers)} contenedores")
                    break
            
            self.logger.info(f"🔍 Falabella contenedores encontrados: {len(containers)}")
            
            for container in containers:
                try:
                    # Extraer ID y link principal (como PORT)
                    product_id = ""
                    product_link = ""
                    link_elem = await container.query_selector(FALABELLA_SELECTORS['product_link'])
                    if link_elem:
                        product_id = await link_elem.get_attribute('data-key') or ''
                        href = await link_elem.get_attribute('href') or ''
                        if href.startswith('/'):
                            product_link = f"https://www.falabella.com{href}"
                        elif href.startswith('http'):
                            product_link = href
                    
                    if not product_id:
                        continue  # Skip si no tiene ID
                    
                    # Extraer marca (del PORT: pod-title)
                    brand = ""
                    brand_elem = await container.query_selector(FALABELLA_SELECTORS['brand'])
                    if brand_elem:
                        brand = await brand_elem.inner_text()
                        brand = brand.strip()
                    
                    # Extraer nombre/descripción del producto (del PORT: pod-subTitle)
                    product_name = ""
                    name_elem = await container.query_selector(FALABELLA_SELECTORS['product_name'])
                    if name_elem:
                        product_name = await name_elem.inner_text()
                        product_name = product_name.strip()
                    
                    if not product_name:
                        continue  # Skip si no tiene nombre
                    
                    # Extraer precios (como PORT: data-cmr-price y data-internet-price)
                    cmr_price_text = ""
                    cmr_price_numeric = None
                    internet_price_text = ""
                    internet_price_numeric = None
                    
                    # Precio CMR
                    cmr_elem = await container.query_selector(FALABELLA_SELECTORS['cmr_price'])
                    if cmr_elem:
                        cmr_price_text = await cmr_elem.get_attribute('data-cmr-price') or ''
                        if cmr_price_text:
                            try:
                                cmr_price_numeric = int(float(cmr_price_text.replace(',', '')))
                            except:
                                pass
                    
                    # Precio Internet 
                    internet_elem = await container.query_selector(FALABELLA_SELECTORS['internet_price'])
                    if internet_elem:
                        internet_price_text = await internet_elem.get_attribute('data-internet-price') or ''
                        if internet_price_text:
                            try:
                                internet_price_numeric = int(float(internet_price_text.replace(',', '')))
                            except:
                                pass
                    
                    # Usar el precio que esté disponible
                    current_price_numeric = internet_price_numeric or cmr_price_numeric
                    current_price_text = internet_price_text or cmr_price_text
                    
                    # Extraer imagen
                    img_src = ""
                    img_elem = await container.query_selector(FALABELLA_SELECTORS['product_image'])
                    if img_elem:
                        img_src = await img_elem.get_attribute('src') or ''
                    
                    # Extraer rating (del PORT: data-rating)
                    rating_value = 0.0
                    rating_elem = await container.query_selector(FALABELLA_SELECTORS['rating'])
                    if rating_elem:
                        rating_attr = await rating_elem.get_attribute('data-rating') or '0'
                        try:
                            rating_value = float(rating_attr)
                        except:
                            rating_value = 0.0
                    
                    # Extraer vendedor (del PORT: pod-sellerText)
                    seller = ""
                    seller_elem = await container.query_selector(FALABELLA_SELECTORS['seller'])
                    if seller_elem:
                        seller = await seller_elem.inner_text()
                        seller = seller.strip()
                    
                    # Generar SKU único con product_id
                    product_sku = f"FALA_{product_id}" if product_id else f"FALA_{hash(product_name + str(current_price_numeric))}"
                    
                    # Extraer especificaciones usando regex (igual que PORT)
                    storage = ""
                    ram = ""
                    network = ""
                    color = ""
                    
                    product_name_lower = product_name.lower()
                    
                    # Storage (del PORT: (\d+)gb)
                    storage_match = re.search(r'(\d+)gb', product_name_lower)
                    if storage_match:
                        storage = f"{storage_match.group(1)}GB"
                    
                    # RAM (del PORT: (\d+)\+(\d+)gb)
                    ram_match = re.search(r'(\d+)\+(\d+)gb', product_name_lower)
                    if ram_match:
                        ram = f"{ram_match.group(1)}GB"
                        if not storage:  # Si no encontramos storage antes
                            storage = f"{ram_match.group(2)}GB"
                    
                    # Color (del PORT: lista de colores)
                    colors = ['negro', 'blanco', 'azul', 'rojo', 'verde', 'gris', 'dorado', 'plateado', 'purple', 'rosa']
                    for color_name in colors:
                        if color_name in product_name_lower:
                            color = color_name.title()
                            break
                    
                    # Solo agregar productos válidos (como PORT)
                    if product_id and product_name:
                        # Crear ProductData
                        product_data = ProductData(
                            title=product_name,
                            sku=product_sku,
                            brand=brand,
                            current_price=float(current_price_numeric) if current_price_numeric else 0.0,
                            original_price=float(cmr_price_numeric) if cmr_price_numeric and cmr_price_numeric != current_price_numeric else 0.0,
                            product_url=product_link,
                            image_urls=[img_src] if img_src else [],
                            rating=rating_value,
                            reviews_count=0,
                            retailer="falabella",
                            category="celulares",
                            additional_info={
                                'product_id': product_id,
                                'seller': seller,
                                'storage': storage,
                                'ram': ram,
                                'color': color,
                                'cmr_price': cmr_price_text,
                                'cmr_price_numeric': cmr_price_numeric,
                                'internet_price': internet_price_text,
                                'internet_price_numeric': internet_price_numeric,
                                'scraped_with': 'parallel_port_integrated'
                            }
                        )
                        
                        products.append(product_data)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando contenedor Falabella: {e}")
                    continue
            
            self.logger.info(f"✅ Falabella productos extraídos: {len(products)}")
            
        except Exception as e:
            self.logger.error(f"💥 Error extracción Falabella: {e}")
        
        return products

    async def _save_retailer_json(self, products: List[ProductData], session_id: str, execution_time: float):
        """💾 Guardar JSON específico para Falabella"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            retailer_dir = Path(__file__).parent.parent / "resultados_json" / self.retailer
            retailer_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{self.retailer}_productos_{timestamp}.json"
            filepath = retailer_dir / filename
            
            # Convertir a diccionarios
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
            
            # Crear estructura JSON
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
                        'avg_price': sum(p.get('current_price', 0) for p in products_data if p.get('current_price', 0) > 0) / len([p for p in products_data if p.get('current_price', 0) > 0]) if products_data else 0
                    },
                    'products_with_specs': len([p for p in products_data if p.get('additional_info', {}).get('storage')])
                }
            }
            
            # Guardar archivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Falabella JSON guardado: {filepath}")
            self.logger.info(f"📊 Resumen Falabella:")
            self.logger.info(f"   🏷️ Marcas: {len(json_data['extraction_summary']['brands_found'])} diferentes")
            self.logger.info(f"   💰 Rango precios: ${json_data['extraction_summary']['price_range']['min_price']:,.0f} - ${json_data['extraction_summary']['price_range']['max_price']:,.0f}")
            
        except Exception as e:
            self.logger.error(f"💥 Error guardando JSON Falabella: {e}")