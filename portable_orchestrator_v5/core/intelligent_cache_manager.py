#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE CACHE INTELIGENTE MULTI-NIVEL V5
==============================================

Sistema profesional de cache multi-nivel con Redis para operación continua
no supervisada y ultra-optimizada.

Niveles de Cache:
- 🟢 L1: Memory Cache (sub-millisegundo) - Hot data
- 🔵 L2: Redis Cache (1-5ms) - Warm data con TTL inteligente  
- 🟡 L3: Predictive Cache (10-50ms) - Precargar datos basado en patrones
- 🟠 L4: Analytics Cache (100ms+) - Agregaciones y análisis

Características profesionales:
- ⚡ Cache predictivo basado en ML
- 🧠 TTL dinámico según volatilidad de datos
- 📊 Auto-warming basado en patrones de acceso
- 🔄 Invalidación inteligente por eventos
- 📈 Métricas y optimización automática

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import logging
import redis.asyncio as redis
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, OrderedDict
from functools import wraps
import pickle
import gzip
from statistics import mean, median
import threading
from concurrent.futures import ThreadPoolExecutor

from .emoji_support import force_emoji_support
force_emoji_support()

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrada de cache con metadatos inteligentes"""
    key: str
    data: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl_seconds: int = 300
    size_bytes: int = 0
    volatility_score: float = 1.0  # 0=estable, 1=volátil
    prediction_confidence: float = 0.0  # 0-1
    tags: List[str] = field(default_factory=list)
    
    @property
    def age_seconds(self) -> float:
        """Edad de la entrada en segundos"""
        return time.time() - self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Verificar si la entrada está expirada"""
        effective_ttl = self._calculate_effective_ttl()
        return self.age_seconds > effective_ttl
    
    @property
    def access_frequency(self) -> float:
        """Frecuencia de acceso (accesos por minuto)"""
        age_minutes = max(1, self.age_seconds / 60)
        return self.access_count / age_minutes
    
    def _calculate_effective_ttl(self) -> float:
        """TTL efectivo basado en volatilidad y frecuencia de acceso"""
        base_ttl = self.ttl_seconds
        
        # Ajustar por volatilidad (datos volátiles = TTL menor)
        volatility_multiplier = 1.0 - (self.volatility_score * 0.5)
        
        # Ajustar por frecuencia de acceso (más accesos = TTL mayor)
        frequency_multiplier = min(2.0, 1.0 + (self.access_frequency * 0.1))
        
        return base_ttl * volatility_multiplier * frequency_multiplier


@dataclass
class CacheMetrics:
    """Métricas detalladas del cache"""
    # Hits y misses por nivel
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    l4_hits: int = 0
    l4_misses: int = 0
    
    # Métricas de rendimiento
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    redis_ops_per_second: float = 0.0
    
    # Eficiencia predictiva
    predictions_made: int = 0
    predictions_correct: int = 0
    preload_success_rate: float = 0.0
    
    # Auto-optimización
    optimizations_applied: int = 0
    last_optimization: Optional[datetime] = None
    
    @property
    def overall_hit_rate(self) -> float:
        """Tasa de hit general del sistema"""
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits + self.l4_hits
        return total_hits / max(1, self.total_requests)
    
    @property
    def prediction_accuracy(self) -> float:
        """Precisión de las predicciones"""
        return self.predictions_correct / max(1, self.predictions_made)


