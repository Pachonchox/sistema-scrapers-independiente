# -*- coding: utf-8 -*-
"""
Integrated Master System
=========================
Sistema integrado que conecta Master de Productos + Master de Precios + Alertas
para pipeline de scraping 24/7 con snapshot diario inteligente.

Pipeline completo:
Scraping → Código Interno → Master Productos → Master Precios → Alertas → Storage
"""

import asyncio
import logging
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import threading
import time as time_module

from .master_products_system import MasterProductsManager, process_scraping_batch
from .master_prices_system import MasterPricesManager, setup_telegram_alerts_integration, process_price_update_from_scraping

logger = logging.getLogger(__name__)


class IntegratedMasterSystem:
    """Sistema integrado de Masters con automatización completa"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        
        # Inicializar managers
        self.products_manager = MasterProductsManager(base_path)
        self.prices_manager = MasterPricesManager(base_path)
        
        # Establecer referencia cruzada para enriquecimiento de alertas
        self.prices_manager.set_products_manager(self.products_manager)
        
        # Control de threading para midnight closure
        self.scheduler_thread = None
        self.running = False
        
        logger.info("Integrated Master System initialized")
    
    async def initialize(self):
        """Inicializar sistema completo"""
        try:
            # Setup integración con Telegram
            await setup_telegram_alerts_integration(self.prices_manager)
            
            # Configurar scheduler para medianoche
            self._setup_midnight_scheduler()
            
            logger.info("Integrated Master System fully initialized")
            
        except Exception as e:
            logger.error(f"Error initializing integrated system: {e}")
    
    def _setup_midnight_scheduler(self):
        """Configurar scheduler simple para cierre automático a medianoche"""
        
        def run_scheduler():
            """Ejecutar scheduler simple en thread separado"""
            while self.running:
                try:
                    now = datetime.now()
                    
                    # Verificar si es medianoche (00:00 - 00:05)
                    if now.hour == 0 and now.minute < 5:
                        # Ejecutar cierre de medianoche
                        asyncio.run(self.prices_manager.midnight_closure())
                        self.products_manager.save_to_storage()
                        
                        logger.info("Scheduled midnight closure completed")
                        
                        # Esperar hasta que pase la ventana de medianoche
                        time_module.sleep(300)  # 5 minutos
                    
                    # Check every minute
                    time_module.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error in scheduler: {e}")
                    time_module.sleep(60)
        
        # Iniciar scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Simple midnight scheduler configured")
    
    async def process_scraping_results(self, scraping_results: List[Dict[str, Any]], 
                                     retailer: str = None) -> Dict[str, Any]:
        """
        Procesar resultados completos de scraping
        
        Args:
            scraping_results: Lista de productos scrapeados
            retailer: Retailer específico (opcional, se puede inferir de datos)
            
        Returns:
            Estadísticas de procesamiento
        """
        
        if not scraping_results:
            return {'status': 'no_data'}
        
        logger.info(f"Processing {len(scraping_results)} scraping results")
        
        processing_stats = {
            'products_processed': 0,
            'products_new': 0,
            'products_updated': 0,
            'prices_updated': 0,
            'alerts_generated': 0,
            'errors': []
        }
        
        try:
            # FASE 1: Procesar Master de Productos
            products_result = process_scraping_batch(scraping_results, self.products_manager)
            
            processing_stats.update({
                'products_processed': products_result['products_processed'],
                'products_new': products_result['products_new'],
                'products_updated': products_result['products_updated'],
                'errors': products_result['errors'].copy()
            })
            
            # FASE 2: Procesar Master de Precios (para cada producto)
            for scraping_data in scraping_results:
                try:
                    # Obtener producto del master (debe existir después de Fase 1)
                    link = scraping_data.get('link', scraping_data.get('product_url', ''))
                    product = self.products_manager.get_product_by_link(link)
                    
                    if not product:
                        processing_stats['errors'].append(f"Product not found in master: {link}")
                        continue
                    
                    # Procesar precio
                    price_result = await process_price_update_from_scraping(
                        codigo_interno=product.codigo_interno,
                        retailer=product.retailer,
                        scraping_data=scraping_data,
                        prices_manager=self.prices_manager
                    )
                    
                    if price_result['updated']:
                        processing_stats['prices_updated'] += 1
                        processing_stats['alerts_generated'] += price_result['alerts_generated']
                    
                except Exception as e:
                    error_msg = f"Error processing price for {scraping_data.get('link', 'unknown')}: {e}"
                    logger.error(error_msg)
                    processing_stats['errors'].append(error_msg)
            
            # FASE 3: Guardar cambios
            await self._save_all_changes()
            
            logger.info(f"Processing completed: {processing_stats['products_processed']} products, "
                       f"{processing_stats['prices_updated']} price updates, "
                       f"{processing_stats['alerts_generated']} alerts")
            
            return processing_stats
            
        except Exception as e:
            logger.error(f"Error in integrated processing: {e}")
            processing_stats['errors'].append(str(e))
            return processing_stats
    
    async def _save_all_changes(self):
        """Guardar todos los cambios pendientes"""
        try:
            # Guardar productos
            self.products_manager.save_to_storage()
            
            # Guardar precios del día actual
            self.prices_manager.save_daily_snapshots()
            
        except Exception as e:
            logger.error(f"Error saving changes: {e}")
    
    def get_product_complete_info(self, codigo_interno: str) -> Dict[str, Any]:
        """Obtener información completa de un producto (master + precios)"""
        
        # Información del producto
        product = self.products_manager.get_product_by_codigo(codigo_interno)
        if not product:
            return {'error': 'product_not_found'}
        
        # Información de precios
        current_price = self.prices_manager.get_snapshot_today(codigo_interno)
        historical_stats = self.prices_manager.get_historical_price_stats(codigo_interno)
        price_evolution = self.prices_manager.get_daily_price_evolution(codigo_interno)
        
        return {
            'product_info': product.to_dict(),
            'current_price': current_price.to_dict() if current_price else None,
            'historical_stats': historical_stats,
            'price_evolution': price_evolution,
            'complete_info_retrieved_at': datetime.now().isoformat()
        }
    
    def search_products(self, query: str = None, retailer: str = None, 
                       categoria: str = None, marca: str = None) -> List[Dict[str, Any]]:
        """Búsqueda de productos en el master"""
        
        products = []
        
        if retailer:
            products = self.products_manager.get_products_by_retailer(retailer)
        elif categoria:
            products = self.products_manager.get_products_by_categoria(categoria)
        else:
            # Búsqueda general (necesitaría implementar full-text search)
            # Por ahora retornar todos los activos
            self.products_manager._load_cache()
            products = [p for p in self.products_manager._products_cache.values() if p.activo]
        
        # Filtros adicionales
        if marca:
            products = [p for p in products if marca.lower() in p.marca.lower()]
        
        if query:
            products = [p for p in products if query.lower() in p.nombre.lower()]
        
        # Convertir a dict y agregar precio actual
        results = []
        for product in products[:50]:  # Limitar a 50 resultados
            product_dict = product.to_dict()
            
            # Agregar precio actual
            current_price = self.prices_manager.get_snapshot_today(product.codigo_interno)
            if current_price:
                product_dict['precio_actual'] = current_price.precio_min_dia
                product_dict['ultimo_cambio'] = current_price.timestamp_ultima_actualizacion.isoformat()
            
            results.append(product_dict)
        
        return results
    
    def get_daily_alerts_summary(self, target_date: date = None) -> Dict[str, Any]:
        """Obtener resumen de alertas del día"""
        if not target_date:
            target_date = date.today()
        
        try:
            import duckdb
            conn = duckdb.connect(str(self.prices_manager.duckdb_path))
            
            # Estadísticas de alertas del día
            query = """
            SELECT 
                COUNT(*) as total_snapshots,
                SUM(alertas_enviadas) as total_alerts_sent,
                SUM(CASE WHEN cambio_porcentaje <= -10.0 THEN 1 ELSE 0 END) as price_drops,
                SUM(CASE WHEN cambio_porcentaje <= -15.0 THEN 1 ELSE 0 END) as flash_sales,
                SUM(CASE WHEN cambio_porcentaje >= 15.0 THEN 1 ELSE 0 END) as price_increases,
                AVG(ABS(cambio_porcentaje)) as avg_price_change,
                SUM(cambios_en_dia) as total_price_changes
            FROM master_precios 
            WHERE fecha = ?
            """
            
            result = conn.execute(query, [target_date.isoformat()]).fetchone()
            conn.close()
            
            if result:
                return {
                    'date': target_date.isoformat(),
                    'total_snapshots': int(result[0] or 0),
                    'total_alerts_sent': int(result[1] or 0),
                    'price_drops': int(result[2] or 0),
                    'flash_sales': int(result[3] or 0),
                    'price_increases': int(result[4] or 0),
                    'avg_price_change_pct': float(result[5] or 0),
                    'total_price_changes': int(result[6] or 0)
                }
            
            return {'date': target_date.isoformat(), 'no_data': True}
            
        except Exception as e:
            logger.error(f"Error getting alerts summary: {e}")
            return {'error': str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas del sistema"""
        
        products_stats = self.products_manager.get_stats()
        prices_stats = self.prices_manager.get_stats()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'products': products_stats,
            'prices': prices_stats,
            'system': {
                'scheduler_running': self.running,
                'scheduler_thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False,
                'base_path': str(self.base_path),
                'next_midnight_closure': '00:00 daily'
            }
        }
    
    async def manual_midnight_closure(self):
        """Ejecutar cierre de medianoche manualmente (para testing)"""
        logger.info("Manual midnight closure initiated")
        await self.prices_manager.midnight_closure()
        self.products_manager.save_to_storage()
        logger.info("Manual midnight closure completed")
    
    async def shutdown(self):
        """Apagar sistema limpiamente (async)"""
        logger.info("Shutting down Integrated Master System...")

        # Detener scheduler
        self.running = False

        # Guardar cambios pendientes sin romper el event loop
        try:
            await self._save_all_changes()
        except Exception as e:
            logger.warning(f"Could not save pending changes during shutdown: {e}")
        
        logger.info("Integrated Master System shutdown completed")
    
    # Context manager support
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Funciones helper para integración con scrapers existentes

