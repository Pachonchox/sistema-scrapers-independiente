# -*- coding: utf-8 -*-
"""
🗂️ Sistema de Logging Centralizado
==================================

Configuración unificada de logging para todo el sistema:
- Master Prices System
- V5 Arbitrage System  
- Alerts Bot
- Scrapers
- Scripts de análisis

Organiza logs por categoría y rotación automática.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Configuración de paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Asegurar que existan las carpetas de logs
LOGS_CATEGORIES = {
    "system": LOGS_DIR / "system",
    "alerts": LOGS_DIR / "alerts", 
    "scraping": LOGS_DIR / "scraping",
    "arbitrage": LOGS_DIR / "arbitrage",
    "analysis": LOGS_DIR / "analysis",
    "tests": LOGS_DIR / "tests",
    "debug": LOGS_DIR / "debug"
}

for category, path in LOGS_CATEGORIES.items():
    path.mkdir(parents=True, exist_ok=True)

class EmojiFormatter(logging.Formatter):
    """Formatter que agrega emojis a los logs según el nivel"""
    
    EMOJI_MAP = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨"
    }
    
    def format(self, record):
        # Agregar emoji según el nivel
        emoji = self.EMOJI_MAP.get(record.levelno, "📝")
        record.emoji = emoji
        
        # Formato con emoji
        original_format = self._style._fmt
        self._style._fmt = f"{emoji} {original_format}"
        
        result = super().format(record)
        
        # Restaurar formato original
        self._style._fmt = original_format
        
        return result

def setup_logger(name: str, category: str = "system", level: int = logging.INFO,
                include_console: bool = True, max_bytes: int = 10*1024*1024,
                backup_count: int = 5) -> logging.Logger:
    """
    Configurar logger con rotación de archivos y formato con emojis
    
    Args:
        name: Nombre del logger (ej: "master_prices", "v5_arbitrage")
        category: Categoría del log (system, alerts, scraping, arbitrage, etc.)
        level: Nivel de logging
        include_console: Si incluir output a consola
        max_bytes: Tamaño máximo del archivo antes de rotar (10MB default)
        backup_count: Número de archivos de backup a mantener
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Path del archivo de log
    log_dir = LOGS_CATEGORIES.get(category, LOGS_CATEGORIES["system"])
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"{name}_{timestamp}.log"
    
    # Handler para archivo con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Handler para consola (opcional)
    if include_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Formato con emojis para consola
        console_formatter = EmojiFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Formato para archivo (sin emojis para compatibilidad)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_system_logger(name: str) -> logging.Logger:
    """Logger para componentes del sistema"""
    return setup_logger(name, "system", logging.INFO)

def get_alerts_logger(name: str) -> logging.Logger:
    """Logger para sistema de alertas"""
    return setup_logger(name, "alerts", logging.INFO)

def get_scraping_logger(name: str) -> logging.Logger:
    """Logger para scrapers"""
    return setup_logger(name, "scraping", logging.INFO)

def get_arbitrage_logger(name: str) -> logging.Logger:
    """Logger para sistema de arbitraje"""
    return setup_logger(name, "arbitrage", logging.INFO)

def get_analysis_logger(name: str) -> logging.Logger:
    """Logger para scripts de análisis"""
    return setup_logger(name, "analysis", logging.INFO)

def get_test_logger(name: str) -> logging.Logger:
    """Logger para tests"""
    return setup_logger(name, "tests", logging.DEBUG, max_bytes=5*1024*1024)

def get_debug_logger(name: str) -> logging.Logger:
    """Logger para debug con nivel DEBUG"""
    return setup_logger(name, "debug", logging.DEBUG, max_bytes=20*1024*1024)

def configure_alerts_bridge_logging():
    """Configuración específica para el alerts bridge"""
    return get_alerts_logger("alerts_bridge")

def configure_master_prices_logging():
    """Configuración específica para master prices"""
    return get_system_logger("master_prices")

def configure_v5_arbitrage_logging():
    """Configuración específica para V5 arbitrage"""
    return get_arbitrage_logger("v5_arbitrage")

