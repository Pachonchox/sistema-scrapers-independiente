#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Carga Final Optimizada con Deduplicación Real
==============================================

Este script:
1. Genera SKU robusto basado en características del producto
2. DEDUPLICA por nombre+retailer para evitar productos repetidos
3. Mantiene solo el registro más reciente de cada producto
4. Respeta el constraint de 1 precio por producto por día
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
import hashlib

# Importar el generador robusto
from generate_robust_sku import RobustSKUGenerator

load_dotenv()

class FinalExcelLoader:
    def __init__(self):
        """Inicializar cargador final optimizado"""
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025')
        )
        self.cursor = self.conn.cursor()
        self.sku_generator = RobustSKUGenerator()
        
        self.stats = {
            'files_processed': 0,
            'products_unique': 0,
            'products_skipped': 0,
            'prices_loaded': 0,
            'errors': 0
        }
        
        # Cache CRÍTICO: Deduplicar por nombre+retailer
        self.product_cache = {}  # key: (nombre, retailer), value: codigo_interno
        self.price_cache = set()  # key: (codigo_interno, fecha)
        
    def extract_date_from_filename(self, filename: str) -> datetime:
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
    
    def find_excel_files(self, directory: str = "data/excel") -> list:
        """Buscar y ordenar archivos Excel cronológicamente"""
        excel_files = []
        
        if not os.path.exists(directory):
            return []
        
        for file in os.listdir(directory):
            if file.endswith('.xlsx') and not file.startswith(('ml_test', 'test_')):
                filepath = os.path.join(directory, file)
                file_date = self.extract_date_from_filename(file)
                excel_files.append((filepath, file_date))
        
        # CRÍTICO: Ordenar por fecha (más antiguos primero)
        excel_files.sort(key=lambda x: x[1])
        return excel_files
    
    def normalize_product_name(self, nombre: str) -> str:
        """Normalizar nombre para mejor deduplicación"""
        # Limpiar espacios extras y convertir a minúsculas para comparación
        nombre = ' '.join(nombre.split())
        return nombre.lower().strip()
    
    def generate_unique_sku(self, row: dict, retailer: str, nombre_normalizado: str) -> str:
        """
        Generar SKU único basado en el nombre normalizado
        Para productos idénticos, genera el mismo SKU
        """
        # Usar el generador robusto para extraer componentes
        marca = self.sku_generator.extract_brand(row.get('nombre', ''), row.get('marca', ''))
        modelo = self.sku_generator.extract_model(row.get('nombre', ''))
        specs = self.sku_generator.extract_specs(row.get('nombre', ''))
        
        # Código de retailer
        ret_codes = {
            'ripley': 'RIP',
            'falabella': 'FAL',
            'paris': 'PAR',
            'mercadolibre': 'ML',
            'hites': 'HIT',
            'abcdin': 'ABC'
        }
        ret_code = ret_codes.get(retailer.lower(), 'UNK')
        
        # CRÍTICO: Hash basado en nombre normalizado para consistencia
        hash_text = f"{nombre_normalizado}-{retailer}"
        hash_part = hashlib.md5(hash_text.encode()).hexdigest()[:6].upper()
        
        # Construir SKU
        sku = f"CL-{marca[:4]}-{modelo[:8]}"
        if specs != 'NA':
            sku += f"-{specs[:10]}"
        sku += f"-{ret_code}-{hash_part}"
        
        return re.sub(r'[^A-Z0-9\-]', '', sku.upper())[:50]
    
    def load_all_files(self, directory: str = "data/excel"):
        """Cargar todos los archivos con deduplicación real"""
        print("="*70)
        print("CARGA FINAL CON DEDUPLICACIÓN REAL")
        print("="*70)
        
        excel_files = self.find_excel_files(directory)
        
        if not excel_files:
            print("[AVISO] No se encontraron archivos Excel")
            return
        
        print(f"\nArchivos encontrados: {len(excel_files)}")
        
        # Agrupar por día
        files_by_day = defaultdict(list)
        for filepath, file_date in excel_files:
            day_key = file_date.date()
            files_by_day[day_key].append((filepath, file_date))
        
        print(f"Días únicos: {len(files_by_day)}")
        
        print("\n" + "="*70)
        print("PROCESANDO ARCHIVOS")
        print("="*70)
        
        # Procesar por día en orden cronológico
        for day in sorted(files_by_day.keys()):
            day_files = files_by_day[day]
            print(f"\n{day}: {len(day_files)} archivos")
            
            day_products = 0
            day_prices = 0
            
            for filepath, file_date in day_files:
                filename = os.path.basename(filepath)
                retailer = filename.split('_')[0].lower()
                fecha = file_date.date()
                
                try:
                    df = pd.read_excel(filepath)
                    
                    for _, row in df.iterrows():
                        nombre = str(row.get('nombre', '')).strip()
                        if not nombre:
                            continue
                        
                        # Normalizar nombre para deduplicación
                        nombre_norm = self.normalize_product_name(nombre)
                        cache_key = (nombre_norm, retailer)
                        
                        # Verificar si ya existe este producto
                        if cache_key in self.product_cache:
                            codigo_interno = self.product_cache[cache_key]
                            self.stats['products_skipped'] += 1
                        else:
                            # Nuevo producto único
                            codigo_interno = self.generate_unique_sku(row.to_dict(), retailer, nombre_norm)
                            
                            # Insertar producto
                            try:
                                self.cursor.execute("""
                                    INSERT INTO master_productos (
                                        codigo_interno, sku, link, nombre, marca, retailer,
                                        categoria, fecha_primera_captura, fecha_ultima_actualizacion,
                                        ultimo_visto, activo
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (codigo_interno) DO UPDATE SET
                                        ultimo_visto = EXCLUDED.ultimo_visto
                                """, (
                                    codigo_interno,
                                    str(row.get('sku', ''))[:100] if pd.notna(row.get('sku')) else '',
                                    str(row.get('link', ''))[:1000] if pd.notna(row.get('link')) else '',
                                    nombre[:500],
                                    str(row.get('marca', ''))[:100],
                                    retailer,
                                    str(row.get('categoria', 'general'))[:100],
                                    fecha, fecha, fecha, True
                                ))
                                
                                self.product_cache[cache_key] = codigo_interno
                                self.stats['products_unique'] += 1
                                day_products += 1
                                
                            except Exception as e:
                                self.conn.rollback()
                                self.stats['errors'] += 1
                                continue
                        
                        # Insertar precio (solo uno por día)
                        price_key = (codigo_interno, fecha)
                        if price_key not in self.price_cache:
                            # Obtener precios
                            precio_normal = None
                            precio_oferta = None
                            precio_tarjeta = None
                            
                            if pd.notna(row.get('precio_normal_num')) and row.get('precio_normal_num') > 0:
                                precio_normal = int(row['precio_normal_num'])
                            elif pd.notna(row.get('normal_num')) and row.get('normal_num') > 0:
                                precio_normal = int(row['normal_num'])
                            
                            if pd.notna(row.get('precio_oferta_num')) and row.get('precio_oferta_num') > 0:
                                precio_oferta = int(row['precio_oferta_num'])
                            elif pd.notna(row.get('oferta_num')) and row.get('oferta_num') > 0:
                                precio_oferta = int(row['oferta_num'])
                            
                            if pd.notna(row.get('precio_tarjeta_num')) and row.get('precio_tarjeta_num') > 0:
                                precio_tarjeta = int(row['precio_tarjeta_num'])
                            elif pd.notna(row.get('tarjeta_num')) and row.get('tarjeta_num') > 0:
                                precio_tarjeta = int(row['tarjeta_num'])
                            
                            if precio_normal or precio_oferta or precio_tarjeta:
                                precios = [p for p in [precio_normal, precio_oferta, precio_tarjeta] if p]
                                precio_min = min(precios) if precios else None
                                
                                try:
                                    self.cursor.execute("""
                                        INSERT INTO master_precios (
                                            codigo_interno, fecha, retailer, precio_normal,
                                            precio_oferta, precio_tarjeta, precio_min_dia,
                                            timestamp_creacion
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                        ON CONFLICT (codigo_interno, fecha) DO NOTHING
                                    """, (
                                        codigo_interno, fecha, retailer,
                                        precio_normal, precio_oferta, precio_tarjeta,
                                        precio_min, file_date
                                    ))
                                    
                                    self.price_cache.add(price_key)
                                    self.stats['prices_loaded'] += 1
                                    day_prices += 1
                                    
                                except Exception as e:
                                    self.conn.rollback()
                                    self.stats['errors'] += 1
                    
                    self.stats['files_processed'] += 1
                    
                    # Commit cada archivo
                    self.conn.commit()
                    
                except Exception as e:
                    if "Bad magic number" not in str(e):
                        self.stats['errors'] += 1
            
            print(f"  Productos nuevos: {day_products}, Precios: {day_prices}")
        
        self.show_summary()
    
    def show_summary(self):
        """Mostrar resumen final"""
        print("\n" + "="*70)
        print("RESUMEN FINAL")
        print("="*70)
        
        print(f"\n[PROCESAMIENTO]")
        print(f"  Archivos procesados: {self.stats['files_processed']}")
        print(f"  Productos únicos encontrados: {self.stats['products_unique']:,}")
        print(f"  Productos duplicados omitidos: {self.stats['products_skipped']:,}")
        print(f"  Precios cargados: {self.stats['prices_loaded']:,}")
        print(f"  Errores: {self.stats['errors']:,}")
        
        # Verificación en BD
        self.cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM master_productos) as productos,
                (SELECT COUNT(*) FROM master_precios) as precios,
                (SELECT COUNT(DISTINCT fecha) FROM master_precios) as dias
        """)
        productos, precios, dias = self.cursor.fetchone()
        
        print(f"\n[BASE DE DATOS]")
        print(f"  Total productos únicos: {productos:,}")
        print(f"  Total precios: {precios:,}")
        print(f"  Días con datos: {dias}")
        
        # Por retailer con análisis de unicidad
        self.cursor.execute("""
            SELECT 
                retailer, 
                COUNT(*) as productos,
                COUNT(DISTINCT nombre) as nombres_unicos
            FROM master_productos
            GROUP BY retailer
            ORDER BY productos DESC
        """)
        
        print(f"\n[PRODUCTOS POR RETAILER]")
        print(f"  {'Retailer':<15} | {'Productos':>10} | {'Nombres Únicos':>15}")
        print(f"  {'-'*15}-+-{'-'*10}-+-{'-'*15}")
        
        for retailer, prods, nombres in self.cursor.fetchall():
            print(f"  {retailer:<15} | {prods:>10,} | {nombres:>15,}")
        
        # Verificar MercadoLibre específicamente
        self.cursor.execute("""
            SELECT nombre, COUNT(*) as cnt
            FROM master_productos
            WHERE retailer = 'mercadolibre'
            GROUP BY nombre
            HAVING COUNT(*) > 1
            LIMIT 5
        """)
        
        duplicados_ml = self.cursor.fetchall()
        if duplicados_ml:
            print(f"\n[AVISO] Aún hay duplicados en MercadoLibre:")
            for nombre, count in duplicados_ml:
                print(f"  {count}x: {nombre[:60]}...")
        else:
            print(f"\n[OK] No hay productos duplicados en MercadoLibre")
    
    def close(self):
        """Cerrar conexiones"""
        self.cursor.close()
        self.conn.close()

def main():
    """Función principal"""
    print("SISTEMA DE CARGA FINAL OPTIMIZADO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Truncar tablas
    conn = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5434'),
        database=os.getenv('PGDATABASE', 'price_orchestrator'),
        user=os.getenv('PGUSER', 'orchestrator'),
        password=os.getenv('PGPASSWORD', 'orchestrator_2025')
    )
    cur = conn.cursor()
    
    print("\nTruncando tablas...")
    cur.execute("TRUNCATE TABLE master_precios, master_productos CASCADE")
    conn.commit()
    print("[OK] Tablas truncadas")
    
    cur.close()
    conn.close()
    
    # Cargar con deduplicación real
    loader = FinalExcelLoader()
    
    try:
        loader.load_all_files()
    finally:
        loader.close()
    
    print("\n[COMPLETADO]")

if __name__ == "__main__":
    main()