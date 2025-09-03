# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
# Usar adapter que conecta con sistema V5 avanzado
try:
    from ..utils.ml_adapters import MatchScoringAdapter as MatchScoringModel
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.ml_adapters import MatchScoringAdapter as MatchScoringModel

def test_optimized_parameters():
    # Conexión a BD
    # Use environment variables or default to Docker port
    port = int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml
    host = os.environ.get('PGHOST', 'localhost')
    database = os.environ.get('PGDATABASE', 'price_orchestrator')
    user = os.environ.get('PGUSER', 'orchestrator')
    password = os.environ.get('PGPASSWORD', 'orchestrator_2025')
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    # Crear scorer ML
    scorer = MatchScoringModel(threshold=0.45)  # Parámetro optimizado
    
    try:
        cursor = conn.cursor()
        
        # Obtener productos con precios diferentes entre retailers
        cursor.execute("""
            SELECT p.codigo_interno, p.nombre, p.marca, p.retailer,
                   pr.precio_min_dia, p.rating, p.reviews_count
            FROM master_productos p
            JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE pr.fecha >= CURRENT_DATE - INTERVAL '7 days'
            AND pr.precio_min_dia > 0
            ORDER BY p.marca, p.nombre
        """)
        
        products = cursor.fetchall()
        
        opportunities = []
        matches_found = 0
        
        # Comparar productos con parámetros optimizados
        for i, prod_a in enumerate(products):
            if prod_a[3] in ['falabella', 'ripley']:  # Solo estos retailers
                for prod_b in products[i+1:]:
                    if prod_b[3] != prod_a[3] and prod_b[3] in ['falabella', 'ripley']:
                        
                        # Crear objetos para ML
                        product_a = {
                            'nombre': prod_a[1],
                            'marca': prod_a[2],
                            'precio_min_num': prod_a[4]
                        }
                        
                        product_b = {
                            'nombre': prod_b[1],
                            'marca': prod_b[2],
                            'precio_min_num': prod_b[4]
                        }
                        
                        # Calcular similitud
                        score = scorer.predict_match_proba(product_a, product_b)
                        
                        if score >= 0.45:  # Threshold optimizado
                            matches_found += 1
                            
                            # Calcular arbitraje con parámetros optimizados
                            precio_a = float(prod_a[4] or 0)
                            precio_b = float(prod_b[4] or 0)
                            
                            if precio_a > 0 and precio_b > 0:
                                margen = abs(precio_a - precio_b)
                                
                                # Margen mínimo optimizado: $2K (era $5K-15K)
                                if margen >= 2000:
                                    roi = (margen / min(precio_a, precio_b)) * 100
                                    
                                    # ROI mínimo optimizado: 10% (era 15-25%)
                                    if roi >= 10.0:
                                        
                                        if precio_a < precio_b:
                                            comprar_en = prod_a[3]
                                            vender_en = prod_b[3]
                                            precio_compra = precio_a
                                            precio_venta = precio_b
                                            producto_barato = prod_a[1]
                                        else:
                                            comprar_en = prod_b[3]
                                            vender_en = prod_a[3]
                                            precio_compra = precio_b
                                            precio_venta = precio_a
                                            producto_barato = prod_b[1]
                                        
                                        opportunities.append({
                                            'producto': producto_barato[:50],
                                            'comprar_en': comprar_en,
                                            'vender_en': vender_en,
                                            'precio_compra': precio_compra,
                                            'precio_venta': precio_venta,
                                            'margen': margen,
                                            'roi': roi,
                                            'similarity': score
                                        })
        
        # Escribir resultados a archivo
        with open('arbitrage/resultados_optimizados.txt', 'w', encoding='utf-8') as f:
            f.write("RESULTADOS SISTEMA ARBITRAJE - PARÁMETROS OPTIMIZADOS\n")
            f.write("=" * 60 + "\n\n")
            f.write("CONFIGURACIÓN:\n")
            f.write("• Similitud mínima: 0.45 (optimizada desde 0.7-0.85)\n")
            f.write("• Margen mínimo: $2,000 (optimizado desde $5K-15K)\n")
            f.write("• ROI mínimo: 10% (optimizado desde 15-25%)\n\n")
            
            f.write(f"RESULTADOS:\n")
            f.write(f"Productos analizados: {len(products)}\n")
            f.write(f"Matches encontrados (≥0.45): {matches_found}\n")
            f.write(f"Oportunidades detectadas: {len(opportunities)}\n\n")
            
            if opportunities:
                f.write("🎯 OPORTUNIDADES DETECTADAS:\n")
                f.write("-" * 40 + "\n")
                
                # Ordenar por margen
                opportunities.sort(key=lambda x: x['margen'], reverse=True)
                
                for i, opp in enumerate(opportunities, 1):
                    f.write(f"\n{i}. {opp['producto']}\n")
                    f.write(f"   Comprar en {opp['comprar_en']}: ${opp['precio_compra']:,}\n")
                    f.write(f"   Vender en {opp['vender_en']}: ${opp['precio_venta']:,}\n")
                    f.write(f"   MARGEN: ${opp['margen']:,} ({opp['roi']:.1f}% ROI)\n")
                    f.write(f"   Similitud ML: {opp['similarity']:.3f}\n")
                
                f.write(f"\n📊 ESTADÍSTICAS:\n")
                total_margin = sum(opp['margen'] for opp in opportunities)
                avg_roi = sum(opp['roi'] for opp in opportunities) / len(opportunities)
                f.write(f"Margen total potencial: ${total_margin:,}\n")
                f.write(f"ROI promedio: {avg_roi:.1f}%\n")
                f.write(f"Mejor oportunidad: ${opportunities[0]['margen']:,}\n")
                
            else:
                f.write("No se encontraron oportunidades con los parámetros optimizados.\n")
                f.write("Los productos disponibles son muy diversos entre retailers.\n")
        
        return len(opportunities)
        
    except Exception as e:
        with open('arbitrage/error_optimizado.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        return -1
        
    finally:
        conn.close()

if __name__ == "__main__":
    opportunities = test_optimized_parameters()
    
    with open('arbitrage/status_optimizado.txt', 'w', encoding='utf-8') as f:
        if opportunities > 0:
            f.write(f"ÉXITO: {opportunities} oportunidades detectadas con parámetros optimizados")
        elif opportunities == 0:
            f.write("SISTEMA OK: Sin oportunidades con parámetros optimizados")
        else:
            f.write("ERROR: Ver error_optimizado.txt")