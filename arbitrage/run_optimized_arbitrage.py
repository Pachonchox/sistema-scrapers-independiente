# -*- coding: utf-8 -*-
"""
🎯 SISTEMA DE ARBITRAJE CON PARÁMETROS OPTIMIZADOS
=================================================

Ejecuta el sistema con parámetros ajustados para detectar
las oportunidades reales basadas en el análisis de datos.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml_integration_sync import ArbitrageMLIntegration

def run_optimized_arbitrage():
    print("SISTEMA DE ARBITRAJE - PARÁMETROS OPTIMIZADOS")
    print("=" * 55)
    print("AJUSTES BASADOS EN ANÁLISIS DE DATOS:")
    print("• Similitud mínima: 0.45 (era 0.7-0.85)")
    print("• Margen mínimo: $2,000 (era $5K-15K)")
    print("• ROI mínimo: 10% (era 15-25%)")
    print("• Enfoque en diferencias reales detectadas")
    print("=" * 55)
    
    # Configuración de BD
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    # Crear integración con parámetros optimizados
    ml_integration = ArbitrageMLIntegration(db_params)
    
    # Sobrescribir configuración con parámetros más permisivos
    ml_integration.config = {
        'min_margin_clp': 2000.0,        # Reducido de 5K-15K
        'min_percentage': 10.0,          # Reducido de 15-25%
        'min_similarity_score': 0.45,    # Reducido de 0.7-0.85
        'max_price_ratio': 5.0,          # Mantenido
        'update_frequency_minutes': 30.0,
        'enable_auto_alerts': True
    }
    
    print(f"\nCONFIGURACIÓN OPTIMIZADA:")
    print(f"Margen mínimo: ${ml_integration.config['min_margin_clp']:,}")
    print(f"ROI mínimo: {ml_integration.config['min_percentage']}%")
    print(f"Similitud mínima: {ml_integration.config['min_similarity_score']}")
    print("=" * 55)
    
    try:
        print("\n1. CONECTANDO...")
        ml_integration.connect()
        
        print("\n2. BUSCANDO MATCHES CON PARÁMETROS OPTIMIZADOS...")
        matches = ml_integration.find_product_matches(
            limit=200, 
            min_similarity=ml_integration.config['min_similarity_score']
        )
        print(f"   Matches encontrados: {len(matches)}")
        
        if matches:
            print("\n3. GUARDANDO MATCHES EN BD...")
            saved = ml_integration.save_matches_to_db(matches)
            print(f"   Matches guardados: {saved}")
            
            print("\n4. DETECTANDO OPORTUNIDADES DE ARBITRAJE...")
            opportunities = ml_integration.detect_arbitrage_opportunities()
            print(f"   Oportunidades detectadas: {len(opportunities)}")
            
            if opportunities:
                print(f"\n🎯 OPORTUNIDADES REALES DETECTADAS:")
                print("=" * 55)
                
                # Ordenar por margen absoluto
                opportunities_sorted = sorted(opportunities, key=lambda x: x['margen_bruto'], reverse=True)
                
                for i, opp in enumerate(opportunities_sorted[:10], 1):
                    metadata = opp['metadata']
                    print(f"\n{i}. OPORTUNIDAD #{opp['matching_id']}")
                    print(f"   📦 Producto: {metadata.get('nombre_barato', 'N/A')[:50]}...")
                    print(f"   🛒 Comprar en {opp['retailer_compra']}: ${opp['precio_compra']:,}")
                    print(f"   💰 Vender en {opp['retailer_venta']}: ${opp['precio_venta']:,}")
                    print(f"   📈 MARGEN: ${opp['margen_bruto']:,} ({opp['diferencia_porcentaje']:.1f}%)")
                    print(f"   🎯 ROI: {opp['roi_estimado']:.1f}% | Score: {opp['opportunity_score']:.3f}")
                    print(f"   ⚖️ Riesgo: {opp['risk_level']} | Similitud: {metadata['similarity_score']:.3f}")
                
                print(f"\n📊 RESUMEN ESTADÍSTICO:")
                print("=" * 30)
                total_margin = sum(opp['margen_bruto'] for opp in opportunities)
                avg_margin = total_margin / len(opportunities) if opportunities else 0
                avg_roi = sum(opp['roi_estimado'] for opp in opportunities) / len(opportunities)
                avg_similarity = sum(opp['metadata']['similarity_score'] for opp in opportunities) / len(opportunities)
                
                print(f"💰 Margen total potencial: ${total_margin:,}")
                print(f"💵 Margen promedio: ${avg_margin:,}")
                print(f"📈 ROI promedio: {avg_roi:.1f}%")
                print(f"🎯 Similitud promedio: {avg_similarity:.3f}")
                print(f"🏆 Mejor oportunidad: ${opportunities_sorted[0]['margen_bruto']:,} margen")
                
                # Guardar oportunidades en BD
                print(f"\n5. GUARDANDO OPORTUNIDADES EN POSTGRESQL...")
                saved_opps = save_opportunities_to_db(ml_integration, opportunities)
                print(f"   Oportunidades guardadas: {saved_opps}")
                
                print(f"\n✅ PROCESO COMPLETADO EXITOSAMENTE")
                print("=" * 55)
                print("Las oportunidades han sido detectadas y guardadas.")
                print("Sistema listo para alertas automáticas.")
                
            else:
                print("   ℹ️ No se encontraron oportunidades con parámetros optimizados")
                
                # Mostrar matches para análisis
                print(f"\n📋 ANÁLISIS DE MATCHES ENCONTRADOS:")
                for i, match in enumerate(matches[:5], 1):
                    print(f"{i}. Similitud {match['similarity_score']:.3f}: {match['nombre_a'][:30]}... vs {match['nombre_b'][:30]}...")
        else:
            print("   ⚠️ No se encontraron matches suficientes")
            print("   Esto indica que los productos son muy diversos entre retailers")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        ml_integration.disconnect()
    
    return True

def save_opportunities_to_db(ml_integration, opportunities):
    """Guarda las oportunidades directamente en la BD"""
    try:
        import psycopg2
        from datetime import date
        import json
        
        conn = psycopg2.connect(**ml_integration.db_params)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for opp in opportunities:
            try:
                # Buscar códigos internos basados en metadata
                cursor.execute("""
                    SELECT codigo_interno FROM master_productos 
                    WHERE nombre ILIKE %s 
                    AND retailer = %s 
                    LIMIT 1
                """, (f"%{opp['metadata']['nombre_barato'][:20]}%", opp['retailer_compra']))
                
                result_barato = cursor.fetchone()
                if not result_barato:
                    continue
                
                cursor.execute("""
                    SELECT codigo_interno FROM master_productos 
                    WHERE nombre ILIKE %s 
                    AND retailer = %s 
                    LIMIT 1  
                """, (f"%{opp['metadata']['nombre_caro'][:20]}%", opp['retailer_venta']))
                
                result_caro = cursor.fetchone()
                if not result_caro:
                    continue
                
                # Insertar oportunidad
                cursor.execute("""
                    INSERT INTO arbitrage_opportunities 
                    (matching_id, producto_barato_codigo, producto_caro_codigo,
                     retailer_compra, retailer_venta, precio_compra, precio_venta,
                     margen_bruto, diferencia_porcentaje, opportunity_score, risk_level,
                     fecha_deteccion, metadata, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                    ON CONFLICT (matching_id, fecha_deteccion) DO UPDATE SET
                    precio_compra = EXCLUDED.precio_compra,
                    precio_venta = EXCLUDED.precio_venta,
                    margen_bruto = EXCLUDED.margen_bruto,
                    opportunity_score = EXCLUDED.opportunity_score,
                    updated_at = NOW()
                """, (
                    opp['matching_id'],
                    result_barato[0],
                    result_caro[0],
                    opp['retailer_compra'],
                    opp['retailer_venta'],
                    int(opp['precio_compra']),
                    int(opp['precio_venta']),
                    int(opp['margen_bruto']),
                    float(opp['diferencia_porcentaje']),
                    float(opp['opportunity_score']),
                    opp['risk_level'],
                    date.today(),
                    json.dumps(opp['metadata'])
                ))
                
                saved_count += 1
                
            except Exception as e:
                print(f"   Warning: Error guardando oportunidad {opp.get('matching_id', 'N/A')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return saved_count
        
    except Exception as e:
        print(f"Error guardando oportunidades: {e}")
        return 0

if __name__ == "__main__":
    success = run_optimized_arbitrage()
    print(f"\nRESULTADO FINAL: {'ÉXITO' if success else 'ERROR'}")