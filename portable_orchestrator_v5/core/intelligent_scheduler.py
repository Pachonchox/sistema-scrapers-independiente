#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧠 INTELLIGENT SCHEDULER V5
============================
Scheduler inteligente para operación continua 24/7 con anti-detección

Características:
- ✅ Coordinación de tiers con randomización temporal
- ✅ Load balancing dinámico entre retailers
- ✅ Patrones anti-detección inteligentes
- ✅ Gestión de recursos y concurrencia
- ✅ Recovery automático ante fallos
- ✅ Métricas y monitoring en tiempo real
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from .advanced_tier_manager import AdvancedTierManager, CategorySchedule
from .anti_detection_system import AntiDetectionSystem
from .emoji_support import force_emoji_support

force_emoji_support()
logger = logging.getLogger(__name__)

class SchedulerState(Enum):
    """Estados del scheduler"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class ExecutionTask:
    """Tarea de ejecución programada"""
    task_id: str
    retailer: str
    category: str
    tier: str
    scheduled_time: datetime
    priority: float
    pages_to_scrape: int
    anti_detection_config: Dict[str, Any]
    retries_left: int = 3
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    
@dataclass
class ResourceManager:
    """Gestor de recursos del sistema"""
    max_concurrent_scrapers: int = 3
    max_concurrent_per_retailer: int = 1  
    current_load: int = 0
    retailer_load: Dict[str, int] = field(default_factory=dict)
    last_resource_check: datetime = field(default_factory=datetime.now)

class IntelligentScheduler:
    """🧠 Scheduler inteligente V5"""
    
    def __init__(self, scraper_callback: Optional[Callable] = None):
        """Inicializar scheduler inteligente"""
        
        # Componentes principales
        self.tier_manager = AdvancedTierManager()
        self.anti_detection = AntiDetectionSystem()
        self.scraper_callback = scraper_callback  # Función para ejecutar scraping
        
        # Estado del scheduler
        self.state = SchedulerState.IDLE
        self.start_time = datetime.now()
        self.running = False
        
        # Cola de tareas y gestión
        self.task_queue: List[ExecutionTask] = []
        self.executing_tasks: Dict[str, ExecutionTask] = {}
        self.completed_tasks: List[ExecutionTask] = []
        
        # Gestión de recursos
        self.resource_manager = ResourceManager()
        
        # Configuración de operación continua
        self.continuous_config = {
            'max_runtime_hours': 24 * 30,  # 30 días por defecto
            'maintenance_window_hour': 4,   # Mantenimiento a las 4 AM
            'maintenance_duration_minutes': 30,
            'health_check_interval_minutes': 15,
            'metrics_save_interval_minutes': 10,
            'session_break_probability': 0.05,  # 5% probabilidad por hora
            'pattern_evolution_hours': 168,  # Evolucionar patrones cada semana
        }
        
        # Métricas y monitoring
        self.metrics = {
            'total_tasks_executed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_products_scraped': 0,
            'average_task_duration': 0.0,
            'uptime_percentage': 100.0,
            'retailers_performance': {},
            'tiers_performance': {},
            'anti_detection_effectiveness': 0.0
        }
        
        # Persistencia
        self.state_file = Path("data/intelligent_scheduler_state.json")
        
        logger.info("🧠 Intelligent Scheduler V5 inicializado")
        self._initialize_system()
    
    def _initialize_system(self):
        """Inicializar componentes del sistema"""
        
        # Cargar configuración de proxies si existe
        proxy_file = Path("config/proxies.json")
        if proxy_file.exists():
            self.anti_detection.load_proxies_from_file(str(proxy_file))
        
        # Inicializar métricas por retailer
        retailers = ['falabella', 'paris', 'ripley', 'hites', 'abcdin']
        for retailer in retailers:
            self.resource_manager.retailer_load[retailer] = 0
            self.metrics['retailers_performance'][retailer] = {
                'tasks_executed': 0,
                'success_rate': 1.0,
                'avg_products_per_task': 0.0,
                'avg_execution_time': 0.0,
                'last_successful_execution': None
            }
        
        # Inicializar métricas por tier
        for tier in ['critical', 'important', 'tracking']:
            self.metrics['tiers_performance'][tier] = {
                'executions_today': 0,
                'success_rate': 1.0,
                'avg_execution_time': 0.0,
                'products_scraped': 0
            }
        
        logger.info("⚙️ Sistema inicializado correctamente")
        self._log_configuration_summary()
    
    def _log_configuration_summary(self):
        """Log de configuración del sistema"""
        logger.info("📊 Configuración Intelligent Scheduler:")
        logger.info(f"   🎯 Tiers configurados: {len(self.tier_manager.tiers)}")
        logger.info(f"   🛡️ Anti-detección: {len(self.anti_detection.user_agent_profiles)} UAs, {len(self.anti_detection.proxy_pool)} proxies")
        logger.info(f"   🔧 Recursos: max {self.resource_manager.max_concurrent_scrapers} scrapers concurrentes")
        logger.info(f"   ⏰ Runtime máximo: {self.continuous_config['max_runtime_hours']} horas")
        logger.info(f"   🔍 Health check: cada {self.continuous_config['health_check_interval_minutes']} min")
    
    async def start(self):
        """🚀 Iniciar el scheduler (alias para start_continuous_operation)"""
        await self.start_continuous_operation()
    
    async def stop(self):
        """🛑 Detener el scheduler de forma graceful"""
        logger.info("🛑 Deteniendo Intelligent Scheduler...")
        
        self.running = False
        self.state = SchedulerState.IDLE
        
        # Cancelar tareas pendientes
        for task in self.task_queue:
            if task.status == "pending":
                task.status = "cancelled"
        
        # Esperar que terminen las tareas en ejecución
        max_wait = 30  # 30 segundos máximo
        wait_count = 0
        
        while self.executing_tasks and wait_count < max_wait:
            logger.info(f"⏳ Esperando {len(self.executing_tasks)} tareas en ejecución...")
            await asyncio.sleep(1)
            wait_count += 1
        
        # Guardar estado final si existe el método
        if hasattr(self, '_save_scheduler_state'):
            try:
                await self._save_scheduler_state()
            except Exception as e:
                logger.debug(f"Error guardando estado: {e}")
        
        logger.info("✅ Intelligent Scheduler detenido correctamente")
    
    async def start_continuous_operation(self):
        """Iniciar operación continua 24/7"""
        logger.info("🚀 Iniciando operación continua 24/7")
        
        self.state = SchedulerState.RUNNING
        self.running = True
        self.start_time = datetime.now()
        
        try:
            # Tareas principales en paralelo (guardar referencias para cancelación)
            self._background_tasks = [
                asyncio.create_task(self._main_scheduling_loop()),
                asyncio.create_task(self._task_execution_loop()), 
                asyncio.create_task(self._health_monitoring_loop()),
                asyncio.create_task(self._metrics_collection_loop()),
                asyncio.create_task(self._maintenance_loop())
            ]
            
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Error crítico en operación continua: {e}")
            self.state = SchedulerState.ERROR
        finally:
            await self._shutdown_gracefully()
    
    async def _main_scheduling_loop(self):
        """Loop principal de programación de tareas"""
        logger.info("📅 Iniciando loop principal de scheduling")
        
        while self.running:
            try:
                # Verificar si hay tiers listos para ejecutar
                next_tier = self.tier_manager.get_next_tier_to_execute()
                
                if next_tier:
                    await self._schedule_tier_execution(next_tier)
                else:
                    # Calcular tiempo hasta próxima ejecución
                    wait_time = self._calculate_next_execution_time()
                    if wait_time > 0:
                        logger.info(f"😴 Esperando {wait_time/60:.1f} min hasta próxima tarea")
                        await asyncio.sleep(min(wait_time, 300))  # Max 5 min
                
                # Aplicar anti-detección ocasional
                if random.random() < self.continuous_config['session_break_probability'] / 60:
                    await self.anti_detection.session_break()
                
                # Pequeña pausa para evitar busy waiting
                await asyncio.sleep(random.uniform(5, 15))
                
            except Exception as e:
                logger.error(f"❌ Error en scheduling loop: {e}")
                await asyncio.sleep(30)  # Pausa en caso de error
    
    async def _schedule_tier_execution(self, tier_name: str):
        """Programar ejecución de un tier"""
        logger.info(f"📅 Programando ejecución de tier: {tier_name}")
        
        # Generar schedule del tier
        tier_schedule = self.tier_manager.generate_tier_schedule(tier_name)
        
        # Aplicar anti-detección y randomización
        tier_schedule = self._apply_anti_detection_to_schedule(tier_schedule)
        
        # Crear tareas de ejecución
        for schedule_item in tier_schedule:
            task = self._create_execution_task(schedule_item)
            self.task_queue.append(task)
        
        # Ordenar cola por prioridad y tiempo
        self.task_queue.sort(key=lambda t: (t.scheduled_time, -t.priority))
        
        logger.info(f"✅ {len(tier_schedule)} tareas programadas para tier {tier_name}")
    
    def _apply_anti_detection_to_schedule(self, schedule: List[CategorySchedule]) -> List[CategorySchedule]:
        """Aplicar técnicas de anti-detección al schedule"""
        
        # Randomizar orden manteniendo distribución temporal
        if len(schedule) > 2 and random.random() < 0.3:
            # Ocasionalmente cambiar orden de 2 tareas adyacentes
            idx = random.randint(0, len(schedule) - 2)
            schedule[idx], schedule[idx + 1] = schedule[idx + 1], schedule[idx]
        
        # Aplicar jitter temporal adicional
        for item in schedule:
            jitter_seconds = random.uniform(-30, 60)  # -30s a +60s
            item.scheduled_time += timedelta(seconds=jitter_seconds)
            
            # Configurar anti-detección específica
            item.randomization_applied.update({
                'temporal_jitter_applied': jitter_seconds,
                'pattern_break': random.random() < 0.1,  # 10% probabilidad
                'extended_delay': random.random() < 0.05  # 5% probabilidad
            })
        
        return schedule
    
    def _create_execution_task(self, schedule_item: CategorySchedule) -> ExecutionTask:
        """Crear tarea de ejecución desde schedule"""
        
        # Obtener configuración anti-detección
        user_agent_profile = self.anti_detection.get_random_user_agent()
        
        anti_detection_config = {
            'user_agent_profile': {
                'user_agent': user_agent_profile.user_agent,
                'browser': user_agent_profile.browser,
                'os': user_agent_profile.os
            },
            'headers': self.anti_detection.get_anti_detection_headers(user_agent_profile),
            'page_sequence': self.anti_detection.generate_page_sequence(10, schedule_item.pages_to_scrape),
            'scroll_behavior': self.anti_detection.apply_scroll_behavior(),
            'delays': {
                'page_load': self.anti_detection.get_human_delay('page_load_wait'),
                'between_pages': self.anti_detection.get_human_delay('between_clicks'),
                'category_switch': self.anti_detection.get_human_delay('category_change')
            },
            'proxy': None  # Se asignará dinámicamente
        }
        
        task_id = f"{schedule_item.retailer}_{schedule_item.category}_{schedule_item.scheduled_time.strftime('%H%M%S')}"
        
        return ExecutionTask(
            task_id=task_id,
            retailer=schedule_item.retailer,
            category=schedule_item.category,
            tier=schedule_item.tier,
            scheduled_time=schedule_item.scheduled_time,
            priority=schedule_item.priority,
            pages_to_scrape=schedule_item.pages_to_scrape,
            anti_detection_config=anti_detection_config
        )
    
    async def _task_execution_loop(self):
        """Loop de ejecución de tareas"""
        logger.info("⚡ Iniciando loop de ejecución de tareas")
        
        while self.running:
            try:
                # Verificar recursos disponibles
                if not self._has_available_resources():
                    await asyncio.sleep(10)
                    continue
                
                # Buscar próxima tarea lista
                ready_task = self._get_next_ready_task()
                
                if ready_task:
                    # Ejecutar tarea en background
                    asyncio.create_task(self._execute_task(ready_task))
                
                await asyncio.sleep(5)  # Verificar cada 5 segundos
                
            except Exception as e:
                logger.error(f"❌ Error en execution loop: {e}")
                await asyncio.sleep(15)
    
    def _has_available_resources(self) -> bool:
        """Verificar si hay recursos disponibles"""
        current_load = len(self.executing_tasks)
        return current_load < self.resource_manager.max_concurrent_scrapers
    
    def _get_next_ready_task(self) -> Optional[ExecutionTask]:
        """Obtener próxima tarea lista para ejecutar"""
        now = datetime.now()
        
        for i, task in enumerate(self.task_queue):
            # Verificar si es tiempo de ejecutar
            if task.scheduled_time <= now:
                # Verificar recursos por retailer
                retailer_load = self.resource_manager.retailer_load.get(task.retailer, 0)
                if retailer_load < self.resource_manager.max_concurrent_per_retailer:
                    # Remover de cola y retornar
                    return self.task_queue.pop(i)
        
        return None
    
    async def _execute_task(self, task: ExecutionTask):
        """Ejecutar una tarea de scraping"""
        task.status = "running"
        self.executing_tasks[task.task_id] = task
        self.resource_manager.current_load += 1
        self.resource_manager.retailer_load[task.retailer] += 1
        
        start_time = datetime.now()
        
        logger.info(f"▶️ Ejecutando: {task.retailer}/{task.category} (tier: {task.tier})")
        
        try:
            # Asignar proxy si está disponible
            proxy = await self.anti_detection.get_working_proxy()
            if proxy:
                task.anti_detection_config['proxy'] = {
                    'host': proxy.host,
                    'port': proxy.port,
                    'username': proxy.username,
                    'password': proxy.password
                }
            
            # Ejecutar scraping (callback proporcionado)
            if self.scraper_callback:
                result = await self.scraper_callback(task)
            else:
                # Simulación para testing
                await asyncio.sleep(random.uniform(30, 120))
                result = {
                    'success': True,
                    'products_found': random.randint(15, 45),
                    'pages_scraped': task.pages_to_scrape,
                    'execution_time_minutes': random.uniform(1, 3)
                }
            
            # Procesar resultado
            task.result = result
            task.status = "completed" if result.get('success', False) else "failed"
            
            # Actualizar métricas
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            self._update_task_metrics(task, execution_time)
            
            # Actualizar tier manager
            self.tier_manager.update_tier_execution(task.tier, result)
            
            # Actualizar anti-detección
            self.anti_detection.update_metrics('request', result.get('success', False))
            
            logger.info(f"✅ Completado: {task.retailer}/{task.category} - "
                       f"{result.get('products_found', 0)} productos en {execution_time:.1f} min")
        
        except Exception as e:
            task.status = "failed"
            task.result = {'success': False, 'error': str(e)}
            logger.error(f"❌ Error ejecutando {task.retailer}/{task.category}: {e}")
            
            # Programar reintento si quedan intentos
            if task.retries_left > 0:
                task.retries_left -= 1
                task.scheduled_time = datetime.now() + timedelta(minutes=random.uniform(5, 15))
                task.status = "pending"
                self.task_queue.append(task)
                logger.info(f"🔄 Reintento programado para {task.task_id} ({task.retries_left} intentos restantes)")
        
        finally:
            # Liberar recursos
            if task.task_id in self.executing_tasks:
                del self.executing_tasks[task.task_id]
            self.resource_manager.current_load -= 1
            self.resource_manager.retailer_load[task.retailer] -= 1
            
            # Mover a completadas
            self.completed_tasks.append(task)
            
            # Mantener historial limitado
            if len(self.completed_tasks) > 200:
                self.completed_tasks = self.completed_tasks[-150:]
    
    def set_scraping_callback(self, callback: Callable):
        """🔗 Configurar callback de scraping"""
        self.scraper_callback = callback
        logger.info("🔗 Callback de scraping configurado")
    
    def get_status(self) -> Dict[str, Any]:
        """📊 Obtener estado completo del scheduler"""
        return self.get_status_summary()
    
    def _update_task_metrics(self, task: ExecutionTask, execution_time: float):
        """Actualizar métricas de la tarea"""
        self.metrics['total_tasks_executed'] += 1
        
        if task.status == "completed":
            self.metrics['successful_tasks'] += 1
            products = task.result.get('products_found', 0)
            self.metrics['total_products_scraped'] += products
            
            # Actualizar métricas por retailer
            retailer_metrics = self.metrics['retailers_performance'][task.retailer]
            retailer_metrics['tasks_executed'] += 1
            retailer_metrics['last_successful_execution'] = datetime.now().isoformat()
            
            # Promedios móviles
            if retailer_metrics['avg_execution_time'] == 0:
                retailer_metrics['avg_execution_time'] = execution_time
                retailer_metrics['avg_products_per_task'] = products
            else:
                retailer_metrics['avg_execution_time'] = (
                    retailer_metrics['avg_execution_time'] * 0.8 + execution_time * 0.2
                )
                retailer_metrics['avg_products_per_task'] = (
                    retailer_metrics['avg_products_per_task'] * 0.8 + products * 0.2
                )
            
            # Actualizar tier
            tier_metrics = self.metrics['tiers_performance'][task.tier]
            tier_metrics['executions_today'] += 1
            tier_metrics['products_scraped'] += products
            
            if tier_metrics['avg_execution_time'] == 0:
                tier_metrics['avg_execution_time'] = execution_time
            else:
                tier_metrics['avg_execution_time'] = (
                    tier_metrics['avg_execution_time'] * 0.8 + execution_time * 0.2
                )
        
        else:
            self.metrics['failed_tasks'] += 1
        
        # Actualizar promedio general
        total_tasks = self.metrics['successful_tasks'] + self.metrics['failed_tasks']
        if total_tasks > 0:
            success_rate = self.metrics['successful_tasks'] / total_tasks
            self.metrics['anti_detection_effectiveness'] = success_rate
    
    def _calculate_next_execution_time(self) -> float:
        """Calcular tiempo hasta próxima ejecución"""
        if self.task_queue:
            next_task_time = min(task.scheduled_time for task in self.task_queue)
            return (next_task_time - datetime.now()).total_seconds()
        
        # Buscar próximo tier programado
        next_tier_times = []
        for tier_name, tier_execution in self.tier_manager.tier_executions.items():
            tier_config = self.tier_manager.tiers[tier_name]
            
            if tier_execution.last_run:
                next_run = tier_execution.last_run + timedelta(hours=tier_config.frequency_hours)
                next_tier_times.append(next_run)
            else:
                next_tier_times.append(datetime.now())  # Ejecutar inmediatamente
        
        if next_tier_times:
            next_time = min(next_tier_times)
            return (next_time - datetime.now()).total_seconds()
        
        return 300  # Default 5 minutos
    
    async def _health_monitoring_loop(self):
        """Loop de monitoreo de salud del sistema"""
        logger.info("🔍 Iniciando monitoreo de salud")
        
        interval = self.continuous_config['health_check_interval_minutes'] * 60
        
        while self.running:
            try:
                await asyncio.sleep(interval)
                await self._perform_health_check()
            except Exception as e:
                logger.error(f"❌ Error en health monitoring: {e}")
    
    async def _perform_health_check(self):
        """Realizar chequeo de salud del sistema"""
        logger.info("🔍 Realizando health check...")
        
        # Verificar proxies
        if self.anti_detection.proxy_pool:
            await self.anti_detection._health_check_proxies()
        
        # Calcular uptime
        uptime = (datetime.now() - self.start_time).total_seconds()
        running_time_ratio = min(1.0, uptime / (24 * 3600))  # Ratio respecto a 24h
        
        # Calcular métricas de salud
        total_tasks = self.metrics['successful_tasks'] + self.metrics['failed_tasks']
        success_rate = self.metrics['successful_tasks'] / max(total_tasks, 1)
        
        health_metrics = {
            'uptime_hours': uptime / 3600,
            'success_rate': success_rate,
            'tasks_in_queue': len(self.task_queue),
            'tasks_executing': len(self.executing_tasks),
            'working_proxies': len([p for p in self.anti_detection.proxy_pool if p.is_working]),
            'resource_utilization': self.resource_manager.current_load / self.resource_manager.max_concurrent_scrapers
        }
        
        logger.info("📊 Health Status:")
        logger.info(f"   ⏱️ Uptime: {health_metrics['uptime_hours']:.1f} horas")
        logger.info(f"   ✅ Success rate: {health_metrics['success_rate']:.1%}")
        logger.info(f"   📋 Cola: {health_metrics['tasks_in_queue']} tareas")
        logger.info(f"   ⚡ Ejecutando: {health_metrics['tasks_executing']}")
        logger.info(f"   🌐 Proxies activos: {health_metrics['working_proxies']}")
        logger.info(f"   🔧 Uso recursos: {health_metrics['resource_utilization']:.1%}")
        
        # Alertas de salud
        if success_rate < 0.8:
            logger.warning("⚠️ ALERTA: Tasa de éxito baja ({:.1%})".format(success_rate))
        
        if len(self.task_queue) > 50:
            logger.warning(f"⚠️ ALERTA: Cola de tareas grande ({len(self.task_queue)} tareas)")
        
        self.metrics['uptime_percentage'] = running_time_ratio * success_rate * 100
    
    async def _metrics_collection_loop(self):
        """Loop de recolección de métricas"""
        interval = self.continuous_config['metrics_save_interval_minutes'] * 60
        
        while self.running:
            try:
                await asyncio.sleep(interval)
                self._save_metrics()
            except Exception as e:
                logger.error(f"❌ Error en metrics collection: {e}")
    
    async def _maintenance_loop(self):
        """Loop de mantenimiento automático"""
        logger.info("🔧 Iniciando loop de mantenimiento")
        
        while self.running:
            try:
                now = datetime.now()
                
                # Ventana de mantenimiento (por defecto 4:00 AM)
                if (now.hour == self.continuous_config['maintenance_window_hour'] and 
                    now.minute < self.continuous_config['maintenance_duration_minutes']):
                    
                    await self._perform_maintenance()
                    
                    # Dormir hasta salir de ventana de mantenimiento
                    sleep_minutes = self.continuous_config['maintenance_duration_minutes'] - now.minute
                    await asyncio.sleep(sleep_minutes * 60)
                
                # Verificar cada hora
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"❌ Error en maintenance loop: {e}")
    
    async def _perform_maintenance(self):
        """Realizar mantenimiento automático"""
        logger.info("🔧 Iniciando mantenimiento automático")
        
        self.state = SchedulerState.MAINTENANCE
        
        # Limpiar tareas completadas antiguas
        cutoff_time = datetime.now() - timedelta(hours=24)
        initial_count = len(self.completed_tasks)
        self.completed_tasks = [
            task for task in self.completed_tasks 
            if task.scheduled_time > cutoff_time
        ]
        cleaned_tasks = initial_count - len(self.completed_tasks)
        
        # Reiniciar contadores diarios
        for tier_metrics in self.metrics['tiers_performance'].values():
            tier_metrics['executions_today'] = 0
        
        # Actualizar tier manager
        for tier_execution in self.tier_manager.tier_executions.values():
            tier_execution.executions_today = 0
        
        # Verificar salud de proxies
        if self.anti_detection.proxy_pool:
            await self.anti_detection._health_check_proxies()
        
        # Guardar estado
        self._save_state()
        self.tier_manager.save_state()
        
        logger.info(f"✅ Mantenimiento completado:")
        logger.info(f"   🗑️ {cleaned_tasks} tareas antiguas limpiadas")
        logger.info(f"   🔄 Contadores diarios reiniciados")
        logger.info(f"   💾 Estado guardado")
        
        self.state = SchedulerState.RUNNING
    
    def _save_metrics(self):
        """Guardar métricas a archivo"""
        try:
            metrics_file = Path("data/scheduler_metrics.json")
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics,
                'anti_detection_metrics': self.anti_detection.get_metrics_summary(),
                'tier_status': self.tier_manager.get_tier_status_summary(),
                'system_state': {
                    'state': self.state.value,
                    'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
                    'tasks_in_queue': len(self.task_queue),
                    'tasks_executing': len(self.executing_tasks)
                }
            }
            
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            logger.error(f"❌ Error guardando métricas: {e}")
    
    def _save_state(self):
        """Guardar estado del scheduler"""
        try:
            state_data = {
                'start_time': self.start_time.isoformat(),
                'metrics': self.metrics,
                'continuous_config': self.continuous_config,
                'task_queue_count': len(self.task_queue),
                'executing_tasks_count': len(self.executing_tasks),
                'completed_tasks_count': len(self.completed_tasks),
                'last_save': datetime.now().isoformat()
            }
            
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            logger.error(f"❌ Error guardando estado: {e}")
    
    async def _shutdown_gracefully(self):
        """Apagar el sistema graciosamente"""
        logger.info("🛑 Iniciando apagado gracioso...")
        
        self.state = SchedulerState.PAUSED
        
        # Cancelar tareas de fondo si siguen activas
        for t in getattr(self, '_background_tasks', []):
            if t and not t.done():
                t.cancel()
        if getattr(self, '_background_tasks', None):
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Esperar que terminen las tareas en ejecución
        max_wait_time = 300  # 5 minutos máximo
        wait_start = datetime.now()
        
        while self.executing_tasks and (datetime.now() - wait_start).seconds < max_wait_time:
            logger.info(f"⏳ Esperando {len(self.executing_tasks)} tareas en ejecución...")
            await asyncio.sleep(10)
        
        # Guardar estado final
        self._save_state()
        self._save_metrics()
        self.tier_manager.save_state()
        
        logger.info("✅ Apagado completado correctamente")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen de estado del scheduler"""
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return {
            'state': self.state.value,
            'uptime_hours': uptime,
            'metrics': self.metrics,
            'resource_usage': {
                'current_load': self.resource_manager.current_load,
                'max_capacity': self.resource_manager.max_concurrent_scrapers,
                'utilization_percentage': (self.resource_manager.current_load / self.resource_manager.max_concurrent_scrapers) * 100
            },
            'queues': {
                'pending_tasks': len(self.task_queue),
                'executing_tasks': len(self.executing_tasks),
                'completed_tasks': len(self.completed_tasks)
            },
            'anti_detection': self.anti_detection.get_metrics_summary(),
            'tiers': self.tier_manager.get_tier_status_summary()
        }
