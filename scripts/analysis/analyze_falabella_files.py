#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis detallado de archivos Excel de Falabella
"""

import pandas as pd
import os
from datetime import datetime
from collections import defaultdict, Counter

def extract_date_from_filename(filename):
    """Extrae fecha del nombre del archivo"""
    parts = filename.replace('.xlsx', '').split('_')
    if len(parts) >= 5:
        year, month, day, time = parts[1], parts[2], parts[3], parts[4]
        return f"{year}-{month}-{day} {time[:2]}:{time[2:4]}"
    return "unknown"

def main():
    excel_dir = 'data/excel'
    falabella_files = [f for f in os.listdir(excel_dir) if f.startswith('falabella') and f.endswith('.xlsx')]
    falabella_files.sort()
    
    print('='*80)
    print('ANÁLISIS DETALLADO DE ARCHIVOS FALABELLA')
    print('='*80)
    
    print(f'\nTotal archivos Falabella: {len(falabella_files)}')
    
    # Estadísticas globales
    all_products = []
    file_stats = []
    productos_por_dia = defaultdict(set)
    nombres_unicos_global = set()
    skus_unicos_global = set()
    
    # Analizar cada archivo
    for i, file in enumerate(falabella_files):
        filepath = os.path.join(excel_dir, file)
        fecha_hora = extract_date_from_filename(file)
        fecha = fecha_hora.split()[0] if ' ' in fecha_hora else fecha_hora
        
        try:
            df = pd.read_excel(filepath)
            
            # Estadísticas del archivo
            num_rows = len(df)
            unique_names = df['nombre'].nunique() if 'nombre' in df.columns else 0
            unique_links = df['link'].nunique() if 'link' in df.columns else 0
            unique_skus = df['sku'].nunique() if 'sku' in df.columns else 0
            has_valid_sku = ((df['sku'] != 'nan') & df['sku'].notna()).sum() if 'sku' in df.columns else 0
            
            file_stats.append({
                'file': file,
                'fecha': fecha,
                'hora': fecha_hora.split()[1] if ' ' in fecha_hora else '00:00',
                'rows': num_rows,
                'unique_names': unique_names,
                'unique_links': unique_links,
                'unique_skus': unique_skus,
                'has_valid_sku': has_valid_sku
            })
            
            # Agregar a estadísticas globales
            for _, row in df.iterrows():
                nombre = str(row.get('nombre', ''))
                sku = str(row.get('sku', ''))
                productos_por_dia[fecha].add(nombre)
                nombres_unicos_global.add(nombre)
                if sku and sku != 'nan':
                    skus_unicos_global.add(sku)
                all_products.append({
                    'nombre': nombre,
                    'sku': sku,
                    'fecha': fecha,
                    'archivo': file
                })
            
            # Mostrar primeros archivos en detalle
            if i < 5:
                print(f'\n[Archivo {i+1}]: {file}')
                print(f'  Fecha/Hora: {fecha_hora}')
                print(f'  Total filas: {num_rows}')
                print(f'  Nombres únicos: {unique_names}')
                print(f'  SKUs únicos: {unique_skus}')
                print(f'  Con SKU válido: {has_valid_sku}')
                
                if num_rows > 0:
                    print(f'  Primeros 3 productos:')
                    for j in range(min(3, len(df))):
                        nombre = df.iloc[j]['nombre'] if 'nombre' in df.columns else 'N/A'
                        sku = df.iloc[j]['sku'] if 'sku' in df.columns else 'N/A'
                        print(f'    {j+1}. SKU:{sku} - {nombre[:50]}...')
                        
        except Exception as e:
            print(f'  Error leyendo {file}: {e}')
    
    # Análisis por día
    print('\n' + '='*80)
    print('RESUMEN POR DÍA')
    print('='*80)
    
    dias_resumen = defaultdict(lambda: {'archivos': 0, 'total_filas': 0, 'nombres_unicos': 0})
    
    for stat in file_stats:
        fecha = stat['fecha']
        dias_resumen[fecha]['archivos'] += 1
        dias_resumen[fecha]['total_filas'] += stat['rows']
        
    for fecha, productos in productos_por_dia.items():
        dias_resumen[fecha]['nombres_unicos'] = len(productos)
    
    print(f'\n{"Fecha":<12} | {"Archivos":>8} | {"Total Filas":>11} | {"Productos Únicos":>16}')
    print('-'*60)
    
    total_archivos = 0
    total_filas = 0
    
    for fecha in sorted(dias_resumen.keys()):
        info = dias_resumen[fecha]
        print(f'{fecha:<12} | {info["archivos"]:>8} | {info["total_filas"]:>11,} | {info["nombres_unicos"]:>16,}')
        total_archivos += info['archivos']
        total_filas += info['total_filas']
    
    print('-'*60)
    print(f'{"TOTAL":<12} | {total_archivos:>8} | {total_filas:>11,} | {len(nombres_unicos_global):>16,}')
    
    # Análisis de duplicación
    print('\n' + '='*80)
    print('ANÁLISIS DE DUPLICACIÓN')
    print('='*80)
    
    # Contar cuántas veces aparece cada producto
    nombres_counter = Counter([p['nombre'] for p in all_products])
    skus_counter = Counter([p['sku'] for p in all_products if p['sku'] != 'nan'])
    
    # Top 20 productos más repetidos
    print('\nTop 20 productos más repetidos en Falabella:')
    print('-'*80)
    
    for nombre, count in nombres_counter.most_common(20):
        print(f'{count:3}x | {nombre[:70]}...')
    
    # Análisis de SKUs
    print('\n' + '='*80)
    print('ANÁLISIS DE SKUs')
    print('='*80)
    
    print(f'\nTotal SKUs únicos: {len(skus_unicos_global):,}')
    
    # SKUs más repetidos
    if skus_counter:
        print('\nTop 10 SKUs más repetidos:')
        for sku, count in skus_counter.most_common(10):
            if sku and sku != 'nan':
                # Buscar nombre del producto con este SKU
                nombre_sku = next((p['nombre'] for p in all_products if p['sku'] == sku), 'N/A')
                print(f'  SKU {sku}: {count}x - {nombre_sku[:50]}...')
    
    # Distribución de repeticiones
    print('\n' + '='*80)
    print('DISTRIBUCIÓN DE REPETICIONES')
    print('='*80)
    
    repeticiones_dist = defaultdict(int)
    for nombre, count in nombres_counter.items():
        if count == 1:
            repeticiones_dist['1 vez'] += 1
        elif count <= 10:
            repeticiones_dist['2-10 veces'] += 1
        elif count <= 50:
            repeticiones_dist['11-50 veces'] += 1
        elif count <= 100:
            repeticiones_dist['51-100 veces'] += 1
        else:
            repeticiones_dist['100+ veces'] += 1
    
    print('\nProductos por frecuencia de aparición:')
    for rango, cantidad in sorted(repeticiones_dist.items()):
        pct = (cantidad / len(nombres_counter)) * 100
        print(f'  {rango:<15}: {cantidad:>5} productos ({pct:>5.1f}%)')
    
    # Análisis temporal
    print('\n' + '='*80)
    print('ANÁLISIS TEMPORAL')
    print('='*80)
    
    # Ver distribución por hora
    horas_dist = defaultdict(int)
    for stat in file_stats:
        hora = stat['hora'][:2] if stat.get('hora') else '00'
        horas_dist[hora] += stat['rows']
    
    print('\nDistribución de productos por hora:')
    for hora in sorted(horas_dist.keys()):
        count = horas_dist[hora]
        print(f'  {hora}:00 - {count:>6,} productos')
    
    # Estadísticas finales
    print('\n' + '='*80)
    print('ESTADÍSTICAS FINALES')
    print('='*80)
    
    print(f'\nTotal archivos analizados: {len(falabella_files)}')
    print(f'Total registros procesados: {total_filas:,}')
    print(f'Productos únicos (por nombre): {len(nombres_unicos_global):,}')
    print(f'SKUs únicos: {len(skus_unicos_global):,}')
    print(f'Promedio de repeticiones: {total_filas / len(nombres_unicos_global) if nombres_unicos_global else 0:.1f}')
    
    print(f'\n[CONCLUSIÓN]')
    print(f'  Falabella tiene {len(nombres_unicos_global):,} productos únicos por nombre')
    print(f'  Falabella tiene {len(skus_unicos_global):,} SKUs únicos')
    print(f'  Los productos aparecen {total_filas:,} veces en total')
    print(f'  Cada producto aparece en promedio {total_filas/len(nombres_unicos_global):.1f} veces')
    
    # Verificar si hay muchos productos con el mismo SKU
    productos_por_sku = defaultdict(set)
    for p in all_products:
        if p['sku'] != 'nan':
            productos_por_sku[p['sku']].add(p['nombre'])
    
    skus_con_multiples_nombres = [(sku, nombres) for sku, nombres in productos_por_sku.items() if len(nombres) > 1]
    
    if skus_con_multiples_nombres:
        print(f'\n[AVISO] Hay {len(skus_con_multiples_nombres)} SKUs con múltiples nombres diferentes')
        for sku, nombres in skus_con_multiples_nombres[:5]:
            print(f'  SKU {sku}:')
            for nombre in list(nombres)[:3]:
                print(f'    - {nombre[:60]}...')

if __name__ == "__main__":
    main()