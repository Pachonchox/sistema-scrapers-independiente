#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 ORQUESTADOR ROBUSTO V5 - SISTEMA COMPLETO
============================================

Orquestador de producción para scrapers V5 con:
- ✅ Integración completa con Master System y PostgreSQL
- ✅ Sistema de reintentos inteligente
- ✅ Manejo robusto de errores
- ✅ Logging detallado con emojis
- ✅ Ciclos continuos con pausas configurables
- ✅ Detección automática de arbitraje
- ✅ Alertas y notificaciones
- ✅ Métricas y estadísticas en tiempo real

Autor: Sistema V5 Production
Fecha: 03/09/2025
"""

import asyncio
import sys
import os
import signal
import logging
import traceback
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import pandas as pd

# Configurar paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# FORZAR SOPORTE COMPLETO DE EMOJIS
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

# Configurar UTF-8
import locale
try:
    locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Chile.1252')
    except:
        pass

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configuración de logging robusto
log_dir = Path("logs/orchestrator_v5")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            log_dir / f'orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)

# Reducir ruido de otros loggers
logging.getLogger("playwright").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger("OrchestratorV5")


class OrchestratorV5Robust:
    """🎯 Orquestador Robusto V5 con todas las características"""
    
    def __init__(self):
        """Inicializar orquestador con configuración completa"""
        
        self.start_time = datetime.now()
        self.running = False
        self.cycle_count = 0
        
        # Configuración del sistema
        self.config = {
            # Tiempos y ciclos
            'max_runtime_minutes': int(os.getenv('MAX_RUNTIME_MINUTES', '60')),
            'cycle_pause_seconds': int(os.getenv('CYCLE_PAUSE_SECONDS', '30')),
            'batch_size': int(os.getenv('BATCH_SIZE', '30')),
            
            # Reintentos
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'retry_delay': int(os.getenv('RETRY_DELAY', '5')),
            
            # Base de datos
            'data_backend': os.getenv('DATA_BACKEND', 'postgres'),
            'master_enabled': os.getenv('MASTER_SYSTEM_ENABLED', 'true').lower() == 'true',
            'arbitrage_enabled': os.getenv('ARBITRAGE_ENABLED', 'true').lower() == 'true',
            
            # Scrapers
            'scrapers_enabled': os.getenv('SCRAPERS_ENABLED', 'paris,ripley,falabella,hites,abcdin').split(','),
            
            # Categorías por retailer
            'categories': {
                'paris': ['celulares', 'computadores', 'televisores'],
                'ripley': ['computacion', 'celulares'],
                'falabella': ['smartphones', 'computadores', 'tablets'],
                'hites': ['celulares', 'computadores', 'televisores'],
                'abcdin': ['celulares', 'computadores', 'tablets', 'televisores']
            }
        }
        
        # Estadísticas globales
        self.stats = {
            'total_products': 0,
            'total_errors': 0,
            'products_by_retailer': {},
            'errors_by_retailer': {},
            'cycles_completed': 0,
            'last_cycle_time': None,
            'arbitrage_opportunities': 0
        }
        
        # Scrapers y sistema master
        self.scrapers = {}
        self.master_system = None
        
        logger.info("🚀 Orquestador V5 Robusto inicializado")
        logger.info(f"📋 Configuración: {json.dumps(self.config, indent=2)}")
    
    async def initialize_systems(self):
        """🔧 Inicializar todos los sistemas necesarios"""
        
        logger.info("\n" + "="*80)
        logger.info("🔧 INICIALIZANDO SISTEMAS")
        logger.info("="*80)
        
        # 1. Inicializar Master System si está habilitado
        if self.config['master_enabled'] and self.config['data_backend'] == 'postgres':
            try:
                logger.info("📦 Inicializando Master System con PostgreSQL...")
                
                from core.integrated_master_system import IntegratedMasterSystem
                
                self.master_system = IntegratedMasterSystem(
                    backend_type='postgres',
                    enable_normalization=True
                )
                
                logger.info("✅ Master System inicializado correctamente")
                
            except Exception as e:
                logger.error(f"❌ Error inicializando Master System: {e}")
                logger.info("⚠️  Continuando sin Master System...")
                self.master_system = None
        
        # 2. Verificar conexión PostgreSQL
        if self.config['data_backend'] == 'postgres':
            await self.verify_database()
        
        # 3. Inicializar scrapers V5
        await self.initialize_scrapers()
        
        logger.info("✅ Todos los sistemas inicializados")
    
    async def verify_database(self):
        """🗄️ Verificar conexión y tablas PostgreSQL"""
        
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
            
            # Verificar tablas
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('master_productos', 'master_precios', 'arbitrage_opportunities')
            """)
            
            tables = [t[0] for t in cur.fetchall()]
            logger.info(f"📊 Tablas PostgreSQL encontradas: {tables}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error verificando PostgreSQL: {e}")
    
    async def initialize_scrapers(self):
        """🕷️ Inicializar scrapers V5"""
        
        logger.info("\n📦 Inicializando scrapers V5...")
        
        from portable_orchestrator_v5.scrapers.paris_scraper_v5 import ParisScraperV5
        from portable_orchestrator_v5.scrapers.ripley_scraper_v5 import RipleyScraperV5
        from portable_orchestrator_v5.scrapers.falabella_scraper_v5 import FalabellaScraperV5
        from portable_orchestrator_v5.scrapers.hites_scraper_v5 import HitesScraperV5
        from portable_orchestrator_v5.scrapers.abcdin_scraper_v5 import AbcdinScraperV5
        
        scraper_classes = {
            'paris': ParisScraperV5,
            'ripley': RipleyScraperV5,
            'falabella': FalabellaScraperV5,
            'hites': HitesScraperV5,
            'abcdin': AbcdinScraperV5
        }
        
        for retailer in self.config['scrapers_enabled']:
            if retailer in scraper_classes:
                try:
                    logger.info(f"  Inicializando {retailer.upper()}...")
                    
                    scraper = scraper_classes[retailer]()
                    await scraper.initialize()
                    
                    self.scrapers[retailer] = scraper
                    self.stats['products_by_retailer'][retailer] = 0
                    self.stats['errors_by_retailer'][retailer] = 0
                    
                    logger.info(f"  ✅ {retailer.upper()} inicializado")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error inicializando {retailer}: {e}")
    
    async def run_scraping_cycle(self) -> Dict[str, Any]:
        """🔄 Ejecutar un ciclo completo de scraping"""
        
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        logger.info("\n" + "="*80)
        logger.info(f"🔄 CICLO {self.cycle_count} - {cycle_start.strftime('%H:%M:%S')}")
        logger.info("="*80)
        
        cycle_products = []
        cycle_stats = {
            'products': 0,
            'errors': 0,
            'by_retailer': {}
        }
        
        # Ejecutar cada scraper con sus categorías
        for retailer, scraper in self.scrapers.items():
            categories = self.config['categories'].get(retailer, [])
            
            for category in categories:
                products = await self.scrape_with_retry(
                    scraper, 
                    retailer, 
                    category
                )
                
                if products:
                    cycle_products.extend(products)
                    cycle_stats['products'] += len(products)
                    
                    if retailer not in cycle_stats['by_retailer']:
                        cycle_stats['by_retailer'][retailer] = 0
                    cycle_stats['by_retailer'][retailer] += len(products)
        
        # Procesar productos con Master System
        if cycle_products and self.master_system:
            await self.process_with_master_system(cycle_products)
        
        # Guardar resultados en Excel
        if cycle_products:
            self.save_to_excel(cycle_products, self.cycle_count)
        
        # Actualizar estadísticas
        cycle_time = (datetime.now() - cycle_start).total_seconds()
        cycle_stats['time'] = cycle_time
        
        self.stats['cycles_completed'] += 1
        self.stats['last_cycle_time'] = cycle_time
        self.stats['total_products'] += cycle_stats['products']
        
        logger.info(f"\n📊 Resumen Ciclo {self.cycle_count}:")
        logger.info(f"  ⏱️  Tiempo: {cycle_time:.1f}s")
        logger.info(f"  📦 Productos: {cycle_stats['products']}")
        logger.info(f"  ❌ Errores: {cycle_stats['errors']}")
        
        for retailer, count in cycle_stats['by_retailer'].items():
            logger.info(f"    {retailer.upper()}: {count} productos")
        
        return cycle_stats
    
    async def scrape_with_retry(
        self, 
        scraper, 
        retailer: str, 
        category: str
    ) -> List[Dict[str, Any]]:
        """🔄 Scraping con reintentos automáticos"""
        
        products = []
        retries = 0
        
        while retries < self.config['max_retries']:
            try:
                logger.info(f"\n🕷️ Scraping {retailer.upper()} - {category}")
                
                result = await scraper.scrape_category(
                    category=category,
                    max_products=self.config['batch_size']
                )
                
                if result.success:
                    count = len(result.products)
                    logger.info(f"  ✅ {count} productos extraídos")
                    
                    # Convertir a diccionarios para procesamiento
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
                            
                            # Timestamps
                            'fecha_captura': datetime.now(),
                            'extraction_timestamp': product.extraction_timestamp,
                            
                            # Especificaciones
                            'storage': product.additional_info.get('storage', '') if product.additional_info else '',
                            'ram': product.additional_info.get('ram', '') if product.additional_info else '',
                            'color': product.additional_info.get('color', '') if product.additional_info else '',
                        }
                        products.append(product_dict)
                    
                    # Actualizar estadísticas
                    self.stats['products_by_retailer'][retailer] += count
                    
                    return products
                    
                else:
                    logger.warning(f"  ⚠️ Error: {result.error_message}")
                    retries += 1
                    
            except Exception as e:
                logger.error(f"  ❌ Error crítico: {e}")
                retries += 1
                self.stats['errors_by_retailer'][retailer] += 1
                
                if retries < self.config['max_retries']:
                    logger.info(f"  🔄 Reintentando ({retries}/{self.config['max_retries']})...")
                    await asyncio.sleep(self.config['retry_delay'])
        
        return products
    
    async def process_with_master_system(self, products: List[Dict[str, Any]]):
        """🎯 Procesar productos con Master System"""
        
        if not self.master_system:
            return
        
        logger.info(f"\n📦 Procesando {len(products)} productos con Master System...")
        
        processed = 0
        errors = 0
        
        for product in products:
            try:
                # Master System se encarga de todo
                self.master_system.process_product(product)
                processed += 1
                
                if processed % 10 == 0:
                    logger.debug(f"  Procesados: {processed}/{len(products)}")
                    
            except Exception as e:
                errors += 1
                logger.debug(f"  Error procesando: {e}")
        
        logger.info(f"  ✅ Procesados: {processed}")
        
        if errors > 0:
            logger.warning(f"  ⚠️ Errores: {errors}")
        
        # Detectar arbitraje si está habilitado
        if self.config['arbitrage_enabled']:
            await self.detect_arbitrage_opportunities()
        
        # Limpiar precios anómalos cada 3 ciclos
        if self.cycle_count % 3 == 0:
            await self.cleanup_anomalous_prices()
    
    async def detect_arbitrage_opportunities(self):
        """💰 Detectar oportunidades de arbitraje"""
        
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
            
            # Contar oportunidades del día
            cur.execute("""
                SELECT COUNT(*) 
                FROM arbitrage_opportunities
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            count = cur.fetchone()[0]
            
            if count > self.stats['arbitrage_opportunities']:
                new_opportunities = count - self.stats['arbitrage_opportunities']
                logger.info(f"  💰 {new_opportunities} nuevas oportunidades de arbitraje detectadas!")
                self.stats['arbitrage_opportunities'] = count
            
            conn.close()
            
        except Exception as e:
            logger.debug(f"  Error verificando arbitraje: {e}")
    
    async def cleanup_anomalous_prices(self):
        """🧹 Limpiar precios anómalos automáticamente"""
        
        try:
            logger.info("  🧹 Ejecutando limpieza de precios anómalos...")
            
            # Importar el detector
            from price_anomaly_detector import PriceAnomalyDetector
            
            detector = PriceAnomalyDetector()
            
            # Ejecutar detección rápida (solo último día)
            results = detector.run_full_detection(days_back=1)
            
            if results['status'] == 'success' and results['anomalies_found'] > 0:
                anomalies = results['anomalies_found']
                deleted = results['deleted_count']
                
                logger.info(f"    🔍 Anomalías detectadas: {anomalies}")
                logger.info(f"    🗑️ Eliminadas automáticamente: {deleted}")
                
                if anomalies > 20:  # Muchas anomalías
                    logger.warning(f"    🚨 Alto número de anomalías detectadas!")
                
                # Actualizar estadísticas
                self.stats['anomalies_cleaned'] = self.stats.get('anomalies_cleaned', 0) + deleted
                
            else:
                logger.info("    ✅ No se encontraron precios anómalos")
                
        except Exception as e:
            logger.error(f"    ❌ Error en limpieza de precios: {e}")
    
    def save_to_excel(self, products: List[Dict[str, Any]], cycle: int):
        """💾 Guardar productos en Excel"""
        
        try:
            excel_dir = Path("data/excel/orchestrator_v5")
            excel_dir.mkdir(parents=True, exist_ok=True)
            
            filename = excel_dir / f"cycle_{cycle}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            df = pd.DataFrame(products)
            df.to_excel(filename, index=False)
            
            logger.info(f"  💾 Guardado en: {filename.name}")
            
        except Exception as e:
            logger.error(f"  ❌ Error guardando Excel: {e}")
    
    async def run_production(self):
        """🚀 Ejecutar orquestador en modo producción"""
        
        self.running = True
        end_time = self.start_time + timedelta(minutes=self.config['max_runtime_minutes'])
        
        print("\n" + "="*80)
        print("🚀 ORQUESTADOR V5 ROBUSTO - MODO PRODUCCIÓN")
        print("="*80)
        print(f"⏰ Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Fin programado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⚙️  Scrapers activos: {', '.join(self.config['scrapers_enabled'])}")
        print(f"📦 Productos por batch: {self.config['batch_size']}")
        print(f"⏸️  Pausa entre ciclos: {self.config['cycle_pause_seconds']}s")
        print("="*80)
        
        try:
            # Inicializar sistemas
            await self.initialize_systems()
            
            # Ejecutar ciclos hasta alcanzar el tiempo límite
            while self.running and datetime.now() < end_time:
                # Ejecutar ciclo de scraping
                cycle_stats = await self.run_scraping_cycle()
                
                # Verificar si continuar
                remaining = (end_time - datetime.now()).total_seconds()
                
                if remaining > self.config['cycle_pause_seconds']:
                    logger.info(f"\n⏸️  Pausando {self.config['cycle_pause_seconds']}s...")
                    logger.info(f"⏱️  Tiempo restante: {remaining/60:.1f} minutos")
                    await asyncio.sleep(self.config['cycle_pause_seconds'])
                else:
                    logger.info(f"\n⏰ Tiempo límite alcanzado")
                    break
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupción por usuario")
            
        except Exception as e:
            logger.error(f"\n❌ Error crítico: {e}")
            traceback.print_exc()
            
        finally:
            await self.cleanup()
            self.show_final_stats()
    
    async def cleanup(self):
        """🧹 Limpiar recursos"""
        
        logger.info("\n🧹 Limpiando recursos...")
        
        for retailer, scraper in self.scrapers.items():
            try:
                await scraper.cleanup()
                logger.info(f"  ✅ {retailer.upper()} cerrado")
            except Exception as e:
                logger.error(f"  ❌ Error cerrando {retailer}: {e}")
        
        self.running = False
    
    def show_final_stats(self):
        """📊 Mostrar estadísticas finales"""
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("📊 ESTADÍSTICAS FINALES")
        print("="*80)
        print(f"⏱️  Tiempo total: {runtime/60:.1f} minutos")
        print(f"🔄 Ciclos completados: {self.stats['cycles_completed']}")
        print(f"📦 Total productos: {self.stats['total_products']}")
        print(f"❌ Total errores: {self.stats['total_errors']}")
        
        if self.stats['cycles_completed'] > 0:
            avg_time = runtime / self.stats['cycles_completed']
            avg_products = self.stats['total_products'] / self.stats['cycles_completed']
            print(f"⚡ Promedio por ciclo: {avg_products:.0f} productos en {avg_time:.1f}s")
        
        print("\n📊 Por retailer:")
        for retailer, count in self.stats['products_by_retailer'].items():
            errors = self.stats['errors_by_retailer'].get(retailer, 0)
            print(f"  {retailer.upper()}: {count} productos, {errors} errores")
        
        if self.stats['arbitrage_opportunities'] > 0:
            print(f"\n💰 Oportunidades de arbitraje detectadas: {self.stats['arbitrage_opportunities']}")
        
        if self.stats.get('anomalies_cleaned', 0) > 0:
            print(f"🧹 Precios anómalos limpiados: {self.stats['anomalies_cleaned']}")
        
        print("="*80)
        print("✅ ORQUESTADOR V5 FINALIZADO")
        print("="*80)


async def main():
    """🎯 Función principal"""
    
    # Manejar señales de interrupción
    def signal_handler(sig, frame):
        logger.info("\n⚠️  Señal de interrupción recibida")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Crear y ejecutar orquestador
    orchestrator = OrchestratorV5Robust()
    await orchestrator.run_production()


if __name__ == "__main__":
    print("\n🚀 Iniciando Orquestador V5 Robusto...")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()