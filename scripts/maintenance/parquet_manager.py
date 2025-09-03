# -*- coding: utf-8 -*-
"""
🗄️ Parquet Manager - Utilidades de Gestión
==========================================

Script de utilidades para gestionar los respaldos Parquet:
- Ver estadísticas de respaldos
- Listar archivos por retailer/fecha
- Limpiar archivos antiguos
- Convertir Parquet a CSV/Excel
- Análisis de datos respaldados
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from core.logging_config import get_system_logger
    from core.parquet_backup_system import ParquetBackupSystem, get_backup_stats, list_recent_backups
    logger = get_system_logger("parquet_manager")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("parquet_manager")

class ParquetManager:
    """Manager para operaciones con respaldos Parquet"""
    
    def __init__(self):
        self.system = ParquetBackupSystem()
    
    def show_stats(self):
        """Mostrar estadísticas de respaldos"""
        logger.info("📊 ESTADÍSTICAS DE RESPALDOS PARQUET")
        logger.info("=" * 50)
        
        stats = get_backup_stats()
        
        if "error" in stats:
            logger.error(f"❌ Error: {stats['error']}")
            return
        
        logger.info(f"🏪 Total retailers: {stats['total_retailers']}")
        logger.info(f"📁 Total archivos: {stats['total_files']}")
        logger.info(f"💾 Tamaño total: {stats['total_size_mb']:.2f} MB")
        
        if stats.get('oldest_backup'):
            logger.info(f"📅 Respaldo más antiguo: {stats['oldest_backup']}")
        
        if stats.get('newest_backup'):
            logger.info(f"📅 Respaldo más reciente: {stats['newest_backup']}")
        
        logger.info("\n🏪 DETALLES POR RETAILER:")
        for retailer, retailer_stats in stats['retailers'].items():
            logger.info(f"  {retailer}:")
            logger.info(f"    📁 Archivos: {retailer_stats['files']}")
            logger.info(f"    💾 Tamaño: {retailer_stats['size_mb']:.2f} MB")
            logger.info(f"    📅 Fechas: {len(retailer_stats['dates'])} días")
    
    def list_backups(self, retailer=None, days=7):
        """Listar respaldos recientes"""
        logger.info(f"📋 RESPALDOS RECIENTES ({days} días)")
        logger.info("=" * 50)
        
        if retailer:
            logger.info(f"🏪 Filtro: {retailer}")
        
        backups = list_recent_backups(retailer, days)
        
        if not backups:
            logger.info("📭 No se encontraron respaldos")
            return
        
        logger.info(f"📦 Encontrados {len(backups)} respaldos:")
        
        for backup in backups:
            logger.info(f"  📁 {backup['retailer']}/{backup['date']}/{backup['file']}")
            logger.info(f"      💾 {backup['size_mb']} MB | 📅 {backup['modified']}")
    
    def convert_to_csv(self, parquet_file, output_file=None):
        """Convertir Parquet a CSV"""
        logger.info(f"🔄 Convirtiendo Parquet a CSV: {parquet_file}")
        
        try:
            # Leer Parquet
            df = self.system.read_backup(parquet_file)
            
            if df.empty:
                logger.error("❌ El archivo Parquet está vacío")
                return
            
            # Generar nombre de salida
            if not output_file:
                parquet_path = Path(parquet_file)
                output_file = parquet_path.with_suffix('.csv')
            
            # Guardar CSV
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            logger.info(f"✅ CSV creado: {output_file}")
            logger.info(f"📊 {len(df)} filas, {len(df.columns)} columnas")
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo a CSV: {e}")
    
    def convert_to_excel(self, parquet_file, output_file=None):
        """Convertir Parquet a Excel"""
        logger.info(f"📊 Convirtiendo Parquet a Excel: {parquet_file}")
        
        try:
            # Leer Parquet
            df = self.system.read_backup(parquet_file)
            
            if df.empty:
                logger.error("❌ El archivo Parquet está vacío")
                return
            
            # Generar nombre de salida
            if not output_file:
                parquet_path = Path(parquet_file)
                output_file = parquet_path.with_suffix('.xlsx')
            
            # Guardar Excel
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            logger.info(f"✅ Excel creado: {output_file}")
            logger.info(f"📊 {len(df)} filas, {len(df.columns)} columnas")
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo a Excel: {e}")
    
    def analyze_file(self, parquet_file):
        """Análizar archivo Parquet"""
        logger.info(f"🔍 ANÁLISIS DE ARCHIVO PARQUET")
        logger.info("=" * 50)
        logger.info(f"📁 Archivo: {parquet_file}")
        
        try:
            df = self.system.read_backup(parquet_file)
            
            if df.empty:
                logger.error("❌ El archivo está vacío")
                return
            
            logger.info(f"📊 Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
            logger.info(f"💾 Tamaño en memoria: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            
            # Información de columnas
            logger.info("\n📋 COLUMNAS:")
            for col in df.columns:
                dtype = df[col].dtype
                null_count = df[col].isnull().sum()
                unique_count = df[col].nunique()
                logger.info(f"  {col}: {dtype} | Nulos: {null_count} | Únicos: {unique_count}")
            
            # Retailers únicos
            if 'retailer' in df.columns:
                retailers = df['retailer'].unique()
                logger.info(f"\n🏪 Retailers: {list(retailers)}")
            
            # Categorías únicas
            if 'categoria' in df.columns:
                categories = df['categoria'].unique()
                logger.info(f"📂 Categorías: {list(categories)}")
            
            # Marcas más comunes
            if 'marca' in df.columns:
                top_brands = df['marca'].value_counts().head(5)
                logger.info(f"\n🏷️ TOP 5 MARCAS:")
                for brand, count in top_brands.items():
                    logger.info(f"  {brand}: {count} productos")
            
            # Rangos de precios
            price_cols = ['precio_normal', 'precio_oferta']
            for col in price_cols:
                if col in df.columns:
                    prices = pd.to_numeric(df[col], errors='coerce')
                    prices = prices.dropna()
                    if not prices.empty:
                        logger.info(f"\n💰 {col.upper()}:")
                        logger.info(f"  Min: ${prices.min():,.0f}")
                        logger.info(f"  Max: ${prices.max():,.0f}")
                        logger.info(f"  Promedio: ${prices.mean():,.0f}")
                        logger.info(f"  Mediana: ${prices.median():,.0f}")
            
        except Exception as e:
            logger.error(f"❌ Error analizando archivo: {e}")
    
    def cleanup_old(self, days=30):
        """Limpiar archivos antiguos"""
        logger.info(f"🧹 LIMPIANDO RESPALDOS ANTIGUOS (>{days} días)")
        logger.info("=" * 50)
        
        result = self.system.cleanup_old_backups(days)
        
        if result.get('success'):
            logger.info(f"✅ Limpieza completada:")
            logger.info(f"🗑️ Carpetas eliminadas: {result['deleted_folders']}")
            logger.info(f"💾 Espacio liberado: {result['freed_space_mb']:.2f} MB")
            logger.info(f"📅 Fecha límite: {result['cutoff_date']}")
        else:
            logger.error(f"❌ Error en limpieza: {result.get('error')}")
    
    def backup_info(self, retailer, date=None):
        """Información de respaldos de un retailer en una fecha"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"ℹ️ INFORMACIÓN DE RESPALDOS")
        logger.info("=" * 50)
        logger.info(f"🏪 Retailer: {retailer}")
        logger.info(f"📅 Fecha: {date}")
        
        retailer_path = self.system.base_path / retailer / date
        
        if not retailer_path.exists():
            logger.warning(f"⚠️ No se encontraron respaldos para {retailer} en {date}")
            return
        
        # Archivos Parquet
        parquet_files = list(retailer_path.glob("*.parquet"))
        logger.info(f"\n📦 ARCHIVOS PARQUET: {len(parquet_files)}")
        
        total_size = 0
        for pf in parquet_files:
            size_mb = pf.stat().st_size / (1024 * 1024)
            total_size += size_mb
            logger.info(f"  📁 {pf.name}: {size_mb:.2f} MB")
        
        logger.info(f"💾 Tamaño total: {total_size:.2f} MB")
        
        # Metadata
        metadata_files = list(retailer_path.glob("*.json"))
        if metadata_files:
            logger.info(f"\n📋 METADATA: {len(metadata_files)} archivos")
            for mf in metadata_files:
                logger.info(f"  📄 {mf.name}")

