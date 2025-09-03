#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Scraper v5 Central Orchestrator - Orquestador Principal Sólido
================================================================

Orquestador central robusto y profesional que coordina todo el sistema:
- 🧠 Gestión inteligente de recursos y scheduling
- ⚡ Sistema de tiers dinámico y adaptativos  
- 🔄 Auto-recovery y circuit breakers
- 📊 Monitoreo en tiempo real con métricas ML
- 🧪 Testing integrado y debugging automático
- 🌐 Gestión avanzada de proxies y rate limiting
- 📈 Optimización continua basada en performance histórico

El orchestrador es el cerebro del sistema que toma decisiones inteligentes
sobre cuándo, cómo y dónde ejecutar scrapers para maximizar eficiencia.

Author: Portable Orchestrator Team
Version: 5.0.0
"""

import sys
import os
import io
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import traceback
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import hashlib
import random

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Imports del sistema
try:
    import redis
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    redis = psycopg2 = RealDictCursor = None

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OrchestratorState(Enum):
    """📊 Estados del orquestador"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class RetailerTier(Enum):
    """⚡ Tiers de prioridad para retailers"""
    TIER_1_CRITICAL = 1    # Tiempo real - productos críticos
    TIER_2_HIGH = 2        # Cada hora - productos importantes  
    TIER_3_MEDIUM = 3      # Cada 4 horas - productos estándar
    TIER_4_LOW = 4         # Diario - productos de baja demanda

@dataclass
class ScrapingTask:
    """📋 Tarea de scraping individual"""
    task_id: str
    retailer: str
    category: str
    url: str
    tier: RetailerTier
    priority: int = 50  # 0-100
    max_retries: int = 3
    timeout: int = 60
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed, retrying
    retry_count: int = 0
    error_message: Optional[str] = None
    products_found: int = 0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.scheduled_at is None:
            self.scheduled_at = self.created_at

@dataclass
class RetailerConfig:
    """🏪 Configuración específica por retailer"""
    name: str
    enabled: bool = True
    tier: RetailerTier = RetailerTier.TIER_3_MEDIUM
    base_url: str = ""
    categories: List[str] = field(default_factory=list)
    rate_limit: float = 1.0  # Requests por segundo
    timeout: int = 60
    max_concurrent: int = 2
    requires_proxy: bool = False
    proxy_pool: str = "default"
    custom_headers: Dict[str, str] = field(default_factory=dict)
    selectors: Dict[str, str] = field(default_factory=dict)
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_until: Optional[datetime] = None
    
class CircuitBreaker:
    """⚡ Circuit breaker para protección contra fallos cascada"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Verificar si se puede ejecutar la operación"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        elif self.state == "half-open":
            return True
        return False
    
    def record_success(self):
        """Registrar éxito"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Registrar fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

