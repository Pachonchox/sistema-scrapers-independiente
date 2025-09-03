# -*- coding: utf-8 -*-
"""
💾 GUARDADO DE OPORTUNIDADES REALES CON SISTEMA INTELIGENTE
==========================================================

Guarda las 17 oportunidades detectadas con:
- Todos los campos necesarios (links, fechas, etc.)
- Evita duplicados
- Solo actualiza si hay cambios reales
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
from datetime import date
from smart_data_saver import SmartArbitrageDataSaver

def parse_opportunities_from_results():
    """
    Parsea las 17 oportunidades del archivo de resultados
    """
    opportunities = []
    
    # Leer archivo de resultados
    with open('arbitrage/resultados_optimizados.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraer cada oportunidad usando regex
    pattern = r'(\d+)\.\s*(.+?)\n\s*Comprar en (\w+): \$([0-9,]+\.0)\n\s*Vender en (\w+): \$([0-9,]+\.0)\n\s*MARGEN: \$([0-9,]+\.0) \(([0-9.]+)% ROI\)\n\s*Similitud ML: ([0-9.]+)'
    
    matches = re.findall(pattern, content, re.MULTILINE)
    
    for i, match in enumerate(matches, 1):
        numero, nombre, retailer_compra, precio_compra_str, retailer_venta, precio_venta_str, margen_str, roi_str, similitud_str = match
        
        # Limpiar y convertir números
        precio_compra = float(precio_compra_str.replace(',', '').replace('.0', ''))
        precio_venta = float(precio_venta_str.replace(',', '').replace('.0', ''))
        margen = float(margen_str.replace(',', '').replace('.0', ''))
        roi = float(roi_str)
        similitud = float(similitud_str)
        
        # Crear oportunidad estructurada
        opp = {
            'matching_id': f'real_opp_{i:03d}',
            'retailer_compra': retailer_compra,
            'retailer_venta': retailer_venta,
            'precio_compra': int(precio_compra),
            'precio_venta': int(precio_venta),
            'margen_bruto': int(margen),
            'diferencia_porcentaje': roi,
            'roi_estimado': roi,
            'opportunity_score': min(1.0, (roi / 100.0) * (similitud / 1.0)),
            'risk_level': 'low' if roi < 50 else 'medium' if roi < 200 else 'high',
            'metadata': {
                'nombre_barato': nombre.strip(),
                'nombre_caro': nombre.strip(),  # Mismo producto
                'similarity_score': similitud,
                'detection_method': 'optimized_ml_system',
                'price_difference_clp': int(margen),
                'source': 'real_detection_2025_09_01'
            }
        }
        
        opportunities.append(opp)
    
    return opportunities

def save_opportunities_to_database():
    """
    Guarda las oportunidades reales usando el sistema inteligente
    """
    print("💾 GUARDANDO OPORTUNIDADES REALES EN BASE DE DATOS")
    print("=" * 55)
    print("• Sistema inteligente de guardado")
    print("• Evita duplicados innecesarios")
    print("• Solo actualiza con cambios reales")
    print("• Incluye todos los campos necesarios")
    print("=" * 55)
    
    # Configuración BD
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    try:
        # Parsear oportunidades
        print("\n1. PARSEANDO OPORTUNIDADES...")
        opportunities = parse_opportunities_from_results()
        print(f"   Oportunidades parseadas: {len(opportunities)}")
        
        # Crear sistema de guardado inteligente
        print("\n2. INICIALIZANDO SISTEMA INTELIGENTE...")
        saver = SmartArbitrageDataSaver(db_params)
        saver.connect()
        
        # Guardar con sistema inteligente
        print("\n3. GUARDANDO CON SISTEMA INTELIGENTE...")
        stats = saver.save_opportunities_smart(opportunities)
        
        print(f"\n4. ESTADÍSTICAS DE GUARDADO:")
        print(f"   🆕 Nuevas oportunidades: {stats['new_opportunities']}")
        print(f"   🔄 Actualizadas: {stats['updated_opportunities']}")
        print(f"   ➡️ Sin cambios: {stats['unchanged_opportunities']}")
        print(f"   ❌ Invalidadas: {stats['invalidated_opportunities']}")
        
        # Verificar datos guardados
        print(f"\n5. VERIFICANDO DATOS GUARDADOS...")
        cursor = saver.conn.cursor()
        
        # Contar oportunidades activas
        cursor.execute("SELECT COUNT(*) as total FROM arbitrage_opportunities WHERE validez_oportunidad = 'active'")
        total_active = cursor.fetchone()['total']
        
        # Top 5 por margen
        cursor.execute("""
            SELECT marca_producto, categoria_producto, retailer_compra, retailer_venta,
                   precio_compra, precio_venta, margen_bruto, diferencia_porcentaje,
                   link_producto_barato, link_producto_caro, fecha_deteccion
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
            ORDER BY margen_bruto DESC 
            LIMIT 5
        """)
        top_opportunities = cursor.fetchall()
        
        print(f"   Total oportunidades activas en BD: {total_active}")
        print(f"\n   🏆 TOP 5 OPORTUNIDADES GUARDADAS:")
        for i, opp in enumerate(top_opportunities, 1):
            print(f"   {i}. {opp['marca_producto']} - {opp['categoria_producto']}")
            print(f"      {opp['retailer_compra']} → {opp['retailer_venta']}: ${opp['margen_bruto']:,} margen ({opp['diferencia_porcentaje']:.1f}%)")
            print(f"      Links: {'✅' if opp['link_producto_barato'] else '❌'} | {'✅' if opp['link_producto_caro'] else '❌'}")
        
        # Generar reporte de guardado
        print(f"\n6. GENERANDO REPORTE...")
        with open('arbitrage/reporte_guardado.txt', 'w', encoding='utf-8') as f:
            f.write("REPORTE DE GUARDADO DE OPORTUNIDADES REALES\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"FECHA: {date.today().strftime('%Y-%m-%d')}\n")
            f.write(f"HORA: {saver.conn.cursor().execute('SELECT NOW()').fetchone()[0] if hasattr(saver.conn.cursor().execute('SELECT NOW()'), 'fetchone') else 'N/A'}\n\n")
            
            f.write(f"ESTADÍSTICAS:\n")
            f.write(f"Nuevas oportunidades creadas: {stats['new_opportunities']}\n")
            f.write(f"Oportunidades actualizadas: {stats['updated_opportunities']}\n")
            f.write(f"Sin cambios detectados: {stats['unchanged_opportunities']}\n")
            f.write(f"Oportunidades invalidadas: {stats['invalidated_opportunities']}\n")
            f.write(f"Total oportunidades activas en BD: {total_active}\n\n")
            
            f.write(f"CAMPOS GUARDADOS POR OPORTUNIDAD:\n")
            f.write("• matching_id (identificador único)\n")
            f.write("• fecha_deteccion (fecha de detección)\n")
            f.write("• retailer_compra y retailer_venta\n")
            f.write("• precio_compra y precio_venta\n")
            f.write("• margen_bruto y diferencia_porcentaje (ROI)\n")
            f.write("• link_producto_barato y link_producto_caro\n")
            f.write("• codigo_sku_barato y codigo_sku_caro\n")
            f.write("• categoria_producto y marca_producto\n")
            f.write("• ratings y reviews de ambos productos\n")
            f.write("• stock_barato y stock_caro\n")
            f.write("• confidence_score y opportunity_score\n")
            f.write("• execution_difficulty y risk_assessment\n")
            f.write("• metadata completa en JSON\n\n")
            
            f.write(f"FUNCIONALIDADES ANTI-DUPLICADOS:\n")
            f.write("• Solo actualiza si hay cambios de precio >1% o >$500\n")
            f.write("• Detecta cambios de stock automáticamente\n")
            f.write("• Tracking histórico de cambios de precios\n")
            f.write("• Invalidación automática de oportunidades obsoletas\n")
            f.write("• Contador de veces detectada (times_detected)\n")
        
        print(f"   ✅ Reporte guardado en: arbitrage/reporte_guardado.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if 'saver' in locals():
            saver.disconnect()

def verify_saved_data():
    """
    Verifica que los datos se guardaron correctamente
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    try:
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        print("\n🔍 VERIFICACIÓN DE DATOS GUARDADOS:")
        print("=" * 40)
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_oportunidades,
                COUNT(DISTINCT marca_producto) as marcas_detectadas,
                COUNT(DISTINCT categoria_producto) as categorias_detectadas,
                SUM(margen_bruto) as margen_total_potencial,
                AVG(diferencia_porcentaje) as roi_promedio,
                MAX(margen_bruto) as mejor_margen
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
        """)
        
        stats = cursor.fetchone()
        
        print(f"Total oportunidades activas: {stats['total_oportunidades']}")
        print(f"Marcas detectadas: {stats['marcas_detectadas']}")
        print(f"Categorías detectadas: {stats['categorias_detectadas']}")
        print(f"Margen total potencial: ${stats['margen_total_potencial']:,}")
        print(f"ROI promedio: {stats['roi_promedio']:.1f}%")
        print(f"Mejor margen: ${stats['mejor_margen']:,}")
        
        # Verificar campos completos
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE link_producto_barato IS NOT NULL) as con_link_barato,
                COUNT(*) FILTER (WHERE link_producto_caro IS NOT NULL) as con_link_caro,
                COUNT(*) FILTER (WHERE categoria_producto IS NOT NULL) as con_categoria,
                COUNT(*) FILTER (WHERE marca_producto IS NOT NULL) as con_marca,
                COUNT(*) as total
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
        """)
        
        completeness = cursor.fetchone()
        
        print(f"\n📊 COMPLETITUD DE DATOS:")
        print(f"Con link producto barato: {completeness['con_link_barato']}/{completeness['total']}")
        print(f"Con link producto caro: {completeness['con_link_caro']}/{completeness['total']}")
        print(f"Con categoría: {completeness['con_categoria']}/{completeness['total']}")
        print(f"Con marca: {completeness['con_marca']}/{completeness['total']}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO GUARDADO INTELIGENTE DE OPORTUNIDADES REALES")
    print()
    
    success = save_opportunities_to_database()
    
    if success:
        print("\n" + "=" * 55)
        print("✅ GUARDADO COMPLETADO EXITOSAMENTE")
        
        # Verificar datos
        verify_saved_data()
        
        print("\n🎉 SISTEMA DE ARBITRAJE COMPLETAMENTE OPERATIVO")
        print("=" * 55)
        print("PRÓXIMOS PASOS:")
        print("1. Consultar oportunidades: SELECT * FROM arbitrage_opportunities;")
        print("2. Ver historial: SELECT * FROM arbitrage_price_history;")
        print("3. Activar alertas automáticas")
        print("4. Ejecutar en modo continuo")
    else:
        print("\n❌ ERROR EN GUARDADO - Ver detalles arriba")