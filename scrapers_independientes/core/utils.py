# -*- coding: utf-8 -*-
"""
🛠️ Utilidades para Sistema de Scrapers Independiente V5
======================================================
Funciones de soporte y utilidades compartidas.
"""

import os
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from colorama import init, Fore, Style

# Inicializar colorama para Windows
init()

def setup_logging(log_file: str = None) -> logging.Logger:
    """🔧 Configurar logging con emojis y colores"""
    
    if not log_file:
        log_file = f"scrapers_independientes/resultados/scraping_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Crear logger
    logger = logging.getLogger('scrapers_system')
    logger.setLevel(logging.INFO)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter con emojis
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler para archivo
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️ Error creando archivo log: {e}")
    
    # Handler para consola con colores
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} | '
        f'%(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def load_config() -> Dict[str, Any]:
    """📄 Cargar configuración del sistema"""
    try:
        config_path = "scrapers_independientes/config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando config: {e}")
        return {}

def get_random_user_agent(config: Dict[str, Any]) -> str:
    """🎭 Obtener User Agent aleatorio"""
    user_agents = config.get('anti_deteccion', {}).get('user_agents', [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ])
    return random.choice(user_agents)

def get_random_delay(config: Dict[str, Any]) -> float:
    """⏱️ Obtener delay aleatorio"""
    min_delay = config.get('anti_deteccion', {}).get('delay_min', 2)
    max_delay = config.get('anti_deteccion', {}).get('delay_max', 5)
    return random.uniform(min_delay, max_delay)

def safe_sleep(delay: float, logger: logging.Logger = None):
    """😴 Sleep seguro con logging"""
    if logger:
        logger.info(f"😴 Esperando {delay:.1f}s...")
    time.sleep(delay)

def save_to_excel(data: List[Dict[str, Any]], filename: str, logger: logging.Logger = None) -> bool:
    """💾 Guardar datos a Excel"""
    try:
        if not data:
            if logger:
                logger.warning("⚠️ No hay datos para guardar")
            return False
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Asegurar directorio
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Guardar Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        if logger:
            logger.info(f"💾 Guardado: {filename} ({len(data)} productos)")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error guardando Excel: {e}")
        return False

def create_unified_report(all_results: Dict[str, List[Dict]], config: Dict, logger: logging.Logger = None):
    """📊 Crear reporte unificado"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Datos para reporte
        summary_data = []
        all_products = []
        
        for retailer, products in all_results.items():
            # Resumen por retailer
            summary_data.append({
                'Retailer': retailer.title(),
                'Productos': len(products),
                'Exitoso': 'Sí' if products else 'No',
                'Timestamp': timestamp
            })
            
            # Agregar productos con retailer
            for product in products:
                product_copy = product.copy()
                product_copy['Retailer'] = retailer.title()
                all_products.append(product_copy)
        
        # Guardar resumen
        summary_file = f"scrapers_independientes/resultados/resumen_scraping_{timestamp}.xlsx"
        with pd.ExcelWriter(summary_file, engine='openpyxl') as writer:
            # Hoja resumen
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja todos los productos
            if all_products:
                pd.DataFrame(all_products).to_excel(writer, sheet_name='Todos_Productos', index=False)
            
            # Hoja por retailer
            for retailer, products in all_results.items():
                if products:
                    sheet_name = retailer.title()[:31]  # Límite Excel
                    pd.DataFrame(products).to_excel(writer, sheet_name=sheet_name, index=False)
        
        if logger:
            logger.info(f"📊 Reporte unificado: {summary_file}")
            logger.info(f"📈 Total productos: {len(all_products)}")
        
        return summary_file
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error creando reporte: {e}")
        return None

def print_banner():
    """🎨 Mostrar banner del sistema"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🚀 SISTEMA SCRAPERS INDEPENDIENTE V5               ║
║                                                              ║
║  📱 Retailers: Falabella • Paris • Ripley • Hites           ║
║              • AbcDin • MercadoLibre                        ║
║                                                              ║
║  ✨ Características:                                         ║
║     • Anti-detección avanzada                               ║
║     • Soporte emojis 😊                                     ║
║     • Exportación Excel automática                          ║
║     • Sistema completamente independiente                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_results_summary(results: Dict[str, List[Dict]], logger: logging.Logger = None):
    """📋 Mostrar resumen de resultados"""
    
    print(f"\n{Fore.GREEN}📋 RESUMEN DE RESULTADOS:{Style.RESET_ALL}")
    print("=" * 50)
    
    total_products = 0
    successful_scrapers = 0
    
    for retailer, products in results.items():
        count = len(products)
        total_products += count
        
        if count > 0:
            successful_scrapers += 1
            status = f"{Fore.GREEN}✅ {count} productos{Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}❌ Sin datos{Style.RESET_ALL}"
        
        print(f"{retailer.title():15} | {status}")
        
        if logger:
            logger.info(f"📊 {retailer}: {count} productos")
    
    print("=" * 50)
    print(f"Total: {Fore.CYAN}{total_products} productos{Style.RESET_ALL} de {successful_scrapers}/6 retailers")
    
    if logger:
        logger.info(f"🎯 Resumen final: {total_products} productos de {successful_scrapers}/6 retailers")

def validate_config(config: Dict[str, Any]) -> bool:
    """✅ Validar configuración"""
    required_keys = ['sistema', 'anti_deteccion', 'retailers']
    
    for key in required_keys:
        if key not in config:
            print(f"❌ Configuración incompleta: falta '{key}'")
            return False
    
    # Verificar retailers activos
    active_retailers = [
        name for name, conf in config['retailers'].items() 
        if conf.get('activo', False)
    ]
    
    if not active_retailers:
        print("❌ No hay retailers activos en la configuración")
        return False
    
    print(f"✅ Configuración válida: {len(active_retailers)} retailers activos")
    return True

def get_output_filename(retailer: str) -> str:
    """📄 Generar nombre de archivo de salida"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"scrapers_independientes/resultados/{retailer}_productos_{timestamp}.xlsx"

def clean_text(text: str) -> str:
    """🧹 Limpiar texto extraído"""
    if not text:
        return ""
    
    # Remover espacios extra, saltos de línea, etc.
    cleaned = " ".join(text.strip().split())
    
    # Remover caracteres especiales problemáticos
    cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return cleaned[:500]  # Limitar longitud

def extract_price_number(price_text: str) -> Optional[int]:
    """💰 Extraer número de precio"""
    if not price_text:
        return None
    
    # Remover caracteres no numéricos excepto punto y coma
    import re
    numbers = re.findall(r'[\d.,]+', price_text)
    
    if not numbers:
        return None
    
    # Tomar el primer número encontrado
    price_str = numbers[0].replace('.', '').replace(',', '')
    
    try:
        return int(price_str)
    except ValueError:
        return None

def format_currency(amount: int) -> str:
    """💲 Formatear moneda"""
    if not amount:
        return "$0"
    
    return f"${amount:,}".replace(',', '.')