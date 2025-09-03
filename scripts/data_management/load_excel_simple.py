#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Carga Simple y Robusta de Excel
================================

Script simplificado que prioriza cargar la mayor cantidad de datos posible,
ignorando errores individuales.
"""

import sys
import os
import re
import pandas as pd
import psycopg2
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

def extract_date_from_filename(filename):
    """Extrae fecha del nombre del archivo"""
    pattern = r'(\w+)_(\d{4})_(\d{2})_(\d{2})_(\d{6})\.xlsx'
    match = re.match(pattern, filename)
    
    if match:
        retailer, year, month, day, time_str = match.groups()
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        return datetime(int(year), int(month), int(day), hour, minute, second)
    
    return datetime.now()

def generate_product_code(row, retailer, idx):
    """Generar código interno único"""
    marca = str(row.get('marca', 'UNKN'))[:4].upper().replace(' ', '').replace('-', '')
    if not marca:
        marca = 'UNKN'
    
    # Usar idx para garantizar unicidad
    return f"CL-{marca}-{retailer.upper()[:3]}-{idx:05d}"

def main():
    print("="*70)
    print("CARGA SIMPLE DE ARCHIVOS EXCEL")
    print("="*70)
    
    # Conexión
    conn = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5434'),
        database=os.getenv('PGDATABASE', 'price_orchestrator'),
        user=os.getenv('PGUSER', 'orchestrator'),
        password=os.getenv('PGPASSWORD', 'orchestrator_2025')
    )
    cur = conn.cursor()
    
    # Buscar archivos
    excel_dir = "data/excel"
    excel_files = []
    
    for file in os.listdir(excel_dir):
        if file.endswith('.xlsx') and not file.startswith(('ml_test', 'test_')):
            filepath = os.path.join(excel_dir, file)
            file_date = extract_date_from_filename(file)
            excel_files.append((filepath, file_date))
    
    excel_files.sort(key=lambda x: x[1])
    print(f"\nArchivos encontrados: {len(excel_files)}")
    
    # Estadísticas
    stats = {
        'files': 0,
        'products': 0,
        'prices': 0,
        'errors': 0
    }
    
    # Cache para evitar duplicados
    products_seen = set()
    prices_seen = set()
    
    # Contador global para códigos únicos
    global_idx = 0
    
    print("\nProcesando archivos...")
    
    for filepath, file_date in excel_files:
        filename = os.path.basename(filepath)
        retailer = filename.split('_')[0].lower()
        fecha = file_date.date()
        
        try:
            df = pd.read_excel(filepath)
            stats['files'] += 1
            
            for idx, row in df.iterrows():
                global_idx += 1
                codigo = generate_product_code(row, retailer, global_idx)
                
                # Insertar producto si no existe
                if codigo not in products_seen:
                    try:
                        cur.execute("""
                            INSERT INTO master_productos (
                                codigo_interno, sku, link, nombre, marca, 
                                retailer, categoria, fecha_primera_captura, activo
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (codigo_interno) DO NOTHING
                        """, (
                            codigo,
                            str(row.get('sku', ''))[:100],
                            str(row.get('link', ''))[:1000] if pd.notna(row.get('link')) else '',
                            str(row.get('nombre', ''))[:500],
                            str(row.get('marca', ''))[:100],
                            retailer,
                            str(row.get('categoria', 'general'))[:100],
                            fecha,
                            True
                        ))
                        products_seen.add(codigo)
                        stats['products'] += 1
                    except Exception as e:
                        conn.rollback()
                        stats['errors'] += 1
                        continue
                
                # Insertar precio
                key = (codigo, fecha)
                if key not in prices_seen:
                    try:
                        precio_normal = row.get('precio_normal_num', 0)
                        precio_oferta = row.get('precio_oferta_num', 0)
                        precio_tarjeta = row.get('precio_tarjeta_num', 0)
                        
                        # Al menos un precio válido
                        if precio_normal > 0 or precio_oferta > 0 or precio_tarjeta > 0:
                            precios = [p for p in [precio_normal, precio_oferta, precio_tarjeta] if p > 0]
                            precio_min = min(precios) if precios else 0
                            
                            cur.execute("""
                                INSERT INTO master_precios (
                                    codigo_interno, fecha, retailer, precio_normal, 
                                    precio_oferta, precio_tarjeta, precio_min_dia,
                                    timestamp_creacion
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (codigo_interno, fecha) DO NOTHING
                            """, (
                                codigo, fecha, retailer,
                                precio_normal if precio_normal > 0 else None,
                                precio_oferta if precio_oferta > 0 else None,
                                precio_tarjeta if precio_tarjeta > 0 else None,
                                precio_min if precio_min > 0 else None,
                                file_date
                            ))
                            prices_seen.add(key)
                            stats['prices'] += 1
                    except Exception as e:
                        conn.rollback()
                        stats['errors'] += 1
                        continue
                
                # Commit cada 100 registros
                if (stats['products'] + stats['prices']) % 100 == 0:
                    conn.commit()
                    
            # Progreso
            if stats['files'] % 50 == 0:
                print(f"  Procesados: {stats['files']} archivos, "
                      f"{stats['products']} productos, {stats['prices']} precios")
                
        except Exception as e:
            stats['errors'] += 1
            continue
    
    # Commit final
    conn.commit()
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Archivos procesados: {stats['files']}")
    print(f"Productos insertados: {stats['products']:,}")
    print(f"Precios insertados: {stats['prices']:,}")
    print(f"Errores ignorados: {stats['errors']:,}")
    
    # Verificar en BD
    cur.execute("SELECT COUNT(*) FROM master_productos")
    total_prod = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM master_precios")
    total_prec = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT fecha) FROM master_precios")
    dias = cur.fetchone()[0]
    
    print(f"\n[BASE DE DATOS]")
    print(f"Total productos: {total_prod:,}")
    print(f"Total precios: {total_prec:,}")
    print(f"Días con datos: {dias}")
    
    cur.close()
    conn.close()
    print("\n[COMPLETADO]")

if __name__ == "__main__":
    main()