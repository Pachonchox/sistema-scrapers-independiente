# -*- coding: utf-8 -*-
"""
🔬 Sistema de Optimización de Datos para Scrapers
=================================================

Testa configuraciones progresivas de ahorro de datos para encontrar
el mínimo consumo de ancho de banda manteniendo funcionalidad por scraper.

CRÍTICO para uso con proxy que cobra por mega.

Features:
- 🧪 Tests unitarios de recursos por scraper
- 📊 Medición de consumo de datos real
- ⚖️ Balance funcionalidad vs ahorro
- 📋 Matriz de compatibilidad recursos
- 🎯 Configuración óptima personalizada

Niveles de Ahorro:
1. CONSERVADOR - Solo bloquea recursos no esenciales
2. MODERADO - Bloquea imágenes y media
3. AGRESIVO - Bloquea todo excepto HTML/CSS crítico
4. EXTREMO - Solo HTML básico
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from playwright.async_api import async_playwright, Browser, Page, Route
import psutil
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data_optimizer")

@dataclass
class DataUsageMetrics:
    """Métricas de uso de datos"""
    bytes_sent: int = 0
    bytes_received: int = 0
    requests_count: int = 0
    blocked_requests: int = 0
    images_blocked: int = 0
    js_blocked: int = 0
    css_blocked: int = 0
    fonts_blocked: int = 0
    media_blocked: int = 0
    total_bytes: int = 0
    success_rate: float = 0.0
    products_extracted: int = 0
    
    @property
    def savings_percentage(self) -> float:
        """Calcular porcentaje de ahorro vs baseline"""
        if hasattr(self, '_baseline_bytes') and self._baseline_bytes > 0:
            return ((self._baseline_bytes - self.total_bytes) / self._baseline_bytes) * 100
        return 0.0

@dataclass 
class ScrapingConfig:
    """Configuración de scraping"""
    name: str
    level: str  # CONSERVADOR, MODERADO, AGRESIVO, EXTREMO
    browser_args: List[str]
    block_images: bool = True
    block_javascript: bool = False
    block_css: bool = False
    block_fonts: bool = True
    block_media: bool = True
    block_websockets: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout: int = 30000

# 🎛️ CONFIGURACIONES PROGRESIVAS
OPTIMIZATION_CONFIGS = [
    ScrapingConfig(
        name="BASELINE",
        level="SIN_OPTIMIZAR",
        browser_args=['--no-sandbox', '--disable-setuid-sandbox'],
        block_images=False,
        block_javascript=False,
        block_css=False,
        block_fonts=False,
        block_media=False,
        block_websockets=False
    ),
    ScrapingConfig(
        name="CONSERVADOR", 
        level="NIVEL_1",
        browser_args=[
            '--no-sandbox', '--disable-setuid-sandbox',
            '--disable-plugins', '--disable-extensions',
            '--disable-background-networking'
        ],
        block_images=False,
        block_javascript=False,
        block_css=False,
        block_fonts=True,
        block_media=True,
        block_websockets=True
    ),
    ScrapingConfig(
        name="MODERADO",
        level="NIVEL_2", 
        browser_args=[
            '--no-sandbox', '--disable-setuid-sandbox',
            '--disable-plugins', '--disable-extensions',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--aggressive-cache-discard'
        ],
        block_images=True,
        block_javascript=False,
        block_css=False,
        block_fonts=True,
        block_media=True,
        block_websockets=True
    ),
    ScrapingConfig(
        name="AGRESIVO",
        level="NIVEL_3",
        browser_args=[
            '--no-sandbox', '--disable-setuid-sandbox',
            '--disable-plugins', '--disable-extensions', 
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--aggressive-cache-discard',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            '--memory-pressure-off'
        ],
        block_images=True,
        block_javascript=True,
        block_css=False,
        block_fonts=True,
        block_media=True,
        block_websockets=True,
        viewport_width=1024,
        viewport_height=600
    ),
    ScrapingConfig(
        name="EXTREMO",
        level="NIVEL_4",
        browser_args=[
            '--no-sandbox', '--disable-setuid-sandbox',
            '--disable-plugins', '--disable-extensions',
            '--disable-background-networking', 
            '--disable-background-timer-throttling',
            '--aggressive-cache-discard',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            '--memory-pressure-off',
            '--disable-javascript',
            '--max-connections-per-host=4'
        ],
        block_images=True,
        block_javascript=True,
        block_css=True,
        block_fonts=True,
        block_media=True,
        block_websockets=True,
        viewport_width=800,
        viewport_height=600
    )
]

class DataUsageTracker:
    """Tracker de uso de datos durante scraping"""
    
    def __init__(self):
        self.metrics = DataUsageMetrics()
        self.start_time = 0
        self.initial_network_stats = None
    
    def start_tracking(self):
        """Iniciar tracking de red"""
        self.start_time = time.time()
        self.initial_network_stats = psutil.net_io_counters()
        self.metrics = DataUsageMetrics()
    
    def stop_tracking(self) -> DataUsageMetrics:
        """Detener tracking y calcular métricas"""
        if self.initial_network_stats:
            current_stats = psutil.net_io_counters()
            self.metrics.bytes_sent = current_stats.bytes_sent - self.initial_network_stats.bytes_sent
            self.metrics.bytes_received = current_stats.bytes_recv - self.initial_network_stats.bytes_recv  
            self.metrics.total_bytes = self.metrics.bytes_sent + self.metrics.bytes_received
        
        return self.metrics

class ScraperDataOptimizer:
    """Optimizador de datos para scrapers"""
    
    def __init__(self):
        self.results_path = Path("data/optimization_results")
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.tracker = DataUsageTracker()
        
        # URLs de test por retailer (páginas ligeras para testing)
        self.test_urls = {
            "paris": "https://www.paris.cl/tecnologia/celulares/?page=1&size=30",
            "falabella": "https://www.falabella.com/falabella-cl/category/cat720161/Smartphones?page=1", 
            "ripley": "https://simple.ripley.cl/tecno/computacion?page=1",
            "hites": "https://www.hites.com/tecnologia/celulares-y-telefonia",
            "abcdin": "https://www.abcdin.cl/tecnologia/celulares",
            "mercadolibre": "https://listado.mercadolibre.cl/celulares-telefonia/celulares-smartphones"
        }
    
    async def setup_route_blocking(self, page: Page, config: ScrapingConfig, tracker: DataUsageTracker):
        """Configurar bloqueo de recursos según configuración"""
        
        async def route_handler(route: Route):
            """Manejar requests y decidir si bloquear"""
            request = route.request
            resource_type = request.resource_type
            url = request.url.lower()
            
            should_block = False
            
            # Contabilizar request
            tracker.metrics.requests_count += 1
            
            # Decidir bloqueo según configuración
            if config.block_images and resource_type in ['image', 'imageset']:
                should_block = True
                tracker.metrics.images_blocked += 1
                
            elif config.block_javascript and resource_type == 'script':
                should_block = True
                tracker.metrics.js_blocked += 1
                
            elif config.block_css and resource_type == 'stylesheet':
                should_block = True 
                tracker.metrics.css_blocked += 1
                
            elif config.block_fonts and resource_type == 'font':
                should_block = True
                tracker.metrics.fonts_blocked += 1
                
            elif config.block_media and resource_type in ['media', 'video', 'audio']:
                should_block = True
                tracker.metrics.media_blocked += 1
                
            elif config.block_websockets and resource_type == 'websocket':
                should_block = True
                
            # Bloqueo adicional por URL patterns
            elif any(pattern in url for pattern in [
                'analytics', 'tracking', 'ads', 'facebook', 'google-analytics',
                'doubleclick', 'googlesyndication', 'googletagmanager',
                'hotjar', 'mixpanel', 'segment', 'intercom'
            ]):
                should_block = True
                
            if should_block:
                tracker.metrics.blocked_requests += 1
                await route.abort()
            else:
                await route.continue_()
        
        await page.route('**/*', route_handler)
    
    async def test_scraper_config(self, retailer: str, config: ScrapingConfig, 
                                 max_products: int = 10) -> Tuple[DataUsageMetrics, bool]:
        """Testear configuración específica en un scraper"""
        
        logger.info(f"🧪 Testing {retailer} con configuración {config.name}")
        
        success = False
        products_found = 0
        
        # Iniciar tracking
        self.tracker.start_tracking()
        
        try:
            playwright = await async_playwright().start()
            
            # Lanzar browser con configuración específica
            browser = await playwright.chromium.launch(
                headless=True,
                args=config.browser_args
            )
            
            # Crear contexto optimizado
            context = await browser.new_context(
                viewport={
                    'width': config.viewport_width, 
                    'height': config.viewport_height
                },
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            # Configurar timeout
            page.set_default_timeout(config.timeout)
            
            # Configurar bloqueo de recursos
            await self.setup_route_blocking(page, config, self.tracker)
            
            # Navegar a página de test
            test_url = self.test_urls.get(retailer)
            if not test_url:
                raise ValueError(f"No test URL for retailer: {retailer}")
                
            await page.goto(test_url, wait_until='networkidle')
            
            # Esperar carga
            await page.wait_for_timeout(3000)
            
            # Testear extracción básica según retailer
            products_found = await self._test_product_extraction(page, retailer, max_products)
            
            if products_found > 0:
                success = True
                logger.info(f"✅ {retailer} {config.name}: {products_found} productos extraídos")
            else:
                logger.warning(f"⚠️ {retailer} {config.name}: No se extrajeron productos")
            
            await browser.close()
            await playwright.stop()
            
        except Exception as e:
            logger.error(f"❌ Error testing {retailer} {config.name}: {e}")
            success = False
        
        # Detener tracking
        metrics = self.tracker.stop_tracking()
        metrics.success_rate = 1.0 if success else 0.0 
        metrics.products_extracted = products_found
        
        return metrics, success
    
    async def _test_product_extraction(self, page: Page, retailer: str, max_products: int) -> int:
        """Testear extracción básica de productos"""
        
        try:
            if retailer == "paris":
                # Buscar productos Paris
                products = await page.query_selector_all('.product-item, .card-product, [data-product-id]')
                
            elif retailer == "falabella":
                # Buscar productos Falabella  
                products = await page.query_selector_all('[data-testid*="product"], .pod, [data-automation*="product"]')
                
            elif retailer == "ripley":
                # Buscar productos Ripley
                products = await page.query_selector_all('.catalog-product-item, .product-card, [data-testid="product"]')
                
            elif retailer == "hites":
                # Buscar productos Hites
                products = await page.query_selector_all('.product-item, .item-product, .product-card')
                
            elif retailer == "abcdin":
                # Buscar productos AbcDin
                products = await page.query_selector_all('.product, .product-item, .card-product')
                
            elif retailer == "mercadolibre":
                # Buscar productos MercadoLibre
                products = await page.query_selector_all('.ui-search-result, .ui-search-item')
                
            else:
                products = []
            
            return min(len(products), max_products)
            
        except Exception as e:
            logger.error(f"Error extrayendo productos {retailer}: {e}")
            return 0
    
    async def optimize_retailer(self, retailer: str) -> Dict[str, Any]:
        """Optimizar configuración para un retailer específico"""
        
        logger.info(f"🎯 Optimizando {retailer.upper()}")
        
        results = {
            "retailer": retailer,
            "timestamp": datetime.now().isoformat(),
            "configurations": [],
            "optimal_config": None,
            "baseline_data_usage": 0,
            "optimal_data_usage": 0,
            "savings_percentage": 0
        }
        
        baseline_bytes = 0
        optimal_config = None
        best_score = -1
        
        # Probar cada configuración
        for config in OPTIMIZATION_CONFIGS:
            logger.info(f"📊 Testing {config.name}...")
            
            metrics, success = await self.test_scraper_config(retailer, config)
            
            # Calcular score: funcionalidad vs ahorro
            if success:
                functionality_score = min(metrics.products_extracted / 10.0, 1.0) # Normalizar a 10 productos
                data_efficiency = 1.0 / (metrics.total_bytes + 1) * 1000000  # Invertir bytes
                combined_score = functionality_score * 0.7 + data_efficiency * 0.3
                
                if config.name == "BASELINE":
                    baseline_bytes = metrics.total_bytes
                    
                if combined_score > best_score:
                    best_score = combined_score
                    optimal_config = config.name
                    
            else:
                combined_score = 0
            
            # Guardar resultado
            config_result = {
                "name": config.name,
                "level": config.level, 
                "success": success,
                "products_extracted": metrics.products_extracted,
                "total_bytes": metrics.total_bytes,
                "requests_count": metrics.requests_count,
                "blocked_requests": metrics.blocked_requests,
                "images_blocked": metrics.images_blocked,
                "js_blocked": metrics.js_blocked,
                "css_blocked": metrics.css_blocked,
                "fonts_blocked": metrics.fonts_blocked,
                "media_blocked": metrics.media_blocked,
                "combined_score": combined_score,
                "config_details": asdict(config)
            }
            
            results["configurations"].append(config_result)
            
            logger.info(f"📋 {config.name}: {metrics.total_bytes:,} bytes, "
                       f"{metrics.products_extracted} productos, Score: {combined_score:.4f}")
        
        # Determinar configuración óptima
        if optimal_config:
            optimal_data = next(c for c in results["configurations"] if c["name"] == optimal_config)
            results["optimal_config"] = optimal_config
            results["baseline_data_usage"] = baseline_bytes
            results["optimal_data_usage"] = optimal_data["total_bytes"]
            
            if baseline_bytes > 0:
                results["savings_percentage"] = ((baseline_bytes - optimal_data["total_bytes"]) / baseline_bytes) * 100
        
        # Guardar resultados
        results_file = self.results_path / f"{retailer}_optimization_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Resultados guardados: {results_file}")
        
        return results
    
    async def optimize_all_retailers(self) -> Dict[str, Any]:
        """Optimizar todos los retailers"""
        
        logger.info("🚀 Iniciando optimización completa de todos los retailers")
        
        summary = {
            "optimization_date": datetime.now().isoformat(),
            "retailers": {},
            "global_recommendations": {},
            "total_potential_savings": 0
        }
        
        total_baseline = 0
        total_optimal = 0
        
        # Optimizar cada retailer
        for retailer in self.test_urls.keys():
            try:
                result = await self.optimize_retailer(retailer)
                summary["retailers"][retailer] = {
                    "optimal_config": result["optimal_config"],
                    "baseline_usage": result["baseline_data_usage"],
                    "optimal_usage": result["optimal_data_usage"], 
                    "savings_percentage": result["savings_percentage"]
                }
                
                total_baseline += result["baseline_data_usage"]
                total_optimal += result["optimal_data_usage"]
                
            except Exception as e:
                logger.error(f"❌ Error optimizando {retailer}: {e}")
                summary["retailers"][retailer] = {"error": str(e)}
        
        # Calcular ahorro total
        if total_baseline > 0:
            summary["total_potential_savings"] = ((total_baseline - total_optimal) / total_baseline) * 100
        
        # Generar recomendaciones globales
        summary["global_recommendations"] = self._generate_global_recommendations(summary["retailers"])
        
        # Guardar resumen
        summary_file = self.results_path / f"optimization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Optimización completada. Ahorro potencial: {summary['total_potential_savings']:.1f}%")
        logger.info(f"📋 Resumen guardado: {summary_file}")
        
        return summary
    
    def _generate_global_recommendations(self, retailers_data: Dict) -> Dict[str, Any]:
        """Generar recomendaciones globales basadas en resultados"""
        
        # Contar configuraciones óptimas
        config_counts = {}
        working_retailers = []
        
        for retailer, data in retailers_data.items():
            if "optimal_config" in data and data["optimal_config"]:
                config = data["optimal_config"]
                config_counts[config] = config_counts.get(config, 0) + 1
                working_retailers.append(retailer)
        
        # Configuración más común
        most_common_config = max(config_counts, key=config_counts.get) if config_counts else "CONSERVADOR"
        
        return {
            "most_compatible_config": most_common_config,
            "config_distribution": config_counts,
            "working_retailers_count": len(working_retailers),
            "failed_retailers": [r for r in retailers_data.keys() if r not in working_retailers],
            "recommendation": f"Usar configuración {most_common_config} como base global",
            "custom_configs_needed": len([r for r, d in retailers_data.items() 
                                        if d.get("optimal_config") != most_common_config])
        }

async def main():
    """Función principal para ejecutar optimización"""
    
    print("SISTEMA DE OPTIMIZACION DE DATOS PARA SCRAPERS")
    print("="*60)
    print("Encontrando configuracion optima para uso con proxy que cobra por mega\n")
    
    optimizer = ScraperDataOptimizer()
    
    # Ejecutar optimización completa
    summary = await optimizer.optimize_all_retailers()
    
    # Mostrar resultados
    print("\nRESULTADOS DE OPTIMIZACION:")
    print("="*40)
    
    for retailer, data in summary["retailers"].items():
        if "optimal_config" in data:
            print(f"{retailer.upper()}: {data['optimal_config']} "
                  f"(Ahorro: {data['savings_percentage']:.1f}%)")
        else:
            print(f"ERROR {retailer.upper()}: Error en optimizacion")
    
    print(f"\nAHORRO POTENCIAL TOTAL: {summary['total_potential_savings']:.1f}%")
    print(f"RECOMENDACION: {summary['global_recommendations']['recommendation']}")
    
    print(f"\nResultados detallados en: data/optimization_results/")

if __name__ == "__main__":
    asyncio.run(main())