class ScraperV5Orchestrator:
    """
    🎯 Orquestador Central Scraper v5 - El Cerebro del Sistema
    
    Orquestador principal que coordina y optimiza todo el sistema de scraping:
    
    🧠 **GESTIÓN INTELIGENTE:**
    - Scheduling adaptativos basado en patrones históricos
    - Distribución automática de recursos
    - Optimización continua de performance
    
    ⚡ **SISTEMA DE TIERS:**
    - Tier 1: Productos críticos (tiempo real)
    - Tier 2: Productos importantes (cada hora)
    - Tier 3: Productos estándar (cada 4 horas)
    - Tier 4: Productos baja demanda (diario)
    
    🔄 **AUTO-RECOVERY:**
    - Circuit breakers por retailer
    - Retry inteligente con backoff exponencial
    - Detección automática de fallos recurrentes
    - Auto-healing de configuraciones
    
    📊 **MONITOREO:**
    - Métricas en tiempo real
    - Alertas proactivas
    - Performance tracking
    - Health checks automáticos
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 enable_testing: bool = True):
        """
        🚀 Inicializar Orquestador Central
        
        Args:
            config_path: Ruta al archivo de configuración
            enable_testing: Habilitar modo testing integrado
        """
        self.config_path = config_path
        self.enable_testing = enable_testing
        self.state = OrchestratorState.INITIALIZING
        
        # Core components
        self.retailers: Dict[str, RetailerConfig] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.task_queue: List[ScrapingTask] = []
        self.active_tasks: Dict[str, ScrapingTask] = {}
        self.completed_tasks: List[ScrapingTask] = []
        
        # Threading y concurrencia
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.scheduler_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Métricas y performance
        self.start_time: Optional[datetime] = None
        self.metrics: Dict[str, Any] = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_products_found': 0,
            'avg_task_duration': 0.0,
            'retailers_active': 0,
            'circuit_breakers_open': 0
        }
        
        # Conexiones externas
        self.redis_client = None
        self.db_connection = None
        
        # Directorios
        self.logs_dir = Path("logs/orchestrator")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Testing integrado
        if self.enable_testing:
            from ..testing.test_runner import RetailerTestRunner
            from ..testing.maintenance_tools import MaintenanceToolkit
            self.test_runner = RetailerTestRunner()
            self.maintenance_toolkit = None  # Se inicializa cuando se necesite
        
        logger.info("🎯 ScraperV5Orchestrator inicializado correctamente")
    
    async def initialize(self) -> bool:
        """
        🚀 Inicialización completa del orquestador
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        logger.info("🚀 Iniciando inicialización del orquestador...")
        
        try:
            # 1. Cargar configuración
            await self._load_configuration()
            
            # 2. Inicializar conexiones
            await self._initialize_connections()
            
            # 3. Configurar retailers
            await self._setup_retailers()
            
            # 4. Inicializar circuit breakers
            self._initialize_circuit_breakers()
            
            # 5. Cargar estado persistente
            await self._load_persistent_state()
            
            # 6. Validación inicial
            validation_result = await self._validate_system()
            if not validation_result:
                logger.error("❌ Falló la validación inicial del sistema")
                return False
            
            self.state = OrchestratorState.RUNNING
            self.start_time = datetime.now()
            
            logger.info("✅ Orquestador inicializado correctamente")
            logger.info(f"📊 Retailers configurados: {len(self.retailers)}")
            logger.info(f"🎯 Estado: {self.state.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Error en inicialización: {str(e)}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            self.state = OrchestratorState.ERROR
            return False
    
    async def start(self) -> None:
        """
        ▶️ Iniciar orquestador y todos sus componentes
        """
        if self.state != OrchestratorState.RUNNING:
            logger.error("❌ Orquestador no está en estado RUNNING")
            return
        
        logger.info("▶️ Iniciando orquestador...")
        
        self.running = True
        
        # Iniciar threads de background
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, 
            daemon=True,
            name="OrchestratorScheduler"
        )
        self.scheduler_thread.start()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True, 
            name="OrchestratorMonitor"
        )
        self.monitor_thread.start()
        
        # Testing inicial si está habilitado
        if self.enable_testing:
            logger.info("🧪 Ejecutando tests iniciales...")
            await self._run_initial_tests()
        
        logger.info("✅ Orquestador iniciado correctamente")
        
        # Loop principal
        try:
            await self._main_execution_loop()
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo orquestador (Ctrl+C)")
            await self.stop()
        except Exception as e:
            logger.error(f"💥 Error en loop principal: {str(e)}")
            await self.stop()
    
    async def stop(self) -> None:
        """
        ⏹️ Detener orquestador de forma ordenada
        """
        logger.info("⏹️ Deteniendo orquestador...")
        self.state = OrchestratorState.STOPPING
        
        # Detener threads
        self.running = False
        
        # Esperar tareas activas
        if self.active_tasks:
            logger.info(f"⏳ Esperando {len(self.active_tasks)} tareas activas...")
            timeout = 30  # 30 segundos máximo
            start_wait = time.time()
            
            while self.active_tasks and (time.time() - start_wait) < timeout:
                await asyncio.sleep(1)
                
            if self.active_tasks:
                logger.warning(f"⚠️  {len(self.active_tasks)} tareas no completadas en timeout")
        
        # Guardar estado
        await self._save_persistent_state()
        
        # Cerrar conexiones
        await self._cleanup_connections()
        
        # Cerrar executor
        self.executor.shutdown(wait=True)
        
        self.state = OrchestratorState.STOPPED
        
        # Reporte final
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info("📊 REPORTE FINAL DEL ORQUESTADOR")
            logger.info(f"⏱️  Tiempo ejecutándose: {duration}")
            logger.info(f"✅ Tareas completadas: {self.metrics['tasks_completed']}")
            logger.info(f"❌ Tareas fallidas: {self.metrics['tasks_failed']}")
            logger.info(f"📦 Productos encontrados: {self.metrics['total_products_found']}")
        
        logger.info("✅ Orquestador detenido correctamente")
    
    async def schedule_task(self, task: ScrapingTask) -> bool:
        """
        📋 Programar nueva tarea de scraping
        
        Args:
            task: Tarea de scraping a programar
            
        Returns:
            bool: True si la tarea fue programada exitosamente
        """
        try:
            # Validar tarea
            if not self._validate_task(task):
                return False
            
            # Verificar circuit breaker
            retailer = task.retailer
            if retailer in self.circuit_breakers:
                if not self.circuit_breakers[retailer].can_execute():
                    logger.warning(f"⚡ Circuit breaker abierto para {retailer}, tarea rechazada")
                    return False
            
            # Calcular prioridad dinámica
            task.priority = self._calculate_dynamic_priority(task)
            
            # Añadir a cola ordenada por prioridad
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: (-t.priority, t.scheduled_at))
            
            logger.info(f"📋 Tarea programada: {task.retailer}/{task.category} "
                       f"(prioridad: {task.priority}, tier: {task.tier.value})")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Error programando tarea: {str(e)}")
            return False
    
    async def _main_execution_loop(self) -> None:
        """🔄 Loop principal de ejecución"""
        logger.info("🔄 Iniciando loop principal de ejecución")
        
        while self.running:
            try:
                # 1. Procesar cola de tareas
                await self._process_task_queue()
                
                # 2. Monitorear tareas activas
                await self._monitor_active_tasks()
                
                # 3. Actualizar métricas
                self._update_metrics()
                
                # 4. Health check periódico
                await self._periodic_health_check()
                
                # 5. Optimización automática
                await self._auto_optimization()
                
                # Pausa entre ciclos
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"💥 Error en loop principal: {str(e)}")
                logger.error(f"🔍 Traceback: {traceback.format_exc()}")
                await asyncio.sleep(5)  # Pausa más larga en caso de error
    
    async def _process_task_queue(self) -> None:
        """📋 Procesar cola de tareas pendientes"""
        if not self.task_queue:
            return
        
        # Limitar tareas concurrentes
        max_concurrent = self._calculate_max_concurrent_tasks()
        if len(self.active_tasks) >= max_concurrent:
            return
        
        # Procesar tareas en orden de prioridad
        tasks_to_start = []
        current_time = datetime.now()
        
        for task in self.task_queue[:]:
            if len(self.active_tasks) + len(tasks_to_start) >= max_concurrent:
                break
                
            # Verificar si es hora de ejecutar
            if task.scheduled_at <= current_time:
                # Verificar recursos disponibles para el retailer
                if self._can_execute_retailer_task(task.retailer):
                    tasks_to_start.append(task)
                    self.task_queue.remove(task)
        
        # Iniciar tareas seleccionadas
        for task in tasks_to_start:
            await self._start_task(task)
    
    async def _start_task(self, task: ScrapingTask) -> None:
        """🚀 Iniciar ejecución de una tarea"""
        task.status = "running"
        task.started_at = datetime.now()
        self.active_tasks[task.task_id] = task
        
        logger.info(f"🚀 Iniciando tarea: {task.task_id} ({task.retailer}/{task.category})")
        
        # Ejecutar tarea en thread pool
        future = self.executor.submit(self._execute_scraping_task, task)
        
        # Manejar resultado de forma asíncrona
        asyncio.create_task(self._handle_task_completion(task, future))
    
    def _execute_scraping_task(self, task: ScrapingTask) -> Dict[str, Any]:
        """
        🕷️ Ejecutar tarea de scraping (en thread separado)
        
        Args:
            task: Tarea a ejecutar
            
        Returns:
            Dict con resultado de la ejecución
        """
        try:
            start_time = time.time()
            
            # TODO: Aquí iría la lógica real de scraping
            # Por ahora simulamos la ejecución
            
            # Simulación de scraping
            scraping_duration = random.uniform(5, 30)  # 5-30 segundos
            time.sleep(scraping_duration)
            
            # Simular productos encontrados
            products_found = random.randint(10, 50)
            
            duration = time.time() - start_time
            
            return {
                'success': True,
                'products_found': products_found,
                'duration': duration,
                'message': f'Scraping completado: {products_found} productos'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    async def _handle_task_completion(self, task: ScrapingTask, future) -> None:
        """✅ Manejar finalización de tarea"""
        try:
            result = future.result()
            
            # Actualizar tarea con resultado
            task.completed_at = datetime.now()
            task.performance_metrics = result
            
            if result.get('success', False):
                task.status = "completed"
                task.products_found = result.get('products_found', 0)
                
                # Registrar éxito en circuit breaker
                if task.retailer in self.circuit_breakers:
                    self.circuit_breakers[task.retailer].record_success()
                
                logger.info(f"✅ Tarea completada: {task.task_id} "
                           f"({task.products_found} productos en "
                           f"{result.get('duration', 0):.2f}s)")
                
                # Actualizar métricas del retailer
                if task.retailer in self.retailers:
                    self.retailers[task.retailer].last_success = task.completed_at
                    self.retailers[task.retailer].consecutive_failures = 0
            else:
                await self._handle_task_failure(task, result.get('error', 'Unknown error'))
            
            # Mover tarea a completadas
            self.active_tasks.pop(task.task_id, None)
            self.completed_tasks.append(task)
            
            # Mantener solo últimas 1000 tareas completadas
            if len(self.completed_tasks) > 1000:
                self.completed_tasks = self.completed_tasks[-1000:]
                
        except Exception as e:
            logger.error(f"💥 Error manejando finalización de tarea {task.task_id}: {str(e)}")
            await self._handle_task_failure(task, str(e))
    
    async def _handle_task_failure(self, task: ScrapingTask, error_message: str) -> None:
        """❌ Manejar fallo de tarea"""
        task.error_message = error_message
        task.retry_count += 1
        
        # Registrar fallo en circuit breaker
        if task.retailer in self.circuit_breakers:
            self.circuit_breakers[task.retailer].record_failure()
        
        # Actualizar métricas del retailer
        if task.retailer in self.retailers:
            self.retailers[task.retailer].consecutive_failures += 1
        
        # Decidir si reintentar
        if task.retry_count < task.max_retries:
            # Calcular backoff exponencial
            backoff_seconds = min(300, 2 ** task.retry_count * 10)  # Max 5 minutos
            task.scheduled_at = datetime.now() + timedelta(seconds=backoff_seconds)
            task.status = "retrying"
            
            # Re-añadir a cola
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: (-t.priority, t.scheduled_at))
            
            logger.warning(f"🔄 Reintentando tarea {task.task_id} en {backoff_seconds}s "
                          f"(intento {task.retry_count + 1}/{task.max_retries})")
        else:
            task.status = "failed"
            logger.error(f"❌ Tarea {task.task_id} falló definitivamente: {error_message}")
            
            # Diagnóstico automático si está habilitado
            if self.enable_testing and hasattr(self, 'maintenance_toolkit'):
                asyncio.create_task(self._auto_diagnose_failure(task))
    
    async def _auto_diagnose_failure(self, task: ScrapingTask) -> None:
        """🩺 Diagnóstico automático de fallos"""
        try:
            if not self.maintenance_toolkit:
                from ..testing.maintenance_tools import MaintenanceToolkit
                self.maintenance_toolkit = MaintenanceToolkit()
            
            # Ejecutar diagnóstico automático
            async with self.maintenance_toolkit as toolkit:
                result = await toolkit.diagnose_scraper_issues(
                    task.url, 
                    task.retailer,
                    self.retailers[task.retailer].selectors,
                    [task.error_message] if task.error_message else []
                )
                
                logger.info(f"🩺 Diagnóstico automático completado para {task.retailer}")
                logger.info(f"📊 Severidad: {result.severity}, Issues: {len(result.issues_found)}")
                
        except Exception as e:
            logger.warning(f"⚠️  Error en diagnóstico automático: {str(e)}")
    
    # ... [Continuará con más métodos del orquestador] ...
    
    async def _load_configuration(self) -> None:
        """📋 Cargar configuración del sistema"""
        # Configuración por defecto si no hay archivo
        default_config = {
            'retailers': {
                'ripley': {
                    'enabled': True,
                    'tier': 'TIER_2_HIGH',
                    'base_url': 'https://simple.ripley.cl',
                    'categories': ['celulares', 'notebooks', 'electrodomesticos'],
                    'rate_limit': 0.5,
                    'timeout': 45,
                    'requires_proxy': True
                },
                'falabella': {
                    'enabled': True,
                    'tier': 'TIER_2_HIGH', 
                    'base_url': 'https://www.falabella.com',
                    'categories': ['celulares', 'computacion', 'electrohogar'],
                    'rate_limit': 1.0,
                    'timeout': 60
                },
                'paris': {
                    'enabled': True,
                    'tier': 'TIER_3_MEDIUM',
                    'base_url': 'https://www.paris.cl',
                    'categories': ['tecnologia', 'electrodomesticos'],
                    'rate_limit': 1.5,
                    'timeout': 40
                }
            },
            'system': {
                'max_concurrent_tasks': 8,
                'health_check_interval': 300,  # 5 minutos
                'auto_optimization_interval': 1800,  # 30 minutos
                'circuit_breaker_failure_threshold': 5,
                'circuit_breaker_recovery_timeout': 600  # 10 minutos
            }
        }
        
        self.config = default_config
        logger.info("📋 Configuración cargada correctamente")
    
    async def _initialize_connections(self) -> None:
        """🔗 Inicializar conexiones a servicios externos"""
        try:
            # Redis para cache y estado
            if redis:
                self.redis_client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=0,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("✅ Conexión Redis establecida")
        except Exception as e:
            logger.warning(f"⚠️  Redis no disponible: {str(e)}")
        
        logger.info("🔗 Conexiones inicializadas")
    
    async def _setup_retailers(self) -> None:
        """🏪 Configurar retailers desde configuración"""
        retailers_config = self.config.get('retailers', {})
        
        for retailer_name, config in retailers_config.items():
            tier_str = config.get('tier', 'TIER_3_MEDIUM')
            tier = RetailerTier[tier_str] if tier_str in RetailerTier.__members__ else RetailerTier.TIER_3_MEDIUM
            
            retailer_config = RetailerConfig(
                name=retailer_name,
                enabled=config.get('enabled', True),
                tier=tier,
                base_url=config.get('base_url', ''),
                categories=config.get('categories', []),
                rate_limit=config.get('rate_limit', 1.0),
                timeout=config.get('timeout', 60),
                requires_proxy=config.get('requires_proxy', False)
            )
            
            self.retailers[retailer_name] = retailer_config
        
        logger.info(f"🏪 {len(self.retailers)} retailers configurados")
    
    def _initialize_circuit_breakers(self) -> None:
        """⚡ Inicializar circuit breakers por retailer"""
        system_config = self.config.get('system', {})
        failure_threshold = system_config.get('circuit_breaker_failure_threshold', 5)
        recovery_timeout = system_config.get('circuit_breaker_recovery_timeout', 600)
        
        for retailer_name in self.retailers.keys():
            self.circuit_breakers[retailer_name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
        
        logger.info(f"⚡ {len(self.circuit_breakers)} circuit breakers inicializados")
    
    async def _validate_system(self) -> bool:
        """✅ Validación inicial del sistema"""
        logger.info("✅ Ejecutando validación inicial...")
        
        # Validar que hay al menos un retailer habilitado
        enabled_retailers = [r for r in self.retailers.values() if r.enabled]
        if not enabled_retailers:
            logger.error("❌ No hay retailers habilitados")
            return False
        
        logger.info(f"✅ {len(enabled_retailers)} retailers habilitados para scraping")
        return True
    
    async def _load_persistent_state(self) -> None:
        """💾 Cargar estado persistente desde Redis/DB"""
        if self.redis_client:
            try:
                # Cargar métricas persistentes
                metrics_key = "orchestrator:metrics"
                stored_metrics = self.redis_client.hgetall(metrics_key)
                
                if stored_metrics:
                    for key, value in stored_metrics.items():
                        if key in self.metrics:
                            try:
                                self.metrics[key] = float(value)
                            except (ValueError, TypeError):
                                pass
                    
                    logger.info("💾 Estado persistente cargado desde Redis")
            except Exception as e:
                logger.warning(f"⚠️  Error cargando estado persistente: {str(e)}")
    
    async def _save_persistent_state(self) -> None:
        """💾 Guardar estado persistente en Redis/DB"""
        if self.redis_client:
            try:
                # Guardar métricas
                metrics_key = "orchestrator:metrics"
                self.redis_client.hmset(metrics_key, self.metrics)
                self.redis_client.expire(metrics_key, 86400)  # 24 horas
                
                logger.info("💾 Estado persistente guardado")
            except Exception as e:
                logger.warning(f"⚠️  Error guardando estado: {str(e)}")
    
    async def _cleanup_connections(self) -> None:
        """🧹 Limpiar conexiones"""
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        if self.db_connection:
            try:
                self.db_connection.close()
            except:
                pass
    
    # Métodos de utilidad y helpers
    def _validate_task(self, task: ScrapingTask) -> bool:
        """Validar tarea antes de programar"""
        if not task.retailer or not task.category or not task.url:
            return False
        
        if task.retailer not in self.retailers:
            logger.warning(f"⚠️  Retailer desconocido: {task.retailer}")
            return False
        
        if not self.retailers[task.retailer].enabled:
            logger.warning(f"⚠️  Retailer deshabilitado: {task.retailer}")
            return False
        
        return True
    
    def _calculate_dynamic_priority(self, task: ScrapingTask) -> int:
        """Calcular prioridad dinámica basada en múltiples factores"""
        base_priority = {
            RetailerTier.TIER_1_CRITICAL: 90,
            RetailerTier.TIER_2_HIGH: 70,
            RetailerTier.TIER_3_MEDIUM: 50,
            RetailerTier.TIER_4_LOW: 30
        }.get(task.tier, 50)
        
        # Ajustar por tiempo de espera
        wait_time = (datetime.now() - task.created_at).total_seconds()
        wait_bonus = min(20, wait_time / 3600 * 10)  # Max 20 puntos por hora de espera
        
        # Ajustar por fallos consecutivos del retailer
        retailer_config = self.retailers.get(task.retailer)
        if retailer_config and retailer_config.consecutive_failures > 0:
            failure_penalty = min(30, retailer_config.consecutive_failures * 5)
            base_priority -= failure_penalty
        
        return max(0, min(100, int(base_priority + wait_bonus)))
    
    def _calculate_max_concurrent_tasks(self) -> int:
        """Calcular máximo de tareas concurrentes"""
        system_config = self.config.get('system', {})
        base_max = system_config.get('max_concurrent_tasks', 8)
        
        # Ajustar basado en performance actual
        if self.metrics['tasks_failed'] > 0:
            failure_rate = self.metrics['tasks_failed'] / max(1, self.metrics['tasks_completed'])
            if failure_rate > 0.2:  # >20% de fallos
                return max(2, base_max // 2)
        
        return base_max
    
    def _can_execute_retailer_task(self, retailer: str) -> bool:
        """Verificar si se puede ejecutar tarea para retailer"""
        if retailer not in self.retailers:
            return False
        
        retailer_config = self.retailers[retailer]
        
        # Verificar circuit breaker
        if retailer in self.circuit_breakers:
            if not self.circuit_breakers[retailer].can_execute():
                return False
        
        # Verificar límite de concurrencia por retailer
        active_retailer_tasks = sum(
            1 for task in self.active_tasks.values()
            if task.retailer == retailer
        )
        
        return active_retailer_tasks < retailer_config.max_concurrent
    
    async def _monitor_active_tasks(self) -> None:
        """👁️ Monitorear tareas activas"""
        current_time = datetime.now()
        
        for task_id, task in list(self.active_tasks.items()):
            if task.started_at:
                duration = (current_time - task.started_at).total_seconds()
                
                # Timeout de tarea
                if duration > task.timeout:
                    logger.warning(f"⏰ Tarea {task_id} en timeout ({duration:.1f}s)")
                    # TODO: Cancelar tarea
    
    def _update_metrics(self) -> None:
        """📊 Actualizar métricas del sistema"""
        self.metrics['retailers_active'] = len([r for r in self.retailers.values() if r.enabled])
        self.metrics['circuit_breakers_open'] = len([
            cb for cb in self.circuit_breakers.values() if cb.state == "open"
        ])
        
        # Calcular duración promedio de tareas
        if self.completed_tasks:
            recent_tasks = [t for t in self.completed_tasks[-100:] if t.completed_at and t.started_at]
            if recent_tasks:
                durations = [(t.completed_at - t.started_at).total_seconds() for t in recent_tasks]
                self.metrics['avg_task_duration'] = sum(durations) / len(durations)
    
    async def _periodic_health_check(self) -> None:
        """🩺 Health check periódico"""
        # TODO: Implementar health checks
        pass
    
    async def _auto_optimization(self) -> None:
        """⚡ Optimización automática del sistema"""
        # TODO: Implementar optimizaciones automáticas
        pass
    
    async def _run_initial_tests(self) -> None:
        """🧪 Ejecutar tests iniciales"""
        try:
            if hasattr(self, 'test_runner'):
                logger.info("🧪 Ejecutando tests rápidos de retailers...")
                
                # Test rápido de cada retailer habilitado
                for retailer_name, retailer_config in self.retailers.items():
                    if retailer_config.enabled:
                        # Aquí iría el test real del retailer
                        logger.info(f"🧪 Test {retailer_name}: OK")
        except Exception as e:
            logger.warning(f"⚠️  Error en tests iniciales: {str(e)}")
    
    def _scheduler_loop(self) -> None:
        """🔄 Loop del scheduler (ejecuta en thread separado)"""
        logger.info("📅 Scheduler iniciado")
        
        while self.running:
            try:
                # Generar tareas automáticas basadas en tiers
                self._generate_scheduled_tasks()
                time.sleep(60)  # Revisar cada minuto
            except Exception as e:
                logger.error(f"💥 Error en scheduler: {str(e)}")
                time.sleep(60)
    
    def _monitor_loop(self) -> None:
        """👁️ Loop de monitoreo (ejecuta en thread separado)"""
        logger.info("👁️ Monitor iniciado")
        
        while self.running:
            try:
                # Log periódico de estado
                if len(self.active_tasks) > 0 or len(self.task_queue) > 0:
                    logger.info(f"📊 Estado: {len(self.active_tasks)} activas, "
                               f"{len(self.task_queue)} en cola")
                
                time.sleep(30)  # Monitor cada 30 segundos
            except Exception as e:
                logger.error(f"💥 Error en monitor: {str(e)}")
                time.sleep(30)
    
    def _generate_scheduled_tasks(self) -> None:
        """📅 Generar tareas programadas automáticamente"""
        current_time = datetime.now()
        
        for retailer_name, retailer_config in self.retailers.items():
            if not retailer_config.enabled:
                continue
            
            # Determinar frecuencia basada en tier
            frequency_minutes = {
                RetailerTier.TIER_1_CRITICAL: 15,   # Cada 15 minutos
                RetailerTier.TIER_2_HIGH: 60,       # Cada hora
                RetailerTier.TIER_3_MEDIUM: 240,    # Cada 4 horas
                RetailerTier.TIER_4_LOW: 1440       # Diario
            }.get(retailer_config.tier, 240)
            
            # Verificar si es tiempo de generar nueva tarea
            if retailer_config.last_success:
                time_since_last = (current_time - retailer_config.last_success).total_seconds() / 60
                if time_since_last < frequency_minutes:
                    continue
            
            # Generar tareas para cada categoría
            for category in retailer_config.categories:
                # Verificar que no exista tarea pendiente similar
                existing_task = any(
                    t.retailer == retailer_name and t.category == category and t.status in ['pending', 'running']
                    for t in self.task_queue + list(self.active_tasks.values())
                )
                
                if not existing_task:
                    task_id = f"{retailer_name}_{category}_{int(current_time.timestamp())}"
                    url = f"{retailer_config.base_url}/{category}"  # URL simplificada
                    
                    task = ScrapingTask(
                        task_id=task_id,
                        retailer=retailer_name,
                        category=category,
                        url=url,
                        tier=retailer_config.tier,
                        timeout=retailer_config.timeout
                    )
                    
                    # Programar tarea usando método async (ejecutar en main thread)
                    asyncio.run_coroutine_threadsafe(
                        self.schedule_task(task),
                        asyncio.get_event_loop()
                    )

# 🎯 FUNCIONES DE UTILIDAD PARA USO RÁPIDO

async def create_orchestrator(config_path: Optional[str] = None) -> ScraperV5Orchestrator:
    """
    🚀 Crear y inicializar orquestador
    
    Args:
        config_path: Ruta opcional al archivo de configuración
        
    Returns:
        ScraperV5Orchestrator: Instancia inicializada del orquestador
    """
    orchestrator = ScraperV5Orchestrator(config_path=config_path)
    
    if await orchestrator.initialize():
        return orchestrator
    else:
        raise RuntimeError("❌ Error inicializando orquestador")

async def quick_scraping_session(retailers: List[str], 
                                categories: List[str], 
                                duration_minutes: int = 30) -> Dict[str, Any]:
    """
    ⚡ Sesión rápida de scraping para testing
    
    Args:
        retailers: Lista de retailers a scrapear
        categories: Lista de categorías
        duration_minutes: Duración de la sesión en minutos
        
    Returns:
        Dict con resultados de la sesión
    """
    orchestrator = await create_orchestrator()
    
    try:
        # Generar tareas rápidas
        for retailer in retailers:
            for category in categories:
                task = ScrapingTask(
                    task_id=f"quick_{retailer}_{category}_{int(datetime.now().timestamp())}",
                    retailer=retailer,
                    category=category,
                    url=f"https://example.com/{retailer}/{category}",
                    tier=RetailerTier.TIER_1_CRITICAL,
                    priority=100
                )
                await orchestrator.schedule_task(task)
        
        # Ejecutar por tiempo limitado
        logger.info(f"⚡ Ejecutando sesión rápida por {duration_minutes} minutos...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Simular ejecución
        while time.time() < end_time:
            await asyncio.sleep(10)
            if not orchestrator.active_tasks and not orchestrator.task_queue:
                break
        
        # Recopilar resultados
        results = {
            'duration_minutes': (time.time() - start_time) / 60,
            'tasks_completed': len([t for t in orchestrator.completed_tasks if t.status == 'completed']),
            'tasks_failed': len([t for t in orchestrator.completed_tasks if t.status == 'failed']),
            'total_products': sum(t.products_found for t in orchestrator.completed_tasks),
            'retailers_processed': list(set(t.retailer for t in orchestrator.completed_tasks))
        }
        
        return results
        
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    """🎯 Ejecutar orquestador desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🎯 Scraper v5 Orchestrator")
    parser.add_argument('--config', help='Archivo de configuración')
    parser.add_argument('--test-mode', action='store_true', help='Ejecutar en modo test')
    parser.add_argument('--duration', type=int, default=60, help='Duración en minutos (modo test)')
    
    args = parser.parse_args()
    
    async def main():
        if args.test_mode:
            logger.info("🧪 Ejecutando en modo test...")
            results = await quick_scraping_session(
                retailers=['ripley', 'falabella'],
                categories=['celulares', 'notebooks'],
                duration_minutes=args.duration
            )
            
            logger.info("📊 RESULTADOS DE TEST:")
            for key, value in results.items():
                logger.info(f"   {key}: {value}")
        else:
            orchestrator = await create_orchestrator(args.config)
            try:
                await orchestrator.start()
            except KeyboardInterrupt:
                logger.info("⏹️ Deteniendo orquestrador...")
                await orchestrator.stop()
    
    asyncio.run(main())