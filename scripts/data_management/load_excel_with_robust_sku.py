#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Carga de Excel con Generación Robusta de SKU
=============================================

Este script:
1. Usa el generador robusto de SKU para crear códigos únicos
2. Deduplica por SKU generado (no por nombre)
3. Maneja correctamente productos de MercadoLibre sin SKU
4. Carga en orden cronológico
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

class RobustExcelLoader:
    def __init__(self):
        """Inicializar cargador con generador robusto de SKU"""
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
            'products_loaded': 0,
            'prices_loaded': 0,
            'duplicates_skipped': 0,
            'errors': []
        }
        
        # Cache de SKUs generados para evitar duplicados
        self.sku_cache = {}  # key: sku_generado, value: codigo_interno
        self.product_index = 0  # Índice global para unicidad
        
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
        
        excel_files.sort(key=lambda x: x[1])
        return excel_files
    
    def process_excel_file(self, filepath: str, file_date: datetime, retailer: str):
        """Procesar un archivo Excel con SKU robusto"""
        try:
            df = pd.read_excel(filepath)
            fecha = file_date.date()
            
            products_batch = []
            prices_batch = []
            
            for idx, row in df.iterrows():
                self.product_index += 1
                
                # Generar SKU robusto
                sku_generado = self.sku_generator.generate_sku(
                    row.to_dict(), 
                    retailer, 
                    self.product_index
                )
                
                # Si ya existe este SKU, solo actualizar precio
                if sku_generado in self.sku_cache:
                    codigo_interno = self.sku_cache[sku_generado]
                    # Solo agregar precio si es de un día diferente
                    key_precio = (codigo_interno, fecha)
                    if key_precio not in prices_batch:
                        price_data = self.prepare_price(row, codigo_interno, fecha, retailer, file_date)
                        if price_data:
                            prices_batch.append(price_data)
                else:
                    # Nuevo producto
                    codigo_interno = sku_generado
                    self.sku_cache[sku_generado] = codigo_interno
                    
                    # Preparar producto
                    product_data = self.prepare_product(row, codigo_interno, fecha, retailer)
                    products_batch.append(product_data)
                    
                    # Preparar precio
                    price_data = self.prepare_price(row, codigo_interno, fecha, retailer, file_date)
                    if price_data:
                        prices_batch.append((codigo_interno, fecha))
                        prices_batch.append(price_data)
            
            # Insertar batch
            self.insert_batch(products_batch, prices_batch)
            self.stats['files_processed'] += 1
            
        except Exception as e:
            if "Bad magic number" not in str(e):
                self.stats['errors'].append(f"Error en {os.path.basename(filepath)}: {str(e)[:100]}")
    
    def prepare_product(self, row, codigo_interno, fecha, retailer):
        """Preparar datos del producto"""
        return {
            'codigo_interno': codigo_interno,
            'sku': str(row.get('sku', ''))[:100] if pd.notna(row.get('sku')) else '',
            'link': str(row.get('link', ''))[:1000] if pd.notna(row.get('link')) else '',
            'nombre': str(row.get('nombre', ''))[:500],
            'marca': str(row.get('marca', ''))[:100],
            'retailer': retailer,
            'categoria': str(row.get('categoria', 'general'))[:100],
            'storage': str(row.get('storage', ''))[:50] if pd.notna(row.get('storage')) else '',
            'ram': str(row.get('ram', ''))[:50] if pd.notna(row.get('ram')) else '',
            'color': str(row.get('color', ''))[:50] if pd.notna(row.get('color')) else '',
            'rating': float(row.get('rating')) if pd.notna(row.get('rating')) and str(row.get('rating')).replace('.','').replace('-','').isdigit() else None,
            'reviews_count': int(row.get('reviews', 0)) if pd.notna(row.get('reviews')) else 0,
            'fecha': fecha
        }
    
    def prepare_price(self, row, codigo_interno, fecha, retailer, file_date):
        """Preparar datos del precio"""
        precio_normal = None
        precio_oferta = None
        precio_tarjeta = None
        
        # Usar campos numéricos
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
        
        # Al menos un precio válido
        if precio_normal or precio_oferta or precio_tarjeta:
            precios = [p for p in [precio_normal, precio_oferta, precio_tarjeta] if p]
            precio_min = min(precios) if precios else None
            
            return {
                'codigo_interno': codigo_interno,
                'fecha': fecha,
                'retailer': retailer,
                'precio_normal': precio_normal,
                'precio_oferta': precio_oferta,
                'precio_tarjeta': precio_tarjeta,
                'precio_min_dia': precio_min,
                'timestamp_creacion': file_date
            }
        return None
    
    def insert_batch(self, products, prices):
        """Insertar batch de productos y precios"""
        if products:
            for product in products:
                try:
                    self.cursor.execute("""
                        INSERT INTO master_productos (
                            codigo_interno, sku, link, nombre, marca, retailer,
                            categoria, storage, ram, color, rating, reviews_count,
                            fecha_primera_captura, fecha_ultima_actualizacion,
                            ultimo_visto, activo
                        ) VALUES (
                            %(codigo_interno)s, %(sku)s, %(link)s, %(nombre)s, 
                            %(marca)s, %(retailer)s, %(categoria)s, %(storage)s,
                            %(ram)s, %(color)s, %(rating)s, %(reviews_count)s,
                            %(fecha)s, %(fecha)s, %(fecha)s, TRUE
                        )
                        ON CONFLICT (codigo_interno) DO UPDATE SET
                            ultimo_visto = EXCLUDED.ultimo_visto,
                            fecha_ultima_actualizacion = EXCLUDED.fecha_ultima_actualizacion
                    """, product)
                    self.stats['products_loaded'] += 1
                except Exception as e:
                    self.conn.rollback()
                    continue
        
        if prices:
            # Deduplicar precios por (codigo, fecha)
            unique_prices = {}
            for price in prices:
                if isinstance(price, dict):
                    key = (price['codigo_interno'], price['fecha'])
                    unique_prices[key] = price
            
            for price in unique_prices.values():
                try:
                    self.cursor.execute("""
                        INSERT INTO master_precios (
                            codigo_interno, fecha, retailer, precio_normal,
                            precio_oferta, precio_tarjeta, precio_min_dia,
                            timestamp_creacion
                        ) VALUES (
                            %(codigo_interno)s, %(fecha)s, %(retailer)s,
                            %(precio_normal)s, %(precio_oferta)s, %(precio_tarjeta)s,
                            %(precio_min_dia)s, %(timestamp_creacion)s
                        )
                        ON CONFLICT (codigo_interno, fecha) DO NOTHING
                    """, price)
                    self.stats['prices_loaded'] += 1
                except Exception as e:
                    self.conn.rollback()
                    continue
        
        # Commit cada batch
        self.conn.commit()
    
    def load_all_files(self, directory: str = "data/excel"):
        """Cargar todos los archivos en orden cronológico"""
        print("="*70)
        print("CARGA CON GENERACION ROBUSTA DE SKU")
        print("="*70)
        
        excel_files = self.find_excel_files(directory)
        
        if not excel_files:
            print("[AVISO] No se encontraron archivos Excel")
            return
        
        print(f"\nArchivos encontrados: {len(excel_files)}")
        print(f"Rango: {excel_files[0][1].date()} a {excel_files[-1][1].date()}")
        
        # Agrupar por día
        files_by_day = defaultdict(list)
        for filepath, file_date in excel_files:
            day_key = file_date.date()
            files_by_day[day_key].append((filepath, file_date))
        
        print(f"Días únicos: {len(files_by_day)}")
        
        print("\nProcesando archivos...")
        start_time = datetime.now()
        
        for day in sorted(files_by_day.keys()):
            day_files = files_by_day[day]
            print(f"\n{day}: {len(day_files)} archivos", end='', flush=True)
            
            for filepath, file_date in day_files:
                filename = os.path.basename(filepath)
                retailer = filename.split('_')[0].lower()
                self.process_excel_file(filepath, file_date, retailer)
                
                # Progreso
                if self.stats['files_processed'] % 50 == 0:
                    print(".", end='', flush=True)
            
            print(f" [OK]")
        
        # Tiempo total
        total_time = (datetime.now() - start_time).total_seconds()
        self.show_summary(total_time)
    
    def show_summary(self, total_time):
        """Mostrar resumen de la carga"""
        print("\n" + "="*70)
        print("RESUMEN DE CARGA")
        print("="*70)
        
        print(f"\n[RENDIMIENTO]")
        print(f"  Tiempo total: {total_time:.1f} segundos")
        if total_time > 0:
            print(f"  Velocidad: {self.stats['files_processed']/total_time:.1f} archivos/seg")
        
        print(f"\n[ESTADISTICAS]")
        print(f"  Archivos procesados: {self.stats['files_processed']}")
        print(f"  Productos cargados: {self.stats['products_loaded']:,}")
        print(f"  Precios cargados: {self.stats['prices_loaded']:,}")
        
        if self.stats['errors']:
            print(f"\n[ERRORES] {len(self.stats['errors'])} errores:")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
        
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
        
        # Por retailer
        self.cursor.execute("""
            SELECT retailer, COUNT(*)
            FROM master_productos
            GROUP BY retailer
            ORDER BY COUNT(*) DESC
        """)
        print(f"\n[PRODUCTOS POR RETAILER]")
        for retailer, count in self.cursor.fetchall():
            print(f"  {retailer}: {count:,}")
    
    def close(self):
        """Cerrar conexiones"""
        self.cursor.close()
        self.conn.close()

def main():
    """Función principal"""
    print("INICIANDO CARGA CON SKU ROBUSTO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Truncar tablas primero
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
    
    # Cargar con SKU robusto
    loader = RobustExcelLoader()
    
    try:
        loader.load_all_files()
    finally:
        loader.close()
    
    print("\n[COMPLETADO] Carga finalizada")

if __name__ == "__main__":
    main()