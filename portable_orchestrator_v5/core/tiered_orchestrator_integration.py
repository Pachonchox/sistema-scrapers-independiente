#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 INTEGRADOR ORQUESTADOR TIER INTELIGENTE V5
============================================

Integra el sistema de tiers inteligente con el orquestador V5 robusto existente,
reemplazando los ciclos continuos por schedulling basado en tiers.

Características:
- 🎚️ Integración transparente con orquestador existente
- ⏰ Scheduling inteligente basado en tiers (2h/6h/24h)
- 🎭 Anti-detección automática integrada
- 📊 Métricas y estadísticas unificadas
- 🔄 Rotación de proxies y user agents
- 🎲 Aleatorización de patrones de scraping

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import logging
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import sys
import os
import json

# Añadir paths
sys.path.append(str(Path(__file__).parent.parent.parent))

from .intelligent_scheduler import IntelligentScheduler
from .advanced_tier_manager import AdvancedTierManager
from .anti_detection_system import AntiDetectionSystem

logger = logging.getLogger(__name__)

class TieredOrchestratorIntegration:
    """
    🎯 Integrador que conecta el sistema de tiers inteligente 
    con el orquestador V5 existente
    """
    
    def __init__(self, orchestrator_instance):
        """
        Inicializar integración con instancia del orquestador
        
        Args:
            orchestrator_instance: Instancia de OrchestratorV5Robust
        """
        self.orchestrator = orchestrator_instance
        self.scheduler = IntelligentScheduler()
        self.running = False
        self.integration_stats = {
            'tier_executions': {'critical': 0, 'important': 0, 'tracking': 0},
            'total_scraping_sessions': 0,
            'anti_detection_activations': 0,
            'proxy_rotations': 0,
            'user_agent_changes': 0,
            'pattern_breaks': 0,
            'errors_handled': 0
        }
        
        logger.info("🎯 TieredOrchestratorIntegration inicializado")
        
        # Configurar handlers de señales
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Configurar manejo de señales para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"📢 Señal recibida: {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self, continuous: bool = True, max_runtime_hours: int = None):
        """
        🚀 Iniciar el sistema integrado de tiers
        
        Args:
            continuous: Si debe ejecutar continuamente
            max_runtime_hours: Máximo tiempo de ejecución en horas
        """
        logger.info("🚀 Iniciando sistema de orquestación por tiers...")
        
        self.running = True
        start_time = datetime.now()
        
        try:
            # Inicializar scheduler inteligente
            await self.scheduler.start()
            
            # Configurar callback de scraping personalizado
            await self._setup_scraping_callbacks()
            
            logger.info("✅ Sistema de tiers iniciado correctamente")
            
            # Bucle principal - delegamos al scheduler inteligente
            while self.running and continuous:
                # El scheduler maneja toda la lógica de timing y ejecución
                await asyncio.sleep(1.0)  # Verificación mínima
                
                # Verificar límite de tiempo si está configurado
                if max_runtime_hours:
                    elapsed = (datetime.now() - start_time).total_seconds() / 3600
                    if elapsed >= max_runtime_hours:
                        logger.info(f"⏰ Límite de tiempo alcanzado: {max_runtime_hours}h")
                        break
                
                # Verificar si el scheduler está activo
                if not self.scheduler.running:
                    logger.warning("⚠️ Scheduler inteligente se detuvo, reiniciando...")
                    await self.scheduler.start()
            
            # Si no es continuo, ejecutar una sola iteración de todos los tiers
            if not continuous:
                await self._execute_single_tier_cycle()
        
        except Exception as e:
            logger.error(f"❌ Error en sistema de tiers: {e}")
            self.integration_stats['errors_handled'] += 1
            raise
        
        finally:
            await self.stop()
    
    async def _setup_scraping_callbacks(self):
        """🔗 Configurar callbacks de scraping para el scheduler"""
        
        async def tier_scraping_callback(tier_name: str, retailers: List[str], 
                                       categories: List[str], pages: int):
            """
            Callback personalizado que ejecuta scraping usando el orquestador existente
            """
            logger.info(f"📊 Ejecutando scraping tier {tier_name}: "
                       f"{retailers} - {categories} - {pages} páginas")
            
            try:
                # Actualizar stats de integración
                self.integration_stats['tier_executions'][tier_name] += 1
                self.integration_stats['total_scraping_sessions'] += 1
                
                # Configurar temporalmente el orquestador para esta ejecución
                original_config = self.orchestrator.config.copy()
                
                # Adaptar configuración para la ejecución de tier específica
                self.orchestrator.config.update({
                    'retailers': retailers,
                    'categories': categories if categories else original_config.get('categories', {}),
                    'max_pages': pages,
                    'tier_mode': True,
                    'current_tier': tier_name
                })
                
                # Ejecutar el ciclo de scraping del orquestador
                cycle_results = await self._execute_orchestrator_cycle(retailers, categories, pages)
                
                # Restaurar configuración original
                self.orchestrator.config = original_config
                
                logger.info(f"✅ Tier {tier_name} completado: {cycle_results}")
                
                return cycle_results
                
            except Exception as e:
                logger.error(f"❌ Error en tier {tier_name}: {e}")
                self.integration_stats['errors_handled'] += 1
                return {'success': False, 'error': str(e), 'products_processed': 0}
        
        # Registrar callback en el scheduler
        self.scheduler.set_scraping_callback(tier_scraping_callback)
        
        # Configurar callback de anti-detección
        async def anti_detection_callback(action: str, details: Dict[str, Any]):
            """Callback para eventos de anti-detección"""
            logger.debug(f"🎭 Anti-detección: {action} - {details}")
            
            if action == 'proxy_rotation':
                self.integration_stats['proxy_rotations'] += 1
            elif action == 'user_agent_change':
                self.integration_stats['user_agent_changes'] += 1
            elif action == 'pattern_break':
                self.integration_stats['pattern_breaks'] += 1
            
            self.integration_stats['anti_detection_activations'] += 1
        
        self.scheduler.anti_detection.set_callback(anti_detection_callback)
    
    async def _execute_orchestrator_cycle(self, retailers: List[str], 
                                        categories: List[str], pages: int) -> Dict[str, Any]:
        """
        🔄 Ejecutar un ciclo de scraping usando el orquestrador existente
        """
        results = {
            'success': True,
            'products_processed': 0,
            'retailers_processed': [],
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            for retailer in retailers:
                if not self.running:
                    break
                
                logger.info(f"🛍️ Procesando retailer: {retailer}")
                
                try:
                    # Obtener scraper para este retailer
                    scraper = await self.orchestrator.get_scraper(retailer)
                    
                    if not scraper:
                        logger.warning(f"⚠️ No se pudo obtener scraper para {retailer}")
                        results['errors'].append(f"Scraper no disponible para {retailer}")
                        continue
                    
                    # Obtener categorías para este retailer
                    retailer_categories = self.orchestrator.config.get('categories', {}).get(retailer, [])
                    if categories:
                        # Filtrar solo las categorías solicitadas que existen para este retailer
                        retailer_categories = [cat for cat in categories if cat in retailer_categories]
                    
                    if not retailer_categories:
                        logger.warning(f"⚠️ No hay categorías válidas para {retailer}")
                        continue
                    
                    # Procesar cada categoría
                    for category in retailer_categories:
                        if not self.running:
                            break
                        
                        logger.info(f"📂 Procesando categoría: {category}")
                        
                        # Ejecutar scraping para esta categoría
                        category_results = await scraper.scrape_category(
                            category=category,
                            max_pages=pages,
                            timeout=300  # 5 minutos timeout por categoría
                        )
                        
                        if category_results and category_results.products:
                            # Procesar productos usando el orquestador
                            processed = await self.orchestrator.process_scraped_data(
                                retailer, category_results
                            )
                            
                            results['products_processed'] += len(category_results.products)
                            logger.info(f"  ✅ {len(category_results.products)} productos procesados")
                        
                        # Aplicar delay entre categorías (anti-detección)
                        await self.scheduler.anti_detection.apply_human_delay('category_change')
                    
                    results['retailers_processed'].append(retailer)
                    
                    # Delay entre retailers
                    if len(retailers) > 1:
                        await self.scheduler.anti_detection.apply_human_delay('retailer_change')
                
                except Exception as e:
                    error_msg = f"Error procesando {retailer}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    results['errors'].append(error_msg)
                    self.integration_stats['errors_handled'] += 1
            
            results['end_time'] = datetime.now()
            
            # Ejecutar detección de arbitraje si está habilitada
            if self.orchestrator.config.get('arbitrage_enabled', False):
                await self.orchestrator.detect_arbitrage_opportunities()
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"❌ Error general en ciclo de scraping: {e}")
        
        return results
    
    async def _execute_single_tier_cycle(self):
        """🔄 Ejecutar una sola iteración de todos los tiers (modo no continuo)"""
        logger.info("🔄 Ejecutando ciclo único de todos los tiers...")
        
        # Ejecutar tier crítico
        await self.scheduler._execute_tier_cycle('critical')
        
        # Pequeño delay entre tiers
        await asyncio.sleep(60)  # 1 minuto entre tiers
        
        # Ejecutar tier importante
        await self.scheduler._execute_tier_cycle('important')
        
        await asyncio.sleep(60)
        
        # Ejecutar tier de tracking
        await self.scheduler._execute_tier_cycle('tracking')
        
        logger.info("✅ Ciclo único de tiers completado")
    
    async def stop(self):
        """🛑 Detener el sistema de tiers de forma graceful"""
        logger.info("🛑 Deteniendo sistema de tiers...")
        
        self.running = False
        
        if self.scheduler and hasattr(self.scheduler, 'stop'):
            await self.scheduler.stop()
        elif self.scheduler:
            # Si no tiene método stop, solo marcamos como no running
            self.scheduler.running = False
        
        # Mostrar estadísticas finales
        self._log_final_stats()
        
        logger.info("✅ Sistema de tiers detenido correctamente")
    
    def _log_final_stats(self):
        """📊 Mostrar estadísticas finales de la integración"""
        logger.info("📊 ESTADÍSTICAS FINALES DE INTEGRACIÓN:")
        logger.info(f"  🎯 Ejecuciones por tier: {self.integration_stats['tier_executions']}")
        logger.info(f"  📈 Total sesiones de scraping: {self.integration_stats['total_scraping_sessions']}")
        logger.info(f"  🎭 Activaciones anti-detección: {self.integration_stats['anti_detection_activations']}")
        logger.info(f"  🔄 Rotaciones de proxy: {self.integration_stats['proxy_rotations']}")
        logger.info(f"  🎪 Cambios de user agent: {self.integration_stats['user_agent_changes']}")
        logger.info(f"  🎲 Rupturas de patrón: {self.integration_stats['pattern_breaks']}")
        logger.info(f"  ❌ Errores manejados: {self.integration_stats['errors_handled']}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """📊 Obtener estado actual de la integración"""
        return {
            'running': self.running,
            'scheduler_running': self.scheduler.running if self.scheduler else False,
            'stats': self.integration_stats.copy(),
            'scheduler_stats': self.scheduler.get_status() if self.scheduler else {},
            'current_time': datetime.now(),
        }


async def main():
    """🚀 Función principal para pruebas de integración"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🧪 Iniciando prueba de integración de tiers...")
    
    # Para pruebas, crear una instancia mock del orquestador
    class MockOrchestrator:
        def __init__(self):
            self.config = {
                'retailers': ['ripley', 'falabella'],
                'categories': {
                    'ripley': ['celulares', 'tablets'],
                    'falabella': ['celulares', 'computadores']
                },
                'arbitrage_enabled': True
            }
        
        async def get_scraper(self, retailer: str):
            logger.info(f"🛍️ Mock: Obteniendo scraper para {retailer}")
            return None  # Mock
        
        async def process_scraped_data(self, retailer: str, data):
            logger.info(f"📊 Mock: Procesando datos de {retailer}")
            return {'processed': True}
        
        async def detect_arbitrage_opportunities(self):
            logger.info("💰 Mock: Detectando oportunidades de arbitraje")
    
    mock_orchestrator = MockOrchestrator()
    integration = TieredOrchestratorIntegration(mock_orchestrator)
    
    try:
        # Ejecutar prueba por 2 minutos
        await integration.start(continuous=True, max_runtime_hours=0.033)  # ~2 minutos
        
    except KeyboardInterrupt:
        logger.info("⏹️ Prueba interrumpida por usuario")
    
    finally:
        await integration.stop()


if __name__ == "__main__":
    asyncio.run(main())