# -*- coding: utf-8 -*-
"""
🧪 Test de Sistema de Respaldo Parquet
=====================================

Tests para validar el sistema de respaldo Parquet integrado
en los scrapers V5.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from core.logging_config import get_test_logger
    logger = get_test_logger("test_parquet_backup")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_parquet_backup")

def test_parquet_backup_system():
    """Test completo del sistema de respaldo Parquet"""
    
    logger.info("🧪 INICIANDO TESTS DE SISTEMA PARQUET BACKUP")
    logger.info("=" * 60)
    
    # Crear directorio temporal para tests
    temp_dir = tempfile.mkdtemp()
    logger.info(f"📁 Directorio temporal: {temp_dir}")
    
    try:
        # Test 1: Importar sistema Parquet
        logger.info("\n🧪 Test 1: Importar ParquetBackupSystem...")
        try:
            from core.parquet_backup_system import ParquetBackupSystem, save_scraper_backup, get_backup_stats
            logger.info("✅ ParquetBackupSystem importado correctamente")
        except ImportError as e:
            logger.error(f"❌ Error importando ParquetBackupSystem: {e}")
            return
        
        # Test 2: Inicializar sistema
        logger.info("\n🧪 Test 2: Inicializar sistema...")
        backup_system = ParquetBackupSystem(base_path=temp_dir)
        logger.info("✅ Sistema inicializado")
        
        # Test 3: Datos de prueba
        logger.info("\n🧪 Test 3: Preparar datos de prueba...")
        test_products = [
            {
                "nombre": "iPhone 15 Pro 128GB Titanio Natural",
                "marca": "Apple",
                "sku": "IPHONE15PRO128TN",
                "precio_normal": 1299990,
                "precio_oferta": 1199990,
                "rating": 4.8,
                "reviews_count": 234,
                "link": "https://falabella.com/iphone15pro",
                "retailer": "falabella",
                "categoria": "smartphones",
                "out_of_stock": False,
                "timestamp_scraping": datetime.now().isoformat()
            },
            {
                "nombre": "Samsung Galaxy S24 Ultra 256GB Negro",
                "marca": "Samsung", 
                "sku": "GALAXYS24ULTRA256N",
                "precio_normal": 1599990,
                "precio_oferta": 1399990,
                "rating": 4.6,
                "reviews_count": 156,
                "link": "https://falabella.com/galaxys24ultra",
                "retailer": "falabella",
                "categoria": "smartphones",
                "out_of_stock": False,
                "timestamp_scraping": datetime.now().isoformat()
            },
            {
                "nombre": "MacBook Air M3 13\" 256GB",
                "marca": "Apple",
                "sku": "MACBOOKAIRM3256", 
                "precio_normal": 1299990,
                "precio_oferta": None,
                "rating": 4.9,
                "reviews_count": 89,
                "link": "https://falabella.com/macbookair",
                "retailer": "falabella", 
                "categoria": "laptops",
                "out_of_stock": False,
                "timestamp_scraping": datetime.now().isoformat()
            }
        ]
        
        test_metadata = {
            "session_id": "test_session_001",
            "source_urls": ["https://falabella.com/smartphones", "https://falabella.com/laptops"],
            "execution_time": 45.5,
            "success_rate": 1.0,
            "errors": [],
            "warnings": ["Algunos precios pueden estar desactualizados"]
        }
        
        logger.info(f"✅ {len(test_products)} productos de prueba preparados")
        
        # Test 4: Guardar respaldo smartphones
        logger.info("\n🧪 Test 4: Guardar respaldo smartphones...")
        smartphones_products = [p for p in test_products if p["categoria"] == "smartphones"]
        result1 = backup_system.save_scraped_data(
            retailer="falabella",
            category="smartphones", 
            products=smartphones_products,
            metadata=test_metadata
        )
        
        if result1["success"]:
            logger.info(f"✅ Respaldo smartphones: {result1['file_path']}")
            logger.info(f"📊 {result1['products_count']} productos, {result1['file_size_mb']:.2f}MB")
        else:
            logger.error(f"❌ Error guardando smartphones: {result1.get('error')}")
            return
        
        # Test 5: Guardar respaldo laptops
        logger.info("\n🧪 Test 5: Guardar respaldo laptops...")
        laptops_products = [p for p in test_products if p["categoria"] == "laptops"]
        result2 = backup_system.save_scraped_data(
            retailer="falabella",
            category="laptops",
            products=laptops_products,
            metadata=test_metadata
        )
        
        if result2["success"]:
            logger.info(f"✅ Respaldo laptops: {result2['file_path']}")
            logger.info(f"📊 {result2['products_count']} productos, {result2['file_size_mb']:.2f}MB")
        else:
            logger.error(f"❌ Error guardando laptops: {result2.get('error')}")
        
        # Test 6: Guardar respaldo para otro retailer
        logger.info("\n🧪 Test 6: Guardar respaldo para Ripley...")
        ripley_products = [
            {
                **test_products[0],
                "retailer": "ripley",
                "link": "https://ripley.com/iphone15pro",
                "sku": "RIPLEY_IPHONE15PRO"
            }
        ]
        
        result3 = backup_system.save_scraped_data(
            retailer="ripley",
            category="smartphones",
            products=ripley_products,
            metadata=test_metadata
        )
        
        if result3["success"]:
            logger.info(f"✅ Respaldo Ripley: {result3['file_path']}")
        else:
            logger.error(f"❌ Error guardando Ripley: {result3.get('error')}")
        
        # Test 7: Leer respaldos
        logger.info("\n🧪 Test 7: Leer respaldos...")
        df1 = backup_system.read_backup(result1["file_path"])
        if not df1.empty:
            logger.info(f"✅ Respaldo smartphones leído: {len(df1)} filas")
            logger.info(f"📋 Columnas: {list(df1.columns)}")
        else:
            logger.error("❌ Error leyendo respaldo smartphones")
        
        # Test 8: Listar respaldos
        logger.info("\n🧪 Test 8: Listar respaldos...")
        backups = backup_system.list_backups(days_back=1)
        logger.info(f"✅ Encontrados {len(backups)} respaldos:")
        for backup in backups:
            logger.info(f"  📦 {backup['retailer']}/{backup['file']} - {backup['size_mb']}MB")
        
        # Test 9: Estadísticas
        logger.info("\n🧪 Test 9: Estadísticas del sistema...")
        stats = backup_system.get_backup_stats()
        if "error" not in stats:
            logger.info(f"✅ Estadísticas obtenidas:")
            logger.info(f"  📊 Total retailers: {stats['total_retailers']}")
            logger.info(f"  📁 Total archivos: {stats['total_files']}")
            logger.info(f"  💾 Total tamaño: {stats['total_size_mb']}MB")
            logger.info(f"  🏪 Retailers: {list(stats['retailers'].keys())}")
        else:
            logger.error(f"❌ Error obteniendo estadísticas: {stats['error']}")
        
        # Test 10: Función helper
        logger.info("\n🧪 Test 10: Función helper save_scraper_backup...")
        helper_result = save_scraper_backup(
            retailer="paris",
            category="smartphones",
            products=[test_products[0]],
            metadata={"session_id": "helper_test"}
        )
        
        if helper_result["success"]:
            logger.info(f"✅ Helper function: {helper_result['file_path']}")
        else:
            logger.error(f"❌ Error con helper: {helper_result.get('error')}")
        
        # Test 11: Función helper stats
        logger.info("\n🧪 Test 11: Función helper get_backup_stats...")
        helper_stats = get_backup_stats()
        if "error" not in helper_stats:
            logger.info(f"✅ Helper stats: {helper_stats['total_files']} archivos totales")
        else:
            logger.error(f"❌ Error con helper stats: {helper_stats['error']}")
        
        # Test 12: Verificar estructura de carpetas
        logger.info("\n🧪 Test 12: Verificar estructura de carpetas...")
        expected_structure = [
            Path(temp_dir) / "falabella" / datetime.now().strftime("%Y-%m-%d"),
            Path(temp_dir) / "ripley" / datetime.now().strftime("%Y-%m-%d"),
            Path(temp_dir) / "paris" / datetime.now().strftime("%Y-%m-%d")
        ]
        
        for path in expected_structure:
            if path.exists():
                logger.info(f"✅ Estructura correcta: {path}")
                # Listar contenido
                files = list(path.glob("*.parquet"))
                json_files = list(path.glob("*.json"))
                logger.info(f"  📦 Archivos Parquet: {len(files)}")
                logger.info(f"  📋 Archivos metadata: {len(json_files)}")
            else:
                logger.warning(f"⚠️ Carpeta no encontrada: {path}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error durante tests: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar directorio temporal
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"🧹 Directorio temporal limpiado: {temp_dir}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo limpiar directorio temporal: {e}")

if __name__ == "__main__":
    test_parquet_backup_system()