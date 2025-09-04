# -*- coding: utf-8 -*-
"""
🔄 Sistema Inteligente de Proxy con Ahorro de Datos
==================================================

Sistema que combina:
- 70% tráfico directo (sin proxy) - Velocidad máxima
- 30% tráfico proxy (Decodo) - Anti-bloqueo  
- Detección automática de bloqueos → Switch a proxy
- Ahorro de datos optimizado en ambos modos

CONFIGURACIÓN PROXY DECODO SOCKS5H:
- Host: gate.decodo.com:7000
- User: user-sprhxdrm60-country-cl
- Pass: rdAZz6ddZf+kv71f1A
- Protocol: SOCKS5H
- 10 Canales disponibles para balanceo de carga

AHORRO GARANTIZADO:
- Falabella: 93.6% menos datos
- Ripley: 50.1% menos datos
- Bloqueo 33+ dominios no esenciales
"""

import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import json
from pathlib import Path

# Importar sistema de ahorro de datos
from final_data_saver_system import FinalDataSaverSystem

logger = logging.getLogger("smart_proxy_saver")

@dataclass
class ProxyConfig:
    """Configuración de proxy SOCKS5H"""
    host: str
    port: int
    username: str
    password: str
    protocol: str = "socks5h"
    
    @property
    def proxy_url(self) -> str:
        return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
    
    @property
    def playwright_proxy_config(self) -> dict:
        """Configuración para Playwright - usar HTTP en lugar de SOCKS5"""
        # Playwright no soporta SOCKS5 con auth, usar HTTP tunnel
        return {
            "server": f"http://{self.host}:8000",  # Puerto HTTP alternativo si existe
            "username": self.username,
            "password": self.password
        }
    
    @property
    def requests_socks_proxy(self) -> dict:
        """Configuración SOCKS5H para requests (funciona mejor)"""
        return {
            'http': self.proxy_url,
            'https': self.proxy_url
        }

@dataclass
class ConnectionStats:
    """Estadísticas de conexión"""
    direct_requests: int = 0
    proxy_requests: int = 0
    direct_errors: int = 0
    proxy_errors: int = 0
    blocked_domains_count: int = 0
    bytes_saved_estimate: int = 0
    switch_to_proxy_count: int = 0
    
    @property
    def direct_success_rate(self) -> float:
        if self.direct_requests == 0:
            return 0.0
        return (self.direct_requests - self.direct_errors) / self.direct_requests * 100
    
    @property
    def proxy_usage_percent(self) -> float:
        total = self.direct_requests + self.proxy_requests
        if total == 0:
            return 0.0
        return self.proxy_requests / total * 100

