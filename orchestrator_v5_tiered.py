#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 ORQUESTADOR V5 CON SISTEMA DE TIERS INTELIGENTE
=================================================

Orquestador de producción V5 con sistema de tiers integrado que reemplaza
los ciclos continuos por scheduling inteligente basado en frecuencias.

Características principales:
- 🎚️ Sistema de tiers (2h/6h/24h) para operación continua optimizada
- 🎭 Anti-detección integrado (proxies, user agents, patrones humanos)
- 📊 Integración completa con Master System y PostgreSQL
- 💰 Detección automática de arbitraje con ML
- 📱 Alertas y notificaciones via Telegram
- 🔄 Rotación inteligente de páginas y categorías
- ⚡ Operación 24/7 sin patrones sospechosos

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import sys
import os
import signal
import logging
import traceback
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Configurar paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# FORZAR SOPORTE COMPLETO DE EMOJIS
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

# Configurar UTF-8
import locale
try:
    locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Chile.1252')
    except:
        pass

# Importar el orquestrador robusto existente y la integración de tiers
from orchestrator_v5_robust import OrchestratorV5Robust
from portable_orchestrator_v5.core.tiered_orchestrator_integration import TieredOrchestratorIntegration

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f'logs/orchestrator_v5_tiered_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)


class OrchestratorV5Tiered:
    """
    🎯 Orquestador V5 con sistema de tiers inteligente
    
    Combina todas las funcionalidades del orquestrador robusto V5
    con el nuevo sistema de tiers para operación continua optimizada.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar orquestador con sistema de tiers
        
        Args:
            config: Configuración personalizada del sistema
        """
        logger.info("🎯 Inicializando Orquestador V5 con Sistema de Tiers...")
        
        # Configuración por defecto
        self.config = {
            'retailers': ['ripley', 'falabella', 'paris', 'hites', 'abcdin'],
            'categories': {
                'ripley': ['celulares', 'tablets', 'computadores', 'televisores'],
                'falabella': ['celulares', 'tablets', 'computadores', 'televisores'],
                'paris': ['celulares', 'tablets', 'computadores', 'televisores'],
                'hites': ['celulares', 'computadores', 'televisores'],
                'abcdin': ['celulares', 'computadores', 'tablets', 'televisores']
            },
            'tier_system_enabled': True,
            'arbitrage_enabled': True,
            'telegram_enabled': True,
            'master_system_enabled': True,
            'postgres_enabled': True,
            'anti_detection_enabled': True,
            'continuous_mode': True,
            'max_runtime_hours': None,
            'test_mode': False
        }
        
        # Actualizar con configuración personalizada
        if config:
            self.config.update(config)
        
        # Crear instancia del orquestador robusto original
        self.base_orchestrator = OrchestratorV5Robust()
        
        # Aplicar configuración al orquestador base
        self.base_orchestrator.config.update(self.config)
        
        # Crear integración de tiers
        self.tier_integration = TieredOrchestratorIntegration(self.base_orchestrator)
        
        # Estado del sistema
        self.running = False
        self.start_time = None
        self.stats = {
            'total_runtime_hours': 0,
            'tier_executions': {'critical': 0, 'important': 0, 'tracking': 0},
            'total_products_processed': 0,
            'arbitrage_opportunities_found': 0,
            'anti_detection_activations': 0,
            'errors_handled': 0,
            'system_restarts': 0
        }
        
        logger.info("✅ Orquestador V5 Tiered inicializado correctamente")
        
        # Configurar manejo de señales
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Configurar manejo de señales para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"📢 Señal recibida: {signum}. Iniciando shutdown graceful...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self, **kwargs):
        """
        🚀 Iniciar el orquestador con sistema de tiers
        
        Args:
            continuous: Modo continuo (default: True)
            max_runtime_hours: Máximo tiempo de ejecución
            test_mode: Modo de prueba con tiempo limitado
            retailers: Lista específica de retailers
            categories: Categorías específicas por retailer
        """
        try:
            self.running = True
            self.start_time = datetime.now()
            
            # Actualizar configuración con parámetros de inicio
            if 'continuous' in kwargs:
                self.config['continuous_mode'] = kwargs['continuous']
            if 'max_runtime_hours' in kwargs:
                self.config['max_runtime_hours'] = kwargs['max_runtime_hours']
            if 'test_mode' in kwargs:
                self.config['test_mode'] = kwargs['test_mode']
            if 'retailers' in kwargs:
                self.config['retailers'] = kwargs['retailers']
            if 'categories' in kwargs:
                self.config['categories'] = kwargs['categories']
            
            logger.info("🚀 INICIANDO ORQUESTADOR V5 CON SISTEMA DE TIERS")
            logger.info("=" * 60)
            logger.info(f"🎚️ Sistema de Tiers: {'✅ ACTIVADO' if self.config['tier_system_enabled'] else '❌ DESACTIVADO'}")
            logger.info(f"🎭 Anti-detección: {'✅ ACTIVADO' if self.config['anti_detection_enabled'] else '❌ DESACTIVADO'}")
            logger.info(f"💰 Arbitraje: {'✅ ACTIVADO' if self.config['arbitrage_enabled'] else '❌ DESACTIVADO'}")
            logger.info(f"📱 Telegram: {'✅ ACTIVADO' if self.config['telegram_enabled'] else '❌ DESACTIVADO'}")
            logger.info(f"🔄 Modo continuo: {'✅ SÍ' if self.config['continuous_mode'] else '❌ NO'}")
            logger.info(f"⏰ Tiempo máximo: {self.config['max_runtime_hours'] or 'ILIMITADO'} horas")
            logger.info(f"🛍️ Retailers: {', '.join(self.config['retailers'])}")
            logger.info("=" * 60)
            
            # Inicializar el orquestador base
            logger.info("🔧 Inicializando sistemas base...")
            # El orquestador robusto se inicializa automáticamente en __init__
            
            if self.config['tier_system_enabled']:
                # Usar sistema de tiers inteligente
                logger.info("🎚️ Iniciando sistema de tiers inteligente...")
                await self.tier_integration.start(
                    continuous=self.config['continuous_mode'],
                    max_runtime_hours=self.config['max_runtime_hours']
                )
            else:
                # Usar el sistema tradicional de ciclos continuos
                logger.info("🔄 Usando sistema tradicional de ciclos continuos...")
                await self._run_traditional_mode()
            
        except Exception as e:
            logger.error(f"❌ Error crítico en el orquestador: {e}")
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            self.stats['errors_handled'] += 1
            raise
        
        finally:
            await self.stop()
    
    async def _run_traditional_mode(self):
        """🔄 Ejecutar en modo tradicional (sin tiers)"""
        logger.info("🔄 Ejecutando en modo tradicional...")
        
        cycle = 0
        
        while self.running and self.config['continuous_mode']:
            cycle += 1
            logger.info(f"🔄 Iniciando ciclo tradicional #{cycle}")
            
            try:
                # Ejecutar ciclo del orquestador base
                await self.base_orchestrator.run_cycle()
                
                # Verificar límite de tiempo
                if self.config['max_runtime_hours']:
                    elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
                    if elapsed >= self.config['max_runtime_hours']:
                        logger.info(f"⏰ Límite de tiempo alcanzado: {self.config['max_runtime_hours']}h")
                        break
                
                # Pausa entre ciclos
                if self.config['continuous_mode']:
                    await asyncio.sleep(300)  # 5 minutos entre ciclos
                
            except Exception as e:
                logger.error(f"❌ Error en ciclo #{cycle}: {e}")
                self.stats['errors_handled'] += 1
                await asyncio.sleep(60)  # Pausa más corta en caso de error
        
        # Si no es continuo, ejecutar solo un ciclo
        if not self.config['continuous_mode']:
            await self.base_orchestrator.run_cycle()
    
    async def stop(self):
        """🛑 Detener el orquestador de forma graceful"""
        if not self.running:
            return
        
        logger.info("🛑 Deteniendo Orquestador V5 Tiered...")
        
        self.running = False
        
        # Detener integración de tiers
        if self.tier_integration:
            await self.tier_integration.stop()
        
        # Detener orquestador base
        if hasattr(self.base_orchestrator, 'stop'):
            await self.base_orchestrator.stop()
        
        # Calcular estadísticas finales
        if self.start_time:
            total_time = (datetime.now() - self.start_time).total_seconds() / 3600
            self.stats['total_runtime_hours'] = round(total_time, 2)
        
        # Mostrar estadísticas finales
        self._log_final_statistics()
        
        logger.info("✅ Orquestador V5 Tiered detenido correctamente")
    
    def _log_final_statistics(self):
        """📊 Mostrar estadísticas finales del sistema"""
        logger.info("📊 ESTADÍSTICAS FINALES DEL ORQUESTADOR V5 TIERED")
        logger.info("=" * 60)
        logger.info(f"⏰ Tiempo total de ejecución: {self.stats['total_runtime_hours']} horas")
        
        if self.tier_integration:
            tier_stats = self.tier_integration.get_integration_status()
            logger.info(f"🎚️ Ejecuciones por tier: {tier_stats['stats']['tier_executions']}")
            logger.info(f"📈 Sesiones de scraping: {tier_stats['stats']['total_scraping_sessions']}")
            logger.info(f"🎭 Activaciones anti-detección: {tier_stats['stats']['anti_detection_activations']}")
            logger.info(f"🔄 Rotaciones de proxy: {tier_stats['stats']['proxy_rotations']}")
            logger.info(f"🎪 Cambios de user agent: {tier_stats['stats']['user_agent_changes']}")
            logger.info(f"🎲 Rupturas de patrón: {tier_stats['stats']['pattern_breaks']}")
        
        if hasattr(self.base_orchestrator, 'stats'):
            base_stats = self.base_orchestrator.stats
            logger.info(f"📦 Productos procesados: {base_stats.get('products_processed', 0)}")
            logger.info(f"💰 Oportunidades de arbitraje: {base_stats.get('arbitrage_opportunities', 0)}")
            logger.info(f"🔄 Ciclos completados: {base_stats.get('cycles_completed', 0)}")
        
        logger.info(f"❌ Errores manejados: {self.stats['errors_handled']}")
        logger.info("=" * 60)
    
    def get_system_status(self) -> Dict[str, Any]:
        """📊 Obtener estado completo del sistema"""
        status = {
            'running': self.running,
            'config': self.config.copy(),
            'stats': self.stats.copy(),
            'start_time': self.start_time,
            'current_time': datetime.now(),
            'uptime_hours': 0
        }
        
        if self.start_time:
            status['uptime_hours'] = round(
                (datetime.now() - self.start_time).total_seconds() / 3600, 2
            )
        
        # Agregar estado de la integración de tiers
        if self.tier_integration:
            status['tier_integration'] = self.tier_integration.get_integration_status()
        
        # Agregar estado del orquestador base
        if hasattr(self.base_orchestrator, 'get_status'):
            status['base_orchestrator'] = self.base_orchestrator.get_status()
        
        return status