async def integrate_with_existing_scraper(scraper_results: List[Dict[str, Any]], 
                                        system: IntegratedMasterSystem) -> Dict[str, Any]:
    """
    Función helper para integrar con scrapers existentes
    
    Args:
        scraper_results: Resultados del scraper (formato actual)
        system: Sistema integrado
        
    Returns:
        Estadísticas de procesamiento
    """
    
    # Normalizar formato de datos si es necesario
    normalized_results = []
    for item in scraper_results:
        # Asegurar que tenemos los campos mínimos requeridos
        normalized_item = {
            'link': item.get('link', item.get('product_url', '')),
            'nombre': item.get('nombre', item.get('name', '')),
            'retailer': item.get('retailer', ''),
            'categoria': item.get('categoria', item.get('category', '')),
            'marca': item.get('marca', item.get('brand', '')),
            
            # Precios
            'precio_normal_num': item.get('precio_normal_num', 0),
            'precio_oferta_num': item.get('precio_oferta_num', 0),
            'precio_tarjeta_num': item.get('precio_tarjeta_num', 0),
        }
        
        # Agregar todos los demás campos tal como vienen
        for key, value in item.items():
            if key not in normalized_item:
                normalized_item[key] = value
        
        normalized_results.append(normalized_item)
    
    # Procesar con sistema integrado
    return await system.process_scraping_results(normalized_results)


