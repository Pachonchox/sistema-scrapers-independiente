# -*- coding: utf-8 -*-
"""
ML Adapters - Sistema V5 Autónomo 🧠
===================================
Adaptadores para integrar componentes ML externos manteniendo autonomía V5.
Compatible con emojis y optimizado para operación continua.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MatchScoringAdapter:
    """
    Adapter para MatchScoringModel que funciona con el sistema V5 avanzado 🎯
    
    Proporciona la interfaz que necesitan los componentes externos
    pero usando la inteligencia interna de V5.
    """
    
    def __init__(self, threshold: float = 0.85, embedder_name: str = None):
        """Inicializar adapter con parámetros compatibles"""
        self.threshold = threshold
        self.embedder_name = embedder_name or "paraphrase-multilingual-mpnet-base-v2"
        
        # Usar sistema de inteligencia V5
        try:
            from ..portable_orchestrator_v5.core.redis_intelligence_system import RedisIntelligenceSystem
            from ..portable_orchestrator_v5.core.master_intelligence_integrator import MasterIntelligenceIntegrator
            
            self.redis_intelligence = RedisIntelligenceSystem()
            self.master_integrator = MasterIntelligenceIntegrator()
            self.v5_available = True
            logger.info("🧠 Adapter conectado al sistema ML V5 avanzado")
            
        except ImportError as e:
            logger.warning(f"⚠️ Sistema V5 no disponible, usando modo compatible: {e}")
            self.v5_available = False
            self._init_fallback_system()
    
    def _init_fallback_system(self):
        """Sistema de fallback básico si V5 no está disponible"""
        self.product_cache = {}
        self.similarity_cache = {}
    
    def calculate_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """
        Calcular similaridad entre productos usando inteligencia V5 🔍
        
        Args:
            product1, product2: Productos a comparar
            
        Returns:
            Score de similaridad (0-1)
        """
        if self.v5_available:
            return self._v5_similarity_calculation(product1, product2)
        else:
            return self._fallback_similarity_calculation(product1, product2)
    
    def _v5_similarity_calculation(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Cálculo usando sistema V5 avanzado"""
        try:
            # Crear claves únicas para productos
            key1 = self._create_product_key(product1)
            key2 = self._create_product_key(product2)
            
            if key1 == key2:
                return 1.0
            
            # Usar inteligencia V5 para análisis
            analysis1 = self.master_integrator.analyze_product_profile(product1)
            analysis2 = self.master_integrator.analyze_product_profile(product2)
            
            # Comparar perfiles inteligentes
            similarity = self._compare_intelligence_profiles(analysis1, analysis2)
            
            return min(max(similarity, 0.0), 1.0)  # Clamp 0-1
            
        except Exception as e:
            logger.warning(f"⚠️ Error en cálculo V5, usando fallback: {e}")
            return self._fallback_similarity_calculation(product1, product2)
    
    def _compare_intelligence_profiles(self, profile1: Dict[str, Any], profile2: Dict[str, Any]) -> float:
        """Comparar perfiles de inteligencia V5"""
        similarity_score = 0.0
        
        # Comparar marca normalizada (peso: 30%)
        if profile1.get('brand_normalized') and profile2.get('brand_normalized'):
            if profile1['brand_normalized'].lower() == profile2['brand_normalized'].lower():
                similarity_score += 0.3
        
        # Comparar modelo/nombre (peso: 40%)
        name1 = (profile1.get('model_extracted') or '').lower()
        name2 = (profile2.get('model_extracted') or '').lower()
        if name1 and name2:
            # Similaridad básica de texto
            common_words = set(name1.split()) & set(name2.split())
            total_words = set(name1.split()) | set(name2.split())
            if total_words:
                similarity_score += 0.4 * (len(common_words) / len(total_words))
        
        # Comparar categoría (peso: 20%)
        if profile1.get('category') and profile2.get('category'):
            if profile1['category'].lower() == profile2['category'].lower():
                similarity_score += 0.2
        
        # Comparar specs técnicas (peso: 10%)
        specs1 = profile1.get('technical_specs', {})
        specs2 = profile2.get('technical_specs', {})
        if specs1 and specs2:
            matching_specs = sum(1 for k, v in specs1.items() 
                                if k in specs2 and v == specs2[k])
            total_specs = len(set(specs1.keys()) | set(specs2.keys()))
            if total_specs > 0:
                similarity_score += 0.1 * (matching_specs / total_specs)
        
        return similarity_score
    
    def _fallback_similarity_calculation(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Cálculo de fallback básico"""
        # Comparación básica por nombre y marca
        name1 = (product1.get('nombre', '') or product1.get('titulo', '')).lower()
        name2 = (product2.get('nombre', '') or product2.get('titulo', '')).lower()
        
        brand1 = (product1.get('marca', '') or product1.get('brand', '')).lower()
        brand2 = (product2.get('marca', '') or product2.get('brand', '')).lower()
        
        similarity = 0.0
        
        # Comparar marcas (50%)
        if brand1 and brand2 and brand1 == brand2:
            similarity += 0.5
        
        # Comparar nombres básico (50%)
        if name1 and name2:
            common_words = set(name1.split()) & set(name2.split())
            total_words = set(name1.split()) | set(name2.split())
            if total_words:
                similarity += 0.5 * (len(common_words) / len(total_words))
        
        return similarity
    
    def _create_product_key(self, product: Dict[str, Any]) -> str:
        """Crear clave única para producto"""
        retailer = product.get('retailer', 'unknown')
        sku = product.get('sku', '')
        name = product.get('nombre', '') or product.get('titulo', '')
        
        return f"{retailer}:{sku}:{hash(name)}"
    
    def find_similar_products(self, target_product: Dict[str, Any], 
                            candidate_products: List[Dict[str, Any]],
                            min_similarity: float = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Encontrar productos similares con scores 🔍
        
        Args:
            target_product: Producto objetivo
            candidate_products: Lista de candidatos
            min_similarity: Similaridad mínima (usa threshold si None)
            
        Returns:
            Lista de (producto, score) ordenada por score
        """
        min_sim = min_similarity or self.threshold
        results = []
        
        for candidate in candidate_products:
            # Evitar comparar con el mismo producto
            if (candidate.get('sku') == target_product.get('sku') and 
                candidate.get('retailer') == target_product.get('retailer')):
                continue
            
            similarity = self.calculate_similarity(target_product, candidate)
            
            if similarity >= min_sim:
                results.append((candidate, similarity))
        
        # Ordenar por similarity descendente
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def batch_scoring(self, product_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[float]:
        """
        Procesamiento en lote de scores de similaridad 📊
        
        Args:
            product_pairs: Lista de pares (producto1, producto2)
            
        Returns:
            Lista de scores correspondientes
        """
        scores = []
        
        for product1, product2 in product_pairs:
            score = self.calculate_similarity(product1, product2)
            scores.append(score)
        
        if self.v5_available:
            logger.info(f"🔄 Procesados {len(scores)} pares con sistema V5 avanzado")
        
        return scores

class GlitchDetectionAdapter:
    """
    Adapter para GlitchDetectionSystem usando inteligencia V5 🚨
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        try:
            from ..portable_orchestrator_v5.core.intelligent_cache_manager import IntelligentCacheManager
            from ..portable_orchestrator_v5.core.redis_intelligence_system import RedisIntelligenceSystem
            
            self.cache_manager = IntelligentCacheManager()
            self.redis_intelligence = RedisIntelligenceSystem()
            self.v5_available = True
            logger.info("🚨 GlitchDetection conectado al sistema V5 avanzado")
            
        except ImportError as e:
            logger.warning(f"⚠️ Sistema V5 no disponible para glitch detection: {e}")
            self.v5_available = False
    
    def detect_glitch(self, current_price: float, historical_prices: List[float], 
                     product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detectar anomalías usando inteligencia V5 🔍
        """
        if self.v5_available:
            return self._v5_glitch_detection(current_price, historical_prices, product_data)
        else:
            return self._fallback_glitch_detection(current_price, historical_prices, product_data)
    
    def _v5_glitch_detection(self, current_price: float, historical_prices: List[float], 
                           product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detección usando sistema V5 avanzado"""
        try:
            # Analizar con inteligencia V5
            product_id = product_data.get('sku', 'unknown')
            retailer = product_data.get('retailer', 'unknown')
            
            # Usar análisis de volatilidad V5
            volatility_analysis = self.redis_intelligence.analyze_price_volatility(
                retailer, product_id, historical_prices
            )
            
            # Determinar si es glitch basado en análisis V5
            is_glitch = volatility_analysis.get('is_anomaly', False)
            confidence = volatility_analysis.get('confidence', 0.0)
            
            return {
                'is_glitch': is_glitch,
                'glitch_score': volatility_analysis.get('anomaly_score', 0.0),
                'confidence': confidence,
                'reasons': volatility_analysis.get('reasons', []),
                'recommendation': 'reject' if is_glitch and confidence > 0.8 else 'accept',
                'v5_analysis': True
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error en análisis V5, usando fallback: {e}")
            return self._fallback_glitch_detection(current_price, historical_prices, product_data)
    
    def _fallback_glitch_detection(self, current_price: float, historical_prices: List[float], 
                                 product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sistema de fallback básico"""
        if not historical_prices or current_price <= 0:
            return {
                'is_glitch': True,
                'glitch_score': 1.0,
                'confidence': 1.0,
                'reasons': ['precio_invalido'],
                'recommendation': 'reject',
                'v5_analysis': False
            }
        
        # Análisis básico
        import statistics
        avg_price = statistics.mean(historical_prices)
        change_pct = abs(current_price - avg_price) / avg_price * 100 if avg_price > 0 else 0
        
        is_glitch = change_pct > 90  # Cambio mayor al 90%
        
        return {
            'is_glitch': is_glitch,
            'glitch_score': min(change_pct / 100, 1.0),
            'confidence': 0.8 if is_glitch else 0.9,
            'reasons': [f'cambio_extremo_{change_pct:.1f}pct'] if is_glitch else [],
            'recommendation': 'reject' if is_glitch else 'accept',
            'v5_analysis': False
        }

class NormalizationHubAdapter:
    """
    Adapter para NormalizationHub usando sistema V5 completo 🌟
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        try:
            from ..portable_orchestrator_v5.core.master_intelligence_integrator import MasterIntelligenceIntegrator
            from ..portable_orchestrator_v5.core.intelligent_cache_manager import IntelligentCacheManager
            
            self.master_integrator = MasterIntelligenceIntegrator()
            self.cache_manager = IntelligentCacheManager()
            self.v5_available = True
            logger.info("🌟 NormalizationHub conectado al sistema V5 completo")
            
        except ImportError as e:
            logger.warning(f"⚠️ Sistema V5 no disponible para normalización: {e}")
            self.v5_available = False
    
    async def process_batch(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Procesar lote usando inteligencia V5 completa 📊
        """
        if self.v5_available:
            return await self._v5_batch_processing(products)
        else:
            return await self._fallback_batch_processing(products)
    
    async def _v5_batch_processing(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesamiento usando sistema V5 completo"""
        try:
            results = {
                'skus_generated': 0,
                'matches_found': 0,
                'opportunities': [],
                'alerts': [],
                'v5_processing': True
            }
            
            for product in products:
                # Usar análisis completo V5
                analysis = await self.master_integrator.analyze_scraping_request(
                    product.get('retailer', ''),
                    product.get('sku', ''),
                    product.get('categoria', '')
                )
                
                if analysis.get('normalized_data'):
                    results['skus_generated'] += 1
                
                if analysis.get('similar_products'):
                    results['matches_found'] += len(analysis['similar_products'])
                
                # Detectar oportunidades usando V5
                if analysis.get('price_opportunities'):
                    results['opportunities'].extend(analysis['price_opportunities'])
                
                if analysis.get('alerts'):
                    results['alerts'].extend(analysis['alerts'])
            
            logger.info(f"🌟 Procesamiento V5 completo: {len(products)} productos")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento V5: {e}")
            return await self._fallback_batch_processing(products)
    
    async def _fallback_batch_processing(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesamiento básico de fallback"""
        return {
            'skus_generated': len(products),
            'matches_found': 0,
            'opportunities': [],
            'alerts': [],
            'v5_processing': False
        }
    
    async def close(self):
        """Cerrar conexiones"""
        if self.v5_available:
            try:
                await self.master_integrator.close()
                await self.cache_manager.close()
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexiones V5: {e}")
        logger.info("🔚 NormalizationHub adapter cerrado")