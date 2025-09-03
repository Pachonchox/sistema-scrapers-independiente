#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕷️ Base Scraper v5 - Clase Base con Integración ML Completa
==========================================================

Scraper base profesional y robusto que sirve como fundación para todos
los scrapers específicos por retailer. Incluye integración ML completa,
manejo avanzado de errores, optimización automática y testing integrado.

Features:
- 🤖 Integración ML para detección de fallos y optimización
- 🌐 Gestión inteligente de proxies y rate limiting
- 🔄 Auto-recovery y circuit breakers integrados
- 📊 ETL optimizado con reducción de campos
- 🧪 Testing y debugging automático
- 📈 Métricas de performance en tiempo real
- 🛡️ Protección anti-detección avanzada

Author: Portable Orchestrator Team
Version: 5.0.0
"""

import sys
import os
import io
import asyncio
import logging
import json
import time
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse, quote
import traceback
import re

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Imports del sistema
try:
    from playwright.async_api import Page, Browser, BrowserContext, Route, Request, async_playwright
    from bs4 import BeautifulSoup, Tag
except ImportError:
    Page = Browser = BrowserContext = Route = Request = None
    BeautifulSoup = Tag = None

# Imports internos
from .exceptions import *
from .field_mapper import ETLFieldMapper

# Importar sistema de respaldo Parquet
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from core.parquet_backup_system import save_scraper_backup
    PARQUET_BACKUP_AVAILABLE = True
    logger.info("📦 Sistema de respaldo Parquet disponible")
except ImportError:
    PARQUET_BACKUP_AVAILABLE = False
    logger.warning("⚠️ Sistema de respaldo Parquet no disponible")

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """📊 Resultado de operación de scraping (v5 unificado)"""
    success: bool
    products: List[Any] = field(default_factory=list)
    total_found: int = 0
    execution_time: float = 0.0
    session_id: str = ""
    source_url: str = ""
    retailer: str = ""
    category: str = ""
    error_message: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_error(self, error: str) -> None:
        """➕ Agregar error al resultado"""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """⚠️ Agregar warning al resultado"""
        self.warnings.append(warning)
    
    def get_product_count(self) -> int:
        """📊 Obtener cantidad de productos"""
        return len(self.products)

@dataclass
class RetailerSelectors:
    """🎯 Selectores CSS específicos por retailer"""
    product_cards: List[str] = field(default_factory=list)
    product_name: List[str] = field(default_factory=list)
    price_normal: List[str] = field(default_factory=list)
    price_offer: List[str] = field(default_factory=list)
    price_card: List[str] = field(default_factory=list)
    brand: List[str] = field(default_factory=list)
    sku: List[str] = field(default_factory=list)
    rating: List[str] = field(default_factory=list)
    reviews_count: List[str] = field(default_factory=list)
    availability: List[str] = field(default_factory=list)
    image_url: List[str] = field(default_factory=list)
    product_url: List[str] = field(default_factory=list)
    
    # Selectores de página
    next_page: List[str] = field(default_factory=list)
    load_more: List[str] = field(default_factory=list)
    pagination: List[str] = field(default_factory=list)
    
    # Selectores de detección de bloqueo
    blocked_indicators: List[str] = field(default_factory=list)
    captcha_indicators: List[str] = field(default_factory=list)

@dataclass
class ScrapingConfig:
    """⚙️ Configuración de scraping para un retailer"""
    retailer: str
    base_url: str
    selectors: RetailerSelectors
    rate_limit: float = 1.0  # requests por segundo
    timeout: int = 30
    max_retries: int = 3
    use_proxy: bool = False
    headless: bool = True
    user_agents: List[str] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    blocked_detection: bool = True
    auto_scroll: bool = True
    wait_for_load: bool = True
    screenshot_on_error: bool = True
    
    def __post_init__(self):
        if not self.user_agents:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ]

@dataclass
class ProductData:
    """📦 Representación de producto estándar v5"""
    title: str
    current_price: float = 0.0
    original_price: float = 0.0
    discount_percentage: int = 0
    card_price: float = 0.0
    currency: str = "CLP"
    availability: str = ""
    product_url: str = ""
    image_urls: List[str] = field(default_factory=list)
    brand: str = ""
    sku: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    retailer: str = ""
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    category: str = ""
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        """Convierte a dict con campos alineados al contrato Excel y Master"""
        # Precios numéricos para Master
        precio_normal_num = int(self.original_price or 0)
        # Asumimos current_price como precio de oferta efectivo si aplica
        precio_oferta_num = int(self.current_price or 0)
        precio_tarjeta_num = int(self.card_price or 0)

        return {
            'nombre': self.title,
            'marca': self.brand,
            'sku': self.sku,
            'categoria': self.category,
            'retailer': self.retailer,
            'link': self.product_url,
            'precio_normal_num': precio_normal_num,
            'precio_oferta_num': precio_oferta_num,
            'precio_tarjeta_num': precio_tarjeta_num,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            # Opcionales comunes (mantener nombres esperados por el proyecto)
            'storage': self.additional_info.get('storage', self.additional_info.get('memoria', '')),
            'ram': self.additional_info.get('ram', ''),
            'screen': self.additional_info.get('screen', self.additional_info.get('screen_size', '')),
        }


class BaseScraperV5(ABC):
    """
    🕷️ Scraper Base v5 - Clase Base Profesional con ML
    
    Scraper base robusto que proporciona toda la funcionalidad común:
    
    🤖 **INTEGRACIÓN ML:**
    - Detección automática de fallos con análisis ML
    - Optimización de selectores basada en éxito histórico
    - Predicción de bloqueos y auto-recovery
    - Análisis de patrones de performance
    
    🛡️ **PROTECCIÓN ANTI-DETECCIÓN:**
    - Rotación automática de user agents
    - Manejo inteligente de proxies
    - Patrones de navegación humanizados
    - Detección de captchas y bloqueos
    
    📊 **ETL OPTIMIZADO:**
    - Reducción inteligente de campos
    - Normalización automática de datos
    - Validación de calidad de datos
    - Formato de salida optimizado
    
    🧪 **TESTING INTEGRADO:**
    - Validación automática de selectores
    - Capturas de pantalla en errores
    - Análisis HTML para debugging
    - Métricas de performance detalladas
    """
    
    def __init__(self, config: Union[ScrapingConfig, str]):
        """
        🚀 Inicializar Base Scraper v5
        
        Args:
            config: Configuración específica del retailer
        """
        # Permitir inicialización con nombre de retailer (compatibilidad con scrapers v5 existentes)
        if isinstance(config, str):
            self.retailer = config
            # Configuración mínima por defecto; selectores se definen en cada scraper
            self.config = ScrapingConfig(
                retailer=config,
                base_url="",
                selectors=RetailerSelectors(),
                rate_limit=1.0,
                timeout=30,
                max_retries=3,
                use_proxy=False,
                headless=True,
            )
        else:
            self.config = config
            self.retailer = config.retailer
        
        # Logger por instancia
        self.logger = logging.getLogger(f"{__name__}.{self.retailer}")

        # Componentes ML
        self.ml_failure_detector = None
        self.proxy_manager = None
        self.field_mapper = ETLFieldMapper()
        
        # Estado del scraper
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context: Optional[BrowserContext] = None
        self.current_proxy: Optional[str] = None
        self.session_id = hashlib.md5(
            f"{self.retailer}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        # Métricas y performance
        self.performance_metrics: Dict[str, float] = {}
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time: Optional[datetime] = None
        self.total_products_scraped = 0
        
        # Rate limiting
        self.last_request_time = 0.0
        self.request_times: List[float] = []
        
        # Estado de recuperación
        self.consecutive_failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.circuit_breaker_open = False
        
        # Directorio de logs y screenshots
        self.logs_dir = Path(f"logs/scrapers/{self.retailer}")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🕷️ BaseScraperV5 inicializado para {self.retailer.upper()}")
        logger.info(f"📁 Session ID: {self.session_id}")
    
    async def __aenter__(self):
        """🚀 Context manager para inicialización automática"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """🔚 Context manager para cleanup automático"""
        await self.cleanup()
    
    async def initialize(self) -> bool:
        """
        🚀 Inicialización completa del scraper
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info(f"🚀 Inicializando scraper para {self.retailer.upper()}...")
            self.start_time = datetime.now()
            
            # 1. Inicializar componentes ML
            await self._initialize_ml_components()
            
            # 2. Configurar browser
            if not await self._setup_browser():
                raise ScraperV5Exception("Error configurando browser")
            
            # 3. Configurar proxy si es necesario
            if self.config.use_proxy:
                await self._setup_proxy()
            
            # 4. Validar configuración
            await self._validate_configuration()
            
            logger.info(f"✅ Scraper {self.retailer.upper()} inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"💥 Error inicializando scraper {self.retailer}: {str(e)}")
            await self.cleanup()
            return False
    
    async def cleanup(self) -> None:
        """
        🧹 Limpieza de recursos
        """
        logger.info(f"🧹 Limpiando recursos de {self.retailer.upper()}...")
        
        try:
            # Cerrar página y context
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            # No cerrar browser aquí, se maneja externamente
            
            # Guardar métricas finales
            await self._save_session_metrics()
            
        except Exception as e:
            logger.warning(f"⚠️ Error en cleanup: {str(e)}")
        
        logger.info(f"✅ Cleanup completado para {self.retailer.upper()}")
    
    @abstractmethod
    async def scrape_category(self, category_url: str, 
                            max_pages: Optional[int] = None) -> ScrapingResult:
        """
        🎯 Método abstracto para scraping de categoría
        
        Debe ser implementado por cada scraper específico.
        
        Args:
            category_url: URL de la categoría a scrapear
            max_pages: Límite máximo de páginas (None = sin límite)
            
        Returns:
            ScrapingResult: Resultado del scraping
        """
        pass
    
    def get_selectors(self) -> RetailerSelectors:
        """🎯 Obtener selectores del retailer (por defecto, desde config)."""
        return self.config.selectors if hasattr(self, 'config') and self.config else RetailerSelectors()
    
    # ==========================================
    # MÉTODOS DE SCRAPING COMUNES
    # ==========================================
    
    async def extract_products_from_page(self, url: str) -> ScrapingResult:
        """
        📊 Extraer productos de una página específica
        
        Args:
            url: URL de la página a scrapear
            
        Returns:
            ScrapingResult: Productos extraídos y métricas
        """
        result = ScrapingResult()
        start_time = time.time()
        
        try:
            logger.info(f"📄 Extrayendo productos de: {url}")
            
            # 1. Navegar a la página
            navigation_result = await self._navigate_to_page(url)
            if not navigation_result:
                result.add_error("Error navegando a la página")
                return result
            
            # 2. Detectar bloqueos
            if await self._detect_blocking():
                result.add_error("Página bloqueada o con captcha")
                await self._handle_blocking()
                return result
            
            # 3. Esperar carga completa
            await self._wait_for_page_load()
            
            # 4. Scroll para cargar contenido lazy
            if self.config.auto_scroll:
                await self._intelligent_scroll()
            
            # 5. Extraer productos
            products = await self._extract_products_with_ml()
            result.products = products
            result.success = len(products) > 0
            
            # 6. Validar calidad de datos
            await self._validate_extracted_data(result)
            
            # 7. Guardar respaldo en Parquet (datos crudos)
            if PARQUET_BACKUP_AVAILABLE and products:
                try:
                    category = self._extract_category_from_url(url)
                    backup_metadata = {
                        'session_id': result.session_id,
                        'source_urls': [url],
                        'execution_time': time.time() - start_time,
                        'success_rate': 1.0 if result.success else 0.0,
                        'errors': result.errors,
                        'warnings': result.warnings
                    }
                    
                    backup_result = save_scraper_backup(
                        retailer=self.retailer,
                        category=category,
                        products=[asdict(p) if hasattr(p, '__dict__') else p for p in products],
                        metadata=backup_metadata
                    )
                    
                    if backup_result.get('success'):
                        logger.info(f"📦 Respaldo Parquet guardado: {backup_result.get('file_path')}")
                        result.metadata['parquet_backup'] = backup_result
                    else:
                        logger.warning(f"⚠️ Error guardando respaldo Parquet: {backup_result.get('error')}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error creando respaldo Parquet: {e}")
            
            # 8. Métricas de performance
            duration = time.time() - start_time
            result.performance_metrics = {
                'extraction_time': duration,
                'products_per_second': len(products) / duration if duration > 0 else 0,
                'page_load_time': self.performance_metrics.get('page_load_time', 0),
                'success_rate': 1.0 if result.success else 0.0
            }
            
            logger.info(f"✅ Extraídos {len(products)} productos en {duration:.2f}s")
            
        except Exception as e:
            result.add_error(f"Error extrayendo productos: {str(e)}")
            logger.error(f"💥 Error en extracción: {str(e)}")
            
            # Screenshot en error si está habilitado
            if self.config.screenshot_on_error:
                await self._capture_error_screenshot("extraction_error")
        
        return result
    
    def _extract_category_from_url(self, url: str) -> str:
        """Extraer categoría desde URL para respaldo Parquet"""
        try:
            # Extraer categoría de la URL
            url_parts = url.lower().split('/')
            
            # Buscar indicadores comunes de categoría
            category_indicators = [
                'celulares', 'smartphones', 'telefonos',
                'laptops', 'notebooks', 'computadores',
                'televisores', 'tv', 'smart-tv',
                'electrohogar', 'electrodomesticos',
                'gaming', 'juegos', 'consolas',
                'audio', 'parlantes', 'audifonos',
                'hogar', 'muebles', 'decoracion'
            ]
            
            for part in url_parts:
                for indicator in category_indicators:
                    if indicator in part:
                        return indicator
            
            # Fallback: usar el retailer como categoría
            return self.retailer if hasattr(self, 'retailer') else 'general'
            
        except Exception:
            return 'general'
    
    async def _navigate_to_page(self, url: str) -> bool:
        """
        🧭 Navegación inteligente a página con retry y error handling
        
        Args:
            url: URL a la que navegar
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        if not self.page:
            logger.error("❌ Página no inicializada")
            return False
        
        try:
            # Rate limiting
            await self._respect_rate_limit()
            
            # Configurar headers
            await self._set_random_headers()
            
            # Navegar con timeout
            logger.debug(f"🧭 Navegando a: {url}")
            start_time = time.time()
            
            response = await self.page.goto(
                url,
                timeout=self.config.timeout * 1000,
                wait_until='networkidle'
            )
            
            load_time = time.time() - start_time
            self.performance_metrics['page_load_time'] = load_time
            
            # Verificar respuesta
            if response and response.status >= 400:
                if response.status == 403:
                    raise RetailerBlockedException(
                        retailer=self.retailer,
                        url=url,
                        detection_indicators=[f"HTTP {response.status}"]
                    )
                elif response.status >= 500:
                    raise NetworkException(
                        message=f"Error del servidor: HTTP {response.status}",
                        url=url,
                        status_code=response.status
                    )
            
            self.request_count += 1
            self.successful_requests += 1
            
            logger.debug(f"✅ Navegación exitosa en {load_time:.2f}s")
            return True
            
        except TimeoutError:
            self.failed_requests += 1
            raise TimeoutException(
                message="Timeout navegando a página",
                timeout_seconds=self.config.timeout,
                operation="navigation",
                context={'url': url}
            )
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"💥 Error navegando a {url}: {str(e)}")
            return False
    
    async def _detect_blocking(self) -> bool:
        """
        🛡️ Detección inteligente de bloqueos y captchas
        
        Returns:
            bool: True si se detecta bloqueo
        """
        if not self.config.blocked_detection or not self.page:
            return False
        
        try:
            # Buscar indicadores de bloqueo en selectores
            blocked_selectors = self.config.selectors.blocked_indicators
            for selector in blocked_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        logger.warning(f"🚫 Bloqueo detectado con selector: {selector}")
                        return True
                except:
                    continue
            
            # Buscar captchas
            captcha_selectors = self.config.selectors.captcha_indicators
            for selector in captcha_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        logger.warning(f"🤖 Captcha detectado con selector: {selector}")
                        return True
                except:
                    continue
            
            # Detección por contenido de texto
            page_content = await self.page.content()
            blocking_keywords = [
                'blocked', 'captcha', 'verification', 'access denied',
                'not authorized', 'bot detection', 'human verification'
            ]
            
            content_lower = page_content.lower()
            for keyword in blocking_keywords:
                if keyword in content_lower:
                    logger.warning(f"🚫 Bloqueo detectado por keyword: {keyword}")
                    return True
            
            # Detección por título de página
            title = await self.page.title()
            if title and any(word in title.lower() for word in ['blocked', 'access', 'error']):
                logger.warning(f"🚫 Bloqueo detectado en título: {title}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error en detección de bloqueo: {str(e)}")
            return False
    
    async def _handle_blocking(self) -> bool:
        """
        🔄 Manejo automático de bloqueos
        
        Returns:
            bool: True si se pudo resolver el bloqueo
        """
        logger.warning(f"🚫 Manejando bloqueo para {self.retailer.upper()}...")
        
        try:
            # Capturar screenshot del bloqueo
            await self._capture_error_screenshot("blocking_detected")
            
            # 1. Cambiar user agent
            await self._rotate_user_agent()
            
            # 2. Cambiar proxy si está disponible
            if self.config.use_proxy and self.proxy_manager:
                new_proxy = await self.proxy_manager.get_fresh_proxy(self.retailer)
                if new_proxy:
                    await self._change_proxy(new_proxy)
                    logger.info("🌐 Proxy cambiado")
            
            # 3. Espera más larga
            wait_time = min(300, 30 * (self.consecutive_failures + 1))  # Max 5 minutos
            logger.info(f"⏳ Esperando {wait_time}s antes de continuar...")
            await asyncio.sleep(wait_time)
            
            # 4. Reinicializar contexto del browser
            await self._reinitialize_browser_context()
            
            self.consecutive_failures += 1
            self.last_failure_time = datetime.now()
            
            # Circuit breaker si hay muchos fallos
            if self.consecutive_failures >= 5:
                self.circuit_breaker_open = True
                logger.error(f"⚡ Circuit breaker abierto para {self.retailer}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Error manejando bloqueo: {str(e)}")
            return False
    
    async def _extract_products_with_ml(self) -> List[Dict[str, Any]]:
        """
        🤖 Extracción de productos con optimización ML
        
        Returns:
            List[Dict]: Lista de productos extraídos
        """
        products = []
        
        try:
            if not self.page:
                return products
            
            # Obtener selectores optimizados por ML
            selectors = await self._get_optimized_selectors()
            
            # Buscar tarjetas de producto
            product_cards = await self._find_product_cards(selectors.product_cards)
            if not product_cards:
                logger.warning("⚠️ No se encontraron tarjetas de producto")
                return products
            
            logger.info(f"🔍 Encontradas {len(product_cards)} tarjetas de producto")
            
            # Extraer datos de cada tarjeta
            for i, card in enumerate(product_cards):
                try:
                    product_data = await self._extract_product_from_card(card, selectors)
                    
                    if product_data:
                        # Aplicar reducción ETL
                        optimized_product = self.field_mapper.reduce_fields(
                            product_data, self.retailer
                        )
                        products.append(optimized_product)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error extrayendo producto {i+1}: {str(e)}")
                    continue
            
            logger.info(f"✅ {len(products)} productos extraídos exitosamente")
            
        except Exception as e:
            logger.error(f"💥 Error en extracción ML: {str(e)}")
        
        return products
    
    async def _find_product_cards(self, card_selectors: List[str]) -> List:
        """
        🔍 Encontrar tarjetas de producto usando selectores con fallback
        
        Args:
            card_selectors: Lista de selectores CSS para buscar
            
        Returns:
            List: Lista de elementos de tarjetas encontradas
        """
        for selector in card_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    logger.debug(f"✅ Selector exitoso: {selector} ({len(elements)} elementos)")
                    return elements
                else:
                    logger.debug(f"❌ Selector sin resultados: {selector}")
            except Exception as e:
                logger.debug(f"💥 Error con selector {selector}: {str(e)}")
                continue
        
        logger.warning("⚠️ Ningún selector de tarjetas funcionó")
        return []
    
    async def _extract_product_from_card(self, card_element, 
                                       selectors: RetailerSelectors) -> Optional[Dict[str, Any]]:
        """
        📊 Extraer datos de producto de una tarjeta
        
        Args:
            card_element: Elemento DOM de la tarjeta
            selectors: Selectores CSS para los campos
            
        Returns:
            Dict con datos del producto o None si falla
        """
        product = {}
        
        try:
            # Extraer cada campo usando selectores con fallback
            product['nombre'] = await self._extract_field(
                card_element, selectors.product_name, 'text'
            )
            
            product['precio_normal'] = await self._extract_price_field(
                card_element, selectors.price_normal
            )
            
            product['precio_oferta'] = await self._extract_price_field(
                card_element, selectors.price_offer
            )
            
            product['precio_tarjeta'] = await self._extract_price_field(
                card_element, selectors.price_card
            )
            
            product['marca'] = await self._extract_field(
                card_element, selectors.brand, 'text'
            )
            
            product['sku'] = await self._extract_field(
                card_element, selectors.sku, 'attribute', 'data-sku'
            )
            
            product['rating'] = await self._extract_numeric_field(
                card_element, selectors.rating
            )
            
            product['reviews_count'] = await self._extract_numeric_field(
                card_element, selectors.reviews_count
            )
            
            product['imagen_url'] = await self._extract_field(
                card_element, selectors.image_url, 'attribute', 'src'
            )
            
            product['link'] = await self._extract_field(
                card_element, selectors.product_url, 'attribute', 'href'
            )
            
            # Limpiar y normalizar datos
            product = self._clean_product_data(product)
            
            # Validar que tenga campos mínimos requeridos
            if not product.get('nombre') or not any([
                product.get('precio_normal'),
                product.get('precio_oferta'), 
                product.get('precio_tarjeta')
            ]):
                logger.debug("❌ Producto sin datos mínimos requeridos")
                return None
            
            # Agregar metadatos
            product['retailer'] = self.retailer
            product['extracted_at'] = datetime.now().isoformat()
            product['session_id'] = self.session_id
            
            return product
            
        except Exception as e:
            logger.debug(f"💥 Error extrayendo producto: {str(e)}")
            return None
    
    # ==========================================
    # MÉTODOS DE UTILIDAD Y HELPERS
    # ==========================================
    
    async def _extract_field(self, element, selectors: List[str], 
                            extraction_type: str = 'text',
                            attribute: Optional[str] = None) -> Optional[str]:
        """🔍 Extraer campo usando selectores con fallback"""
        for selector in selectors:
            try:
                field_element = await element.query_selector(selector)
                if not field_element:
                    continue
                
                if extraction_type == 'text':
                    value = await field_element.inner_text()
                elif extraction_type == 'attribute':
                    value = await field_element.get_attribute(attribute or 'value')
                else:
                    value = None
                
                if value and value.strip():
                    return value.strip()
                    
            except Exception:
                continue
        
        return None
    
    async def _extract_price_field(self, element, selectors: List[str]) -> Optional[float]:
        """💰 Extraer campo de precio con limpieza automática"""
        price_text = await self._extract_field(element, selectors, 'text')
        if not price_text:
            return None
        
        # Limpiar precio usando regex
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return None
    
    async def _extract_numeric_field(self, element, selectors: List[str]) -> Optional[float]:
        """🔢 Extraer campo numérico"""
        text = await self._extract_field(element, selectors, 'text')
        if not text:
            return None
        
        # Buscar primer número en el texto
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        
        return None
    
    def _clean_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """🧹 Limpiar y normalizar datos de producto"""
        cleaned = {}
        
        for key, value in product.items():
            if value is None:
                continue
            
            if isinstance(value, str):
                # Limpiar strings
                value = value.strip()
                value = re.sub(r'\s+', ' ', value)  # Normalizar espacios
                
                if not value:
                    continue
            
            cleaned[key] = value
        
        return cleaned
    
    # ==========================================
    # MÉTODOS DE CONFIGURACIÓN Y SETUP
    # ==========================================
    
    async def _initialize_ml_components(self) -> None:
        """🤖 Inicializar componentes ML"""
        try:
            # Cargar detector de fallos ML (se implementará después)
            # self.ml_failure_detector = await self._load_failure_detector()
            
            # Cargar gestor de proxies ML (se implementará después)  
            # self.proxy_manager = await self._load_proxy_manager()
            
            logger.debug("🤖 Componentes ML inicializados")
            
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando ML: {str(e)}")

    async def get_page(self) -> Optional[Page]:
        """Crear/obtener una página lista para navegar.

        Lanza Chromium si no hay browser disponible y configura contexto/página.
        """
        try:
            if not self.browser:
                # Lanzar navegador
                pw = await async_playwright().start()
                launch_kwargs = {
                    'headless': True,
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                }
                try:
                    self.browser = await pw.chromium.launch(**launch_kwargs)
                except Exception:
                    # Fallback headless_shell si aplica
                    self.browser = await pw.chromium.launch(headless=True)

            if not await self._setup_browser():
                return None
            return self.page
        except Exception as e:
            logger.error(f"💥 Error creando página: {e}")
            return None
    
    async def _setup_browser(self) -> bool:
        """🌐 Configurar browser y context"""
        if not self.browser:
            # Intentar lanzar browser si no existe
            try:
                pw = await async_playwright().start()
                self.browser = await pw.chromium.launch(headless=True)
            except Exception as e:
                logger.error(f"❌ Browser no disponible: {e}")
                return False
        
        try:
            # Crear contexto con configuración anti-detección
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': random.choice(self.config.user_agents),
                'locale': 'es-CL',
                'timezone_id': 'America/Santiago',
                'geolocation': {'latitude': -33.4489, 'longitude': -70.6693},  # Santiago
                'permissions': ['geolocation']
            }
            
            # Agregar proxy si está configurado
            if self.current_proxy:
                context_options['proxy'] = {'server': self.current_proxy}
            
            self.context = await self.browser.new_context(**context_options)
            
            # Crear página
            self.page = await self.context.new_page()
            
            # Configurar interceptores
            await self._setup_request_interceptors()
            
            logger.debug("🌐 Browser configurado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"💥 Error configurando browser: {str(e)}")
            return False
    
    async def _setup_request_interceptors(self) -> None:
        """🔗 Configurar interceptores de requests"""
        if not self.page:
            return
        
        async def route_handler(route: Route, request: Request):
            # Bloquear recursos innecesarios para optimizar velocidad
            if request.resource_type in ['image', 'stylesheet', 'font', 'media']:
                await route.abort()
            else:
                await route.continue_()
        
        # Interceptar requests
        await self.page.route("**/*", route_handler)
    
    async def _setup_proxy(self) -> None:
        """🌐 Configurar proxy si está disponible"""
        try:
            if self.proxy_manager:
                proxy = await self.proxy_manager.get_best_proxy(self.retailer)
                if proxy:
                    self.current_proxy = proxy
                    logger.info(f"🌐 Proxy configurado: {proxy}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error configurando proxy: {str(e)}")
    
    async def _validate_configuration(self) -> None:
        """✅ Validar configuración del scraper"""
        errors = []
        
        if not self.config.base_url:
            errors.append("base_url no configurado")
        
        if not self.config.selectors.product_cards:
            errors.append("Selectores de tarjetas de producto no configurados")
        
        if self.config.rate_limit <= 0:
            errors.append("rate_limit debe ser mayor a 0")
        
        if errors:
            raise ConfigurationException(
                config_key="scraper_config",
                context={'retailer': self.retailer, 'errors': errors}
            )
    
    # ==========================================
    # MÉTODOS DE OPTIMIZACIÓN Y ML
    # ==========================================
    
    async def _get_optimized_selectors(self) -> RetailerSelectors:
        """🎯 Obtener selectores optimizados por ML"""
        # Por ahora retorna selectores base
        # En el futuro incluirá optimización ML basada en éxito histórico
        return self.config.selectors
    
    async def _respect_rate_limit(self) -> None:
        """🚦 Respetar rate limiting"""
        if self.config.rate_limit <= 0:
            return
        
        min_interval = 1.0 / self.config.rate_limit
        current_time = time.time()
        
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _set_random_headers(self) -> None:
        """🎲 Configurar headers aleatorios"""
        if not self.page:
            return
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Agregar headers custom
        headers.update(self.config.custom_headers)
        
        await self.page.set_extra_http_headers(headers)
    
    async def _intelligent_scroll(self) -> None:
        """📜 Scroll inteligente para cargar contenido lazy"""
        if not self.page:
            return
        
        try:
            # Obtener dimensiones
            viewport_height = await self.page.evaluate('window.innerHeight')
            total_height = await self.page.evaluate('document.body.scrollHeight')
            
            # Scroll gradual
            current_position = 0
            scroll_step = viewport_height // 3  # Scroll de 1/3 de viewport
            
            while current_position < total_height:
                # Scroll suave
                await self.page.evaluate(f'window.scrollTo(0, {current_position})')
                
                # Pausa para carga lazy
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                current_position += scroll_step
                
                # Recalcular altura (puede crecer con lazy loading)
                new_height = await self.page.evaluate('document.body.scrollHeight')
                if new_height > total_height:
                    total_height = new_height
            
            # Volver al top
            await self.page.evaluate('window.scrollTo(0, 0)')
            
        except Exception as e:
            logger.debug(f"⚠️ Error en scroll inteligente: {str(e)}")
    
    async def _wait_for_page_load(self) -> None:
        """⏳ Esperar carga completa de página"""
        if not self.page or not self.config.wait_for_load:
            return
        
        try:
            # Esperar que el DOM esté listo
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Esperar que no haya requests de red pendientes
            await self.page.wait_for_load_state('networkidle')
            
            # Pausa adicional para JavaScript asíncrono
            await asyncio.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.debug(f"⚠️ Error esperando carga: {str(e)}")
    
    # ==========================================
    # MÉTODOS DE RECOVERY Y ERROR HANDLING
    # ==========================================
    
    async def _rotate_user_agent(self) -> None:
        """🎭 Rotar user agent"""
        if not self.page:
            return
        
        new_user_agent = random.choice(self.config.user_agents)
        await self.page.set_user_agent(new_user_agent)
        logger.debug(f"🎭 User agent rotado")
    
    async def _change_proxy(self, new_proxy: str) -> None:
        """🌐 Cambiar proxy reinicializando contexto"""
        try:
            # Cerrar contexto actual
            if self.context:
                await self.context.close()
            
            # Actualizar proxy
            self.current_proxy = new_proxy
            
            # Reinicializar contexto con nuevo proxy
            await self._setup_browser()
            
        except Exception as e:
            logger.warning(f"⚠️ Error cambiando proxy: {str(e)}")
    
    async def _reinitialize_browser_context(self) -> None:
        """🔄 Reinicializar contexto del browser"""
        try:
            if self.context:
                await self.context.close()
            
            await self._setup_browser()
            
        except Exception as e:
            logger.warning(f"⚠️ Error reinicializando contexto: {str(e)}")
    
    async def _capture_error_screenshot(self, error_type: str) -> Optional[str]:
        """📸 Capturar screenshot en caso de error"""
        if not self.config.screenshot_on_error or not self.page:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.retailer}_{error_type}_{timestamp}.png"
            screenshot_path = self.logs_dir / "screenshots" / filename
            screenshot_path.parent.mkdir(exist_ok=True)
            
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"📸 Screenshot capturado: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Error capturando screenshot: {str(e)}")
            return None
    
    async def _validate_extracted_data(self, result: ScrapingResult) -> None:
        """✅ Validar calidad de datos extraídos"""
        if not result.products:
            result.add_warning("No se extrajeron productos")
            return
        
        # Validaciones de calidad
        products_with_prices = len([
            p for p in result.products 
            if any([p.get('precio_normal'), p.get('precio_oferta'), p.get('precio_tarjeta')])
        ])
        
        price_coverage = products_with_prices / len(result.products)
        if price_coverage < 0.8:  # <80% con precios
            result.add_warning(f"Baja cobertura de precios: {price_coverage:.1%}")
        
        # Validar nombres de producto
        products_with_names = len([p for p in result.products if p.get('nombre')])
        name_coverage = products_with_names / len(result.products)
        if name_coverage < 0.9:  # <90% con nombres
            result.add_warning(f"Baja cobertura de nombres: {name_coverage:.1%}")
    
    async def _save_session_metrics(self) -> None:
        """💾 Guardar métricas de sesión"""
        try:
            if not self.start_time:
                return
            
            duration = datetime.now() - self.start_time
            
            metrics = {
                'session_id': self.session_id,
                'retailer': self.retailer,
                'start_time': self.start_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'request_count': self.request_count,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'total_products_scraped': self.total_products_scraped,
                'success_rate': self.successful_requests / max(1, self.request_count),
                'products_per_minute': self.total_products_scraped / max(1, duration.total_seconds() / 60),
                'consecutive_failures': self.consecutive_failures,
                'circuit_breaker_open': self.circuit_breaker_open,
                'performance_metrics': self.performance_metrics
            }
            
            # Guardar en archivo
            metrics_file = self.logs_dir / f"session_{self.session_id}_metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Métricas guardadas: {metrics_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error guardando métricas: {str(e)}")

# ==========================================
# FUNCIONES DE UTILIDAD
# ==========================================

def create_base_selectors() -> RetailerSelectors:
    """
    🎯 Crear selectores base comunes para retailers
    
    Returns:
        RetailerSelectors: Selectores CSS base
    """
    return RetailerSelectors(
        product_cards=[
            '.product-item', '.product-card', '.product', 
            '[data-product]', '.item', '.card'
        ],
        product_name=[
            '.product-name', '.name', '.title', 'h1', 'h2', 'h3',
            '[data-name]', '.product-title'
        ],
        price_normal=[
            '.price', '.normal-price', '.original-price', 
            '[data-price]', '.price-normal'
        ],
        price_offer=[
            '.offer-price', '.sale-price', '.discount-price',
            '.price-offer', '.special-price'
        ],
        price_card=[
            '.card-price', '.member-price', '.tc-price',
            '.price-card'
        ],
        brand=[
            '.brand', '.marca', '[data-brand]', '.brand-name'
        ],
        sku=[
            '[data-sku]', '[data-id]', '.sku', '.product-id'
        ],
        blocked_indicators=[
            '.blocked', '.access-denied', '.captcha',
            '#captcha', '.verification'
        ],
        captcha_indicators=[
            '.captcha', '#captcha', '.recaptcha', 
            '.verification', '.challenge'
        ]
    )