def main():
    parser = argparse.ArgumentParser(description="Parquet Manager - Gestión de respaldos")
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Stats command
    subparsers.add_parser('stats', help='Mostrar estadísticas de respaldos')
    
    # List command
    list_parser = subparsers.add_parser('list', help='Listar respaldos recientes')
    list_parser.add_argument('--retailer', help='Filtrar por retailer')
    list_parser.add_argument('--days', type=int, default=7, help='Días hacia atrás (default: 7)')
    
    # Convert commands
    csv_parser = subparsers.add_parser('to-csv', help='Convertir Parquet a CSV')
    csv_parser.add_argument('parquet_file', help='Archivo Parquet a convertir')
    csv_parser.add_argument('--output', help='Archivo CSV de salida')
    
    excel_parser = subparsers.add_parser('to-excel', help='Convertir Parquet a Excel')
    excel_parser.add_argument('parquet_file', help='Archivo Parquet a convertir')
    excel_parser.add_argument('--output', help='Archivo Excel de salida')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analizar archivo Parquet')
    analyze_parser.add_argument('parquet_file', help='Archivo Parquet a analizar')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Limpiar archivos antiguos')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Días a mantener (default: 30)')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Información de respaldos')
    info_parser.add_argument('retailer', help='Nombre del retailer')
    info_parser.add_argument('--date', help='Fecha (YYYY-MM-DD, default: hoy)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ParquetManager()
    
    # Ejecutar comando
    if args.command == 'stats':
        manager.show_stats()
    elif args.command == 'list':
        manager.list_backups(args.retailer, args.days)
    elif args.command == 'to-csv':
        manager.convert_to_csv(args.parquet_file, args.output)
    elif args.command == 'to-excel':
        manager.convert_to_excel(args.parquet_file, args.output)
    elif args.command == 'analyze':
        manager.analyze_file(args.parquet_file)
    elif args.command == 'cleanup':
        manager.cleanup_old(args.days)
    elif args.command == 'info':
        manager.backup_info(args.retailer, args.date)

if __name__ == "__main__":
    main()