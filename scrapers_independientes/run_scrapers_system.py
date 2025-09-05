#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE SCRAPERS INDEPENDIENTE V5
=======================================
Ejecutor principal del sistema unificado de scrapers.

Uso:
    python run_scrapers_system.py

Características:
- ✅ 6 scrapers funcionando (Falabella, Paris, Ripley, Hites, AbcDin, MercadoLibre)
- ✅ Sistema completamente independiente
- ✅ Anti-detección avanzada
- ✅ Exportación automática a Excel
- ✅ Soporte emojis 😊
- ✅ Logs detallados
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import (
    setup_logging, load_config, print_banner, print_results_summary,
    validate_config, save_to_excel, create_unified_report, get_output_filename
)
from core.base_scraper import (
    FalabellaScraper, ParisScraper, RipleyScraper,
    HitesScraper, AbcDinScraper, MercadoLibreScraper
)

class ScrapersSystem:
    """🚀 Sistema principal de scrapers independiente"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging()
        self.scrapers_map = {
            'falabella': FalabellaScraper,
            'paris': ParisScraper,
            'ripley': RipleyScraper,
            'hites': HitesScraper,
            'abcdin': AbcDinScraper,
            'mercadolibre': MercadoLibreScraper
        }
        self.results: Dict[str, List[Dict[str, Any]]] = {}
    
    async def run_scraper(self, retailer_name: str) -> List[Dict[str, Any]]:
        """🕷️ Ejecutar scraper individual"""
        try:
            # Verificar si está activo
            retailer_config = self.config.get('retailers', {}).get(retailer_name, {})
            if not retailer_config.get('activo', False):
                self.logger.info(f"⏭️ {retailer_name.title()} desactivado en configuración")
                return []
            
            # Crear scraper
            scraper_class = self.scrapers_map.get(retailer_name)
            if not scraper_class:
                self.logger.error(f"❌ Scraper no encontrado: {retailer_name}")
                return []
            
            self.logger.info(f"🚀 Iniciando scraper: {retailer_name.title()}")
            
            # Ejecutar scraping
            scraper = scraper_class(self.config, self.logger)
            productos = await scraper.scrape()
            
            # Guardar resultados individuales
            if productos:
                filename = get_output_filename(retailer_name)
                if save_to_excel(productos, filename, self.logger):
                    self.logger.info(f"💾 {retailer_name.title()}: {len(productos)} productos guardados")
                else:
                    self.logger.warning(f"⚠️ Error guardando {retailer_name}")
            else:
                self.logger.warning(f"⚠️ {retailer_name.title()}: Sin productos extraídos")
            
            return productos
            
        except Exception as e:
            self.logger.error(f"❌ Error en scraper {retailer_name}: {e}")
            return []
    
    async def run_all_scrapers(self):
        """🔄 Ejecutar todos los scrapers"""
        try:
            self.logger.info("🚀 Iniciando sistema de scrapers...")
            
            # Obtener scrapers activos
            active_scrapers = [
                name for name, config in self.config.get('retailers', {}).items()
                if config.get('activo', False)
            ]
            
            if not active_scrapers:
                self.logger.error("❌ No hay scrapers activos")
                return
            
            self.logger.info(f"🎯 Scrapers activos: {', '.join(s.title() for s in active_scrapers)}")
            
            # Determinar si ejecutar en paralelo o secuencial
            max_workers = self.config.get('sistema', {}).get('max_workers', 1)
            
            if max_workers > 1:
                # Ejecución paralela (limitada)
                self.logger.info(f"⚡ Ejecución paralela: {max_workers} workers")
                await self.run_parallel_scrapers(active_scrapers, max_workers)
            else:
                # Ejecución secuencial (más segura)
                self.logger.info("🔄 Ejecución secuencial")
                await self.run_sequential_scrapers(active_scrapers)
            
            # Crear reporte unificado
            if self.config.get('sistema', {}).get('export_unified', True):
                unified_file = create_unified_report(self.results, self.config, self.logger)
                if unified_file:
                    self.logger.info(f"📊 Reporte unificado creado: {unified_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando sistema: {e}")
    
    async def run_sequential_scrapers(self, scrapers_list: List[str]):
        """🔄 Ejecución secuencial de scrapers"""
        for retailer in scrapers_list:
            try:
                self.logger.info(f"🎯 Procesando: {retailer.title()}")
                productos = await self.run_scraper(retailer)
                self.results[retailer] = productos
                
                # Delay entre scrapers
                if retailer != scrapers_list[-1]:  # No delay después del último
                    from core.utils import get_random_delay
                    delay = get_random_delay(self.config) * 2  # Delay más largo entre scrapers
                    self.logger.info(f"⏱️ Pausa entre scrapers: {delay:.1f}s")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"❌ Error ejecutando {retailer}: {e}")
                self.results[retailer] = []
    
    async def run_parallel_scrapers(self, scrapers_list: List[str], max_workers: int):
        """⚡ Ejecución paralela limitada de scrapers"""
        semaforo = asyncio.Semaphore(max_workers)
        
        async def run_with_semaphore(retailer):
            async with semaforo:
                productos = await self.run_scraper(retailer)
                self.results[retailer] = productos
                return retailer, productos
        
        # Ejecutar con concurrencia limitada
        tasks = [run_with_semaphore(retailer) for retailer in scrapers_list]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def print_final_summary(self):
        """📋 Mostrar resumen final"""
        self.logger.info("🏁 Scraping completado!")
        print_results_summary(self.results, self.logger)


async def main():
    """🚀 Función principal"""
    try:
        # Banner
        print_banner()
        
        # Cargar y validar configuración
        config = load_config()
        if not validate_config(config):
            print("❌ Error en configuración. Revisa config.json")
            return
        
        # Crear y ejecutar sistema
        sistema = ScrapersSystem()
        await sistema.run_all_scrapers()
        
        # Resumen final
        sistema.print_final_summary()
        
        print(f"\n🎉 ¡Sistema ejecutado exitosamente!")
        print(f"📁 Resultados en: scrapers_independientes/resultados/")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Sistema interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")


def run_single_scraper(retailer_name: str):
    """🎯 Ejecutar un solo scraper (función de conveniencia)"""
    async def single_run():
        config = load_config()
        logger = setup_logging()
        
        scrapers_map = {
            'falabella': FalabellaScraper,
            'paris': ParisScraper,
            'ripley': RipleyScraper,
            'hites': HitesScraper,
            'abcdin': AbcDinScraper,
            'mercadolibre': MercadoLibreScraper
        }
        
        scraper_class = scrapers_map.get(retailer_name.lower())
        if not scraper_class:
            print(f"❌ Scraper no válido: {retailer_name}")
            return
        
        print(f"🚀 Ejecutando scraper: {retailer_name.title()}")
        scraper = scraper_class(config, logger)
        productos = await scraper.scrape()
        
        if productos:
            filename = get_output_filename(retailer_name)
            save_to_excel(productos, filename, logger)
            print(f"✅ {len(productos)} productos guardados en {filename}")
        else:
            print("⚠️ No se extrajeron productos")
    
    asyncio.run(single_run())


if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) > 1:
        # Ejecutar scraper individual
        retailer = sys.argv[1].lower()
        valid_scrapers = ['falabella', 'paris', 'ripley', 'hites', 'abcdin', 'mercadolibre']
        
        if retailer in valid_scrapers:
            run_single_scraper(retailer)
        else:
            print(f"❌ Scraper no válido. Opciones: {', '.join(valid_scrapers)}")
            print(f"📋 Uso: python run_scrapers_system.py [scraper_name]")
            print(f"🚀 O ejecuta sin argumentos para correr todos los scrapers")
    else:
        # Ejecutar sistema completo
        asyncio.run(main())