# -*- coding: utf-8 -*-
"""
📦 Sistema de Respaldo Parquet
==============================

Sistema para guardar datos crudos de scrapers en archivos Parquet
organizados por retailer y fecha para respaldo completo.

Estructura:
data/parquet/
├── falabella/
│   ├── 2025-09-03/
│   │   ├── smartphones_20250903_143022.parquet
│   │   ├── laptops_20250903_144511.parquet
│   │   └── metadata_20250903.json
│   └── 2025-09-04/
├── ripley/
└── paris/

Features:
- 🗂️ Organización por retailer/fecha/categoría
- 📊 Formato Parquet optimizado para analytics
- 🔄 Compresión automática (snappy)
- 📝 Metadata completa en JSON
- 🧹 Limpieza automática de archivos antiguos
- 📈 Estadísticas de respaldo
"""

import os
import json
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import hashlib
import gzip

try:
    from core.logging_config import get_system_logger
    logger = get_system_logger("parquet_backup")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("parquet_backup")

@dataclass
class BackupMetadata:
    """Metadata del respaldo"""
    retailer: str
    category: str
    timestamp: datetime
    products_count: int
    file_size_mb: float
    file_path: str
    scraping_session_id: str
    source_urls: List[str]
    execution_time_seconds: float
    success_rate: float
    errors: List[str]
    warnings: List[str]
    schema_version: str = "1.0"

