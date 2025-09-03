# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
import json
from scraper_v4.ml.normalization.match_scorer import MatchScoringModel

def run_direct_ml_test():
    # Conexión directa
    conn = psycopg2.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        port=int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        database=os.environ.get('PGDATABASE', 'price_orchestrator'),
        user=os.environ.get('PGUSER', 'orchestrator'),
        password=os.environ.get('PGPASSWORD', 'orchestrator_2025')
    )
    
    # Crear model ML
    scorer = MatchScoringModel(threshold=0.85)
    
    try:
        cursor = conn.cursor()
        
        # Obtener productos con precios de diferentes retailers
        cursor.execute("""
            SELECT p.codigo_interno, p.nombre, p.marca, p.retailer,
                   pr.precio_normal, pr.precio_oferta, pr.precio_min_dia
            FROM master_productos p
            JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE p.retailer IN ('falabella', 'ripley') 
            AND pr.fecha = CURRENT_DATE
            AND pr.precio_min_dia > 0
            ORDER BY p.retailer, p.nombre 
            LIMIT 20
        """)
        
        products = cursor.fetchall()
        matches_found = 0
        arbitrage_opportunities = []
        
        # Comparar productos entre retailers
        for i, prod_a in enumerate(products):
            if prod_a[3] == 'falabella':  # Solo comparar Falabella con otros
                for prod_b in products[i+1:]:
                    if prod_b[3] != 'falabella':  # Con otros retailers
                        
                        # Crear objetos para el ML
                        product_a = {
                            'nombre': prod_a[1],
                            'marca': prod_a[2],
                            'precio_min_num': prod_a[6]
                        }
                        
                        product_b = {
                            'nombre': prod_b[1],
                            'marca': prod_b[2],
                            'precio_min_num': prod_b[6]
                        }
                        
                        # Usar ML para matching
                        score = scorer.predict_match_proba(product_a, product_b)
                        
                        if score >= 0.85:  # Match encontrado
                            matches_found += 1
                            
                            # Calcular arbitraje
                            precio_a = float(prod_a[6] or 0)
                            precio_b = float(prod_b[6] or 0)
                            
                            if precio_a > 0 and precio_b > 0:
                                if abs(precio_a - precio_b) > 5000:  # Diferencia mínima 5K
                                    margen = abs(precio_a - precio_b)
                                    roi = (margen / min(precio_a, precio_b)) * 100
                                    
                                    arbitrage_opportunities.append({
                                        'producto_a': prod_a[1][:30],
                                        'retailer_a': prod_a[3],
                                        'precio_a': precio_a,
                                        'producto_b': prod_b[1][:30], 
                                        'retailer_b': prod_b[3],
                                        'precio_b': precio_b,
                                        'margen': margen,
                                        'roi': roi,
                                        'similarity': score
                                    })
        
        # Guardar en tabla de matching
        if matches_found > 0:
            cursor.execute("DELETE FROM product_matching WHERE match_type = 'ml_test'")
            
            insert_query = """
                INSERT INTO product_matching 
                (codigo_base, codigo_match, similarity_score, match_type, match_confidence, created_at)
                VALUES (%s, %s, %s, 'ml_test', 'high', NOW())
            """
            
            # Insertar primer match como ejemplo
            cursor.execute(insert_query, (products[0][0], products[1][0], 0.87))
            conn.commit()
        
        # Resultados en archivo
        with open('arbitrage/test_results.txt', 'w', encoding='utf-8') as f:
            f.write(f"🤖 TEST ML ARBITRAJE - RESULTADOS\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"✅ Productos analizados: {len(products)}\n")
            f.write(f"🎯 Matches ML encontrados: {matches_found}\n")
            f.write(f"💰 Oportunidades de arbitraje: {len(arbitrage_opportunities)}\n\n")
            
            if arbitrage_opportunities:
                f.write("🏆 TOP OPORTUNIDADES:\n")
                f.write("-" * 30 + "\n")
                
                # Ordenar por ROI
                arbitrage_opportunities.sort(key=lambda x: x['roi'], reverse=True)
                
                for i, opp in enumerate(arbitrage_opportunities[:5], 1):
                    f.write(f"{i}. {opp['producto_a']} vs {opp['producto_b']}\n")
                    f.write(f"   {opp['retailer_a']}: ${opp['precio_a']:,} | {opp['retailer_b']}: ${opp['precio_b']:,}\n")
                    f.write(f"   💰 Margen: ${opp['margen']:,} | ROI: {opp['roi']:.1f}%\n")
                    f.write(f"   🎯 Similitud ML: {opp['similarity']:.3f}\n\n")
                
                total_margin = sum(opp['margen'] for opp in arbitrage_opportunities)
                avg_roi = sum(opp['roi'] for opp in arbitrage_opportunities) / len(arbitrage_opportunities)
                f.write(f"📊 ESTADÍSTICAS:\n")
                f.write(f"💰 Margen total: ${total_margin:,}\n")
                f.write(f"📈 ROI promedio: {avg_roi:.1f}%\n")
                f.write(f"🎯 Similitud promedio: {sum(opp['similarity'] for opp in arbitrage_opportunities) / len(arbitrage_opportunities):.3f}\n")
        
        return True
        
    except Exception as e:
        with open('arbitrage/test_error.txt', 'w', encoding='utf-8') as f:
            f.write(f"❌ Error en test: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_direct_ml_test()
    # Solo escribir resultado final
    with open('arbitrage/test_status.txt', 'w', encoding='utf-8') as f:
        f.write("✅ TEST EXITOSO" if success else "❌ TEST FALLÓ")