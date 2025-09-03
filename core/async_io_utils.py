# -*- coding: utf-8 -*-
"""
Async I/O Utils - Wrappers asíncronos para operaciones de I/O bloqueantes
=========================================================================
Previene el bloqueo del event loop durante operaciones de pandas y I/O de archivos
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Thread pool compartido para I/O
_io_thread_pool: Optional[ThreadPoolExecutor] = None
MAX_IO_WORKERS = 3  # Limite conservativo para I/O


def _get_io_thread_pool() -> ThreadPoolExecutor:
    """Obtener thread pool compartido para I/O"""
    global _io_thread_pool
    if _io_thread_pool is None:
        _io_thread_pool = ThreadPoolExecutor(
            max_workers=MAX_IO_WORKERS, 
            thread_name_prefix="async_io"
        )
    return _io_thread_pool


async def read_excel_async(file_path: Path, **kwargs) -> pd.DataFrame:
    """
    Leer archivo Excel de forma asíncrona
    
    Args:
        file_path: Ruta al archivo Excel
        **kwargs: Argumentos adicionales para pd.read_excel()
        
    Returns:
        DataFrame con los datos
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        Exception: Para otros errores de lectura
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    try:
        loop = asyncio.get_event_loop()
        thread_pool = _get_io_thread_pool()
        
        # Ejecutar pandas.read_excel en thread pool
        logger.debug(f"Leyendo Excel async: {file_path.name}")
        df = await loop.run_in_executor(
            thread_pool, 
            partial(pd.read_excel, **kwargs), 
            str(file_path)
        )
        
        logger.debug(f"Excel leído: {len(df)} filas, {len(df.columns)} columnas")
        return df
        
    except Exception as e:
        logger.error(f"Error leyendo Excel {file_path}: {e}")
        raise


