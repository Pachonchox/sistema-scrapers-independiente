#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis detallado de archivos Excel de MercadoLibre
"""

import pandas as pd
import os
from datetime import datetime
from collections import defaultdict

def extract_date_from_filename(filename):
    """Extrae fecha del nombre del archivo"""
    parts = filename.replace('.xlsx', '').split('_')
    if len(parts) >= 5:
        year, month, day, time = parts[1], parts[2], parts[3], parts[4]
        return f"{year}-{month}-{day} {time[:2]}:{time[2:4]}"
    return "unknown"

def main():
    excel_dir = 'data/excel'
    ml_files = [f for f in os.listdir(excel_dir) if f.startswith('mercadolibre') and f.endswith('.xlsx')]
    ml_files.sort()
    
    print('='*80)
    print('ANÁLISIS DETALLADO DE ARCHIVOS MERCADOLIBRE')
    print('='*80)
    
    print(f'\nTotal archivos MercadoLibre: {len(ml_files)}')
    
    # Estadísticas globales
    all_products = []
    file_stats = []
    productos_por_dia = defaultdict(set)
    nombres_unicos_global = set()
    
    # Analizar cada archivo
    for i, file in enumerate(ml_files):
        filepath = os.path.join(excel_dir, file)
        fecha_hora = extract_date_from_filename(file)
        fecha = fecha_hora.split()[0] if ' ' in fecha_hora else fecha_hora
        
        try:
            df = pd.read_excel(filepath)
            
            # Estadísticas del archivo
            num_rows = len(df)
            unique_names = df['nombre'].nunique() if 'nombre' in df.columns else 0
            unique_links = df['link'].nunique() if 'link' in df.columns else 0
            has_sku = (df['sku'] != 'nan').sum() if 'sku' in df.columns else 0
            
            file_stats.append({
                'file': file,
                'fecha': fecha,
                'rows': num_rows,
                'unique_names': unique_names,
                'unique_links': unique_links,
                'has_sku': has_sku
            })
            
            # Agregar a estadísticas globales
            for _, row in df.iterrows():
                nombre = str(row.get('nombre', ''))
                productos_por_dia[fecha].add(nombre)
                nombres_unicos_global.add(nombre)
                all_products.append({
                    'nombre': nombre,
                    'fecha': fecha,
                    'archivo': file
                })
            
            # Mostrar primeros archivos en detalle
            if i < 5:
                print(f'\n[Archivo {i+1}]: {file}')
                print(f'  Fecha/Hora: {fecha_hora}')
                print(f'  Total filas: {num_rows}')
                print(f'  Nombres únicos: {unique_names}')
                print(f'  Links únicos: {unique_links}')
                print(f'  Con SKU válido: {has_sku}')
                
                if num_rows > 0:
                    # Ver algunos productos
                    print(f'  Primeros 3 productos:')
                    for j in range(min(3, len(df))):
                        nombre = df.iloc[j]['nombre'] if 'nombre' in df.columns else 'N/A'
                        print(f'    {j+1}. {nombre[:60]}...')
                        
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
    from collections import Counter
    nombres_counter = Counter([p['nombre'] for p in all_products])
    
    # Top 20 productos más repetidos
    print('\nTop 20 productos más repetidos (aparecen en múltiples archivos):')
    print('-'*80)
    
    for nombre, count in nombres_counter.most_common(20):
        print(f'{count:3}x | {nombre[:70]}...')
    
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
        elif count <= 200:
            repeticiones_dist['101-200 veces'] += 1
        else:
            repeticiones_dist['200+ veces'] += 1
    
    print('\nProductos por frecuencia de aparición:')
    for rango, cantidad in sorted(repeticiones_dist.items()):
        pct = (cantidad / len(nombres_counter)) * 100
        print(f'  {rango:<15}: {cantidad:>5} productos ({pct:>5.1f}%)')
    
    # Estadísticas finales
    print('\n' + '='*80)
    print('ESTADÍSTICAS FINALES')
    print('='*80)
    
    print(f'\nTotal archivos analizados: {len(ml_files)}')
    print(f'Total registros procesados: {total_filas:,}')
    print(f'Productos únicos (por nombre): {len(nombres_unicos_global):,}')
    print(f'Promedio de repeticiones: {total_filas / len(nombres_unicos_global) if nombres_unicos_global else 0:.1f}')
    
    # Calcular cuántos productos únicos deberíamos tener
    productos_reales = len(nombres_unicos_global)
    print(f'\n[CONCLUSIÓN]')
    print(f'  MercadoLibre tiene solo {productos_reales} productos únicos')
    print(f'  Pero aparecen {total_filas:,} veces en total en los archivos')
    print(f'  Cada producto aparece en promedio {total_filas/productos_reales:.0f} veces')

if __name__ == "__main__":
    main()