# -*- coding: utf-8 -*-
"""
🎯 OpportunityDetector V5 - Detector de Oportunidades Autónomo
=============================================================
Detector especializado de oportunidades de arbitraje con inteligencia V5.
Completamente autocontenido y optimizado para operación continua.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from ..config.arbitrage_config import ArbitrageConfigV5
from ..database.db_manager import DatabaseManagerV5
from .ml_integration import MLIntegrationV5

logger = logging.getLogger(__name__)

class OpportunityDetectorV5:
    """
    Detector de oportunidades V5 con análisis inteligente 🎯
    
    Funcionalidades:
    - 🔍 Detección avanzada de oportunidades
    - 📊 Análisis de rentabilidad multi-factor
    - ⏰ Timing óptimo de ejecución
    - 🎲 Evaluación de riesgos
    - 📈 Scoring predictivo
    """
    
    def __init__(self, config: ArbitrageConfigV5, db_manager: DatabaseManagerV5, 
                 ml_integration: MLIntegrationV5, cache_manager=None):
        """Inicializar detector de oportunidades"""
        self.config = config
        self.db_manager = db_manager
        self.ml_integration = ml_integration
        self.cache_manager = cache_manager
        
        # Métricas del detector
        self.metrics = {
            'opportunities_analyzed': 0,
            'opportunities_validated': 0,
            'opportunities_rejected': 0,
            'avg_opportunity_score': 0.0,
            'high_confidence_count': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("🎯 OpportunityDetector V5 inicializado")
    
    async def initialize(self):
        """Inicializar detector 🔧"""
        try:
            logger.info("🔧 Inicializando OpportunityDetector V5...")
            # Inicialización básica completada
            logger.info("✅ OpportunityDetector V5 listo")
        except Exception as e:
            logger.error(f"❌ Error inicializando detector: {e}")
            raise
    
    async def detect_opportunities(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detectar oportunidades de arbitraje 💰
        
        Args:
            matches: Lista de matches de productos
            
        Returns:
            Lista de oportunidades detectadas y validadas
        """
        try:
            logger.info(f"🔍 Analizando {len(matches)} matches para oportunidades...")
            
            opportunities = []
            
            for match in matches:
                try:
                    # Analizar match individual
                    opportunity = await self._analyze_match_for_opportunity(match)
                    
                    if opportunity:
                        # Validar oportunidad
                        if await self._validate_opportunity(opportunity):
                            opportunities.append(opportunity)
                            self.metrics['opportunities_validated'] += 1
                        else:
                            self.metrics['opportunities_rejected'] += 1
                    
                    self.metrics['opportunities_analyzed'] += 1
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error analizando match: {e}")
                    continue
            
            # Actualizar métricas
            if opportunities:
                avg_score = sum(o.get('opportunity_score', 0) for o in opportunities) / len(opportunities)
                self.metrics['avg_opportunity_score'] = avg_score
                
                high_conf_count = sum(1 for o in opportunities if o.get('confidence_score', 0) > 0.8)
                self.metrics['high_confidence_count'] = high_conf_count
            
            self.metrics['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"💎 Detectadas {len(opportunities)} oportunidades válidas")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error detectando oportunidades: {e}")
            return []
    
    async def _analyze_match_for_opportunity(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analizar match individual para oportunidad 🔍"""
        try:
            # Obtener productos del match
            product1 = match.get('product1', {})
            product2 = match.get('product2', {})
            
            if not product1 or not product2:
                return None
            
            # Extraer precios
            price1 = self._extract_best_price(product1)
            price2 = self._extract_best_price(product2)
            
            if not price1 or not price2 or price1 <= 0 or price2 <= 0:
                return None
            
            # Determinar productos barato y caro
            if price1 < price2:
                cheap_product, expensive_product = product1, product2
                cheap_price, expensive_price = price1, price2
            else:
                cheap_product, expensive_product = product2, product1
                cheap_price, expensive_price = price2, price1
            
            # Calcular métricas básicas
            margin = expensive_price - cheap_price
            percentage = (margin / cheap_price) * 100
            
            # Verificar umbrales mínimos
            if (margin < self.config.min_margin_clp or 
                percentage < self.config.min_percentage):
                return None
            
            # Crear oportunidad básica
            opportunity = {
                'cheap_product': cheap_product,
                'expensive_product': expensive_product,
                'cheap_price': cheap_price,
                'expensive_price': expensive_price,
                'margin': margin,
                'percentage': percentage,
                'roi': percentage,
                'match_data': match,
                'detection_timestamp': datetime.now().isoformat()
            }
            
            # Enriquecer con análisis avanzado
            await self._enrich_opportunity_analysis(opportunity)
            
            return opportunity
            
        except Exception as e:
            logger.debug(f"⚠️ Error analizando match: {e}")
            return None
    
    async def _enrich_opportunity_analysis(self, opportunity: Dict[str, Any]):
        """Enriquecer análisis de oportunidad 📊"""
        try:
            # Análisis de scoring
            opportunity_score = self._calculate_opportunity_score(opportunity)
            opportunity['opportunity_score'] = opportunity_score
            
            # Análisis de confianza
            confidence_score = self._calculate_confidence_score(opportunity)
            opportunity['confidence_score'] = confidence_score
            
            # Análisis de riesgo
            risk_analysis = await self._analyze_risk(opportunity)
            opportunity['risk_analysis'] = risk_analysis
            opportunity['risk_level'] = risk_analysis.get('level', 'medium')
            
            # Análisis de timing
            timing_analysis = self._analyze_timing(opportunity)
            opportunity['timing_analysis'] = timing_analysis
            opportunity['timing_score'] = timing_analysis.get('score', 0.5)
            
            # Predicciones
            predictions = await self._make_predictions(opportunity)
            opportunity['predictions'] = predictions
            
            # Clasificación final
            opportunity['priority_level'] = self._determine_priority(opportunity)
            opportunity['tier_classification'] = self._determine_tier(opportunity)
            
        except Exception as e:
            logger.debug(f"⚠️ Error enriqueciendo análisis: {e}")
    
    def _calculate_opportunity_score(self, opportunity: Dict[str, Any]) -> float:
        """Calcular score de oportunidad 📈"""
        try:
            margin = opportunity['margin']
            percentage = opportunity['percentage']
            match_score = opportunity.get('match_data', {}).get('similarity_score', 0.5)
            
            # Normalizar métricas
            margin_norm = min(margin / 100000, 1.0)  # Max 100k
            percentage_norm = min(percentage / 50, 1.0)  # Max 50%
            
            # Score combinado usando pesos configurables
            weights = self.config.scoring_weights
            
            score = (
                margin_norm * weights['profit_margin'] +
                percentage_norm * weights['profit_margin'] * 0.5 +  # Complementar
                match_score * weights['similarity_score']
            )
            
            return min(max(score, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    def _calculate_confidence_score(self, opportunity: Dict[str, Any]) -> float:
        """Calcular score de confianza 🎯"""
        try:
            # Factores de confianza
            match_similarity = opportunity.get('match_data', {}).get('similarity_score', 0.5)
            margin_size = opportunity['margin']
            percentage_size = opportunity['percentage']
            
            # Confianza basada en similaridad del match
            conf_similarity = match_similarity
            
            # Confianza basada en tamaño de oportunidad (más grande = más confiable)
            conf_margin = min(margin_size / 50000, 1.0)  # Max 50k para confidence = 1.0
            conf_percentage = min(percentage_size / 30, 1.0)  # Max 30% para confidence = 1.0
            
            # Combinar factores
            confidence = (
                conf_similarity * 0.4 +
                conf_margin * 0.3 +
                conf_percentage * 0.3
            )
            
            return min(max(confidence, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    async def _analyze_risk(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar riesgos de la oportunidad 🎲"""
        try:
            risk_factors = []
            risk_score = 0.0
            
            # Riesgo por margen muy alto (puede ser error)
            margin = opportunity['margin']
            if margin > 200000:  # 200k+
                risk_factors.append('margen_extremo')
                risk_score += 0.3
            elif margin > 100000:  # 100k+
                risk_factors.append('margen_muy_alto')
                risk_score += 0.1
            
            # Riesgo por porcentaje muy alto
            percentage = opportunity['percentage']
            if percentage > 100:  # 100%+
                risk_factors.append('porcentaje_extremo')
                risk_score += 0.4
            elif percentage > 50:  # 50%+
                risk_factors.append('porcentaje_alto')
                risk_score += 0.2
            
            # Riesgo por baja similaridad
            similarity = opportunity.get('match_data', {}).get('similarity_score', 1.0)
            if similarity < 0.7:
                risk_factors.append('baja_similaridad')
                risk_score += 0.3
            elif similarity < 0.8:
                risk_factors.append('similaridad_moderada')
                risk_score += 0.1
            
            # Determinar nivel de riesgo
            if risk_score < 0.3:
                level = 'low'
            elif risk_score < 0.6:
                level = 'medium'
            elif risk_score < 0.8:
                level = 'high'
            else:
                level = 'very_high'
            
            return {
                'score': risk_score,
                'level': level,
                'factors': risk_factors,
                'recommendation': 'proceed' if risk_score < 0.5 else 'caution' if risk_score < 0.8 else 'avoid'
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error análisis riesgo: {e}")
            return {'score': 0.5, 'level': 'medium', 'factors': [], 'recommendation': 'caution'}
    
    def _analyze_timing(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar timing de la oportunidad ⏰"""
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Horario comercial óptimo
            is_business_hours = 9 <= current_hour <= 21
            
            # Score de timing
            if is_business_hours:
                if 10 <= current_hour <= 18:  # Horario prime
                    timing_score = 1.0
                else:  # Horario comercial pero no prime
                    timing_score = 0.8
            else:  # Fuera de horario
                timing_score = 0.3
            
            # Próxima ventana óptima
            if is_business_hours and current_hour <= 18:
                next_optimal = current_time + timedelta(minutes=30)
            else:
                # Próximo día 10 AM
                next_optimal = current_time.replace(hour=10, minute=0, second=0, microsecond=0)
                if current_hour >= 22:
                    next_optimal += timedelta(days=1)
            
            return {
                'score': timing_score,
                'is_optimal_time': is_business_hours,
                'current_hour': current_hour,
                'next_optimal_window': next_optimal.isoformat(),
                'recommendation': 'execute_now' if timing_score >= 0.8 else 'wait_for_optimal'
            }
            
        except Exception:
            return {'score': 0.5, 'is_optimal_time': True, 'recommendation': 'execute_now'}
    
    async def _make_predictions(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Hacer predicciones sobre la oportunidad 🔮"""
        try:
            # Duración estimada (basado en volatilidad general)
            base_duration = 24  # 24 horas base
            
            margin = opportunity['margin']
            percentage = opportunity['percentage']
            
            # Oportunidades más grandes tienden a durar menos (más competitivas)
            if margin > 100000:
                duration_hours = 6
            elif margin > 50000:
                duration_hours = 12
            elif percentage > 30:
                duration_hours = 8
            else:
                duration_hours = base_duration
            
            # Tasa de éxito estimada
            confidence = opportunity.get('confidence_score', 0.5)
            risk_score = opportunity.get('risk_analysis', {}).get('score', 0.5)
            
            success_rate = max(0.1, min(0.95, confidence * (1.0 - risk_score)))
            
            # Momento óptimo
            timing_analysis = opportunity.get('timing_analysis', {})
            if timing_analysis.get('is_optimal_time', False):
                optimal_execution = datetime.now() + timedelta(minutes=15)
            else:
                optimal_execution = datetime.fromisoformat(
                    timing_analysis.get('next_optimal_window', datetime.now().isoformat())
                )
            
            return {
                'duration_hours': duration_hours,
                'success_rate': success_rate,
                'optimal_execution_time': optimal_execution.isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=duration_hours)).isoformat()
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error haciendo predicciones: {e}")
            return {
                'duration_hours': 24,
                'success_rate': 0.7,
                'optimal_execution_time': datetime.now().isoformat()
            }
    
    def _determine_priority(self, opportunity: Dict[str, Any]) -> int:
        """Determinar prioridad (1-5) 🏆"""
        try:
            opportunity_score = opportunity.get('opportunity_score', 0.5)
            confidence_score = opportunity.get('confidence_score', 0.5)
            timing_score = opportunity.get('timing_score', 0.5)
            
            # Score combinado
            combined_score = (
                opportunity_score * 0.5 +
                confidence_score * 0.3 +
                timing_score * 0.2
            )
            
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
            return 3  # Default medio
    
    def _determine_tier(self, opportunity: Dict[str, Any]) -> str:
        """Determinar tier de la oportunidad 📊"""
        try:
            margin = opportunity['margin']
            confidence = opportunity.get('confidence_score', 0.5)
            opportunity_score = opportunity.get('opportunity_score', 0.5)
            
            # Critical: Alto margen + alta confianza
            if margin >= 100000 and confidence >= 0.8 and opportunity_score >= 0.8:
                return 'critical'
            
            # Important: Buen margen + buena confianza
            elif margin >= 50000 and confidence >= 0.6 and opportunity_score >= 0.6:
                return 'important'
            
            # Tracking: Resto
            else:
                return 'tracking'
                
        except Exception:
            return 'tracking'
    
    async def _validate_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Validar que la oportunidad sea viable 🔍"""
        try:
            # Validaciones básicas
            if opportunity.get('margin', 0) < self.config.min_margin_clp:
                return False
            
            if opportunity.get('percentage', 0) < self.config.min_percentage:
                return False
            
            # Validar que no sea ratio de precio extremo
            cheap_price = opportunity.get('cheap_price', 0)
            expensive_price = opportunity.get('expensive_price', 0)
            
            if cheap_price <= 0 or expensive_price <= 0:
                return False
            
            price_ratio = expensive_price / cheap_price
            if price_ratio > self.config.max_price_ratio:
                return False
            
            # Validar productos diferentes
            cheap_retailer = opportunity.get('cheap_product', {}).get('retailer', '')
            expensive_retailer = opportunity.get('expensive_product', {}).get('retailer', '')
            
            if cheap_retailer == expensive_retailer:
                return False
            
            # Validar retailers habilitados
            if not self.config.is_retailer_enabled(cheap_retailer):
                return False
            
            if not self.config.is_retailer_enabled(expensive_retailer):
                return False
            
            # Validar nivel de riesgo aceptable
            risk_level = opportunity.get('risk_analysis', {}).get('level', 'medium')
            if risk_level == 'very_high':
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"⚠️ Error validando oportunidad: {e}")
            return False
    
    def _extract_best_price(self, product: Dict[str, Any]) -> float:
        """Extraer mejor precio de producto 💰"""
        try:
            price_fields = [
                'precio_min_num', 'precio_oferta_num', 'precio_tarjeta_num',
                'precio_normal_num', 'precio', 'normal_num', 'oferta_num',
                'precio_actual'
            ]
            
            valid_prices = []
            for field in price_fields:
                price = product.get(field, 0)
                if isinstance(price, (int, float)) and price > 0:
                    valid_prices.append(float(price))
            
            return min(valid_prices) if valid_prices else 0.0
            
        except Exception:
            return 0.0
    
    async def get_detector_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del detector 📊"""
        return self.metrics.copy()
    
    async def close(self):
        """Cerrar detector 🔚"""
        try:
            logger.info("🔚 OpportunityDetector V5 cerrado")
        except Exception as e:
            logger.error(f"❌ Error cerrando detector: {e}")