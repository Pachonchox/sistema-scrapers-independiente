# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml_integration_sync import ArbitrageMLIntegration
import logging

# Configurar logging para evitar conflictos
logging.basicConfig(level=logging.WARNING)

def test_simple():
    # Configuración de conexión
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    ml_integration = ArbitrageMLIntegration(db_params)
    
    try:
        # Test conexión
        ml_integration.connect()
        print("✅ Conexión exitosa")
        
        # Test matches (solo 10 para prueba rápida)
        matches = ml_integration.find_product_matches(limit=10)
        print(f"✅ Encontrados {len(matches)} matches")
        
        if matches:
            # Mostrar primer match
            first_match = matches[0]
            print(f"📦 Match ejemplo: {first_match['similarity_score']:.3f}")
            
            # Guardar matches
            saved = ml_integration.save_matches_to_db(matches)
            print(f"✅ Guardados {saved} matches")
            
            # Test oportunidades
            opportunities = ml_integration.detect_arbitrage_opportunities()
            print(f"✅ Detectadas {len(opportunities)} oportunidades")
            
            if opportunities:
                best_opp = opportunities[0]
                print(f"🏆 Mejor oportunidad: ${best_opp['margen_bruto']:,} margen ({best_opp['diferencia_porcentaje']:.1f}%)")
            
            return True
        else:
            print("⚠️ Sin matches encontrados")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        ml_integration.disconnect()

if __name__ == "__main__":
    success = test_simple()
    print(f"\n{'✅ TEST EXITOSO' if success else '❌ TEST FALLÓ'}")