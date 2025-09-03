# -*- coding: utf-8 -*-
"""
Core utilities module for portable_orchestrator
"""

# Import only existing modules
try:
    from .async_io_utils import (
        read_excel_async,
        read_csv_async, 
        write_excel_async,
        write_csv_async,
        read_table_async,
        read_multiple_files_async,
        AsyncIOContext,
        shutdown_io_thread_pool
    )
except ImportError:
    pass

try:
    from .connection_manager import (
        ConnectionManager,
        get_redis_client,
        get_duckdb_connection,
        release_duckdb_connection,
        DuckDBConnection,
        initialize_connections,
        ConnectionHealthError
    )
except ImportError:
    pass

try:
    from .telegram_logger import (
        TelegramLogger,
        initialize_telegram_logger,
        get_telegram_logger,
        send_price_alert,
        send_system_alert,
        send_summary_report
    )
except ImportError:
    pass

__all__ = [
    # Async I/O
    'read_excel_async',
    'read_csv_async',
    'write_excel_async', 
    'write_csv_async',
    'read_table_async',
    'read_multiple_files_async',
    'AsyncIOContext',
    'shutdown_io_thread_pool',
    
    # Connection Management
    'ConnectionManager',
    'get_redis_client',
    'get_duckdb_connection',
    'release_duckdb_connection',
    'DuckDBConnection',
    'initialize_connections',
    'ConnectionHealthError',
    
    # Telegram Logging
    'TelegramLogger',
    'initialize_telegram_logger',
    'get_telegram_logger',
    'send_price_alert',
    'send_system_alert',
    'send_summary_report'
]