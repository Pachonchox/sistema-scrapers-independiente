#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 EJECUTOR DEL ORQUESTADOR V5
================================
Script para ejecutar el orquestador V5 con opciones configurables
"""

import asyncio
import argparse
import os
import sys
import io
from pathlib import Path

# Añadir paths necesarios
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# FORZAR SOPORTE COMPLETO DE EMOJIS
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()


def setup_environment(args):
    """Configurar variables de entorno basadas en argumentos"""
    
    # Backend y sistemas
    os.environ['DATA_BACKEND'] = args.backend
    os.environ['MASTER_SYSTEM_ENABLED'] = 'true' if args.master else 'false'
    os.environ['ARBITRAGE_ENABLED'] = 'true' if args.arbitrage else 'false'
    os.environ['NORMALIZATION_ENABLED'] = 'true' if args.normalization else 'false'
    
    # Tiempos y configuración
    os.environ['MAX_RUNTIME_MINUTES'] = str(args.runtime)
    os.environ['CYCLE_PAUSE_SECONDS'] = str(args.pause)
    os.environ['BATCH_SIZE'] = str(args.batch)
    os.environ['MAX_RETRIES'] = str(args.retries)
    
    # Scrapers
    if args.scrapers:
        os.environ['SCRAPERS_ENABLED'] = ','.join(args.scrapers)
    
    # PostgreSQL si es necesario
    if args.backend == 'postgres':
        if args.pghost:
            os.environ['PGHOST'] = args.pghost
        if args.pgport:
            os.environ['PGPORT'] = str(args.pgport)
        if args.pgdb:
            os.environ['PGDATABASE'] = args.pgdb


async def run_orchestrator():
    """Ejecutar el orquestador"""
    
    from orchestrator_v5_robust import OrchestratorV5Robust
    
    orchestrator = OrchestratorV5Robust()
    await orchestrator.run_production()


def main():
    """Función principal con argumentos CLI"""
    
    parser = argparse.ArgumentParser(
        description='🚀 Orquestador V5 - Sistema Completo de Scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Ejecución estándar (1 hora)
  python run_orchestrator_v5.py

  # Test rápido (5 minutos)
  python run_orchestrator_v5.py --runtime 5 --test

  # Solo Paris y Ripley con PostgreSQL
  python run_orchestrator_v5.py --scrapers paris ripley --backend postgres

  # Modo completo con todos los sistemas
  python run_orchestrator_v5.py --master --arbitrage --normalization

  # Configuración personalizada
  python run_orchestrator_v5.py --runtime 30 --batch 50 --pause 60
        """
    )
    
    # Argumentos de configuración
    parser.add_argument(
        '--runtime', 
        type=int, 
        default=60,
        help='Tiempo máximo de ejecución en minutos (default: 60)'
    )
    
    parser.add_argument(
        '--pause', 
        type=int, 
        default=30,
        help='Pausa entre ciclos en segundos (default: 30)'
    )
    
    parser.add_argument(
        '--batch', 
        type=int, 
        default=30,
        help='Productos por batch/categoría (default: 30)'
    )
    
    parser.add_argument(
        '--retries', 
        type=int, 
        default=3,
        help='Número máximo de reintentos (default: 3)'
    )
    
    # Scrapers
    parser.add_argument(
        '--scrapers', 
        nargs='+',
        choices=['paris', 'ripley', 'falabella'],
        default=['paris', 'ripley', 'falabella'],
        help='Scrapers a ejecutar (default: todos)'
    )
    
    # Backend
    parser.add_argument(
        '--backend',
        choices=['postgres', 'excel'],
        default='postgres',
        help='Backend de almacenamiento (default: postgres)'
    )
    
    # Sistemas opcionales
    parser.add_argument(
        '--master',
        action='store_true',
        default=True,
        help='Habilitar Master System (default: True)'
    )
    
    parser.add_argument(
        '--arbitrage',
        action='store_true',
        default=True,
        help='Habilitar detección de arbitraje (default: True)'
    )
    
    parser.add_argument(
        '--normalization',
        action='store_true',
        default=True,
        help='Habilitar normalización ML (default: True)'
    )
    
    # PostgreSQL
    parser.add_argument(
        '--pghost',
        default='localhost',
        help='Host de PostgreSQL (default: localhost)'
    )
    
    parser.add_argument(
        '--pgport',
        type=int,
        default=5432,
        help='Puerto de PostgreSQL (default: 5432)'
    )
    
    parser.add_argument(
        '--pgdb',
        default='orchestrator',
        help='Base de datos PostgreSQL (default: orchestrator)'
    )
    
    # Modo test
    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo test: 5 minutos, 10 productos por batch'
    )
    
    args = parser.parse_args()
    
    # Aplicar configuración de test si es necesario
    if args.test:
        args.runtime = 5
        args.batch = 10
        args.pause = 15
        print("🧪 MODO TEST ACTIVADO: 5 minutos, 10 productos por batch")
    
    # Mostrar configuración
    print("\n" + "="*60)
    print("🚀 CONFIGURACIÓN DEL ORQUESTADOR V5")
    print("="*60)
    print(f"⏱️  Tiempo máximo: {args.runtime} minutos")
    print(f"⏸️  Pausa entre ciclos: {args.pause} segundos")
    print(f"📦 Productos por batch: {args.batch}")
    print(f"🔄 Reintentos máximos: {args.retries}")
    print(f"🕷️  Scrapers: {', '.join(args.scrapers)}")
    print(f"💾 Backend: {args.backend}")
    print(f"🎯 Master System: {'Sí' if args.master else 'No'}")
    print(f"💰 Arbitraje: {'Sí' if args.arbitrage else 'No'}")
    print(f"🤖 Normalización ML: {'Sí' if args.normalization else 'No'}")
    
    if args.backend == 'postgres':
        print(f"🐘 PostgreSQL: {args.pghost}:{args.pgport}/{args.pgdb}")
    
    print("="*60)
    
    # Configurar entorno
    setup_environment(args)
    
    # Ejecutar orquestador
    print("\n🚀 Iniciando orquestador...")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        asyncio.run(run_orchestrator())
        
    except KeyboardInterrupt:
        print("\n\n✋ Detenido por usuario")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()