#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛠️ Maintenance Toolkit - Herramientas de Mantenimiento y Debugging
===================================================================

Suite completa de herramientas para mantenimiento, debugging y análisis
de scrapers. Incluye capturas de pantalla, análisis HTML, diagnósticos
automáticos y herramientas de reparación.

Features:
- 📸 Capturas automáticas de páginas fallidas  
- 🔍 Análisis HTML para debugging de selectores
- 🩺 Diagnóstico automático de problemas
- 🔧 Herramientas de reparación automática
- 📊 Análisis de performance y métricas
- 📝 Reportes detallados con recomendaciones

Author: Portable Orchestrator Team
Version: 5.0.0
"""

import sys
import os
import io
import asyncio
import logging
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import traceback
import hashlib
from urllib.parse import urlparse, urljoin

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from playwright.async_api import Page, Browser, Playwright, async_playwright
    from bs4 import BeautifulSoup
    import cv2
    import numpy as np
except ImportError as e:
    logging.warning(f"⚠️  Dependencias opcionales no disponibles: {e}")
    Page = Browser = Playwright = async_playwright = None
    BeautifulSoup = cv2 = np = None

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
class DiagnosticResult:
    """🩺 Resultado de diagnóstico automático"""
    url: str
    retailer: str
    timestamp: datetime
    issues_found: List[str]
    recommendations: List[str]
    severity: str  # 'low', 'medium', 'high', 'critical'
    screenshot_path: Optional[str] = None
    html_analysis: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None

@dataclass
class SelectorAnalysis:
    """🎯 Análisis de selectores CSS"""
    selector: str
    found_elements: int
    element_samples: List[str]
    suggestions: List[str]
    confidence_score: float

class MaintenanceToolkit:
    """
    🛠️ Toolkit Principal de Mantenimiento
    
    Herramientas completas para:
    - Debugging automático de scrapers
    - Análisis de páginas fallidas
    - Capturas de pantalla automáticas
    - Análisis HTML y CSS
    - Diagnósticos y reparaciones
    - Optimización de performance
    """
    
    def __init__(self, output_dir: str = "logs/maintenance"):
        """
        🚀 Inicializar Maintenance Toolkit
        
        Args:
            output_dir: Directorio para logs y archivos de mantenimiento
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectorios especializados
        self.screenshots_dir = self.output_dir / "screenshots"
        self.html_dumps_dir = self.output_dir / "html_dumps"
        self.diagnostics_dir = self.output_dir / "diagnostics"
        self.reports_dir = self.output_dir / "reports"
        
        for dir_path in [self.screenshots_dir, self.html_dumps_dir, 
                        self.diagnostics_dir, self.reports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None
        
        logger.info("🛠️ MaintenanceToolkit iniciado correctamente")
        logger.info(f"📁 Directorio de salida: {self.output_dir}")
    
    async def __aenter__(self):
        """🚀 Context manager para inicializar browser"""
        if async_playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Visible para debugging
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """🔚 Cleanup del context manager"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def capture_failure_screenshot(self, url: str, retailer: str, 
                                       error_context: str = "") -> Optional[str]:
        """
        📸 Capturar screenshot de página fallida con análisis automático
        
        Args:
            url: URL de la página fallida
            retailer: Nombre del retailer
            error_context: Contexto del error para el filename
            
        Returns:
            str: Ruta al archivo de screenshot
        """
        if not self.browser:
            logger.error("❌ Browser no inicializado. Usar async with MaintenanceToolkit()")
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            context_clean = "".join(c for c in error_context if c.isalnum() or c in '-_')[:20]
            filename = f"{retailer}_{timestamp}_{context_clean}.png"
            screenshot_path = self.screenshots_dir / filename
            
            logger.info(f"📸 Capturando screenshot: {url}")
            
            # Crear nueva página
            page = await self.browser.new_page()
            
            try:
                # Configurar viewport grande para capturar más contenido
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Navegar con timeout
                await page.goto(url, timeout=30000, wait_until="networkidle")
                
                # Scroll completo para cargar contenido lazy
                await self._full_page_scroll(page)
                
                # Capturar screenshot de página completa
                await page.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                    type='png'
                )
                
                logger.info(f"✅ Screenshot capturado: {screenshot_path}")
                
                # Análisis automático de la imagen
                await self._analyze_screenshot(screenshot_path, url, retailer)
                
                return str(screenshot_path)
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"💥 Error capturando screenshot de {url}: {str(e)}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return None
    
    async def dump_html_for_analysis(self, url: str, retailer: str, 
                                   selectors_to_test: List[str] = None) -> Optional[str]:
        """
        📄 Extraer y guardar HTML para análisis de selectores
        
        Args:
            url: URL a analizar
            retailer: Nombre del retailer
            selectors_to_test: Lista de selectores CSS a validar
            
        Returns:
            str: Ruta al archivo HTML
        """
        if not self.browser:
            logger.error("❌ Browser no inicializado")
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{retailer}_{timestamp}.html"
            html_path = self.html_dumps_dir / filename
            
            logger.info(f"📄 Extrayendo HTML: {url}")
            
            page = await self.browser.new_page()
            
            try:
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await self._full_page_scroll(page)
                
                # Extraer HTML completo
                html_content = await page.content()
                
                # Guardar HTML
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Análisis de selectores si se proporcionan
                if selectors_to_test:
                    analysis_result = await self._analyze_html_selectors(
                        html_content, selectors_to_test, retailer
                    )
                    
                    # Guardar análisis
                    analysis_path = html_path.with_suffix('.json')
                    with open(analysis_path, 'w', encoding='utf-8') as f:
                        json.dump(analysis_result, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"🔍 Análisis de selectores guardado: {analysis_path}")
                
                logger.info(f"✅ HTML guardado: {html_path}")
                return str(html_path)
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"💥 Error extrayendo HTML de {url}: {str(e)}")
            return None
    
    async def diagnose_scraper_issues(self, url: str, retailer: str, 
                                    expected_selectors: Dict[str, str],
                                    error_logs: List[str] = None) -> DiagnosticResult:
        """
        🩺 Diagnóstico automático completo de issues de scraper
        
        Args:
            url: URL problemática
            retailer: Nombre del retailer
            expected_selectors: Selectores CSS esperados
            error_logs: Logs de errores previos
            
        Returns:
            DiagnosticResult: Resultado completo del diagnóstico
        """
        logger.info(f"🩺 Iniciando diagnóstico automático: {retailer} - {url}")
        
        issues_found = []
        recommendations = []
        severity = 'low'
        screenshot_path = None
        html_analysis = None
        performance_metrics = {}
        
        try:
            # 1. Capturar screenshot y HTML
            screenshot_path = await self.capture_failure_screenshot(
                url, retailer, "diagnostic"
            )
            
            html_path = await self.dump_html_for_analysis(
                url, retailer, list(expected_selectors.values())
            )
            
            # 2. Análisis de conectividad básica
            connectivity_issues = await self._diagnose_connectivity(url)
            issues_found.extend(connectivity_issues)
            
            # 3. Análisis de selectores CSS
            if html_path:
                selector_analysis = await self._diagnose_selectors(
                    html_path, expected_selectors
                )
                html_analysis = selector_analysis
                
                for selector_name, analysis in selector_analysis.items():
                    if analysis['found_elements'] == 0:
                        issues_found.append(f"Selector '{selector_name}' no encuentra elementos")
                        recommendations.append(f"Revisar selector: {analysis['selector']}")
                        severity = 'high'
            
            # 4. Análisis de performance
            performance_metrics = await self._measure_page_performance(url)
            
            if performance_metrics.get('load_time', 0) > 30:
                issues_found.append("Tiempo de carga excesivo (>30s)")
                recommendations.append("Optimizar timeouts y estrategia de carga")
                severity = 'medium' if severity == 'low' else severity
            
            # 5. Análisis de logs de error
            if error_logs:
                log_analysis = self._analyze_error_logs(error_logs)
                issues_found.extend(log_analysis['issues'])
                recommendations.extend(log_analysis['recommendations'])
                
                if 'timeout' in ' '.join(error_logs).lower():
                    severity = 'high'
                elif 'blocked' in ' '.join(error_logs).lower():
                    severity = 'critical'
            
            # 6. Determinar severidad final
            if 'blocked' in ' '.join(issues_found).lower():
                severity = 'critical'
            elif len(issues_found) > 5:
                severity = 'high'
            elif len(issues_found) > 2:
                severity = 'medium'
            
        except Exception as e:
            issues_found.append(f"Error en diagnóstico: {str(e)}")
            severity = 'critical'
            logger.error(f"💥 Error en diagnóstico: {str(e)}")
        
        # Crear resultado
        result = DiagnosticResult(
            url=url,
            retailer=retailer,
            timestamp=datetime.now(),
            issues_found=issues_found,
            recommendations=recommendations,
            severity=severity,
            screenshot_path=screenshot_path,
            html_analysis=html_analysis,
            performance_metrics=performance_metrics
        )
        
        # Guardar diagnóstico
        await self._save_diagnostic_report(result)
        
        # Log resultado
        severity_emoji = {
            'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'
        }.get(severity, '⚪')
        
        logger.info(f"{severity_emoji} Diagnóstico completado - Severidad: {severity.upper()}")
        logger.info(f"🚨 Issues encontrados: {len(issues_found)}")
        logger.info(f"💡 Recomendaciones: {len(recommendations)}")
        
        return result
    
    async def _full_page_scroll(self, page: Page) -> None:
        """📜 Scroll completo de página para cargar contenido lazy"""
        try:
            # Obtener altura total
            total_height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            # Scroll gradual
            current_height = 0
            while current_height < total_height:
                await page.evaluate(f'window.scrollTo(0, {current_height})')
                await asyncio.sleep(0.5)  # Pausa para carga lazy
                current_height += viewport_height
                
                # Recalcular altura (puede cambiar con contenido lazy)
                new_total_height = await page.evaluate('document.body.scrollHeight')
                if new_total_height > total_height:
                    total_height = new_total_height
            
            # Volver al top
            await page.evaluate('window.scrollTo(0, 0)')
            
        except Exception as e:
            logger.warning(f"⚠️  Error en scroll: {str(e)}")
    
    async def _analyze_screenshot(self, screenshot_path: Path, url: str, retailer: str) -> None:
        """🔍 Análisis automático de screenshot usando CV"""
        try:
            if not cv2 or not np:
                return
                
            # Cargar imagen
            img = cv2.imread(str(screenshot_path))
            if img is None:
                return
            
            # Análisis básico
            height, width = img.shape[:2]
            
            # Detectar si la página está en blanco o tiene error
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            # Detectar elementos de error comunes
            error_indicators = []
            if mean_brightness > 240:  # Muy blanco
                error_indicators.append("Página muy blanca - posible error de carga")
            elif mean_brightness < 20:  # Muy negro
                error_indicators.append("Página muy oscura - posible timeout")
            
            # Guardar análisis
            analysis = {
                'url': url,
                'retailer': retailer,
                'image_dimensions': {'width': width, 'height': height},
                'mean_brightness': float(mean_brightness),
                'error_indicators': error_indicators,
                'timestamp': datetime.now().isoformat()
            }
            
            analysis_path = screenshot_path.with_suffix('.json')
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"⚠️  Error en análisis de screenshot: {str(e)}")
    
    async def _analyze_html_selectors(self, html_content: str, selectors: List[str], 
                                    retailer: str) -> Dict[str, Any]:
        """🎯 Análisis detallado de selectores CSS en HTML"""
        try:
            if not BeautifulSoup:
                return {}
                
            soup = BeautifulSoup(html_content, 'html.parser')
            analysis = {}
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    element_count = len(elements)
                    
                    # Muestras de elementos encontrados
                    samples = []
                    for el in elements[:3]:  # Primeros 3
                        sample_info = {
                            'tag': el.name,
                            'text': el.get_text(strip=True)[:100],
                            'attributes': dict(el.attrs) if hasattr(el, 'attrs') else {}
                        }
                        samples.append(sample_info)
                    
                    # Generar sugerencias si no se encuentran elementos
                    suggestions = []
                    if element_count == 0:
                        # Buscar selectores similares
                        similar = self._find_similar_selectors(soup, selector)
                        suggestions = [f"Probar: {s}" for s in similar[:3]]
                    
                    analysis[selector] = {
                        'selector': selector,
                        'found_elements': element_count,
                        'element_samples': samples,
                        'suggestions': suggestions,
                        'confidence_score': min(element_count / 5.0, 1.0)  # Score basado en elementos
                    }
                    
                except Exception as e:
                    analysis[selector] = {
                        'selector': selector,
                        'found_elements': 0,
                        'error': str(e),
                        'suggestions': ['Verificar sintaxis del selector'],
                        'confidence_score': 0.0
                    }
            
            return analysis
            
        except Exception as e:
            logger.error(f"💥 Error en análisis HTML: {str(e)}")
            return {}
    
    def _find_similar_selectors(self, soup: BeautifulSoup, original_selector: str) -> List[str]:
        """🔍 Encontrar selectores similares que podrían funcionar"""
        suggestions = []
        
        try:
            # Extraer clases y IDs del selector original
            parts = original_selector.replace('.', ' .').replace('#', ' #').split()
            
            for part in parts:
                if part.startswith('.'):  # Clase
                    class_name = part[1:]
                    # Buscar clases similares
                    all_classes = set()
                    for el in soup.find_all(attrs={'class': True}):
                        all_classes.update(el['class'])
                    
                    # Clases que contienen el nombre buscado
                    similar_classes = [c for c in all_classes if class_name.lower() in c.lower()]
                    suggestions.extend([f".{c}" for c in similar_classes[:3]])
                
                elif part.startswith('#'):  # ID  
                    id_name = part[1:]
                    # Buscar IDs similares
                    all_ids = [el.get('id') for el in soup.find_all(attrs={'id': True})]
                    similar_ids = [i for i in all_ids if i and id_name.lower() in i.lower()]
                    suggestions.extend([f"#{i}" for i in similar_ids[:3]])
        
        except Exception:
            pass
        
        return list(set(suggestions))
    
    async def _diagnose_connectivity(self, url: str) -> List[str]:
        """🌐 Diagnosticar problemas de conectividad"""
        issues = []
        
        try:
            # Análisis básico de URL
            parsed = urlparse(url)
            
            if not parsed.scheme:
                issues.append("URL sin esquema (http/https)")
            if not parsed.netloc:
                issues.append("URL sin dominio válido")
                
            # TODO: Implementar más checks de conectividad
            # - DNS resolution
            # - SSL certificate validation
            # - Response codes
            
        except Exception as e:
            issues.append(f"Error analizando URL: {str(e)}")
        
        return issues
    
    async def _diagnose_selectors(self, html_path: str, 
                                expected_selectors: Dict[str, str]) -> Dict[str, Any]:
        """🎯 Diagnosticar problemas con selectores"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return await self._analyze_html_selectors(
                html_content, list(expected_selectors.values()), "diagnostic"
            )
            
        except Exception as e:
            logger.error(f"💥 Error en diagnóstico de selectores: {str(e)}")
            return {}
    
    async def _measure_page_performance(self, url: str) -> Dict[str, float]:
        """⚡ Medir métricas de performance de página"""
        metrics = {}
        
        try:
            if not self.browser:
                return metrics
                
            page = await self.browser.new_page()
            
            try:
                start_time = datetime.now()
                await page.goto(url, timeout=60000)
                load_time = (datetime.now() - start_time).total_seconds()
                
                metrics['load_time'] = load_time
                
                # Métricas adicionales usando JavaScript
                performance_metrics = await page.evaluate("""
                    () => {
                        const perfData = performance.getEntriesByType('navigation')[0];
                        return {
                            dns_lookup: perfData.domainLookupEnd - perfData.domainLookupStart,
                            tcp_connect: perfData.connectEnd - perfData.connectStart,
                            dom_content_loaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                            dom_complete: perfData.domComplete - perfData.navigationStart
                        };
                    }
                """)
                
                metrics.update(performance_metrics)
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.warning(f"⚠️  Error midiendo performance: {str(e)}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _analyze_error_logs(self, error_logs: List[str]) -> Dict[str, List[str]]:
        """📋 Analizar logs de error para extraer patrones"""
        issues = []
        recommendations = []
        
        error_text = ' '.join(error_logs).lower()
        
        # Patrones comunes de error
        patterns = {
            'timeout': {
                'issue': 'Timeouts frecuentes detectados',
                'recommendation': 'Aumentar timeouts y optimizar wait conditions'
            },
            'blocked': {
                'issue': 'Posible bloqueo por parte del sitio web',
                'recommendation': 'Revisar user agents y implementar rotación de IPs'
            },
            'selector not found': {
                'issue': 'Selectores CSS no encuentran elementos',
                'recommendation': 'Actualizar selectores CSS y verificar estructura HTML'
            },
            'connection': {
                'issue': 'Problemas de conexión de red',
                'recommendation': 'Verificar conectividad y configuración de proxies'
            },
            'memory': {
                'issue': 'Problemas de memoria detectados',
                'recommendation': 'Optimizar gestión de memoria y cerrar recursos'
            }
        }
        
        for pattern, info in patterns.items():
            if pattern in error_text:
                issues.append(info['issue'])
                recommendations.append(info['recommendation'])
        
        return {'issues': issues, 'recommendations': recommendations}
    
    async def _save_diagnostic_report(self, result: DiagnosticResult) -> None:
        """💾 Guardar reporte de diagnóstico"""
        try:
            timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostic_{result.retailer}_{timestamp}.json"
            report_path = self.diagnostics_dir / filename
            
            # Convertir a diccionario serializable
            report_data = asdict(result)
            report_data['timestamp'] = result.timestamp.isoformat()
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Reporte de diagnóstico guardado: {report_path}")
            
        except Exception as e:
            logger.error(f"💥 Error guardando reporte: {str(e)}")

# 🎯 FUNCIONES DE UTILIDAD PARA MANTENIMIENTO RÁPIDO

async def quick_diagnostic(url: str, retailer: str) -> DiagnosticResult:
    """
    ⚡ Diagnóstico rápido de una URL problemática
    
    Args:
        url: URL a diagnosticar
        retailer: Nombre del retailer
        
    Returns:
        DiagnosticResult: Resultado del diagnóstico
    """
    async with MaintenanceToolkit() as toolkit:
        # Selectores básicos para el diagnóstico
        basic_selectors = {
            'products': '.product, .item, [data-product]',
            'prices': '.price, .cost, .amount',
            'names': '.name, .title, h1, h2, h3'
        }
        
        result = await toolkit.diagnose_scraper_issues(
            url, retailer, basic_selectors
        )
        
        return result

async def capture_error_page(url: str, retailer: str, error_context: str = "") -> Optional[str]:
    """
    📸 Capturar screenshot rápido de página con error
    
    Args:
        url: URL problemática
        retailer: Nombre del retailer  
        error_context: Contexto del error
        
    Returns:
        str: Ruta al screenshot o None si falla
    """
    async with MaintenanceToolkit() as toolkit:
        return await toolkit.capture_failure_screenshot(url, retailer, error_context)

if __name__ == "__main__":
    """🛠️ Ejecutar herramientas desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🛠️ Scraper v5 Maintenance Tools")
    parser.add_argument('--diagnose', nargs=2, metavar=('URL', 'RETAILER'),
                       help='Diagnosticar URL problemática')
    parser.add_argument('--screenshot', nargs=2, metavar=('URL', 'RETAILER'), 
                       help='Capturar screenshot de página')
    parser.add_argument('--html-dump', nargs=2, metavar=('URL', 'RETAILER'),
                       help='Extraer HTML para análisis')
    
    args = parser.parse_args()
    
    async def main():
        if args.diagnose:
            url, retailer = args.diagnose
            result = await quick_diagnostic(url, retailer)
            
            print(f"🩺 Diagnóstico completado - Severidad: {result.severity.upper()}")
            print(f"🚨 Issues: {len(result.issues_found)}")
            for issue in result.issues_found:
                print(f"   - {issue}")
            print(f"💡 Recomendaciones: {len(result.recommendations)}")
            for rec in result.recommendations:
                print(f"   - {rec}")
                
        elif args.screenshot:
            url, retailer = args.screenshot
            screenshot_path = await capture_error_page(url, retailer)
            if screenshot_path:
                print(f"📸 Screenshot guardado: {screenshot_path}")
            else:
                print("❌ Error capturando screenshot")
                
        elif args.html_dump:
            url, retailer = args.html_dump
            async with MaintenanceToolkit() as toolkit:
                html_path = await toolkit.dump_html_for_analysis(url, retailer)
                if html_path:
                    print(f"📄 HTML guardado: {html_path}")
                else:
                    print("❌ Error extrayendo HTML")
        else:
            parser.print_help()
    
    asyncio.run(main())