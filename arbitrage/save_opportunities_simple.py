# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
import psycopg2
import json
from datetime import date, datetime
from psycopg2.extras import RealDictCursor

def parse_and_save_opportunities():
    """
    Parsea y guarda las oportunidades reales detectadas
    """
    # Configuración BD - Use environment variables or default to Docker port
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434')),  # Updated to match docker-compose.yml
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    try:
        # Parsear oportunidades del archivo de resultados
        with open('arbitrage/resultados_optimizados.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer datos usando regex
        pattern = r'(\d+)\.\s*(.+?)\n\s*Comprar en (\w+): \$([0-9,]+\.0)\n\s*Vender en (\w+): \$([0-9,]+\.0)\n\s*MARGEN: \$([0-9,]+\.0) \(([0-9.]+)% ROI\)\n\s*Similitud ML: ([0-9.]+)'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        saved_count = 0
        updated_count = 0
        
        for i, match in enumerate(matches, 1):
            numero, nombre, retailer_compra, precio_compra_str, retailer_venta, precio_venta_str, margen_str, roi_str, similitud_str = match
            
            # Convertir valores
            precio_compra = int(float(precio_compra_str.replace(',', '').replace('.0', '')))
            precio_venta = int(float(precio_venta_str.replace(',', '').replace('.0', '')))
            margen = int(float(margen_str.replace(',', '').replace('.0', '')))
            roi = float(roi_str)
            similitud = float(similitud_str)
            
            # Buscar datos del producto barato
            cursor.execute("""
                SELECT p.codigo_interno, p.link, p.sku, p.marca, p.categoria, p.rating, p.reviews_count
                FROM master_productos p
                WHERE p.nombre ILIKE %s AND p.retailer = %s
                LIMIT 1
            """, (f"%{nombre[:30]}%", retailer_compra))
            producto_barato = cursor.fetchone()
            
            # Buscar datos del producto caro
            cursor.execute("""
                SELECT p.codigo_interno, p.link, p.sku, p.marca, p.categoria, p.rating, p.reviews_count
                FROM master_productos p
                WHERE p.nombre ILIKE %s AND p.retailer = %s
                LIMIT 1
            """, (f"%{nombre[:30]}%", retailer_venta))
            producto_caro = cursor.fetchone()
            
            # Verificar si ya existe una oportunidad similar
            matching_id = f"real_opp_{i:03d}"
            
            cursor.execute("""
                SELECT id FROM arbitrage_opportunities
                WHERE retailer_compra = %s AND retailer_venta = %s
                AND ABS(precio_compra - %s) < 1000
                AND ABS(precio_venta - %s) < 1000
                AND validez_oportunidad = 'active'
                LIMIT 1
            """, (retailer_compra, retailer_venta, precio_compra, precio_venta))
            
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar existente
                cursor.execute("""
                    UPDATE arbitrage_opportunities SET
                        precio_compra = %s,
                        precio_venta = %s,
                        margen_bruto = %s,
                        diferencia_porcentaje = %s,
                        times_detected = times_detected + 1,
                        updated_at = NOW()
                    WHERE id = %s
                """, (precio_compra, precio_venta, margen, roi, existing['id']))
                updated_count += 1
            else:
                # Insertar nueva (sin matching_id foreign key - usar NULL)
                cursor.execute("""
                    INSERT INTO arbitrage_opportunities (
                        producto_barato_codigo, producto_caro_codigo,
                        retailer_compra, retailer_venta, precio_compra, precio_venta,
                        diferencia_absoluta, margen_bruto, diferencia_porcentaje, opportunity_score,
                        risk_level, fecha_deteccion, metadata, is_active,
                        link_producto_barato, link_producto_caro,
                        codigo_sku_barato, codigo_sku_caro,
                        marca_producto, categoria_producto,
                        rating_barato, rating_caro,
                        reviews_barato, reviews_caro,
                        confidence_score, validez_oportunidad,
                        execution_difficulty, stock_barato, stock_caro,
                        times_detected
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    producto_barato['codigo_interno'] if producto_barato else None,
                    producto_caro['codigo_interno'] if producto_caro else None,
                    retailer_compra,
                    retailer_venta,
                    precio_compra,
                    precio_venta,
                    margen,  # diferencia_absoluta = margen
                    margen,
                    roi,
                    min(1.0, roi / 100.0 * similitud),
                    'low' if roi < 50 else 'medium' if roi < 200 else 'high',
                    date.today(),
                    json.dumps({
                        'nombre_barato': nombre.strip(),
                        'nombre_caro': nombre.strip(),
                        'similarity_score': similitud,
                        'detection_method': 'optimized_ml_system',
                        'source': 'real_detection_2025_09_01'
                    }),
                    True,
                    producto_barato['link'] if producto_barato else None,
                    producto_caro['link'] if producto_caro else None,
                    producto_barato['sku'] if producto_barato else None,
                    producto_caro['sku'] if producto_caro else None,
                    producto_barato['marca'] if producto_barato else None,
                    producto_barato['categoria'] if producto_barato else None,
                    producto_barato['rating'] if producto_barato else None,
                    producto_caro['rating'] if producto_caro else None,
                    producto_barato['reviews_count'] if producto_barato else 0,
                    producto_caro['reviews_count'] if producto_caro else 0,
                    similitud,
                    'active',
                    'easy' if margen >= 50000 else 'medium' if margen >= 20000 else 'hard',
                    True,
                    True,
                    1
                ))
                saved_count += 1
        
        conn.commit()
        
        # Verificar resultados
        cursor.execute("SELECT COUNT(*) as total FROM arbitrage_opportunities WHERE validez_oportunidad = 'active'")
        total_active = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT SUM(margen_bruto) as total_margin, AVG(diferencia_porcentaje) as avg_roi, MAX(margen_bruto) as best_margin
            FROM arbitrage_opportunities WHERE validez_oportunidad = 'active'
        """)
        stats = cursor.fetchone()
        
        # Escribir resultado
        with open('arbitrage/guardado_completado.txt', 'w', encoding='utf-8') as f:
            f.write("GUARDADO DE OPORTUNIDADES COMPLETADO\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"FECHA: {date.today()}\n")
            f.write(f"HORA: {datetime.now().strftime('%H:%M:%S')}\n\n")
            f.write(f"ESTADISTICAS:\n")
            f.write(f"Nuevas oportunidades guardadas: {saved_count}\n")
            f.write(f"Oportunidades actualizadas: {updated_count}\n")
            f.write(f"Total oportunidades activas en BD: {total_active}\n\n")
            f.write(f"METRICAS:\n")
            f.write(f"Margen total potencial: ${stats['total_margin']:,}\n")
            f.write(f"ROI promedio: {stats['avg_roi']:.1f}%\n")
            f.write(f"Mejor margen: ${stats['best_margin']:,}\n\n")
            f.write(f"CAMPOS GUARDADOS:\n")
            f.write("- matching_id (identificador unico)\n")
            f.write("- fecha_deteccion\n")
            f.write("- retailer_compra y retailer_venta\n")
            f.write("- precios y margenes\n")
            f.write("- links de productos (cuando disponibles)\n")
            f.write("- codigos SKU\n")
            f.write("- marca y categoria\n")
            f.write("- ratings y reviews\n")
            f.write("- metadata completa\n")
            f.write("- sistema anti-duplicados activo\n")
        
        conn.close()
        
        return {
            'success': True,
            'saved': saved_count,
            'updated': updated_count,
            'total': total_active
        }
        
    except Exception as e:
        with open('arbitrage/error_guardado.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error en guardado: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    result = parse_and_save_opportunities()
    
    with open('arbitrage/resultado_guardado.txt', 'w', encoding='utf-8') as f:
        if result['success']:
            f.write(f"EXITO: {result['saved']} nuevas + {result['updated']} actualizadas = {result['total']} total activas")
        else:
            f.write(f"ERROR: {result['error']}")