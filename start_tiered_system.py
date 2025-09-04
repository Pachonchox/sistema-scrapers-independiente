#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 INICIADOR SISTEMA V5 CON TIERS INTELIGENTE
============================================

Script de inicio simplificado para el sistema completo V5 con:
- 🎚️ Sistema de tiers inteligente (2h/6h/24h)
- 🎭 Anti-detección automática
- 💰 Arbitraje con ML
- 📱 Telegram bot integrado
- 🗄️ PostgreSQL + Redis backend

Uso:
    python start_tiered_system.py                    # Modo completo
    python start_tiered_system.py --test             # Modo prueba 10min
    python start_tiered_system.py --retailers ripley falabella
    python start_tiered_system.py --max-runtime 2    # 2 horas máximo

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import argparse
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.append(str(Path(__file__).parent))

# FORZAR SOPORTE COMPLETO DE EMOJIS
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

from orchestrator_v5_tiered import OrchestratorV5Tiered

# Configurar logging mejorado
def setup_logging(test_mode: bool = False):
    """Configurar sistema de logging con emojis"""
    
    log_level = logging.DEBUG if test_mode else logging.INFO
    
    # Crear directorio de logs
    os.makedirs('logs', exist_ok=True)
    
    # Formato con emojis
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Handler para archivo
    log_file = f'logs/tiered_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger


def print_banner():
    """Mostrar banner del sistema"""
    print("🎯" + "=" * 58 + "🎯")
    print("🚀         SISTEMA V5 CON TIERS INTELIGENTE         🚀")
    print("🎯" + "=" * 58 + "🎯")
    print("🎚️ Tiers: Crítico(2h) | Importante(6h) | Seguimiento(24h)")
    print("🎭 Anti-detección: Proxies + User Agents + Patrones Humanos")
    print("💰 Arbitraje ML: Detección automática de oportunidades")
    print("📱 Telegram: Alertas y notificaciones en tiempo real")
    print("🗄️ Backend: PostgreSQL + Redis para máximo rendimiento")
    print("🎯" + "=" * 58 + "🎯")


