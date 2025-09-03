# -*- coding: utf-8 -*-
"""
🔍 ML Failure Detector - Sistema de Detección Inteligente de Fallos
==================================================================

Detector de fallos basado en ML que identifica patrones de errores recurrentes,
captura screenshots automáticamente y extrae HTML para análisis posterior.

Funcionalidades:
- Detección automática de páginas bloqueadas/fallidas
- Captura de screenshots para análisis visual
- Extracción y almacenamiento de HTML problemático
- Clasificación de tipos de error con ML
- Predicción de probabilidad de éxito
- Sistema de learning continuo

Autor: Sistema Scraper v5 🚀
"""

import os
import json
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import pandas as pd
from bs4 import BeautifulSoup
import requests
from playwright.async_api import Page, Browser


@dataclass
class FailurePattern:
    """📊 Patrón de fallo detectado"""
    pattern_id: str
    error_type: str
    frequency: int
    success_rate: float
    html_signatures: List[str]
    visual_features: Dict[str, float]
    retailer: str
    url_pattern: str
    last_seen: datetime
    confidence: float
    recovery_suggestions: List[str]


@dataclass
class PageAnalysis:
    """🔍 Análisis completo de página"""
    url: str
    retailer: str
    timestamp: datetime
    html_content: str
    screenshot_path: str
    is_blocked: bool
    block_probability: float
    error_indicators: List[str]
    visual_anomalies: List[str]
    loading_time: float
    response_code: int
    content_length: int
    has_products: bool
    captcha_detected: bool
    rate_limit_detected: bool


