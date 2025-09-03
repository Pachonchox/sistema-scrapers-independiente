# -*- coding: utf-8 -*-
"""
🚀 INICIADOR DEL MOTOR DE ARBITRAJE BACKEND
===========================================

Script para iniciar el motor de arbitraje de forma independiente.
Funciona completamente separado del flujo principal de scraping.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend_arbitrage_engine import BackendArbitrageEngine, ArbitrageConfig

def start_arbitrage_system():
    """Inicia el sistema completo de arbitraje"""
    
    print("🤖 SISTEMA DE ARBITRAJE BACKEND INDEPENDIENTE")
    print("=" * 55)
    print("✅ Separado del flujo principal de scraping")
    print("✅ Utiliza ML existente para matching")
    print("✅ Detección automática de oportunidades")
    print("✅ Persistencia en PostgreSQL")
    print("=" * 55)
    
    # Configuración de base de datos
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    # Configuración del motor
    config = ArbitrageConfig(
        min_margin_clp=10000.0,       # Margen mínimo $10K (más permisivo para testing)
        min_percentage=15.0,          # ROI mínimo 15% 
        min_similarity_score=0.7,     # Similitud mínima 70% (más permisivo)
        update_frequency_minutes=30,  # Cada 30 minutos para testing
        enable_auto_alerts=True,
        max_opportunities_per_run=50,
        retailers_to_compare=['falabella', 'ripley', 'paris']
    )
    
    print(f"📊 CONFIGURACIÓN:")
    print(f"   💰 Margen mínimo: ${config.min_margin_clp:,}")
    print(f"   📈 ROI mínimo: {config.min_percentage}%")
    print(f"   🎯 Similitud ML mínima: {config.min_similarity_score}")
    print(f"   ⏱️  Frecuencia: cada {config.update_frequency_minutes} min")
    print(f"   🏪 Retailers: {', '.join(config.retailers_to_compare)}")
    print("=" * 55)
    
    # Crear motor
    engine = BackendArbitrageEngine(db_params, config)
    
    # Opciones de ejecución
    print("\nOPCIONES:")
    print("1. [ENTER] - Ciclo manual único (testing)")
    print("2. 'c' - Modo continuo (producción)")
    print("3. 'q' - Salir")
    
    choice = input("\nSeleccionar opción: ").lower().strip()
    
    if choice == 'q':
        print("👋 Saliendo...")
        return
    
    elif choice == 'c':
        print("\n🟢 INICIANDO MODO CONTINUO...")
        print("Presiona Ctrl+C para detener")
        try:
            engine.start_engine()
        except KeyboardInterrupt:
            print("\n🛑 Detenido por usuario")
    
    else:
        print("\n⚡ EJECUTANDO CICLO MANUAL...")
        result = engine.run_manual_cycle()
        
        print(f"\n📊 RESULTADO:")
        print(f"✅ Éxito: {result['success']}")
        print(f"⏱️  Duración: {result['duration']:.2f}s")
        print(f"📅 Timestamp: {result['timestamp']}")
        
        # Mostrar estadísticas
        status = engine.get_status()
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   🔄 Ciclos ejecutados: {status['stats']['total_runs']}")
        print(f"   💰 Oportunidades encontradas: {status['stats']['total_opportunities_found']}")
        print(f"   🎯 Matches creados: {status['stats']['total_matches_created']}")
        
        print(f"\n💾 Logs guardados en: arbitrage/arbitrage_engine.log")
        print(f"🔔 Alertas en: arbitrage/latest_alerts.json")

if __name__ == "__main__":
    try:
        start_arbitrage_system()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()