#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Completo V5 con Base de Datos
===================================
Prueba el flujo completo incluyendo guardado en PostgreSQL
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Configurar paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_complete_flow():
    """Test completo con base de datos"""
    
    print("\n" + "="*80)
    print("TEST COMPLETO V5 CON BASE DE DATOS")
    print("="*80)
    print(f"Inicio: {datetime.now()}")
    
    # Paso 1: Verificar configuración
    print("\n=== PASO 1: VERIFICACIÓN DE CONFIGURACIÓN ===")
    
    # Verificar .env
    from dotenv import load_dotenv
    load_dotenv()
    
    db_backend = os.getenv('DATA_BACKEND', 'excel')
    master_enabled = os.getenv('MASTER_SYSTEM_ENABLED', 'false').lower() == 'true'
    
    print(f"DATA_BACKEND: {db_backend}")
    print(f"MASTER_SYSTEM_ENABLED: {master_enabled}")
    
    if db_backend == 'postgres':
        print("[OK] Configurado para PostgreSQL")
        
        # Verificar conexión
        try:
            import psycopg2
            from psycopg2 import sql
            
            conn_params = {
                'host': os.getenv('PGHOST', 'localhost'),
                'port': os.getenv('PGPORT', '5432'),
                'database': os.getenv('PGDATABASE', 'orchestrator'),
                'user': os.getenv('PGUSER', 'postgres'),
                'password': os.getenv('PGPASSWORD', 'postgres')
            }
            
            print(f"\nConectando a PostgreSQL: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
            
            conn = psycopg2.connect(**conn_params)
            cur = conn.cursor()
            
            # Verificar tablas
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('master_productos', 'master_precios', 'productos_raw')
            """)
            
            tables = cur.fetchall()
            print(f"Tablas encontradas: {[t[0] for t in tables]}")
            
            # Contar registros actuales
            for table in ['master_productos', 'master_precios', 'productos_raw']:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"  {table}: {count} registros")
                except:
                    print(f"  {table}: No existe")
            
            conn.close()
            print("[OK] Conexion a PostgreSQL exitosa")
            
        except Exception as e:
            print(f"[ERROR] Error conectando a PostgreSQL: {e}")
            print("Continuando sin base de datos...")
    else:
        print("[WARN] Sistema configurado para Excel, no PostgreSQL")
    
    # Paso 2: Inicializar Master System si está habilitado
    print("\n=== PASO 2: SISTEMA MASTER ===")
    
    master_system = None
    if master_enabled:
        try:
            sys.path.append(str(Path(__file__).parent.parent.parent / 'core'))
            from integrated_master_system import IntegratedMasterSystem
            
            master_system = IntegratedMasterSystem(
                backend_type=db_backend,
                enable_normalization=True
            )
            
            print("[OK] Master System inicializado")
            
        except Exception as e:
            print(f"[ERROR] Error inicializando Master System: {e}")
            master_system = None
    else:
        print("[WARN] Master System no habilitado")
    
    # Paso 3: Ejecutar scrapers V5
    print("\n=== PASO 3: EJECUTAR SCRAPERS V5 ===")
    
    from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
    from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
    from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
    
    scrapers = [
        ('paris', ParisScraperV5(), 'celulares'),
        ('ripley', RipleyScraperV5(), 'computacion'),
        ('falabella', FalabellaScraperV5(), 'smartphones')
    ]
    
    all_products = []
    
    for retailer_name, scraper, category in scrapers:
        print(f"\n--- {retailer_name.upper()} ---")
        
        try:
            # Inicializar
            await scraper.initialize()
            print(f"Scraper inicializado")
            
            # Ejecutar scraping
            result = await scraper.scrape_category(
                category=category,
                max_products=10  # Solo 10 para prueba rápida
            )
            
            if result.success:
                print(f"[OK] {len(result.products)} productos extraidos")
                
                # Preparar productos para guardar
                for product in result.products:
                    product_dict = {
                        'sku': product.sku or f"{retailer_name}_{hash(product.title)}",
                        'nombre': product.title,
                        'marca': product.brand,
                        'precio_normal': product.original_price,
                        'precio_oferta': product.current_price,
                        'precio_tarjeta': product.current_price,
                        'precio_normal_num': int(product.original_price),
                        'precio_oferta_num': int(product.current_price),
                        'precio_tarjeta_num': int(product.current_price),
                        'link': product.product_url,
                        'imagen': product.image_urls[0] if product.image_urls else '',
                        'rating': product.rating,
                        'disponibilidad': product.availability,
                        'retailer': retailer_name,
                        'categoria': category,
                        'fecha_captura': datetime.now()
                    }
                    all_products.append(product_dict)
                    
            else:
                print(f"[ERROR] Error: {result.error_message}")
            
            # Cerrar scraper
            await scraper.cleanup()
            
        except Exception as e:
            print(f"[ERROR] Error con {retailer_name}: {e}")
    
    print(f"\nTotal productos extraídos: {len(all_products)}")
    
    # Paso 4: Guardar en base de datos
    if all_products and master_system:
        print("\n=== PASO 4: GUARDAR EN BASE DE DATOS ===")
        
        try:
            # Procesar con Master System
            for product in all_products:
                try:
                    # El master system maneja la normalización y guardado
                    master_system.process_product(product)
                    print(f"[OK] Guardado: {product['nombre'][:50]}...")
                    
                except Exception as e:
                    print(f"[ERROR] Error guardando producto: {e}")
            
            print(f"\n[OK] Productos procesados por Master System")
            
        except Exception as e:
            print(f"[ERROR] Error procesando productos: {e}")
    
    elif all_products and db_backend == 'postgres':
        print("\n=== PASO 4: GUARDAR DIRECTAMENTE EN POSTGRESQL ===")
        
        try:
            import psycopg2
            from psycopg2.extras import execute_values
            
            conn = psycopg2.connect(**conn_params)
            cur = conn.cursor()
            
            # Insertar en productos_raw
            insert_query = """
                INSERT INTO productos_raw (
                    sku, nombre, marca, precio_normal, precio_oferta, precio_tarjeta,
                    link, imagen, rating, disponibilidad, retailer, categoria,
                    fecha_captura, created_at
                ) VALUES %s
                ON CONFLICT (sku, retailer, fecha_captura) DO NOTHING
            """
            
            values = [
                (
                    p['sku'], p['nombre'], p['marca'], 
                    p['precio_normal'], p['precio_oferta'], p['precio_tarjeta'],
                    p['link'], p['imagen'], p['rating'], p['disponibilidad'],
                    p['retailer'], p['categoria'], p['fecha_captura'], datetime.now()
                )
                for p in all_products
            ]
            
            execute_values(cur, insert_query, values)
            conn.commit()
            
            inserted = cur.rowcount
            print(f"[OK] {inserted} productos insertados en productos_raw")
            
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Error guardando en PostgreSQL: {e}")
    
    else:
        print("\n[WARN] No se guardaron productos (sin BD configurada)")
    
    # Paso 5: Verificar datos guardados
    if db_backend == 'postgres':
        print("\n=== PASO 5: VERIFICAR DATOS GUARDADOS ===")
        
        try:
            conn = psycopg2.connect(**conn_params)
            cur = conn.cursor()
            
            # Verificar productos_raw
            cur.execute("""
                SELECT retailer, COUNT(*) as total, 
                       MIN(precio_oferta) as min_precio,
                       MAX(precio_oferta) as max_precio,
                       AVG(precio_oferta) as avg_precio
                FROM productos_raw
                WHERE DATE(fecha_captura) = CURRENT_DATE
                GROUP BY retailer
            """)
            
            results = cur.fetchall()
            
            if results:
                print("\nProductos guardados hoy:")
                for retailer, total, min_p, max_p, avg_p in results:
                    print(f"  {retailer}: {total} productos")
                    print(f"    Precio min: ${min_p:,.0f}")
                    print(f"    Precio max: ${max_p:,.0f}")
                    print(f"    Precio avg: ${avg_p:,.0f}")
            else:
                print("No hay productos guardados hoy")
            
            # Verificar master_productos si existe
            try:
                cur.execute("""
                    SELECT COUNT(*) FROM master_productos
                    WHERE created_at >= CURRENT_DATE
                """)
                count = cur.fetchone()[0]
                print(f"\nMaster productos creados hoy: {count}")
            except:
                pass
            
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Error verificando datos: {e}")
    
    print("\n" + "="*80)
    print("TEST COMPLETADO")
    print(f"Fin: {datetime.now()}")
    print("="*80)
    
    return len(all_products)

if __name__ == "__main__":
    print("Iniciando test completo con base de datos...")
    
    try:
        products = asyncio.run(test_complete_flow())
        
        if products > 0:
            print(f"\n[EXITOSO] TEST EXITOSO - {products} productos procesados")
        else:
            print("\n[WARN] TEST SIN PRODUCTOS")
            
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()