def setup_system_for_24_7_scraping(base_path: str = "./data") -> IntegratedMasterSystem:
    """
    Setup completo del sistema para scraping 24/7
    
    Returns:
        Sistema configurado y listo para usar
    """
    
    system = IntegratedMasterSystem(base_path)
    
    # Inicializar solo estructuras básicas (no async para evitar loop conflicts)
    logger.info("System configured for 24/7 scraping")
    return system


# Script example de uso
if __name__ == "__main__":
    
    async def demo():
        """Demo del sistema integrado"""
        
        async with IntegratedMasterSystem("./data") as system:
            
            # Ejemplo de datos de scraping
            demo_scraping_data = [
                {
                    'link': 'https://www.ripley.cl/samsung-galaxy-s24-128gb',
                    'nombre': 'Samsung Galaxy S24 128GB Negro',
                    'retailer': 'ripley',
                    'categoria': 'smartphones',
                    'marca': 'Samsung',
                    'precio_normal_num': 899990,
                    'precio_oferta_num': 799990,
                    'precio_tarjeta_num': 749990,
                    'storage': '128GB',
                    'color': 'Negro'
                }
            ]
            
            # Procesar
            result = await system.process_scraping_results(demo_scraping_data)
            print("Processing result:", result)
            
            # Obtener estadísticas
            stats = system.get_system_stats()
            print("System stats:", stats)
    
    asyncio.run(demo())
