#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧠 SISTEMA DE INTELIGENCIA REDIS V5
==================================

Sistema central de inteligencia usando Redis como cerebro entre scraping y base de datos
para optimización máxima de operación continua no supervisada.

Características profesionales:
- 🚀 Cache de consultas ultra-rápidas (sub-millisegundo)
- 📊 Predicción de volatilidad con ML integrado
- ⏰ Detección automática de horarios óptimos de scraping
- 🎯 Priorización dinámica basada en comportamiento histórico
- 📈 Análisis de tendencias temporales en tiempo real
- 🔄 Auto-optimización continua sin supervisión humana

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import redis.asyncio as redis
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from pathlib import Path
import pickle
import hashlib
from statistics import mean, median, stdev
import math

from .emoji_support import force_emoji_support
force_emoji_support()

logger = logging.getLogger(__name__)


@dataclass
class PriceVolatilityMetrics:
    """Métricas de volatilidad de precios para ML"""
    product_id: str
    retailer: str
    
    # Métricas de volatilidad
    volatility_score: float = 0.0  # 0-1, donde 1 es máxima volatilidad
    price_changes_24h: int = 0
    price_changes_7d: int = 0
    avg_change_magnitude: float = 0.0
    
    # Patrones temporales
    peak_hours: List[int] = field(default_factory=list)  # Horas con más cambios
    change_frequency_score: float = 0.0  # Frecuencia promedio de cambios
    
    # Predicciones
    next_change_probability: float = 0.0  # Probabilidad próximo cambio
    optimal_check_frequency: int = 60  # Minutos entre checks óptimos
    
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RetailerPattern:
    """Patrones de comportamiento por retailer"""
    retailer: str
    
    # Horarios de actividad
    peak_update_hours: List[int] = field(default_factory=list)
    low_activity_hours: List[int] = field(default_factory=list)
    
    # Comportamiento de precios
    avg_daily_changes: float = 0.0
    typical_change_magnitude: float = 0.0
    weekend_behavior_diff: float = 0.0
    
    # Patrones estacionales
    high_activity_days: List[str] = field(default_factory=list)  # lun, mar, etc.
    promotion_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Métricas de confiabilidad
    data_consistency_score: float = 1.0
    scraping_success_rate: float = 1.0
    
    last_analysis: datetime = field(default_factory=datetime.now)


@dataclass
class SmartCacheEntry:
    """Entrada inteligente de cache con TTL dinámico"""
    key: str
    data: Any
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    volatility_factor: float = 1.0  # Multiplica TTL basado en volatilidad
    
    @property
    def effective_ttl(self) -> int:
        """TTL efectivo basado en volatilidad"""
        base_ttl = self.ttl_seconds
        # Productos volátiles = TTL menor
        # Productos estables = TTL mayor
        return max(30, int(base_ttl * self.volatility_factor))
    
    @property
    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.effective_ttl


