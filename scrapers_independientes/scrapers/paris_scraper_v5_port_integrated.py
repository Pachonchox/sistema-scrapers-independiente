# -*- coding: utf-8 -*-
"""
🏬 Paris Chile Scraper v5 - INTEGRACIÓN COMPLETA PORT
====================================================

ESTE SCRAPER INTEGRA COMPLETAMENTE LA LÓGICA FUNCIONAL DEL scrappers_port/paris_final.py
QUE SÍ EXTRAE PRODUCTOS, ADAPTÁNDOLA AL SISTEMA V5 CON PLAYWRIGHT.

✅ CARACTERÍSTICAS INTEGRADAS DEL PORT:
- Selectores exactos que funcionan: div[data-cnstrc-item-id]
- Extracción de data attributes
- Parsing de precios con regex específico  
- Timing de scroll: 10s inicial + scroll completo + scroll a mitad
- Especificaciones técnicas (storage, RAM, network, color)
- Sistema de rating y reviews
- Enlaces e imágenes
- Estructura de datos completa

🎯 OBJETIVO: 100% funcionalidad PORT en arquitectura V5 Playwright
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

# Selector principal: div con data-cnstrc-item-id (el que SÍ FUNCIONA)
PRODUCT_CONTAINER_SELECTOR = 'div[data-cnstrc-item-id]'

# Selectores de precios (exactos del PORT)
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

# Regex exactos del PORT para especificaciones
SPECS_REGEX = {
    'storage': r'(\d+)gb(?!\s+ram)',  # Storage (no RAM)
    'ram': r'(\d+)gb\s+ram',         # RAM específico
    'network': r'(4g|5g)',           # Red móvil
    'color': r'(negro|blanco|azul|rojo|verde|gris|dorado|plateado|purpura|rosa)$'
}


class ParisScraperV5PortIntegrated(BaseScraperV5):
    """🏬 Scraper Paris V5 - LÓGICA PORT INTEGRADA COMPLETA"""
    
    def __init__(self):
        super().__init__("paris")
        
        # URLs exactas
        self.base_url = "https://www.paris.cl/tecnologia/celulares/"
        
        # Configuración de paginación centralizada
        self.pagination_config = self._load_pagination_config()
        
        # Configuración ULTRA-RÁPIDA optimizada
        self.config = {
            'initial_wait': 2,         # 2 segundos mínimos
            'scroll_wait': 1,          # 1 segundo después del scroll
            'mid_scroll_wait': 0.5,    # 0.5 segundos después del scroll a mitad
            'element_timeout': 3000,   # 3 segundos timeout por elemento
            'page_timeout': 30000,     # 30 segundos total optimizado
        }
        
        self.logger.info("🏬 Paris Scraper V5 - PORT INTEGRADO inicializado")

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
        """🔍 Scraper con lógica PORT COMPLETA integrada"""
        
        start_time = datetime.now()
        session_id = f"paris_port_{category}_{int(start_time.timestamp())}"
        
        page = None
        try:
            self.logger.info(f"🔍 Scraping Paris PORT INTEGRADO - {category}: {self.base_url}")
            
            # Obtener página
            page = await self.get_page()
            if not page:
                raise Exception("No se pudo obtener la página")
            
            # Scraping con paginación usando configuración centralizada
            products = await self._scrape_with_pagination_port(page, max_products)
            
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
                    'scraping_method': 'port_logic_integrated',
                    'port_compatibility': True,
                    'extraction_method': 'playwright_port_selectors',
                    'success_rate': f"{len(products)}/{max_products}",
                    'pagination_used': len(self.pagination_config) > 0
                }
            )
            
            # Guardar JSON COMPLETO (esperando a que termine)
            await self._save_retailer_json_complete(products, session_id, execution_time)
            
            self.logger.info(f"✅ Paris PORT INTEGRADO completado: {len(products)} productos en {execution_time:.1f}s")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"❌ Error Paris PORT INTEGRADO categoría {category}: {e}")
            
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
                metadata={'error_type': type(e).__name__, 'scraping_method': 'port_logic_integrated'}
            )
        
        finally:
            # Limpiar recursos de forma segura
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def _scrape_with_pagination_port(self, initial_page: Page, max_products: int) -> List[ProductData]:
        """📦 Scraping PARALELO con 5 páginas simultáneas + detección automática + guardado periódico"""
        
        all_products = []
        current_batch_start = 1
        consecutive_empty_batches = 0
        
        # Configuración de detección de fin (desde config.json)
        max_empty_pages = self.pagination_config.get('empty_page_threshold', 2) if self.pagination_config else 2
        min_products_per_page = self.pagination_config.get('min_products_per_page', 5) if self.pagination_config else 5
        max_pages_config = self.pagination_config.get('max_pages', 999) if self.pagination_config else 999
        auto_stop_enabled = self.pagination_config.get('auto_stop', True) if self.pagination_config else True
        
        # Configuración de paralelismo
        batch_size = 5  # 5 páginas simultáneas
        
        self.logger.info(f"🚀 Iniciando paginación PARALELA:")
        self.logger.info(f"   📄 Max páginas: {max_pages_config}")
        self.logger.info(f"   ⚡ Páginas paralelas: {batch_size}")
        self.logger.info(f"   🔚 Auto-stop: {'Activado' if auto_stop_enabled else 'Desactivado'}")
        self.logger.info(f"   ⚠️ Threshold páginas vacías: {max_empty_pages}")
        
        while len(all_products) < max_products and current_batch_start <= max_pages_config:
            # Preparar lote de páginas para procesar en paralelo
            batch_pages = []
            for i in range(batch_size):
                page_num = current_batch_start + i
                if page_num > max_pages_config:
                    break
                batch_pages.append(page_num)
            
            if not batch_pages:
                break
            
            self.logger.info(f"🚀 Procesando lote PARALELO páginas {batch_pages[0]} a {batch_pages[-1]}")
            
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
                    self.logger.info(f"✅ Página {page_num}: {len(page_products)} productos")
            
            self.logger.info(f"📊 Lote completado: {batch_total_products} productos de {len(batch_pages)} páginas")
            
            # Verificar condiciones de fin
            if auto_stop_enabled:
                # Si todas las páginas del lote están vacías
                if empty_pages_in_batch == len(batch_pages):
                    consecutive_empty_batches += 1
                    self.logger.warning(f"⚠️ Lote completamente vacío ({consecutive_empty_batches})")
                    
                    if consecutive_empty_batches >= 2:  # 2 lotes vacíos = terminar
                        self.logger.info("🔚 2 lotes vacíos consecutivos, terminando")
                        break
                else:
                    consecutive_empty_batches = 0
                
                # Verificar límite de productos
                if len(all_products) >= max_products:
                    self.logger.info(f"🎯 Límite alcanzado: {len(all_products)}/{max_products}")
                    break
            
            # 💾 Guardado periódico cada 10 lotes para prevenir pérdida de datos
            if len(all_products) > 0 and (current_batch_start % 50 == 1):  # Cada 50 páginas
                try:
                    import time
                    current_time = time.time()
                    await self._save_retailer_json_complete(all_products, f"periodic_{current_batch_start}", current_time)
                    self.logger.info(f"💾 Guardado periódico: {len(all_products)} productos salvados")
                except Exception as save_error:
                    self.logger.error(f"⚠️ Error en guardado periódico: {save_error}")
            
            # Siguiente lote
            current_batch_start += batch_size
            
            # Pausa mínima entre lotes
            await asyncio.sleep(0.1)
        
        # 🛡️ Guardado final SEGURO - Asegurar que TODOS los productos se guarden
        if len(all_products) > 0:
            try:
                import time
                final_time = time.time()
                await self._save_retailer_json_complete(all_products, f"final_{len(all_products)}", final_time)
                self.logger.info(f"💾 GUARDADO FINAL EXITOSO: {len(all_products)} productos")
            except Exception as final_save_error:
                self.logger.error(f"🚨 ERROR CRÍTICO en guardado final: {final_save_error}")
                # Intentar guardado de emergencia
                try:
                    emergency_filename = f"paris_emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    emergency_data = {
                        "total_products": len(all_products),
                        "products": [prod.to_dict() for prod in all_products],
                        "emergency_save": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    import json
                    with open(emergency_filename, 'w', encoding='utf-8') as f:
                        json.dump(emergency_data, f, ensure_ascii=False, indent=2)
                    self.logger.warning(f"⚠️ Guardado de emergencia en: {emergency_filename}")
                except:
                    self.logger.error("🚨 FALLO TOTAL del guardado - datos perdidos")
        
        # Limitar resultados finales
        final_products = all_products[:max_products]
        
        self.logger.info(f"📦 Paginación PARALELA completada:")
        self.logger.info(f"   📄 Páginas procesadas: hasta {current_batch_start - 1}")
        self.logger.info(f"   ⚡ Lotes procesados: {(current_batch_start - 1) // batch_size}")
        self.logger.info(f"   🎯 Productos extraídos: {len(final_products)}")
        self.logger.info(f"   🔚 Razón de fin: {'Límite alcanzado' if len(all_products) >= max_products else 'No más productos'}")
        
        return final_products

    async def _process_pages_parallel(self, page_numbers: List[int]) -> List[tuple]:
        """🚀 Procesar múltiples páginas en paralelo usando asyncio.gather"""
        
        # Crear tareas para cada página
        tasks = []
        for page_num in page_numbers:
            task = asyncio.create_task(self._scrape_single_page(page_num))
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados y manejar excepciones
        processed_results = []
        for i, result in enumerate(results):
            page_num = page_numbers[i]
            
            if isinstance(result, Exception):
                error_msg = str(result)
                if 'ERR_ABORTED' in error_msg:
                    self.logger.warning(f"🔄 Página {page_num} ERR_ABORTED - continuando con otras")
                else:
                    self.logger.error(f"❌ Error página {page_num}: {result}")
                processed_results.append((page_num, None))
            else:
                processed_results.append((page_num, result))
        
        return processed_results

    async def _scrape_single_page(self, page_num: int) -> tuple:
        """📄 Scraper una página individual (para usar en paralelo)"""
        
        page = None
        try:
            # Crear nueva página para esta tarea
            page = await self.get_page()
            if not page:
                return ([], "error")
            
            # Construir URL
            page_url = self._build_page_url_centralized(page_num)
            
            # Navegar a la página con manejo mejorado de ERR_ABORTED
            navigation_result = await self._navigate_with_error_detection(page, page_url)
            if not navigation_result:
                # Distinguir entre ERR_ABORTED (seguir) vs otros errores (detener)
                self.logger.info(f"🔄 Navegación falló en página {page_num} - marcando como vacía")
                return ([], "empty")  # Marcar como vacía en lugar de error para continuar
            
            # Verificar si es redirección a página principal
            current_url = page.url
            if page_num > 1 and current_url == self.base_url:
                self.logger.info(f"🔚 Página {page_num} redirigió a principal")
                return ([], "empty")
            
            # Aplicar timing optimizado
            await self._apply_port_timing(page)
            
            # Extraer productos
            page_products = await self._extract_products_port_logic(page)
            
            if len(page_products) == 0:
                return ([], "empty")
            
            return (page_products, "success")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error página {page_num}: {e}")
            return ([], "error")
        
        finally:
            # Cerrar página específica
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def _save_retailer_json(self, products: List[ProductData], session_id: str, execution_time: float):
        """💾 Guardar resultados en JSON específico por retailer con timestamp"""
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
                'extraction_method': 'port_logic_integrated_v5',
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
                    'discounts_found': len([p for p in products_data if p.get('additional_info', {}).get('discount_percent')]),
                    'products_with_specs': len([p for p in products_data if p.get('additional_info', {}).get('storage')])
                }
            }
            
            # Guardar archivo JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 JSON guardado: {filepath}")
            self.logger.info(f"📊 Resumen guardado:")
            self.logger.info(f"   🏷️ Marcas: {len(json_data['extraction_summary']['brands_found'])} diferentes")
            self.logger.info(f"   💰 Rango precios: ${json_data['extraction_summary']['price_range']['min_price']:,.0f} - ${json_data['extraction_summary']['price_range']['max_price']:,.0f}")
            self.logger.info(f"   🏷️ Descuentos: {json_data['extraction_summary']['discounts_found']} productos")
            
        except Exception as e:
            self.logger.error(f"💥 Error guardando JSON específico: {e}")

    async def _navigate_with_error_detection(self, page: Page, url: str) -> bool:
        """🧭 Navegación con detección de errores y páginas inválidas + manejo ERR_ABORTED"""
        try:
            response = await page.goto(url, wait_until='domcontentloaded', timeout=self.config['page_timeout'])
            
            # Verificar códigos de error HTTP
            if response and response.status >= 400:
                self.logger.warning(f"⚠️ Código HTTP {response.status} en {url}")
                if response.status == 404:
                    self.logger.info("🔚 Página 404 - fin de páginas alcanzado")
                    return False
                elif response.status >= 500:
                    self.logger.warning("🔄 Error del servidor, intentando continuar...")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            # Manejar específicamente errores ERR_ABORTED
            if 'ERR_ABORTED' in error_msg:
                self.logger.warning(f"🔄 ERR_ABORTED detectado en {url} - continuando con otras páginas")
                # No retornar False para ERR_ABORTED, permitir continuar
                return False  # Esta página falló pero no detenemos el proceso completo
            
            # Manejar otros errores de timeout/navegación
            elif 'timeout' in error_msg.lower() or 'net::' in error_msg:
                self.logger.warning(f"🔄 Error de red en {url}: {error_msg} - continuando")
                return False  # Esta página falló pero seguimos
            
            # Otros errores más graves
            else:
                self.logger.error(f"💥 Error crítico navegando a {url}: {e}")
                return False

    async def _detect_end_of_pages(self, page: Page, page_num: int) -> bool:
        """🔚 Detectar indicadores de fin de páginas usando múltiples estrategias"""
        try:
            # Estrategia 1: Detectar mensajes de "no hay más resultados"
            no_results_selectors = [
                'div:has-text("No se encontraron productos")',
                'div:has-text("No hay más resultados")',
                'div:has-text("Sin resultados")',
                '.no-results',
                '.empty-results',
                '[data-testid*="no-results"]',
                'div:has-text("0 productos")'
            ]
            
            for selector in no_results_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        self.logger.info(f"🔚 Mensaje de fin detectado: '{text.strip()}'")
                        return True
                except:
                    continue
            
            # Estrategia 2: Detectar URL de redirección a página principal
            current_url = page.url
            if 'page=' not in current_url and page_num > 1:
                self.logger.info(f"🔄 Redirección detectada a página principal desde página {page_num}")
                return True
            
            # Estrategia 3: Detectar títulos de página que indican fin
            try:
                title = await page.title()
                end_titles = ['404', 'página no encontrada', 'error']
                if any(end_title in title.lower() for end_title in end_titles):
                    self.logger.info(f"🔚 Título de fin detectado: '{title}'")
                    return True
            except:
                pass
            
            # Estrategia 4: Detectar controles de paginación
            pagination_indicators = await self._check_pagination_controls(page, page_num)
            if pagination_indicators:
                return True
                
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en detección de fin: {e}")
            return False

    async def _check_pagination_controls(self, page: Page, current_page: int) -> bool:
        """📄 Verificar controles de paginación para detectar fin"""
        try:
            # Buscar controles de paginación comunes
            pagination_selectors = [
                '.pagination',
                '[data-testid*="pagination"]',
                '.page-numbers',
                '.pager',
                'nav[aria-label*="paginación"]',
                'nav[aria-label*="pagination"]'
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination = await page.query_selector(selector)
                    if pagination:
                        # Buscar botón "siguiente" deshabilitado
                        next_disabled = await pagination.query_selector('button[disabled]:has-text("Siguiente"), a[disabled]:has-text("Siguiente"), .disabled:has-text("Siguiente")')
                        if next_disabled:
                            self.logger.info("🔚 Botón 'Siguiente' deshabilitado - fin de páginas")
                            return True
                        
                        # Verificar si la página actual es la máxima visible
                        page_numbers = await pagination.query_selector_all('a, button')
                        if page_numbers:
                            max_page = 0
                            for page_elem in page_numbers:
                                try:
                                    text = await page_elem.inner_text()
                                    if text.isdigit():
                                        max_page = max(max_page, int(text))
                                except:
                                    continue
                            
                            if max_page > 0 and current_page >= max_page:
                                self.logger.info(f"🔚 Página actual ({current_page}) >= máxima visible ({max_page})")
                                return True
                        
                        break
                except:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando controles de paginación: {e}")
            return False

    async def _verify_next_page_empty(self, page: Page, next_page_num: int) -> bool:
        """🔍 Verificar si la próxima página está vacía (sin navegar completamente)"""
        try:
            # Construir URL de la próxima página
            next_url = self._build_page_url_centralized(next_page_num)
            
            # Hacer una verificación rápida (HEAD request simulado)
            current_url = page.url
            
            # Navegación rápida sin timing completo
            try:
                await page.goto(next_url, wait_until='domcontentloaded', timeout=10000)
                await asyncio.sleep(2)  # Espera mínima
                
                # Verificar si hay contenedores de productos
                containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
                is_empty = len(containers) == 0
                
                # Volver a la página anterior
                await page.goto(current_url, wait_until='domcontentloaded', timeout=10000)
                
                return is_empty
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error verificando página {next_page_num}: {e}")
                return True  # Asumir vacía si hay error
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error en verificación de página siguiente: {e}")
            return False

    async def _detect_duplicate_pattern(self, products: List[ProductData]) -> bool:
        """🔄 Detectar patrones de productos duplicados (posible loop)"""
        try:
            if len(products) < 20:  # No hay suficientes productos para detectar patrones
                return False
            
            # Obtener últimos 20 productos
            recent_products = products[-20:]
            skus = [p.sku for p in recent_products if p.sku]
            
            # Verificar si hay más de 50% duplicados en los últimos productos
            if len(skus) > 10:
                unique_skus = set(skus)
                duplicate_ratio = 1 - (len(unique_skus) / len(skus))
                
                if duplicate_ratio > 0.5:
                    self.logger.warning(f"🔄 Alto ratio de duplicados detectado: {duplicate_ratio:.1%}")
                    return True
            
            # Verificar patrones de repetición en los últimos 10 productos
            if len(products) >= 10:
                last_10_skus = [p.sku for p in products[-10:] if p.sku]
                first_10_skus = [p.sku for p in products[:10] if p.sku]
                
                if len(last_10_skus) >= 5 and len(first_10_skus) >= 5:
                    common = set(last_10_skus) & set(first_10_skus)
                    if len(common) >= 3:
                        self.logger.warning(f"🔄 Patrón de repetición detectado: {len(common)} SKUs comunes")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error detectando duplicados: {e}")
            return False

    def _build_page_url_centralized(self, page_num: int) -> str:
        """🔗 Construir URL específica para Paris con lógica correcta"""
        try:
            # LÓGICA ESPECÍFICA PARA PARIS:
            # Página 1: https://www.paris.cl/tecnologia/celulares/ (sin parámetros)
            # Página 2+: https://www.paris.cl/tecnologia/celulares/?page=2
            
            if page_num <= 1:
                # Página 1: URL base sin parámetros
                return self.base_url
            else:
                # Página 2+: agregar ?page=X
                base_clean = self.base_url.rstrip('/')  # Quitar / final si existe
                return f"{base_clean}/?page={page_num}"
            
        except Exception as e:
            self.logger.error(f"💥 Error construyendo URL de página: {e}")
            # Fallback seguro
            if page_num <= 1:
                return self.base_url
            else:
                base_clean = self.base_url.rstrip('/')
                return f"{base_clean}/?page={page_num}"

    async def _apply_port_timing(self, page: Page):
        """⚡ ULTRA-RÁPIDO: Timing mínimo optimizado para velocidad"""
        try:
            # 1. Espera mínima hasta detectar contenedores
            self.logger.info("⚡ MODO ULTRA-RÁPIDO: Carga mínima...")
            
            # Esperar máximo 3 segundos para contenedores iniciales
            for _ in range(6):  # 6 x 0.5s = 3s máximo
                containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
                if len(containers) >= 3:  # Solo 3 productos mínimos
                    self.logger.info(f"⚡ Carga detectada: {len(containers)} contenedores")
                    break
                await asyncio.sleep(0.5)
            
            # 2. Scroll rápido único al final
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)  # Solo 1 segundo
            
            # 3. Scroll final a media página
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
            await asyncio.sleep(0.5)  # Solo medio segundo
            
            final_count = len(await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR))
            self.logger.info(f"⚡ RÁPIDO: {final_count} contenedores listos")
            
        except Exception as e:
            self.logger.error(f"💥 Error timing rápido: {e}")
            # Fallback súper rápido
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)

    async def _extract_products_port_logic(self, page: Page) -> List[ProductData]:
        """📊 Extraer productos usando lógica EXACTA del PORT"""
        products = []
        
        try:
            # Buscar contenedores con data-cnstrc-item-id (selector PORT)
            containers = await page.query_selector_all(PRODUCT_CONTAINER_SELECTOR)
            
            self.logger.info(f"🔍 Contenedores con data-cnstrc-item-id encontrados: {len(containers)}")
            
            for container in containers:
                try:
                    # Extraer información desde data attributes (como PORT)
                    product_code = await container.get_attribute('data-cnstrc-item-id') or ''
                    product_name = await container.get_attribute('data-cnstrc-item-name') or ''
                    price_from_data = await container.get_attribute('data-cnstrc-item-price') or ''
                    
                    product_name = product_name.strip()
                    
                    # Filtro de productos válidos
                    if not product_code or not product_name:
                        continue
                    
                    # Buscar link del producto
                    product_link = ""
                    link_element = await container.query_selector('a[href]')
                    if link_element:
                        href = await link_element.get_attribute('href') or ''
                        if href.startswith('/'):
                            product_link = f"https://www.paris.cl{href}"
                        elif href.startswith('http'):
                            product_link = href
                    
                    # Extraer precios usando selectores PORT
                    current_price_text = ""
                    current_price_numeric = None
                    old_price_text = ""
                    old_price_numeric = None
                    discount_percent = ""
                    
                    # Precio actual
                    current_price_elem = await container.query_selector(PRICE_SELECTORS['current_price'])
                    if current_price_elem:
                        current_price_text = await current_price_elem.inner_text()
                        current_price_text = current_price_text.strip()
                        price_match = re.search(r'\$?([\d.,]+)', current_price_text.replace('.', ''))
                        if price_match:
                            try:
                                current_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
                    
                    # Precio anterior (con descuento)
                    old_price_elem = await container.query_selector(PRICE_SELECTORS['old_price'])
                    if old_price_elem:
                        old_price_text = await old_price_elem.inner_text()
                        old_price_text = old_price_text.strip()
                        price_match = re.search(r'\$?([\d.,]+)', old_price_text.replace('.', ''))
                        if price_match:
                            try:
                                old_price_numeric = int(price_match.group(1).replace(',', ''))
                            except:
                                pass
                    
                    # Descuento
                    discount_elem = await container.query_selector(PRICE_SELECTORS['discount'])
                    if discount_elem:
                        discount_percent = await discount_elem.get_attribute('aria-label') or ''
                    
                    # Marca
                    brand = ""
                    brand_elem = await container.query_selector(PRICE_SELECTORS['brand'])
                    if brand_elem:
                        brand = await brand_elem.inner_text()
                        brand = brand.strip()
                    
                    # Imagen
                    img_src = ""
                    img_element = await container.query_selector(METADATA_SELECTORS['product_image'])
                    if img_element:
                        # Obtener imagen de mayor resolución del srcset
                        srcset = await img_element.get_attribute('srcset') or ''
                        if srcset:
                            urls = re.findall(r'(https://[^\s]+)', srcset)
                            img_src = urls[-1] if urls else (await img_element.get_attribute('src') or '')
                        else:
                            img_src = await img_element.get_attribute('src') or ''
                    
                    # Rating y reviews
                    rating = "0"
                    rating_elem = await container.query_selector(PRICE_SELECTORS['rating_value'])
                    if rating_elem:
                        rating = await rating_elem.inner_text()
                        rating = rating.strip()
                    
                    reviews = "0"
                    reviews_elem = await container.query_selector(PRICE_SELECTORS['rating_count'])
                    if reviews_elem:
                        reviews = await reviews_elem.inner_text()
                        reviews = reviews.strip().replace('(', '').replace(')', '')
                    
                    # Extraer especificaciones usando regex PORT
                    storage = ""
                    ram = ""
                    network = ""
                    color = ""
                    
                    product_name_lower = product_name.lower()
                    
                    # Storage (primer número + GB que no sea RAM)
                    storage_match = re.search(SPECS_REGEX['storage'], product_name_lower)
                    if storage_match:
                        storage = f"{storage_match.group(1)}GB"
                    
                    # RAM
                    ram_match = re.search(SPECS_REGEX['ram'], product_name_lower)
                    if ram_match:
                        ram = f"{ram_match.group(1)}GB"
                    
                    # Red móvil
                    network_match = re.search(SPECS_REGEX['network'], product_name_lower)
                    if network_match:
                        network = network_match.group(1).upper()
                    
                    # Color
                    color_match = re.search(SPECS_REGEX['color'], product_name_lower)
                    if color_match:
                        color = color_match.group(1).title()
                    
                    # Crear ProductData con estructura V5
                    product_data = ProductData(
                        title=product_name,
                        sku=product_code,
                        brand=brand,
                        current_price=float(current_price_numeric) if current_price_numeric else 0.0,
                        original_price=float(old_price_numeric) if old_price_numeric else 0.0,
                        product_url=product_link,
                        image_urls=[img_src] if img_src else [],
                        rating=float(rating) if rating.replace('.', '').isdigit() else 0.0,
                        reviews_count=int(reviews) if reviews.isdigit() else 0,
                        retailer="paris",
                        category="celulares",
                        additional_info={
                            'storage': storage,
                            'ram': ram,
                            'network': network,
                            'color': color,
                            'discount_percent': discount_percent,
                            'current_price_text': current_price_text,
                            'old_price_text': old_price_text,
                            'price_from_data': price_from_data,
                            'scraped_with': 'port_logic_integrated'
                        }
                    )
                    
                    products.append(product_data)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando contenedor: {e}")
                    continue
            
            self.logger.info(f"✅ Productos extraídos con lógica PORT: {len(products)}")
            
        except Exception as e:
            self.logger.error(f"💥 Error en extracción PORT: {e}")
        
        return products

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
                'extraction_method': 'port_logic_integrated_v5',
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
                    'discounts_found': len([p for p in products_data if p.get('additional_info', {}).get('discount_percent')]),
                    'products_with_specs': len([p for p in products_data if p.get('additional_info', {}).get('storage')])
                }
            }
            
            # Guardar archivo JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 JSON guardado COMPLETO: {filepath}")
            self.logger.info(f"📊 Resumen guardado:")
            self.logger.info(f"   🏷️ Marcas: {len(json_data['extraction_summary']['brands_found'])} diferentes")
            self.logger.info(f"   💰 Rango precios: ${json_data['extraction_summary']['price_range']['min_price']:,.0f} - ${json_data['extraction_summary']['price_range']['max_price']:,.0f}")
            self.logger.info(f"   🎯 Total productos guardados: {len(products_data)}")
            
        except Exception as e:
            self.logger.error(f"💥 Error guardando JSON completo: {e}")
            import traceback
            self.logger.error(traceback.format_exc())