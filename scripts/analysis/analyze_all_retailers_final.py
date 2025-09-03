#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis Comparativo Final de Todos los Retailers
==================================================

Compara los datos de Excel vs PostgreSQL para asegurar
la integridad de la carga.
"""

import pandas as pd
import psycopg2
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

def extract_date_from_filename(filename):
    """Extrae fecha del nombre del archivo"""
    parts = filename.replace('.xlsx', '').split('_')
    if len(parts) >= 5:
        year, month, day, time = parts[1], parts[2], parts[3], parts[4]
        return f"{year}-{month}-{day}"
    return "unknown"

def analyze_excel_files():
    """Analizar archivos Excel por retailer"""
    excel_dir = 'data/excel'
    
    if not os.path.exists(excel_dir):
        print(f"[ERROR] No existe el directorio {excel_dir}")
        return {}
    
    retailers = defaultdict(lambda: {
        'files': 0,
        'total_rows': 0,
        'unique_names': set(),
        'unique_skus': set(),
        'dates': set(),
        'samples': []
    })
    
    print("="*80)
    print("ANALIZANDO ARCHIVOS EXCEL")
    print("="*80)
    
    for file in os.listdir(excel_dir):
        if file.endswith('.xlsx') and not file.startswith(('test_', 'ml_test')):
            retailer = file.split('_')[0].lower()
            fecha = extract_date_from_filename(file)
            filepath = os.path.join(excel_dir, file)
            
            try:
                df = pd.read_excel(filepath)
                
                retailers[retailer]['files'] += 1
                retailers[retailer]['total_rows'] += len(df)
                retailers[retailer]['dates'].add(fecha)
                
                # Agregar nombres únicos
                if 'nombre' in df.columns:
                    for nombre in df['nombre'].dropna().unique():
                        retailers[retailer]['unique_names'].add(str(nombre))
                
                # Agregar SKUs únicos
                if 'sku' in df.columns:
                    for sku in df['sku'].dropna().unique():
                        if str(sku) != 'nan':
                            retailers[retailer]['unique_skus'].add(str(sku))
                
                # Guardar algunos ejemplos
                if len(retailers[retailer]['samples']) < 3 and len(df) > 0:
                    sample = df.iloc[0]['nombre'] if 'nombre' in df.columns else 'N/A'
                    retailers[retailer]['samples'].append(sample[:60])
                    
            except Exception as e:
                if "Bad magic number" not in str(e):
                    print(f"  Error leyendo {file}: {e}")
    
    return retailers

def analyze_database():
    """Analizar datos en PostgreSQL"""
    conn = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5434'),
        database=os.getenv('PGDATABASE', 'price_orchestrator'),
        user=os.getenv('PGUSER', 'orchestrator'),
        password=os.getenv('PGPASSWORD', 'orchestrator_2025')
    )
    cursor = conn.cursor()
    
    # Productos por retailer con análisis detallado
    cursor.execute("""
        SELECT 
            retailer,
            COUNT(*) as total_products,
            COUNT(DISTINCT nombre) as unique_names,
            COUNT(DISTINCT sku) as unique_skus,
            COUNT(CASE WHEN sku IS NOT NULL AND sku != '' THEN 1 END) as with_sku
        FROM master_productos
        GROUP BY retailer
        ORDER BY total_products DESC
    """)
    
    db_products = {}
    for row in cursor.fetchall():
        db_products[row[0]] = {
            'total': row[1],
            'unique_names': row[2],
            'unique_skus': row[3],
            'with_sku': row[4]
        }
    
    # Precios por retailer
    cursor.execute("""
        SELECT 
            retailer,
            COUNT(*) as total_prices,
            COUNT(DISTINCT fecha) as unique_dates,
            MIN(fecha) as min_date,
            MAX(fecha) as max_date
        FROM master_precios
        GROUP BY retailer
        ORDER BY total_prices DESC
    """)
    
    db_prices = {}
    for row in cursor.fetchall():
        db_prices[row[0]] = {
            'total': row[1],
            'unique_dates': row[2],
            'min_date': row[3],
            'max_date': row[4]
        }
    
    # Verificar duplicados por retailer
    cursor.execute("""
        WITH duplicados AS (
            SELECT retailer, nombre, COUNT(*) as cnt
            FROM master_productos
            GROUP BY retailer, nombre
            HAVING COUNT(*) > 1
        )
        SELECT retailer, COUNT(*) as productos_duplicados, SUM(cnt) as total_duplicados
        FROM duplicados
        GROUP BY retailer
    """)
    
    db_duplicates = {}
    for row in cursor.fetchall():
        db_duplicates[row[0]] = {
            'productos_duplicados': row[1],
            'total_duplicados': row[2]
        }
    
    cursor.close()
    conn.close()
    
    return db_products, db_prices, db_duplicates

def main():
    """Función principal"""
    print("ANÁLISIS COMPARATIVO FINAL DE RETAILERS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analizar Excel
    excel_data = analyze_excel_files()
    
    # Analizar DB
    db_products, db_prices, db_duplicates = analyze_database()
    
    # Comparación
    print("\n" + "="*80)
    print("COMPARACIÓN EXCEL vs POSTGRESQL")
    print("="*80)
    
    print(f"\n{'Retailer':<15} | {'Excel Files':>11} | {'Excel Rows':>10} | {'Excel Unique':>12} | {'DB Products':>11} | {'DB Unique':>10} | {'Efficiency':>10}")
    print("-"*110)
    
    total_excel_rows = 0
    total_excel_unique = 0
    total_db_products = 0
    
    for retailer in sorted(set(list(excel_data.keys()) + list(db_products.keys()))):
        excel = excel_data.get(retailer, {'files': 0, 'total_rows': 0, 'unique_names': set()})
        db = db_products.get(retailer, {'total': 0, 'unique_names': 0})
        
        excel_unique = len(excel['unique_names'])
        efficiency = (db['total'] / excel['total_rows'] * 100) if excel['total_rows'] > 0 else 0
        
        print(f"{retailer:<15} | {excel['files']:>11} | {excel['total_rows']:>10,} | {excel_unique:>12,} | {db['total']:>11,} | {db['unique_names']:>10,} | {efficiency:>9.1f}%")
        
        total_excel_rows += excel['total_rows']
        total_excel_unique += excel_unique
        total_db_products += db['total']
    
    print("-"*110)
    print(f"{'TOTAL':<15} | {'':>11} | {total_excel_rows:>10,} | {total_excel_unique:>12,} | {total_db_products:>11,} | {'':>10} | {total_db_products/total_excel_rows*100:>9.1f}%")
    
    # Análisis de duplicados
    print("\n" + "="*80)
    print("ANÁLISIS DE DUPLICACIÓN EN BASE DE DATOS")
    print("="*80)
    
    print(f"\n{'Retailer':<15} | {'Total Productos':>15} | {'Productos Dup.':>15} | {'Total Dup.':>11} | {'% Limpio':>10}")
    print("-"*80)
    
    for retailer in sorted(db_products.keys()):
        db = db_products.get(retailer, {'total': 0})
        dup = db_duplicates.get(retailer, {'productos_duplicados': 0, 'total_duplicados': 0})
        
        pct_limpio = ((db['total'] - dup.get('total_duplicados', 0)) / db['total'] * 100) if db['total'] > 0 else 100
        
        print(f"{retailer:<15} | {db['total']:>15,} | {dup.get('productos_duplicados', 0):>15,} | {dup.get('total_duplicados', 0):>11,} | {pct_limpio:>9.1f}%")
    
    # Análisis temporal
    print("\n" + "="*80)
    print("ANÁLISIS TEMPORAL DE PRECIOS")
    print("="*80)
    
    print(f"\n{'Retailer':<15} | {'Total Precios':>13} | {'Días Únicos':>11} | {'Fecha Min':>12} | {'Fecha Max':>12}")
    print("-"*80)
    
    for retailer in sorted(db_prices.keys()):
        price = db_prices[retailer]
        print(f"{retailer:<15} | {price['total']:>13,} | {price['unique_dates']:>11} | {str(price['min_date']):>12} | {str(price['max_date']):>12}")
    
    # Resumen de problemas detectados
    print("\n" + "="*80)
    print("RESUMEN DE PROBLEMAS DETECTADOS")
    print("="*80)
    
    problemas = []
    
    for retailer in db_products.keys():
        excel = excel_data.get(retailer, {'unique_names': set()})
        db = db_products.get(retailer, {'total': 0, 'unique_names': 0})
        dup = db_duplicates.get(retailer, {'productos_duplicados': 0})
        
        # Verificar si hay duplicados significativos
        if dup.get('productos_duplicados', 0) > 10:
            problemas.append(f"[{retailer}] Tiene {dup['productos_duplicados']} productos duplicados")
        
        # Verificar discrepancia Excel vs DB
        if len(excel['unique_names']) > 0:
            diferencia = abs(len(excel['unique_names']) - db['unique_names'])
            if diferencia > 100:
                problemas.append(f"[{retailer}] Gran diferencia Excel({len(excel['unique_names'])}) vs DB({db['unique_names']})")
    
    if problemas:
        print("\nProblemas encontrados:")
        for problema in problemas:
            print(f"  - {problema}")
    else:
        print("\n[OK] No se detectaron problemas significativos")
    
    # Estadísticas finales
    print("\n" + "="*80)
    print("ESTADÍSTICAS FINALES")
    print("="*80)
    
    print(f"\nEficiencia de deduplicación: {total_db_products/total_excel_rows*100:.1f}%")
    print(f"Reducción de datos: {(1 - total_db_products/total_excel_rows)*100:.1f}%")
    print(f"Factor de compresión: {total_excel_rows/total_db_products:.1f}x")
    
    # Verificar integridad de precios
    conn = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5434'),
        database=os.getenv('PGDATABASE', 'price_orchestrator'),
        user=os.getenv('PGUSER', 'orchestrator'),
        password=os.getenv('PGPASSWORD', 'orchestrator_2025')
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT codigo_interno, fecha, COUNT(*) as cnt
            FROM master_precios
            GROUP BY codigo_interno, fecha
            HAVING COUNT(*) > 1
        ) duplicados
    """)
    
    precio_duplicados = cursor.fetchone()[0]
    
    if precio_duplicados > 0:
        print(f"\n[AVISO] Hay {precio_duplicados} casos de precios duplicados por día")
    else:
        print(f"\n[OK] Constraint de 1 precio por producto por día: CUMPLIDO")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("ANÁLISIS COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()