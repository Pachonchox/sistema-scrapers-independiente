#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 Bot de Alertas de Telegram - Sistema Inteligente de Precios
Punto de entrada principal con interfaz de usuario mejorada
"""
from __future__ import annotations
import asyncio
import logging
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Importar componentes
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from .config import BotConfig
from .storage import RedisStorage
from .repositories.products_repo import ProductsRepo
from .repositories.postgres_repo import PostgresRepo
from .notifiers.telegram_notifier import TelegramNotifier
from .engine.alert_engine import AlertEngine
from .maintenance import refresh_bot_tables
from .bot.handlers import (
    cmd_start, cmd_help, cmd_find, cmd_buscar, cmd_menu, cmd_subscribe, cmd_unsubscribe,
    cmd_mysubs, cmd_setspread, cmd_setdelta, cmd_summary_on, cmd_summary_off,
    cmd_stats, cmd_broadcast, cmd_promote, cmd_demote,
    cb_search_nav, cb_subscribe, cb_menu, cb_unsubscribe, cmd_top, cmd_refresh_bot_tables, cmd_sysmetrics,
    cmd_arbitrage, cmd_arbitrage_stats, cmd_arbitrage_by_retailer, cmd_arbitrage_detect
)

# Reportería operacional
from .ops_reporter import ops_report_job, overnight_report_job, send_report

# Función de trabajo periódico para evaluar alertas
async def alert_job(context: ContextTypes.DEFAULT_TYPE):
    """Job periódico que evalúa y envía alertas"""
    logger.info("Ejecutando job de alertas...")
    
    try:
        engine = context.bot_data["engine"]
        config = context.bot_data["config"]
        storage = context.bot_data.get("storage")
        
        import time as _t
        _t0 = _t.perf_counter()
        await engine.evaluate_and_send(
            shard_total=config.shard_total,
            shard_index=config.shard_index
        )
        
        # Registrar métrica de duración del job
        try:
            elapsed_ms = int((_t.perf_counter() - _t0) * 1000)
            if storage:
                storage.set_metric_value("last_alert_job_ms", str(elapsed_ms), ttl_seconds=86400)
        except Exception:
            pass
        
    except Exception as e:
        logger.error(f"Error en job de alertas: {e}")

async def post_init(application: Application) -> None:
    """Inicialización después de que el bot está listo"""
    logger.info("Bot inicializado, configurando job de alertas...")
    
    config = application.bot_data["config"]
    
    # Programar job de alertas
    jq = getattr(application, "job_queue", None)
    if jq is not None:
        jq.run_repeating(
            alert_job,
            interval=config.poll_interval_seconds,
            first=10  # Esperar 10 segundos antes del primer run
        )
        logger.info(f"Job de alertas programado cada {config.poll_interval_seconds} segundos (JobQueue)")

        # Refresco de tablas del bot (PostgreSQL siempre habilitado)
        try:
            enabled = str(os.getenv('BOT_REFRESH_ENABLED', 'true')).lower() in ('1','true','yes','on')
            interval = int(os.getenv('BOT_REFRESH_INTERVAL_SECONDS', '300'))
            if enabled:
                async def _refresh_job(context: ContextTypes.DEFAULT_TYPE):
                    cfg = context.bot_data["config"]
                    try:
                        # Ejecutar en thread para no bloquear event loop
                        import asyncio
                        await asyncio.to_thread(refresh_bot_tables, cfg.database_url)
                        logger.info("Tablas bot.* refrescadas")
                    except Exception as e:
                        logger.warning(f"Fallo refresh bot tables: {e}")

                jq.run_repeating(_refresh_job, interval=interval, first=30)
                logger.info(f"Refresh bot tables programado cada {interval}s")
        except Exception as e:
            logger.warning(f"No se pudo programar refresh bot tables: {e}")
    else:
        # Fallback sin JobQueue: bucle asíncrono propio
        async def _alert_loop(app: Application):
            while True:
                try:
                    engine = app.bot_data["engine"]
                    cfg = app.bot_data["config"]
                    await engine.evaluate_and_send(shard_total=cfg.shard_total, shard_index=cfg.shard_index)
                except Exception as e:
                    logger.warning(f"Alerta loop error: {e}")
                await asyncio.sleep(config.poll_interval_seconds)
        application.create_task(_alert_loop(application))
        logger.info(f"Job de alertas programado cada {config.poll_interval_seconds} segundos (async loop)")

    # Configurar menú de comandos (solo comandos de usuario visibles)
    try:
        commands = [
            BotCommand("start", "🚀 Iniciar y registrarte en el bot"),
            BotCommand("help", "❓ Ver comandos disponibles"),
            BotCommand("menu", "🏠 Abrir panel principal"),
            BotCommand("top", "🏆 Ver top del día"),
            BotCommand("buscar", "🔎 Buscar productos canónicos"),
            BotCommand("subscribe", "➕ Suscribirte a un SKU"),
            BotCommand("unsubscribe", "❌ Cancelar suscripción a un SKU"),
            BotCommand("mysubs", "📜 Listar tus suscripciones"),
            BotCommand("setspread", "📊 Fijar umbral de spread (%)"),
            BotCommand("setdelta", "📈 Fijar umbral intradía (%)"),
            BotCommand("summary_on", "🔔 Activar resumen diario"),
            BotCommand("summary_off", "🔕 Desactivar resumen diario"),
            BotCommand("arbitrage", "💎 Ver oportunidades de arbitraje"),
            BotCommand("arbitrage_stats", "📊 Estadísticas de arbitraje"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Menú de comandos configurado")
    except Exception as e:
        logger.warning(f"No se pudo configurar el menú de comandos: {e}")

    # Programar reporte operacional (horario + overnight)
    try:
        enabled = str(os.getenv("OPS_REPORT_ENABLED", "true")).lower() in ("1","true","yes","on")
        if enabled:
            interval = int(os.getenv("OPS_REPORT_INTERVAL_SECONDS", "3600"))
            from datetime import datetime, timedelta, time as _dtime
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            first_delay = max(5, int((next_hour - now).total_seconds()))
            if jq is not None:
                jq.run_repeating(ops_report_job, interval=interval, first=first_delay)
                start_hour = int(os.getenv("OPS_REPORT_START_HOUR", "9"))
                jq.run_daily(overnight_report_job, time=_dtime(hour=start_hour, minute=0))
                logger.info("Reporte operacional programado (JobQueue)")
            else:
                async def _ops_loop(app: Application):
                    await asyncio.sleep(first_delay)
                    while True:
                        try:
                            from alerts_bot.ops_reporter import _int_env, within_active_window
                            start_h = _int_env("OPS_REPORT_START_HOUR", 9)
                            end_h = _int_env("OPS_REPORT_END_HOUR", 22)
                            now2 = datetime.now()
                            if within_active_window(now2, start_h, end_h):
                                storage = app.bot_data["storage"]
                                repo = app.bot_data["repo"]
                                await send_report(app, storage, repo, kind="hourly", start_hour=start_h, end_hour=end_h)
                        except Exception as e:
                            logger.warning(f"Ops loop error: {e}")
                        await asyncio.sleep(interval)
                application.create_task(_ops_loop(application))
                # Programar overnight simple
                async def _overnight_loop(app: Application):
                    start_hour = int(os.getenv("OPS_REPORT_START_HOUR", "9"))
                    while True:
                        now3 = datetime.now()
                        target = now3.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                        if target <= now3:
                            target = target + timedelta(days=1)
                        await asyncio.sleep((target - now3).total_seconds())
                        try:
                            storage = app.bot_data["storage"]
                            repo = app.bot_data["repo"]
                            await send_report(app, storage, repo, kind="overnight", start_hour=start_hour, end_hour=22)
                        except Exception as e:
                            logger.warning(f"Overnight loop error: {e}")
                application.create_task(_overnight_loop(application))
                logger.info("Reporte operacional programado (async loop)")
    except Exception as e:
        logger.warning(f"No se pudo programar reporte operacional: {e}")

def main():
    """Función principal"""
    
    # Cargar configuración
    config = BotConfig()
    
    # Validar configuración mínima
    if not config.telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN no configurado en .env")
        sys.exit(1)
    
    # Inicializar storage
    try:
        storage = RedisStorage(config.redis_url)
        logger.info("Redis conectado exitosamente")
    except Exception as e:
        logger.error(f"No se pudo conectar a Redis: {e}")
        sys.exit(1)
    
    # Inicializar repository PostgreSQL (único backend)
    try:
        repo = PostgresRepo(config.database_url)
        logger.info("Repositorio de datos: PostgreSQL (sistema unificado)")
    except Exception as e:
        logger.error(f"No se pudo conectar a PostgreSQL: {e}")
        sys.exit(1)
    
    # Crear vistas SQL si existen
    views_sql = Path(__file__).parent / "create_views.sql"
    if views_sql.exists():
        try:
            repo.ensure_views(str(views_sql))
            logger.info("Vistas SQL creadas/actualizadas")
        except Exception as e:
            logger.warning(f"No se pudieron crear vistas: {e}")
    
    # Configurar superusuarios iniciales
    if config.superusers():
        storage.set_superusers_initial(config.superusers())
        logger.info(f"Superusuarios configurados: {config.superusers()}")
    
    # Crear aplicación de Telegram
    application = Application.builder().token(config.telegram_token).build()
    
    # Crear notifier y engine
    notifier = TelegramNotifier(application)
    engine = AlertEngine(
        storage, repo, notifier,
        config.default_spread_threshold,
        config.default_delta_threshold
    )
    
    # Guardar componentes en bot_data para acceso global
    application.bot_data["config"] = config
    application.bot_data["storage"] = storage
    application.bot_data["repo"] = repo
    application.bot_data["engine"] = engine
    
    # Registrar comandos de usuario
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("menu", cmd_menu))
    application.add_handler(CommandHandler("buscar", cmd_buscar))
    application.add_handler(CommandHandler("top", cmd_top))
    application.add_handler(CommandHandler("refresh_bot", cmd_refresh_bot_tables))
    application.add_handler(CommandHandler("sysmetrics", cmd_sysmetrics))
    application.add_handler(CommandHandler("find", cmd_find))
    application.add_handler(CommandHandler("subscribe", cmd_subscribe))
    application.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    application.add_handler(CommandHandler("mysubs", cmd_mysubs))
    application.add_handler(CommandHandler("setspread", cmd_setspread))
    application.add_handler(CommandHandler("setdelta", cmd_setdelta))
    application.add_handler(CommandHandler("summary_on", cmd_summary_on))
    application.add_handler(CommandHandler("summary_off", cmd_summary_off))
    
    # Registrar comandos de admin
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))
    application.add_handler(CommandHandler("promote", cmd_promote))
    application.add_handler(CommandHandler("demote", cmd_demote))
    
    # Comandos de arbitraje
    application.add_handler(CommandHandler("arbitrage", cmd_arbitrage))
    application.add_handler(CommandHandler("arbitrage_stats", cmd_arbitrage_stats))
    application.add_handler(CommandHandler("arbitrage_by_retailer", cmd_arbitrage_by_retailer))
    application.add_handler(CommandHandler("arbitrage_detect", cmd_arbitrage_detect))
    # Callbacks para búsqueda
    application.add_handler(CallbackQueryHandler(cb_search_nav, pattern=r"^pg:"))
    application.add_handler(CallbackQueryHandler(cb_subscribe, pattern=r"^sub:"))
    application.add_handler(CallbackQueryHandler(cb_unsubscribe, pattern=r"^unsub:"))
    application.add_handler(CallbackQueryHandler(cb_menu, pattern=r"^menu:"))
    
    # Callback de inicialización
    application.post_init = post_init
    
    # Iniciar bot
    logger.info("🤖 Bot de alertas iniciando...")
    logger.info(f"   Shard: {config.shard_index}/{config.shard_total}")
    logger.info(f"   Umbrales por defecto: spread={config.default_spread_threshold:.1%}, delta={config.default_delta_threshold:.1%}")
    logger.info(f"   Intervalo de evaluación: {config.poll_interval_seconds} segundos")
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

