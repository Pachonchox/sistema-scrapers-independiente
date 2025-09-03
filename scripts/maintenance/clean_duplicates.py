# -*- coding: utf-8 -*-
"""
🧹 Script de Limpieza de Duplicados
===================================

Script para detectar y eliminar productos duplicados en la base de datos.
Mantiene solo 1 producto por cada entidad única.

Criterios de deduplicación:
- Mismo SKU + mismo retailer = duplicado
- Se mantiene el producto con código interno más reciente
- Se preservan los precios históricos del producto mantenido
"""

import psycopg2
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from core.logging_config import get_system_logger
    logger = get_system_logger("clean_duplicates")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    logger = logging.getLogger("clean_duplicates")

def get_database_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025')
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {e}")
        return None

def detect_duplicates(conn):
    """Detectar productos duplicados por SKU+retailer"""
    cur = conn.cursor()
    
    logger.info("🔍 Detectando productos duplicados...")
    
    # Buscar duplicados por SKU + retailer
    cur.execute("""
        SELECT sku, retailer, COUNT(*) as count,
               ARRAY_AGG(codigo_interno ORDER BY codigo_interno) as codigos
        FROM master_productos 
        WHERE sku IS NOT NULL AND sku != '' AND sku != 'N/A'
        GROUP BY sku, retailer 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    
    duplicates = cur.fetchall()
    logger.info(f"📊 Encontrados {len(duplicates)} grupos de duplicados")
    
    return duplicates

def clean_duplicate_group(conn, sku, retailer, codigos):
    """Limpiar un grupo de duplicados manteniendo solo uno"""
    cur = conn.cursor()
    
    # Mantener el último código (más reciente)
    codigo_a_mantener = codigos[-1]  # El último en orden alfabético
    codigos_a_eliminar = codigos[:-1]
    
    logger.info(f"🧹 SKU {sku} ({retailer}):")
    logger.info(f"   ✅ Mantener: {codigo_a_mantener}")
    logger.info(f"   🗑️  Eliminar: {', '.join(codigos_a_eliminar)}")
    
    # Obtener detalles del producto a mantener
    cur.execute("SELECT nombre FROM master_productos WHERE codigo_interno = %s", 
                (codigo_a_mantener,))
    nombre_producto = cur.fetchone()[0]
    
    try:
        # 1. Eliminar precios de productos duplicados
        for codigo in codigos_a_eliminar:
            cur.execute("DELETE FROM master_precios WHERE codigo_interno = %s", (codigo,))
            deleted_prices = cur.rowcount
            logger.info(f"   📊 Eliminados {deleted_prices} registros de precios para {codigo}")
        
        # 2. Eliminar productos duplicados
        for codigo in codigos_a_eliminar:
            cur.execute("DELETE FROM master_productos WHERE codigo_interno = %s", (codigo,))
            logger.info(f"   ✅ Producto {codigo} eliminado")
        
        # 3. Confirmar cambios
        conn.commit()
        
        logger.info(f"   🎯 Producto único mantenido: {nombre_producto[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Error limpiando duplicados: {e}")
        conn.rollback()
        return False

def generate_cleanup_report(conn, duplicates_before, duplicates_after):
    """Generar reporte de limpieza"""
    cur = conn.cursor()
    
    # Estadísticas finales
    cur.execute("SELECT COUNT(*) FROM master_productos")
    total_productos = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM master_precios")
    total_precios = cur.fetchone()[0]
    
    logger.info("=" * 60)
    logger.info("📊 REPORTE DE LIMPIEZA DE DUPLICADOS")
    logger.info("=" * 60)
    logger.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📦 Duplicados antes: {duplicates_before}")
    logger.info(f"📦 Duplicados después: {duplicates_after}")
    logger.info(f"🧹 Grupos limpiados: {duplicates_before - duplicates_after}")
    logger.info(f"📊 Total productos finales: {total_productos}")
    logger.info(f"💰 Total registros precios: {total_precios}")
    logger.info("=" * 60)
    
    if duplicates_after == 0:
        logger.info("✅ LIMPIEZA EXITOSA - No quedan duplicados")
    else:
        logger.warning(f"⚠️ Quedan {duplicates_after} duplicados por revisar")

def main():
    """Función principal de limpieza"""
    logger.info("🚀 Iniciando limpieza de duplicados")
    
    # Conexión a BD
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        # Detectar duplicados iniciales
        duplicates_initial = detect_duplicates(conn)
        duplicates_before = len(duplicates_initial)
        
        if duplicates_before == 0:
            logger.info("✅ No se encontraron duplicados - Base de datos limpia")
            return
        
        # Limpiar cada grupo de duplicados
        cleaned_count = 0
        for sku, retailer, count, codigos in duplicates_initial:
            if clean_duplicate_group(conn, sku, retailer, codigos):
                cleaned_count += 1
        
        # Verificar duplicados finales
        duplicates_final = detect_duplicates(conn)
        duplicates_after = len(duplicates_final)
        
        # Generar reporte
        generate_cleanup_report(conn, duplicates_before, duplicates_after)
        
        logger.info(f"🎉 Limpieza completada - {cleaned_count} grupos procesados")
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()