def configure_telegram_bot_logging():
    """Configuración específica para telegram bot"""
    return get_alerts_logger("telegram_bot")

def log_system_startup(logger: logging.Logger, component: str, version: str = "1.0.0"):
    """Log estándar de inicio de componente"""
    logger.info("=" * 60)
    logger.info(f"🚀 INICIANDO {component.upper()}")
    logger.info("=" * 60)
    logger.info(f"📦 Versión: {version}")
    logger.info(f"📁 Logs: {logger.handlers[1].baseFilename if len(logger.handlers) > 1 else 'console only'}")
    logger.info(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

def log_system_shutdown(logger: logging.Logger, component: str):
    """Log estándar de cierre de componente"""
    logger.info("=" * 60)
    logger.info(f"🛑 CERRANDO {component.upper()}")
    logger.info(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

def cleanup_old_logs(days_to_keep: int = 30):
    """
    Limpiar logs antiguos para evitar acumulación excesiva
    
    Args:
        days_to_keep: Días de logs a mantener
    """
    import time
    from pathlib import Path
    
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    cleaned_count = 0
    
    for category_path in LOGS_CATEGORIES.values():
        if not category_path.exists():
            continue
            
        for log_file in category_path.rglob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except OSError:
                    pass
    
    if cleaned_count > 0:
        logger = get_system_logger("log_cleanup")
        logger.info(f"🧹 Limpieza de logs completada: {cleaned_count} archivos eliminados")

def get_logs_status() -> Dict[str, Any]:
    """
    Obtener estado de los logs del sistema
    
    Returns:
        Diccionario con información de logs
    """
    status = {
        "logs_dir": str(LOGS_DIR),
        "categories": {},
        "total_size_mb": 0,
        "total_files": 0
    }
    
    for category, path in LOGS_CATEGORIES.items():
        if not path.exists():
            continue
            
        category_info = {
            "path": str(path),
            "files": 0,
            "size_mb": 0,
            "latest_log": None
        }
        
        latest_time = 0
        for log_file in path.rglob("*.log*"):
            category_info["files"] += 1
            file_size = log_file.stat().st_size
            category_info["size_mb"] += file_size / (1024 * 1024)
            
            if log_file.stat().st_mtime > latest_time:
                latest_time = log_file.stat().st_mtime
                category_info["latest_log"] = log_file.name
        
        status["categories"][category] = category_info
        status["total_size_mb"] += category_info["size_mb"]
        status["total_files"] += category_info["files"]
    
    return status

# Configuración por defecto del proyecto
def setup_project_logging():
    """Configurar logging para todo el proyecto"""
    
    # Crear logger principal del proyecto
    main_logger = get_system_logger("orchestrator_v5")
    log_system_startup(main_logger, "Sistema Orchestrator V5", "5.0.0")
    
    # Configurar logging para componentes principales
    configure_alerts_bridge_logging()
    configure_master_prices_logging()
    configure_v5_arbitrage_logging()
    configure_telegram_bot_logging()
    
    main_logger.info("📊 Sistema de logging centralizado configurado")
    
    # Mostrar estado inicial
    status = get_logs_status()
    main_logger.info(f"📁 Logs dir: {status['logs_dir']}")
    main_logger.info(f"📦 Categorías: {len(status['categories'])}")
    main_logger.info(f"💾 Archivos totales: {status['total_files']}")
    main_logger.info(f"📏 Tamaño total: {status['total_size_mb']:.1f} MB")
    
    return main_logger

if __name__ == "__main__":
    # Test del sistema de logging
    print("🧪 Testing logging system...")
    
    main_logger = setup_project_logging()
    
    # Test de diferentes tipos de log
    test_logger = get_debug_logger("test_logging")
    test_logger.debug("Test debug message")
    test_logger.info("Test info message")
    test_logger.warning("Test warning message") 
    test_logger.error("Test error message")
    
    # Test de status
    status = get_logs_status()
    print(f"✅ Logging system configured")
    print(f"📁 Logs directory: {status['logs_dir']}")
    print(f"📊 Categories: {list(status['categories'].keys())}")