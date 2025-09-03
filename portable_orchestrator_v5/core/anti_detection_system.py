#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🛡️ ANTI-DETECTION SYSTEM V5
============================
Sistema avanzado de anti-detección para scraping continuo

Características:
- ✅ Rotación inteligente de proxies
- ✅ Gestión de user-agents realistas  
- ✅ Patrones de navegación humanos
- ✅ Delays variables con jitter
- ✅ Rotación de páginas aleatorias
- ✅ Fingerprint randomization
"""

import asyncio
import random
import json
import logging
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import time

from .emoji_support import force_emoji_support
force_emoji_support()

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """Configuración de proxy"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    last_used: Optional[datetime] = None
    success_rate: float = 1.0
    response_time_ms: float = 0.0
    failed_attempts: int = 0
    is_working: bool = True

@dataclass
class UserAgentProfile:
    """Perfil de user agent con características"""
    user_agent: str
    browser: str
    os: str
    probability: float
    last_used: Optional[datetime] = None

@dataclass
class NavigationPattern:
    """Patrón de navegación humano"""
    name: str
    page_sequence: List[int]  # Secuencia de páginas
    delays_range: Tuple[float, float]  # Rangos de delays
    scroll_behavior: Dict[str, Any]
    interaction_probability: float

class AntiDetectionSystem:
    """🛡️ Sistema avanzado de anti-detección"""
    
    def __init__(self):
        """Inicializar sistema de anti-detección"""
        
        # Configuración de proxies
        self.proxy_pool: List[ProxyConfig] = []
        self.proxy_rotation_enabled = True
        self.proxy_rotation_frequency = 5  # Cambiar cada 5 requests
        self.current_proxy_index = 0
        self.proxy_health_check_interval = 300  # 5 minutos
        
        # User agents realistas con distribución de probabilidades
        self.user_agent_profiles = self._load_user_agent_profiles()
        self.current_user_agent_index = 0
        
        # Patrones de navegación humanos
        self.navigation_patterns = self._load_navigation_patterns()
        
        # Estado de randomización
        self.randomization_state = {
            'last_proxy_rotation': datetime.now(),
            'last_ua_rotation': datetime.now(),
            'requests_with_current_proxy': 0,
            'requests_with_current_ua': 0,
            'current_session_fingerprint': self._generate_session_fingerprint(),
            'navigation_pattern_changes': 0
        }
        
        # Métricas de anti-detección
        self.metrics = {
            'proxy_rotations': 0,
            'ua_rotations': 0,
            'pattern_breaks_applied': 0,
            'human_delays_applied': 0,
            'captcha_encounters': 0,
            'blocked_requests': 0,
            'successful_requests': 0
        }
        
        # Configuración de delays humanos
        self.human_delays = {
            'page_load_wait': (2.0, 8.0),      # Esperar carga de página
            'between_clicks': (0.5, 2.0),      # Entre clicks
            'scroll_pause': (1.0, 3.0),        # Pausas al hacer scroll
            'category_change': (3.0, 10.0),    # Entre cambios de categoría
            'retailer_change': (30.0, 120.0),  # Entre retailers
            'session_break': (300.0, 900.0)    # Pausas largas de sesión
        }
        
        logger.info("🛡️ Anti-Detection System V5 inicializado")
        self._log_configuration_summary()
    
    def _load_user_agent_profiles(self) -> List[UserAgentProfile]:
        """Cargar perfiles de user agents realistas con probabilidades"""
        profiles = [
            # Chrome Windows (más común)
            UserAgentProfile(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                browser='Chrome', os='Windows', probability=0.35
            ),
            UserAgentProfile(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                browser='Chrome', os='Windows', probability=0.25
            ),
            # Chrome macOS
            UserAgentProfile(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                browser='Chrome', os='macOS', probability=0.15
            ),
            # Safari macOS  
            UserAgentProfile(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
                browser='Safari', os='macOS', probability=0.10
            ),
            # Firefox Windows
            UserAgentProfile(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
                browser='Firefox', os='Windows', probability=0.10
            ),
            # Chrome Linux
            UserAgentProfile(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                browser='Chrome', os='Linux', probability=0.05
            )
        ]
        
        # Normalizar probabilidades
        total_prob = sum(p.probability for p in profiles)
        for profile in profiles:
            profile.probability = profile.probability / total_prob
        
        return profiles
    
    def _load_navigation_patterns(self) -> List[NavigationPattern]:
        """Cargar patrones de navegación humanos"""
        return [
            NavigationPattern(
                name='sequential_browse',
                page_sequence=[1, 2, 3, 2, 4],  # Navegar secuencialmente, volver atrás
                delays_range=(2.0, 5.0),
                scroll_behavior={'enabled': True, 'scroll_ratio': 0.7, 'pauses': 3},
                interaction_probability=0.8
            ),
            NavigationPattern(
                name='random_jump',
                page_sequence=[1, 4, 2, 6, 3],  # Saltar aleatoriamente
                delays_range=(1.5, 4.0),
                scroll_behavior={'enabled': True, 'scroll_ratio': 0.5, 'pauses': 2},
                interaction_probability=0.6
            ),
            NavigationPattern(
                name='deep_browse',
                page_sequence=[1, 2, 3, 4, 5, 6, 7],  # Navegación profunda
                delays_range=(3.0, 7.0),
                scroll_behavior={'enabled': True, 'scroll_ratio': 0.9, 'pauses': 5},
                interaction_probability=0.9
            ),
            NavigationPattern(
                name='quick_scan',
                page_sequence=[1, 3, 5],  # Escaneo rápido
                delays_range=(1.0, 2.5),
                scroll_behavior={'enabled': True, 'scroll_ratio': 0.3, 'pauses': 1},
                interaction_probability=0.4
            )
        ]
    
    def _generate_session_fingerprint(self) -> str:
        """Generar fingerprint único de sesión"""
        timestamp = str(time.time())
        random_data = str(random.randint(100000, 999999))
        return hashlib.md5(f"{timestamp}{random_data}".encode()).hexdigest()[:8]
    
    def _log_configuration_summary(self):
        """Log de resumen de configuración"""
        logger.info("🔧 Configuración Anti-Detección:")
        logger.info(f"   👥 User Agents: {len(self.user_agent_profiles)} perfiles")
        logger.info(f"   🌐 Proxies: {len(self.proxy_pool)} configurados")
        logger.info(f"   🧭 Patrones navegación: {len(self.navigation_patterns)}")
        logger.info(f"   🎲 Rotación proxy: cada {self.proxy_rotation_frequency} requests")
        logger.info(f"   🆔 Session fingerprint: {self.randomization_state['current_session_fingerprint']}")
    
    def add_proxy(self, host: str, port: int, username: str = None, password: str = None, protocol: str = "http"):
        """Agregar proxy al pool"""
        proxy_config = ProxyConfig(
            host=host, port=port, username=username, 
            password=password, protocol=protocol
        )
        self.proxy_pool.append(proxy_config)
        logger.info(f"🌐 Proxy agregado: {host}:{port}")
    
    def load_proxies_from_file(self, file_path: str):
        """Cargar proxies desde archivo"""
        try:
            proxy_file = Path(file_path)
            if proxy_file.exists():
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    proxies_data = json.load(f)
                
                for proxy_data in proxies_data:
                    self.add_proxy(**proxy_data)
                    
                logger.info(f"📁 {len(proxies_data)} proxies cargados desde {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron cargar proxies: {e}")
    
    async def check_proxy_health(self, proxy: ProxyConfig) -> bool:
        """Verificar salud de un proxy"""
        try:
            proxy_url = f"{proxy.protocol}://"
            if proxy.username and proxy.password:
                proxy_url += f"{proxy.username}:{proxy.password}@"
            proxy_url += f"{proxy.host}:{proxy.port}"
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://httpbin.org/ip', 
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        response_time = (time.time() - start_time) * 1000
                        proxy.response_time_ms = response_time
                        proxy.is_working = True
                        proxy.failed_attempts = 0
                        proxy.success_rate = min(1.0, proxy.success_rate * 0.9 + 0.1)
                        return True
        
        except Exception as e:
            proxy.failed_attempts += 1
            proxy.is_working = False
            proxy.success_rate = max(0.0, proxy.success_rate * 0.8)
            logger.warning(f"❌ Proxy {proxy.host}:{proxy.port} falló: {e}")
        
        return False
    
    async def get_working_proxy(self) -> Optional[ProxyConfig]:
        """Obtener un proxy funcional"""
        if not self.proxy_pool or not self.proxy_rotation_enabled:
            return None
        
        # Filtrar proxies funcionales
        working_proxies = [p for p in self.proxy_pool if p.is_working and p.failed_attempts < 3]
        
        if not working_proxies:
            # Intentar verificar algunos proxies
            await self._health_check_proxies()
            working_proxies = [p for p in self.proxy_pool if p.is_working]
        
        if not working_proxies:
            logger.warning("⚠️ No hay proxies funcionales disponibles")
            return None
        
        # Seleccionar proxy basado en success rate y tiempo de uso
        best_proxy = max(working_proxies, key=lambda p: (
            p.success_rate * 0.7 + 
            (1 - min(1.0, (datetime.now() - (p.last_used or datetime.now())).seconds / 3600)) * 0.3
        ))
        
        best_proxy.last_used = datetime.now()
        return best_proxy
    
    async def _health_check_proxies(self):
        """Verificar salud de proxies en paralelo"""
        if not self.proxy_pool:
            return
        
        logger.info(f"🔍 Verificando salud de {len(self.proxy_pool)} proxies...")
        
        # Verificar en paralelo con límite de concurrencia
        semaphore = asyncio.Semaphore(5)
        
        async def check_with_semaphore(proxy):
            async with semaphore:
                return await self.check_proxy_health(proxy)
        
        tasks = [check_with_semaphore(proxy) for proxy in self.proxy_pool]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        working_count = sum(1 for result in results if result is True)
        logger.info(f"✅ {working_count}/{len(self.proxy_pool)} proxies funcionales")
    
    def get_random_user_agent(self) -> UserAgentProfile:
        """Obtener user agent aleatorio basado en probabilidades"""
        # Usar distribución de probabilidades para selección realista
        rand = random.random()
        cumulative = 0.0
        
        for profile in self.user_agent_profiles:
            cumulative += profile.probability
            if rand <= cumulative:
                profile.last_used = datetime.now()
                return profile
        
        # Fallback al último si algo sale mal
        return self.user_agent_profiles[-1]
    
    def should_rotate_user_agent(self) -> bool:
        """Determinar si se debe rotar el user agent"""
        requests_count = self.randomization_state['requests_with_current_ua']
        time_since_last = (datetime.now() - self.randomization_state['last_ua_rotation']).seconds
        
        # Rotar cada 20-40 requests o cada 30-60 minutos
        return (requests_count >= random.randint(20, 40) or 
                time_since_last >= random.randint(1800, 3600))
    
    def should_rotate_proxy(self) -> bool:
        """Determinar si se debe rotar el proxy"""
        requests_count = self.randomization_state['requests_with_current_proxy']
        time_since_last = (datetime.now() - self.randomization_state['last_proxy_rotation']).seconds
        
        # Rotar cada 5-10 requests o cada 10-20 minutos
        return (requests_count >= random.randint(5, 10) or 
                time_since_last >= random.randint(600, 1200))
    
    def get_human_delay(self, delay_type: str) -> float:
        """Obtener delay humano aleatorio"""
        if delay_type not in self.human_delays:
            return random.uniform(1.0, 3.0)  # Default
        
        min_delay, max_delay = self.human_delays[delay_type]
        
        # Aplicar distribución más realista (no uniforme)
        # Favorecer delays más cortos con ocasionales delays largos
        if random.random() < 0.8:  # 80% de las veces
            delay = random.uniform(min_delay, min_delay + (max_delay - min_delay) * 0.6)
        else:  # 20% delays más largos
            delay = random.uniform(min_delay + (max_delay - min_delay) * 0.6, max_delay)
        
        self.metrics['human_delays_applied'] += 1
        return delay
    
    def generate_page_sequence(self, total_pages: int, pages_to_scrape: int) -> List[int]:
        """Generar secuencia de páginas humana"""
        if pages_to_scrape >= total_pages:
            return list(range(1, total_pages + 1))
        
        # Seleccionar patrón de navegación
        pattern = random.choice(self.navigation_patterns)
        
        if pattern.name == 'sequential_browse':
            # Navegación secuencial con algunos saltos
            sequence = list(range(1, min(pages_to_scrape + 1, total_pages + 1)))
            if len(sequence) > 2 and random.random() < 0.3:
                # Ocasionalmente volver a una página anterior
                sequence.append(random.choice(sequence[:-1]))
        
        elif pattern.name == 'random_jump':
            # Saltos aleatorios pero evitando páginas muy altas
            max_page = min(total_pages, pages_to_scrape * 2)
            sequence = random.sample(range(1, max_page + 1), min(pages_to_scrape, max_page))
            sequence.sort()  # Mantener algo de orden
        
        elif pattern.name == 'deep_browse':
            # Navegación profunda desde página 1
            sequence = list(range(1, min(pages_to_scrape + 1, total_pages + 1)))
        
        else:  # quick_scan
            # Escaneo rápido de páginas espaciadas
            if total_pages <= 3:
                sequence = list(range(1, total_pages + 1))
            else:
                step = max(1, total_pages // pages_to_scrape)
                sequence = [i for i in range(1, total_pages + 1, step)][:pages_to_scrape]
        
        return sequence[:pages_to_scrape]  # Asegurar límite
    
    def apply_scroll_behavior(self, page_height: int = 100) -> Dict[str, Any]:
        """Generar comportamiento de scroll humano"""
        pattern = random.choice(self.navigation_patterns)
        scroll_config = pattern.scroll_behavior
        
        if not scroll_config.get('enabled', True):
            return {'enabled': False}
        
        scroll_ratio = scroll_config.get('scroll_ratio', 0.7)
        pauses = scroll_config.get('pauses', 3)
        
        # Generar puntos de pausa aleatorios
        scroll_points = []
        for _ in range(pauses):
            scroll_point = random.uniform(0.1, scroll_ratio)
            pause_duration = random.uniform(0.5, 2.0)
            scroll_points.append({
                'position': scroll_point,
                'pause_seconds': pause_duration
            })
        
        scroll_points.sort(key=lambda x: x['position'])
        
        return {
            'enabled': True,
            'scroll_ratio': scroll_ratio,
            'points': scroll_points,
            'final_pause': random.uniform(1.0, 3.0)
        }
    
    def get_anti_detection_headers(self, user_agent_profile: UserAgentProfile) -> Dict[str, str]:
        """Generar headers anti-detección"""
        headers = {
            'User-Agent': user_agent_profile.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'es-CL,es;q=0.9,en;q=0.8',
                'es-CL,es;q=0.8,en-US;q=0.6,en;q=0.4',
                'es;q=0.9,en;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': str(random.randint(0, 1)),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Headers específicos por browser
        if 'Chrome' in user_agent_profile.browser:
            headers.update({
                'sec-ch-ua': random.choice([
                    '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                    '"Google Chrome";v="121", "Not(A:Brand";v="24", "Chromium";v="121"'
                ]),
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': f'"{user_agent_profile.os}"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            })
        
        # Cache control aleatorio
        if random.random() < 0.3:
            headers['Cache-Control'] = random.choice([
                'max-age=0',
                'no-cache',
                'no-store, no-cache, must-revalidate'
            ])
        
        return headers
    
    def update_metrics(self, event_type: str, success: bool = True):
        """Actualizar métricas del sistema"""
        if event_type == 'proxy_rotation':
            self.metrics['proxy_rotations'] += 1
            self.randomization_state['last_proxy_rotation'] = datetime.now()
            self.randomization_state['requests_with_current_proxy'] = 0
        
        elif event_type == 'ua_rotation':
            self.metrics['ua_rotations'] += 1
            self.randomization_state['last_ua_rotation'] = datetime.now()
            self.randomization_state['requests_with_current_ua'] = 0
        
        elif event_type == 'request':
            self.randomization_state['requests_with_current_proxy'] += 1
            self.randomization_state['requests_with_current_ua'] += 1
            
            if success:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['blocked_requests'] += 1
        
        elif event_type == 'captcha':
            self.metrics['captcha_encounters'] += 1
        
        elif event_type == 'pattern_break':
            self.metrics['pattern_breaks_applied'] += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        total_requests = self.metrics['successful_requests'] + self.metrics['blocked_requests']
        success_rate = self.metrics['successful_requests'] / max(total_requests, 1)
        
        return {
            'success_rate': success_rate,
            'total_requests': total_requests,
            'proxy_rotations': self.metrics['proxy_rotations'],
            'ua_rotations': self.metrics['ua_rotations'],
            'pattern_breaks': self.metrics['pattern_breaks_applied'],
            'human_delays': self.metrics['human_delays_applied'],
            'captcha_encounters': self.metrics['captcha_encounters'],
            'current_session_fingerprint': self.randomization_state['current_session_fingerprint'],
            'working_proxies': len([p for p in self.proxy_pool if p.is_working])
        }
    
    async def session_break(self):
        """Realizar pausa de sesión para simular comportamiento humano"""
        break_duration = self.get_human_delay('session_break')
        
        logger.info(f"😴 Pausa de sesión: {break_duration/60:.1f} minutos")
        logger.info("🔄 Regenerando fingerprint de sesión...")
        
        # Regenerar fingerprint
        self.randomization_state['current_session_fingerprint'] = self._generate_session_fingerprint()
        
        # Forzar rotación en próxima request
        self.randomization_state['requests_with_current_proxy'] = 999
        self.randomization_state['requests_with_current_ua'] = 999
        
        await asyncio.sleep(break_duration)
        
        self.update_metrics('pattern_break')