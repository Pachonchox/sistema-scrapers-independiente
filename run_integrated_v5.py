#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema Integrado v5 - Flujo completo: Scraping → Excel → PostgreSQL
=====================================================================

Flujo completo del sistema:
1. Ejecuta scrapers (simula v5)
2. Genera Excel con output_manager
3. Carga Excel al Master System
4. Persiste en PostgreSQL vía Docker

Basado en la estructura real del proyecto principal.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging

# Configurar encoding UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Agregar paths necesarios
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Flujo principal integrado"""
    
    logger.info("="*70)
    logger.info(" SISTEMA INTEGRADO v5 - FLUJO COMPLETO")
    logger.info("="*70)
    
    # ======================
    # PASO 1: Generar datos de prueba (simula scraping v5)
    # ======================
    logger.info("\n[PASO 1] Generando datos de scraping...")
    
    # Usar el generador de datos de muestra
    from generate_sample_excel import generate_sample_data
    excel_files = generate_sample_data()
    logger.info(f"Generados {len(excel_files)} archivos Excel")
    
    # ======================
    # PASO 2: Inicializar Docker con PostgreSQL
    # ======================
    logger.info("\n[PASO 2] Verificando PostgreSQL en Docker...")
    logger.info("Por favor asegurate de que Docker este ejecutando:")
    logger.info("  docker-compose up -d")
    
    # Esperar un momento para que los servicios inicien
    await asyncio.sleep(2)
    
    # ======================
    # PASO 3: Cargar Excel al Master System
    # ======================
    logger.info("\n[PASO 3] Cargando Excel al Master System...")
    
    try:
        from core.integrated_master_system import IntegratedMasterSystem
        
        # Inicializar Master System
        master_system = IntegratedMasterSystem("./data")
        await master_system.initialize()
        logger.info("Master System inicializado")
        
        # Procesar cada archivo Excel
        total_productos = 0
        total_precios = 0
        
        for excel_file in excel_files:
            logger.info(f"\nProcesando: {excel_file}")
            
            # Leer Excel
            df = pd.read_excel(excel_file)
            products_list = df.to_dict('records')
            
            # Detectar retailer del nombre del archivo
            retailer = Path(excel_file).stem.split('_')[0]
            
            # Procesar con el Master System
            results = await master_system.process_scraping_results(
                products_list,
                retailer=retailer
            )
            
            total_productos += results.get('products_processed', 0)
            total_precios += results.get('prices_updated', 0)
            
            logger.info(f"  Productos procesados: {results.get('products_processed', 0)}")
            logger.info(f"  Precios actualizados: {results.get('prices_updated', 0)}")
            
            if results.get('alerts_generated', 0) > 0:
                logger.info(f"  Alertas generadas: {results.get('alerts_generated', 0)}")
    
    except ImportError as e:
        logger.warning(f"Master System no disponible, usando modo simplificado: {e}")
        
        # Modo fallback: Solo mostrar datos
        for excel_file in excel_files:
            df = pd.read_excel(excel_file)
            logger.info(f"  {excel_file}: {len(df)} productos")
    
    # ======================
    # PASO 4: Verificar datos en PostgreSQL
    # ======================
    logger.info("\n[PASO 4] Verificando datos en PostgreSQL...")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025')
        )
        
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            logger.info("Tablas en PostgreSQL:")
            for table in tables:
                logger.info(f"  - {table[0]}")
                
                # Contar registros
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    logger.info(f"    Registros: {count}")
                except:
                    pass
        else:
            logger.info("No hay tablas creadas aun. Ejecutar schema_fixed.sql primero")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"No se pudo conectar a PostgreSQL: {e}")
        logger.info("Asegurate de que Docker este ejecutando: docker-compose up -d")
    
    # ======================
    # RESUMEN FINAL
    # ======================
    logger.info("\n" + "="*70)
    logger.info(" RESUMEN DEL PROCESAMIENTO")
    logger.info("="*70)
    logger.info(f"Archivos Excel procesados: {len(excel_files)}")
    
    try:
        logger.info(f"Total productos procesados: {total_productos}")
        logger.info(f"Total precios actualizados: {total_precios}")
    except:
        pass
    
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)

if __name__ == "__main__":
    asyncio.run(main())