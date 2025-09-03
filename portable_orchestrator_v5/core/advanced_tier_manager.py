#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 ADVANCED TIER MANAGER V5
===========================
Sistema de tiers optimizado para operación continua 24/7 con anti-detección avanzado

Características:
- ✅ Rotación temporal inteligente (2h, 6h, 24h)
- ✅ Páginas aleatorias distribuidas 
- ✅ Gestión de proxies con rotación
- ✅ Patrones anti-detección (jitter, delays variables)
- ✅ ML-assisted scheduling
- ✅ Load balancing dinámico
"""

import asyncio
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from .emoji_support import force_emoji_support
force_emoji_support()

logger = logging.getLogger(__name__)

@dataclass
class TierConfig:
    """Configuración avanzada de un tier"""
    name: str
    frequency_hours: int
    pages_range: Tuple[int, int]  # (min, max) páginas aleatorias
    priority: float
    jitter_percent: float = 15.0  # Variabilidad temporal
    max_concurrent: int = 2  # Scrapers concurrentes
    proxy_rotation: bool = True
    stealth_mode: bool = True
    
@dataclass  
class TierExecution:
    """Estado de ejecución de un tier"""
    tier_name: str
    last_run: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None
    executions_today: int = 0
    success_rate: float = 1.0
    avg_execution_time: float = 0.0
    pages_scraped_total: int = 0
    products_extracted: int = 0
    
@dataclass
class CategorySchedule:
    """Programación de una categoría específica"""
    retailer: str
    category: str
    url: str
    tier: str
    priority: float
    pages_to_scrape: int
    scheduled_time: datetime
    randomization_applied: Dict[str, Any] = field(default_factory=dict)

class AdvancedTierManager:
    """🎯 Gestor avanzado de tiers con anti-detección"""
    
    def __init__(self):
        """Inicializar tier manager avanzado"""
        
        # Configuración de tiers optimizada
        self.tiers = {
            'critical': TierConfig(
                name='critical',
                frequency_hours=2,
                pages_range=(2, 4),
                priority=0.9,
                jitter_percent=10.0,  # Menos variabilidad para tier crítico
                max_concurrent=3,
                proxy_rotation=True,
                stealth_mode=True
            ),
            'important': TierConfig(
                name='important', 
                frequency_hours=6,
                pages_range=(1, 3),
                priority=0.7,
                jitter_percent=15.0,
                max_concurrent=2,
                proxy_rotation=True,
                stealth_mode=True
            ),
            'tracking': TierConfig(
                name='tracking',
                frequency_hours=24,
                pages_range=(1, 2),
                priority=0.5,
                jitter_percent=20.0,  # Más variabilidad para tracking
                max_concurrent=1,
                proxy_rotation=False,  # Menos agresivo
                stealth_mode=False
            )
        }
        
        # Estado de ejecuciones
        self.tier_executions = {
            tier_name: TierExecution(tier_name) 
            for tier_name in self.tiers.keys()
        }
        
        # Configuración de categorías por tier
        self.tier_categories = self._load_tier_categories()
        
        # Sistema de programación
        self.schedule_queue: List[CategorySchedule] = []
        self.execution_history: List[Dict[str, Any]] = []
        
        # Anti-detección
        self.proxy_pool: List[str] = []
        self.user_agents: List[str] = self._load_user_agents()
        self.randomization_state = {
            'last_proxy_rotation': datetime.now(),
            'last_ua_rotation': datetime.now(),
            'pattern_break_counter': 0
        }
        
        # Persistencia de estado
        self.state_file = Path("data/tier_manager_state.json")
        self.load_state()
        
        logger.info("🎯 Advanced Tier Manager V5 inicializado")
        self._log_tier_summary()
    
    def _load_tier_categories(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Cargar categorías organizadas por tiers"""
        return {
            'critical': {
                # TIER 1 - Cada 2 horas: Tecnología Core
                'falabella': [
                    {'key': 'smartphones', 'url': 'https://www.falabella.com/falabella-cl/category/cat720161/Smartphones', 'priority': 0.95},
                    {'key': 'computadores', 'url': 'https://www.falabella.com/falabella-cl/category/cat40052/Computadores', 'priority': 0.9},
                    {'key': 'smart_tv', 'url': 'https://www.falabella.com/falabella-cl/category/cat7190148/Smart-TV', 'priority': 0.9}
                ],
                'paris': [
                    {'key': 'celulares', 'url': 'https://www.paris.cl/tecnologia/celulares/', 'priority': 0.95},
                    {'key': 'computadores', 'url': 'https://www.paris.cl/tecnologia/computadores/', 'priority': 0.9},
                    {'key': 'television', 'url': 'https://www.paris.cl/tecnologia/television/', 'priority': 0.9}
                ],
                'ripley': [
                    {'key': 'celulares', 'url': 'https://simple.ripley.cl/tecno/celulares', 'priority': 0.95},
                    {'key': 'computacion', 'url': 'https://simple.ripley.cl/tecno/computacion', 'priority': 0.9},
                    {'key': 'television', 'url': 'https://simple.ripley.cl/tecno/television', 'priority': 0.9}
                ],
                'hites': [
                    {'key': 'celulares', 'url': 'https://www.hites.com/celulares/smartphones/', 'priority': 0.9},
                    {'key': 'computadores', 'url': 'https://www.hites.com/computacion/notebooks/', 'priority': 0.85},
                    {'key': 'television', 'url': 'https://www.hites.com/television/smart-tv/', 'priority': 0.85}
                ],
                'abcdin': [
                    {'key': 'celulares', 'url': 'https://www.abc.cl/tecnologia/celulares/smartphones/', 'priority': 0.9},
                    {'key': 'computadores', 'url': 'https://www.abc.cl/tecnologia/computadores/notebooks/', 'priority': 0.85},
                    {'key': 'television', 'url': 'https://www.abc.cl/tecnologia/television/', 'priority': 0.85}
                ]
            },
            'important': {
                # TIER 2 - Cada 6 horas: Tecnología Complementaria  
                'falabella': [
                    {'key': 'tablets', 'url': 'https://www.falabella.com/falabella-cl/category/cat7230007/Tablets', 'priority': 0.7},
                    {'key': 'smartwatch', 'url': 'https://www.falabella.com/falabella-cl/category/cat4290063/SmartWatch', 'priority': 0.7},
                    {'key': 'consolas', 'url': 'https://www.falabella.com/falabella-cl/category/cat202303/Consolas', 'priority': 0.65}
                ],
                'paris': [
                    {'key': 'tablets', 'url': 'https://www.paris.cl/tecnologia/tablets/', 'priority': 0.7},
                    {'key': 'smartwatches', 'url': 'https://www.paris.cl/tecnologia/wearables/smartwatches/', 'priority': 0.7},
                    {'key': 'gaming', 'url': 'https://www.paris.cl/tecnologia/gaming/', 'priority': 0.65}
                ],
                'ripley': [
                    {'key': 'tablets', 'url': 'https://simple.ripley.cl/tecno/tablets', 'priority': 0.7},
                    {'key': 'smartwatches', 'url': 'https://simple.ripley.cl/tecno/smartwatches-y-smartbands', 'priority': 0.7},
                    {'key': 'gaming', 'url': 'https://simple.ripley.cl/tecno/gaming', 'priority': 0.65}
                ],
                'hites': [
                    {'key': 'tablets', 'url': 'https://www.hites.com/celulares/tablets/', 'priority': 0.65}
                ],
                'abcdin': [
                    {'key': 'tablets', 'url': 'https://www.abc.cl/tecnologia/tablets/', 'priority': 0.65}
                ]
            },
            'tracking': {
                # TIER 3 - Cada 24 horas: Seguimiento Histórico
                'falabella': [
                    {'key': 'parlantes', 'url': 'https://www.falabella.com/falabella-cl/category/cat3171/Parlantes-bluetooth', 'priority': 0.5},
                    {'key': 'monitores', 'url': 'https://www.falabella.com/falabella-cl/category/cat2062/Monitores', 'priority': 0.5}
                ],
                'paris': [
                    {'key': 'audio', 'url': 'https://www.paris.cl/tecnologia/audio/', 'priority': 0.5},
                    {'key': 'accesorios', 'url': 'https://www.paris.cl/tecnologia/accesorios-tecnologia/', 'priority': 0.45}
                ],
                'ripley': [
                    {'key': 'audio', 'url': 'https://simple.ripley.cl/tecno/audio', 'priority': 0.5},
                    {'key': 'accesorios', 'url': 'https://simple.ripley.cl/tecno/accesorios-computacion', 'priority': 0.45}
                ]
            }
        }
    
    def _load_user_agents(self) -> List[str]:
        """Cargar pool de user agents realistas"""
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
        ]
    
    def _log_tier_summary(self):
        """Mostrar resumen de configuración de tiers"""
        logger.info("📊 Configuración de Tiers:")
        
        total_categories = 0
        for tier_name, tier_config in self.tiers.items():
            tier_categories = self.tier_categories.get(tier_name, {})
            categories_count = sum(len(cats) for cats in tier_categories.values())
            total_categories += categories_count
            
            daily_executions = 24 / tier_config.frequency_hours
            
            logger.info(f"   🎯 {tier_name.upper()}: {categories_count} categorías")
            logger.info(f"      ⏰ Frecuencia: {tier_config.frequency_hours}h ({daily_executions:.1f} exec/día)")
            logger.info(f"      📄 Páginas: {tier_config.pages_range[0]}-{tier_config.pages_range[1]}")
            logger.info(f"      🎲 Jitter: ±{tier_config.jitter_percent}%")
        
        logger.info(f"📈 Total: {total_categories} categorías distribuidas en 3 tiers")
    
    def should_execute_tier(self, tier_name: str) -> bool:
        """Determinar si un tier debe ejecutarse"""
        tier_config = self.tiers[tier_name]
        tier_execution = self.tier_executions[tier_name]
        
        if not tier_execution.last_run:
            return True  # Primera ejecución
        
        # Calcular tiempo con jitter
        base_interval = tier_config.frequency_hours * 3600  # segundos
        jitter_seconds = base_interval * (tier_config.jitter_percent / 100)
        actual_interval = random.uniform(
            base_interval - jitter_seconds,
            base_interval + jitter_seconds
        )
        
        time_since_last = (datetime.now() - tier_execution.last_run).total_seconds()
        
        return time_since_last >= actual_interval
    
    def get_next_tier_to_execute(self) -> Optional[str]:
        """Obtener el próximo tier prioritario para ejecutar"""
        candidates = []
        
        for tier_name in self.tiers.keys():
            if self.should_execute_tier(tier_name):
                tier_config = self.tiers[tier_name]
                tier_execution = self.tier_executions[tier_name]
                
                # Calcular puntuación de urgencia
                if tier_execution.last_run:
                    hours_since = (datetime.now() - tier_execution.last_run).total_seconds() / 3600
                    urgency = max(0, hours_since - tier_config.frequency_hours) / tier_config.frequency_hours
                else:
                    urgency = 1.0
                
                priority_score = tier_config.priority + urgency
                candidates.append((tier_name, priority_score))
        
        if not candidates:
            return None
        
        # Ordenar por prioridad y retornar el más prioritario
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Agregar algo de randomización para evitar patrones
        if len(candidates) > 1 and random.random() < 0.15:  # 15% chance
            # Ocasionalmente tomar el segundo más prioritario
            return candidates[1][0] if len(candidates) > 1 else candidates[0][0]
        
        return candidates[0][0]
    
    def generate_tier_schedule(self, tier_name: str) -> List[CategorySchedule]:
        """Generar programación aleatoria para un tier"""
        tier_config = self.tiers[tier_name]
        tier_categories = self.tier_categories.get(tier_name, {})
        
        schedule = []
        base_time = datetime.now()
        
        # Recopilar todas las categorías
        all_categories = []
        for retailer, categories in tier_categories.items():
            for category in categories:
                all_categories.append((retailer, category))
        
        # Randomizar orden de ejecución
        random.shuffle(all_categories)
        
        # Distribuir temporalmente con gaps aleatorios
        current_time = base_time
        for retailer, category in all_categories:
            
            # Páginas aleatorias dentro del rango
            pages_to_scrape = random.randint(*tier_config.pages_range)
            
            # Crear schedule entry
            schedule_entry = CategorySchedule(
                retailer=retailer,
                category=category['key'],
                url=category['url'],
                tier=tier_name,
                priority=category['priority'],
                pages_to_scrape=pages_to_scrape,
                scheduled_time=current_time,
                randomization_applied={
                    'pages': pages_to_scrape,
                    'original_range': tier_config.pages_range,
                    'user_agent': random.choice(self.user_agents),
                    'proxy_enabled': tier_config.proxy_rotation,
                    'stealth_mode': tier_config.stealth_mode,
                    'execution_id': str(uuid.uuid4())[:8]
                }
            )
            
            schedule.append(schedule_entry)
            
            # Gap aleatorio entre categorías (30s a 5min)
            gap_seconds = random.uniform(30, 300)
            current_time += timedelta(seconds=gap_seconds)
        
        logger.info(f"📅 Programación generada para tier {tier_name}:")
        logger.info(f"   📊 {len(schedule)} categorías distribuidas en {(current_time - base_time).total_seconds()/60:.1f} minutos")
        
        return schedule
    
    def apply_pattern_breaking(self) -> Dict[str, Any]:
        """Aplicar técnicas de ruptura de patrones"""
        self.randomization_state['pattern_break_counter'] += 1
        
        pattern_breaks = {}
        
        # Ruptura cada 5-7 ejecuciones
        if self.randomization_state['pattern_break_counter'] % random.randint(5, 7) == 0:
            pattern_breaks.update({
                'extended_pause': random.uniform(300, 900),  # 5-15 min pausa extra
                'shuffle_retailers': True,
                'randomize_pages': True,
                'reason': 'pattern_break_scheduled'
            })
            logger.info("🔀 Aplicando ruptura de patrones automática")
        
        # Rotación de proxies/user agents
        now = datetime.now()
        if (now - self.randomization_state['last_ua_rotation']).seconds > 3600:  # Cada hora
            pattern_breaks['rotate_user_agents'] = True
            self.randomization_state['last_ua_rotation'] = now
        
        if (now - self.randomization_state['last_proxy_rotation']).seconds > 1800:  # Cada 30 min
            pattern_breaks['rotate_proxies'] = True
            self.randomization_state['last_proxy_rotation'] = now
        
        return pattern_breaks
    
    def update_tier_execution(self, tier_name: str, execution_result: Dict[str, Any]):
        """Actualizar estado de ejecución de un tier"""
        tier_execution = self.tier_executions[tier_name]
        
        tier_execution.last_run = datetime.now()
        tier_execution.executions_today += 1
        
        if execution_result.get('success', False):
            # Actualizar métricas de éxito
            execution_time = execution_result.get('execution_time_minutes', 0)
            if tier_execution.avg_execution_time == 0:
                tier_execution.avg_execution_time = execution_time
            else:
                tier_execution.avg_execution_time = (
                    tier_execution.avg_execution_time * 0.8 + execution_time * 0.2
                )
            
            tier_execution.success_rate = min(1.0, tier_execution.success_rate * 0.95 + 0.05)
            tier_execution.pages_scraped_total += execution_result.get('pages_scraped', 0)
            tier_execution.products_extracted += execution_result.get('products_extracted', 0)
        else:
            # Penalizar tasa de éxito
            tier_execution.success_rate = max(0.0, tier_execution.success_rate * 0.9)
        
        # Calcular próxima ejecución programada
        tier_config = self.tiers[tier_name]
        base_hours = tier_config.frequency_hours
        jitter_hours = base_hours * (tier_config.jitter_percent / 100)
        
        next_hours = random.uniform(base_hours - jitter_hours, base_hours + jitter_hours)
        tier_execution.next_scheduled = datetime.now() + timedelta(hours=next_hours)
        
        logger.info(f"📊 Tier {tier_name} actualizado:")
        logger.info(f"   ✅ Éxito: {tier_execution.success_rate:.1%}")
        logger.info(f"   ⏱️ Tiempo promedio: {tier_execution.avg_execution_time:.1f} min")
        logger.info(f"   📅 Próxima ejecución: {tier_execution.next_scheduled.strftime('%H:%M')}")
    
    def get_tier_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado de todos los tiers"""
        summary = {
            'tiers': {},
            'system': {
                'total_executions_today': sum(te.executions_today for te in self.tier_executions.values()),
                'overall_success_rate': sum(te.success_rate for te in self.tier_executions.values()) / len(self.tier_executions),
                'pattern_break_counter': self.randomization_state['pattern_break_counter'],
                'next_scheduled': {}
            }
        }
        
        for tier_name, tier_execution in self.tier_executions.items():
            summary['tiers'][tier_name] = {
                'last_run': tier_execution.last_run.isoformat() if tier_execution.last_run else None,
                'next_scheduled': tier_execution.next_scheduled.isoformat() if tier_execution.next_scheduled else None,
                'executions_today': tier_execution.executions_today,
                'success_rate': tier_execution.success_rate,
                'avg_execution_time': tier_execution.avg_execution_time,
                'products_extracted': tier_execution.products_extracted
            }
            
            if tier_execution.next_scheduled:
                summary['system']['next_scheduled'][tier_name] = tier_execution.next_scheduled
        
        return summary
    
    def save_state(self):
        """Guardar estado persistente"""
        try:
            state = {
                'tier_executions': {},
                'randomization_state': {
                    'pattern_break_counter': self.randomization_state['pattern_break_counter'],
                    'last_proxy_rotation': self.randomization_state['last_proxy_rotation'].isoformat(),
                    'last_ua_rotation': self.randomization_state['last_ua_rotation'].isoformat()
                },
                'execution_history': self.execution_history[-50:],  # Últimos 50
                'last_save': datetime.now().isoformat()
            }
            
            for tier_name, tier_execution in self.tier_executions.items():
                state['tier_executions'][tier_name] = {
                    'last_run': tier_execution.last_run.isoformat() if tier_execution.last_run else None,
                    'next_scheduled': tier_execution.next_scheduled.isoformat() if tier_execution.next_scheduled else None,
                    'executions_today': tier_execution.executions_today,
                    'success_rate': tier_execution.success_rate,
                    'avg_execution_time': tier_execution.avg_execution_time,
                    'pages_scraped_total': tier_execution.pages_scraped_total,
                    'products_extracted': tier_execution.products_extracted
                }
            
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Error guardando estado: {e}")
    
    def load_state(self):
        """Cargar estado persistente"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # Cargar ejecuciones de tiers
                for tier_name, tier_data in state.get('tier_executions', {}).items():
                    if tier_name in self.tier_executions:
                        tier_execution = self.tier_executions[tier_name]
                        
                        if tier_data.get('last_run'):
                            tier_execution.last_run = datetime.fromisoformat(tier_data['last_run'])
                        if tier_data.get('next_scheduled'):
                            tier_execution.next_scheduled = datetime.fromisoformat(tier_data['next_scheduled'])
                        
                        tier_execution.executions_today = tier_data.get('executions_today', 0)
                        tier_execution.success_rate = tier_data.get('success_rate', 1.0)
                        tier_execution.avg_execution_time = tier_data.get('avg_execution_time', 0.0)
                        tier_execution.pages_scraped_total = tier_data.get('pages_scraped_total', 0)
                        tier_execution.products_extracted = tier_data.get('products_extracted', 0)
                
                # Cargar estado de randomización
                rand_state = state.get('randomization_state', {})
                if 'pattern_break_counter' in rand_state:
                    self.randomization_state['pattern_break_counter'] = rand_state['pattern_break_counter']
                if 'last_proxy_rotation' in rand_state:
                    self.randomization_state['last_proxy_rotation'] = datetime.fromisoformat(rand_state['last_proxy_rotation'])
                if 'last_ua_rotation' in rand_state:
                    self.randomization_state['last_ua_rotation'] = datetime.fromisoformat(rand_state['last_ua_rotation'])
                
                # Cargar historial
                self.execution_history = state.get('execution_history', [])
                
                logger.info("📁 Estado anterior cargado correctamente")
        
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar estado anterior: {e}")