class ParquetBackupSystem:
    """
    Sistema de respaldo en Parquet para scrapers V5
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """Inicializar sistema de respaldo Parquet"""
        self.base_path = Path(base_path) if base_path else Path("data/parquet")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Configuración
        self.compression = 'snappy'
        self.max_file_size_mb = 100  # Dividir archivos grandes
        self.max_age_days = 30       # Mantener respaldos por 30 días
        
        logger.info(f"📦 ParquetBackupSystem inicializado en: {self.base_path}")
    
    def _get_retailer_path(self, retailer: str, date: Optional[datetime] = None) -> Path:
        """Obtener ruta del retailer para una fecha específica"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        retailer_path = self.base_path / retailer / date_str
        retailer_path.mkdir(parents=True, exist_ok=True)
        
        return retailer_path
    
    def _generate_filename(self, retailer: str, category: str, timestamp: datetime) -> str:
        """Generar nombre único para el archivo Parquet"""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{category}_{timestamp_str}.parquet"
    
    def _prepare_dataframe(self, products: List[Dict[str, Any]]) -> pd.DataFrame:
        """Preparar DataFrame para Parquet con tipos optimizados"""
        if not products:
            return pd.DataFrame()
        
        df = pd.DataFrame(products)
        
        # Optimizar tipos de datos para Parquet
        for col in df.columns:
            if df[col].dtype == 'object':
                # Intentar convertir strings numéricas
                if col in ['precio_normal', 'precio_oferta', 'precio_tarjeta', 'reviews_count']:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                elif col == 'rating':
                    df[col] = pd.to_numeric(df[col], errors='ignore', downcast='float')
                elif col in ['out_of_stock', 'is_sponsored', 'is_promoted']:
                    df[col] = df[col].astype('boolean')
                else:
                    # Mantener como string pero optimizar
                    df[col] = df[col].astype('string')
        
        # Agregar columnas técnicas
        df['backup_timestamp'] = datetime.now()
        df['backup_id'] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        
        return df
    
    def save_scraped_data(self, 
                         retailer: str,
                         category: str,
                         products: List[Dict[str, Any]],
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Guardar datos scrapeados en Parquet
        
        Args:
            retailer: Nombre del retailer (falabella, ripley, etc.)
            category: Categoría de productos (smartphones, laptops, etc.) 
            products: Lista de productos scrapeados
            metadata: Metadata adicional del scraping
            
        Returns:
            Información del respaldo creado
        """
        timestamp = datetime.now()
        
        try:
            # Preparar datos
            df = self._prepare_dataframe(products)
            
            if df.empty:
                logger.warning(f"⚠️ No hay productos para respaldar: {retailer}/{category}")
                return {"success": False, "error": "No products to backup"}
            
            # Generar rutas
            retailer_path = self._get_retailer_path(retailer, timestamp)
            filename = self._generate_filename(retailer, category, timestamp)
            file_path = retailer_path / filename
            
            # Guardar en Parquet con compresión
            table = pa.Table.from_pandas(df)
            pq.write_table(
                table, 
                file_path,
                compression=self.compression,
                use_dictionary=True,  # Optimizar strings repetidos
                write_statistics=True
            )
            
            # Calcular estadísticas
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            products_count = len(products)
            
            # Crear metadata del respaldo
            backup_metadata = BackupMetadata(
                retailer=retailer,
                category=category,
                timestamp=timestamp,
                products_count=products_count,
                file_size_mb=file_size_mb,
                file_path=str(file_path),
                scraping_session_id=metadata.get('session_id', '') if metadata else '',
                source_urls=metadata.get('source_urls', []) if metadata else [],
                execution_time_seconds=metadata.get('execution_time', 0.0) if metadata else 0.0,
                success_rate=metadata.get('success_rate', 1.0) if metadata else 1.0,
                errors=metadata.get('errors', []) if metadata else [],
                warnings=metadata.get('warnings', []) if metadata else []
            )
            
            # Guardar metadata en JSON
            metadata_file = retailer_path / f"metadata_{timestamp.strftime('%Y%m%d')}.json"
            self._append_metadata(metadata_file, backup_metadata)
            
            logger.info(f"📦 Respaldo guardado: {file_path}")
            logger.info(f"📊 {products_count} productos, {file_size_mb:.2f}MB")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "products_count": products_count,
                "file_size_mb": file_size_mb,
                "retailer": retailer,
                "category": category,
                "timestamp": timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error guardando respaldo Parquet: {e}")
            return {"success": False, "error": str(e)}
    
    def _append_metadata(self, metadata_file: Path, backup_metadata: BackupMetadata):
        """Agregar metadata al archivo JSON diario"""
        try:
            # Leer metadata existente
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    daily_metadata = json.load(f)
            else:
                daily_metadata = {
                    "date": backup_metadata.timestamp.strftime("%Y-%m-%d"),
                    "retailer": backup_metadata.retailer,
                    "backups": []
                }
            
            # Agregar nuevo respaldo
            daily_metadata["backups"].append(asdict(backup_metadata))
            
            # Guardar metadata actualizada
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(daily_metadata, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            logger.warning(f"⚠️ Error guardando metadata: {e}")
    
    def read_backup(self, file_path: str) -> pd.DataFrame:
        """Leer respaldo Parquet"""
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"📖 Respaldo leído: {file_path} ({len(df)} productos)")
            return df
        except Exception as e:
            logger.error(f"❌ Error leyendo respaldo: {e}")
            return pd.DataFrame()
    
    def list_backups(self, retailer: str = None, days_back: int = 7) -> List[Dict[str, Any]]:
        """Listar respaldos disponibles"""
        backups = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            if retailer:
                retailers = [retailer]
            else:
                retailers = [d.name for d in self.base_path.iterdir() if d.is_dir()]
            
            for retailer_name in retailers:
                retailer_path = self.base_path / retailer_name
                if not retailer_path.exists():
                    continue
                
                for date_dir in retailer_path.iterdir():
                    if not date_dir.is_dir():
                        continue
                    
                    try:
                        date_obj = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if date_obj < cutoff_date:
                            continue
                    except ValueError:
                        continue
                    
                    # Buscar archivos Parquet
                    for parquet_file in date_dir.glob("*.parquet"):
                        file_size = parquet_file.stat().st_size / (1024 * 1024)
                        backups.append({
                            "retailer": retailer_name,
                            "date": date_dir.name,
                            "file": parquet_file.name,
                            "path": str(parquet_file),
                            "size_mb": round(file_size, 2),
                            "modified": datetime.fromtimestamp(parquet_file.stat().st_mtime)
                        })
            
            return sorted(backups, key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Error listando respaldos: {e}")
            return []
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de respaldos"""
        try:
            stats = {
                "total_retailers": 0,
                "total_files": 0,
                "total_size_mb": 0,
                "retailers": {},
                "oldest_backup": None,
                "newest_backup": None
            }
            
            if not self.base_path.exists():
                return stats
            
            oldest_time = None
            newest_time = None
            
            for retailer_dir in self.base_path.iterdir():
                if not retailer_dir.is_dir():
                    continue
                
                stats["total_retailers"] += 1
                retailer_stats = {"files": 0, "size_mb": 0, "dates": []}
                
                for date_dir in retailer_dir.iterdir():
                    if not date_dir.is_dir():
                        continue
                    
                    retailer_stats["dates"].append(date_dir.name)
                    
                    for parquet_file in date_dir.glob("*.parquet"):
                        file_size = parquet_file.stat().st_size / (1024 * 1024)
                        file_time = datetime.fromtimestamp(parquet_file.stat().st_mtime)
                        
                        retailer_stats["files"] += 1
                        retailer_stats["size_mb"] += file_size
                        stats["total_files"] += 1
                        stats["total_size_mb"] += file_size
                        
                        if oldest_time is None or file_time < oldest_time:
                            oldest_time = file_time
                            stats["oldest_backup"] = str(parquet_file)
                        
                        if newest_time is None or file_time > newest_time:
                            newest_time = file_time
                            stats["newest_backup"] = str(parquet_file)
                
                retailer_stats["size_mb"] = round(retailer_stats["size_mb"], 2)
                stats["retailers"][retailer_dir.name] = retailer_stats
            
            stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def cleanup_old_backups(self, max_age_days: Optional[int] = None) -> Dict[str, Any]:
        """Limpiar respaldos antiguos"""
        if max_age_days is None:
            max_age_days = self.max_age_days
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        try:
            deleted_files = []
            deleted_size_mb = 0
            
            for retailer_dir in self.base_path.iterdir():
                if not retailer_dir.is_dir():
                    continue
                
                for date_dir in retailer_dir.iterdir():
                    if not date_dir.is_dir():
                        continue
                    
                    try:
                        date_obj = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if date_obj < cutoff_date:
                            # Eliminar toda la carpeta de fecha antigua
                            total_size = sum(f.stat().st_size for f in date_dir.rglob('*') if f.is_file())
                            deleted_size_mb += total_size / (1024 * 1024)
                            
                            import shutil
                            shutil.rmtree(date_dir)
                            deleted_files.append(str(date_dir))
                            
                    except ValueError:
                        continue
            
            logger.info(f"🧹 Limpieza completada: {len(deleted_files)} carpetas eliminadas, {deleted_size_mb:.2f}MB liberados")
            
            return {
                "success": True,
                "deleted_folders": len(deleted_files),
                "freed_space_mb": round(deleted_size_mb, 2),
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
            return {"success": False, "error": str(e)}

# Instancia global del sistema
parquet_backup_system = ParquetBackupSystem()

def save_scraper_backup(retailer: str, category: str, products: List[Dict], metadata: Dict = None) -> Dict:
    """Función helper para guardar respaldo desde scrapers"""
    return parquet_backup_system.save_scraped_data(retailer, category, products, metadata)

def get_backup_stats() -> Dict:
    """Función helper para obtener estadísticas"""
    return parquet_backup_system.get_backup_stats()

def list_recent_backups(retailer: str = None, days: int = 7) -> List[Dict]:
    """Función helper para listar respaldos recientes"""
    return parquet_backup_system.list_backups(retailer, days)

if __name__ == "__main__":
    # Test del sistema
    print("🧪 Testing ParquetBackupSystem...")
    
    # Datos de prueba
    test_products = [
        {
            "nombre": "iPhone 15 Pro 128GB",
            "marca": "Apple",
            "precio_normal": 1299990,
            "precio_oferta": 1199990,
            "rating": 4.8,
            "reviews_count": 234,
            "link": "https://test.com/iphone15pro"
        },
        {
            "nombre": "Samsung Galaxy S24 256GB", 
            "marca": "Samsung",
            "precio_normal": 999990,
            "precio_oferta": 899990,
            "rating": 4.6,
            "reviews_count": 156,
            "link": "https://test.com/galaxys24"
        }
    ]
    
    test_metadata = {
        "session_id": "test_session_001",
        "source_urls": ["https://test.com"],
        "execution_time": 45.5,
        "success_rate": 1.0
    }
    
    # Guardar respaldo
    result = save_scraper_backup("test_retailer", "smartphones", test_products, test_metadata)
    print(f"📦 Resultado del respaldo: {result}")
    
    # Obtener estadísticas
    stats = get_backup_stats()
    print(f"📊 Estadísticas: {stats}")
    
    # Listar respaldos
    backups = list_recent_backups()
    print(f"📋 Respaldos recientes: {len(backups)}")