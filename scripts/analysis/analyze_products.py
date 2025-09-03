#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis detallado de productos en la base de datos
"""

import psycopg2
from dotenv import load_dotenv
import os
from collections import defaultdict

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
print('ANALISIS DETALLADO DE TABLA MASTER_PRODUCTOS')
print('='*70)

# 1. Estadísticas básicas
cur.execute('''
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT codigo_interno) as codigos_unicos,
        COUNT(DISTINCT sku) as skus_unicos,
        COUNT(DISTINCT nombre) as nombres_unicos,
        COUNT(DISTINCT link) as links_unicos,
        COUNT(DISTINCT nombre || '-' || retailer) as nombre_retailer_unicos
    FROM master_productos
''')
stats = cur.fetchone()
print('\n[ESTADISTICAS BASICAS]')
print(f'  Total registros: {stats[0]:,}')
print(f'  Códigos únicos: {stats[1]:,}')
print(f'  SKUs únicos: {stats[2]:,}')
print(f'  Nombres únicos: {stats[3]:,}')
print(f'  Links únicos: {stats[4]:,}')
print(f'  Combinaciones nombre+retailer: {stats[5]:,}')

# 2. Análisis de SKUs
cur.execute('''
    SELECT 
        COUNT(*) as con_sku,
        COUNT(CASE WHEN sku IS NULL THEN 1 END) as sku_null,
        COUNT(CASE WHEN sku = '' THEN 1 END) as sku_vacio,
        COUNT(CASE WHEN sku = 'nan' THEN 1 END) as sku_nan
    FROM master_productos
''')
sku_stats = cur.fetchone()
print('\n[ANALISIS DE SKUs]')
print(f'  Con SKU válido: {sku_stats[0]:,}')
print(f'  SKU NULL: {sku_stats[1]:,}')
print(f'  SKU vacío: {sku_stats[2]:,}')
print(f'  SKU = nan: {sku_stats[3]:,}')

# 3. Productos sin SKU (que fueron excluidos del deduplicado)
cur.execute('''
    SELECT retailer, COUNT(*) 
    FROM master_productos
    WHERE sku = 'nan' OR sku IS NULL OR sku = ''
    GROUP BY retailer
    ORDER BY COUNT(*) DESC
''')
print('\n[PRODUCTOS SIN SKU VALIDO (no se deduplicaron)]')
sin_sku_total = 0
for retailer, count in cur.fetchall():
    print(f'  {retailer}: {count:,}')
    sin_sku_total += count
print(f'  TOTAL SIN SKU: {sin_sku_total:,}')

# 4. Duplicados por nombre exacto + retailer
cur.execute('''
    SELECT nombre, retailer, COUNT(*) as cnt
    FROM master_productos
    GROUP BY nombre, retailer
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 15
''')
print('\n[DUPLICADOS POR NOMBRE EXACTO + RETAILER]')
duplicados_nombre = cur.fetchall()
total_duplicados = 0
for nombre, retailer, count in duplicados_nombre:
    print(f'  {retailer}: "{nombre[:50]}..." x{count}')
    total_duplicados += (count - 1)
    
if duplicados_nombre:
    print(f'\n  Total productos duplicados por nombre: {total_duplicados}')

# 5. Análisis más profundo - productos MercadoLibre sin SKU
cur.execute('''
    SELECT codigo_interno, nombre
    FROM master_productos
    WHERE retailer = 'mercadolibre' AND sku = 'nan'
    LIMIT 10
''')
print('\n[EJEMPLO: MercadoLibre sin SKU (5,703 productos)]')
for codigo, nombre in cur.fetchall()[:5]:
    print(f'  {codigo}: {nombre[:60]}...')

# 6. Verificar si los productos de MercadoLibre son todos diferentes
cur.execute('''
    SELECT COUNT(DISTINCT nombre)
    FROM master_productos
    WHERE retailer = 'mercadolibre' AND sku = 'nan'
''')
ml_nombres_unicos = cur.fetchone()[0]
print(f'\n  Nombres únicos en MercadoLibre sin SKU: {ml_nombres_unicos:,}')

# 7. Ver duplicados por nombre en MercadoLibre
cur.execute('''
    SELECT nombre, COUNT(*) as cnt
    FROM master_productos
    WHERE retailer = 'mercadolibre'
    GROUP BY nombre
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 10
''')
print('\n[DUPLICADOS EN MERCADOLIBRE POR NOMBRE]')
ml_dup = cur.fetchall()
if ml_dup:
    for nombre, count in ml_dup:
        print(f'  "{nombre[:60]}..." x{count}')
else:
    print('  No hay duplicados por nombre en MercadoLibre')

# 8. Análisis global de duplicados potenciales
print('\n' + '='*70)
print('RESUMEN DE DUPLICADOS POTENCIALES')
print('='*70)

# Productos que podrían ser el mismo
cur.execute('''
    WITH productos_normalizados AS (
        SELECT 
            codigo_interno,
            nombre,
            retailer,
            UPPER(REPLACE(REPLACE(SUBSTRING(nombre, 1, 30), ' ', ''), '-', '')) as nombre_norm
        FROM master_productos
    )
    SELECT nombre_norm, COUNT(*) as cnt, COUNT(DISTINCT retailer) as retailers
    FROM productos_normalizados
    GROUP BY nombre_norm
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 20
''')

print('\n[PRODUCTOS PROBABLEMENTE DUPLICADOS (nombre normalizado)]')
for nombre_norm, count, retailers in cur.fetchall():
    print(f'  Producto similar aparece {count} veces en {retailers} retailer(s)')

# 9. Sugerencia de limpieza adicional
print('\n' + '='*70)
print('SUGERENCIAS DE LIMPIEZA ADICIONAL')
print('='*70)

print('\n1. PRODUCTOS SIN SKU (5,703 de MercadoLibre):')
print('   - Estos productos no se deduplicaron porque no tienen SKU')
print('   - Podrían contener duplicados por nombre')

print('\n2. DEDUPLICACION POR NOMBRE:')
print('   - Se podría hacer una deduplicación adicional por nombre+retailer')
print('   - Esto eliminaría productos con nombres idénticos del mismo retailer')

# Contar cuántos se eliminarían
cur.execute('''
    WITH productos_a_mantener AS (
        SELECT DISTINCT ON (nombre, retailer) codigo_interno
        FROM master_productos
        ORDER BY nombre, retailer, fecha_ultima_actualizacion DESC
    )
    SELECT COUNT(*)
    FROM master_productos
    WHERE codigo_interno NOT IN (SELECT codigo_interno FROM productos_a_mantener)
''')
eliminables = cur.fetchone()[0]

print(f'\n3. IMPACTO DE DEDUPLICACION POR NOMBRE:')
print(f'   - Se eliminarían {eliminables:,} productos adicionales')
print(f'   - Quedarían aproximadamente {stats[0] - eliminables:,} productos únicos')

cur.close()
conn.close()