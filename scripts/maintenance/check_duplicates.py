#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificación y eliminación de productos duplicados
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('PGHOST', 'localhost'),
    port=os.getenv('PGPORT', '5434'),
    database=os.getenv('PGDATABASE', 'price_orchestrator'),
    user=os.getenv('PGUSER', 'orchestrator'),
    password=os.getenv('PGPASSWORD', 'orchestrator_2025')
)
cur = conn.cursor()

print('='*70)
print('ANALISIS DETALLADO DE DUPLICADOS')
print('='*70)

# 1. Contar duplicados reales por SKU
cur.execute("""
    SELECT retailer, COUNT(*) as productos_duplicados
    FROM (
        SELECT sku, retailer, COUNT(*) as cnt
        FROM master_productos
        WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
        GROUP BY sku, retailer
        HAVING COUNT(*) > 1
    ) as duplicados
    GROUP BY retailer
    ORDER BY productos_duplicados DESC
""")

print('\n[DUPLICADOS POR RETAILER] (productos con mismo SKU):')
total_dup = 0
duplicados_por_retailer = cur.fetchall()
for retailer, count in duplicados_por_retailer:
    print(f'  {retailer}: {count} SKUs duplicados')
    total_dup += count

if total_dup == 0:
    print('  [OK] No hay duplicados por SKU')

# 2. Impacto de duplicados
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT CASE WHEN sku != 'nan' THEN sku || '-' || retailer END) as unicos_por_sku,
        COUNT(*) - COUNT(DISTINCT CASE WHEN sku != 'nan' THEN sku || '-' || retailer END) as duplicados
    FROM master_productos
    WHERE sku IS NOT NULL AND sku != ''
""")
total, unicos, duplicados = cur.fetchone()

print(f'\n[IMPACTO DE DUPLICADOS]:')
print(f'  Total productos (con SKU válido): {total:,}')
print(f'  Productos únicos por SKU: {unicos:,}')
print(f'  Registros duplicados: {duplicados:,}')
if total > 0:
    print(f'  Porcentaje duplicado: {(duplicados/total)*100:.1f}%')

# 3. Top 10 productos más duplicados
cur.execute("""
    WITH duplicados AS (
        SELECT sku, retailer
        FROM master_productos
        WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
        GROUP BY sku, retailer
        HAVING COUNT(*) > 1
    )
    SELECT 
        p.sku,
        p.retailer,
        COUNT(DISTINCT p.fecha_primera_captura) as dias_diferentes,
        COUNT(*) as total_registros,
        MIN(p.codigo_interno) as primer_codigo,
        MAX(p.codigo_interno) as ultimo_codigo
    FROM master_productos p
    INNER JOIN duplicados d ON p.sku = d.sku AND p.retailer = d.retailer
    GROUP BY p.sku, p.retailer
    ORDER BY total_registros DESC
    LIMIT 10
""")

duplicados_top = cur.fetchall()
if duplicados_top:
    print('\n[ANALISIS TEMPORAL] Top 10 productos más duplicados:')
    for sku, retailer, dias, total, primer, ultimo in duplicados_top:
        print(f'  SKU {sku} ({retailer}):')
        print(f'    - {total} registros en {dias} día(s) diferentes')
        print(f'    - Códigos: {primer} ... {ultimo}')

# 4. Identificar duplicados a eliminar
print('\n' + '='*70)
print('ELIMINACION DE DUPLICADOS')
print('='*70)

# Contar duplicados a eliminar
cur.execute("""
    WITH productos_a_mantener AS (
        SELECT DISTINCT ON (sku, retailer) codigo_interno
        FROM master_productos
        WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
        ORDER BY sku, retailer, fecha_ultima_actualizacion DESC, codigo_interno DESC
    )
    SELECT COUNT(*) 
    FROM master_productos
    WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
        AND codigo_interno NOT IN (SELECT codigo_interno FROM productos_a_mantener)
""")

duplicados_a_eliminar = cur.fetchone()[0]
print(f'\nProductos duplicados identificados: {duplicados_a_eliminar:,}')

if duplicados_a_eliminar > 0:
    respuesta = input('\n¿Desea eliminar los duplicados? (s/n): ')
    
    if respuesta.lower() == 's':
        # Eliminar duplicados de precios primero
        cur.execute("""
            DELETE FROM master_precios
            WHERE codigo_interno IN (
                WITH productos_a_mantener AS (
                    SELECT DISTINCT ON (sku, retailer) codigo_interno
                    FROM master_productos
                    WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
                    ORDER BY sku, retailer, fecha_ultima_actualizacion DESC, codigo_interno DESC
                )
                SELECT codigo_interno 
                FROM master_productos
                WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
                    AND codigo_interno NOT IN (SELECT codigo_interno FROM productos_a_mantener)
            )
        """)
        precios_eliminados = cur.rowcount
        
        # Eliminar duplicados de productos
        cur.execute("""
            DELETE FROM master_productos
            WHERE codigo_interno IN (
                WITH productos_a_mantener AS (
                    SELECT DISTINCT ON (sku, retailer) codigo_interno
                    FROM master_productos
                    WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
                    ORDER BY sku, retailer, fecha_ultima_actualizacion DESC, codigo_interno DESC
                )
                SELECT codigo_interno 
                FROM master_productos
                WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
                    AND codigo_interno NOT IN (SELECT codigo_interno FROM productos_a_mantener)
            )
        """)
        productos_eliminados = cur.rowcount
        
        conn.commit()
        print(f'\n[OK] Eliminados:')
        print(f'  - {productos_eliminados:,} productos duplicados')
        print(f'  - {precios_eliminados:,} precios asociados')
    else:
        print('\n[INFO] Operación cancelada')

# 5. Verificación final
cur.execute("SELECT COUNT(*) FROM master_productos")
total_final = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM master_precios")
precios_final = cur.fetchone()[0]

print('\n' + '='*70)
print('ESTADO FINAL')
print('='*70)
print(f'Total productos: {total_final:,}')
print(f'Total precios: {precios_final:,}')

# Verificar que no hay duplicados
cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT sku, retailer, COUNT(*) as cnt
        FROM master_productos
        WHERE sku IS NOT NULL AND sku != '' AND sku != 'nan'
        GROUP BY sku, retailer
        HAVING COUNT(*) > 1
    ) as dup
""")
duplicados_restantes = cur.fetchone()[0]

if duplicados_restantes == 0:
    print('[OK] No hay duplicados por SKU+retailer')
else:
    print(f'[AVISO] Aún quedan {duplicados_restantes} SKUs duplicados')

cur.close()
conn.close()