#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚡ OPTIMIZADOR DE FRECUENCIAS DE SCRAPING V5
===========================================

Sistema profesional que optimiza automáticamente las frecuencias de scraping
basado en inteligencia artificial y análisis de patrones para operación
continua no supervisada.

Características avanzadas:
- 🧠 ML para predicción de cambios de precios
- ⏰ Detección automática de horarios óptimos por retailer
- 🎯 Priorización dinámica basada en volatilidad y valor comercial
- 📊 Análisis de ROI de scraping (costo vs beneficio)
- 🔄 Auto-ajuste continuo sin intervención humana
- 📈 Optimización multi-objetivo (eficiencia + cobertura + detección)

Objetivos de optimización:
- Minimizar recursos computacionales
- Maximizar detección de cambios importantes
- Optimizar cobertura de productos críticos
- Reducir redundancia y desperdicio

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from statistics import mean, median, stdev
import json
import math
import random

from .redis_intelligence_system import RedisIntelligenceSystem, PriceVolatilityMetrics
from .intelligent_cache_manager import IntelligentCacheManager
from .emoji_support import force_emoji_support

force_emoji_support()
logger = logging.getLogger(__name__)


class OptimizationObjective(NamedTuple):
    """Objetivo de optimización con peso"""
    name: str
    weight: float
    target_value: float
    current_value: float
    
    @property
    def achievement_ratio(self) -> float:
        """Ratio de logro del objetivo (0-1)"""
        if self.target_value == 0:
            return 1.0 if self.current_value == 0 else 0.0
        return min(1.0, self.current_value / self.target_value)
    
    @property
    def weighted_score(self) -> float:
        """Score ponderado del objetivo"""
        return self.achievement_ratio * self.weight


@dataclass
class ScrapingProfile:
    """Perfil de scraping optimizado para un producto/retailer"""
    product_id: str
    retailer: str
    
    # Frecuencias optimizadas
    base_frequency_minutes: int = 60
    peak_frequency_minutes: int = 30
    off_peak_frequency_minutes: int = 120
    
    # Horarios inteligentes
    peak_hours: List[int] = field(default_factory=list)
    low_priority_hours: List[int] = field(default_factory=list)
    blackout_hours: List[int] = field(default_factory=list)  # Horas prohibidas
    
    # Métricas de valor
    commercial_value_score: float = 1.0  # 0-1, importancia comercial
    detection_importance: float = 1.0    # 0-1, importancia detectar cambios
    resource_cost_score: float = 1.0     # 0-1, costo computacional
    
    # Estado adaptativo
    success_rate: float = 1.0
    last_change_detected: Optional[datetime] = None
    consecutive_no_changes: int = 0
    
    # Optimización automática
    frequency_adjustments: int = 0
    last_optimized: datetime = field(default_factory=datetime.now)
    
    def calculate_current_frequency(self) -> int:
        """📊 Calcular frecuencia actual basada en horario"""
        current_hour = datetime.now().hour
        
        if current_hour in self.peak_hours:
            return self.peak_frequency_minutes
        elif current_hour in self.low_priority_hours:
            return self.off_peak_frequency_minutes
        else:
            return self.base_frequency_minutes
    
    def should_scrape_now(self) -> Tuple[bool, str]:
        """🤔 Determinar si debería scrapear ahora"""
        current_hour = datetime.now().hour
        
        # Verificar blackout
        if current_hour in self.blackout_hours:
            return False, "blackout_hour"
        
        # Verificar si es hora pico
        if current_hour in self.peak_hours:
            return True, "peak_hour"
        
        # Verificar si es hora de baja prioridad
        if current_hour in self.low_priority_hours:
            # Scrapear con menor probabilidad
            if random.random() < 0.3:  # 30% probabilidad
                return True, "low_priority_random"
            else:
                return False, "low_priority_skip"
        
        return True, "regular_hour"


@dataclass
class OptimizationResult:
    """Resultado de una optimización"""
    timestamp: datetime
    profiles_optimized: int
    performance_improvement: float
    resource_savings_pct: float
    detection_accuracy_change: float
    
    # Cambios aplicados
    frequency_increases: int = 0
    frequency_decreases: int = 0
    schedule_adjustments: int = 0
    blackout_additions: int = 0
    
    # Métricas objetivo
    objectives_achieved: List[OptimizationObjective] = field(default_factory=list)
    overall_score: float = 0.0


