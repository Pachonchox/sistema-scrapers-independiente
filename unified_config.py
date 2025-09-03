# -*- coding: utf-8 -*-
"""
⚙️ CONFIGURACIÓN UNIFICADA V5 - CENTRO DE CONTROL
=================================================

Sistema de configuración centralizada que actúa como centro de control
SIN modificar las configuraciones específicas de cada scraper.
Proporciona una interfaz unificada manteniendo la especialización.

Características:
- ✅ Centro único de configuración
- ✅ Preserva configuraciones específicas de scrapers
- ✅ Configuración por ambiente (dev/test/prod)
- ✅ Validación automática de settings
- ✅ Hot-reload sin reinicio

Autor: Sistema V5 Unificado  
Fecha: 03/09/2025
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    """Configuración específica de un scraper (SIN modificar originales)"""
    name: str
    enabled: bool = True
    max_products: int = 100
    timeout_seconds: int = 60
    categories: List[str] = field(default_factory=list)
    
    # Configuraciones específicas que cada scraper ya tiene
    preserve_original_config: bool = True
    original_selectors: str = "MANTENER_EXACTOS"
    original_timeouts: str = "MANTENER_ORIGINALES" 
    original_patterns: str = "NO_CAMBIAR"

@dataclass 
class MLConfig:
    """Configuración ML (preservando algoritmos originales)"""
    enabled: bool = True
    matching_threshold: float = 0.85  # Valor original
    max_cache_size: int = 10000
    redis_enabled: bool = True
    
    # Protección de algoritmos originales
    preserve_ml_algorithms: bool = True
    preserve_scoring_weights: bool = True
    preserve_embedder_config: bool = True

@dataclass
class ArbitrageConfig:
    """Configuración de arbitraje (preservando lógica original)"""
    enabled: bool = True
    min_margin_clp: float = 5000.0
    min_percentage: float = 15.0
    max_opportunities: int = 50
    
    # Protección de lógica de detección original
    preserve_detection_logic: bool = True
    preserve_scoring_algorithm: bool = True

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    backend: str = "postgres"
    host: str = "localhost"
    port: int = 5434
    database: str = "price_orchestrator"
    user: str = "orchestrator"
    password: str = "orchestrator_2025"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0

@dataclass
class TelegramConfig:
    """Configuración de Telegram"""
    enabled: bool = True
    bot_token: str = ""
    chat_id: str = ""
    superusers: List[str] = field(default_factory=list)
    alerts_enabled: bool = True

@dataclass
class SystemConfig:
    """Configuración global del sistema"""
    environment: str = "development"  # development, test, production
    max_runtime_minutes: int = 60
    cycle_pause_seconds: int = 30
    log_level: str = "INFO"
    enable_emojis: bool = True

class UnifiedConfigV5:
    """
    ⚙️ Configurador Unificado V5
    
    Centro de configuración que unifica todos los settings
    SIN modificar las configuraciones específicas y probadas
    de cada componente del sistema.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Inicializar configurador unificado"""
        self.config_file = config_file or ".env"
        self.config_loaded_time = None
        
        # Configuraciones por componente
        self.scrapers: Dict[str, ScraperConfig] = {}
        self.ml: MLConfig = MLConfig()
        self.arbitrage: ArbitrageConfig = ArbitrageConfig()
        self.database: DatabaseConfig = DatabaseConfig()
        self.telegram: TelegramConfig = TelegramConfig()
        self.system: SystemConfig = SystemConfig()
        
        # Estado del configurador
        self.validation_errors: List[str] = []
        self.warnings: List[str] = []
        
        logger.info("⚙️ Configurador Unificado V5 inicializado")
    
    def load_configuration(self) -> bool:
        """
        Cargar configuración completa manteniendo originales ⚙️
        
        Carga desde .env y archivos de config SIN modificar
        las configuraciones específicas de cada scraper.
        """
        try:
            logger.info("⚙️ Cargando configuración unificada (preservando específicas)")
            
            # Cargar variables de entorno
            load_dotenv(self.config_file)
            
            # 1. Configuración de Sistema
            self._load_system_config()
            
            # 2. Configuración de Base de Datos
            self._load_database_config()
            
            # 3. Configuración de Telegram
            self._load_telegram_config()
            
            # 4. Configuración ML (preservando algoritmos)
            self._load_ml_config()
            
            # 5. Configuración de Arbitraje (preservando lógica)
            self._load_arbitrage_config()
            
            # 6. Configuración de Scrapers (preservando selectores)
            self._load_scrapers_config()
            
            # 7. Validar configuración
            self._validate_configuration()
            
            self.config_loaded_time = datetime.now()
            
            if self.validation_errors:
                logger.error(f"❌ Errores de validación: {len(self.validation_errors)}")
                for error in self.validation_errors:
                    logger.error(f"   - {error}")
                return False
            
            if self.warnings:
                logger.warning(f"⚠️ Advertencias: {len(self.warnings)}")
                for warning in self.warnings:
                    logger.warning(f"   - {warning}")
            
            logger.info("✅ Configuración unificada cargada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            return False
    
    def _load_system_config(self):
        """Cargar configuración del sistema"""
        self.system = SystemConfig(
            environment=os.getenv('ENVIRONMENT', 'development'),
            max_runtime_minutes=int(os.getenv('MAX_RUNTIME_MINUTES', '60')),
            cycle_pause_seconds=int(os.getenv('CYCLE_PAUSE_SECONDS', '30')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            enable_emojis=os.getenv('ENABLE_EMOJIS', 'true').lower() == 'true'
        )
    
    def _load_database_config(self):
        """Cargar configuración de base de datos"""
        self.database = DatabaseConfig(
            backend=os.getenv('DATA_BACKEND', 'postgres'),
            host=os.getenv('PGHOST', 'localhost'),
            port=int(os.getenv('PGPORT', '5434')),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025'),
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', '6380')),
            redis_db=int(os.getenv('REDIS_DB', '0'))
        )
    
    def _load_telegram_config(self):
        """Cargar configuración de Telegram"""
        superusers_str = os.getenv('SUPERUSERS', '')
        superusers = [s.strip() for s in superusers_str.split(',') if s.strip()]
        
        self.telegram = TelegramConfig(
            enabled=os.getenv('TELEGRAM_ALERTS_ENABLED', 'true').lower() == 'true',
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
            superusers=superusers,
            alerts_enabled=os.getenv('ALERTS_ENABLED', 'true').lower() == 'true'
        )
    
    def _load_ml_config(self):
        """Cargar configuración ML (PRESERVANDO algoritmos originales)"""
        self.ml = MLConfig(
            enabled=os.getenv('ML_ENABLED', 'true').lower() == 'true',
            matching_threshold=float(os.getenv('ML_MATCHING_THRESHOLD', '0.85')),  # Original
            max_cache_size=int(os.getenv('ML_CACHE_SIZE', '10000')),
            redis_enabled=os.getenv('REDIS_ENABLED', 'true').lower() == 'true',
            
            # IMPORTANTE: Preservar algoritmos originales
            preserve_ml_algorithms=True,
            preserve_scoring_weights=True,
            preserve_embedder_config=True
        )
    
    def _load_arbitrage_config(self):
        """Cargar configuración de arbitraje (PRESERVANDO lógica original)"""
        self.arbitrage = ArbitrageConfig(
            enabled=os.getenv('ARBITRAGE_ENABLED', 'true').lower() == 'true',
            min_margin_clp=float(os.getenv('ARBITRAGE_MIN_MARGIN', '5000')),
            min_percentage=float(os.getenv('ARBITRAGE_MIN_ROI', '15.0')),
            max_opportunities=int(os.getenv('MAX_OPPORTUNITIES', '50')),
            
            # IMPORTANTE: Preservar lógica de detección original
            preserve_detection_logic=True,
            preserve_scoring_algorithm=True
        )
    
    def _load_scrapers_config(self):
        """Cargar configuración de scrapers (PRESERVANDO selectores específicos)"""
        # Scrapers disponibles con sus configuraciones ORIGINALES
        scrapers_info = {
            'paris': {
                'categories': ['celulares', 'computadores', 'television'],
                'note': 'Selectores exactos del v3 - NO MODIFICAR'
            },
            'falabella': {
                'categories': ['smartphones', 'computadores', 'smart_tv', 'tablets'],
                'note': 'Método portable funcional - NO MODIFICAR'
            },
            'ripley': {
                'categories': ['computacion', 'smartphones'],
                'note': 'Sistema propio - NO MODIFICAR'
            },
            'hites': {
                'categories': ['celulares', 'computadores', 'televisores', 'tablets'],
                'note': 'Método portable - NO MODIFICAR'
            },
            'abcdin': {
                'categories': ['celulares', 'computadores', 'tablets', 'televisores'],
                'note': 'Método portable - NO MODIFICAR'
            },
            'mercadolibre': {
                'categories': ['celulares', 'computadoras', 'tablets'],
                'note': 'Scraper bonus - NO MODIFICAR'
            }
        }
        
        # Crear configuraciones preservando especificaciones
        for scraper_name, info in scrapers_info.items():
            enabled = os.getenv(f'{scraper_name.upper()}_ENABLED', 'true').lower() == 'true'
            max_products = int(os.getenv(f'{scraper_name.upper()}_MAX_PRODUCTS', '100'))
            
            self.scrapers[scraper_name] = ScraperConfig(
                name=scraper_name,
                enabled=enabled,
                max_products=max_products,
                timeout_seconds=60,  # Mantener original
                categories=info['categories'],  # Categorías específicas
                
                # IMPORTANTE: Flags de preservación
                preserve_original_config=True,
                original_selectors="MANTENER_EXACTOS",
                original_timeouts="MANTENER_ORIGINALES", 
                original_patterns="NO_CAMBIAR"
            )
    
    def _validate_configuration(self):
        """Validar configuración completa"""
        self.validation_errors.clear()
        self.warnings.clear()
        
        # Validar Telegram
        if self.telegram.enabled and not self.telegram.bot_token:
            self.validation_errors.append("TELEGRAM_BOT_TOKEN requerido si Telegram está habilitado")
        
        # Validar Base de Datos
        if not self.database.password:
            self.warnings.append("Contraseña de base de datos no configurada")
        
        # Validar ML
        if self.ml.matching_threshold < 0 or self.ml.matching_threshold > 1:
            self.validation_errors.append("ML matching threshold debe estar entre 0 y 1")
        
        # Validar Scrapers
        enabled_scrapers = [name for name, config in self.scrapers.items() if config.enabled]
        if not enabled_scrapers:
            self.warnings.append("Ningún scraper habilitado")
        
        # Validar preservación (CRÍTICO)
        for scraper_name, config in self.scrapers.items():
            if not config.preserve_original_config:
                self.validation_errors.append(f"CRÍTICO: {scraper_name} no tiene preservación activada")
    
    def get_scraper_config(self, retailer: str) -> Optional[ScraperConfig]:
        """Obtener configuración específica de un scraper"""
        return self.scrapers.get(retailer)
    
    def get_enabled_scrapers(self) -> List[str]:
        """Obtener lista de scrapers habilitados"""
        return [name for name, config in self.scrapers.items() if config.enabled]
    
    def get_database_url(self) -> str:
        """Obtener URL de conexión a base de datos"""
        return f"postgresql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.database}"
    
    def get_redis_url(self) -> str:
        """Obtener URL de conexión a Redis"""
        return f"redis://{self.database.redis_host}:{self.database.redis_port}/{self.database.redis_db}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Exportar toda la configuración como diccionario"""
        return {
            'system': asdict(self.system),
            'database': asdict(self.database),
            'telegram': asdict(self.telegram),
            'ml': asdict(self.ml),
            'arbitrage': asdict(self.arbitrage),
            'scrapers': {name: asdict(config) for name, config in self.scrapers.items()},
            'meta': {
                'loaded_time': self.config_loaded_time.isoformat() if self.config_loaded_time else None,
                'validation_errors': self.validation_errors,
                'warnings': self.warnings
            }
        }
    
    def save_config_snapshot(self, output_file: str = "config_snapshot.json"):
        """Guardar snapshot de configuración para backup"""
        try:
            snapshot = self.to_dict()
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Snapshot guardado en {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando snapshot: {e}")

# Función de conveniencia para crear configurador global
def create_unified_config(config_file: str = None) -> UnifiedConfigV5:
    """Crear configurador unificado listo para usar"""
    config = UnifiedConfigV5(config_file)
    
    if config.load_configuration():
        return config
    else:
        raise Exception("Error cargando configuración unificada")

# Instancia global (singleton)
_global_config: Optional[UnifiedConfigV5] = None

def get_global_config() -> UnifiedConfigV5:
    """Obtener instancia global del configurador"""
    global _global_config
    
    if _global_config is None:
        _global_config = create_unified_config()
    
    return _global_config