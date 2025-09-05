#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 Sistema Optimizado de Scraping V5
=====================================

Script principal para ejecutar el sistema de scraping optimizado con:
- SKU único de 10 caracteres
- Inserción directa a base de datos
- Backup automático en Excel
- Procesamiento paralelo de múltiples retailers

Uso:
    python run_optimized_scraping.py                    # Todos los retailers
    python run_optimized_scraping.py --retailer falabella
    python run_optimized_scraping.py --test             # Modo test (5 productos)
    python run_optimized_scraping.py --migrate          # Migrar datos existentes

Autor: Sistema Optimizado V5
Fecha: Diciembre 2024
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Cargar variables de entorno
load_dotenv()

# Imports del sistema optimizado
from core.scraping_orchestrator import ScrapingOrchestrator
from core.product_processor import ProductProcessor
from core.sku_generator import SKUGenerator
from core.price_manager import PriceManager

# Configuración de logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('optimized_scraping.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class OptimizedScrapingSystem:
    """🚀 Sistema principal de scraping optimizado"""
    
    def __init__(self):
        """Inicializa el sistema"""
        self.config = self._load_config()
        self.orchestrator = None
        
        logger.info("=" * 70)
        logger.info("🚀 SISTEMA OPTIMIZADO DE SCRAPING V5")
        logger.info("=" * 70)
        logger.info("✅ SKU único de 10 caracteres")
        logger.info("✅ Inserción directa a DB")
        logger.info("✅ Backup automático en Excel")
        logger.info("✅ Procesamiento paralelo")
        logger.info("=" * 70)
    
    def _load_config(self) -> dict:
        """Carga configuración del sistema"""
        return {
            'db': {
                'host': os.getenv('PGHOST', 'localhost'),
                'port': os.getenv('PGPORT', '5434'),
                'database': os.getenv('PGDATABASE', 'price_orchestrator'),
                'user': os.getenv('PGUSER', 'orchestrator'),
                'password': os.getenv('PGPASSWORD', 'orchestrator_2025')
            },
            'scraping': {
                'batch_size': 100,
                'enable_excel_backup': True,
                'parallel_execution': True,
                'default_category': 'smartphones',
                'default_max_products': 100
            },
            'retailers': {
                'enabled': ['falabella', 'ripley', 'paris', 'mercadolibre', 'hites', 'abcdin'],
                'categories': {
                    'smartphones': ['smartphones', 'celulares', 'telefonos'],
                    'notebooks': ['computadores', 'notebooks', 'laptops'],
                    'tablets': ['tablets', 'ipad'],
                    'smart_tv': ['smart-tv', 'televisores', 'tv']
                }
            }
        }
    
    async def run_full_scraping(self, test_mode: bool = False):
        """
        Ejecuta scraping completo de todos los retailers
        
        Args:
            test_mode: Si es True, solo procesa 5 productos por retailer
        """
        start_time = datetime.now()
        
        try:
            # Crear orquestador
            self.orchestrator = ScrapingOrchestrator(
                db_config=self.config['db'],
                enable_excel_backup=self.config['scraping']['enable_excel_backup'],
                batch_size=self.config['scraping']['batch_size']
            )
            
            # Configuración de scraping
            max_products = 5 if test_mode else self.config['scraping']['default_max_products']
            
            if test_mode:
                logger.info("🧪 MODO TEST: Solo 5 productos por retailer")
            
            # Ejecutar scraping para todos los retailers habilitados
            stats = await self.orchestrator.scrape_all_retailers(
                category=self.config['scraping']['default_category'],
                max_products_per_retailer=max_products
            )
            
            # Mostrar resumen final
            self._show_final_summary(stats, start_time)
            
        except Exception as e:
            logger.error(f"❌ Error en scraping: {e}")
            raise
        finally:
            if self.orchestrator:
                await self.orchestrator.close()
    
    async def run_single_retailer(self, retailer: str, category: str = None, max_products: int = None):
        """
        Ejecuta scraping para un solo retailer
        
        Args:
            retailer: Nombre del retailer
            category: Categoría (opcional)
            max_products: Máximo de productos (opcional)
        """
        start_time = datetime.now()
        
        try:
            # Valores por defecto
            category = category or self.config['scraping']['default_category']
            max_products = max_products or self.config['scraping']['default_max_products']
            
            logger.info(f"🎯 Scraping individual: {retailer}")
            logger.info(f"   Categoría: {category}")
            logger.info(f"   Max productos: {max_products}")
            
            # Crear orquestador
            self.orchestrator = ScrapingOrchestrator(
                db_config=self.config['db'],
                enable_excel_backup=self.config['scraping']['enable_excel_backup'],
                batch_size=self.config['scraping']['batch_size']
            )
            
            # Ejecutar scraping
            result = await self.orchestrator.scrape_retailer(
                retailer=retailer,
                category=category,
                max_products=max_products
            )
            
            # Mostrar resultado
            logger.info("=" * 70)
            logger.info("📊 RESULTADO")
            logger.info("=" * 70)
            logger.info(f"✅ Éxito: {result['success']}")
            logger.info(f"📦 Productos scrapeados: {result['products_scraped']}")
            logger.info(f"💾 Productos procesados: {result['products_processed']}")
            logger.info(f"⏱️ Tiempo: {result['execution_time']:.1f} segundos")
            
            if result['errors']:
                logger.warning(f"⚠️ Errores: {result['errors']}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise
        finally:
            if self.orchestrator:
                await self.orchestrator.close()
    
    async def run_custom_config(self, config: dict):
        """
        Ejecuta scraping con configuración personalizada
        
        Args:
            config: Configuración personalizada
        """
        try:
            # Crear orquestador
            self.orchestrator = ScrapingOrchestrator(
                db_config=self.config['db'],
                enable_excel_backup=self.config['scraping']['enable_excel_backup'],
                batch_size=self.config['scraping']['batch_size']
            )
            
            # Ejecutar con configuración personalizada
            stats = await self.orchestrator.scrape_with_config(config)
            
            # Mostrar estadísticas
            print(stats.get_summary())
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise
        finally:
            if self.orchestrator:
                await self.orchestrator.close()
    
    def _show_final_summary(self, stats, start_time):
        """Muestra resumen final de la ejecución"""
        total_time = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("🏁 EJECUCIÓN COMPLETADA")
        print("=" * 70)
        print(f"⏱️  Tiempo total: {total_time:.1f} segundos")
        print(f"🕷️  Scrapers ejecutados: {stats.scrapers_executed}")
        print(f"📦 Productos totales: {stats.total_products_scraped:,}")
        print(f"💾 Productos procesados: {stats.total_products_processed:,}")
        print(f"✅ Productos insertados: {stats.total_products_inserted:,}")
        print(f"🔄 Duplicados detectados: {stats.total_duplicates:,}")
        
        if stats.total_products_processed > 0:
            efficiency = (stats.total_products_inserted / stats.total_products_processed) * 100
            print(f"📊 Eficiencia: {efficiency:.1f}%")
        
        if total_time > 0:
            rate = stats.total_products_processed / total_time
            print(f"⚡ Velocidad: {rate:.1f} productos/segundo")
        
        print("=" * 70)


async def migrate_existing_data():
    """Migra datos existentes al nuevo sistema de SKU"""
    logger.info("🔄 MIGRACIÓN DE DATOS EXISTENTES")
    logger.info("=" * 70)
    
    try:
        import psycopg2
        from core.sku_generator import SKUGenerator
        
        # Conectar a DB
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025')
        )
        cursor = conn.cursor()
        
        # Agregar columna para nuevo SKU si no existe
        logger.info("📝 Preparando base de datos...")
        cursor.execute("""
            ALTER TABLE master_productos 
            ADD COLUMN IF NOT EXISTS sku_nuevo VARCHAR(11)
        """)
        
        # Obtener todos los productos
        logger.info("📦 Obteniendo productos existentes...")
        cursor.execute("""
            SELECT codigo_interno, sku, link, nombre, retailer
            FROM master_productos
            WHERE sku_nuevo IS NULL
        """)
        
        products = cursor.fetchall()
        logger.info(f"   Encontrados: {len(products)} productos para migrar")
        
        if products:
            # Generar nuevos SKUs
            generator = SKUGenerator()
            migrated = 0
            
            for product in products:
                codigo_interno, sku, link, nombre, retailer = product
                
                # Crear dict para generador
                product_data = {
                    'sku': sku,
                    'link': link,
                    'nombre': nombre
                }
                
                # Generar nuevo SKU
                new_sku = generator.generate_sku(product_data, retailer)
                
                # Actualizar en DB
                cursor.execute("""
                    UPDATE master_productos
                    SET sku_nuevo = %s
                    WHERE codigo_interno = %s
                """, (new_sku, codigo_interno))
                
                migrated += 1
                
                if migrated % 100 == 0:
                    logger.info(f"   Migrados: {migrated}/{len(products)}")
                    conn.commit()
            
            # Commit final
            conn.commit()
            
            logger.info(f"✅ Migración completada: {migrated} productos")
            
            # Estadísticas del generador
            stats = generator.get_stats()
            logger.info(f"📊 SKUs únicos generados: {stats['unique_skus']}")
            logger.info(f"📊 Colisiones detectadas: {stats['collisions_checked']}")
        else:
            logger.info("ℹ️ No hay productos para migrar")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        raise


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Sistema Optimizado de Scraping V5')
    parser.add_argument('--test', action='store_true', help='Modo test (5 productos)')
    parser.add_argument('--retailer', type=str, help='Ejecutar solo un retailer')
    parser.add_argument('--category', type=str, default='smartphones', help='Categoría a scrapear')
    parser.add_argument('--max-products', type=int, help='Máximo de productos')
    parser.add_argument('--migrate', action='store_true', help='Migrar datos existentes')
    parser.add_argument('--parallel', action='store_true', default=True, help='Ejecución paralela')
    
    args = parser.parse_args()
    
    # Modo migración
    if args.migrate:
        asyncio.run(migrate_existing_data())
        return
    
    # Crear sistema
    system = OptimizedScrapingSystem()
    
    # Determinar qué ejecutar
    if args.retailer:
        # Un solo retailer
        asyncio.run(system.run_single_retailer(
            retailer=args.retailer,
            category=args.category,
            max_products=args.max_products
        ))
    elif args.test:
        # Modo test
        asyncio.run(system.run_full_scraping(test_mode=True))
    else:
        # Scraping completo
        asyncio.run(system.run_full_scraping(test_mode=False))


if __name__ == "__main__":
    try:
        print("\n" + "🚀" * 35)
        print("    SISTEMA OPTIMIZADO DE SCRAPING V5    ")
        print("🚀" * 35 + "\n")
        
        main()
        
        print("\n✅ Ejecución completada exitosamente")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Ejecución interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)