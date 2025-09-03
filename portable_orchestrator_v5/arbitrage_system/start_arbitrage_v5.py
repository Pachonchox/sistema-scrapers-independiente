#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Start Arbitrage V5 - Script de Inicio Sistema Arbitraje Autónomo
==================================================================
Script principal para iniciar el sistema de arbitraje V5 completamente autónomo.
Compatible con emojis y optimizado para operación continua no supervisada.

Uso:
    python start_arbitrage_v5.py                    # Modo producción
    python start_arbitrage_v5.py --dev              # Modo desarrollo
    python start_arbitrage_v5.py --test             # Modo test (5 min)
    python start_arbitrage_v5.py --status           # Ver estado
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Agregar el directorio padre al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importaciones V5 completamente autónomas
from portable_orchestrator_v5.arbitrage_system.core.arbitrage_engine import ArbitrageEngineV5, create_arbitrage_engine_v5
from portable_orchestrator_v5.arbitrage_system.config.arbitrage_config import get_config, PRODUCTION_CONFIG, DEVELOPMENT_CONFIG
from portable_orchestrator_v5.arbitrage_system.database.db_manager import get_db_manager

# Configurar logging principal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - 🚀 ArbitrageV5 - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ArbitrageV5Launcher:
    """
    Lanzador del sistema de arbitraje V5 🚀
    
    Maneja inicio, configuración y monitoreo del sistema completo
    """
    
    def __init__(self):
        self.engine = None
        self.config = None
        self.mode = 'production'
        
    async def start_system(self, mode: str = 'production', test_duration_minutes: int = None):
        """
        Iniciar sistema completo de arbitraje V5 🎯
        
        Args:
            mode: 'production', 'development', 'test'
            test_duration_minutes: Duración en modo test
        """
        try:
            logger.info("🚀 INICIANDO SISTEMA DE ARBITRAJE V5 AUTÓNOMO")
            logger.info("=" * 60)
            
            self.mode = mode
            
            # Seleccionar configuración
            if mode == 'production':
                self.config = PRODUCTION_CONFIG
                logger.info("🏭 Modo: PRODUCCIÓN - Configuración optimizada")
            elif mode == 'development':
                self.config = DEVELOPMENT_CONFIG
                logger.info("🔧 Modo: DESARROLLO - Configuración debug")
            else:  # test
                self.config = DEVELOPMENT_CONFIG
                logger.info(f"🧪 Modo: TEST - Duración: {test_duration_minutes} minutos")
            
            # Mostrar configuración
            self._display_config()
            
            # Verificar prerequisitos
            await self._check_prerequisites()
            
            # Crear e inicializar engine
            logger.info("🔧 Creando ArbitrageEngine V5...")
            self.engine = await create_arbitrage_engine_v5(self.config)
            
            # Iniciar engine
            logger.info("⚡ Iniciando motor de arbitraje...")
            await self.engine.start_engine()
            
            # Modo test con duración limitada
            if mode == 'test' and test_duration_minutes:
                logger.info(f"⏱️ Ejecutando en modo test por {test_duration_minutes} minutos...")
                await asyncio.sleep(test_duration_minutes * 60)
                logger.info("⏰ Tiempo de test completado")
                
            else:
                # Modo continuo
                logger.info("🔄 Sistema en operación continua - Presiona Ctrl+C para detener")
                
                # Mostrar estado inicial
                await self._display_initial_status()
                
                # Loop de monitoreo
                await self._monitoring_loop()
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrupción de usuario detectada")
        except Exception as e:
            logger.error(f"❌ Error crítico en sistema: {e}")
            raise
        finally:
            await self._shutdown_system()
    
    def _display_config(self):
        """Mostrar configuración actual 📋"""
        try:
            logger.info("📋 CONFIGURACIÓN ACTUAL:")
            logger.info(f"   💰 Margen mínimo: ${self.config.min_margin_clp:,.0f} CLP")
            logger.info(f"   📊 ROI mínimo: {self.config.min_percentage}%")
            logger.info(f"   🎯 Similaridad ML: {self.config.min_similarity_score}")
            logger.info(f"   🏪 Retailers: {len(self.config.retailers_enabled)} activos")
            logger.info(f"   🧠 Inteligencia V5: {'✅ Activada' if self.config.use_redis_intelligence else '❌ Desactivada'}")
            logger.info(f"   ⚡ Cache inteligente: {'✅ L1-L4' if self.config.use_intelligent_cache else '❌ Básico'}")
            logger.info(f"   🚨 Alertas emoji: {'✅ Activadas' if self.config.enable_emoji_alerts else '❌ Desactivadas'}")
            logger.info("─" * 50)
            
        except Exception as e:
            logger.warning(f"⚠️ Error mostrando configuración: {e}")
    
    async def _check_prerequisites(self):
        """Verificar prerequisitos del sistema 🔍"""
        try:
            logger.info("🔍 Verificando prerequisitos...")
            
            # Verificar base de datos
            db_manager = get_db_manager(self.config)
            
            try:
                await db_manager.initialize_async_pool()
                health = await db_manager.health_check()
                
                if health['status'] == 'healthy':
                    logger.info(f"✅ PostgreSQL: Conectado ({health.get('v5_tables_count', 0)} tablas V5)")
                else:
                    raise Exception(f"Database no saludable: {health}")
                    
            except Exception as e:
                logger.error(f"❌ Error conexión PostgreSQL: {e}")
                logger.error("💡 Verifica que PostgreSQL esté ejecutándose y accesible")
                raise
            
            # Verificar Redis (si está habilitado)
            if self.config.use_redis_intelligence or self.config.use_intelligent_cache:
                try:
                    # Test básico Redis
                    import redis
                    redis_client = redis.Redis(
                        host=self.config.redis_config['host'],
                        port=self.config.redis_config['port'],
                        db=self.config.redis_config['db'],
                        socket_timeout=5
                    )
                    redis_client.ping()
                    logger.info("✅ Redis: Conectado y operativo")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Redis no disponible: {e}")
                    logger.warning("🔧 Continuando sin funciones de inteligencia Redis...")
            
            # Verificar puertos
            logger.info(f"🔌 PostgreSQL: {self.config.database_config['host']}:{self.config.database_config['port']}")
            if self.config.use_redis_intelligence:
                logger.info(f"🔥 Redis: {self.config.redis_config['host']}:{self.config.redis_config['port']}")
            
            logger.info("✅ Prerequisitos verificados")
            
        except Exception as e:
            logger.error(f"❌ Fallo en verificación de prerequisitos: {e}")
            raise
    
    async def _display_initial_status(self):
        """Mostrar estado inicial del sistema 📊"""
        try:
            logger.info("📊 ESTADO INICIAL DEL SISTEMA:")
            
            if self.engine:
                status = await self.engine.get_engine_status()
                
                logger.info(f"   🆔 Engine ID: {status.get('engine_id')}")
                logger.info(f"   ⚡ Componentes V5: {sum(status.get('components', {}).values())}/8 activos")
                
                db_health = status.get('database_health', {})
                if db_health:
                    logger.info(f"   🗄️ Base de datos: {db_health.get('status')} ")
                    logger.info(f"   📋 Oportunidades hoy: {db_health.get('opportunities_today', 0)}")
                
                config_info = status.get('configuration', {})
                logger.info(f"   🏪 Retailers: {', '.join(config_info.get('retailers_enabled', []))}")
            
            logger.info("═" * 50)
            
        except Exception as e:
            logger.warning(f"⚠️ Error mostrando estado inicial: {e}")
    
    async def _monitoring_loop(self):
        """Loop de monitoreo del sistema 👁️"""
        try:
            last_status_time = datetime.now()
            
            while True:
                await asyncio.sleep(30)  # Monitorear cada 30 segundos
                
                # Estado cada 5 minutos
                if (datetime.now() - last_status_time).total_seconds() >= 300:
                    await self._display_periodic_status()
                    last_status_time = datetime.now()
                
                # Verificar que el engine siga corriendo
                if self.engine and not self.engine.is_running:
                    logger.warning("⚠️ Engine se detuvo inesperadamente")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error en loop de monitoreo: {e}")
    
    async def _display_periodic_status(self):
        """Mostrar estado periódico 📈"""
        try:
            if not self.engine:
                return
                
            status = await self.engine.get_engine_status()
            metrics = status.get('metrics', {})
            
            uptime_hours = status.get('uptime_seconds', 0) / 3600
            
            logger.info("📈 ESTADO PERIÓDICO:")
            logger.info(f"   ⏱️ Tiempo operación: {uptime_hours:.1f} horas")
            logger.info(f"   🔄 Ciclos ejecutados: {metrics.get('total_cycles', 0)}")
            logger.info(f"   ✅ Tasa éxito: {metrics.get('successful_cycles', 0)}/{metrics.get('total_cycles', 0)}")
            logger.info(f"   💰 Oportunidades detectadas: {metrics.get('total_opportunities_detected', 0)}")
            logger.info(f"   💾 Oportunidades guardadas: {metrics.get('total_opportunities_saved', 0)}")
            
            # Performance cache si está disponible
            cache_perf = status.get('cache_performance', {})
            if cache_perf:
                logger.info(f"   ⚡ Cache hits L1/L2: {cache_perf.get('l1_hits', 0)}/{cache_perf.get('l2_hits', 0)}")
            
            logger.info("─" * 40)
            
        except Exception as e:
            logger.debug(f"⚠️ Error mostrando estado periódico: {e}")
    
    async def _shutdown_system(self):
        """Apagar sistema limpiamente 🔚"""
        try:
            logger.info("🔚 Apagando sistema de arbitraje V5...")
            
            if self.engine:
                await self.engine.stop_engine()
                
                # Mostrar estadísticas finales
                final_status = await self.engine.get_engine_status()
                metrics = final_status.get('metrics', {})
                
                logger.info("📊 ESTADÍSTICAS FINALES:")
                logger.info(f"   🔄 Ciclos totales: {metrics.get('total_cycles', 0)}")
                logger.info(f"   ✅ Ciclos exitosos: {metrics.get('successful_cycles', 0)}")
                logger.info(f"   💰 Oportunidades totales: {metrics.get('total_opportunities_detected', 0)}")
                logger.info(f"   💾 Guardadas exitosamente: {metrics.get('total_opportunities_saved', 0)}")
                logger.info(f"   📈 Promedio duración ciclo: {metrics.get('avg_cycle_duration_seconds', 0):.1f}s")
            
            logger.info("🎉 Sistema de arbitraje V5 apagado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error apagando sistema: {e}")
    
    async def show_status(self):
        """Mostrar estado actual del sistema sin iniciarlo 📊"""
        try:
            logger.info("📊 CONSULTANDO ESTADO DEL SISTEMA...")
            
            # Verificar conexiones básicas
            await self._check_prerequisites()
            
            # Obtener métricas de BD
            db_manager = get_db_manager(self.config)
            performance = await db_manager.get_performance_summary(days=1)
            
            logger.info("📈 RESUMEN ÚLTIMAS 24 HORAS:")
            logger.info(f"   💰 Oportunidades detectadas: {performance.get('total_opportunities', 0)}")
            logger.info(f"   ✅ Oportunidades válidas: {performance.get('total_valid', 0)}")
            logger.info(f"   📊 Tasa éxito: {performance.get('success_rate', 0)*100:.1f}%")
            
            if performance.get('total_margin'):
                logger.info(f"   💵 Margen total: ${performance.get('total_margin', 0):,.0f} CLP")
                logger.info(f"   📈 ROI promedio: {performance.get('avg_roi', 0):.1f}%")
            
            # Estado de tablas
            health = await db_manager.health_check()
            logger.info(f"   🗄️ Estado BD: {health.get('status')}")
            logger.info(f"   📋 Tablas V5: {health.get('v5_tables_count', 0)}")
            
            # Oportunidades recientes
            recent_opps = await db_manager.get_active_opportunities(limit=5)
            if recent_opps:
                logger.info(f"   🔥 Oportunidades activas: {len(recent_opps)}")
                
                best_opp = max(recent_opps, key=lambda x: x.get('margen_bruto', 0))
                logger.info(f"   🏆 Mejor oportunidad: ${best_opp.get('margen_bruto', 0):,.0f} CLP")
            else:
                logger.info("   📊 Sin oportunidades activas")
                
            await db_manager.close()
            
        except Exception as e:
            logger.error(f"❌ Error consultando estado: {e}")

