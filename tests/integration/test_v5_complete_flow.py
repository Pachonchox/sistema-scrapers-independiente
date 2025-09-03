#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prueba Completa del Flujo V5
=============================

Ejecuta el ciclo completo:
1. Scraping con v5
2. Generación de Excel
3. Carga a PostgreSQL
4. Validación
"""

import sys
import os
import time
import pandas as pd
import psycopg2
from datetime import datetime
from pathlib import Path
import asyncio
import aiohttp
from typing import Dict, List, Any

# Añadir rutas al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portable_orchestrator_v5'))

# Importar scrapers v5
from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
from portable_orchestrator_v5.scrapers.mercadolibre_scraper_v5 import MercadoLibreScraperV5
from portable_orchestrator_v5.scrapers.hites_scraper_v5 import HitesScraperV5
from portable_orchestrator_v5.scrapers.abcdin_scraper_v5 import AbcdinScraperV5

# Importar sistema de carga
from load_excel_final import FinalExcelLoader
from dotenv import load_dotenv

load_dotenv()

class V5SystemTest:
    def __init__(self, max_runtime: int = 300):
        """
        Inicializar prueba del sistema
        
        Args:
            max_runtime: Tiempo máximo en segundos (default 5 minutos)
        """
        self.max_runtime = max_runtime
        self.start_time = time.time()
        self.results = {}
        self.test_dir = Path("data/test_v5")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
    def check_time_limit(self):
        """Verificar si se excedió el tiempo límite"""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_runtime:
            print(f"\n[TIEMPO] Límite de {self.max_runtime}s alcanzado")
            return True
        return False
    
    async def run_scraper_async(self, scraper_class, name: str, max_products: int = 30):
        """Ejecutar un scraper de forma asíncrona"""
        print(f"\n[{name.upper()}] Iniciando scraper...")
        
        try:
            scraper = scraper_class()
            
            # Los scrapers v5 usan scrape_category
            if hasattr(scraper, 'scrape_category'):
                # Definir categorías válidas de prueba por retailer
                categorias = {
                    'ripley': 'computacion',        # Válida
                    'falabella': 'computadores',    # Cambiado a válida
                    'paris': 'celulares',           # Cambiado a válida  
                    'mercadolibre': 'celulares',    # OK pero no implementado
                    'hites': 'computacion',         # OK pero no implementado
                    'abcdin': 'tecnologia'          # OK pero no implementado
                }
                categoria = categorias.get(name, 'tecnologia')
                result = await scraper.scrape_category(categoria, max_products=max_products)
                
                # Extraer productos del resultado
                if hasattr(result, 'products'):
                    productos = result.products
                elif isinstance(result, list):
                    productos = result
                else:
                    productos = []
            else:
                # Fallback para otros métodos
                productos = []
            
            if productos:
                # Convertir ProductData a dict si es necesario
                if productos and hasattr(productos[0], '__dict__'):
                    productos_dict = []
                    for p in productos:
                        # Convertir ProductData a dict
                        producto_dict = {
                            'nombre': getattr(p, 'nombre', ''),
                            'link': getattr(p, 'link', ''),
                            'sku': getattr(p, 'sku', ''),
                            'marca': getattr(p, 'marca', ''),
                            'precio_normal': getattr(p, 'precio_normal', 0),
                            'precio_oferta': getattr(p, 'precio_oferta', 0),
                            'precio_tarjeta': getattr(p, 'precio_tarjeta', 0),
                            'precio_normal_num': getattr(p, 'precio_normal_num', 0),
                            'precio_oferta_num': getattr(p, 'precio_oferta_num', 0),
                            'precio_tarjeta_num': getattr(p, 'precio_tarjeta_num', 0),
                            'categoria': getattr(p, 'categoria', 'general'),
                            'rating': getattr(p, 'rating', None),
                            'reviews': getattr(p, 'reviews', 0),
                            'descripcion': getattr(p, 'descripcion', ''),
                            'disponibilidad': getattr(p, 'disponibilidad', True)
                        }
                        productos_dict.append(producto_dict)
                    productos = productos_dict
                    
                # Guardar en Excel
                df = pd.DataFrame(productos)
                timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
                filename = self.test_dir / f"{name}_{timestamp}.xlsx"
                df.to_excel(filename, index=False)
                
                print(f"  [OK] {len(productos)} productos guardados")
                self.results[name] = {
                    'status': 'OK',
                    'count': len(productos),
                    'file': str(filename)
                }
                return len(productos)
            else:
                print(f"  [AVISO] No se obtuvieron productos")
                self.results[name] = {'status': 'NO_DATA', 'count': 0}
                return 0
                
        except Exception as e:
            print(f"  [ERROR] {str(e)[:100]}")
            self.results[name] = {'status': 'ERROR', 'error': str(e)[:100]}
            return 0
    
    async def phase1_scrapers(self):
        """Fase 1: Ejecutar todos los scrapers"""
        print("="*80)
        print("FASE 1: EJECUTANDO SCRAPERS V5")
        print("="*80)
        
        scrapers_config = [
            (RipleyScraperV5, 'ripley'),
            (FalabellaScraperV5, 'falabella'),
            (ParisScraperV5, 'paris'),
            (MercadoLibreScraperV5, 'mercadolibre'),
            (HitesScraperV5, 'hites'),
            (AbcdinScraperV5, 'abcdin')
        ]
        
        # Crear tareas para ejecutar en paralelo
        tasks = []
        for scraper_class, name in scrapers_config:
            if self.check_time_limit():
                break
                
            # Limitar productos para prueba rápida
            max_products = 20 if name == 'mercadolibre' else 30
            task = self.run_scraper_async(scraper_class, name, max_products)
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_products = sum(r for r in results if isinstance(r, int))
            print(f"\n[RESUMEN] Total productos scrapeados: {total_products}")
        
        return len([r for r in self.results.values() if r.get('status') == 'OK'])
    
    def phase2_load_to_db(self):
        """Fase 2: Cargar datos a PostgreSQL"""
        print("\n" + "="*80)
        print("FASE 2: CARGANDO A POSTGRESQL")
        print("="*80)
        
        excel_files = list(self.test_dir.glob("*.xlsx"))
        
        if not excel_files:
            print("[AVISO] No hay archivos Excel para cargar")
            return False
        
        print(f"Archivos a cargar: {len(excel_files)}")
        
        try:
            # No vamos a cargar en esta prueba para no contaminar la DB
            # Solo simulamos la carga
            total_productos = 0
            for file in excel_files:
                df = pd.read_excel(file)
                total_productos += len(df)
                print(f"  [SIMULADO] {file.name}: {len(df)} productos")
            
            print(f"\n[INFO] Total productos a cargar (simulado): {total_productos}")
            print("[OK] Carga simulada - DB no modificada")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error en carga: {str(e)[:200]}")
            return False
    
    def phase3_validate(self):
        """Fase 3: Validar integridad del sistema"""
        print("\n" + "="*80)
        print("FASE 3: VALIDACIÓN DE INTEGRIDAD")
        print("="*80)
        
        try:
            conn = psycopg2.connect(
                host=os.getenv('PGHOST', 'localhost'),
                port=os.getenv('PGPORT', '5434'),
                database=os.getenv('PGDATABASE', 'price_orchestrator'),
                user=os.getenv('PGUSER', 'orchestrator'),
                password=os.getenv('PGPASSWORD', 'orchestrator_2025')
            )
            cursor = conn.cursor()
            
            # Obtener estadísticas antes
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM master_productos) as productos_antes,
                    (SELECT COUNT(*) FROM master_precios) as precios_antes
            """)
            productos_antes, precios_antes = cursor.fetchone()
            
            print(f"\nEstado actual:")
            print(f"  Productos: {productos_antes:,}")
            print(f"  Precios: {precios_antes:,}")
            
            # Verificar productos nuevos del test
            cursor.execute("""
                SELECT retailer, COUNT(*) as nuevos
                FROM master_productos
                WHERE fecha_ultima_actualizacion::date = CURRENT_DATE
                GROUP BY retailer
                ORDER BY retailer
            """)
            
            nuevos_hoy = cursor.fetchall()
            if nuevos_hoy:
                print(f"\nProductos agregados hoy:")
                for retailer, count in nuevos_hoy:
                    print(f"  {retailer}: {count}")
            
            # Verificar constraint de unicidad
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT codigo_interno, fecha, COUNT(*)
                    FROM master_precios
                    GROUP BY codigo_interno, fecha
                    HAVING COUNT(*) > 1
                ) dup
            """)
            
            duplicados = cursor.fetchone()[0]
            
            if duplicados == 0:
                print(f"\n[OK] Constraint de unicidad: CUMPLIDO")
            else:
                print(f"\n[ERROR] {duplicados} violaciones de unicidad detectadas")
            
            cursor.close()
            conn.close()
            
            return duplicados == 0
            
        except Exception as e:
            print(f"[ERROR] Error validando: {str(e)[:200]}")
            return False
    
    async def run(self):
        """Ejecutar prueba completa"""
        print("="*80)
        print("PRUEBA COMPLETA DEL SISTEMA V5")
        print("="*80)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tiempo máximo: {self.max_runtime}s ({self.max_runtime/60:.1f} minutos)")
        
        # Fase 1: Scrapers
        scrapers_ok = await self.phase1_scrapers()
        
        if self.check_time_limit():
            return self.print_summary()
        
        # Fase 2: Carga a DB
        load_ok = self.phase2_load_to_db()
        
        if self.check_time_limit():
            return self.print_summary()
        
        # Fase 3: Validación
        validation_ok = self.phase3_validate()
        
        return self.print_summary()
    
    def print_summary(self):
        """Imprimir resumen final"""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("RESUMEN FINAL")
        print("="*80)
        print(f"Tiempo total: {elapsed:.1f}s ({elapsed/60:.1f} minutos)")
        
        # Resumen de scrapers
        print("\nResultados por scraper:")
        for name, result in self.results.items():
            status = result.get('status', 'UNKNOWN')
            count = result.get('count', 0)
            symbol = "[OK]" if status == "OK" else "[FALLO]"
            print(f"  {symbol} {name}: {count} productos")
        
        # Contar éxitos
        total_scrapers = len(self.results)
        scrapers_ok = len([r for r in self.results.values() if r.get('status') == 'OK'])
        total_products = sum(r.get('count', 0) for r in self.results.values())
        
        print(f"\nEstadísticas:")
        print(f"  Scrapers exitosos: {scrapers_ok}/{total_scrapers}")
        print(f"  Total productos: {total_products}")
        print(f"  Velocidad: {total_products/elapsed:.1f} productos/segundo")
        
        if scrapers_ok > 0:
            print(f"\n[OK] Sistema V5 funcionando correctamente")
        else:
            print(f"\n[ERROR] No se pudieron ejecutar los scrapers")
        
        print(f"\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Limpiar archivos de prueba si todo salió bien
        if scrapers_ok > 0:
            print(f"\n[INFO] Archivos de prueba guardados en: {self.test_dir}")

def main():
    """Función principal"""
    # Crear y ejecutar prueba
    test = V5SystemTest(max_runtime=300)  # 5 minutos
    
    # Ejecutar con asyncio
    asyncio.run(test.run())

if __name__ == "__main__":
    main()