async def main():
    """🚀 Función principal del orquestador V5 Tiered"""
    parser = argparse.ArgumentParser(
        description='🎯 Orquestador V5 con Sistema de Tiers Inteligente'
    )
    
    parser.add_argument(
        '--retailers',
        nargs='+',
        default=['ripley', 'falabella', 'paris'],
        help='Lista de retailers a procesar'
    )
    
    parser.add_argument(
        '--continuous',
        action='store_true',
        default=True,
        help='Ejecutar en modo continuo'
    )
    
    parser.add_argument(
        '--max-runtime',
        type=float,
        help='Tiempo máximo de ejecución en horas'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo de prueba (10 minutos)'
    )
    
    parser.add_argument(
        '--disable-tiers',
        action='store_true',
        help='Desactivar sistema de tiers (usar modo tradicional)'
    )
    
    parser.add_argument(
        '--disable-arbitrage',
        action='store_true',
        help='Desactivar detección de arbitraje'
    )
    
    parser.add_argument(
        '--disable-telegram',
        action='store_true',
        help='Desactivar notificaciones de Telegram'
    )
    
    args = parser.parse_args()
    
    # Configurar basándose en argumentos
    config = {
        'retailers': args.retailers,
        'continuous_mode': args.continuous,
        'max_runtime_hours': args.max_runtime,
        'test_mode': args.test,
        'tier_system_enabled': not args.disable_tiers,
        'arbitrage_enabled': not args.disable_arbitrage,
        'telegram_enabled': not args.disable_telegram
    }
    
    # Modo de prueba
    if args.test:
        config['max_runtime_hours'] = 0.167  # 10 minutos
        config['test_mode'] = True
    
    orchestrator = OrchestratorV5Tiered(config)
    
    try:
        await orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Ejecución interrumpida por usuario")
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    # Crear directorios de logs si no existen
    os.makedirs('logs', exist_ok=True)
    
    # Ejecutar orquestador
    asyncio.run(main())