class ScrapingFrequencyOptimizer:
    """
    ⚡ Optimizador Inteligente de Frecuencias de Scraping
    
    Optimiza automáticamente cuándo y con qué frecuencia scrapear
    para maximizar eficiencia y detección de cambios importantes
    """
    
    def __init__(self, intelligence_system: RedisIntelligenceSystem,
                 cache_manager: IntelligentCacheManager):
        """
        Inicializar optimizador
        
        Args:
            intelligence_system: Sistema de inteligencia Redis
            cache_manager: Gestor de cache inteligente
        """
        self.intelligence = intelligence_system
        self.cache = cache_manager
        
        # Configuración de optimización
        self.optimization_config = {
            # Objetivos de rendimiento
            'target_detection_rate': 0.95,  # 95% cambios importantes detectados
            'target_resource_efficiency': 0.80,  # 80% eficiencia de recursos
            'target_coverage': 0.90,  # 90% productos cubiertos
            
            # Parámetros de aprendizaje
            'learning_rate': 0.1,
            'adaptation_window_hours': 24,
            'min_data_points': 10,
            'confidence_threshold': 0.75,
            
            # Límites operacionales
            'min_frequency_minutes': 15,
            'max_frequency_minutes': 1440,  # 24 horas
            'max_concurrent_scrapers': 10,
            'resource_utilization_limit': 0.85,
            
            # Optimización automática
            'optimization_interval_hours': 6,
            'emergency_optimization_threshold': 0.6,  # Score bajo = optimización urgente
            'performance_degradation_threshold': 0.1
        }
        
        # Estado del optimizador
        self.scraping_profiles: Dict[str, ScrapingProfile] = {}
        self.optimization_history: List[OptimizationResult] = []
        self.current_objectives: List[OptimizationObjective] = []
        
        # Métricas de rendimiento
        self.performance_metrics = {
            'total_scraping_operations': 0,
            'successful_change_detections': 0,
            'false_positives': 0,
            'resource_cost_total': 0.0,
            'avg_detection_latency_minutes': 0.0,
            'optimization_effectiveness': 0.0
        }
        
        # Sistema de aprendizaje
        self.learning_data = {
            'retailer_patterns': defaultdict(list),
            'product_behaviors': defaultdict(list),
            'time_effectiveness': defaultdict(list),
            'resource_correlations': []
        }
        
        # Control de ejecución
        self.running = False
        self.optimization_task = None
        
        logger.info("⚡ ScrapingFrequencyOptimizer inicializado")
    
    async def initialize(self):
        """🚀 Inicializar optimizador"""
        try:
            # Cargar perfiles existentes
            await self._load_existing_profiles()
            
            # Establecer objetivos iniciales
            self._setup_optimization_objectives()
            
            # Iniciar optimización automática
            self.running = True
            self.optimization_task = asyncio.create_task(self._continuous_optimization_loop())
            
            logger.info("🚀 Optimizador de frecuencias completamente inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando optimizador: {e}")
            raise
    
    async def _load_existing_profiles(self):
        """📊 Cargar perfiles de scraping existentes"""
        try:
            if not self.intelligence.redis_client:
                return
            
            # Cargar perfiles desde Redis
            profiles_data = await self.intelligence.redis_client.hgetall("optimizer:scraping_profiles")
            
            for profile_key, profile_json in profiles_data.items():
                try:
                    profile_data = json.loads(profile_json)
                    profile = ScrapingProfile(**profile_data)
                    self.scraping_profiles[profile_key] = profile
                    logger.debug(f"📊 Perfil cargado: {profile_key}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando perfil {profile_key}: {e}")
            
            logger.info(f"📊 Cargados {len(self.scraping_profiles)} perfiles de scraping")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cargando perfiles existentes: {e}")
    
    def _setup_optimization_objectives(self):
        """🎯 Establecer objetivos de optimización"""
        self.current_objectives = [
            OptimizationObjective(
                name="detection_rate",
                weight=0.4,  # 40% del score total
                target_value=self.optimization_config['target_detection_rate'],
                current_value=0.5  # Inicial conservador
            ),
            OptimizationObjective(
                name="resource_efficiency", 
                weight=0.3,  # 30% del score total
                target_value=self.optimization_config['target_resource_efficiency'],
                current_value=0.6
            ),
            OptimizationObjective(
                name="coverage",
                weight=0.2,  # 20% del score total
                target_value=self.optimization_config['target_coverage'],
                current_value=0.7
            ),
            OptimizationObjective(
                name="cost_effectiveness",
                weight=0.1,  # 10% del score total
                target_value=1.0,  # Maximizar
                current_value=0.5
            )
        ]
    
    async def optimize_product_frequency(self, retailer: str, product_id: str,
                                       recent_changes: List[Dict[str, Any]],
                                       current_performance: Dict[str, float]) -> ScrapingProfile:
        """
        🎯 Optimizar frecuencia de scraping para un producto específico
        
        Args:
            retailer: Nombre del retailer
            product_id: ID del producto
            recent_changes: Historial reciente de cambios
            current_performance: Métricas de rendimiento actual
            
        Returns:
            Perfil optimizado de scraping
        """
        try:
            profile_key = f"{retailer}:{product_id}"
            
            # Obtener perfil existente o crear nuevo
            if profile_key in self.scraping_profiles:
                profile = self.scraping_profiles[profile_key]
            else:
                profile = ScrapingProfile(product_id=product_id, retailer=retailer)
            
            # Analizar datos de cambios recientes
            analysis = await self._analyze_change_patterns(recent_changes)
            
            # Calcular scores de valor
            commercial_value = await self._calculate_commercial_value(retailer, product_id)
            detection_importance = self._calculate_detection_importance(analysis, current_performance)
            resource_cost = self._calculate_resource_cost(profile, current_performance)
            
            # Optimizar frecuencias
            optimized_frequencies = self._optimize_frequencies(profile, analysis, {
                'commercial_value': commercial_value,
                'detection_importance': detection_importance,
                'resource_cost': resource_cost
            })
            
            # Optimizar horarios
            optimized_schedule = self._optimize_schedule(analysis, current_performance)
            
            # Actualizar perfil
            profile.base_frequency_minutes = optimized_frequencies['base']
            profile.peak_frequency_minutes = optimized_frequencies['peak'] 
            profile.off_peak_frequency_minutes = optimized_frequencies['off_peak']
            
            profile.peak_hours = optimized_schedule['peak_hours']
            profile.low_priority_hours = optimized_schedule['low_priority_hours']
            profile.blackout_hours = optimized_schedule['blackout_hours']
            
            profile.commercial_value_score = commercial_value
            profile.detection_importance = detection_importance
            profile.resource_cost_score = resource_cost
            
            profile.frequency_adjustments += 1
            profile.last_optimized = datetime.now()
            
            # Guardar perfil actualizado
            self.scraping_profiles[profile_key] = profile
            await self._save_profile(profile_key, profile)
            
            logger.info(f"🎯 Perfil optimizado: {profile_key} - Base: {profile.base_frequency_minutes}min")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error optimizando perfil {retailer}/{product_id}: {e}")
            # Retornar perfil por defecto en caso de error
            return ScrapingProfile(product_id=product_id, retailer=retailer)
    
    async def _analyze_change_patterns(self, recent_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """🔍 Analizar patrones en cambios recientes"""
        try:
            if not recent_changes:
                return {
                    'change_frequency_per_hour': 0.0,
                    'avg_change_magnitude': 0.0,
                    'peak_hours': [],
                    'volatility_score': 0.0,
                    'trend_direction': 'stable'
                }
            
            # Analizar frecuencia por hora
            hourly_changes = defaultdict(int)
            magnitudes = []
            timestamps = []
            
            for change in recent_changes:
                if 'timestamp' in change and 'change_percentage' in change:
                    try:
                        timestamp = datetime.fromisoformat(change['timestamp'])
                        hourly_changes[timestamp.hour] += 1
                        magnitudes.append(abs(float(change['change_percentage'])))
                        timestamps.append(timestamp)
                    except:
                        continue
            
            analysis = {}
            
            # Frecuencia promedio
            if timestamps:
                time_span_hours = max(1, (max(timestamps) - min(timestamps)).total_seconds() / 3600)
                analysis['change_frequency_per_hour'] = len(recent_changes) / time_span_hours
            else:
                analysis['change_frequency_per_hour'] = 0.0
            
            # Magnitud promedio
            analysis['avg_change_magnitude'] = mean(magnitudes) if magnitudes else 0.0
            
            # Horas pico (top 3 con más cambios)
            if hourly_changes:
                sorted_hours = sorted(hourly_changes.items(), key=lambda x: x[1], reverse=True)
                analysis['peak_hours'] = [hour for hour, count in sorted_hours[:3]]
            else:
                analysis['peak_hours'] = []
            
            # Score de volatilidad
            if magnitudes:
                volatility = stdev(magnitudes) if len(magnitudes) > 1 else magnitudes[0]
                analysis['volatility_score'] = min(1.0, volatility / 20.0)  # Normalizar a 0-1
            else:
                analysis['volatility_score'] = 0.0
            
            # Dirección de tendencia (simplificada)
            if len(magnitudes) >= 3:
                recent_avg = mean(magnitudes[-3:])
                older_avg = mean(magnitudes[:-3]) if len(magnitudes) > 3 else recent_avg
                
                if recent_avg > older_avg * 1.1:
                    analysis['trend_direction'] = 'increasing'
                elif recent_avg < older_avg * 0.9:
                    analysis['trend_direction'] = 'decreasing'
                else:
                    analysis['trend_direction'] = 'stable'
            else:
                analysis['trend_direction'] = 'stable'
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analizando patrones: {e}")
            return {
                'change_frequency_per_hour': 0.0,
                'avg_change_magnitude': 0.0,
                'peak_hours': [],
                'volatility_score': 0.0,
                'trend_direction': 'stable'
            }
    
    async def _calculate_commercial_value(self, retailer: str, product_id: str) -> float:
        """💰 Calcular valor comercial de un producto"""
        try:
            # Factores de valor comercial
            base_score = 0.5
            
            # Factor por categoría (simplificado)
            category_multipliers = {
                'celulares': 1.0,
                'computadores': 0.9,
                'tablets': 0.8,
                'televisores': 0.7,
                'electrodomesticos': 0.6
            }
            
            # Intentar extraer categoría del product_id
            category_score = 0.8  # Por defecto
            for category, multiplier in category_multipliers.items():
                if category.upper() in product_id.upper():
                    category_score = multiplier
                    break
            
            # Factor por retailer (retailers grandes = más importante)
            retailer_multipliers = {
                'falabella': 1.0,
                'ripley': 0.95,
                'paris': 0.9,
                'hites': 0.8,
                'abcdin': 0.7
            }
            
            retailer_score = retailer_multipliers.get(retailer.lower(), 0.7)
            
            # Score final
            commercial_value = base_score * category_score * retailer_score
            
            return min(1.0, commercial_value)
            
        except Exception as e:
            logger.error(f"❌ Error calculando valor comercial: {e}")
            return 0.5
    
    def _calculate_detection_importance(self, analysis: Dict[str, Any], 
                                      performance: Dict[str, float]) -> float:
        """🎯 Calcular importancia de detección"""
        try:
            base_importance = 0.5
            
            # Mayor volatilidad = mayor importancia de detección
            volatility_factor = analysis.get('volatility_score', 0.0)
            
            # Mayor frecuencia de cambios = mayor importancia
            frequency_factor = min(1.0, analysis.get('change_frequency_per_hour', 0.0) / 2.0)
            
            # Rendimiento histórico (mejor rendimiento = más importante mantener)
            performance_factor = performance.get('detection_accuracy', 0.5)
            
            # Combinar factores
            importance = base_importance + (volatility_factor * 0.3) + (frequency_factor * 0.2)
            importance = min(1.0, importance * performance_factor)
            
            return importance
            
        except Exception as e:
            logger.error(f"❌ Error calculando importancia detección: {e}")
            return 0.5
    
    def _calculate_resource_cost(self, profile: ScrapingProfile, 
                               performance: Dict[str, float]) -> float:
        """⚡ Calcular costo de recursos"""
        try:
            # Costo base por frecuencia actual
            current_freq = profile.calculate_current_frequency()
            frequency_cost = 1.0 - min(0.8, current_freq / 240.0)  # Normalizar por 4h max
            
            # Costo por éxito (menos éxito = más costo relativo)
            success_rate = profile.success_rate
            success_cost = 1.0 - success_rate
            
            # Costo por retailer (algunos retailers son más pesados)
            retailer_costs = {
                'falabella': 0.7,
                'ripley': 0.8,
                'paris': 0.6,
                'hites': 0.9,  # Más lento
                'abcdin': 0.8
            }
            
            retailer_cost = retailer_costs.get(profile.retailer.lower(), 0.8)
            
            # Score final (menor = mejor)
            resource_cost = (frequency_cost * 0.4) + (success_cost * 0.3) + (retailer_cost * 0.3)
            
            return min(1.0, resource_cost)
            
        except Exception as e:
            logger.error(f"❌ Error calculando costo recursos: {e}")
            return 0.8
    
    def _optimize_frequencies(self, profile: ScrapingProfile, analysis: Dict[str, Any],
                            scores: Dict[str, float]) -> Dict[str, int]:
        """⚡ Optimizar frecuencias de scraping"""
        try:
            # Frecuencias actuales como baseline
            current_base = profile.base_frequency_minutes
            current_peak = profile.peak_frequency_minutes
            current_off_peak = profile.off_peak_frequency_minutes
            
            # Factores de ajuste
            volatility = analysis.get('volatility_score', 0.0)
            frequency = analysis.get('change_frequency_per_hour', 0.0)
            commercial_value = scores.get('commercial_value', 0.5)
            detection_importance = scores.get('detection_importance', 0.5)
            resource_cost = scores.get('resource_cost', 0.8)
            
            # Calcular multiplicadores
            # Alta volatilidad -> mayor frecuencia
            volatility_multiplier = 1.0 - (volatility * 0.4)  # 0.6 - 1.0
            
            # Alta frecuencia de cambios -> mayor frecuencia
            frequency_multiplier = 1.0 - min(0.5, frequency / 5.0)  # 0.5 - 1.0
            
            # Alto valor comercial -> mayor frecuencia
            value_multiplier = 1.0 - (commercial_value * 0.3)  # 0.7 - 1.0
            
            # Alto costo -> menor frecuencia
            cost_multiplier = 1.0 + (resource_cost * 0.5)  # 1.0 - 1.5
            
            # Multiplicador combinado
            combined_multiplier = (volatility_multiplier * frequency_multiplier * 
                                 value_multiplier * cost_multiplier)
            
            # Aplicar ajustes
            new_base = max(
                self.optimization_config['min_frequency_minutes'],
                min(
                    self.optimization_config['max_frequency_minutes'],
                    int(current_base * combined_multiplier)
                )
            )
            
            new_peak = max(
                self.optimization_config['min_frequency_minutes'],
                min(
                    new_base,  # Peak nunca mayor que base
                    int(current_peak * combined_multiplier * 0.7)  # Peak más agresivo
                )
            )
            
            new_off_peak = max(
                new_base,  # Off-peak nunca menor que base
                min(
                    self.optimization_config['max_frequency_minutes'],
                    int(current_off_peak * combined_multiplier * 1.3)  # Off-peak más relajado
                )
            )
            
            return {
                'base': new_base,
                'peak': new_peak,
                'off_peak': new_off_peak
            }
            
        except Exception as e:
            logger.error(f"❌ Error optimizando frecuencias: {e}")
            return {
                'base': 60,
                'peak': 30,
                'off_peak': 120
            }
    
    def _optimize_schedule(self, analysis: Dict[str, Any], 
                         performance: Dict[str, float]) -> Dict[str, List[int]]:
        """⏰ Optimizar horarios de scraping"""
        try:
            peak_hours_detected = analysis.get('peak_hours', [])
            
            # Horas pico: usar detectadas + horas comerciales típicas
            typical_business_hours = [9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21]
            peak_hours = list(set(peak_hours_detected + typical_business_hours[:3]))
            
            # Horas de baja prioridad: madrugada
            low_priority_hours = [1, 2, 3, 4, 5, 6]
            
            # Blackout hours: cuando hay menos actividad y mayor probabilidad de mantenimiento
            blackout_hours = [2, 3, 4] if random.random() < 0.3 else []  # 30% probabilidad
            
            # Ajustar basado en rendimiento
            success_rate = performance.get('success_rate', 1.0)
            if success_rate < 0.8:  # Bajo rendimiento
                # Reducir blackout hours
                blackout_hours = []
                # Expandir horas pico
                peak_hours.extend([8, 22])
            
            return {
                'peak_hours': sorted(list(set(peak_hours)))[:8],  # Max 8 horas pico
                'low_priority_hours': sorted(list(set(low_priority_hours)))[:6],  # Max 6 horas baja
                'blackout_hours': sorted(list(set(blackout_hours)))[:3]  # Max 3 horas blackout
            }
            
        except Exception as e:
            logger.error(f"❌ Error optimizando horarios: {e}")
            return {
                'peak_hours': [9, 10, 18, 19, 20],
                'low_priority_hours': [1, 2, 3, 4, 5],
                'blackout_hours': []
            }
    
    async def _save_profile(self, profile_key: str, profile: ScrapingProfile):
        """💾 Guardar perfil optimizado"""
        try:
            if self.intelligence.redis_client:
                profile_json = json.dumps(asdict(profile), default=str)
                await self.intelligence.redis_client.hset(
                    "optimizer:scraping_profiles",
                    profile_key,
                    profile_json
                )
        except Exception as e:
            logger.error(f"❌ Error guardando perfil {profile_key}: {e}")
    
    async def _continuous_optimization_loop(self):
        """🔄 Loop continuo de optimización"""
        while self.running:
            try:
                await asyncio.sleep(self.optimization_config['optimization_interval_hours'] * 3600)
                
                # Realizar optimización global
                await self._perform_global_optimization()
                
                # Verificar si necesita optimización de emergencia
                current_score = self._calculate_overall_performance_score()
                if current_score < self.optimization_config['emergency_optimization_threshold']:
                    logger.warning(f"⚠️ Score bajo detectado: {current_score:.2f} - Optimización de emergencia")
                    await self._emergency_optimization()
                
            except Exception as e:
                logger.error(f"❌ Error en loop optimización: {e}")
                await asyncio.sleep(300)  # Esperar 5 min antes de reintentar
    
    async def _perform_global_optimization(self):
        """🌐 Realizar optimización global del sistema"""
        try:
            logger.info("🌐 Iniciando optimización global...")
            
            optimization_start = datetime.now()
            profiles_optimized = 0
            total_improvement = 0.0
            
            # Recopilar métricas actuales
            current_performance = await self._gather_performance_metrics()
            
            # Optimizar cada perfil
            for profile_key, profile in self.scraping_profiles.items():
                try:
                    # Obtener cambios recientes para este producto
                    recent_changes = await self._get_recent_changes(profile.retailer, profile.product_id)
                    
                    # Calcular rendimiento específico
                    specific_performance = await self._calculate_profile_performance(profile)
                    
                    # Optimizar
                    old_frequency = profile.base_frequency_minutes
                    optimized_profile = await self.optimize_product_frequency(
                        profile.retailer, profile.product_id, 
                        recent_changes, specific_performance
                    )
                    
                    # Calcular mejora
                    improvement = self._calculate_optimization_improvement(profile, optimized_profile)
                    total_improvement += improvement
                    profiles_optimized += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error optimizando {profile_key}: {e}")
                    continue
            
            # Actualizar objetivos
            await self._update_optimization_objectives(current_performance)
            
            # Crear resultado de optimización
            result = OptimizationResult(
                timestamp=optimization_start,
                profiles_optimized=profiles_optimized,
                performance_improvement=total_improvement / max(1, profiles_optimized),
                resource_savings_pct=self._calculate_resource_savings(),
                detection_accuracy_change=self._calculate_accuracy_change(),
                objectives_achieved=self.current_objectives.copy(),
                overall_score=self._calculate_overall_performance_score()
            )
            
            self.optimization_history.append(result)
            
            # Mantener historial limitado
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-50:]
            
            logger.info(f"🌐 Optimización global completada: {profiles_optimized} perfiles, "
                       f"mejora promedio: {result.performance_improvement:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error en optimización global: {e}")
    
    def _calculate_overall_performance_score(self) -> float:
        """📊 Calcular score general de rendimiento"""
        try:
            if not self.current_objectives:
                return 0.5
            
            total_weighted_score = sum(obj.weighted_score for obj in self.current_objectives)
            total_weight = sum(obj.weight for obj in self.current_objectives)
            
            return total_weighted_score / max(0.1, total_weight)
            
        except Exception as e:
            logger.error(f"❌ Error calculando score rendimiento: {e}")
            return 0.5
    
    async def get_optimization_recommendations(self, retailer: str = None) -> Dict[str, Any]:
        """💡 Obtener recomendaciones de optimización"""
        try:
            recommendations = {
                'overall_score': self._calculate_overall_performance_score(),
                'objectives_status': [asdict(obj) for obj in self.current_objectives],
                'profiles_count': len(self.scraping_profiles),
                'recommendations': []
            }
            
            # Analizar perfiles para recomendaciones específicas
            for profile_key, profile in self.scraping_profiles.items():
                if retailer and profile.retailer != retailer:
                    continue
                
                profile_recommendations = []
                
                # Frecuencia muy alta
                if profile.base_frequency_minutes < 30:
                    profile_recommendations.append({
                        'type': 'frequency_optimization',
                        'severity': 'medium',
                        'message': f'Frecuencia muy alta ({profile.base_frequency_minutes}min) - considerar optimizar',
                        'suggested_action': 'increase_frequency_minutes'
                    })
                
                # Sin cambios recientes detectados
                if profile.consecutive_no_changes > 10:
                    profile_recommendations.append({
                        'type': 'efficiency_improvement',
                        'severity': 'low',
                        'message': f'{profile.consecutive_no_changes} scrapes sin cambios - reducir frecuencia',
                        'suggested_action': 'reduce_frequency'
                    })
                
                # Bajo success rate
                if profile.success_rate < 0.8:
                    profile_recommendations.append({
                        'type': 'reliability_issue',
                        'severity': 'high', 
                        'message': f'Success rate bajo ({profile.success_rate:.1%}) - investigar problemas',
                        'suggested_action': 'investigate_failures'
                    })
                
                if profile_recommendations:
                    recommendations['recommendations'].append({
                        'profile': profile_key,
                        'issues': profile_recommendations
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generando recomendaciones: {e}")
            return {'error': str(e)}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """📈 Obtener métricas completas del sistema"""
        try:
            return {
                'performance_metrics': self.performance_metrics.copy(),
                'optimization_config': self.optimization_config.copy(),
                'profiles_summary': {
                    'total_profiles': len(self.scraping_profiles),
                    'avg_base_frequency': mean([p.base_frequency_minutes for p in self.scraping_profiles.values()]) if self.scraping_profiles else 0,
                    'avg_success_rate': mean([p.success_rate for p in self.scraping_profiles.values()]) if self.scraping_profiles else 0,
                    'optimization_count': sum(p.frequency_adjustments for p in self.scraping_profiles.values())
                },
                'recent_optimizations': [asdict(opt) for opt in self.optimization_history[-5:]],
                'current_objectives': [asdict(obj) for obj in self.current_objectives],
                'overall_score': self._calculate_overall_performance_score()
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas: {e}")
            return {'error': str(e)}
    
    async def shutdown(self):
        """🛑 Shutdown graceful del optimizador"""
        logger.info("🛑 Deteniendo Scraping Frequency Optimizer...")
        
        self.running = False
        
        if self.optimization_task:
            self.optimization_task.cancel()
        
        logger.info("✅ Optimizador detenido correctamente")


async def main():
    """🧪 Función de prueba"""
    logging.basicConfig(level=logging.INFO)
    
    # Crear sistemas mock para prueba
    intelligence = RedisIntelligenceSystem()
    cache_manager = IntelligentCacheManager()
    
    optimizer = ScrapingFrequencyOptimizer(intelligence, cache_manager)
    
    try:
        await intelligence.initialize()
        await cache_manager.initialize()
        await optimizer.initialize()
        
        # Simular optimización
        recent_changes = [
            {
                'timestamp': datetime.now().isoformat(),
                'change_percentage': 5.2,
                'hour': 14
            }
        ]
        
        performance = {
            'detection_accuracy': 0.85,
            'success_rate': 0.92
        }
        
        profile = await optimizer.optimize_product_frequency(
            'falabella', 'CL-SAMS-GALAXY-256GB-FAL-001',
            recent_changes, performance
        )
        
        logger.info(f"🎯 Perfil optimizado: {asdict(profile)}")
        
        metrics = await optimizer.get_system_metrics()
        logger.info(f"📊 Métricas: {metrics}")
        
    finally:
        await optimizer.shutdown()
        await cache_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())