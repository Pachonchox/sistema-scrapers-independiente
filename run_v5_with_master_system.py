#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema V5 con Master System Completo
======================================
Ejecuta los scrapers V5 con el flujo completo del Master System
siguiendo exactamente el flujo del README principal.

Este script:
1. Inicializa el Master System con PostgreSQL
2. Ejecuta los scrapers V5 (Paris, Ripley, Falabella)
3. Procesa productos con códigos internos únicos
4. Guarda en PostgreSQL con snapshots de precios
5. Detecta oportunidades de arbitraje
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Configurar paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# FORZAR SOPORTE COMPLETO DE EMOJIS
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'v5_master_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Configurar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Forzar configuración para PostgreSQL
os.environ['DATA_BACKEND'] = 'postgres'
os.environ['MASTER_SYSTEM_ENABLED'] = 'true'
os.environ['NORMALIZATION_ENABLED'] = 'true'
os.environ['COMPARISON_ENABLED'] = 'true'
os.environ['ARBITRAGE_ENABLED'] = 'true'

async def run_v5_with_master_system():
    """Ejecutar scrapers V5 con Master System completo"""
    
    print("\n" + "="*80)
    print("SISTEMA V5 CON MASTER SYSTEM COMPLETO")
    print("="*80)
    print(f"Inicio: {datetime.now()}")
    print("-"*80)
    
    # Paso 1: Inicializar Master System
    print("\n=== PASO 1: INICIALIZAR MASTER SYSTEM ===")
    
    master_system = None
    try:
        from core.integrated_master_system import IntegratedMasterSystem
        
        master_system = IntegratedMasterSystem(
            backend_type='postgres',
            enable_normalization=True
        )
        
        print("[OK] Master System inicializado con PostgreSQL")
        print(f"  Backend: {master_system.backend_type}")
        print(f"  Normalizacion: {master_system.normalization_enabled}")
        
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar Master System: {e}")
        print("Continuando sin Master System...")
    
    # Paso 2: Verificar conexión PostgreSQL
    print("\n=== PASO 2: VERIFICAR POSTGRESQL ===")
    
    try:
        import psycopg2
        
        conn_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'orchestrator'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', 'postgres')
        }
        
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Verificar tablas principales
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('master_productos', 'master_precios')
        """)
        
        tables = cur.fetchall()
        print(f"[OK] Tablas encontradas: {[t[0] for t in tables]}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] PostgreSQL: {e}")
    
    # Paso 3: Inicializar scrapers V5
    print("\n=== PASO 3: INICIALIZAR SCRAPERS V5 ===")
    
    from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
    from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
    from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
    
    scrapers = {
        'paris': ParisScraperV5(),
        'ripley': RipleyScraperV5(),
        'falabella': FalabellaScraperV5()
    }
    
    # Categorías a scrapear
    categories = {
        'paris': ['celulares', 'computadores'],
        'ripley': ['computacion', 'smartphones'],
        'falabella': ['smartphones', 'computadores']
    }
    
    # Inicializar todos los scrapers
    for retailer, scraper in scrapers.items():
        try:
            print(f"\nInicializando {retailer.upper()}...")
            await scraper.initialize()
            print(f"[OK] {retailer.upper()} inicializado")
        except Exception as e:
            print(f"[ERROR] {retailer}: {e}")
    
    # Paso 4: Ejecutar scraping
    print("\n=== PASO 4: EJECUTAR SCRAPING ===")
    
    all_products = []
    stats = {
        'total': 0,
        'by_retailer': {}
    }
    
    for retailer, scraper in scrapers.items():
        retailer_categories = categories[retailer]
        
        for category in retailer_categories:
            print(f"\n--- {retailer.upper()} - {category} ---")
            
            try:
                result = await scraper.scrape_category(
                    category=category,
                    max_products=30  # 30 productos por categoría
                )
                
                if result.success:
                    count = len(result.products)
                    stats['total'] += count
                    
                    if retailer not in stats['by_retailer']:
                        stats['by_retailer'][retailer] = 0
                    stats['by_retailer'][retailer] += count
                    
                    print(f"[OK] {count} productos extraidos")
                    
                    # Convertir a formato para Master System
                    for product in result.products:
                        product_dict = {
                            # Identificación
                            'sku': product.sku or f"{retailer}_{hash(product.title)}",
                            'nombre': product.title,
                            'marca': product.brand,
                            'retailer': retailer,
                            'categoria': category,
                            
                            # Precios
                            'precio_normal': int(product.original_price),
                            'precio_oferta': int(product.current_price),
                            'precio_tarjeta': int(product.current_price),
                            
                            # URLs
                            'link': product.product_url,
                            'imagen': product.image_urls[0] if product.image_urls else '',
                            
                            # Métricas
                            'rating': product.rating,
                            'disponibilidad': product.availability,
                            
                            # Metadata
                            'fecha_captura': datetime.now(),
                            'extraction_timestamp': product.extraction_timestamp,
                            
                            # Especificaciones adicionales
                            'storage': product.additional_info.get('storage', '') if product.additional_info else '',
                            'ram': product.additional_info.get('ram', '') if product.additional_info else '',
                            'color': product.additional_info.get('color', '') if product.additional_info else '',
                        }
                        
                        all_products.append(product_dict)
                        
                else:
                    print(f"[ERROR] {result.error_message}")
                    
            except Exception as e:
                print(f"[ERROR] {retailer}-{category}: {e}")
    
    print(f"\n=== TOTAL PRODUCTOS EXTRAIDOS: {stats['total']} ===")
    for retailer, count in stats['by_retailer'].items():
        print(f"  {retailer.upper()}: {count}")
    
    # Paso 5: Procesar con Master System
    if all_products and master_system:
        print("\n=== PASO 5: PROCESAR CON MASTER SYSTEM ===")
        
        processed = 0
        errors = 0
        
        for product in all_products:
            try:
                # El Master System se encarga de:
                # 1. Normalizar el producto
                # 2. Generar código interno único
                # 3. Guardar en master_productos
                # 4. Crear snapshot de precios en master_precios
                # 5. Detectar oportunidades de arbitraje
                
                master_system.process_product(product)
                processed += 1
                
                if processed % 10 == 0:
                    print(f"  Procesados: {processed}/{len(all_products)}")
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error procesando producto: {e}")
        
        print(f"\n[OK] Productos procesados: {processed}")
        if errors > 0:
            print(f"[WARN] Errores: {errors}")
    
    # Paso 6: Verificar datos guardados
    print("\n=== PASO 6: VERIFICAR DATOS GUARDADOS ===")
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Verificar master_productos
        cur.execute("""
            SELECT retailer, COUNT(*) as total
            FROM master_productos
            WHERE created_at >= CURRENT_DATE
            GROUP BY retailer
        """)
        
        results = cur.fetchall()
        if results:
            print("\nProductos en master_productos (hoy):")
            for retailer, total in results:
                print(f"  {retailer}: {total}")
        
        # Verificar master_precios
        cur.execute("""
            SELECT COUNT(*) as total,
                   MIN(precio_oferta) as min_precio,
                   MAX(precio_oferta) as max_precio,
                   AVG(precio_oferta) as avg_precio
            FROM master_precios
            WHERE fecha = CURRENT_DATE
        """)
        
        result = cur.fetchone()
        if result and result[0] > 0:
            total, min_p, max_p, avg_p = result
            print(f"\nPrecios en master_precios (hoy):")
            print(f"  Total snapshots: {total}")
            print(f"  Precio minimo: ${min_p:,.0f}")
            print(f"  Precio maximo: ${max_p:,.0f}")
            print(f"  Precio promedio: ${avg_p:,.0f}")
        
        # Verificar oportunidades de arbitraje
        cur.execute("""
            SELECT COUNT(*) FROM arbitrage_opportunities
            WHERE detected_at >= CURRENT_DATE
        """)
        
        opportunities = cur.fetchone()[0]
        if opportunities > 0:
            print(f"\n[OK] Oportunidades de arbitraje detectadas: {opportunities}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Verificando datos: {e}")
    
    # Paso 7: Cerrar scrapers
    print("\n=== PASO 7: LIMPIEZA ===")
    
    for retailer, scraper in scrapers.items():
        try:
            await scraper.cleanup()
            print(f"[OK] {retailer.upper()} cerrado")
        except Exception as e:
            print(f"[ERROR] Cerrando {retailer}: {e}")
    
    print("\n" + "="*80)
    print("PROCESO COMPLETADO")
    print(f"Fin: {datetime.now()}")
    print("="*80)
    
    return stats

if __name__ == "__main__":
    print("Iniciando Sistema V5 con Master System completo...")
    
    try:
        stats = asyncio.run(run_v5_with_master_system())
        
        if stats['total'] > 0:
            print(f"\n[EXITOSO] {stats['total']} productos procesados con Master System")
        else:
            print("\n[WARN] No se procesaron productos")
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()