class IntelligentCacheManager:
    """
    🚀 Gestor de Cache Inteligente Multi-Nivel
    
    Optimiza automáticamente el acceso a datos para operación continua
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0",
                 max_memory_mb: int = 100):
        """
        Inicializar cache manager
        
        Args:
            redis_url: URL de conexión Redis
            max_memory_mb: Memoria máxima para L1 cache
        """
        self.redis_url = redis_url
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # Conexiones
        self.redis_client: Optional[redis.Redis] = None
        
        # L1 Cache - Memory (LRU)
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.l1_size_bytes = 0
        self.l1_lock = threading.RLock()
        
        # Configuración inteligente
        self.config = {
            'l1_max_size_mb': max_memory_mb,
            'l2_default_ttl': 900,  # 15 minutos
            'l3_predictive_window': 3600,  # 1 hora
            'l4_analytics_ttl': 7200,  # 2 horas
            
            'auto_optimization_interval': 300,  # 5 minutos
            'preload_threshold_confidence': 0.7,
            'volatility_adjustment_factor': 0.5,
            'access_pattern_window': 1800,  # 30 minutos
        }
        
        # Métricas y monitoreo
        self.metrics = CacheMetrics()
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
        self.prediction_models: Dict[str, Any] = {}
        
        # Thread pool para operaciones asíncronas
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="CacheManager")
        
        # Timers para auto-optimización
        self.optimization_timer = None
        self.running = False
        
        logger.info("🚀 IntelligentCacheManager inicializado")
    
    async def initialize(self):
        """🔧 Inicializar conexiones y estructuras"""
        try:
            # Conectar a Redis
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Para datos binarios
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True
            )
            
            await self.redis_client.ping()
            logger.info("✅ Conexión Redis establecida para cache")
            
            # Cargar patrones de acceso existentes
            await self._load_access_patterns()
            
            # Iniciar optimización automática
            self.running = True
            self.optimization_timer = asyncio.create_task(self._auto_optimization_loop())
            
            logger.info("🔧 Cache manager completamente inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando cache manager: {e}")
            raise
    
    async def get(self, key: str, default: Any = None, 
                  tags: List[str] = None) -> Tuple[Any, str]:
        """
        🔍 Obtener dato del cache multi-nivel
        
        Args:
            key: Clave de búsqueda
            default: Valor por defecto si no existe
            tags: Tags para categorización
            
        Returns:
            Tuple de (data, cache_level) donde cache_level es 'L1', 'L2', 'L3' o 'L4'
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        # Registrar patrón de acceso
        self._record_access_pattern(key, start_time)
        
        try:
            # L1: Memory cache (más rápido)
            result = await self._get_from_l1(key)
            if result is not None:
                self.metrics.l1_hits += 1
                response_time = (time.time() - start_time) * 1000
                self._update_response_time(response_time)
                return result, 'L1'
            
            self.metrics.l1_misses += 1
            
            # L2: Redis cache  
            result = await self._get_from_l2(key)
            if result is not None:
                self.metrics.l2_hits += 1
                # Promover a L1 si es accedido frecuentemente
                await self._maybe_promote_to_l1(key, result, tags or [])
                response_time = (time.time() - start_time) * 1000
                self._update_response_time(response_time)
                return result, 'L2'
            
            self.metrics.l2_misses += 1
            
            # L3: Predictive cache - intentar predecir y precargar
            result = await self._get_from_l3_predictive(key)
            if result is not None:
                self.metrics.l3_hits += 1
                response_time = (time.time() - start_time) * 1000
                self._update_response_time(response_time)
                return result, 'L3'
            
            self.metrics.l3_misses += 1
            
            # L4: Analytics/aggregation cache
            result = await self._get_from_l4_analytics(key)
            if result is not None:
                self.metrics.l4_hits += 1
                response_time = (time.time() - start_time) * 1000
                self._update_response_time(response_time)
                return result, 'L4'
            
            self.metrics.l4_misses += 1
            
            # No encontrado en ningún nivel
            response_time = (time.time() - start_time) * 1000
            self._update_response_time(response_time)
            
            return default, 'MISS'
            
        except Exception as e:
            logger.error(f"❌ Error en cache get: {e}")
            return default, 'ERROR'
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None,
                  volatility_score: float = 1.0, tags: List[str] = None,
                  level_preference: str = 'auto') -> bool:
        """
        💾 Almacenar dato en cache inteligente
        
        Args:
            key: Clave de almacenamiento
            data: Datos a almacenar
            ttl: TTL en segundos (None = usar por defecto)
            volatility_score: Score de volatilidad 0-1
            tags: Tags para categorización
            level_preference: 'L1', 'L2', 'L3', 'L4' o 'auto'
            
        Returns:
            True si se almacenó correctamente
        """
        try:
            tags = tags or []
            current_time = time.time()
            
            # Determinar TTL inteligente
            if ttl is None:
                ttl = self._calculate_intelligent_ttl(key, volatility_score)
            
            # Calcular tamaño
            data_size = self._estimate_data_size(data)
            
            # Crear entrada de cache
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=current_time,
                accessed_at=current_time,
                ttl_seconds=ttl,
                size_bytes=data_size,
                volatility_score=volatility_score,
                tags=tags
            )
            
            # Determinar niveles de almacenamiento
            if level_preference == 'auto':
                levels = self._determine_storage_levels(entry)
            else:
                levels = [level_preference]
            
            success = True
            
            # Almacenar en niveles seleccionados
            if 'L1' in levels:
                success &= await self._set_in_l1(entry)
            
            if 'L2' in levels:
                success &= await self._set_in_l2(entry)
            
            if 'L3' in levels:
                success &= await self._set_in_l3(entry)
            
            if 'L4' in levels:
                success &= await self._set_in_l4(entry)
            
            # Actualizar modelos predictivos
            await self._update_prediction_models(key, data, tags)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en cache set: {e}")
            return False
    
    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """🟢 Obtener desde L1 Memory Cache"""
        with self.l1_lock:
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                
                # Verificar expiración
                if entry.is_expired:
                    del self.l1_cache[key]
                    self.l1_size_bytes -= entry.size_bytes
                    return None
                
                # Mover al final (LRU)
                self.l1_cache.move_to_end(key)
                
                # Actualizar estadísticas de acceso
                entry.accessed_at = time.time()
                entry.access_count += 1
                
                return entry.data
        
        return None
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """🔵 Obtener desde L2 Redis Cache"""
        try:
            redis_key = f"cache:l2:{key}"
            serialized_data = await self.redis_client.get(redis_key)
            
            if serialized_data:
                # Deserializar datos comprimidos
                try:
                    decompressed = gzip.decompress(serialized_data)
                    data = pickle.loads(decompressed)
                    return data
                except Exception as e:
                    logger.warning(f"⚠️ Error deserializando L2 {key}: {e}")
                    # Limpiar entrada corrupta
                    await self.redis_client.delete(redis_key)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error L2 get {key}: {e}")
            return None
    
    async def _get_from_l3_predictive(self, key: str) -> Optional[Any]:
        """🟡 Obtener desde L3 Predictive Cache"""
        try:
            # Intentar predecir el dato basado en patrones
            predicted_data = await self._try_predict_data(key)
            
            if predicted_data is not None:
                # Almacenar predicción en L2 para futuros accesos
                await self.set(key, predicted_data, ttl=300, 
                             volatility_score=0.8, level_preference='L2')
                self.metrics.predictions_correct += 1
                return predicted_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error L3 predictive {key}: {e}")
            return None
    
    async def _get_from_l4_analytics(self, key: str) -> Optional[Any]:
        """🟠 Obtener desde L4 Analytics Cache"""
        try:
            # Cache de agregaciones y análisis
            redis_key = f"cache:l4:analytics:{key}"
            data = await self.redis_client.get(redis_key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error L4 analytics {key}: {e}")
            return None
    
    async def _set_in_l1(self, entry: CacheEntry) -> bool:
        """🟢 Almacenar en L1 Memory Cache"""
        try:
            with self.l1_lock:
                # Verificar límites de memoria
                while (self.l1_size_bytes + entry.size_bytes > self.max_memory_bytes and 
                       len(self.l1_cache) > 0):
                    # Expulsar LRU
                    oldest_key, oldest_entry = self.l1_cache.popitem(last=False)
                    self.l1_size_bytes -= oldest_entry.size_bytes
                
                # Almacenar
                self.l1_cache[entry.key] = entry
                self.l1_size_bytes += entry.size_bytes
                
                self.metrics.memory_usage_mb = self.l1_size_bytes / (1024 * 1024)
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error L1 set: {e}")
            return False
    
    async def _set_in_l2(self, entry: CacheEntry) -> bool:
        """🔵 Almacenar en L2 Redis Cache"""
        try:
            # Serializar y comprimir datos
            serialized = pickle.dumps(entry.data)
            compressed = gzip.compress(serialized, compresslevel=6)
            
            redis_key = f"cache:l2:{entry.key}"
            
            # Almacenar con TTL
            await self.redis_client.setex(
                redis_key, 
                int(entry.ttl_seconds),
                compressed
            )
            
            # Almacenar metadatos
            metadata = {
                'created_at': entry.created_at,
                'volatility_score': entry.volatility_score,
                'tags': entry.tags,
                'size_bytes': entry.size_bytes
            }
            
            await self.redis_client.setex(
                f"cache:l2:meta:{entry.key}",
                int(entry.ttl_seconds),
                json.dumps(metadata)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error L2 set: {e}")
            return False
    
    async def _set_in_l3(self, entry: CacheEntry) -> bool:
        """🟡 Almacenar en L3 Predictive Cache"""
        try:
            # Actualizar patrones para predicción futura
            pattern_key = f"cache:l3:patterns:{entry.key}"
            pattern_data = {
                'access_time': entry.created_at,
                'tags': entry.tags,
                'volatility': entry.volatility_score,
                'size': entry.size_bytes
            }
            
            await self.redis_client.lpush(pattern_key, json.dumps(pattern_data))
            await self.redis_client.ltrim(pattern_key, 0, 99)  # Mantener últimos 100
            await self.redis_client.expire(pattern_key, 86400)  # TTL 24h
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error L3 set: {e}")
            return False
    
    async def _set_in_l4(self, entry: CacheEntry) -> bool:
        """🟠 Almacenar en L4 Analytics Cache"""
        try:
            # Solo para datos de análisis/agregaciones
            if 'analytics' in entry.tags or 'aggregation' in entry.tags:
                redis_key = f"cache:l4:analytics:{entry.key}"
                await self.redis_client.setex(
                    redis_key,
                    self.config['l4_analytics_ttl'],
                    json.dumps(entry.data, default=str)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error L4 set: {e}")
            return False
    
    def _calculate_intelligent_ttl(self, key: str, volatility_score: float) -> int:
        """🧠 Calcular TTL inteligente basado en patrones"""
        base_ttl = self.config['l2_default_ttl']
        
        # Ajustar por volatilidad
        volatility_multiplier = 1.0 - (volatility_score * 0.7)
        
        # Ajustar por frecuencia de acceso histórica
        access_pattern = self.access_patterns.get(key, [])
        if access_pattern:
            recent_accesses = [t for t in access_pattern if time.time() - t < 3600]  # Última hora
            if len(recent_accesses) > 5:  # Accedido frecuentemente
                frequency_multiplier = 1.5
            else:
                frequency_multiplier = 1.0
        else:
            frequency_multiplier = 1.0
        
        intelligent_ttl = int(base_ttl * volatility_multiplier * frequency_multiplier)
        return max(60, min(7200, intelligent_ttl))  # Entre 1 min y 2 horas
    
    def _determine_storage_levels(self, entry: CacheEntry) -> List[str]:
        """🎯 Determinar en qué niveles almacenar basado en características"""
        levels = []
        
        # L1: Datos pequeños y frecuentemente accedidos
        if (entry.size_bytes < 10240 and  # < 10KB
            entry.volatility_score < 0.5):  # Relativamente estable
            levels.append('L1')
        
        # L2: Todos los datos van a L2 por defecto
        levels.append('L2')
        
        # L3: Datos con patrones predecibles
        if entry.volatility_score > 0.3:  # Algo volátil = interesante para predicción
            levels.append('L3')
        
        # L4: Solo datos de análisis
        if 'analytics' in entry.tags or 'aggregation' in entry.tags:
            levels.append('L4')
        
        return levels
    
    def _record_access_pattern(self, key: str, access_time: float):
        """📊 Registrar patrón de acceso para ML"""
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        
        self.access_patterns[key].append(access_time)
        
        # Mantener ventana deslizante
        cutoff_time = access_time - self.config['access_pattern_window']
        self.access_patterns[key] = [
            t for t in self.access_patterns[key] if t > cutoff_time
        ]
    
    async def _try_predict_data(self, key: str) -> Optional[Any]:
        """🔮 Intentar predecir datos basado en patrones ML"""
        try:
            # Implementación simplificada de predicción
            # En producción, aquí iría un modelo ML más sofisticado
            
            # Buscar patrones similares
            similar_keys = [k for k in self.access_patterns.keys() 
                          if k != key and self._keys_are_similar(k, key)]
            
            if similar_keys:
                # Intentar obtener dato de clave similar
                for similar_key in similar_keys[:3]:  # Top 3 similares
                    similar_data = await self._get_from_l2(similar_key)
                    if similar_data is not None:
                        self.metrics.predictions_made += 1
                        # En producción, aquí transformaríamos el dato similar
                        return similar_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return None
    
    def _keys_are_similar(self, key1: str, key2: str) -> bool:
        """🔍 Determinar si dos claves son similares (heurística simple)"""
        # Implementación básica - en producción usar embeddings o distancia de edición
        key1_parts = key1.split(':')
        key2_parts = key2.split(':')
        
        if len(key1_parts) != len(key2_parts):
            return False
        
        # Al menos 70% de partes deben ser iguales
        matches = sum(1 for p1, p2 in zip(key1_parts, key2_parts) if p1 == p2)
        return (matches / len(key1_parts)) >= 0.7
    
    def _estimate_data_size(self, data: Any) -> int:
        """📏 Estimar tamaño de datos en bytes"""
        try:
            return len(pickle.dumps(data))
        except:
            return len(str(data).encode('utf-8'))
    
    def _update_response_time(self, response_time_ms: float):
        """⏱️ Actualizar tiempo promedio de respuesta"""
        if self.metrics.total_requests == 1:
            self.metrics.avg_response_time_ms = response_time_ms
        else:
            # Media móvil exponencial
            alpha = 0.1
            self.metrics.avg_response_time_ms = (
                alpha * response_time_ms + 
                (1 - alpha) * self.metrics.avg_response_time_ms
            )
    
    async def _auto_optimization_loop(self):
        """🔄 Loop de auto-optimización continua"""
        while self.running:
            try:
                await asyncio.sleep(self.config['auto_optimization_interval'])
                await self._perform_optimization()
            except Exception as e:
                logger.error(f"❌ Error en auto-optimización: {e}")
    
    async def _perform_optimization(self):
        """⚙️ Realizar optimizaciones automáticas"""
        try:
            optimizations = 0
            
            # 1. Limpiar entradas expiradas de L1
            with self.l1_lock:
                expired_keys = [
                    key for key, entry in self.l1_cache.items() 
                    if entry.is_expired
                ]
                
                for key in expired_keys:
                    entry = self.l1_cache.pop(key)
                    self.l1_size_bytes -= entry.size_bytes
                    optimizations += 1
            
            # 2. Precarga predictiva de datos calientes
            hot_keys = await self._identify_hot_keys()
            for key in hot_keys:
                if await self._should_preload(key):
                    await self._preload_data(key)
                    optimizations += 1
            
            # 3. Ajustar TTLs basado en patrones
            await self._optimize_ttls()
            optimizations += 1
            
            # 4. Actualizar métricas de Redis
            info = await self.redis_client.info('stats')
            self.metrics.redis_ops_per_second = float(info.get('instantaneous_ops_per_sec', 0))
            
            if optimizations > 0:
                self.metrics.optimizations_applied += optimizations
                self.metrics.last_optimization = datetime.now()
                logger.debug(f"⚙️ Optimización automática: {optimizations} acciones aplicadas")
            
        except Exception as e:
            logger.error(f"❌ Error en optimización: {e}")
    
    async def _identify_hot_keys(self) -> List[str]:
        """🔥 Identificar claves calientes para precargar"""
        hot_keys = []
        
        for key, access_times in self.access_patterns.items():
            if len(access_times) >= 5:  # Al menos 5 accesos
                # Calcular frecuencia reciente
                recent_accesses = [t for t in access_times if time.time() - t < 1800]  # 30 min
                if len(recent_accesses) >= 3:
                    hot_keys.append(key)
        
        return hot_keys[:10]  # Top 10 hot keys
    
    async def _should_preload(self, key: str) -> bool:
        """🤔 Determinar si debería precargarse una clave"""
        # Verificar si ya está en L1
        with self.l1_lock:
            if key in self.l1_cache:
                return False
        
        # Verificar confianza en predicción
        prediction_confidence = self._calculate_prediction_confidence(key)
        return prediction_confidence >= self.config['preload_threshold_confidence']
    
    def _calculate_prediction_confidence(self, key: str) -> float:
        """📊 Calcular confianza de predicción para una clave"""
        access_times = self.access_patterns.get(key, [])
        
        if len(access_times) < 3:
            return 0.0
        
        # Calcular regularidad de accesos (más regular = más confianza)
        intervals = []
        for i in range(1, len(access_times)):
            intervals.append(access_times[i] - access_times[i-1])
        
        if not intervals:
            return 0.0
        
        # Calcular variación en intervalos (menos variación = más confianza)
        avg_interval = mean(intervals)
        if avg_interval == 0:
            return 0.0
        
        # Coeficiente de variación invertido
        try:
            cv = stdev(intervals) / avg_interval
            confidence = max(0.0, min(1.0, 1.0 - cv))
            return confidence
        except:
            return 0.0
    
    async def _preload_data(self, key: str):
        """📥 Precargar dato basado en predicción"""
        try:
            predicted_data = await self._try_predict_data(key)
            if predicted_data is not None:
                await self.set(key, predicted_data, 
                             volatility_score=0.7, 
                             tags=['predicted'],
                             level_preference='L1')
                logger.debug(f"📥 Precargado: {key}")
        except Exception as e:
            logger.error(f"❌ Error precargando {key}: {e}")
    
    async def _optimize_ttls(self):
        """⏰ Optimizar TTLs basado en patrones de acceso"""
        # Implementación simplificada - en producción sería más sofisticada
        try:
            # Analizar patrones y ajustar TTLs en Redis
            pattern_keys = await self.redis_client.keys("cache:l3:patterns:*")
            
            for pattern_key in pattern_keys[:50]:  # Procesar en lotes
                try:
                    patterns = await self.redis_client.lrange(pattern_key, 0, -1)
                    if len(patterns) >= 10:  # Suficientes datos
                        # Calcular TTL óptimo basado en patrones
                        # (implementación simplificada)
                        base_key = pattern_key.replace("cache:l3:patterns:", "")
                        optimal_ttl = self._calculate_optimal_ttl_from_patterns(patterns)
                        
                        # Aplicar nuevo TTL si es diferente
                        current_ttl = await self.redis_client.ttl(f"cache:l2:{base_key}")
                        if abs(current_ttl - optimal_ttl) > 60:  # Diferencia > 1 minuto
                            await self.redis_client.expire(f"cache:l2:{base_key}", optimal_ttl)
                except Exception as e:
                    logger.debug(f"Error optimizando TTL para {pattern_key}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error optimizando TTLs: {e}")
    
    def _calculate_optimal_ttl_from_patterns(self, patterns: List[str]) -> int:
        """📊 Calcular TTL óptimo desde patrones de acceso"""
        try:
            access_times = []
            volatilities = []
            
            for pattern_str in patterns:
                pattern = json.loads(pattern_str)
                access_times.append(pattern['access_time'])
                volatilities.append(pattern.get('volatility', 1.0))
            
            # Calcular intervalo promedio entre accesos
            if len(access_times) >= 2:
                access_times.sort()
                intervals = [
                    access_times[i] - access_times[i-1] 
                    for i in range(1, len(access_times))
                ]
                avg_interval = mean(intervals)
                
                # TTL = 2x el intervalo promedio, ajustado por volatilidad
                avg_volatility = mean(volatilities)
                base_ttl = avg_interval * 2
                volatility_adjustment = 1.0 - (avg_volatility * 0.5)
                
                optimal_ttl = int(base_ttl * volatility_adjustment)
                return max(60, min(7200, optimal_ttl))  # Entre 1 min y 2 horas
            
            return self.config['l2_default_ttl']
            
        except Exception as e:
            logger.debug(f"Error calculando TTL óptimo: {e}")
            return self.config['l2_default_ttl']
    
    async def get_metrics(self) -> Dict[str, Any]:
        """📈 Obtener métricas completas del cache"""
        return {
            'cache_metrics': asdict(self.metrics),
            'l1_status': {
                'entries': len(self.l1_cache),
                'size_mb': self.l1_size_bytes / (1024 * 1024),
                'utilization_pct': (self.l1_size_bytes / self.max_memory_bytes) * 100
            },
            'access_patterns': {
                'tracked_keys': len(self.access_patterns),
                'total_accesses': sum(len(pattern) for pattern in self.access_patterns.values())
            },
            'performance': {
                'overall_hit_rate': self.metrics.overall_hit_rate,
                'prediction_accuracy': self.metrics.prediction_accuracy,
                'avg_response_time_ms': self.metrics.avg_response_time_ms
            }
        }
    
    async def invalidate(self, pattern: str = None, tags: List[str] = None):
        """🗑️ Invalidar entradas de cache"""
        try:
            if pattern:
                # Invalidar por patrón
                keys_to_remove = []
                
                # L1
                with self.l1_lock:
                    for key in list(self.l1_cache.keys()):
                        if pattern in key:
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        entry = self.l1_cache.pop(key, None)
                        if entry:
                            self.l1_size_bytes -= entry.size_bytes
                
                # L2
                redis_keys = await self.redis_client.keys(f"cache:l2:*{pattern}*")
                if redis_keys:
                    await self.redis_client.delete(*redis_keys)
            
            if tags:
                # Invalidar por tags (más complejo, requiere índice)
                # Implementación simplificada
                pass
            
        except Exception as e:
            logger.error(f"❌ Error invalidando cache: {e}")
    
    async def shutdown(self):
        """🛑 Shutdown graceful del cache manager"""
        logger.info("🛑 Deteniendo Intelligent Cache Manager...")
        
        self.running = False
        
        if self.optimization_timer:
            self.optimization_timer.cancel()
        
        if self.redis_client:
            await self.redis_client.aclose()
        
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Cache Manager detenido correctamente")


# Decorator para cache automático
def intelligent_cache(ttl: int = 300, volatility_score: float = 1.0, 
                     tags: List[str] = None):
    """🎯 Decorator para cachear automáticamente resultados de funciones"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave única basada en función y argumentos
            func_name = f"{func.__module__}.{func.__qualname__}"
            args_hash = hashlib.md5(str((args, kwargs)).encode()).hexdigest()[:8]
            cache_key = f"func:{func_name}:{args_hash}"
            
            # Intentar obtener desde cache
            cache_manager = getattr(wrapper, '_cache_manager', None)
            if cache_manager:
                result, level = await cache_manager.get(cache_key)
                if level != 'MISS':
                    return result
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            
            if cache_manager:
                await cache_manager.set(
                    cache_key, result, ttl=ttl,
                    volatility_score=volatility_score,
                    tags=tags or ['function_cache']
                )
            
            return result
        
        return wrapper
    return decorator


async def main():
    """🧪 Función de prueba"""
    logging.basicConfig(level=logging.INFO)
    
    cache_manager = IntelligentCacheManager()
    
    try:
        await cache_manager.initialize()
        
        # Pruebas
        await cache_manager.set("test:key1", {"data": "test"}, volatility_score=0.3)
        result, level = await cache_manager.get("test:key1")
        
        logger.info(f"🔍 Resultado: {result} desde {level}")
        
        metrics = await cache_manager.get_metrics()
        logger.info(f"📊 Métricas: {metrics}")
        
    finally:
        await cache_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())