async def check_system_requirements():
    """🔍 Verificar requisitos del sistema"""
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Verificando requisitos del sistema...")
    
    checks = []
    
    # Verificar Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        checks.append("✅ Python 3.8+ disponible")
    else:
        checks.append("❌ Python 3.8+ requerido")
        return False
    
    # Verificar módulos críticos
    critical_modules = [
        'asyncio', 'logging', 'datetime', 'json', 'pathlib', 'playwright'
    ]
    
    for module in critical_modules:
        try:
            __import__(module)
            checks.append(f"✅ {module}")
        except ImportError:
            checks.append(f"❌ {module} (requerido)")
    
    # Verificar módulos opcionales
    optional_modules = [
        ('psycopg2', 'PostgreSQL backend'),
        ('redis', 'Redis caching')  # Usar redis en lugar de aioredis
    ]
    
    for module, description in optional_modules:
        try:
            __import__(module)
            checks.append(f"✅ {module} ({description})")
        except (ImportError, TypeError, Exception) as e:
            checks.append(f"⚠️ {module} ({description} - opcional, error: {type(e).__name__})")
    
    # Verificar archivos críticos del sistema
    critical_files = [
        'portable_orchestrator_v5/core/intelligent_scheduler.py',
        'portable_orchestrator_v5/core/advanced_tier_manager.py',
        'portable_orchestrator_v5/core/anti_detection_system.py',
        'portable_orchestrator_v5/core/tiered_orchestrator_integration.py'
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            checks.append(f"✅ {Path(file_path).name}")
        else:
            checks.append(f"❌ {Path(file_path).name} (crítico)")
    
    # Mostrar resultados
    for check in checks:
        logger.info(f"  {check}")
    
    # Verificar si hay errores críticos (solo módulos críticos bloquean)
    critical_failed = [check for check in checks if check.startswith("❌") and "(requerido)" in check]
    optional_missing = [check for check in checks if check.startswith("⚠️")]
    
    if critical_failed:
        logger.error("❌ Faltan requisitos críticos del sistema:")
        for failed in critical_failed:
            logger.error(f"  {failed}")
        return False
    
    if optional_missing:
        logger.warning("⚠️ Módulos opcionales no disponibles:")
        for missing in optional_missing:
            logger.warning(f"  {missing}")
        logger.info("💡 El sistema funcionará con funcionalidad reducida")
    
    logger.info("✅ Todos los requisitos del sistema verificados correctamente")
    return True


def create_default_config(args) -> dict:
    """📋 Crear configuración por defecto basada en argumentos"""
    
    # Configuración base
    config = {
        'retailers': ['ripley', 'falabella', 'paris'],
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
        'continuous_mode': not args.single_run,
        'max_runtime_hours': args.max_runtime,
        'test_mode': args.test
    }
    
    # Aplicar parámetros específicos
    if args.retailers:
        config['retailers'] = args.retailers
    
    if args.test:
        config['max_runtime_hours'] = 0.167  # 10 minutos
        config['test_mode'] = True
        # En modo test, usar solo retailers principales
        config['retailers'] = ['ripley', 'falabella']
    
    if args.disable_tiers:
        config['tier_system_enabled'] = False
    
    if args.disable_arbitrage:
        config['arbitrage_enabled'] = False
    
    if args.disable_telegram:
        config['telegram_enabled'] = False
    
    return config


async def main():
    """🚀 Función principal del iniciador"""
    
    parser = argparse.ArgumentParser(
        description='🎯 Sistema V5 con Tiers Inteligente',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🌟 EJEMPLOS DE USO:

  # Modo completo (recomendado)
  python start_tiered_system.py
  
  # Modo prueba (10 minutos)
  python start_tiered_system.py --test
  
  # Retailers específicos
  python start_tiered_system.py --retailers ripley falabella
  
  # Tiempo máximo de ejecución
  python start_tiered_system.py --max-runtime 8
  
  # Solo una ejecución (no continuo)
  python start_tiered_system.py --single-run
  
  # Sin sistema de tiers (modo tradicional)
  python start_tiered_system.py --disable-tiers

🎚️ CONFIGURACIÓN DE TIERS:
  - Tier 1 (Crítico): Tecnología - cada 2 horas
  - Tier 2 (Importante): Hogar/Electrodomésticos - cada 6 horas  
  - Tier 3 (Seguimiento): Otros productos - cada 24 horas

🎭 ANTI-DETECCIÓN:
  - Rotación automática de proxies
  - Cambio de user agents
  - Patrones de navegación humanos
  - Delays aleatorios entre requests
        """
    )
    
    # Argumentos principales
    parser.add_argument(
        '--retailers',
        nargs='+',
        choices=['ripley', 'falabella', 'paris', 'hites', 'abcdin', 'mercadolibre'],
        help='🛍️ Retailers específicos a procesar'
    )
    
    parser.add_argument(
        '--max-runtime',
        type=float,
        help='⏰ Tiempo máximo de ejecución en horas'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='🧪 Modo de prueba (10 minutos, retailers limitados)'
    )
    
    parser.add_argument(
        '--single-run',
        action='store_true',
        help='🔄 Ejecutar solo una vez (no continuo)'
    )
    
    # Argumentos de control
    parser.add_argument(
        '--disable-tiers',
        action='store_true',
        help='🎚️ Desactivar sistema de tiers (usar modo tradicional)'
    )
    
    parser.add_argument(
        '--disable-arbitrage',
        action='store_true',
        help='💰 Desactivar detección de arbitraje'
    )
    
    parser.add_argument(
        '--disable-telegram',
        action='store_true',
        help='📱 Desactivar notificaciones de Telegram'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='📝 Logging detallado (modo debug)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(test_mode=args.test or args.verbose)
    logger = logging.getLogger(__name__)
    
    # Mostrar banner
    print_banner()
    
    try:
        # Verificar requisitos del sistema
        if not await check_system_requirements():
            logger.error("❌ El sistema no cumple con los requisitos mínimos")
            sys.exit(1)
        
        # Crear configuración
        config = create_default_config(args)
        
        logger.info("📋 CONFIGURACIÓN DEL SISTEMA:")
        logger.info(f"  🛍️ Retailers: {', '.join(config['retailers'])}")
        logger.info(f"  🎚️ Sistema de Tiers: {'✅' if config['tier_system_enabled'] else '❌'}")
        logger.info(f"  💰 Arbitraje ML: {'✅' if config['arbitrage_enabled'] else '❌'}")
        logger.info(f"  📱 Telegram: {'✅' if config['telegram_enabled'] else '❌'}")
        logger.info(f"  🔄 Modo continuo: {'✅' if config['continuous_mode'] else '❌'}")
        logger.info(f"  ⏰ Tiempo máximo: {config['max_runtime_hours'] or 'ILIMITADO'} horas")
        logger.info(f"  🧪 Modo test: {'✅' if config['test_mode'] else '❌'}")
        
        # Crear y iniciar orquestador
        logger.info("🚀 Iniciando Orquestador V5 con Sistema de Tiers...")
        
        orchestrator = OrchestratorV5Tiered(config)
        
        # Iniciar sistema (tarea cancelable para responder a Ctrl+C)
        orch_task = asyncio.create_task(orchestrator.start())
        await orch_task
        
    except KeyboardInterrupt:
        logger.info("⏹️ Sistema detenido por el usuario (Ctrl+C)")
        
    except Exception as e:
        logger.error(f"❌ Error crítico en el sistema: {e}")
        import traceback
        logger.error(f"📋 Traceback completo:\n{traceback.format_exc()}")
        sys.exit(1)
    
    finally:
        logger.info("✅ Sistema completamente detenido")


if __name__ == "__main__":
    # Ejecutar sistema
    asyncio.run(main())