async def main():
    """Función principal 🎯"""
    parser = argparse.ArgumentParser(
        description="🚀 Sistema de Arbitraje V5 Autónomo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python start_arbitrage_v5.py                    # Producción continua
  python start_arbitrage_v5.py --dev              # Modo desarrollo  
  python start_arbitrage_v5.py --test --minutes 5 # Test 5 minutos
  python start_arbitrage_v5.py --status           # Solo mostrar estado
        """
    )
    
    parser.add_argument('--dev', action='store_true', 
                       help='Ejecutar en modo desarrollo')
    parser.add_argument('--test', action='store_true',
                       help='Ejecutar en modo test')
    parser.add_argument('--minutes', type=int, default=5,
                       help='Duración en minutos para modo test (default: 5)')
    parser.add_argument('--status', action='store_true',
                       help='Solo mostrar estado actual')
    
    args = parser.parse_args()
    
    launcher = ArbitrageV5Launcher()
    
    try:
        if args.status:
            # Solo mostrar estado
            await launcher.show_status()
        else:
            # Determinar modo
            if args.dev:
                mode = 'development'
            elif args.test:
                mode = 'test'
            else:
                mode = 'production'
            
            # Iniciar sistema
            test_duration = args.minutes if args.test else None
            await launcher.start_system(mode, test_duration)
            
    except KeyboardInterrupt:
        logger.info("🛑 Programa interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando programa: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Forzar soporte UTF-8 para emojis en Windows
    if sys.platform == 'win32':
        import codecs
        import io
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # Ejecutar con manejo de emojis
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)