class MLFailureDetector:
    """🤖 Detector ML de Fallos - El Sherlock Holmes del Scraping"""
    
    def __init__(self, storage_path: str = "./scraper_v5/data/failure_analysis"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Paths específicos
        self.screenshots_path = self.storage_path / "screenshots"
        self.html_dumps_path = self.storage_path / "html_dumps"
        self.models_path = self.storage_path / "models"
        self.patterns_path = self.storage_path / "patterns"
        
        # Crear directorios
        for path in [self.screenshots_path, self.html_dumps_path, self.models_path, self.patterns_path]:
            path.mkdir(exist_ok=True)
        
        # Modelos ML
        self.block_classifier: Optional[RandomForestClassifier] = None
        self.html_vectorizer: Optional[TfidfVectorizer] = None
        self.feature_scaler: Optional[StandardScaler] = None
        
        # Patrones detectados
        self.failure_patterns: Dict[str, FailurePattern] = {}
        
        # Configuración
        self.min_pattern_frequency = 3
        self.confidence_threshold = 0.7
        self.max_screenshots_per_hour = 50
        self.max_html_dumps_per_day = 200
        
        # Indicadores de bloqueo conocidos
        self.block_indicators = {
            'html_keywords': [
                'blocked', 'forbidden', 'access denied', 'rate limit',
                'too many requests', 'cloudflare', 'captcha', 'verificación',
                'robot', 'bot detection', 'suspicious activity', 'temporary block'
            ],
            'visual_indicators': [
                'captcha_box', 'cloudflare_logo', 'block_message',
                'access_denied_icon', 'rate_limit_warning'
            ],
            'http_codes': [403, 429, 503, 502, 504],
            'response_patterns': [
                r'challenge.*cloudflare',
                r'access.*denied',
                r'rate.*limit',
                r'temporarily.*unavailable'
            ]
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        self._init_logger()
        
        # Cargar modelos y patrones existentes
        self._load_models()
        self._load_patterns()
        
        self.logger.info("🔍 ML Failure Detector inicializado correctamente")

    def _init_logger(self) -> None:
        """🔧 Inicializar sistema de logging"""
        log_path = self.storage_path / "failure_detector.log"
        
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _load_models(self) -> None:
        """📥 Cargar modelos ML existentes"""
        try:
            classifier_path = self.models_path / "block_classifier.joblib"
            vectorizer_path = self.models_path / "html_vectorizer.joblib"
            scaler_path = self.models_path / "feature_scaler.joblib"
            
            if classifier_path.exists():
                self.block_classifier = joblib.load(classifier_path)
                self.logger.info("✅ Clasificador de bloqueos cargado")
            
            if vectorizer_path.exists():
                self.html_vectorizer = joblib.load(vectorizer_path)
                self.logger.info("✅ Vectorizador HTML cargado")
            
            if scaler_path.exists():
                self.feature_scaler = joblib.load(scaler_path)
                self.logger.info("✅ Escalador de características cargado")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando modelos: {e}")

    def _save_models(self) -> None:
        """💾 Guardar modelos ML entrenados"""
        try:
            if self.block_classifier:
                joblib.dump(self.block_classifier, self.models_path / "block_classifier.joblib")
            
            if self.html_vectorizer:
                joblib.dump(self.html_vectorizer, self.models_path / "html_vectorizer.joblib")
            
            if self.feature_scaler:
                joblib.dump(self.feature_scaler, self.models_path / "feature_scaler.joblib")
            
            self.logger.info("✅ Modelos ML guardados correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando modelos: {e}")

    def _load_patterns(self) -> None:
        """📥 Cargar patrones de fallo existentes"""
        patterns_file = self.patterns_path / "failure_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                
                for pattern_id, pattern_dict in patterns_data.items():
                    # Convertir datetime strings de vuelta a datetime
                    pattern_dict['last_seen'] = datetime.fromisoformat(pattern_dict['last_seen'])
                    self.failure_patterns[pattern_id] = FailurePattern(**pattern_dict)
                
                self.logger.info(f"✅ Cargados {len(self.failure_patterns)} patrones de fallo")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error cargando patrones: {e}")

    def _save_patterns(self) -> None:
        """💾 Guardar patrones de fallo detectados"""
        patterns_file = self.patterns_path / "failure_patterns.json"
        
        try:
            patterns_dict = {}
            for pattern_id, pattern in self.failure_patterns.items():
                pattern_dict = asdict(pattern)
                # Convertir datetime a string
                pattern_dict['last_seen'] = pattern.last_seen.isoformat()
                patterns_dict[pattern_id] = pattern_dict
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Guardados {len(patterns_dict)} patrones de fallo")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando patrones: {e}")

    async def analyze_page(
        self, 
        page: Page, 
        url: str, 
        retailer: str,
        capture_evidence: bool = True
    ) -> PageAnalysis:
        """🔍 Analizar página en busca de fallos y capturas de evidencia"""
        
        start_time = datetime.now()
        
        try:
            # Información básica
            response_code = 200  # Por defecto, se actualizará si hay error
            content_length = 0
            
            # Obtener HTML
            html_content = await page.content()
            content_length = len(html_content)
            
            # Análisis HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detección de indicadores
            is_blocked = await self._detect_blocking(page, html_content, soup)
            block_probability = await self._calculate_block_probability(html_content, soup)
            error_indicators = self._find_error_indicators(html_content, soup)
            captcha_detected = self._detect_captcha(soup)
            rate_limit_detected = self._detect_rate_limit(soup)
            has_products = self._detect_products(soup, retailer)
            
            # Captura de evidencia si es necesario
            screenshot_path = ""
            if capture_evidence and (is_blocked or block_probability > 0.5):
                screenshot_path = await self._capture_screenshot(page, url, retailer)
                await self._save_html_dump(html_content, url, retailer)
            
            # Análisis visual (si hay screenshot)
            visual_anomalies = []
            if screenshot_path and os.path.exists(screenshot_path):
                visual_anomalies = await self._analyze_visual_anomalies(screenshot_path)
            
            loading_time = (datetime.now() - start_time).total_seconds()
            
            analysis = PageAnalysis(
                url=url,
                retailer=retailer,
                timestamp=datetime.now(),
                html_content=html_content,
                screenshot_path=screenshot_path,
                is_blocked=is_blocked,
                block_probability=block_probability,
                error_indicators=error_indicators,
                visual_anomalies=visual_anomalies,
                loading_time=loading_time,
                response_code=response_code,
                content_length=content_length,
                has_products=has_products,
                captcha_detected=captcha_detected,
                rate_limit_detected=rate_limit_detected
            )
            
            # Actualizar patrones
            await self._update_failure_patterns(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analizando página {url}: {e}")
            
            # Análisis básico de emergencia
            return PageAnalysis(
                url=url,
                retailer=retailer,
                timestamp=datetime.now(),
                html_content="",
                screenshot_path="",
                is_blocked=True,
                block_probability=1.0,
                error_indicators=[f"Analysis error: {str(e)}"],
                visual_anomalies=[],
                loading_time=(datetime.now() - start_time).total_seconds(),
                response_code=500,
                content_length=0,
                has_products=False,
                captcha_detected=False,
                rate_limit_detected=False
            )

    async def _detect_blocking(self, page: Page, html_content: str, soup: BeautifulSoup) -> bool:
        """🚫 Detectar si la página está bloqueada"""
        
        # 1. Verificar palabras clave en HTML
        html_lower = html_content.lower()
        for keyword in self.block_indicators['html_keywords']:
            if keyword in html_lower:
                return True
        
        # 2. Verificar título de la página
        title = await page.title()
        if title:
            title_lower = title.lower()
            for keyword in ['blocked', 'access denied', 'forbidden', 'cloudflare']:
                if keyword in title_lower:
                    return True
        
        # 3. Verificar elementos visuales específicos
        try:
            # Detectar Cloudflare
            cloudflare_elements = await page.query_selector_all('[data-ray]')
            if cloudflare_elements:
                return True
            
            # Detectar CAPTCHA
            captcha_elements = await page.query_selector_all('iframe[src*="captcha"]')
            if captcha_elements:
                return True
            
        except Exception as e:
            self.logger.debug(f"Error en detección visual: {e}")
        
        # 4. Verificar contenido mínimo esperado
        if len(html_content.strip()) < 1000:  # Página muy pequeña, posible bloqueo
            return True
        
        return False

    async def _calculate_block_probability(self, html_content: str, soup: BeautifulSoup) -> float:
        """📊 Calcular probabilidad de bloqueo usando ML"""
        
        if not self.block_classifier:
            # Fallback: análisis basado en reglas
            return self._rule_based_block_probability(html_content, soup)
        
        try:
            # Extraer características
            features = self._extract_features(html_content, soup)
            
            # Vectorizar HTML si hay vectorizador
            if self.html_vectorizer:
                html_features = self.html_vectorizer.transform([html_content])
                features = np.concatenate([features, html_features.toarray().flatten()])
            
            # Escalar características
            if self.feature_scaler:
                features = self.feature_scaler.transform([features])
            else:
                features = [features]
            
            # Predecir probabilidad
            probability = self.block_classifier.predict_proba(features)[0][1]  # Probabilidad de clase "blocked"
            
            return float(probability)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en predicción ML: {e}")
            return self._rule_based_block_probability(html_content, soup)

    def _rule_based_block_probability(self, html_content: str, soup: BeautifulSoup) -> float:
        """📐 Calcular probabilidad usando reglas predefinidas"""
        
        score = 0.0
        max_score = 10.0
        
        html_lower = html_content.lower()
        
        # Palabras clave de bloqueo (peso: 3.0)
        for keyword in self.block_indicators['html_keywords']:
            if keyword in html_lower:
                score += 3.0
                break
        
        # Elementos de CAPTCHA (peso: 4.0)
        if soup.find('iframe', src=lambda x: x and 'captcha' in x.lower()):
            score += 4.0
        
        # Cloudflare indicators (peso: 3.5)
        if soup.find(attrs={'data-ray': True}) or 'cloudflare' in html_lower:
            score += 3.5
        
        # Contenido muy pequeño (peso: 2.0)
        if len(html_content.strip()) < 1000:
            score += 2.0
        
        # JavaScript de verificación (peso: 1.5)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and any(word in script.string.lower() for word in ['challenge', 'verify', 'protection']):
                score += 1.5
                break
        
        return min(score / max_score, 1.0)

    def _extract_features(self, html_content: str, soup: BeautifulSoup) -> np.ndarray:
        """🔧 Extraer características numéricas para ML"""
        
        features = []
        
        # Características básicas
        features.append(len(html_content))  # Tamaño HTML
        features.append(len(soup.find_all()))  # Número total de elementos
        features.append(len(soup.find_all('script')))  # Scripts
        features.append(len(soup.find_all('img')))  # Imágenes
        features.append(len(soup.find_all('a')))  # Enlaces
        
        # Características de texto
        text_content = soup.get_text()
        features.append(len(text_content))  # Tamaño texto
        features.append(len(text_content.split()))  # Palabras
        
        # Indicadores de bloqueo
        html_lower = html_content.lower()
        for keyword in self.block_indicators['html_keywords']:
            features.append(1 if keyword in html_lower else 0)
        
        # Elementos específicos
        features.append(1 if soup.find('iframe', src=lambda x: x and 'captcha' in x.lower()) else 0)
        features.append(1 if soup.find(attrs={'data-ray': True}) else 0)
        features.append(1 if 'cloudflare' in html_lower else 0)
        
        return np.array(features)

    def _find_error_indicators(self, html_content: str, soup: BeautifulSoup) -> List[str]:
        """🔍 Encontrar indicadores específicos de error"""
        
        indicators = []
        html_lower = html_content.lower()
        
        # Mensajes de error específicos
        error_messages = [
            'access denied', 'forbidden', 'blocked', 'rate limit exceeded',
            'too many requests', 'temporarily unavailable', 'service unavailable',
            'cloudflare security', 'bot detection', 'suspicious activity'
        ]
        
        for message in error_messages:
            if message in html_lower:
                indicators.append(f"error_message: {message}")
        
        # Elementos HTML específicos
        if soup.find('div', class_=lambda x: x and 'error' in x.lower()):
            indicators.append("error_div_found")
        
        if soup.find('title', string=lambda x: x and any(err in x.lower() for err in ['error', 'forbidden', 'denied'])):
            indicators.append("error_in_title")
        
        # Meta tags de error
        error_meta = soup.find('meta', attrs={'name': 'robots', 'content': 'noindex'})
        if error_meta:
            indicators.append("noindex_meta_tag")
        
        return indicators

    def _detect_captcha(self, soup: BeautifulSoup) -> bool:
        """🤖 Detectar presencia de CAPTCHA"""
        
        # reCAPTCHA
        if soup.find('div', class_='g-recaptcha'):
            return True
        
        # hCaptcha
        if soup.find('div', class_='h-captcha'):
            return True
        
        # CAPTCHA genérico en iframe
        captcha_iframe = soup.find('iframe', src=lambda x: x and 'captcha' in x.lower())
        if captcha_iframe:
            return True
        
        # Cloudflare challenge
        if soup.find('form', id='challenge-form'):
            return True
        
        return False

    def _detect_rate_limit(self, soup: BeautifulSoup) -> bool:
        """⏰ Detectar límite de velocidad"""
        
        text_content = soup.get_text().lower()
        
        rate_limit_indicators = [
            'rate limit', 'too many requests', '429', 'retry after',
            'request limit', 'api limit', 'throttled'
        ]
        
        for indicator in rate_limit_indicators:
            if indicator in text_content:
                return True
        
        return False

    def _detect_products(self, soup: BeautifulSoup, retailer: str) -> bool:
        """🛍️ Detectar si hay productos en la página"""
        
        # Selectores comunes de productos por retailer
        product_selectors = {
            'ripley': ['.product-item', '.catalog-product-item', '[data-testid="product"]'],
            'falabella': ['.product-item', '.ProductItem', '.product-card'],
            'paris': ['.product-item', '.item-product', '.product-card'],
            'hites': ['.product-item', '.producto', '.item'],
            'abcdin': ['.product-item', '.producto', '.product'],
            'mercadolibre': ['.ui-search-result', '.item', '.product-item']
        }
        
        selectors = product_selectors.get(retailer, ['.product-item', '.product', '.item'])
        
        for selector in selectors:
            if soup.select(selector):
                return True
        
        # Búsqueda genérica
        product_keywords = ['precio', 'price', '$', 'producto', 'product', 'agregar', 'comprar', 'add to cart']
        text_content = soup.get_text().lower()
        
        product_count = sum(1 for keyword in product_keywords if keyword in text_content)
        
        return product_count >= 3  # Al menos 3 indicadores de productos

    async def _capture_screenshot(self, page: Page, url: str, retailer: str) -> str:
        """📸 Capturar screenshot de la página"""
        
        try:
            # Generar nombre único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{retailer}_{timestamp}_{url_hash}.png"
            filepath = self.screenshots_path / filename
            
            # Capturar screenshot
            await page.screenshot(path=str(filepath), full_page=True)
            
            self.logger.info(f"📸 Screenshot capturado: {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error capturando screenshot: {e}")
            return ""

    async def _save_html_dump(self, html_content: str, url: str, retailer: str) -> str:
        """💾 Guardar dump de HTML para análisis"""
        
        try:
            # Generar nombre único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{retailer}_{timestamp}_{url_hash}.html"
            filepath = self.html_dumps_path / filename
            
            # Guardar HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"💾 HTML dump guardado: {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando HTML: {e}")
            return ""

    async def _analyze_visual_anomalies(self, screenshot_path: str) -> List[str]:
        """👁️ Analizar anomalías visuales en screenshot"""
        
        anomalies = []
        
        try:
            # Cargar imagen
            img = cv2.imread(screenshot_path)
            if img is None:
                return ["error_loading_image"]
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detectar texto (posible CAPTCHA)
            text_areas = self._detect_text_areas(gray)
            if len(text_areas) < 5:  # Muy poco texto, posible bloqueo
                anomalies.append("minimal_text_detected")
            
            # Detectar colores predominantes
            colors = self._analyze_color_distribution(img)
            if colors.get('red', 0) > 0.3:  # Mucho rojo, posible error
                anomalies.append("high_red_content")
            
            # Detectar patrones geométricos (posible CAPTCHA)
            if self._detect_geometric_patterns(gray):
                anomalies.append("geometric_patterns_detected")
            
            # Verificar si la imagen es muy uniforme (página en blanco)
            if self._is_uniform_image(gray):
                anomalies.append("uniform_blank_page")
            
        except Exception as e:
            self.logger.error(f"❌ Error en análisis visual: {e}")
            anomalies.append(f"analysis_error: {str(e)}")
        
        return anomalies

    def _detect_text_areas(self, gray_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """📝 Detectar áreas de texto en imagen"""
        
        try:
            # Usar detección de contornos para encontrar áreas de texto
            edges = cv2.Canny(gray_image, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_areas = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filtrar por tamaño típico de texto
                if 10 < w < 200 and 5 < h < 50:
                    text_areas.append((x, y, w, h))
            
            return text_areas
            
        except Exception:
            return []

    def _analyze_color_distribution(self, image: np.ndarray) -> Dict[str, float]:
        """🎨 Analizar distribución de colores"""
        
        try:
            # Convertir a HSV para mejor análisis de color
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            total_pixels = image.shape[0] * image.shape[1]
            
            # Definir rangos de color
            red_lower = np.array([0, 50, 50])
            red_upper = np.array([10, 255, 255])
            red_mask = cv2.inRange(hsv, red_lower, red_upper)
            
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            
            # Calcular proporciones
            red_ratio = np.sum(red_mask > 0) / total_pixels
            blue_ratio = np.sum(blue_mask > 0) / total_pixels
            
            return {
                'red': red_ratio,
                'blue': blue_ratio
            }
            
        except Exception:
            return {'red': 0, 'blue': 0}

    def _detect_geometric_patterns(self, gray_image: np.ndarray) -> bool:
        """🔷 Detectar patrones geométricos (CAPTCHA)"""
        
        try:
            # Detectar círculos (común en CAPTCHAs)
            circles = cv2.HoughCircles(
                gray_image, cv2.HOUGH_GRADIENT, 1, 20,
                param1=50, param2=30, minRadius=10, maxRadius=100
            )
            
            if circles is not None:
                return len(circles[0]) > 2  # Múltiples círculos
            
            # Detectar líneas (grids en CAPTCHAs)
            edges = cv2.Canny(gray_image, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
            
            if lines is not None:
                return len(lines) > 10  # Muchas líneas, posible grid
            
            return False
            
        except Exception:
            return False

    def _is_uniform_image(self, gray_image: np.ndarray) -> bool:
        """📄 Verificar si imagen es uniforme (página en blanco)"""
        
        try:
            # Calcular desviación estándar
            std_dev = np.std(gray_image)
            
            # Si la desviación es muy baja, la imagen es uniforme
            return std_dev < 10
            
        except Exception:
            return False

    async def _update_failure_patterns(self, analysis: PageAnalysis) -> None:
        """🔄 Actualizar patrones de fallo con nuevo análisis"""
        
        if not analysis.is_blocked and analysis.block_probability < 0.5:
            return  # No es un fallo, no actualizar
        
        # Generar ID del patrón
        pattern_elements = [
            analysis.retailer,
            analysis.url.split('/')[-2] if '/' in analysis.url else 'root',
            'blocked' if analysis.is_blocked else 'suspicious'
        ]
        pattern_id = '_'.join(pattern_elements)
        
        # HTML signatures (primeros indicadores encontrados)
        html_signatures = analysis.error_indicators[:3]
        
        # Características visuales
        visual_features = {
            'has_screenshot': bool(analysis.screenshot_path),
            'anomaly_count': len(analysis.visual_anomalies),
            'loading_time': analysis.loading_time,
            'content_length': analysis.content_length
        }
        
        # Sugerencias de recuperación
        recovery_suggestions = self._generate_recovery_suggestions(analysis)
        
        if pattern_id in self.failure_patterns:
            # Actualizar patrón existente
            pattern = self.failure_patterns[pattern_id]
            pattern.frequency += 1
            pattern.last_seen = analysis.timestamp
            pattern.confidence = min(pattern.confidence + 0.1, 1.0)
            
            # Actualizar signatures (agregar nuevas)
            for signature in html_signatures:
                if signature not in pattern.html_signatures:
                    pattern.html_signatures.append(signature)
                    pattern.html_signatures = pattern.html_signatures[-5:]  # Mantener últimas 5
            
        else:
            # Crear nuevo patrón
            error_type = self._classify_error_type(analysis)
            
            pattern = FailurePattern(
                pattern_id=pattern_id,
                error_type=error_type,
                frequency=1,
                success_rate=0.0,  # Se calculará con el tiempo
                html_signatures=html_signatures,
                visual_features=visual_features,
                retailer=analysis.retailer,
                url_pattern=self._extract_url_pattern(analysis.url),
                last_seen=analysis.timestamp,
                confidence=0.5,
                recovery_suggestions=recovery_suggestions
            )
            
            self.failure_patterns[pattern_id] = pattern
        
        # Guardar patrones actualizados
        self._save_patterns()

    def _classify_error_type(self, analysis: PageAnalysis) -> str:
        """🏷️ Clasificar tipo de error basado en análisis"""
        
        if analysis.captcha_detected:
            return "captcha"
        
        if analysis.rate_limit_detected:
            return "rate_limit"
        
        if 'cloudflare' in ' '.join(analysis.error_indicators).lower():
            return "cloudflare_protection"
        
        if analysis.response_code in [403, 429]:
            return "http_blocking"
        
        if analysis.content_length < 1000:
            return "empty_response"
        
        if not analysis.has_products:
            return "no_products"
        
        return "unknown_blocking"

    def _extract_url_pattern(self, url: str) -> str:
        """🔗 Extraer patrón de URL para agrupación"""
        
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            
            # Generalizar partes numéricas y específicas
            generalized_parts = []
            for part in path_parts:
                if part.isdigit():
                    generalized_parts.append("{id}")
                elif len(part) > 20:  # Probablemente un ID largo
                    generalized_parts.append("{long_id}")
                else:
                    generalized_parts.append(part)
            
            return f"{parsed.netloc}{'/' + '/'.join(generalized_parts) if generalized_parts else ''}"
            
        except Exception:
            return url.split('?')[0]  # Fallback: URL sin parámetros

    def _generate_recovery_suggestions(self, analysis: PageAnalysis) -> List[str]:
        """💡 Generar sugerencias de recuperación"""
        
        suggestions = []
        
        if analysis.captcha_detected:
            suggestions.extend([
                "Cambiar user agent",
                "Usar proxy diferente",
                "Esperar antes de reintentar",
                "Usar navegador con extensiones anti-detección"
            ])
        
        if analysis.rate_limit_detected:
            suggestions.extend([
                "Reducir velocidad de scraping",
                "Implementar backoff exponencial",
                "Rotar proxies más frecuentemente"
            ])
        
        if 'cloudflare' in ' '.join(analysis.error_indicators).lower():
            suggestions.extend([
                "Usar navegador real con stealth mode",
                "Implementar resolución de challenges",
                "Cambiar datacenter del proxy"
            ])
        
        if analysis.loading_time > 10:
            suggestions.extend([
                "Aumentar timeout",
                "Verificar conectividad",
                "Usar proxy más rápido"
            ])
        
        if not suggestions:
            suggestions = [
                "Cambiar estrategia de scraping",
                "Verificar selectores CSS",
                "Revisar logs detallados"
            ]
        
        return suggestions

    def get_failure_report(self, retailer: str = None, hours: int = 24) -> Dict[str, Any]:
        """📊 Generar reporte de fallos"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filtrar patrones
        relevant_patterns = {}
        for pattern_id, pattern in self.failure_patterns.items():
            if pattern.last_seen >= cutoff_time:
                if retailer is None or pattern.retailer == retailer:
                    relevant_patterns[pattern_id] = pattern
        
        # Estadísticas generales
        total_patterns = len(relevant_patterns)
        error_types = {}
        for pattern in relevant_patterns.values():
            error_types[pattern.error_type] = error_types.get(pattern.error_type, 0) + 1
        
        # Top errores por frecuencia
        top_errors = sorted(relevant_patterns.values(), key=lambda x: x.frequency, reverse=True)[:10]
        
        # Patrones por retailer
        retailer_stats = {}
        for pattern in relevant_patterns.values():
            ret = pattern.retailer
            if ret not in retailer_stats:
                retailer_stats[ret] = {'count': 0, 'types': set()}
            retailer_stats[ret]['count'] += 1
            retailer_stats[ret]['types'].add(pattern.error_type)
        
        # Convertir sets a lists para JSON serialization
        for ret_stat in retailer_stats.values():
            ret_stat['types'] = list(ret_stat['types'])
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'period_hours': hours,
            'retailer_filter': retailer,
            'summary': {
                'total_patterns': total_patterns,
                'error_types': error_types,
                'retailers_affected': len(retailer_stats)
            },
            'top_errors': [
                {
                    'pattern_id': p.pattern_id,
                    'error_type': p.error_type,
                    'frequency': p.frequency,
                    'confidence': p.confidence,
                    'last_seen': p.last_seen.isoformat(),
                    'recovery_suggestions': p.recovery_suggestions[:3]
                }
                for p in top_errors
            ],
            'retailer_breakdown': retailer_stats,
            'recommendations': self._generate_recommendations(relevant_patterns)
        }
        
        return report

    def _generate_recommendations(self, patterns: Dict[str, FailurePattern]) -> List[str]:
        """💡 Generar recomendaciones basadas en patrones"""
        
        recommendations = []
        
        # Analizar tipos de error más comunes
        error_counts = {}
        for pattern in patterns.values():
            error_counts[pattern.error_type] = error_counts.get(pattern.error_type, 0) + 1
        
        most_common_error = max(error_counts.items(), key=lambda x: x[1]) if error_counts else None
        
        if most_common_error:
            error_type, count = most_common_error
            
            if error_type == "captcha":
                recommendations.append(f"🤖 {count} CAPTCHAs detectados - Implementar solving automático")
            
            elif error_type == "rate_limit":
                recommendations.append(f"⏰ {count} rate limits - Reducir velocidad de scraping")
            
            elif error_type == "cloudflare_protection":
                recommendations.append(f"☁️ {count} bloqueos Cloudflare - Mejorar stealth mode")
        
        # Recomendaciones por retailers más afectados
        retailer_counts = {}
        for pattern in patterns.values():
            retailer_counts[pattern.retailer] = retailer_counts.get(pattern.retailer, 0) + 1
        
        if retailer_counts:
            most_affected = max(retailer_counts.items(), key=lambda x: x[1])
            recommendations.append(f"🏪 {most_affected[0]} es el más afectado ({most_affected[1]} patrones)")
        
        # Recomendaciones generales
        if len(patterns) > 50:
            recommendations.append("📈 Alto volumen de fallos - Revisar configuración general")
        
        if not recommendations:
            recommendations.append("✅ No se detectaron patrones críticos")
        
        return recommendations

    async def train_models(self, force_retrain: bool = False) -> bool:
        """🎓 Entrenar modelos ML con datos históricos"""
        
        if not force_retrain and self.block_classifier is not None:
            self.logger.info("🎓 Modelos ya entrenados, usar force_retrain=True para re-entrenar")
            return True
        
        try:
            # Preparar datos de entrenamiento
            training_data = self._prepare_training_data()
            
            if len(training_data) < 50:
                self.logger.warning("⚠️ Datos insuficientes para entrenar modelos ML")
                return False
            
            # Dividir datos
            X_features = [item['features'] for item in training_data]
            X_html = [item['html_content'] for item in training_data]
            y = [item['is_blocked'] for item in training_data]
            
            # Entrenar vectorizador HTML
            self.html_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            X_html_vectorized = self.html_vectorizer.fit_transform(X_html)
            
            # Combinar características
            X_combined = np.column_stack([
                X_features,
                X_html_vectorized.toarray()
            ])
            
            # Escalar características
            self.feature_scaler = StandardScaler()
            X_scaled = self.feature_scaler.fit_transform(X_combined)
            
            # Dividir en train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Entrenar clasificador
            self.block_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.block_classifier.fit(X_train, y_train)
            
            # Evaluar modelo
            train_score = self.block_classifier.score(X_train, y_train)
            test_score = self.block_classifier.score(X_test, y_test)
            
            self.logger.info(f"🎯 Modelo entrenado - Train: {train_score:.3f}, Test: {test_score:.3f}")
            
            # Guardar modelos
            self._save_models()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error entrenando modelos: {e}")
            return False

    def _prepare_training_data(self) -> List[Dict[str, Any]]:
        """📚 Preparar datos de entrenamiento desde HTML dumps"""
        
        training_data = []
        
        try:
            # Cargar HTML dumps existentes
            for html_file in self.html_dumps_path.glob("*.html"):
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Parsear HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extraer características
                    features = self._extract_features(html_content, soup)
                    
                    # Determinar label (basado en nombre del archivo o análisis)
                    filename = html_file.name
                    is_blocked = self._infer_blocking_status(html_content, soup, filename)
                    
                    training_data.append({
                        'features': features,
                        'html_content': html_content,
                        'is_blocked': is_blocked,
                        'filename': filename
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando {html_file}: {e}")
                    continue
            
            self.logger.info(f"📚 Preparados {len(training_data)} ejemplos de entrenamiento")
            
        except Exception as e:
            self.logger.error(f"❌ Error preparando datos: {e}")
        
        return training_data

    def _infer_blocking_status(self, html_content: str, soup: BeautifulSoup, filename: str) -> bool:
        """🔍 Inferir estado de bloqueo para entrenamiento"""
        
        # 1. Basado en nombre de archivo (si incluye indicadores)
        filename_lower = filename.lower()
        if any(word in filename_lower for word in ['blocked', 'error', 'captcha', 'denied']):
            return True
        
        # 2. Basado en análisis de contenido
        block_prob = self._rule_based_block_probability(html_content, soup)
        
        return block_prob > 0.6  # Threshold para clasificar como bloqueado

    def cleanup_old_data(self, days: int = 7) -> Dict[str, int]:
        """🧹 Limpiar datos antiguos para mantener almacenamiento eficiente"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleanup_stats = {
            'screenshots_removed': 0,
            'html_dumps_removed': 0,
            'patterns_removed': 0
        }
        
        try:
            # Limpiar screenshots antiguos
            for screenshot in self.screenshots_path.glob("*.png"):
                if datetime.fromtimestamp(screenshot.stat().st_mtime) < cutoff_date:
                    screenshot.unlink()
                    cleanup_stats['screenshots_removed'] += 1
            
            # Limpiar HTML dumps antiguos
            for html_dump in self.html_dumps_path.glob("*.html"):
                if datetime.fromtimestamp(html_dump.stat().st_mtime) < cutoff_date:
                    html_dump.unlink()
                    cleanup_stats['html_dumps_removed'] += 1
            
            # Limpiar patrones antiguos
            patterns_to_remove = []
            for pattern_id, pattern in self.failure_patterns.items():
                if pattern.last_seen < cutoff_date:
                    patterns_to_remove.append(pattern_id)
            
            for pattern_id in patterns_to_remove:
                del self.failure_patterns[pattern_id]
                cleanup_stats['patterns_removed'] += 1
            
            # Guardar patrones actualizados
            if cleanup_stats['patterns_removed'] > 0:
                self._save_patterns()
            
            self.logger.info(f"🧹 Limpieza completada: {cleanup_stats}")
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza: {e}")
        
        return cleanup_stats