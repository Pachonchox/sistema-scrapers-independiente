# -*- coding: utf-8 -*-
"""
📅 ArbitrageScheduler V5 - Planificador Inteligente Autónomo
===========================================================
Scheduler avanzado integrado con inteligencia V5 para operación continua.
Compatible con tiers dinámicos y optimización predictiva.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

from ..config.arbitrage_config import ArbitrageConfigV5

logger = logging.getLogger(__name__)

@dataclass
class ScheduleTask:
    """Tarea del scheduler con inteligencia V5 📋"""
    task_id: str
    task_type: str
    tier_classification: str
    frequency_minutes: int
    next_run: datetime
    last_run: Optional[datetime] = None
    enabled: bool = True
    priority: int = 3
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ArbitrageSchedulerV5:
    """
    Scheduler V5 con inteligencia avanzada 📅
    
    Funcionalidades:
    - 🧠 Scheduling basado en tiers dinámicos
    - ⚡ Optimización predictiva de frecuencias
    - 🎯 Priorización inteligente de tareas
    - 📊 Métricas y ajuste automático
    - 🔄 Auto-recovery y resiliencia
    """
    
    def __init__(self, config: ArbitrageConfigV5, engine=None, frequency_optimizer=None):
        """Inicializar scheduler V5"""
        self.config = config
        self.engine = engine  # Referencia al ArbitrageEngine
        self.frequency_optimizer = frequency_optimizer
        
        # Estado del scheduler
        self.is_running = False
        self.tasks: Dict[str, ScheduleTask] = {}
        self.scheduler_loop_task = None
        
        # Métricas
        self.metrics = {
            'tasks_scheduled': 0,
            'tasks_executed': 0,
            'tasks_failed': 0,
            'avg_execution_time': 0.0,
            'last_optimization': None,
            'frequency_adjustments': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("📅 ArbitrageScheduler V5 inicializado")
    
    async def initialize(self):
        """Inicializar scheduler con tareas base 🔧"""
        try:
            logger.info("🔧 Inicializando ArbitrageScheduler V5...")
            
            # Crear tareas base por tier
            await self._create_base_tasks()
            
            # Cargar tareas persistidas (si existen)
            await self._load_persisted_tasks()
            
            logger.info(f"✅ Scheduler inicializado con {len(self.tasks)} tareas")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando scheduler: {e}")
            raise
    
    async def _create_base_tasks(self):
        """Crear tareas base por tier 📋"""
        try:
            base_tasks = [
                {
                    'task_id': 'arbitrage_critical',
                    'task_type': 'full_arbitrage_cycle',
                    'tier_classification': 'critical',
                    'frequency_minutes': self.config.critical_tier_frequency,
                    'priority': 1
                },
                {
                    'task_id': 'arbitrage_important',
                    'task_type': 'full_arbitrage_cycle', 
                    'tier_classification': 'important',
                    'frequency_minutes': self.config.important_tier_frequency,
                    'priority': 2
                },
                {
                    'task_id': 'arbitrage_tracking',
                    'task_type': 'full_arbitrage_cycle',
                    'tier_classification': 'tracking', 
                    'frequency_minutes': self.config.tracking_tier_frequency,
                    'priority': 3
                },
                {
                    'task_id': 'metrics_update',
                    'task_type': 'update_metrics',
                    'tier_classification': 'system',
                    'frequency_minutes': 60,  # Cada hora
                    'priority': 4
                },
                {
                    'task_id': 'frequency_optimization',
                    'task_type': 'optimize_frequencies',
                    'tier_classification': 'optimization',
                    'frequency_minutes': 240,  # Cada 4 horas
                    'priority': 5
                }
            ]
            
            for task_config in base_tasks:
                task = ScheduleTask(
                    task_id=task_config['task_id'],
                    task_type=task_config['task_type'],
                    tier_classification=task_config['tier_classification'],
                    frequency_minutes=task_config['frequency_minutes'],
                    next_run=datetime.now() + timedelta(minutes=1),  # Empezar pronto
                    priority=task_config['priority'],
                    metadata={
                        'created_by': 'scheduler_v5',
                        'auto_generated': True
                    }
                )
                
                self.tasks[task.task_id] = task
                self.metrics['tasks_scheduled'] += 1
            
            logger.info(f"📋 Creadas {len(base_tasks)} tareas base")
            
        except Exception as e:
            logger.error(f"❌ Error creando tareas base: {e}")
    
    async def _load_persisted_tasks(self):
        """Cargar tareas persistidas desde BD (si existen) 💾"""
        try:
            # Por ahora, usar tareas base únicamente
            # En futuro se puede implementar persistencia en BD
            logger.debug("💾 Carga de tareas persistidas - usando configuración base")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cargando tareas persistidas: {e}")
    
    async def start(self):
        """Iniciar scheduler en modo continuo 🚀"""
        if self.is_running:
            logger.warning("⚠️ Scheduler ya está ejecutándose")
            return
        
        try:
            logger.info("🚀 Iniciando ArbitrageScheduler V5...")
            
            self.is_running = True
            
            # Iniciar loop principal del scheduler
            self.scheduler_loop_task = asyncio.create_task(self._scheduler_loop())
            
            logger.info("✅ Scheduler V5 iniciado - Operación continua activada")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando scheduler: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Detener scheduler limpiamente 🛑"""
        try:
            logger.info("🛑 Deteniendo ArbitrageScheduler V5...")
            
            self.is_running = False
            
            # Cancelar loop principal
            if self.scheduler_loop_task and not self.scheduler_loop_task.done():
                self.scheduler_loop_task.cancel()
                try:
                    await self.scheduler_loop_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("✅ Scheduler V5 detenido correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo scheduler: {e}")
    
    async def _scheduler_loop(self):
        """Loop principal del scheduler 🔄"""
        logger.info("🔄 Loop scheduler V5 iniciado")
        
        try:
            while self.is_running:
                try:
                    # Obtener tareas pendientes
                    pending_tasks = await self._get_pending_tasks()
                    
                    if pending_tasks:
                        logger.info(f"📋 Ejecutando {len(pending_tasks)} tareas pendientes")
                        
                        # Ejecutar tareas por prioridad
                        for task in sorted(pending_tasks, key=lambda t: t.priority):
                            if not self.is_running:
                                break
                            
                            try:
                                await self._execute_task(task)
                            except Exception as e:
                                logger.error(f"❌ Error ejecutando tarea {task.task_id}: {e}")
                                self.metrics['tasks_failed'] += 1
                    
                    # Optimización periódica si está habilitada
                    await self._periodic_optimization()
                    
                    # Actualizar métricas
                    self.metrics['timestamp'] = datetime.now().isoformat()
                    
                    # Esperar antes del siguiente ciclo
                    await asyncio.sleep(30)  # Check cada 30 segundos
                    
                except Exception as e:
                    logger.error(f"❌ Error en loop scheduler: {e}")
                    await asyncio.sleep(60)  # Esperar más tras error
                    
        except asyncio.CancelledError:
            logger.info("🛑 Loop scheduler cancelado")
        except Exception as e:
            logger.error(f"❌ Error crítico en loop scheduler: {e}")
        finally:
            logger.info("🔚 Loop scheduler finalizado")
    
    async def _get_pending_tasks(self) -> List[ScheduleTask]:
        """Obtener tareas pendientes de ejecución 📋"""
        try:
            current_time = datetime.now()
            pending = []
            
            for task in self.tasks.values():
                if (task.enabled and 
                    task.next_run <= current_time):
                    pending.append(task)
            
            return pending
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo tareas pendientes: {e}")
            return []
    
    async def _execute_task(self, task: ScheduleTask):
        """Ejecutar tarea individual 🎯"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🎯 Ejecutando tarea: {task.task_id} ({task.tier_classification})")
            
            # Ejecutar según tipo de tarea
            if task.task_type == 'full_arbitrage_cycle':
                await self._execute_arbitrage_cycle(task)
            elif task.task_type == 'update_metrics':
                await self._execute_metrics_update(task)
            elif task.task_type == 'optimize_frequencies':
                await self._execute_frequency_optimization(task)
            else:
                logger.warning(f"⚠️ Tipo de tarea desconocido: {task.task_type}")
                return
            
            # Actualizar estadísticas de la tarea
            task.last_run = start_time
            task.next_run = start_time + timedelta(minutes=task.frequency_minutes)
            
            # Métricas
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics['tasks_executed'] += 1
            
            # Actualizar promedio de tiempo de ejecución
            current_avg = self.metrics['avg_execution_time']
            total_executed = self.metrics['tasks_executed']
            self.metrics['avg_execution_time'] = (
                (current_avg * (total_executed - 1) + execution_time) / total_executed
            )
            
            logger.info(f"✅ Tarea {task.task_id} completada en {execution_time:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando tarea {task.task_id}: {e}")
            
            # Reagendar con delay en caso de error
            task.next_run = datetime.now() + timedelta(minutes=5)
            self.metrics['tasks_failed'] += 1
            raise
    
    async def _execute_arbitrage_cycle(self, task: ScheduleTask):
        """Ejecutar ciclo de arbitraje 🔄"""
        try:
            if not self.engine:
                logger.warning("⚠️ No hay engine disponible para ejecutar ciclo")
                return
            
            # Ejecutar ciclo completo
            cycle_result = await self.engine.run_arbitrage_cycle()
            
            # Actualizar metadata de la tarea
            task.metadata.update({
                'last_cycle_result': {
                    'success': cycle_result.get('success', False),
                    'opportunities_detected': cycle_result.get('opportunities_detected', 0),
                    'duration_seconds': cycle_result.get('duration_seconds', 0)
                },
                'last_execution': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo arbitraje para tarea {task.task_id}: {e}")
            raise
    
    async def _execute_metrics_update(self, task: ScheduleTask):
        """Actualizar métricas del sistema 📊"""
        try:
            if not self.engine:
                return
            
            # Obtener métricas del engine
            engine_status = await self.engine.get_engine_status()
            
            # Actualizar metadata
            task.metadata.update({
                'last_metrics': {
                    'engine_cycles': engine_status.get('metrics', {}).get('total_cycles', 0),
                    'opportunities_detected': engine_status.get('metrics', {}).get('total_opportunities_detected', 0),
                    'success_rate': self._calculate_success_rate(engine_status)
                },
                'last_execution': datetime.now().isoformat()
            })
            
            logger.debug(f"📊 Métricas actualizadas para {task.task_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando métricas: {e}")
    
    async def _execute_frequency_optimization(self, task: ScheduleTask):
        """Optimizar frecuencias basado en performance 🎯"""
        try:
            if not self.frequency_optimizer:
                logger.debug("🎯 Frequency optimizer no disponible")
                return
            
            logger.info("🔧 Ejecutando optimización de frecuencias...")
            
            # Analizar performance de tareas
            optimization_performed = False
            
            for task_id, monitored_task in self.tasks.items():
                if monitored_task.task_type == 'full_arbitrage_cycle':
                    try:
                        # Obtener métricas de la tarea
                        last_result = monitored_task.metadata.get('last_cycle_result', {})
                        
                        if last_result:
                            # Determinar si ajustar frecuencia
                            should_adjust, new_frequency = await self._analyze_frequency_adjustment(
                                monitored_task, last_result
                            )
                            
                            if should_adjust and new_frequency != monitored_task.frequency_minutes:
                                logger.info(f"🔧 Ajustando frecuencia {task_id}: "
                                           f"{monitored_task.frequency_minutes}min → {new_frequency}min")
                                
                                monitored_task.frequency_minutes = new_frequency
                                # Reagendar próxima ejecución
                                monitored_task.next_run = datetime.now() + timedelta(minutes=new_frequency)
                                
                                optimization_performed = True
                                self.metrics['frequency_adjustments'] += 1
                    
                    except Exception as e:
                        logger.debug(f"⚠️ Error optimizando {task_id}: {e}")
            
            # Actualizar metadata
            task.metadata.update({
                'last_optimization': datetime.now().isoformat(),
                'optimization_performed': optimization_performed,
                'tasks_analyzed': len([t for t in self.tasks.values() if t.task_type == 'full_arbitrage_cycle'])
            })
            
            if optimization_performed:
                self.metrics['last_optimization'] = datetime.now().isoformat()
                logger.info("✅ Optimización de frecuencias completada")
            else:
                logger.debug("📊 No se requieren ajustes de frecuencia")
            
        except Exception as e:
            logger.error(f"❌ Error en optimización de frecuencias: {e}")
    
    async def _analyze_frequency_adjustment(self, task: ScheduleTask, last_result: Dict[str, Any]) -> tuple[bool, int]:
        """Analizar si ajustar frecuencia de tarea 🔍"""
        try:
            current_frequency = task.frequency_minutes
            
            # Factores para ajuste
            opportunities_detected = last_result.get('opportunities_detected', 0)
            success = last_result.get('success', False)
            duration = last_result.get('duration_seconds', 0)
            
            # Lógica de ajuste básica
            if not success:
                # Si falló, reducir frecuencia (ejecutar menos seguido)
                new_frequency = min(current_frequency * 1.5, current_frequency + 60)
                return True, int(new_frequency)
            
            elif opportunities_detected > 5:
                # Muchas oportunidades - ejecutar más frecuentemente
                new_frequency = max(current_frequency * 0.8, current_frequency - 30)
                return True, int(new_frequency)
            
            elif opportunities_detected == 0 and duration < 10:
                # Sin oportunidades y rápido - reducir frecuencia
                new_frequency = min(current_frequency * 1.2, current_frequency + 30)
                return True, int(new_frequency)
            
            # No cambios necesarios
            return False, current_frequency
            
        except Exception as e:
            logger.debug(f"⚠️ Error analizando ajuste frecuencia: {e}")
            return False, task.frequency_minutes
    
    async def _periodic_optimization(self):
        """Optimización periódica del scheduler 🔧"""
        try:
            # Ejecutar cada 30 minutos
            if not hasattr(self, '_last_periodic_optimization'):
                self._last_periodic_optimization = datetime.now()
                return
            
            if (datetime.now() - self._last_periodic_optimization).total_seconds() < 1800:  # 30 min
                return
            
            logger.debug("🔧 Ejecutando optimización periódica...")
            
            # Limpiar tareas deshabilitadas
            disabled_tasks = [task_id for task_id, task in self.tasks.items() if not task.enabled]
            for task_id in disabled_tasks:
                del self.tasks[task_id]
                logger.debug(f"🗑️ Tarea deshabilitada eliminada: {task_id}")
            
            # Actualizar timestamp
            self._last_periodic_optimization = datetime.now()
            
        except Exception as e:
            logger.debug(f"⚠️ Error en optimización periódica: {e}")
    
    def _calculate_success_rate(self, engine_status: Dict[str, Any]) -> float:
        """Calcular tasa de éxito 📈"""
        try:
            metrics = engine_status.get('metrics', {})
            total_cycles = metrics.get('total_cycles', 0)
            successful_cycles = metrics.get('successful_cycles', 0)
            
            if total_cycles > 0:
                return successful_cycles / total_cycles
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    async def add_task(self, task: ScheduleTask):
        """Agregar tarea personalizada 📝"""
        try:
            self.tasks[task.task_id] = task
            self.metrics['tasks_scheduled'] += 1
            
            logger.info(f"📝 Tarea agregada: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error agregando tarea: {e}")
    
    async def remove_task(self, task_id: str):
        """Remover tarea 🗑️"""
        try:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f"🗑️ Tarea removida: {task_id}")
            else:
                logger.warning(f"⚠️ Tarea no encontrada: {task_id}")
                
        except Exception as e:
            logger.error(f"❌ Error removiendo tarea: {e}")
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Obtener estado del scheduler 📊"""
        try:
            return {
                'is_running': self.is_running,
                'total_tasks': len(self.tasks),
                'enabled_tasks': len([t for t in self.tasks.values() if t.enabled]),
                'tasks': {
                    task_id: {
                        'tier_classification': task.tier_classification,
                        'frequency_minutes': task.frequency_minutes,
                        'next_run': task.next_run.isoformat(),
                        'last_run': task.last_run.isoformat() if task.last_run else None,
                        'priority': task.priority,
                        'enabled': task.enabled
                    }
                    for task_id, task in self.tasks.items()
                },
                'metrics': self.metrics.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado scheduler: {e}")
            return {'error': str(e)}
    
    async def close(self):
        """Cerrar scheduler 🔚"""
        try:
            await self.stop()
            logger.info("🔚 ArbitrageScheduler V5 cerrado")
        except Exception as e:
            logger.error(f"❌ Error cerrando scheduler: {e}")