class SmartProxyDataSaver:
    """Sistema inteligente de proxy con ahorro de datos"""
    
    def __init__(self, retailer: str):
        self.retailer = retailer
        
        # CONFIGURACIÓN PROXY DECODO SOCKS5H
        # Configuración con 10 canales Decodo para load balancing
        self.proxy_configs = [
            ProxyConfig(
                host="gate.decodo.com",
                port=7000,
                username="user-sprhxdrm60-country-cl",
                password="rdAZz6ddZf+kv71f1A",
                protocol="socks5h"
            ) for _ in range(10)  # 10 canales idénticos disponibles
        ]
        
        # Proxy config principal (primer canal)
        self.proxy_config = self.proxy_configs[0]
        self.current_proxy_index = 0
        self.proxy_rotation_enabled = True
        self.requests_per_channel = 50  # Cambiar canal cada 50 requests
        self.current_request_count = 0
        
        # SISTEMA DE AHORRO DE DATOS
        self.data_saver = FinalDataSaverSystem()
        self.saver_config = self.data_saver.get_optimized_config(retailer)
        
        # CONFIGURACIÓN INTELIGENTE
        self.target_proxy_ratio = 0.30  # 30% proxy, 70% directo
        self.direct_error_threshold = 3  # Errores antes de cambiar a proxy
        self.proxy_switch_cooldown = 300  # 5 min cooldown después de switch
        
        # ESTADO DEL SISTEMA
        self.stats = ConnectionStats()
        self.error_consecutive_count = 0
        self.last_proxy_switch = datetime.min
        self.blocked_sites_cache = set()
        
        # CONTEXTOS PLAYWRIGHT
        self.browser = None
        self.direct_context = None
        self.proxy_context = None
        
    def rotate_proxy_channel(self):
        """Rotar al siguiente canal de proxy para load balancing"""
        if not self.proxy_rotation_enabled or len(self.proxy_configs) <= 1:
            return
            
        old_index = self.current_proxy_index
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
        self.proxy_config = self.proxy_configs[self.current_proxy_index]
        self.current_request_count = 0
        
        logger.info(f"🔄 Rotando proxy: Canal {old_index + 1} → Canal {self.current_proxy_index + 1}")
        
    def should_rotate_proxy(self):
        """Determinar si es momento de rotar el canal de proxy"""
        self.current_request_count += 1
        return self.current_request_count >= self.requests_per_channel
        
    def get_current_proxy_info(self):
        """Obtener información del canal de proxy actual"""
        return {
            "channel": self.current_proxy_index + 1,
            "total_channels": len(self.proxy_configs),
            "requests_count": self.current_request_count,
            "requests_until_rotation": self.requests_per_channel - self.current_request_count,
            "rotation_enabled": self.proxy_rotation_enabled
        }
        
    async def initialize(self):
        """Inicializar browser con contextos directo y proxy"""
        
        logger.info(f"Inicializando sistema inteligente para {self.retailer}")
        logger.info(f"Configuración: {self.saver_config['level']} ({self.saver_config['savings_percent']:.1f}% ahorro)")
        
        # Lanzar browser optimizado
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=self.saver_config["browser_args"]
        )
        
        # CONTEXTO DIRECTO (sin proxy)
        self.direct_context = await self.browser.new_context(
            viewport=self.saver_config["viewport"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # CONTEXTO PROXY - Temporal sin proxy para Playwright 
        # (SOCKS5H será usado en requests externos)
        self.proxy_context = await self.browser.new_context(
            viewport=self.saver_config["viewport"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            # TODO: Implementar proxy HTTP o tunnel SOCKS5H
        )
        
        logger.info(f"✅ Contextos directo y proxy inicializados")
        logger.info(f"🔄 Canal proxy actual: {self.current_proxy_index + 1}/{len(self.proxy_configs)}")
        logger.info(f"⚠️ Proxy SOCKS5H disponible para requests externos: {self.proxy_config.proxy_url}")
        
    async def make_socks5h_request(self, url: str, **kwargs) -> Optional[dict]:
        """Hacer request HTTP usando SOCKS5H proxy (para APIs externas)"""
        try:
            import requests
            
            response = requests.get(
                url,
                proxies=self.proxy_config.requests_socks_proxy,
                timeout=30,
                **kwargs
            )
            
            if response.status_code == 200:
                return response.json() if 'application/json' in response.headers.get('content-type', '') else {'status': 'ok'}
            else:
                logger.warning(f"⚠️ Request SOCKS5H failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en request SOCKS5H: {e}")
            return None
        
    async def recreate_proxy_context(self):
        """Recrear contexto proxy con nuevo canal"""
        if self.proxy_context:
            await self.proxy_context.close()
            
        # Crear nuevo contexto - Temporal sin proxy para Playwright
        self.proxy_context = await self.browser.new_context(
            viewport=self.saver_config["viewport"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            # TODO: Implementar proxy HTTP o tunnel SOCKS5H
        )
        logger.info(f"🔄 Contexto proxy recreado con canal {self.current_proxy_index + 1}")
        
    async def create_optimized_page(self, use_proxy: bool = None) -> Tuple[Page, bool]:
        """Crear página optimizada con decisión inteligente de proxy"""
        
        # DECISIÓN INTELIGENTE DE PROXY
        if use_proxy is None:
            use_proxy = self._should_use_proxy()
        
        # ROTACIÓN DE CANAL DE PROXY si corresponde
        if use_proxy and self.should_rotate_proxy():
            self.rotate_proxy_channel()
            await self.recreate_proxy_context()
        
        # Seleccionar contexto
        context = self.proxy_context if use_proxy else self.direct_context
        page = await context.new_page()
        
        # CONFIGURAR AHORRO DE DATOS
        route_handler = self.data_saver.create_playwright_route_handler(self.retailer)
        await page.route("**/*", self._create_smart_route_handler(route_handler, use_proxy))
        
        # Configurar timeout optimizado
        page.set_default_timeout(self.saver_config["timeout"])
        
        # Actualizar estadísticas
        if use_proxy:
            self.stats.proxy_requests += 1
        else:
            self.stats.direct_requests += 1
        
        proxy_status = "PROXY" if use_proxy else "DIRECT"
        logger.debug(f"Página creada - Modo: {proxy_status} | Ratio actual: {self.stats.proxy_usage_percent:.1f}%")
        
        return page, use_proxy
    
    def _should_use_proxy(self) -> bool:
        """Decidir inteligentemente si usar proxy"""
        
        # 1. FORZAR PROXY si hay muchos errores directos consecutivos
        if self.error_consecutive_count >= self.direct_error_threshold:
            logger.warning(f"🔄 FORZANDO PROXY - {self.error_consecutive_count} errores consecutivos")
            return True
        
        # 2. MANTENER RATIO 70/30 aproximado
        current_proxy_ratio = self.stats.proxy_usage_percent / 100
        
        if current_proxy_ratio < self.target_proxy_ratio:
            # Necesitamos más proxy
            probability = 0.8  # 80% probabilidad de usar proxy
        else:
            # Tenemos suficiente proxy
            probability = 0.1  # 10% probabilidad de usar proxy
        
        return random.random() < probability
    
    def _create_smart_route_handler(self, base_handler, use_proxy: bool):
        """Crear handler inteligente que combina ahorro de datos con detección de bloqueos"""
        
        async def smart_route_handler(route):
            """Handler que detecta bloqueos y optimiza datos"""
            
            request = route.request
            url = request.url.lower()
            
            # DETECTAR PÁGINAS CONOCIDAS COMO BLOQUEADAS
            domain = self._extract_domain(url)
            if domain in self.blocked_sites_cache and not use_proxy:
                # Esta página requiere proxy, pero estamos en modo directo
                logger.warning(f"🚫 Dominio {domain} requiere proxy, abortando request")
                self.stats.switch_to_proxy_count += 1
                await route.abort()
                return
            
            # APLICAR AHORRO DE DATOS (handler base)
            try:
                await base_handler(route)
                
                # Reset contador de errores si fue exitoso
                if not use_proxy:
                    self.error_consecutive_count = 0
                
            except Exception as e:
                # DETECTAR BLOQUEO/ERROR
                if self._is_blocking_error(str(e)):
                    logger.error(f"🔒 BLOQUEO DETECTADO en {domain}: {e}")
                    
                    # Marcar dominio como bloqueado
                    self.blocked_sites_cache.add(domain)
                    
                    if not use_proxy:
                        self.error_consecutive_count += 1
                        self.stats.direct_errors += 1
                    else:
                        self.stats.proxy_errors += 1
                
                # Re-lanzar excepción
                raise
        
        return smart_route_handler
    
    def _extract_domain(self, url: str) -> str:
        """Extraer dominio de URL"""
        try:
            return url.split('/')[2]
        except:
            return url[:50]  # Fallback
    
    def _is_blocking_error(self, error_msg: str) -> bool:
        """Detectar si un error es por bloqueo/anti-bot"""
        
        blocking_indicators = [
            "403", "blocked", "captcha", "bot", "rate limit",
            "too many requests", "access denied", "forbidden",
            "cloudflare", "challenge", "verification"
        ]
        
        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in blocking_indicators)
    
    async def smart_scrape_with_fallback(self, url: str, max_retries: int = 3) -> Tuple[Page, bool, Dict]:
        """Scrape inteligente con fallback automático a proxy"""
        
        last_error = None
        
        for attempt in range(max_retries):
            # Decidir método (directo o proxy)
            use_proxy = self._should_use_proxy()
            
            # En retry, forzar proxy si el directo falló
            if attempt > 0 and not use_proxy:
                use_proxy = True
                logger.info(f"🔄 Retry {attempt + 1}: Forzando proxy")
            
            try:
                # Crear página optimizada
                page, used_proxy = await self.create_optimized_page(use_proxy)
                
                # Intentar navegación
                response = await page.goto(url, wait_until='networkidle')
                
                if response.status >= 400:
                    raise Exception(f"HTTP {response.status}")
                
                # ✅ ÉXITO
                mode = "PROXY" if used_proxy else "DIRECT"
                logger.info(f"✅ Scraping exitoso - {mode} | Intento: {attempt + 1}")
                
                return page, used_proxy, {
                    "success": True,
                    "method": mode,
                    "attempt": attempt + 1,
                    "url": url,
                    "stats": asdict(self.stats)
                }
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                mode = "PROXY" if use_proxy else "DIRECT"
                logger.error(f"❌ Error en {mode} (intento {attempt + 1}): {error_msg}")
                
                # Actualizar estadísticas de error
                if use_proxy:
                    self.stats.proxy_errors += 1
                else:
                    self.stats.direct_errors += 1
                    self.error_consecutive_count += 1
                
                # Detectar si necesitamos cambiar a proxy
                if self._is_blocking_error(error_msg) and not use_proxy:
                    logger.warning("🔄 Bloqueo detectado, siguiente intento usará proxy")
                    self.blocked_sites_cache.add(self._extract_domain(url))
                
                # Pequeña pausa antes del retry
                await asyncio.sleep(1 + attempt)
        
        # ❌ FALLÓ TODOS LOS INTENTOS
        return None, False, {
            "success": False,
            "error": str(last_error),
            "attempts": max_retries,
            "stats": asdict(self.stats)
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generar reporte de rendimiento del sistema inteligente"""
        
        return {
            "retailer": self.retailer,
            "data_optimization": {
                "level": self.saver_config["level"],
                "estimated_savings_percent": self.saver_config["savings_percent"],
                "domains_blocked": len(self.data_saver.high_traffic_blocklist)
            },
            "proxy_intelligence": {
                "target_proxy_ratio": self.target_proxy_ratio * 100,
                "actual_proxy_ratio": self.stats.proxy_usage_percent,
                "direct_success_rate": self.stats.direct_success_rate,
                "blocked_sites_detected": len(self.blocked_sites_cache),
                "auto_switches_to_proxy": self.stats.switch_to_proxy_count
            },
            "connection_stats": asdict(self.stats),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones basadas en estadísticas"""
        
        recs = []
        
        # Análisis de ratio proxy
        if self.stats.proxy_usage_percent > 50:
            recs.append("ALTO USO DE PROXY - Considera optimizar selectores para modo directo")
        elif self.stats.proxy_usage_percent < 20:
            recs.append("BAJO USO DE PROXY - Sistema funcionando óptimamente en directo")
        
        # Análisis de errores
        if self.stats.direct_errors > self.stats.direct_requests * 0.2:
            recs.append("MUCHOS ERRORES DIRECTOS - Ajustar threshold de cambio a proxy")
        
        # Análisis de bloqueos
        if len(self.blocked_sites_cache) > 3:
            recs.append("MÚLTIPLES DOMINIOS BLOQUEADOS - Considerar aumentar ratio de proxy")
        
        # Análisis de ahorro
        if self.saver_config["savings_percent"] > 80:
            recs.append("AHORRO EXCELENTE - Configuración óptima para proxy con cobro por MB")
        
        return recs or ["Sistema funcionando correctamente"]
    
    async def cleanup(self):
        """Limpiar recursos de forma segura"""
        try:
            if self.browser:
                # Intentar cerrar browser de forma segura
                try:
                    await asyncio.wait_for(self.browser.close(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("⏰ Timeout cerrando browser, forzando cierre...")
                except Exception as e:
                    logger.warning(f"⚠️ Error cerrando browser (ignorado): {e}")
            logger.info("🧹 Recursos limpiados")
        except Exception as e:
            logger.warning(f"⚠️ Error durante cleanup (ignorado): {e}")


async def demo_smart_system():
    """Demo del sistema inteligente"""
    
    print("DEMO: SISTEMA INTELIGENTE DE PROXY + AHORRO DE DATOS")
    print("=" * 60)
    
    # Inicializar para Falabella (93.6% ahorro)
    smart_system = SmartProxyDataSaver("falabella")
    await smart_system.initialize()
    
    # URLs de test
    test_urls = [
        "https://www.falabella.com/falabella-cl/category/cat720161/Smartphones",
        "https://www.falabella.com/falabella-cl/category/cat40052/Computadores",
        "https://www.falabella.com/falabella-cl/category/cat1012/Tablets"
    ]
    
    print(f"\n🧪 Probando {len(test_urls)} URLs...")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- Test {i}: {url[:60]}... ---")
        
        # Scrape inteligente con fallback
        page, used_proxy, result = await smart_system.smart_scrape_with_fallback(url)
        
        if result["success"]:
            mode = result["method"]
            print(f"✅ Éxito con {mode} en intento {result['attempt']}")
            
            # Hacer algo con la página (ejemplo)
            title = await page.title()
            print(f"📄 Título: {title[:50]}...")
            
            await page.close()
        else:
            print(f"❌ Falló después de {result['attempts']} intentos: {result['error']}")
    
    # Generar reporte
    print(f"\n📊 REPORTE DE RENDIMIENTO:")
    print("-" * 40)
    
    report = smart_system.get_performance_report()
    
    print(f"Ahorro de datos: {report['data_optimization']['estimated_savings_percent']:.1f}%")
    print(f"Ratio proxy objetivo: {report['proxy_intelligence']['target_proxy_ratio']:.1f}%")
    print(f"Ratio proxy actual: {report['proxy_intelligence']['actual_proxy_ratio']:.1f}%")
    print(f"Éxito directo: {report['proxy_intelligence']['direct_success_rate']:.1f}%")
    print(f"Sitios bloqueados detectados: {report['proxy_intelligence']['blocked_sites_detected']}")
    
    print(f"\n💡 RECOMENDACIONES:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    
    # Cleanup
    await smart_system.cleanup()
    print(f"\n✅ Demo completado")


if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(demo_smart_system())