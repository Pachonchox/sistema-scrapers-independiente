# -*- coding: utf-8 -*-
"""
🌐 Intelligent Proxy Manager - Sistema de Gestión Inteligente de Proxies
========================================================================

Manager de proxies con ML que optimiza automáticamente la rotación,
detecta proxies problemáticos y selecciona los mejores para cada retailer.

Funcionalidades:
- Rotación inteligente basada en performance
- Detección automática de proxies bloqueados
- Optimización por retailer y categoría
- Health checks automatizados
- Geolocalización y latencia optimizada
- Backup de proxies de emergencia
- Estadísticas detalladas de uso

Autor: Sistema Scraper v5 🚀
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse
import hashlib

import aiohttp
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import numpy as np
import pandas as pd


@dataclass
class ProxyMetrics:
    """📊 Métricas de rendimiento de proxy"""
    proxy_id: str
    host: str
    port: int
    protocol: str
    country: str
    success_rate: float
    avg_response_time: float
    total_requests: int
    successful_requests: int
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    retailer_performance: Dict[str, float]
    failure_reasons: List[str]
    blocked_by: Set[str]
    health_score: float
    cost_per_request: float
    concurrent_capacity: int
    uptime_percentage: float


@dataclass
class ProxyProvider:
    """🏢 Proveedor de proxies"""
    provider_id: str
    name: str
    api_endpoint: str
    auth_token: str
    proxy_type: str  # 'residential', 'datacenter', 'mobile'
    rotation_interval: int  # seconds
    concurrent_limit: int
    cost_per_gb: float
    countries_available: List[str]
    protocols_supported: List[str]
    reliability_score: float
    is_active: bool


@dataclass
class ScrapingSession:
    """🎯 Sesión de scraping con proxy asignado"""
    session_id: str
    retailer: str
    proxy_id: str
    start_time: datetime
    requests_made: int
    success_count: int
    avg_response_time: float
    data_transferred: float
    is_active: bool
    failure_reasons: List[str]


class IntelligentProxyManager:
    """🧠 Manager Inteligente de Proxies - El Estratega de la Red"""
    
    def __init__(self, config_path: str = "./scraper_v5/config/proxy_config.json"):
        self.config_path = Path(config_path)
        self.storage_path = Path("./scraper_v5/data/proxy_management")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Paths específicos
        self.metrics_path = self.storage_path / "proxy_metrics.json"
        self.sessions_path = self.storage_path / "sessions.json"
        self.models_path = self.storage_path / "models"
        self.providers_path = self.storage_path / "providers.json"
        
        self.models_path.mkdir(exist_ok=True)
        
        # Estado del manager
        self.proxy_metrics: Dict[str, ProxyMetrics] = {}
        self.proxy_providers: Dict[str, ProxyProvider] = {}
        self.active_sessions: Dict[str, ScrapingSession] = {}
        self.proxy_pool: List[str] = []
        self.blocked_proxies: Dict[str, Set[str]] = {}  # proxy_id -> retailers que lo bloquearon
        
        # Modelos ML
        self.performance_predictor: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        
        # Configuración
        self.max_concurrent_per_proxy = 5
        self.max_failures_before_quarantine = 3
        self.quarantine_duration_hours = 24
        self.min_success_rate = 0.7
        self.health_check_interval = 300  # 5 minutos
        self.rotation_strategy = "intelligent"  # 'round_robin', 'random', 'intelligent'
        
        # Retailers chilenos y sus características
        self.retailer_configs = {
            'ripley': {
                'preferred_countries': ['CL', 'PE', 'CO'],
                'max_requests_per_minute': 30,
                'requires_residential': False,
                'strict_geo_targeting': True
            },
            'falabella': {
                'preferred_countries': ['CL', 'PE', 'CO', 'AR'],
                'max_requests_per_minute': 25,
                'requires_residential': True,
                'strict_geo_targeting': True
            },
            'paris': {
                'preferred_countries': ['CL'],
                'max_requests_per_minute': 20,
                'requires_residential': False,
                'strict_geo_targeting': True
            },
            'hites': {
                'preferred_countries': ['CL'],
                'max_requests_per_minute': 40,
                'requires_residential': False,
                'strict_geo_targeting': False
            },
            'abcdin': {
                'preferred_countries': ['CL'],
                'max_requests_per_minute': 35,
                'requires_residential': False,
                'strict_geo_targeting': False
            },
            'mercadolibre': {
                'preferred_countries': ['CL', 'AR', 'PE', 'CO'],
                'max_requests_per_minute': 15,
                'requires_residential': True,
                'strict_geo_targeting': True
            }
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        self._init_logger()
        
        # Cargar datos existentes
        self._load_configuration()
        self._load_metrics()
        self._load_models()
        
        # Iniciar health checks
        self._health_check_task = None
        
        self.logger.info("🌐 Intelligent Proxy Manager inicializado correctamente")

    def _init_logger(self) -> None:
        """🔧 Inicializar sistema de logging"""
        log_path = self.storage_path / "proxy_manager.log"
        
        handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _load_configuration(self) -> None:
        """📥 Cargar configuración de proxies"""
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Cargar proveedores
                for provider_data in config.get('providers', []):
                    provider = ProxyProvider(**provider_data)
                    self.proxy_providers[provider.provider_id] = provider
                
                # Cargar configuraciones
                self.max_concurrent_per_proxy = config.get('max_concurrent_per_proxy', 5)
                self.rotation_strategy = config.get('rotation_strategy', 'intelligent')
                self.min_success_rate = config.get('min_success_rate', 0.7)
                
                self.logger.info(f"✅ Configuración cargada: {len(self.proxy_providers)} proveedores")
            else:
                # Crear configuración por defecto
                self._create_default_configuration()
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración: {e}")
            self._create_default_configuration()

    def _create_default_configuration(self) -> None:
        """🔧 Crear configuración por defecto"""
        
        default_config = {
            "providers": [
                {
                    "provider_id": "brightdata",
                    "name": "Bright Data",
                    "api_endpoint": "https://brd-customer-hl_username-zone-datacenter_proxy1:password@brd.superproxy.io:22225",
                    "auth_token": "",
                    "proxy_type": "datacenter",
                    "rotation_interval": 600,
                    "concurrent_limit": 100,
                    "cost_per_gb": 15.0,
                    "countries_available": ["CL", "US", "DE", "SG"],
                    "protocols_supported": ["http", "https"],
                    "reliability_score": 0.95,
                    "is_active": False
                },
                {
                    "provider_id": "smartproxy",
                    "name": "SmartProxy",
                    "api_endpoint": "http://user:pass@gate.smartproxy.com:7000",
                    "auth_token": "",
                    "proxy_type": "residential",
                    "rotation_interval": 300,
                    "concurrent_limit": 50,
                    "cost_per_gb": 12.5,
                    "countries_available": ["CL", "PE", "CO", "AR"],
                    "protocols_supported": ["http", "https"],
                    "reliability_score": 0.90,
                    "is_active": False
                },
                {
                    "provider_id": "local_test",
                    "name": "Local Test Proxy",
                    "api_endpoint": "http://127.0.0.1:8888",
                    "auth_token": "",
                    "proxy_type": "datacenter",
                    "rotation_interval": 60,
                    "concurrent_limit": 10,
                    "cost_per_gb": 0.0,
                    "countries_available": ["CL"],
                    "protocols_supported": ["http", "https"],
                    "reliability_score": 0.5,
                    "is_active": True
                }
            ],
            "max_concurrent_per_proxy": 5,
            "rotation_strategy": "intelligent",
            "min_success_rate": 0.7,
            "health_check_interval": 300
        }
        
        # Crear directorio de configuración
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        # Cargar proveedores por defecto
        for provider_data in default_config['providers']:
            provider = ProxyProvider(**provider_data)
            self.proxy_providers[provider.provider_id] = provider
        
        self.logger.info("🔧 Configuración por defecto creada")

    def _load_metrics(self) -> None:
        """📊 Cargar métricas de proxies existentes"""
        
        try:
            if self.metrics_path.exists():
                with open(self.metrics_path, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                
                for proxy_id, metrics_dict in metrics_data.items():
                    # Convertir timestamps
                    if metrics_dict.get('last_success'):
                        metrics_dict['last_success'] = datetime.fromisoformat(metrics_dict['last_success'])
                    if metrics_dict.get('last_failure'):
                        metrics_dict['last_failure'] = datetime.fromisoformat(metrics_dict['last_failure'])
                    
                    # Convertir sets
                    if 'blocked_by' in metrics_dict:
                        metrics_dict['blocked_by'] = set(metrics_dict['blocked_by'])
                    else:
                        metrics_dict['blocked_by'] = set()
                    
                    self.proxy_metrics[proxy_id] = ProxyMetrics(**metrics_dict)
                
                self.logger.info(f"📊 Métricas cargadas para {len(self.proxy_metrics)} proxies")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando métricas: {e}")

    def _save_metrics(self) -> None:
        """💾 Guardar métricas de proxies"""
        
        try:
            metrics_dict = {}
            
            for proxy_id, metrics in self.proxy_metrics.items():
                metrics_data = asdict(metrics)
                
                # Convertir datetime a string
                if metrics_data.get('last_success'):
                    metrics_data['last_success'] = metrics.last_success.isoformat()
                if metrics_data.get('last_failure'):
                    metrics_data['last_failure'] = metrics.last_failure.isoformat()
                
                # Convertir set a list
                metrics_data['blocked_by'] = list(metrics.blocked_by)
                
                metrics_dict[proxy_id] = metrics_data
            
            with open(self.metrics_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"💾 Métricas guardadas para {len(metrics_dict)} proxies")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando métricas: {e}")

    def _load_models(self) -> None:
        """🤖 Cargar modelos ML entrenados"""
        
        try:
            predictor_path = self.models_path / "performance_predictor.joblib"
            scaler_path = self.models_path / "feature_scaler.joblib"
            
            if predictor_path.exists():
                self.performance_predictor = joblib.load(predictor_path)
                self.logger.info("✅ Predictor de performance cargado")
            
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                self.logger.info("✅ Escalador de características cargado")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando modelos ML: {e}")

    def _save_models(self) -> None:
        """💾 Guardar modelos ML entrenados"""
        
        try:
            if self.performance_predictor:
                joblib.dump(self.performance_predictor, self.models_path / "performance_predictor.joblib")
            
            if self.scaler:
                joblib.dump(self.scaler, self.models_path / "feature_scaler.joblib")
            
            self.logger.info("✅ Modelos ML guardados")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando modelos ML: {e}")

    async def get_optimal_proxy(
        self, 
        retailer: str,
        category: str = "default",
        priority: str = "medium"
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """🎯 Obtener proxy óptimo para retailer específico"""
        
        try:
            # Filtrar proxies disponibles
            available_proxies = self._get_available_proxies(retailer)
            
            if not available_proxies:
                self.logger.warning(f"⚠️ No hay proxies disponibles para {retailer}")
                return None
            
            # Seleccionar según estrategia
            if self.rotation_strategy == "intelligent":
                proxy_id = await self._intelligent_selection(available_proxies, retailer, category, priority)
            elif self.rotation_strategy == "random":
                proxy_id = random.choice(available_proxies)
            else:  # round_robin
                proxy_id = self._round_robin_selection(available_proxies, retailer)
            
            if not proxy_id:
                return None
            
            # Obtener configuración del proxy
            proxy_config = await self._get_proxy_configuration(proxy_id)
            
            if proxy_config:
                # Registrar asignación
                await self._register_proxy_assignment(proxy_id, retailer, category)
                
                self.logger.info(f"🎯 Proxy {proxy_id} asignado a {retailer}")
                return proxy_id, proxy_config
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo proxy para {retailer}: {e}")
            return None

    def _get_available_proxies(self, retailer: str) -> List[str]:
        """📋 Obtener lista de proxies disponibles para retailer"""
        
        available = []
        retailer_config = self.retailer_configs.get(retailer, {})
        
        for proxy_id, metrics in self.proxy_metrics.items():
            # Verificar si está bloqueado por este retailer
            if retailer in metrics.blocked_by:
                continue
            
            # Verificar tasa de éxito mínima
            if metrics.success_rate < self.min_success_rate:
                continue
            
            # Verificar failures consecutivos
            if metrics.consecutive_failures >= self.max_failures_before_quarantine:
                continue
            
            # Verificar capacidad concurrente
            active_sessions_count = sum(1 for session in self.active_sessions.values() 
                                     if session.proxy_id == proxy_id and session.is_active)
            
            if active_sessions_count >= metrics.concurrent_capacity:
                continue
            
            # Verificar requisitos específicos del retailer
            if retailer_config.get('requires_residential', False):
                provider = self._get_provider_for_proxy(proxy_id)
                if provider and provider.proxy_type != 'residential':
                    continue
            
            # Verificar geo-targeting
            if retailer_config.get('strict_geo_targeting', False):
                preferred_countries = retailer_config.get('preferred_countries', ['CL'])
                if metrics.country not in preferred_countries:
                    continue
            
            available.append(proxy_id)
        
        return available

    async def _intelligent_selection(
        self, 
        available_proxies: List[str],
        retailer: str,
        category: str,
        priority: str
    ) -> Optional[str]:
        """🧠 Selección inteligente basada en ML y heurísticas"""
        
        if not available_proxies:
            return None
        
        # Si solo hay uno disponible
        if len(available_proxies) == 1:
            return available_proxies[0]
        
        # Calcular scores para cada proxy
        proxy_scores = {}
        
        for proxy_id in available_proxies:
            metrics = self.proxy_metrics[proxy_id]
            
            # Score base (performance histórica)
            base_score = self._calculate_base_score(metrics, retailer)
            
            # ML prediction si está disponible
            ml_score = 0.0
            if self.performance_predictor and self.scaler:
                ml_score = await self._predict_performance(proxy_id, retailer, category)
            
            # Factores adicionales
            recency_score = self._calculate_recency_score(metrics)
            load_score = self._calculate_load_score(proxy_id)
            geo_score = self._calculate_geo_score(metrics, retailer)
            
            # Score final ponderado
            final_score = (
                base_score * 0.4 +
                ml_score * 0.3 +
                recency_score * 0.15 +
                load_score * 0.1 +
                geo_score * 0.05
            )
            
            proxy_scores[proxy_id] = final_score
        
        # Seleccionar el mejor, con algo de aleatoriedad para evitar overuse
        sorted_proxies = sorted(proxy_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Top 3 proxies con probabilidades ponderadas
        top_proxies = sorted_proxies[:3]
        weights = [0.6, 0.3, 0.1]  # Mayor probabilidad al mejor
        
        if len(top_proxies) < 3:
            weights = weights[:len(top_proxies)]
            weights = [w/sum(weights) for w in weights]  # Renormalizar
        
        selected_proxy = random.choices(
            [proxy[0] for proxy in top_proxies],
            weights=weights
        )[0]
        
        return selected_proxy

    def _calculate_base_score(self, metrics: ProxyMetrics, retailer: str) -> float:
        """📊 Calcular score base del proxy"""
        
        # Score basado en performance específica del retailer
        retailer_performance = metrics.retailer_performance.get(retailer, metrics.success_rate)
        
        # Penalizar por failures recientes
        failure_penalty = min(metrics.consecutive_failures * 0.1, 0.5)
        
        # Bonus por uptime
        uptime_bonus = metrics.uptime_percentage * 0.2
        
        # Penalizar por latencia alta
        latency_penalty = min(metrics.avg_response_time / 10.0, 0.3)
        
        base_score = (
            retailer_performance + 
            uptime_bonus - 
            failure_penalty - 
            latency_penalty
        )
        
        return max(0.0, min(1.0, base_score))

    async def _predict_performance(self, proxy_id: str, retailer: str, category: str) -> float:
        """🔮 Predecir performance usando ML"""
        
        try:
            # Extraer características para predicción
            features = self._extract_prediction_features(proxy_id, retailer, category)
            
            if features is None:
                return 0.5  # Score neutral si no se pueden extraer características
            
            # Escalar características
            features_scaled = self.scaler.transform([features])
            
            # Predecir
            prediction = self.performance_predictor.predict(features_scaled)[0]
            
            # Normalizar a [0, 1]
            return max(0.0, min(1.0, prediction))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en predicción ML para {proxy_id}: {e}")
            return 0.5

    def _extract_prediction_features(self, proxy_id: str, retailer: str, category: str) -> Optional[np.ndarray]:
        """🔧 Extraer características para predicción ML"""
        
        try:
            metrics = self.proxy_metrics.get(proxy_id)
            if not metrics:
                return None
            
            # Características del proxy
            features = [
                metrics.success_rate,
                metrics.avg_response_time,
                metrics.total_requests,
                metrics.consecutive_failures,
                metrics.health_score,
                metrics.uptime_percentage,
                metrics.concurrent_capacity
            ]
            
            # Características del retailer (encoding one-hot simplificado)
            retailer_features = [0] * len(self.retailer_configs)
            if retailer in self.retailer_configs:
                retailer_idx = list(self.retailer_configs.keys()).index(retailer)
                retailer_features[retailer_idx] = 1
            
            features.extend(retailer_features)
            
            # Características temporales
            now = datetime.now()
            hour_of_day = now.hour / 24.0
            day_of_week = now.weekday() / 7.0
            
            features.extend([hour_of_day, day_of_week])
            
            # Performance específica del retailer
            retailer_perf = metrics.retailer_performance.get(retailer, metrics.success_rate)
            features.append(retailer_perf)
            
            # Load actual del proxy
            active_sessions = sum(1 for session in self.active_sessions.values() 
                                if session.proxy_id == proxy_id and session.is_active)
            load_ratio = active_sessions / max(metrics.concurrent_capacity, 1)
            features.append(load_ratio)
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo características: {e}")
            return None

    def _calculate_recency_score(self, metrics: ProxyMetrics) -> float:
        """⏰ Calcular score basado en recencia de uso"""
        
        if not metrics.last_success:
            return 0.0
        
        hours_since_success = (datetime.now() - metrics.last_success).total_seconds() / 3600
        
        # Score decae exponencialmente con el tiempo
        recency_score = np.exp(-hours_since_success / 24)  # 24 horas = half-life
        
        return recency_score

    def _calculate_load_score(self, proxy_id: str) -> float:
        """⚖️ Calcular score basado en carga actual"""
        
        active_sessions = sum(1 for session in self.active_sessions.values() 
                            if session.proxy_id == proxy_id and session.is_active)
        
        metrics = self.proxy_metrics.get(proxy_id)
        if not metrics:
            return 0.5
        
        load_ratio = active_sessions / max(metrics.concurrent_capacity, 1)
        
        # Score más alto para proxies menos cargados
        load_score = 1.0 - min(load_ratio, 1.0)
        
        return load_score

    def _calculate_geo_score(self, metrics: ProxyMetrics, retailer: str) -> float:
        """🌍 Calcular score basado en geolocalización"""
        
        retailer_config = self.retailer_configs.get(retailer, {})
        preferred_countries = retailer_config.get('preferred_countries', ['CL'])
        
        if metrics.country in preferred_countries:
            # Score más alto para país preferido primario
            if metrics.country == preferred_countries[0]:
                return 1.0
            else:
                return 0.8
        
        return 0.3  # Score bajo para países no preferidos

    def _round_robin_selection(self, available_proxies: List[str], retailer: str) -> str:
        """🔄 Selección round-robin simple"""
        
        # Usar hash del retailer para determinismo por retailer
        retailer_hash = hash(retailer) % len(available_proxies)
        
        # Rotar basado en tiempo
        time_factor = int(time.time() / 60) % len(available_proxies)  # Cambio cada minuto
        
        index = (retailer_hash + time_factor) % len(available_proxies)
        
        return available_proxies[index]

    async def _get_proxy_configuration(self, proxy_id: str) -> Optional[Dict[str, Any]]:
        """🔧 Obtener configuración completa del proxy"""
        
        try:
            metrics = self.proxy_metrics.get(proxy_id)
            if not metrics:
                return None
            
            # Encontrar el proveedor
            provider = self._get_provider_for_proxy(proxy_id)
            if not provider:
                return None
            
            # Construir configuración
            config = {
                'proxy_id': proxy_id,
                'host': metrics.host,
                'port': metrics.port,
                'protocol': metrics.protocol,
                'username': '',
                'password': '',
                'provider': provider.name,
                'proxy_type': provider.proxy_type,
                'country': metrics.country,
                'rotation_interval': provider.rotation_interval,
                'auth_headers': {},
                'timeout': 30,
                'retry_count': 3
            }
            
            # Extraer credenciales del endpoint si están disponibles
            if '@' in provider.api_endpoint:
                # Formato: http://user:pass@host:port
                import re
                auth_match = re.search(r'://([^:]+):([^@]+)@', provider.api_endpoint)
                if auth_match:
                    config['username'] = auth_match.group(1)
                    config['password'] = auth_match.group(2)
            
            return config
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo configuración de {proxy_id}: {e}")
            return None

    def _get_provider_for_proxy(self, proxy_id: str) -> Optional[ProxyProvider]:
        """🏢 Obtener proveedor asociado al proxy"""
        
        # Extraer provider_id del proxy_id (formato: provider_id:host:port)
        provider_id = proxy_id.split(':')[0] if ':' in proxy_id else proxy_id
        
        return self.proxy_providers.get(provider_id)

    async def _register_proxy_assignment(self, proxy_id: str, retailer: str, category: str) -> None:
        """📋 Registrar asignación de proxy"""
        
        session_id = f"{proxy_id}_{retailer}_{int(time.time())}"
        
        session = ScrapingSession(
            session_id=session_id,
            retailer=retailer,
            proxy_id=proxy_id,
            start_time=datetime.now(),
            requests_made=0,
            success_count=0,
            avg_response_time=0.0,
            data_transferred=0.0,
            is_active=True,
            failure_reasons=[]
        )
        
        self.active_sessions[session_id] = session
        self.logger.debug(f"📋 Sesión {session_id} registrada")

    async def record_request_result(
        self,
        proxy_id: str,
        retailer: str,
        success: bool,
        response_time: float,
        error_reason: str = None,
        data_size: int = 0
    ) -> None:
        """📊 Registrar resultado de request"""
        
        try:
            # Actualizar métricas del proxy
            if proxy_id not in self.proxy_metrics:
                await self._initialize_proxy_metrics(proxy_id)
            
            metrics = self.proxy_metrics[proxy_id]
            
            # Actualizar contadores
            metrics.total_requests += 1
            
            if success:
                metrics.successful_requests += 1
                metrics.last_success = datetime.now()
                metrics.consecutive_failures = 0
                
                # Remover de lista de bloqueados si aplica
                metrics.blocked_by.discard(retailer)
                
            else:
                metrics.last_failure = datetime.now()
                metrics.consecutive_failures += 1
                
                # Agregar razón de fallo
                if error_reason:
                    metrics.failure_reasons.append(error_reason)
                    metrics.failure_reasons = metrics.failure_reasons[-10:]  # Mantener últimas 10
                
                # Marcar como bloqueado si es necesario
                if self._is_blocking_error(error_reason):
                    metrics.blocked_by.add(retailer)
            
            # Actualizar success rate
            metrics.success_rate = metrics.successful_requests / metrics.total_requests
            
            # Actualizar tiempo de respuesta promedio
            if response_time > 0:
                current_avg = metrics.avg_response_time
                total_successful = metrics.successful_requests
                
                if total_successful > 1:
                    metrics.avg_response_time = (
                        (current_avg * (total_successful - 1)) + response_time
                    ) / total_successful
                else:
                    metrics.avg_response_time = response_time
            
            # Actualizar performance por retailer
            if retailer not in metrics.retailer_performance:
                metrics.retailer_performance[retailer] = 0.0
            
            retailer_requests = sum(1 for session in self.active_sessions.values() 
                                  if session.proxy_id == proxy_id and session.retailer == retailer)
            
            if retailer_requests > 0:
                current_retailer_rate = metrics.retailer_performance[retailer]
                new_success_value = 1.0 if success else 0.0
                
                # Promedio ponderado con factor de decay
                alpha = 0.1  # Factor de aprendizaje
                metrics.retailer_performance[retailer] = (
                    (1 - alpha) * current_retailer_rate + alpha * new_success_value
                )
            
            # Actualizar health score
            await self._update_health_score(proxy_id)
            
            # Actualizar sesión activa si existe
            for session in self.active_sessions.values():
                if (session.proxy_id == proxy_id and 
                    session.retailer == retailer and 
                    session.is_active):
                    
                    session.requests_made += 1
                    if success:
                        session.success_count += 1
                    else:
                        session.failure_reasons.append(error_reason or "unknown")
                    
                    session.data_transferred += data_size / 1024 / 1024  # MB
                    
                    # Actualizar tiempo promedio de respuesta de la sesión
                    if response_time > 0:
                        if session.requests_made > 1:
                            session.avg_response_time = (
                                (session.avg_response_time * (session.requests_made - 1)) + response_time
                            ) / session.requests_made
                        else:
                            session.avg_response_time = response_time
                    
                    break
            
            # Guardar métricas
            self._save_metrics()
            
            self.logger.debug(f"📊 Resultado registrado para {proxy_id}: {'✅' if success else '❌'}")
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando resultado para {proxy_id}: {e}")

    async def _initialize_proxy_metrics(self, proxy_id: str) -> None:
        """🔧 Inicializar métricas para nuevo proxy"""
        
        # Extraer información básica del proxy_id
        parts = proxy_id.split(':')
        provider_id = parts[0] if len(parts) >= 3 else "unknown"
        host = parts[1] if len(parts) >= 3 else "unknown"
        port = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 8080
        
        # Determinar protocolo y país
        protocol = "http"
        country = "CL"  # Default para Chile
        
        provider = self.proxy_providers.get(provider_id)
        if provider:
            if provider.countries_available:
                country = provider.countries_available[0]
            if provider.protocols_supported:
                protocol = provider.protocols_supported[0]
        
        metrics = ProxyMetrics(
            proxy_id=proxy_id,
            host=host,
            port=port,
            protocol=protocol,
            country=country,
            success_rate=1.0,  # Comenzar con optimismo
            avg_response_time=2.0,
            total_requests=0,
            successful_requests=0,
            last_success=None,
            last_failure=None,
            consecutive_failures=0,
            retailer_performance={},
            failure_reasons=[],
            blocked_by=set(),
            health_score=1.0,
            cost_per_request=0.01,
            concurrent_capacity=self.max_concurrent_per_proxy,
            uptime_percentage=1.0
        )
        
        self.proxy_metrics[proxy_id] = metrics

    def _is_blocking_error(self, error_reason: str) -> bool:
        """🚫 Determinar si el error indica bloqueo"""
        
        if not error_reason:
            return False
        
        blocking_indicators = [
            'blocked', 'forbidden', '403', '429', 'rate limit',
            'access denied', 'cloudflare', 'captcha', 'bot detected',
            'suspicious activity', 'temporary block', 'ip banned'
        ]
        
        error_lower = error_reason.lower()
        
        return any(indicator in error_lower for indicator in blocking_indicators)

    async def _update_health_score(self, proxy_id: str) -> None:
        """❤️ Actualizar score de salud del proxy"""
        
        metrics = self.proxy_metrics.get(proxy_id)
        if not metrics:
            return
        
        # Componentes del health score
        success_component = metrics.success_rate * 0.4
        
        # Penalización por failures consecutivos
        failure_penalty = min(metrics.consecutive_failures * 0.1, 0.3)
        
        # Componente de latencia (normalizar response time)
        latency_component = max(0, (10 - metrics.avg_response_time) / 10) * 0.2
        
        # Componente de recencia
        recency_component = 0.1
        if metrics.last_success:
            hours_since = (datetime.now() - metrics.last_success).total_seconds() / 3600
            recency_component = max(0, (24 - hours_since) / 24) * 0.1
        
        # Componente de uptime
        uptime_component = metrics.uptime_percentage * 0.1
        
        # Penalización por bloqueos
        blocking_penalty = len(metrics.blocked_by) * 0.05
        
        health_score = (
            success_component + 
            latency_component + 
            recency_component + 
            uptime_component - 
            failure_penalty - 
            blocking_penalty
        )
        
        metrics.health_score = max(0.0, min(1.0, health_score))

    async def perform_health_checks(self) -> Dict[str, Any]:
        """🏥 Realizar health checks de todos los proxies"""
        
        start_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_proxies': len(self.proxy_metrics),
            'healthy_proxies': 0,
            'quarantined_proxies': 0,
            'blocked_proxies': 0,
            'check_results': []
        }
        
        # URLs de test para cada retailer
        test_urls = {
            'ripley': 'https://simple.ripley.cl/informatica',
            'falabella': 'https://www.falabella.com/falabella-cl/category/cat70037',
            'paris': 'https://www.paris.cl/informatica',
            'hites': 'https://www.hites.com/informatica',
            'abcdin': 'https://www.abcdin.cl/informatica',
            'mercadolibre': 'https://listado.mercadolibre.cl/informatica'
        }
        
        for proxy_id, metrics in self.proxy_metrics.items():
            try:
                # Test básico de conectividad
                proxy_config = await self._get_proxy_configuration(proxy_id)
                
                if not proxy_config:
                    continue
                
                # Test con una URL de muestra
                test_url = test_urls.get('ripley', 'https://httpbin.org/ip')
                
                health_result = await self._test_proxy_health(proxy_id, test_url, proxy_config)
                
                # Actualizar métricas basado en resultado
                if health_result['success']:
                    results['healthy_proxies'] += 1
                    metrics.uptime_percentage = min(1.0, metrics.uptime_percentage + 0.1)
                else:
                    metrics.uptime_percentage = max(0.0, metrics.uptime_percentage - 0.2)
                    
                    if health_result.get('blocked', False):
                        results['blocked_proxies'] += 1
                    
                    if metrics.consecutive_failures >= self.max_failures_before_quarantine:
                        results['quarantined_proxies'] += 1
                
                results['check_results'].append({
                    'proxy_id': proxy_id,
                    'success': health_result['success'],
                    'response_time': health_result.get('response_time', 0),
                    'error': health_result.get('error', ''),
                    'health_score': metrics.health_score
                })
                
                await self._update_health_score(proxy_id)
                
            except Exception as e:
                self.logger.error(f"❌ Error en health check de {proxy_id}: {e}")
                continue
        
        # Guardar métricas actualizadas
        self._save_metrics()
        
        execution_time = time.time() - start_time
        results['execution_time'] = execution_time
        
        self.logger.info(
            f"🏥 Health check completado: {results['healthy_proxies']}/{results['total_proxies']} "
            f"proxies saludables en {execution_time:.1f}s"
        )
        
        return results

    async def _test_proxy_health(
        self, 
        proxy_id: str, 
        test_url: str, 
        proxy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """🔍 Test individual de salud de proxy"""
        
        start_time = time.time()
        result = {
            'success': False,
            'response_time': 0,
            'error': '',
            'blocked': False
        }
        
        try:
            # Configurar proxy para requests
            proxy_url = f"{proxy_config['protocol']}://"
            
            if proxy_config.get('username') and proxy_config.get('password'):
                proxy_url += f"{proxy_config['username']}:{proxy_config['password']}@"
            
            proxy_url += f"{proxy_config['host']}:{proxy_config['port']}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Headers para parecer más humano
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-CL,es;q=0.8,en;q=0.6',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            # Realizar request
            response = requests.get(
                test_url,
                proxies=proxies,
                headers=headers,
                timeout=proxy_config.get('timeout', 15),
                verify=False,
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            result['response_time'] = response_time
            
            # Verificar respuesta
            if response.status_code == 200:
                result['success'] = True
                self.logger.debug(f"✅ Health check exitoso para {proxy_id}")
            
            elif response.status_code in [403, 429, 503]:
                result['blocked'] = True
                result['error'] = f"HTTP {response.status_code}"
                self.logger.warning(f"🚫 Proxy {proxy_id} bloqueado: {response.status_code}")
            
            else:
                result['error'] = f"HTTP {response.status_code}"
                self.logger.warning(f"⚠️ Health check fallido para {proxy_id}: {response.status_code}")
            
        except requests.exceptions.ProxyError:
            result['error'] = "Proxy connection error"
            result['blocked'] = True
            
        except requests.exceptions.Timeout:
            result['error'] = "Timeout"
            
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection error"
            
        except Exception as e:
            result['error'] = str(e)
        
        result['response_time'] = time.time() - start_time
        
        return result

    async def rotate_proxy_pool(self, provider_id: str = None) -> int:
        """🔄 Rotar pool de proxies obteniendo nuevos"""
        
        rotated_count = 0
        
        try:
            providers_to_rotate = [provider_id] if provider_id else list(self.proxy_providers.keys())
            
            for pid in providers_to_rotate:
                provider = self.proxy_providers.get(pid)
                
                if not provider or not provider.is_active:
                    continue
                
                # Obtener nuevos proxies del proveedor
                new_proxies = await self._fetch_proxies_from_provider(provider)
                
                for proxy_info in new_proxies:
                    proxy_id = f"{pid}:{proxy_info['host']}:{proxy_info['port']}"
                    
                    if proxy_id not in self.proxy_metrics:
                        await self._initialize_proxy_metrics(proxy_id)
                        rotated_count += 1
                        
                        self.logger.info(f"🔄 Nuevo proxy agregado: {proxy_id}")
                
            self.logger.info(f"🔄 Rotación completada: {rotated_count} proxies nuevos")
            
        except Exception as e:
            self.logger.error(f"❌ Error en rotación de proxies: {e}")
        
        return rotated_count

    async def _fetch_proxies_from_provider(self, provider: ProxyProvider) -> List[Dict[str, Any]]:
        """📡 Obtener proxies de un proveedor específico"""
        
        # Esta es una implementación base que debe ser personalizada por proveedor
        proxies = []
        
        try:
            if provider.provider_id == "local_test":
                # Proxy de prueba local
                proxies = [{
                    'host': '127.0.0.1',
                    'port': 8888,
                    'protocol': 'http',
                    'country': 'CL'
                }]
            
            elif provider.api_endpoint:
                # Para proveedores reales, implementar llamadas API específicas
                # Este sería el lugar para integrar con APIs de Bright Data, SmartProxy, etc.
                self.logger.warning(f"⚠️ Implementar API para proveedor {provider.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo proxies de {provider.name}: {e}")
        
        return proxies

    def get_proxy_statistics(self, retailer: str = None, hours: int = 24) -> Dict[str, Any]:
        """📈 Obtener estadísticas detalladas de proxies"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'period_hours': hours,
            'retailer_filter': retailer,
            'summary': {
                'total_proxies': len(self.proxy_metrics),
                'active_sessions': len([s for s in self.active_sessions.values() if s.is_active]),
                'avg_success_rate': 0.0,
                'avg_response_time': 0.0,
                'total_requests': 0,
                'successful_requests': 0
            },
            'top_performers': [],
            'problematic_proxies': [],
            'retailer_breakdown': {},
            'provider_performance': {}
        }
        
        # Filtrar métricas relevantes
        relevant_metrics = []
        for metrics in self.proxy_metrics.values():
            if retailer is None or retailer in metrics.retailer_performance:
                # Filtrar por tiempo si hay actividad reciente
                if metrics.last_success and metrics.last_success >= cutoff_time:
                    relevant_metrics.append(metrics)
                elif metrics.last_failure and metrics.last_failure >= cutoff_time:
                    relevant_metrics.append(metrics)
        
        if not relevant_metrics:
            return stats
        
        # Estadísticas generales
        total_requests = sum(m.total_requests for m in relevant_metrics)
        successful_requests = sum(m.successful_requests for m in relevant_metrics)
        
        stats['summary'].update({
            'avg_success_rate': sum(m.success_rate for m in relevant_metrics) / len(relevant_metrics),
            'avg_response_time': sum(m.avg_response_time for m in relevant_metrics) / len(relevant_metrics),
            'total_requests': total_requests,
            'successful_requests': successful_requests
        })
        
        # Top performers (por success rate y health score)
        top_performers = sorted(
            relevant_metrics, 
            key=lambda x: (x.success_rate * 0.7 + x.health_score * 0.3), 
            reverse=True
        )[:10]
        
        stats['top_performers'] = [
            {
                'proxy_id': m.proxy_id,
                'success_rate': m.success_rate,
                'health_score': m.health_score,
                'avg_response_time': m.avg_response_time,
                'total_requests': m.total_requests,
                'country': m.country
            }
            for m in top_performers
        ]
        
        # Proxies problemáticos
        problematic = [
            m for m in relevant_metrics 
            if m.success_rate < 0.5 or m.consecutive_failures > 2 or len(m.blocked_by) > 0
        ]
        
        stats['problematic_proxies'] = [
            {
                'proxy_id': m.proxy_id,
                'success_rate': m.success_rate,
                'consecutive_failures': m.consecutive_failures,
                'blocked_by': list(m.blocked_by),
                'last_failure_reasons': m.failure_reasons[-3:]
            }
            for m in problematic[:10]
        ]
        
        # Breakdown por retailer
        if retailer is None:
            for ret in self.retailer_configs.keys():
                retailer_metrics = [
                    m for m in relevant_metrics 
                    if ret in m.retailer_performance
                ]
                
                if retailer_metrics:
                    stats['retailer_breakdown'][ret] = {
                        'proxies_used': len(retailer_metrics),
                        'avg_success_rate': sum(m.retailer_performance[ret] for m in retailer_metrics) / len(retailer_metrics),
                        'blocked_proxies': len([m for m in retailer_metrics if ret in m.blocked_by])
                    }
        
        # Performance por proveedor
        provider_stats = {}
        for metrics in relevant_metrics:
            provider_id = metrics.proxy_id.split(':')[0]
            
            if provider_id not in provider_stats:
                provider_stats[provider_id] = {
                    'proxy_count': 0,
                    'success_rates': [],
                    'response_times': []
                }
            
            provider_stats[provider_id]['proxy_count'] += 1
            provider_stats[provider_id]['success_rates'].append(metrics.success_rate)
            provider_stats[provider_id]['response_times'].append(metrics.avg_response_time)
        
        for provider_id, data in provider_stats.items():
            provider = self.proxy_providers.get(provider_id)
            stats['provider_performance'][provider_id] = {
                'provider_name': provider.name if provider else provider_id,
                'proxy_count': data['proxy_count'],
                'avg_success_rate': sum(data['success_rates']) / len(data['success_rates']),
                'avg_response_time': sum(data['response_times']) / len(data['response_times'])
            }
        
        return stats

    async def train_performance_model(self, force_retrain: bool = False) -> bool:
        """🎓 Entrenar modelo de predicción de performance"""
        
        if not force_retrain and self.performance_predictor is not None:
            self.logger.info("🎓 Modelo ya entrenado, usar force_retrain=True para re-entrenar")
            return True
        
        try:
            # Preparar datos de entrenamiento
            training_data = self._prepare_ml_training_data()
            
            if len(training_data) < 100:
                self.logger.warning("⚠️ Datos insuficientes para entrenar modelo ML")
                return False
            
            # Preparar features y targets
            X = []
            y = []
            
            for data_point in training_data:
                X.append(data_point['features'])
                y.append(data_point['success_rate'])
            
            X = np.array(X)
            y = np.array(y)
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Escalar características
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelo
            self.performance_predictor = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.performance_predictor.fit(X_train_scaled, y_train)
            
            # Evaluar modelo
            train_score = self.performance_predictor.score(X_train_scaled, y_train)
            test_score = self.performance_predictor.score(X_test_scaled, y_test)
            
            self.logger.info(f"🎯 Modelo ML entrenado - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
            
            # Guardar modelos
            self._save_models()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error entrenando modelo ML: {e}")
            return False

    def _prepare_ml_training_data(self) -> List[Dict[str, Any]]:
        """📚 Preparar datos de entrenamiento para ML"""
        
        training_data = []
        
        for proxy_id, metrics in self.proxy_metrics.items():
            if metrics.total_requests < 10:  # Muy pocos datos
                continue
            
            # Para cada retailer con el que se ha usado este proxy
            for retailer, retailer_success_rate in metrics.retailer_performance.items():
                features = self._extract_prediction_features(proxy_id, retailer, "default")
                
                if features is not None:
                    training_data.append({
                        'proxy_id': proxy_id,
                        'retailer': retailer,
                        'features': features,
                        'success_rate': retailer_success_rate
                    })
        
        self.logger.info(f"📚 Preparados {len(training_data)} ejemplos de entrenamiento ML")
        
        return training_data

    async def start_health_monitoring(self) -> None:
        """🏥 Iniciar monitoreo continuo de salud"""
        
        if self._health_check_task is not None:
            return  # Ya está corriendo
        
        async def health_monitor():
            while True:
                try:
                    await self.perform_health_checks()
                    await asyncio.sleep(self.health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error en monitoreo de salud: {e}")
                    await asyncio.sleep(60)  # Retry en 1 minuto
        
        self._health_check_task = asyncio.create_task(health_monitor())
        self.logger.info("🏥 Monitoreo de salud iniciado")

    async def stop_health_monitoring(self) -> None:
        """⏹️ Detener monitoreo de salud"""
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            
            self._health_check_task = None
            self.logger.info("⏹️ Monitoreo de salud detenido")

    def cleanup_old_sessions(self, hours: int = 24) -> int:
        """🧹 Limpiar sesiones antiguas"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        removed_count = 0
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session.start_time < cutoff_time or not session.is_active:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            removed_count += 1
        
        self.logger.info(f"🧹 Limpieza de sesiones: {removed_count} sesiones eliminadas")
        
        return removed_count

    def export_metrics(self, filepath: str = None) -> str:
        """📤 Exportar métricas a archivo JSON"""
        
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(self.storage_path / f"proxy_metrics_export_{timestamp}.json")
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_proxies': len(self.proxy_metrics),
            'active_sessions': len([s for s in self.active_sessions.values() if s.is_active]),
            'proxy_metrics': {},
            'providers': {}
        }
        
        # Exportar métricas de proxies
        for proxy_id, metrics in self.proxy_metrics.items():
            export_data['proxy_metrics'][proxy_id] = {
                'success_rate': metrics.success_rate,
                'avg_response_time': metrics.avg_response_time,
                'total_requests': metrics.total_requests,
                'health_score': metrics.health_score,
                'retailer_performance': metrics.retailer_performance,
                'blocked_by': list(metrics.blocked_by),
                'country': metrics.country,
                'uptime_percentage': metrics.uptime_percentage
            }
        
        # Exportar información de proveedores
        for provider_id, provider in self.proxy_providers.items():
            export_data['providers'][provider_id] = {
                'name': provider.name,
                'proxy_type': provider.proxy_type,
                'reliability_score': provider.reliability_score,
                'is_active': provider.is_active
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📤 Métricas exportadas a: {filepath}")
        
        return filepath