#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cargar archivo Excel generado al sistema productivo Master
"""
import sys
import os
import asyncio
from pathlib import Path

# Force UTF-8 encoding
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

from core.integrated_master_system import IntegratedMasterSystem

async def load_excel_to_master(excel_file: str):
    """Cargar archivo Excel al sistema Master"""
    
    print(f"📥 Cargando archivo: {excel_file}")
    print("-" * 60)
    
    # Verificar que el archivo existe
    if not os.path.exists(excel_file):
        print(f"❌ Error: El archivo {excel_file} no existe")
        return
    
    # Inicializar Master System
    master_system = IntegratedMasterSystem("./data")
    await master_system.initialize()
    print("✅ Master System inicializado")
    
    # Procesar archivo Excel
    print(f"📊 Procesando archivo Excel...")
    
    # Leer el archivo Excel
    import pandas as pd
    df = pd.read_excel(excel_file)
    print(f"   Filas en Excel: {len(df)}")
    
    # Preparar productos para procesamiento
    products_list = df.to_dict('records')
    
    # Procesar con el Master System
    results = await master_system.process_scraping_results(products_list)
    
    print("\n📈 RESULTADOS DEL PROCESAMIENTO:")
    print("-" * 60)
    print(f"   📦 Productos procesados: {results.get('products_processed', 0)}")
    print(f"   💰 Actualizaciones de precio: {results.get('prices_updated', 0)}")
    print(f"   🚨 Alertas generadas: {results.get('alerts_generated', 0)}")
    if results.get('errors'):
        print(f"   ⚠️ Errores encontrados: {len(results['errors'])}")
    
    # Verificar datos en DuckDB
    import duckdb
    conn = duckdb.connect('./data/warehouse_master.duckdb', read_only=True)
    
    print("\n📊 ESTADO DE LA BASE DE DATOS:")
    print("-" * 60)
    
    # Contar productos
    productos = conn.execute("SELECT COUNT(*) FROM master_productos").fetchone()[0]
    print(f"   Total productos en master_productos: {productos}")
    
    # Contar precios
    precios = conn.execute("SELECT COUNT(*) FROM master_precios").fetchone()[0]
    print(f"   Total registros en master_precios: {precios}")
    
    # Productos por retailer
    print("\n   Productos por retailer:")
    retailers = conn.execute("""
        SELECT retailer, COUNT(*) as count 
        FROM master_productos 
        GROUP BY retailer 
        ORDER BY count DESC
    """).fetchall()
    
    for retailer, count in retailers:
        print(f"      - {retailer}: {count} productos")
    
    conn.close()
    
    # Shutdown
    await master_system.shutdown()
    print("\n✅ Procesamiento completado exitosamente")

if __name__ == "__main__":
    # Usar el archivo más reciente de Ripley
    excel_file = "data/excel/ripley_2025_08_31_204559.xlsx"
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    
    asyncio.run(load_excel_to_master(excel_file))