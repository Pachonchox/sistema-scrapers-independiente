#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Carga de archivos Excel con fechas del nombre del archivo
=========================================================

Este script:
1. Busca todos los archivos Excel en data/excel/
2. Extrae la fecha del nombre del archivo (formato: retailer_YYYY_MM_DD_HHMMSS.xlsx)
3. Los ordena cronológicamente (más antiguos primero)
4. Los carga usando la fecha del archivo, no la fecha del sistema
5. Aplica el constraint de 1 precio por producto por día
"""

import sys
import os
import re
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict
from dotenv import load_dotenv

load_dotenv()

class ExcelLoaderWithFileDate:
    def __init__(self):
        """Inicializar cargador con conexión a PostgreSQL"""
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025')
        )
        self.cursor = self.conn.cursor()
        self.stats = {
            'files_processed': 0,
            'products_loaded': 0,
            'prices_loaded': 0,
            'duplicates_skipped': 0,
            'errors': []
        }
        
    def extract_date_from_filename(self, filename: str) -> datetime:
        """
        Extrae fecha del nombre del archivo
        Formato esperado: retailer_YYYY_MM_DD_HHMMSS.xlsx
        """
        # Patrón para extraer fecha
        pattern = r'(\w+)_(\d{4})_(\d{2})_(\d{2})_(\d{6})\.xlsx'
        match = re.match(pattern, filename)
        
        if match:
            retailer, year, month, day, time_str = match.groups()
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            
            return datetime(int(year), int(month), int(day), hour, minute, second)
        
        # Si no coincide con el formato, usar fecha actual como fallback
        print(f"[AVISO] No se pudo extraer fecha de {filename}, usando fecha actual")
        return datetime.now()
    
    def find_excel_files(self, directory: str = "data/excel") -> List[Tuple[str, datetime]]:
        """
        Buscar todos los archivos Excel y ordenarlos por fecha
        Retorna lista de tuplas (filepath, fecha)
        """
        excel_files = []
        
        if not os.path.exists(directory):
            print(f"[ERROR] Directorio {directory} no existe")
            return []
        
        # Buscar todos los archivos .xlsx
        for file in os.listdir(directory):
            if file.endswith('.xlsx'):
                filepath = os.path.join(directory, file)
                file_date = self.extract_date_from_filename(file)
                excel_files.append((filepath, file_date))
        
        # Ordenar por fecha (más antiguos primero)
        excel_files.sort(key=lambda x: x[1])
        
        return excel_files
    
    def generate_product_code(self, row: dict, retailer: str) -> str:
        """
        Generar código interno único para el producto
        Formato: CL-MARCA-MODELO-SPEC-RET-SEQ
        """
        # Normalizar marca (4 letras)
        marca = str(row.get('marca', 'UNKN'))[:4].upper().replace(' ', '')
        if not marca:
            marca = 'UNKN'
        
        # Extraer modelo del nombre
        nombre = str(row.get('nombre', ''))
        modelo = 'UNKN'
        
        # Intentar extraer modelo
        palabras = nombre.split()
        for palabra in palabras:
            if len(palabra) > 3 and palabra[0].isupper():
                modelo = palabra[:10].upper()
                break
        
        # Extraer especificación (storage, ram, etc)
        spec = 'NA'
        if 'storage' in row:
            spec = str(row['storage']).replace('GB', '').replace(' ', '')
        elif '128GB' in nombre:
            spec = '128GB'
        elif '256GB' in nombre:
            spec = '256GB'
        elif '512GB' in nombre:
            spec = '512GB'
        elif '1TB' in nombre:
            spec = '1TB'
        
        # Código de retailer (3 letras)
        ret_codes = {
            'ripley': 'RIP',
            'falabella': 'FAL',
            'paris': 'PAR',
            'mercadolibre': 'MLC',
            'hites': 'HIT',
            'abcdin': 'ABC'
        }
        ret_code = ret_codes.get(retailer.lower(), 'UNK')
        
        # Generar secuencia única basada en SKU o link
        seq = str(abs(hash(row.get('sku', row.get('link', '')))))[:3]
        
        return f"CL-{marca}-{modelo}-{spec}-{ret_code}-{seq}"
    
    def load_product(self, row: dict, retailer: str, file_date: datetime) -> str:
        """
        Cargar o actualizar producto en master_productos
        Retorna codigo_interno
        """
        # Generar código interno
        codigo_interno = self.generate_product_code(row, retailer)
        
        # Verificar si producto existe
        self.cursor.execute(
            "SELECT codigo_interno FROM master_productos WHERE codigo_interno = %s",
            (codigo_interno,)
        )
        
        if self.cursor.fetchone():
            # Actualizar producto existente
            self.cursor.execute("""
                UPDATE master_productos
                SET fecha_ultima_actualizacion = %s,
                    ultimo_visto = %s,
                    veces_visto = veces_visto + 1,
                    activo = TRUE
                WHERE codigo_interno = %s
            """, (file_date.date(), file_date.date(), codigo_interno))
        else:
            # Insertar nuevo producto
            self.cursor.execute("""
                INSERT INTO master_productos (
                    codigo_interno, sku, link, nombre, marca, categoria, retailer,
                    storage, ram, color, rating, reviews_count,
                    out_of_stock, fecha_primera_captura, fecha_ultima_actualizacion,
                    ultimo_visto, activo, veces_visto
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                codigo_interno,
                row.get('sku', ''),
                row.get('link', ''),
                row.get('nombre', ''),
                row.get('marca', ''),
                row.get('categoria', 'smartphones'),
                retailer,
                row.get('storage', ''),
                row.get('ram', ''),
                row.get('color', ''),
                row.get('rating'),
                row.get('reviews_count', 0),
                row.get('out_of_stock', False),
                file_date.date(),
                file_date.date(),
                file_date.date(),
                True,
                1
            ))
            self.stats['products_loaded'] += 1
        
        return codigo_interno
    
    def load_price(self, row: dict, codigo_interno: str, retailer: str, file_date: datetime) -> bool:
        """
        Cargar precio con fecha del archivo
        Respeta el constraint de 1 precio por producto por día
        """
        fecha = file_date.date()
        
        # Verificar si ya existe precio para este producto en esta fecha
        self.cursor.execute("""
            SELECT id FROM master_precios
            WHERE codigo_interno = %s AND fecha = %s
        """, (codigo_interno, fecha))
        
        if self.cursor.fetchone():
            self.stats['duplicates_skipped'] += 1
            return False
        
        # Convertir precios a centavos (bigint)
        precio_normal = None
        precio_oferta = None
        precio_tarjeta = None
        
        if row.get('precio_normal'):
            precio_normal = int(float(row['precio_normal']) * 100)
        if row.get('precio_oferta'):
            precio_oferta = int(float(row['precio_oferta']) * 100)
        if row.get('precio_tarjeta'):
            precio_tarjeta = int(float(row['precio_tarjeta']) * 100)
        
        # Calcular precio mínimo del día
        precios = [p for p in [precio_normal, precio_oferta, precio_tarjeta] if p is not None]
        precio_min_dia = min(precios) if precios else None
        
        # Insertar nuevo precio
        self.cursor.execute("""
            INSERT INTO master_precios (
                codigo_interno, fecha, retailer,
                precio_normal, precio_oferta, precio_tarjeta, precio_min_dia,
                timestamp_creacion, timestamp_ultima_actualizacion,
                cambios_en_dia, precio_anterior_dia, cambio_porcentaje, cambio_absoluto
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s
            )
        """, (
            codigo_interno, fecha, retailer,
            precio_normal, precio_oferta, precio_tarjeta, precio_min_dia,
            file_date, file_date,  # Usar timestamp del archivo
            1, 0, 0.0, 0  # Valores por defecto para primer registro del día
        ))
        
        self.stats['prices_loaded'] += 1
        return True
    
    def process_excel_file(self, filepath: str, file_date: datetime):
        """
        Procesar un archivo Excel completo
        """
        print(f"\n[PROCESANDO] {os.path.basename(filepath)}")
        print(f"  Fecha del archivo: {file_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Extraer retailer del nombre del archivo
        filename = os.path.basename(filepath)
        retailer = filename.split('_')[0].lower()
        
        try:
            # Leer Excel
            df = pd.read_excel(filepath)
            print(f"  Productos en archivo: {len(df)}")
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Cargar producto
                    codigo_interno = self.load_product(row, retailer, file_date)
                    
                    # Cargar precio
                    self.load_price(row, codigo_interno, retailer, file_date)
                    
                    # Commit cada 100 registros
                    if (index + 1) % 100 == 0:
                        self.conn.commit()
                        print(f"    Procesados: {index + 1}/{len(df)}")
                        
                except Exception as e:
                    self.stats['errors'].append(f"Error en fila {index}: {str(e)}")
                    self.conn.rollback()
            
            # Commit final
            self.conn.commit()
            self.stats['files_processed'] += 1
            print(f"  [OK] Archivo procesado completamente")
            
        except Exception as e:
            print(f"  [ERROR] Error procesando archivo: {e}")
            self.stats['errors'].append(f"Error en {filename}: {str(e)}")
            self.conn.rollback()
    
    def load_all_files(self, directory: str = "data/excel"):
        """
        Cargar todos los archivos Excel en orden cronológico
        """
        print("="*70)
        print("CARGA CRONOLOGICA DE ARCHIVOS EXCEL")
        print("="*70)
        
        # Buscar y ordenar archivos
        excel_files = self.find_excel_files(directory)
        
        if not excel_files:
            print("[AVISO] No se encontraron archivos Excel para cargar")
            return
        
        print(f"\nArchivos encontrados: {len(excel_files)}")
        print("\nOrden de carga (más antiguos primero):")
        for filepath, file_date in excel_files:
            print(f"  - {os.path.basename(filepath)}: {file_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*70)
        print("INICIANDO CARGA")
        print("="*70)
        
        # Procesar cada archivo en orden cronológico
        for filepath, file_date in excel_files:
            self.process_excel_file(filepath, file_date)
        
        # Mostrar resumen
        self.show_summary()
    
    def show_summary(self):
        """
        Mostrar resumen de la carga
        """
        print("\n" + "="*70)
        print("RESUMEN DE CARGA")
        print("="*70)
        
        print(f"\n[ESTADISTICAS]")
        print(f"  Archivos procesados: {self.stats['files_processed']}")
        print(f"  Productos cargados: {self.stats['products_loaded']}")
        print(f"  Precios cargados: {self.stats['prices_loaded']}")
        print(f"  Duplicados omitidos: {self.stats['duplicates_skipped']}")
        
        if self.stats['errors']:
            print(f"\n[ERRORES] Se encontraron {len(self.stats['errors'])} errores:")
            for error in self.stats['errors'][:5]:  # Mostrar máximo 5 errores
                print(f"  - {error}")
        
        # Verificación final en base de datos
        self.cursor.execute("""
            SELECT 
                COUNT(DISTINCT codigo_interno) as productos,
                COUNT(*) as precios,
                COUNT(DISTINCT fecha) as dias,
                MIN(fecha) as fecha_inicio,
                MAX(fecha) as fecha_fin
            FROM master_precios
        """)
        
        stats = self.cursor.fetchone()
        if stats:
            productos, precios, dias, fecha_inicio, fecha_fin = stats
            print(f"\n[BASE DE DATOS]")
            print(f"  Total productos únicos: {productos}")
            print(f"  Total registros de precios: {precios}")
            print(f"  Días con datos: {dias}")
            if fecha_inicio and fecha_fin:
                print(f"  Rango de fechas: {fecha_inicio} a {fecha_fin}")
        
        # Verificar constraint de 1 precio por producto por día
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT codigo_interno, fecha, COUNT(*) as cnt
                FROM master_precios
                GROUP BY codigo_interno, fecha
                HAVING COUNT(*) > 1
            ) as duplicados
        """)
        
        duplicados = self.cursor.fetchone()[0]
        if duplicados > 0:
            print(f"\n[AVISO] Hay {duplicados} casos de múltiples precios por día (violación de constraint)")
        else:
            print(f"\n[OK] Constraint cumplido: 1 precio por producto por día")
    
    def close(self):
        """Cerrar conexiones"""
        self.cursor.close()
        self.conn.close()

def main():
    """Función principal"""
    print("SISTEMA DE CARGA CRONOLOGICA DE EXCEL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    loader = ExcelLoaderWithFileDate()
    
    try:
        # Cargar todos los archivos en orden cronológico
        loader.load_all_files()
    finally:
        loader.close()
    
    print("\n[COMPLETADO] Carga finalizada")

if __name__ == "__main__":
    main()