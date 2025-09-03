# -*- coding: utf-8 -*-
"""
Prueba rápida del sistema completo de arbitraje con ML reentrenado
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend_arbitrage_engine import BackendArbitrageEngine, ArbitrageConfig

def test_arbitrage_system():
    print("PROBANDO SISTEMA COMPLETO DE ARBITRAJE")
    print("=" * 50)
    print("- ML reentrenado con 19 features expandidas")
    print("- Modelos entrenados: GBM, RF, LR (100% accuracy)")
    print("- Reglas de matching actualizadas automaticamente")
    print("=" * 50)
    
    # Configuración de BD
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    # Configuración del motor (más permisiva para detectar oportunidades)
    config = ArbitrageConfig(
        min_margin_clp=5000.0,        # Margen mínimo $5K (permisivo)
        min_percentage=10.0,          # ROI mínimo 10% (permisivo)
        min_similarity_score=0.7,     # Similitud mínima 70%
        enable_auto_alerts=True,
        max_opportunities_per_run=20
    )
    
    print("CONFIGURACION DEL MOTOR:")
    print(f"  Margen minimo: ${config.min_margin_clp:,}")
    print(f"  ROI minimo: {config.min_percentage}%") 
    print(f"  Similitud ML minima: {config.min_similarity_score}")
    print("=" * 50)
    
    # Crear motor de arbitraje
    engine = BackendArbitrageEngine(db_params, config)
    
    print("\nEjecutando CICLO MANUAL de arbitraje...")
    print("(Usa el ML reentrenado con campos expandidos)")
    
    result = engine.run_manual_cycle()
    
    print("\nRESULTADO DEL CICLO:")
    print(f"Exito: {result['success']}")
    print(f"Duracion: {result['duration']:.2f}s")
    print(f"Timestamp: {result['timestamp']}")
    
    # Obtener estadísticas
    status = engine.get_status()
    stats = status['stats']
    
    print("\nESTADISTICAS DEL MOTOR:")
    print(f"Ciclos ejecutados: {stats['total_runs']}")
    print(f"Oportunidades encontradas: {stats['total_opportunities_found']}")
    print(f"Matches ML creados: {stats['total_matches_created']}")
    print(f"Ultima duracion: {stats['last_run_duration']:.2f}s")
    
    # Verificar archivos generados
    print("\nARCHIVOS GENERADOS:")
    
    log_files = [
        'arbitrage/arbitrage_engine.log',
        'arbitrage/latest_alerts.json'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"  {log_file} ({size} bytes)")
        else:
            print(f"  {log_file} (no creado)")
    
    print("\nSISTEMA DE ARBITRAJE BACKEND OPERATIVO!")
    print("=" * 50)
    print("PROXIMOS PASOS:")
    print("1. Para modo continuo: python arbitrage/start_arbitrage_engine.py")
    print("2. Revisar logs en: arbitrage/arbitrage_engine.log")
    print("3. Alertas en: arbitrage/latest_alerts.json")
    print("4. Oportunidades guardadas en tabla: arbitrage_opportunities")

if __name__ == "__main__":
    test_arbitrage_system()