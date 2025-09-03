#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🗄️ VERIFICADOR DE DATOS EN BASE DE DATOS
========================================
Script para verificar cuántos datos se cargaron en PostgreSQL
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Añadir paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# Forzar soporte de emojis
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

def check_database_data():
    """🔍 Verificar datos en base de datos PostgreSQL"""
    
    try:
        import psycopg2
        
        # Parámetros de conexión
        conn_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'orchestrator'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', 'postgres')
        }
        
        print("\n" + "="*80)
        print("🗄️ VERIFICANDO DATOS EN POSTGRESQL")
        print("="*80)
        print(f"🐘 Conectando a: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # 1. VERIFICAR TABLAS EXISTENTES
        print("\n📋 TABLAS EXISTENTES:")
        
        cur.execute("""
            SELECT table_name, 
                   (xpath('/row/c/text()', query_to_xml('SELECT COUNT(*) as c FROM ' || table_name, false, true, '')))[1]::text::int as row_count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        total_records = 0
        
        for table_name, row_count in tables:
            print(f"  📊 {table_name}: {row_count:,} registros")
            total_records += row_count if row_count else 0
        
        print(f"\n📈 TOTAL REGISTROS EN BD: {total_records:,}")
        
        # 2. DATOS POR RETAILER (si existe master_productos)
        try:
            print("\n🏪 PRODUCTOS POR RETAILER:")
            
            cur.execute("""
                SELECT retailer, 
                       COUNT(*) as productos,
                       MIN(created_at) as primera_carga,
                       MAX(created_at) as ultima_carga
                FROM master_productos
                GROUP BY retailer
                ORDER BY COUNT(*) DESC;
            """)
            
            retailer_data = cur.fetchall()
            
            for retailer, count, first_load, last_load in retailer_data:
                print(f"  🏪 {retailer.upper()}: {count:,} productos")
                print(f"    Primera carga: {first_load.strftime('%d/%m/%Y %H:%M')}")
                print(f"    Última carga: {last_load.strftime('%d/%m/%Y %H:%M')}")
                print()
                
        except Exception as e:
            print(f"  ⚠️ No se pudo consultar master_productos: {e}")
        
        # 3. PRECIOS HISTÓRICOS (si existe master_precios)
        try:
            print("\n💰 SNAPSHOTS DE PRECIOS:")
            
            cur.execute("""
                SELECT DATE(fecha) as fecha_snapshot,
                       COUNT(*) as snapshots,
                       MIN(precio_oferta) as precio_min,
                       MAX(precio_oferta) as precio_max,
                       AVG(precio_oferta) as precio_promedio
                FROM master_precios
                WHERE fecha >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(fecha)
                ORDER BY fecha_snapshot DESC
                LIMIT 10;
            """)
            
            price_data = cur.fetchall()
            
            for fecha, snapshots, min_price, max_price, avg_price in price_data:
                print(f"  📅 {fecha.strftime('%d/%m/%Y')}: {snapshots:,} snapshots")
                if min_price and max_price and avg_price:
                    print(f"    💵 Rango precios: ${min_price:,.0f} - ${max_price:,.0f} (promedio: ${avg_price:,.0f})")
                print()
                
        except Exception as e:
            print(f"  ⚠️ No se pudo consultar master_precios: {e}")
        
        # 4. DATOS DE HOY
        print("\n📅 DATOS DE HOY:")
        
        try:
            cur.execute("""
                SELECT 'Productos nuevos' as tipo, COUNT(*) as cantidad
                FROM master_productos
                WHERE DATE(created_at) = CURRENT_DATE
                UNION ALL
                SELECT 'Snapshots de precios' as tipo, COUNT(*) as cantidad
                FROM master_precios
                WHERE fecha = CURRENT_DATE;
            """)
            
            today_data = cur.fetchall()
            
            for tipo, cantidad in today_data:
                print(f"  📊 {tipo}: {cantidad:,}")
                
        except Exception as e:
            print(f"  ⚠️ Error consultando datos de hoy: {e}")
        
        # 5. ARBITRAJE (si existe)
        try:
            print("\n💎 OPORTUNIDADES DE ARBITRAJE:")
            
            cur.execute("""
                SELECT COUNT(*) as total_oportunidades,
                       COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as hoy,
                       MIN(margen_bruto) as margen_min,
                       MAX(margen_bruto) as margen_max,
                       AVG(margen_bruto) as margen_promedio
                FROM arbitrage_opportunities;
            """)
            
            arbitrage = cur.fetchone()
            
            if arbitrage and arbitrage[0] > 0:
                total, hoy, min_margen, max_margen, avg_margen = arbitrage
                print(f"  🎯 Total oportunidades: {total:,}")
                print(f"  📅 Detectadas hoy: {hoy:,}")
                if min_margen and max_margen and avg_margen:
                    print(f"  💰 Margen: ${min_margen:,.0f} - ${max_margen:,.0f} (promedio: ${avg_margen:,.0f})")
            else:
                print(f"  ⚠️ Sin oportunidades de arbitraje registradas")
                
        except Exception as e:
            print(f"  ⚠️ No se pudo consultar arbitraje: {e}")
        
        # 6. ESTADÍSTICAS FINALES
        print("\n📊 RESUMEN FINAL:")
        print(f"  🗄️ Tablas activas: {len(tables)}")
        print(f"  📦 Total registros: {total_records:,}")
        print(f"  🕐 Verificación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("="*80)
        
        return total_records
        
    except Exception as e:
        print(f"\n❌ Error conectando a PostgreSQL: {e}")
        print("   Verifica que PostgreSQL esté ejecutándose y accesible")
        return 0

if __name__ == "__main__":
    print("🔍 Verificando datos en base de datos...")
    total = check_database_data()
    
    if total > 0:
        print(f"\n🎉 Base de datos activa con {total:,} registros totales")
    else:
        print(f"\n⚠️ No se pudieron verificar los datos de la base")