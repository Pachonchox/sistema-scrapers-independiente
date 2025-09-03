# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
import json
from scraper_v4.ml.normalization.match_scorer import MatchScoringModel

def run_improved_ml_test():
    # Conexión directa
    conn = psycopg2.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        port=int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        database=os.environ.get('PGDATABASE', 'price_orchestrator'),
        user=os.environ.get('PGUSER', 'orchestrator'),
        password=os.environ.get('PGPASSWORD', 'orchestrator_2025')
    )
    
    # Crear model ML con threshold más bajo para testing
    scorer = MatchScoringModel(threshold=0.7)
    
    try:
        cursor = conn.cursor()
        
        # Obtener productos con precios más recientes (no solo de hoy)
        cursor.execute("""
            SELECT DISTINCT ON (p.codigo_interno) 
                   p.codigo_interno, p.nombre, p.marca, p.retailer,
                   pr.precio_normal, pr.precio_oferta, pr.precio_min_dia
            FROM master_productos p
            JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE p.retailer IN ('falabella', 'ripley', 'paris') 
            AND pr.precio_min_dia > 10000  -- Precios razonables
            ORDER BY p.codigo_interno, pr.fecha DESC
            LIMIT 30
        """)
        
        products = cursor.fetchall()
        matches_found = 0
        all_comparisons = []
        arbitrage_opportunities = []
        
        # Comparar TODOS los productos con TODOS
        for i, prod_a in enumerate(products):
            for j, prod_b in enumerate(products):
                if i != j and prod_a[3] != prod_b[3]:  # Diferentes retailers
                    
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
                    
                    # Guardar TODAS las comparaciones para análisis
                    comparison = {
                        'producto_a': prod_a[1][:40],
                        'retailer_a': prod_a[3],
                        'precio_a': float(prod_a[6] or 0),
                        'producto_b': prod_b[1][:40],
                        'retailer_b': prod_b[3], 
                        'precio_b': float(prod_b[6] or 0),
                        'similarity': score
                    }
                    all_comparisons.append(comparison)
                    
                    if score >= 0.7:  # Match encontrado con threshold más bajo
                        matches_found += 1
                        
                        # Calcular arbitraje
                        precio_a = float(prod_a[6] or 0)
                        precio_b = float(prod_b[6] or 0)
                        
                        if precio_a > 0 and precio_b > 0:
                            margen = abs(precio_a - precio_b)
                            if margen > 5000:  # Diferencia mínima 5K
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
        
        # Guardar comparaciones exitosas en BD
        if matches_found > 0:
            cursor.execute("DELETE FROM product_matching WHERE match_type = 'ml_test_improved'")
            
            insert_query = """
                INSERT INTO product_matching 
                (codigo_base, codigo_match, similarity_score, match_type, match_confidence, created_at)
                VALUES (%s, %s, %s, 'ml_test_improved', %s, NOW())
            """
            
            # Insertar todos los matches encontrados
            match_count = 0
            for comp in all_comparisons:
                if comp['similarity'] >= 0.7:
                    confidence = 'high' if comp['similarity'] >= 0.85 else 'medium'
                    # Encontrar códigos internos correspondientes
                    for prod in products:
                        if prod[1][:40] == comp['producto_a'] and prod[3] == comp['retailer_a']:
                            codigo_a = prod[0]
                        if prod[1][:40] == comp['producto_b'] and prod[3] == comp['retailer_b']:
                            codigo_b = prod[0]
                    
                    cursor.execute(insert_query, (codigo_a, codigo_b, comp['similarity'], confidence))
                    match_count += 1
                    if match_count >= 10:  # Limitar para testing
                        break
            
            conn.commit()
        
        # Escribir resultados detallados
        with open('arbitrage/test_results_improved.txt', 'w', encoding='utf-8') as f:
            f.write(f"🤖 TEST ML ARBITRAJE MEJORADO - RESULTADOS\n")
            f.write(f"=" * 55 + "\n\n")
            f.write(f"✅ Productos analizados: {len(products)}\n")
            f.write(f"🔍 Comparaciones realizadas: {len(all_comparisons)}\n")
            f.write(f"🎯 Matches ML encontrados (≥0.7): {matches_found}\n")
            f.write(f"💰 Oportunidades de arbitraje: {len(arbitrage_opportunities)}\n\n")
            
            # Top comparaciones por similitud
            f.write("🔍 TOP 10 COMPARACIONES POR SIMILITUD:\n")
            f.write("-" * 50 + "\n")
            all_comparisons.sort(key=lambda x: x['similarity'], reverse=True)
            for i, comp in enumerate(all_comparisons[:10], 1):
                f.write(f"{i}. {comp['producto_a']} ({comp['retailer_a']})\n")
                f.write(f"    vs {comp['producto_b']} ({comp['retailer_b']})\n")
                f.write(f"    🎯 Similitud: {comp['similarity']:.3f} | Precios: ${comp['precio_a']:,} vs ${comp['precio_b']:,}\n\n")
            
            if arbitrage_opportunities:
                f.write("💰 OPORTUNIDADES DE ARBITRAJE:\n")
                f.write("-" * 35 + "\n")
                
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
            
            # Estadísticas de similitud
            similarities = [comp['similarity'] for comp in all_comparisons]
            if similarities:
                f.write(f"\n📈 ESTADÍSTICAS DE SIMILITUD:\n")
                f.write(f"🔝 Máxima similitud: {max(similarities):.3f}\n")
                f.write(f"📊 Similitud promedio: {sum(similarities)/len(similarities):.3f}\n")
                f.write(f"💥 Matches con similitud ≥0.85: {sum(1 for s in similarities if s >= 0.85)}\n")
                f.write(f"⚡ Matches con similitud ≥0.7: {sum(1 for s in similarities if s >= 0.7)}\n")
        
        return True
        
    except Exception as e:
        with open('arbitrage/test_error_improved.txt', 'w', encoding='utf-8') as f:
            f.write(f"❌ Error en test mejorado: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_improved_ml_test()
    with open('arbitrage/test_status_improved.txt', 'w', encoding='utf-8') as f:
        f.write("✅ TEST MEJORADO EXITOSO" if success else "❌ TEST MEJORADO FALLÓ")