async def read_csv_async(file_path: Path, encoding: str = 'utf-8-sig', **kwargs) -> pd.DataFrame:
    """
    Leer archivo CSV de forma asíncrona con manejo de encoding
    
    Args:
        file_path: Ruta al archivo CSV
        encoding: Encoding a usar (default: utf-8-sig)
        **kwargs: Argumentos adicionales para pd.read_csv()
        
    Returns:
        DataFrame con los datos
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        Exception: Para otros errores de lectura
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    try:
        loop = asyncio.get_event_loop()
        thread_pool = _get_io_thread_pool()
        
        logger.debug(f"Leyendo CSV async: {file_path.name} (encoding: {encoding})")
        
        try:
            # Intentar con encoding especificado
            df = await loop.run_in_executor(
                thread_pool,
                partial(pd.read_csv, encoding=encoding, **kwargs),
                str(file_path)
            )
        except (UnicodeDecodeError, UnicodeError):
            # Fallback a latin-1 si utf-8 falla
            logger.warning(f"Fallback a latin-1 para {file_path.name}")
            df = await loop.run_in_executor(
                thread_pool,
                partial(pd.read_csv, encoding='latin-1', **kwargs),
                str(file_path)
            )
            
        logger.debug(f"CSV leído: {len(df)} filas, {len(df.columns)} columnas")
        return df
        
    except Exception as e:
        logger.error(f"Error leyendo CSV {file_path}: {e}")
        raise


async def write_excel_async(df: pd.DataFrame, file_path: Path, **kwargs) -> None:
    """
    Escribir DataFrame a Excel de forma asíncrona
    
    Args:
        df: DataFrame a escribir
        file_path: Ruta de destino
        **kwargs: Argumentos adicionales para DataFrame.to_excel()
    """
    try:
        # Asegurar que el directorio existe
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        loop = asyncio.get_event_loop()
        thread_pool = _get_io_thread_pool()
        
        logger.debug(f"Escribiendo Excel async: {file_path.name} ({len(df)} filas)")
        
        # Usar engine='openpyxl' por defecto para mejor compatibilidad
        kwargs.setdefault('engine', 'openpyxl')
        kwargs.setdefault('index', False)
        
        await loop.run_in_executor(
            thread_pool,
            partial(df.to_excel, **kwargs),
            str(file_path)
        )
        
        logger.debug(f"Excel escrito: {file_path}")
        
    except Exception as e:
        logger.error(f"Error escribiendo Excel {file_path}: {e}")
        raise


async def write_csv_async(df: pd.DataFrame, file_path: Path, encoding: str = 'utf-8-sig', **kwargs) -> None:
    """
    Escribir DataFrame a CSV de forma asíncrona
    
    Args:
        df: DataFrame a escribir
        file_path: Ruta de destino
        encoding: Encoding a usar (default: utf-8-sig)
        **kwargs: Argumentos adicionales para DataFrame.to_csv()
    """
    try:
        # Asegurar que el directorio existe
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        loop = asyncio.get_event_loop()
        thread_pool = _get_io_thread_pool()
        
        logger.debug(f"Escribiendo CSV async: {file_path.name} ({len(df)} filas)")
        
        kwargs.setdefault('index', False)
        kwargs.setdefault('encoding', encoding)
        
        await loop.run_in_executor(
            thread_pool,
            partial(df.to_csv, **kwargs),
            str(file_path)
        )
        
        logger.debug(f"CSV escrito: {file_path}")
        
    except Exception as e:
        logger.error(f"Error escribiendo CSV {file_path}: {e}")
        raise


async def read_table_async(file_path: Path, **kwargs) -> pd.DataFrame:
    """
    Leer tabla (Excel o CSV) de forma asíncrona basado en extensión
    
    Args:
        file_path: Ruta al archivo
        **kwargs: Argumentos adicionales
        
    Returns:
        DataFrame con los datos
        
    Raises:
        ValueError: Si el tipo de archivo no es soportado
        FileNotFoundError: Si el archivo no existe
    """
    suffix = file_path.suffix.lower()
    
    if suffix in ('.xlsx', '.xls'):
        return await read_excel_async(file_path, **kwargs)
    elif suffix == '.csv':
        return await read_csv_async(file_path, **kwargs)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {suffix}")


async def shutdown_io_thread_pool():
    """Cerrar thread pool de I/O de forma limpia"""
    global _io_thread_pool
    if _io_thread_pool is not None:
        logger.info("Cerrando thread pool de I/O...")
        _io_thread_pool.shutdown(wait=True)
        _io_thread_pool = None


# Context manager para operaciones I/O con métricas
class AsyncIOContext:
    """Context manager para monitorear operaciones I/O"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        
    async def __aenter__(self):
        import time
        self.start_time = time.time()
        logger.debug(f"Iniciando operación I/O: {self.operation_name}")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.debug(f"Operación I/O completada: {self.operation_name} ({duration:.2f}s)")
        else:
            logger.error(f"Operación I/O falló: {self.operation_name} ({duration:.2f}s) - {exc_val}")


# Utility para batch I/O operations
async def read_multiple_files_async(file_paths: list[Path], max_concurrent: int = 3) -> Dict[str, pd.DataFrame]:
    """
    Leer múltiples archivos de forma concurrente pero limitada
    
    Args:
        file_paths: Lista de rutas a leer
        max_concurrent: Máximo número de lecturas concurrentes
        
    Returns:
        Diccionario con nombre_archivo -> DataFrame
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def read_single(path: Path) -> tuple[str, pd.DataFrame]:
        async with semaphore:
            async with AsyncIOContext(f"read_{path.name}"):
                df = await read_table_async(path)
                return path.name, df
    
    tasks = [read_single(path) for path in file_paths if path.exists()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Procesar resultados
    successful_reads = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Error en lectura batch: {result}")
        else:
            filename, df = result
            successful_reads[filename] = df
    
    logger.info(f"Batch read completado: {len(successful_reads)}/{len(file_paths)} archivos")
    return successful_reads