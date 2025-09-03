# -*- coding: utf-8 -*-
"""
🧠 ML Integration V5 - Sistema de Arbitraje Autónomo
===================================================
Integración completa con inteligencia V5 avanzada para matching y detección de oportunidades.
Compatible con emojis y optimizado para operación continua no supervisada.
"""

import logging
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

# Importar componentes V5 avanzados
from ...core.redis_intelligence_system import RedisIntelligenceSystem
from ...core.intelligent_cache_manager import IntelligentCacheManager
from ...core.master_intelligence_integrator import MasterIntelligenceIntegrator
from ...core.scraping_frequency_optimizer import ScrapingFrequencyOptimizer

from ..database.db_manager import DatabaseManagerV5, get_db_manager
from ..config.arbitrage_config import ArbitrageConfigV5, get_config
from ..ml.adapters import MatchScoringAdapter, GlitchDetectionAdapter, NormalizationHubAdapter

logger = logging.getLogger(__name__)

class MLIntegrationV5:
    """
    Integración ML V5 con inteligencia avanzada completa 🚀
    
    Combina:
    - 🧠 Redis Intelligence System  
    - ⚡ Intelligent Cache Manager
    - 🎯 Master Intelligence Integrator
    - 🔍 MatchScoring con V5
    - 📊 Análisis predictivo de oportunidades
    """
    
    def __init__(self, config: Optional[ArbitrageConfigV5] = None):
        """Inicializar ML Integration V5"""
        self.config = config or get_config()
        self.db_manager = get_db_manager(self.config)
        
        # Componentes V5 inteligentes
        self.redis_intelligence = None
        self.cache_manager = None
        self.master_integrator = None
        self.frequency_optimizer = None
        
        # ML Components
        self.match_scorer = None
        self.glitch_detector = None
        self.normalizer = None
        
        # Métricas
        self.matches_processed = 0
        self.opportunities_detected = 0
        self.cache_hits = {'l1': 0, 'l2': 0, 'l3': 0, 'l4': 0}
        self.ml_predictions = 0
        
        logger.info("🧠 MLIntegration V5 inicializando con inteligencia avanzada...")
    
    async def initialize(self):
        """Inicializar todos los componentes V5 🚀"""
        try:
            # Inicializar base de datos
            await self.db_manager.initialize_async_pool()
            
            # Verificar/instalar schema
            if not self.db_manager._schema_initialized:
                logger.info("📋 Instalando schema V5...")
                await self.db_manager.install_schema()
            
            # Inicializar componentes V5
            await self._initialize_v5_components()
            
            # Inicializar ML components
            self._initialize_ml_components()
            
            logger.info("✅ MLIntegration V5 inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando MLIntegration V5: {e}")
            raise
    
    async def _initialize_v5_components(self):
        """Inicializar componentes de inteligencia V5 🧠"""
        try:
            # Redis Intelligence System
            if self.config.use_redis_intelligence:
                self.redis_intelligence = RedisIntelligenceSystem(
                    redis_config=self.config.redis_config
                )
                await self.redis_intelligence.initialize()
                logger.info("🔥 Redis Intelligence System conectado")
            
            # Intelligent Cache Manager  
            if self.config.use_intelligent_cache:
                self.cache_manager = IntelligentCacheManager(
                    l1_size=self.config.cache_l1_size,
                    l2_ttl=self.config.cache_l2_ttl,
                    redis_config=self.config.redis_config
                )
                await self.cache_manager.initialize()
                logger.info("⚡ Intelligent Cache Manager conectado")
            
            # Master Intelligence Integrator
            self.master_integrator = MasterIntelligenceIntegrator()
            await self.master_integrator.initialize()
            logger.info("🎯 Master Intelligence Integrator conectado")
            
            # Scraping Frequency Optimizer
            if self.config.use_volatility_analysis:
                self.frequency_optimizer = ScrapingFrequencyOptimizer(
                    redis_intelligence=self.redis_intelligence
                )
                await self.frequency_optimizer.initialize()
                logger.info("📊 Scraping Frequency Optimizer conectado")
            
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando componentes V5: {e}")
            # Continuar sin componentes V5 si falla
    
    def _initialize_ml_components(self):
        """Inicializar componentes ML 🤖"""
        try:
            # Match Scorer con adapter V5 autónomo
            self.match_scorer = MatchScoringAdapter()
            logger.info("🎯 MatchScoring V5 adapter inicializado")
            
            # Glitch Detector con adapter V5 autónomo
            self.glitch_detector = GlitchDetectionAdapter()
            logger.info("🚨 GlitchDetection V5 adapter inicializado")
            
            # Normalization Hub con adapter V5 autónomo
            self.normalizer = NormalizationHubAdapter()
            logger.info("🔄 Normalization V5 adapter inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando componentes ML: {e}")
            raise
    
    async def find_product_matches(self, products: List[Dict[str, Any]], 
                                 min_similarity: float = None) -> List[Dict[str, Any]]:
        """
        Encontrar matches entre productos usando inteligencia V5 🔍
        
        Args:
            products: Lista de productos a analizar
            min_similarity: Similaridad mínima (usar config si None)
            
        Returns:
            Lista de matches detectados con scoring V5
        """
        min_sim = min_similarity or self.config.min_similarity_score
        matches = []
        
        try:
            logger.info(f"🔍 Analizando {len(products)} productos para matching...")
            
            # Procesar por pares
            for i, product1 in enumerate(products):
                for j, product2 in enumerate(products[i+1:], i+1):
                    
                    # Evitar mismo retailer
                    if product1.get('retailer') == product2.get('retailer'):
                        continue
                    
                    # Buscar en cache inteligente primero
                    cache_key = self._generate_match_cache_key(product1, product2)
                    cached_result = await self._get_cached_match(cache_key)
                    
                    if cached_result:
                        self.cache_hits['l2'] += 1
                        matches.append(cached_result)
                        continue
                    
                    # Calcular similaridad con ML V5
                    similarity_score = await self._calculate_v5_similarity(product1, product2)
                    
                    if similarity_score >= min_sim:
                        # Crear match con análisis V5 completo
                        match_data = await self._create_v5_match(product1, product2, similarity_score)
                        matches.append(match_data)
                        
                        # Guardar en cache
                        await self._cache_match_result(cache_key, match_data)
                        
                        # Guardar en BD
                        match_id = await self.db_manager.save_product_match(match_data)
                        match_data['match_id'] = match_id
                        
                        self.matches_processed += 1
            
            logger.info(f"🎯 Detectados {len(matches)} matches con V5 intelligence")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error en find_product_matches: {e}")
            return matches
    
    async def _calculate_v5_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calcular similaridad usando inteligencia V5 🧠"""
        try:
            if not self.match_scorer:
                return 0.0
            
            # Usar adapter que conecta con V5
            similarity, details = self.match_scorer.calculate_match_score(product1, product2)
            
            # Si tenemos inteligencia V5, enriquecer análisis
            if self.master_integrator:
                # Análisis inteligente de productos
                analysis1 = await self.master_integrator.analyze_product_profile(product1)
                analysis2 = await self.master_integrator.analyze_product_profile(product2)
                
                # Aplicar boost inteligente basado en análisis V5
                intelligence_boost = self._calculate_intelligence_boost(analysis1, analysis2)
                similarity = min(similarity + intelligence_boost, 1.0)
            
            self.ml_predictions += 1
            return similarity
            
        except Exception as e:
            logger.error(f"❌ Error calculando similaridad V5: {e}")
            return 0.0
    
    def _calculate_intelligence_boost(self, analysis1: Dict[str, Any], analysis2: Dict[str, Any]) -> float:
        """Calcular boost inteligente basado en análisis V5 📈"""
        boost = 0.0
        
        try:
            # Boost por misma categoría inteligente
            if (analysis1.get('intelligent_category') and 
                analysis1.get('intelligent_category') == analysis2.get('intelligent_category')):
                boost += 0.05
            
            # Boost por tier similar (productos de importancia similar)
            tier1 = analysis1.get('tier_classification', '')
            tier2 = analysis2.get('tier_classification', '')
            if tier1 and tier1 == tier2:
                boost += 0.03
            
            # Boost por volatilidad similar (comportamiento de precio similar)
            vol1 = analysis1.get('volatility_score', 0)
            vol2 = analysis2.get('volatility_score', 0)
            if abs(vol1 - vol2) < 0.2:  # Volatilidades similares
                boost += 0.02
            
            # Boost por popularidad similar
            pop1 = analysis1.get('popularity_score', 0)
            pop2 = analysis2.get('popularity_score', 0)
            if abs(pop1 - pop2) < 0.3:
                boost += 0.02
            
        except Exception as e:
            logger.debug(f"⚠️ Error calculando intelligence boost: {e}")
        
        return boost
    
    async def _create_v5_match(self, product1: Dict[str, Any], product2: Dict[str, Any], similarity: float) -> Dict[str, Any]:
        """Crear match enriquecido con análisis V5 🎯"""
        try:
            # Determinar cuál es base y cuál match (por código interno)
            codigo_base = product1.get('codigo_interno', product1.get('sku', ''))
            codigo_match = product2.get('codigo_interno', product2.get('sku', ''))
            
            # Análisis detallado con V5
            v5_analysis = {}
            
            if self.master_integrator:
                # Análisis completo de ambos productos
                analysis1 = await self.master_integrator.analyze_product_profile(product1)
                analysis2 = await self.master_integrator.analyze_product_profile(product2)
                
                v5_analysis = {
                    'product1_analysis': analysis1,
                    'product2_analysis': analysis2,
                    'intelligence_comparison': self._compare_intelligence_profiles(analysis1, analysis2)
                }
            
            # Calcular scores componentes
            brand_match_score = self._calculate_brand_similarity(product1, product2)
            model_match_score = self._calculate_model_similarity(product1, product2)
            specs_match_score = self._calculate_specs_similarity(product1, product2)
            
            # Score inteligente V5 (combinando todos los factores)
            v5_intelligence_score = self._calculate_v5_intelligence_score(
                similarity, brand_match_score, model_match_score, specs_match_score, v5_analysis
            )
            
            match_data = {
                'codigo_base': codigo_base,
                'codigo_match': codigo_match,
                'similarity_score': similarity,
                'v5_intelligence_score': v5_intelligence_score,
                'brand_match_score': brand_match_score,
                'model_match_score': model_match_score,
                'specs_match_score': specs_match_score,
                'semantic_similarity': similarity,  # Para compatibilidad
                'match_type': 'cross_retailer',
                'match_confidence': self._determine_confidence(v5_intelligence_score),
                'match_reason': f'V5 ML matching - Similarity: {similarity:.3f}',
                'match_features': {
                    'brand_match': brand_match_score > 0.8,
                    'model_match': model_match_score > 0.6,
                    'specs_match': specs_match_score > 0.5,
                    'v5_analysis': True
                },
                'v5_analysis': v5_analysis,
                'ml_model_version': 'v5.0.0',
                'redis_cache_key': self._generate_match_cache_key(product1, product2),
                'product1': product1,  # Para referencia
                'product2': product2   # Para referencia
            }
            
            return match_data
            
        except Exception as e:
            logger.error(f"❌ Error creando match V5: {e}")
            return {}
    
    def _calculate_v5_intelligence_score(self, similarity: float, brand_score: float, 
                                       model_score: float, specs_score: float,
                                       v5_analysis: Dict[str, Any]) -> float:
        """Calcular score inteligente V5 combinando todos los factores 🧠"""
        try:
            # Score base de similaridad ML
            base_score = similarity * 0.40  # 40%
            
            # Scores de componentes específicos
            component_score = (brand_score * 0.25 +   # 25% marca
                             model_score * 0.20 +    # 20% modelo  
                             specs_score * 0.15) / 1.0  # 15% specs
            
            # Score inteligencia V5
            intelligence_score = 0.0
            if v5_analysis.get('intelligence_comparison'):
                intel_comp = v5_analysis['intelligence_comparison']
                intelligence_score = (
                    intel_comp.get('category_match', 0) * 0.05 +    # 5%
                    intel_comp.get('tier_match', 0) * 0.03 +        # 3%
                    intel_comp.get('volatility_match', 0) * 0.07 +  # 7%
                    intel_comp.get('popularity_match', 0) * 0.05    # 5%
                )
            
            # Score total combinado
            total_score = base_score + component_score + intelligence_score
            
            # Normalizar entre 0 y 1
            return min(max(total_score, 0.0), 1.0)
            
        except Exception as e:
            logger.debug(f"⚠️ Error calculando V5 intelligence score: {e}")
            return similarity  # Fallback al score básico
    
    def _compare_intelligence_profiles(self, analysis1: Dict[str, Any], analysis2: Dict[str, Any]) -> Dict[str, Any]:
        """Comparar perfiles de inteligencia V5 📊"""
        comparison = {}
        
        try:
            # Comparación de categoría inteligente
            cat1 = analysis1.get('intelligent_category', '')
            cat2 = analysis2.get('intelligent_category', '')
            comparison['category_match'] = 1.0 if cat1 and cat1 == cat2 else 0.0
            
            # Comparación de tier
            tier1 = analysis1.get('tier_classification', '')
            tier2 = analysis2.get('tier_classification', '')
            comparison['tier_match'] = 1.0 if tier1 and tier1 == tier2 else 0.0
            
            # Comparación de volatilidad
            vol1 = analysis1.get('volatility_score', 0)
            vol2 = analysis2.get('volatility_score', 0)
            if vol1 > 0 and vol2 > 0:
                vol_diff = abs(vol1 - vol2)
                comparison['volatility_match'] = max(0.0, 1.0 - vol_diff * 2)  # Penalizar diferencias
            else:
                comparison['volatility_match'] = 0.0
            
            # Comparación de popularidad
            pop1 = analysis1.get('popularity_score', 0)
            pop2 = analysis2.get('popularity_score', 0)
            if pop1 > 0 and pop2 > 0:
                pop_diff = abs(pop1 - pop2)
                comparison['popularity_match'] = max(0.0, 1.0 - pop_diff)
            else:
                comparison['popularity_match'] = 0.0
                
        except Exception as e:
            logger.debug(f"⚠️ Error comparando perfiles inteligencia: {e}")
        
        return comparison
    
    def _calculate_brand_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calcular similaridad de marca 🏷️"""
        try:
            brand1 = (product1.get('marca', '') or product1.get('brand', '')).lower().strip()
            brand2 = (product2.get('marca', '') or product2.get('brand', '')).lower().strip()
            
            if not brand1 or not brand2:
                return 0.0
            
            if brand1 == brand2:
                return 1.0
            
            # Similaridad básica por palabras comunes
            words1 = set(brand1.split())
            words2 = set(brand2.split())
            
            if words1 & words2:  # Hay palabras comunes
                return len(words1 & words2) / len(words1 | words2)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_model_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calcular similaridad de modelo/nombre 📱"""
        try:
            name1 = (product1.get('nombre', '') or product1.get('titulo', '')).lower()
            name2 = (product2.get('nombre', '') or product2.get('titulo', '')).lower()
            
            if not name1 or not name2:
                return 0.0
            
            # Palabras comunes
            words1 = set(name1.split())
            words2 = set(name2.split())
            
            if not words1 or not words2:
                return 0.0
            
            common_words = words1 & words2
            total_words = words1 | words2
            
            return len(common_words) / len(total_words) if total_words else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_specs_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calcular similaridad de especificaciones técnicas 🔧"""
        try:
            specs_score = 0.0
            specs_count = 0
            
            # Comparar campos de especificaciones comunes
            spec_fields = ['storage', 'ram', 'screen_size', 'camera', 'color']
            
            for field in spec_fields:
                val1 = product1.get(field)
                val2 = product2.get(field)
                
                if val1 and val2:
                    specs_count += 1
                    if str(val1).lower() == str(val2).lower():
                        specs_score += 1.0
                    elif self._specs_similar(str(val1), str(val2)):
                        specs_score += 0.7
            
            return specs_score / specs_count if specs_count > 0 else 0.5  # Default neutral
            
        except Exception:
            return 0.5
    
    def _specs_similar(self, spec1: str, spec2: str) -> bool:
        """Determinar si dos specs son similares 🔍"""
        try:
            spec1 = spec1.lower().strip()
            spec2 = spec2.lower().strip()
            
            # Extraer números para comparación
            import re
            numbers1 = re.findall(r'\d+', spec1)
            numbers2 = re.findall(r'\d+', spec2)
            
            # Si tienen números similares
            if numbers1 and numbers2:
                return any(n1 == n2 for n1 in numbers1 for n2 in numbers2)
            
            # Comparación textual básica
            return spec1 in spec2 or spec2 in spec1
            
        except Exception:
            return False
    
    def _determine_confidence(self, intelligence_score: float) -> str:
        """Determinar nivel de confianza 🎯"""
        if intelligence_score >= 0.9:
            return 'very_high'
        elif intelligence_score >= 0.8:
            return 'high'  
        elif intelligence_score >= 0.7:
            return 'medium'
        elif intelligence_score >= 0.6:
            return 'low'
        else:
            return 'very_low'
    
    def _generate_match_cache_key(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> str:
        """Generar clave de cache para match 🔑"""
        try:
            # Ordenar para consistencia
            code1 = product1.get('codigo_interno', product1.get('sku', ''))
            code2 = product2.get('codigo_interno', product2.get('sku', ''))
            
            if code1 < code2:
                return f"match:v5:{code1}:{code2}"
            else:
                return f"match:v5:{code2}:{code1}"
                
        except Exception:
            return "match:v5:unknown"
    
    async def _get_cached_match(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtener match del cache inteligente 📦"""
        try:
            if self.cache_manager:
                cached_data, level = await self.cache_manager.get(cache_key)
                if cached_data:
                    self.cache_hits[level] += 1
                    return cached_data
            return None
            
        except Exception:
            return None
    
    async def _cache_match_result(self, cache_key: str, match_data: Dict[str, Any]):
        """Guardar resultado en cache inteligente 💾"""
        try:
            if self.cache_manager:
                # Cache con TTL basado en confidence
                confidence = match_data.get('match_confidence', 'medium')
                ttl_multiplier = {'very_high': 2.0, 'high': 1.5, 'medium': 1.0, 'low': 0.5}.get(confidence, 1.0)
                
                await self.cache_manager.set(
                    cache_key, 
                    match_data,
                    ttl=int(self.config.cache_l2_ttl * ttl_multiplier),
                    tags=['match', 'ml', 'v5']
                )
                
        except Exception as e:
            logger.debug(f"⚠️ Error guardando en cache: {e}")
    
    async def detect_arbitrage_opportunities(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detectar oportunidades de arbitraje usando inteligencia V5 💰
        
        Args:
            matches: Lista de matches detectados
            
        Returns:
            Lista de oportunidades con scoring V5 avanzado
        """
        opportunities = []
        
        try:
            logger.info(f"💰 Analizando {len(matches)} matches para oportunidades...")
            
            for match in matches:
                try:
                    # Obtener productos del match
                    product1 = match.get('product1', {})
                    product2 = match.get('product2', {})
                    
                    if not product1 or not product2:
                        continue
                    
                    # Extraer precios
                    price1 = self._extract_best_price(product1)
                    price2 = self._extract_best_price(product2)
                    
                    if not price1 or not price2 or price1 <= 0 or price2 <= 0:
                        continue
                    
                    # Determinar cuál es más barato
                    if price1 < price2:
                        cheap_product, expensive_product = product1, product2
                        cheap_price, expensive_price = price1, price2
                    else:
                        cheap_product, expensive_product = product2, product1
                        cheap_price, expensive_price = price2, price1
                    
                    # Calcular métricas básicas
                    margin = expensive_price - cheap_price
                    percentage = (margin / cheap_price) * 100
                    roi = percentage
                    
                    # Verificar umbrales mínimos
                    if (margin < self.config.min_margin_clp or 
                        percentage < self.config.min_percentage):
                        continue
                    
                    # Crear oportunidad con análisis V5
                    opportunity = await self._create_v5_opportunity(
                        cheap_product, expensive_product,
                        cheap_price, expensive_price,
                        margin, percentage, roi, match
                    )
                    
                    if opportunity:
                        opportunities.append(opportunity)
                        self.opportunities_detected += 1
                        
                except Exception as e:
                    logger.debug(f"⚠️ Error procesando match: {e}")
                    continue
            
            logger.info(f"🎯 Detectadas {len(opportunities)} oportunidades de arbitraje V5")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error detectando oportunidades: {e}")
            return opportunities
    
    async def _create_v5_opportunity(self, cheap_product: Dict[str, Any], expensive_product: Dict[str, Any],
                                   cheap_price: float, expensive_price: float, margin: float, 
                                   percentage: float, roi: float, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crear oportunidad enriquecida con análisis V5 🚀"""
        try:
            # Códigos de productos
            cheap_code = cheap_product.get('codigo_interno', cheap_product.get('sku', ''))
            expensive_code = expensive_product.get('codigo_interno', expensive_product.get('sku', ''))
            
            # Análisis V5 avanzado si disponible
            v5_analysis = {}
            volatility_risk = 0.0
            timing_score = 0.5
            predicted_duration = 24
            predicted_success_rate = 0.7
            
            if self.master_integrator:
                # Análisis completo V5
                cheap_analysis = await self.master_integrator.analyze_scraping_request(
                    cheap_product.get('retailer', ''),
                    cheap_code
                )
                
                expensive_analysis = await self.master_integrator.analyze_scraping_request(
                    expensive_product.get('retailer', ''),
                    expensive_code
                )
                
                v5_analysis = {
                    'cheap_product_analysis': cheap_analysis,
                    'expensive_product_analysis': expensive_analysis
                }
                
                # Extraer métricas inteligentes
                volatility_risk = max(
                    cheap_analysis.get('volatility_score', 0),
                    expensive_analysis.get('volatility_score', 0)
                )
                
                # Score de timing basado en patrones V5
                timing_score = self._calculate_timing_score(cheap_analysis, expensive_analysis)
                
                # Predicciones basadas en inteligencia V5
                predicted_duration = self._predict_opportunity_duration(v5_analysis)
                predicted_success_rate = self._predict_success_rate(v5_analysis, volatility_risk)
            
            # Calcular scores V5
            opportunity_score = self._calculate_opportunity_score(
                margin, percentage, match.get('v5_intelligence_score', 0.5), 
                volatility_risk, timing_score
            )
            
            v5_intelligence_score = self._calculate_opportunity_intelligence_score(
                v5_analysis, match, volatility_risk
            )
            
            confidence_score = self._calculate_confidence_score(
                match.get('v5_intelligence_score', 0.5), volatility_risk, timing_score
            )
            
            # Clasificación inteligente
            risk_level = self._classify_risk_level(volatility_risk, confidence_score)
            priority_level = self._calculate_priority_level(opportunity_score, v5_intelligence_score)
            tier_classification = self._determine_tier_classification(v5_analysis)
            
            # Momento óptimo de ejecución
            optimal_execution_time = await self._calculate_optimal_execution_time(v5_analysis)
            
            # Alerta con emojis
            emoji_alert = self._generate_emoji_alert(margin, percentage, confidence_score)
            
            opportunity = {
                'producto_barato_codigo': cheap_code,
                'producto_caro_codigo': expensive_code,
                'matching_id': match.get('match_id'),
                'retailer_compra': cheap_product.get('retailer', ''),
                'retailer_venta': expensive_product.get('retailer', ''),
                'precio_compra': int(cheap_price),
                'precio_venta': int(expensive_price),
                'diferencia_absoluta': int(margin),
                'diferencia_porcentaje': round(percentage, 2),
                'margen_bruto': int(margin),
                'roi_estimado': round(roi, 2),
                'opportunity_score': opportunity_score,
                'v5_intelligence_score': v5_intelligence_score,
                'volatility_risk_score': volatility_risk,
                'timing_score': timing_score,
                'confidence_score': confidence_score,
                'risk_level': risk_level,
                'priority_level': priority_level,
                'tier_classification': tier_classification,
                'predicted_duration_hours': predicted_duration,
                'predicted_success_rate': predicted_success_rate,
                'optimal_execution_time': optimal_execution_time,
                'detection_method': 'v5_ml_intelligence',
                'emoji_alert': emoji_alert,
                'v5_analysis': v5_analysis,
                'redis_cache_data': {},  # Se llenará por cache manager
                'learned_insights': {},  # Se llenará por sistema de aprendizaje
                'metadata': {
                    'ml_model_version': 'v5.0.0',
                    'detection_timestamp': datetime.now().isoformat(),
                    'match_similarity': match.get('similarity_score', 0),
                    'v5_components_used': {
                        'redis_intelligence': self.redis_intelligence is not None,
                        'cache_manager': self.cache_manager is not None,
                        'master_integrator': self.master_integrator is not None
                    }
                },
                # Referencias para procesamiento
                'cheap_product': cheap_product,
                'expensive_product': expensive_product
            }
            
            return opportunity
            
        except Exception as e:
            logger.error(f"❌ Error creando oportunidad V5: {e}")
            return None
    
    def _extract_best_price(self, product: Dict[str, Any]) -> float:
        """Extraer el mejor precio de un producto 💰"""
        try:
            price_fields = [
                'precio_min_num', 'precio_oferta_num', 'precio_tarjeta_num',
                'precio_normal_num', 'precio', 'normal_num', 'oferta_num'
            ]
            
            valid_prices = []
            for field in price_fields:
                price = product.get(field, 0)
                if isinstance(price, (int, float)) and price > 0:
                    valid_prices.append(float(price))
            
            return min(valid_prices) if valid_prices else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_opportunity_score(self, margin: float, percentage: float, 
                                   similarity_score: float, volatility_risk: float, timing_score: float) -> float:
        """Calcular score de oportunidad con pesos configurables 📊"""
        try:
            weights = self.config.scoring_weights
            
            # Normalizar métricas
            margin_norm = min(margin / 100000, 1.0)  # Normalizar a 100k max
            percentage_norm = min(percentage / 50, 1.0)  # Normalizar a 50% max
            volatility_factor = max(0, 1.0 - volatility_risk)  # Invertir volatilidad
            
            score = (
                margin_norm * weights['profit_margin'] +
                percentage_norm * weights['profit_margin'] * 0.5 +  # Complementar margen
                similarity_score * weights['similarity_score'] +
                volatility_factor * weights['volatility_score'] +
                timing_score * weights['timing_score']
            )
            
            return min(max(score, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    def _calculate_opportunity_intelligence_score(self, v5_analysis: Dict[str, Any], 
                                                 match: Dict[str, Any], volatility_risk: float) -> float:
        """Calcular score de inteligencia V5 para oportunidad 🧠"""
        try:
            base_score = match.get('v5_intelligence_score', 0.5)
            
            # Factores de ajuste basados en análisis V5
            adjustment = 0.0
            
            if v5_analysis:
                cheap_analysis = v5_analysis.get('cheap_product_analysis', {})
                expensive_analysis = v5_analysis.get('expensive_product_analysis', {})
                
                # Bonus por tier alto en ambos productos
                cheap_tier = cheap_analysis.get('tier_classification', '')
                expensive_tier = expensive_analysis.get('tier_classification', '')
                
                if cheap_tier == 'critical' or expensive_tier == 'critical':
                    adjustment += 0.1
                elif cheap_tier == 'important' or expensive_tier == 'important':
                    adjustment += 0.05
                
                # Bonus por baja volatilidad (menor riesgo)
                if volatility_risk < 0.3:
                    adjustment += 0.05
                elif volatility_risk < 0.5:
                    adjustment += 0.02
                
                # Penalty por alta volatilidad (mayor riesgo)
                if volatility_risk > 0.7:
                    adjustment -= 0.1
            
            final_score = base_score + adjustment
            return min(max(final_score, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    def _calculate_timing_score(self, cheap_analysis: Dict[str, Any], expensive_analysis: Dict[str, Any]) -> float:
        """Calcular score de timing basado en patrones V5 ⏰"""
        try:
            # Por ahora, score básico - se puede mejorar con más datos históricos
            timing_score = 0.5
            
            # Si hay análisis de frecuencia óptima
            if self.frequency_optimizer:
                cheap_freq = cheap_analysis.get('optimal_frequency_hours', 24)
                expensive_freq = expensive_analysis.get('optimal_frequency_hours', 24)
                
                # Mejor timing si ambos productos tienen frecuencia similar (estables)
                freq_diff = abs(cheap_freq - expensive_freq)
                if freq_diff < 2:  # Muy similar
                    timing_score += 0.3
                elif freq_diff < 6:  # Moderadamente similar
                    timing_score += 0.1
            
            # Timing basado en hora actual (lógica básica)
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 21:  # Horario comercial
                timing_score += 0.2
            
            return min(timing_score, 1.0)
            
        except Exception:
            return 0.5
    
    def _predict_opportunity_duration(self, v5_analysis: Dict[str, Any]) -> int:
        """Predecir duración de oportunidad en horas 🔮"""
        try:
            # Duración base
            base_duration = 24
            
            if v5_analysis:
                cheap_analysis = v5_analysis.get('cheap_product_analysis', {})
                expensive_analysis = v5_analysis.get('expensive_product_analysis', {})
                
                # Duración basada en volatilidad promedio
                cheap_vol = cheap_analysis.get('volatility_score', 0.5)
                expensive_vol = expensive_analysis.get('volatility_score', 0.5)
                avg_volatility = (cheap_vol + expensive_vol) / 2
                
                # Alta volatilidad = menor duración
                if avg_volatility > 0.7:
                    base_duration = 6
                elif avg_volatility > 0.5:
                    base_duration = 12
                elif avg_volatility < 0.3:
                    base_duration = 48
            
            return base_duration
            
        except Exception:
            return 24
    
    def _predict_success_rate(self, v5_analysis: Dict[str, Any], volatility_risk: float) -> float:
        """Predecir tasa de éxito de oportunidad 📈"""
        try:
            base_success_rate = 0.7
            
            # Ajustar por volatilidad
            if volatility_risk < 0.3:
                base_success_rate = 0.9
            elif volatility_risk < 0.5:
                base_success_rate = 0.8
            elif volatility_risk > 0.7:
                base_success_rate = 0.5
            
            # Ajustar por análisis V5
            if v5_analysis:
                cheap_analysis = v5_analysis.get('cheap_product_analysis', {})
                expensive_analysis = v5_analysis.get('expensive_product_analysis', {})
                
                # Bonus por productos en tier critical/important
                cheap_tier = cheap_analysis.get('tier_classification', '')
                expensive_tier = expensive_analysis.get('tier_classification', '')
                
                if cheap_tier in ['critical', 'important'] and expensive_tier in ['critical', 'important']:
                    base_success_rate += 0.1
            
            return min(max(base_success_rate, 0.1), 1.0)
            
        except Exception:
            return 0.7
    
    def _calculate_confidence_score(self, match_intelligence: float, volatility_risk: float, timing_score: float) -> float:
        """Calcular score de confianza general 🎯"""
        try:
            # Combinar factores
            confidence = (
                match_intelligence * 0.5 +           # 50% del match ML
                (1.0 - volatility_risk) * 0.3 +      # 30% estabilidad 
                timing_score * 0.2                   # 20% timing
            )
            
            return min(max(confidence, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    def _classify_risk_level(self, volatility_risk: float, confidence_score: float) -> str:
        """Clasificar nivel de riesgo 🚨"""
        try:
            # Combinar volatilidad y confianza
            risk_factor = (volatility_risk * 0.7) + ((1.0 - confidence_score) * 0.3)
            
            if risk_factor < 0.3:
                return 'low'
            elif risk_factor < 0.5:
                return 'medium'
            elif risk_factor < 0.7:
                return 'high'
            else:
                return 'very_high'
                
        except Exception:
            return 'medium'
    
    def _calculate_priority_level(self, opportunity_score: float, intelligence_score: float) -> int:
        """Calcular nivel de prioridad (1-5) 🏆"""
        try:
            combined_score = (opportunity_score + intelligence_score) / 2
            
            if combined_score >= 0.9:
                return 1  # Máxima prioridad
            elif combined_score >= 0.8:
                return 2  # Alta prioridad
            elif combined_score >= 0.6:
                return 3  # Prioridad media
            elif combined_score >= 0.4:
                return 4  # Baja prioridad
            else:
                return 5  # Muy baja prioridad
                
        except Exception:
            return 3
    
    def _determine_tier_classification(self, v5_analysis: Dict[str, Any]) -> str:
        """Determinar clasificación de tier 📊"""
        try:
            if not v5_analysis:
                return 'tracking'
            
            cheap_analysis = v5_analysis.get('cheap_product_analysis', {})
            expensive_analysis = v5_analysis.get('expensive_product_analysis', {})
            
            # Tomar el tier más alto de ambos productos
            cheap_tier = cheap_analysis.get('tier_classification', 'tracking')
            expensive_tier = expensive_analysis.get('tier_classification', 'tracking')
            
            tier_priority = {'critical': 3, 'important': 2, 'tracking': 1}
            
            cheap_priority = tier_priority.get(cheap_tier, 1)
            expensive_priority = tier_priority.get(expensive_tier, 1)
            
            max_priority = max(cheap_priority, expensive_priority)
            
            for tier, priority in tier_priority.items():
                if priority == max_priority:
                    return tier
            
            return 'tracking'
            
        except Exception:
            return 'tracking'
    
    async def _calculate_optimal_execution_time(self, v5_analysis: Dict[str, Any]) -> Optional[datetime]:
        """Calcular momento óptimo de ejecución ⏰"""
        try:
            # Por ahora, dentro de las próximas 2 horas en horario comercial
            from datetime import timedelta
            
            now = datetime.now()
            
            # Si estamos en horario comercial, ejecutar pronto
            if 9 <= now.hour <= 21:
                return now + timedelta(minutes=30)
            else:
                # Esperar al siguiente horario comercial
                next_day = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if now.hour >= 22:
                    next_day += timedelta(days=1)
                return next_day
                
        except Exception:
            return None
    
    def _generate_emoji_alert(self, margin: float, percentage: float, confidence: float) -> str:
        """Generar alerta con emojis 🎭"""
        try:
            if not self.config.enable_emoji_alerts:
                return f"Arbitraje detectado: ${margin:,.0f} CLP ({percentage:.1f}%)"
            
            # Seleccionar emoji principal
            if margin >= 50000:
                main_emoji = "🔥💰"
            elif margin >= 25000:
                main_emoji = "💰✨"
            elif percentage >= 25:
                main_emoji = "📈💎"
            else:
                main_emoji = "💰📊"
            
            # Emoji de confianza
            if confidence >= 0.9:
                conf_emoji = "⭐⭐⭐"
            elif confidence >= 0.7:
                conf_emoji = "⭐⭐"
            else:
                conf_emoji = "⭐"
            
            return f"{main_emoji} OPORTUNIDAD DETECTADA {conf_emoji}\n💵 Margen: ${margin:,.0f} CLP ({percentage:.1f}% ROI)"
            
        except Exception:
            return f"💰 Oportunidad: ${margin:,.0f} CLP ({percentage:.1f}%)"
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas ML V5 📈"""
        return {
            'matches_processed': self.matches_processed,
            'opportunities_detected': self.opportunities_detected,
            'ml_predictions': self.ml_predictions,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': {
                level: hits / max(self.ml_predictions, 1) 
                for level, hits in self.cache_hits.items()
            },
            'v5_components_active': {
                'redis_intelligence': self.redis_intelligence is not None,
                'cache_manager': self.cache_manager is not None, 
                'master_integrator': self.master_integrator is not None,
                'frequency_optimizer': self.frequency_optimizer is not None
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def close(self):
        """Cerrar conexiones y liberar recursos 🔚"""
        try:
            # Cerrar componentes V5
            if self.redis_intelligence:
                await self.redis_intelligence.close()
            
            if self.cache_manager:
                await self.cache_manager.close()
            
            if self.master_integrator:
                await self.master_integrator.close()
            
            if self.frequency_optimizer:
                await self.frequency_optimizer.close()
            
            # Cerrar database manager
            await self.db_manager.close()
            
            logger.info("🔚 MLIntegration V5 cerrado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error cerrando MLIntegration V5: {e}")

# Función de utilidad para crear instancia
async def create_ml_integration_v5(config: Optional[ArbitrageConfigV5] = None) -> MLIntegrationV5:
    """Crear e inicializar MLIntegration V5 🚀"""
    ml_integration = MLIntegrationV5(config)
    await ml_integration.initialize()
    return ml_integration