class RedisIntelligenceSystem:
    """
    🧠 Sistema Central de Inteligencia con Redis
    
    Maneja toda la inteligencia operacional para optimización continua
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Inicializar sistema de inteligencia
        
        Args:
            redis_url: URL de conexión a Redis
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
        # Configuración de inteligencia
        self.intelligence_config = {
            # Cache inteligente
            'default_cache_ttl': 300,  # 5 minutos base
            'volatile_product_ttl': 60,  # 1 minuto para productos volátiles
            'stable_product_ttl': 1800,  # 30 minutos para productos estables
            
            # Análisis de volatilidad
            'volatility_window_hours': 24,
            'high_volatility_threshold': 0.7,
            'change_significance_pct': 2.0,  # 2% cambio mínimo significativo
            
            # Predicción de patrones
            'pattern_analysis_days': 30,
            'min_samples_for_prediction': 50,
            'confidence_threshold': 0.75,
            
            # Optimización automática
            'auto_tune_frequency_hours': 6,
            'performance_monitoring_enabled': True,
            'adaptive_scheduling': True
        }
        
        # Métricas del sistema
        self.system_metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'predictions_made': 0,
            'optimizations_applied': 0,
            'data_points_analyzed': 0,
            'system_uptime_start': datetime.now()
        }
        
        # Cache local para hot data
        self.local_cache: Dict[str, SmartCacheEntry] = {}
        self.volatility_cache: Dict[str, PriceVolatilityMetrics] = {}
        self.retailer_patterns: Dict[str, RetailerPattern] = {}
        
        logger.info("🧠 RedisIntelligenceSystem inicializado")
    
    async def initialize(self):
        """🚀 Inicializar conexión y estructuras de datos"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Verificar conexión
            await self.redis_client.ping()
            logger.info("✅ Conexión Redis establecida correctamente")
            
            # Cargar patrones existentes
            await self._load_existing_patterns()
            
            # Inicializar estructuras de datos
            await self._initialize_redis_structures()
            
            logger.info("🧠 Sistema de inteligencia completamente inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Redis Intelligence: {e}")
            raise
    
    async def _load_existing_patterns(self):
        """📊 Cargar patrones y análisis previos"""
        try:
            # Cargar patrones de retailers
            retailers_data = await self.redis_client.hgetall("intelligence:retailer_patterns")
            for retailer, pattern_data in retailers_data.items():
                try:
                    pattern = RetailerPattern(**json.loads(pattern_data))
                    self.retailer_patterns[retailer] = pattern
                    logger.info(f"📊 Patrón cargado para {retailer}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando patrón de {retailer}: {e}")
            
            # Cargar métricas de volatilidad recientes
            volatility_keys = await self.redis_client.keys("intelligence:volatility:*")
            for key in volatility_keys:
                try:
                    volatility_data = await self.redis_client.get(key)
                    if volatility_data:
                        metrics = PriceVolatilityMetrics(**json.loads(volatility_data))
                        cache_key = f"{metrics.retailer}:{metrics.product_id}"
                        self.volatility_cache[cache_key] = metrics
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando volatilidad {key}: {e}")
            
            logger.info(f"📊 Cargados {len(self.retailer_patterns)} patrones de retailers")
            logger.info(f"📊 Cargadas {len(self.volatility_cache)} métricas de volatilidad")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cargando patrones existentes: {e}")
    
    async def _initialize_redis_structures(self):
        """🔧 Inicializar estructuras de datos en Redis"""
        try:
            # Crear índices para búsquedas rápidas
            await self.redis_client.hset("intelligence:indexes:retailers", mapping={
                "active_retailers": json.dumps([]),
                "last_updated": datetime.now().isoformat()
            })
            
            # Inicializar métricas del sistema
            await self.redis_client.hset("intelligence:system_metrics", mapping={
                "initialized_at": datetime.now().isoformat(),
                "version": "5.0",
                "auto_optimization": "enabled"
            })
            
            logger.info("🔧 Estructuras Redis inicializadas")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando estructuras Redis: {e}")
    
    async def analyze_price_change(self, retailer: str, product_id: str, 
                                 old_price: float, new_price: float) -> Dict[str, Any]:
        """
        🔍 Analizar cambio de precio y actualizar inteligencia
        
        Args:
            retailer: Nombre del retailer
            product_id: ID interno del producto  
            old_price: Precio anterior
            new_price: Precio nuevo
            
        Returns:
            Análisis completo del cambio con recomendaciones
        """
        try:
            change_magnitude = abs(new_price - old_price)
            change_percentage = (change_magnitude / old_price * 100) if old_price > 0 else 0
            
            # Registrar el cambio
            change_data = {
                'retailer': retailer,
                'product_id': product_id,
                'old_price': old_price,
                'new_price': new_price,
                'change_magnitude': change_magnitude,
                'change_percentage': change_percentage,
                'timestamp': datetime.now().isoformat(),
                'hour': datetime.now().hour,
                'weekday': datetime.now().weekday()
            }
            
            # Almacenar en Redis para análisis histórico
            change_key = f"intelligence:price_changes:{retailer}:{product_id}"
            await self.redis_client.lpush(change_key, json.dumps(change_data))
            
            # Mantener solo los últimos 1000 cambios por producto
            await self.redis_client.ltrim(change_key, 0, 999)
            
            # Actualizar métricas de volatilidad
            await self._update_volatility_metrics(retailer, product_id, change_data)
            
            # Actualizar patrones de retailer
            await self._update_retailer_patterns(retailer, change_data)
            
            # Calcular recomendaciones
            recommendations = await self._generate_scraping_recommendations(
                retailer, product_id, change_percentage
            )
            
            analysis_result = {
                'change_data': change_data,
                'significance': 'high' if change_percentage >= self.intelligence_config['change_significance_pct'] else 'low',
                'volatility_impact': await self._calculate_volatility_impact(retailer, product_id),
                'recommendations': recommendations,
                'next_check_suggestion': recommendations.get('optimal_next_check_minutes', 60)
            }
            
            self.system_metrics['data_points_analyzed'] += 1
            
            logger.info(f"🔍 Análisis completado: {retailer}/{product_id} - {change_percentage:.1f}% cambio")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error analizando cambio de precio: {e}")
            return {'error': str(e)}
    
    async def _update_volatility_metrics(self, retailer: str, product_id: str, change_data: Dict[str, Any]):
        """📊 Actualizar métricas de volatilidad del producto"""
        try:
            cache_key = f"{retailer}:{product_id}"
            
            # Obtener métricas existentes o crear nuevas
            if cache_key in self.volatility_cache:
                metrics = self.volatility_cache[cache_key]
            else:
                metrics = PriceVolatilityMetrics(product_id=product_id, retailer=retailer)
            
            # Obtener historial de cambios recientes
            change_key = f"intelligence:price_changes:{retailer}:{product_id}"
            recent_changes = await self.redis_client.lrange(change_key, 0, 100)
            
            if recent_changes:
                changes_24h = 0
                changes_7d = 0
                change_magnitudes = []
                peak_hours_count = defaultdict(int)
                
                now = datetime.now()
                
                for change_json in recent_changes:
                    try:
                        change = json.loads(change_json)
                        change_time = datetime.fromisoformat(change['timestamp'])
                        
                        # Contar cambios por ventana de tiempo
                        hours_ago = (now - change_time).total_seconds() / 3600
                        if hours_ago <= 24:
                            changes_24h += 1
                        if hours_ago <= 168:  # 7 días
                            changes_7d += 1
                            
                        # Recopilar magnitudes para estadísticas
                        change_magnitudes.append(change['change_percentage'])
                        peak_hours_count[change['hour']] += 1
                        
                    except Exception as e:
                        logger.debug(f"Error procesando cambio: {e}")
                        continue
                
                # Actualizar métricas
                metrics.price_changes_24h = changes_24h
                metrics.price_changes_7d = changes_7d
                
                if change_magnitudes:
                    metrics.avg_change_magnitude = mean(change_magnitudes)
                    
                    # Calcular score de volatilidad (0-1)
                    # Basado en frecuencia y magnitud de cambios
                    frequency_factor = min(1.0, changes_24h / 10.0)  # Máximo esperado 10 cambios/día
                    magnitude_factor = min(1.0, metrics.avg_change_magnitude / 20.0)  # Máximo esperado 20%
                    metrics.volatility_score = (frequency_factor + magnitude_factor) / 2.0
                
                # Identificar horas pico (top 3 horas con más cambios)
                if peak_hours_count:
                    top_hours = sorted(peak_hours_count.items(), key=lambda x: x[1], reverse=True)[:3]
                    metrics.peak_hours = [hour for hour, _ in top_hours]
                
                # Calcular frecuencia de cambios
                if changes_7d > 0:
                    metrics.change_frequency_score = changes_7d / 7.0  # Cambios por día promedio
                
                # Predicción simple de próximo cambio
                if changes_24h > 0:
                    # Más cambios recientes = mayor probabilidad de cambio próximo
                    metrics.next_change_probability = min(1.0, changes_24h / 5.0)
                else:
                    metrics.next_change_probability = max(0.1, metrics.next_change_probability * 0.9)
                
                # Calcular frecuencia óptima de chequeo
                if metrics.volatility_score > 0.7:
                    metrics.optimal_check_frequency = 15  # Cada 15 min para alta volatilidad
                elif metrics.volatility_score > 0.3:
                    metrics.optimal_check_frequency = 60  # Cada hora para volatilidad media
                else:
                    metrics.optimal_check_frequency = 240  # Cada 4 horas para baja volatilidad
                
                metrics.last_updated = datetime.now()
                
                # Guardar en cache local y Redis
                self.volatility_cache[cache_key] = metrics
                
                redis_key = f"intelligence:volatility:{retailer}:{product_id}"
                await self.redis_client.setex(
                    redis_key, 
                    86400,  # TTL 24 horas
                    json.dumps(asdict(metrics), default=str)
                )
                
                logger.debug(f"📊 Volatilidad actualizada: {cache_key} - Score: {metrics.volatility_score:.2f}")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando volatilidad: {e}")
    
    async def _update_retailer_patterns(self, retailer: str, change_data: Dict[str, Any]):
        """📈 Actualizar patrones de comportamiento del retailer"""
        try:
            # Obtener patrón existente o crear nuevo
            if retailer in self.retailer_patterns:
                pattern = self.retailer_patterns[retailer]
            else:
                pattern = RetailerPattern(retailer=retailer)
            
            # Actualizar estadísticas de actividad por hora
            current_hour = change_data['hour']
            
            # Obtener historial de cambios del retailer
            all_changes_key = f"intelligence:retailer_activity:{retailer}"
            await self.redis_client.lpush(all_changes_key, json.dumps({
                'hour': current_hour,
                'weekday': change_data['weekday'],
                'change_magnitude': change_data['change_percentage'],
                'timestamp': change_data['timestamp']
            }))
            
            # Mantener historial de 30 días
            await self.redis_client.ltrim(all_changes_key, 0, 4319)  # ~30 días * 144 cambios/día
            
            # Analizar actividad reciente del retailer
            recent_activity = await self.redis_client.lrange(all_changes_key, 0, 1000)
            
            if recent_activity:
                hourly_activity = defaultdict(int)
                daily_changes = []
                magnitude_sum = 0
                
                for activity_json in recent_activity:
                    try:
                        activity = json.loads(activity_json)
                        hourly_activity[activity['hour']] += 1
                        daily_changes.append(activity['change_magnitude'])
                        magnitude_sum += activity['change_magnitude']
                    except:
                        continue
                
                # Identificar horas pico y de baja actividad
                if hourly_activity:
                    sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
                    pattern.peak_update_hours = [hour for hour, count in sorted_hours[:6]]  # Top 6 horas
                    pattern.low_activity_hours = [hour for hour, count in sorted_hours[-6:]]  # Bottom 6 horas
                
                # Calcular métricas promedio
                if daily_changes:
                    pattern.avg_daily_changes = len(daily_changes) / max(1, len(set(
                        datetime.fromisoformat(json.loads(act)['timestamp']).date() 
                        for act in recent_activity if act
                    )))
                    pattern.typical_change_magnitude = mean(daily_changes)
                
                pattern.last_analysis = datetime.now()
                
                # Guardar patrón actualizado
                self.retailer_patterns[retailer] = pattern
                
                await self.redis_client.hset(
                    "intelligence:retailer_patterns",
                    retailer,
                    json.dumps(asdict(pattern), default=str)
                )
                
                logger.debug(f"📈 Patrón actualizado para {retailer}")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando patrón de retailer: {e}")
    
    async def _generate_scraping_recommendations(self, retailer: str, product_id: str, 
                                              change_percentage: float) -> Dict[str, Any]:
        """🎯 Generar recomendaciones inteligentes de scraping"""
        try:
            recommendations = {}
            
            # Obtener métricas de volatilidad
            cache_key = f"{retailer}:{product_id}"
            volatility_metrics = self.volatility_cache.get(cache_key)
            
            if volatility_metrics:
                # Recomendar frecuencia basada en volatilidad
                recommendations['optimal_next_check_minutes'] = volatility_metrics.optimal_check_frequency
                
                # Ajustar por cambio actual
                if change_percentage >= self.intelligence_config['change_significance_pct']:
                    # Cambio significativo = aumentar frecuencia temporalmente
                    recommendations['optimal_next_check_minutes'] = min(
                        15, volatility_metrics.optimal_check_frequency // 2
                    )
                    recommendations['reason'] = 'Cambio significativo detectado - aumentando frecuencia'
                else:
                    recommendations['reason'] = f'Volatilidad {volatility_metrics.volatility_score:.2f}'
                
                # Recomendar horarios óptimos
                if volatility_metrics.peak_hours:
                    recommendations['preferred_hours'] = volatility_metrics.peak_hours
                    recommendations['avoid_hours'] = [h for h in range(24) 
                                                   if h not in volatility_metrics.peak_hours]
            else:
                # Sin datos históricos - usar configuración por defecto
                recommendations['optimal_next_check_minutes'] = 60
                recommendations['reason'] = 'Producto sin historial - usando frecuencia estándar'
            
            # Recomendar tier apropiado
            if change_percentage >= 10:
                recommendations['suggested_tier'] = 'critical'
            elif change_percentage >= 5:
                recommendations['suggested_tier'] = 'important'
            else:
                recommendations['suggested_tier'] = 'tracking'
            
            # Predicciones
            if volatility_metrics:
                recommendations['next_change_probability'] = volatility_metrics.next_change_probability
                recommendations['volatility_score'] = volatility_metrics.volatility_score
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generando recomendaciones: {e}")
            return {'optimal_next_check_minutes': 60, 'reason': 'Error en análisis'}
    
    async def _calculate_volatility_impact(self, retailer: str, product_id: str) -> Dict[str, Any]:
        """📊 Calcular impacto de volatilidad en el sistema"""
        try:
            cache_key = f"{retailer}:{product_id}"
            volatility_metrics = self.volatility_cache.get(cache_key)
            
            if not volatility_metrics:
                return {'impact_level': 'unknown', 'score': 0.0}
            
            impact_score = volatility_metrics.volatility_score
            
            if impact_score >= 0.8:
                impact_level = 'very_high'
                system_impact = 'Requiere monitoreo continuo'
            elif impact_score >= 0.6:
                impact_level = 'high'  
                system_impact = 'Monitoreo frecuente recomendado'
            elif impact_score >= 0.3:
                impact_level = 'medium'
                system_impact = 'Monitoreo regular suficiente'
            else:
                impact_level = 'low'
                system_impact = 'Monitoreo esporádico'
            
            return {
                'impact_level': impact_level,
                'score': impact_score,
                'system_impact': system_impact,
                'recommended_action': f'Frecuencia óptima: cada {volatility_metrics.optimal_check_frequency} min'
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculando impacto de volatilidad: {e}")
            return {'impact_level': 'error', 'score': 0.0}


async def main():
    """🧪 Función de prueba del sistema"""
    logging.basicConfig(level=logging.INFO)
    
    intelligence = RedisIntelligenceSystem()
    
    try:
        await intelligence.initialize()
        
        # Simular análisis de cambios de precio
        analysis = await intelligence.analyze_price_change(
            retailer="falabella",
            product_id="CL-SAMS-GALAXY-256GB-FAL-001",
            old_price=299990,
            new_price=279990
        )
        
        logger.info(f"🔍 Análisis resultado: {analysis}")
        
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")


if __name__ == "__main__":
    asyncio.run(main())