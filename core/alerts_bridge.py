# -*- coding: utf-8 -*-
"""
🌉 Alerts Bridge - Conector de Integración de Alertas
=====================================================

Conecta el sistema de alertas del bot con los sistemas core:
- Master Prices System → Telegram Alerts
- V5 Arbitrage System → Telegram Alerts  
- Configuración unificada y templates reutilizables

Autor: Sistema de Integración V5 🚀
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import os

# Imports del sistema de alertas
try:
    from ..alerts_bot.config import BotConfig
    from ..alerts_bot.storage import RedisStorage
    from ..alerts_bot.repositories.postgres_repo import PostgresRepo
    from ..alerts_bot.notifiers.telegram_notifier import TelegramNotifier
    from ..alerts_bot.engine.templates import (
        format_spread_msg, format_intraday_msg, 
        fmt_clp, fmt_price_with_trend, pct
    )
    from ..alerts_bot.ui.emoji_constants import (
        PRECIOS_EMOJIS, ARBITRAGE_EMOJIS, ALERTAS_EMOJIS, ESTADOS_EMOJIS
    )
    ALERTS_SYSTEM_AVAILABLE = True
    logging.getLogger(__name__).info("✅ Sistema de alertas disponible para integración")
except ImportError as e:
    ALERTS_SYSTEM_AVAILABLE = False
    logging.getLogger(__name__).warning(f"⚠️ Sistema de alertas no disponible: {e}")

logger = logging.getLogger(__name__)

@dataclass
class PriceAlertData:
    """Estructura de datos para alertas de precios"""
    codigo_interno: str
    nombre_producto: str
    retailer: str
    precio_anterior: int
    precio_actual: int
    cambio_porcentaje: float
    cambio_absoluto: int
    tipo_precio: str  # 'normal', 'oferta', 'tarjeta'
    timestamp: datetime

@dataclass  
class ArbitrageAlertData:
    """Estructura de datos para alertas de arbitraje"""
    producto_codigo: str
    nombre_producto: str
    retailer_barato: str
    retailer_caro: str
    precio_barato: int
    precio_caro: int
    margen_clp: int
    margen_porcentaje: float
    confidence_score: float
    timestamp: datetime

class AlertsBridge:
    """
    🌉 Conector principal del sistema de alertas
    
    Funciones:
    - Conecta Master System con Telegram Bot
    - Conecta V5 Arbitrage con Telegram Bot
    - Reutiliza templates y emojis del bot
    - Maneja configuración unificada
    """
    
    def __init__(self, enable_telegram: bool = True):
        self.enable_telegram = enable_telegram
        self.enabled = ALERTS_SYSTEM_AVAILABLE and enable_telegram
        
        if self.enabled:
            self._initialize_bot_components()
        else:
            logger.info("📵 Alerts Bridge deshabilitado - modo offline")
    
    def _initialize_bot_components(self):
        """Inicializar componentes del bot sin el application completo"""
        try:
            # Cargar configuración
            self.bot_config = BotConfig()
            
            # Validar token
            if not self.bot_config.telegram_token:
                logger.warning("⚠️ TELEGRAM_BOT_TOKEN no configurado - alertas deshabilitadas")
                self.enabled = False
                return
            
            # Inicializar storage Redis
            self.storage = RedisStorage(self.bot_config.redis_url)
            
            # Inicializar repositorio PostgreSQL
            self.repo = PostgresRepo(self.bot_config.database_url)
            
            # Para envío de mensajes necesitamos una instancia bot mínima
            self.telegram_notifier = None  # Se inicializará cuando se necesite
            
            logger.info("✅ Alerts Bridge inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Alerts Bridge: {e}")
            self.enabled = False
    
    async def _ensure_telegram_notifier(self):
        """Crear notifier Telegram solo cuando se necesite"""
        if not self.enabled:
            return False
            
        if self.telegram_notifier is None:
            try:
                from telegram.ext import Application
                
                # Crear application mínimo solo para envío de mensajes
                application = Application.builder().token(self.bot_config.telegram_token).build()
                self.telegram_notifier = TelegramNotifier(application)
                
                logger.info("📱 Telegram Notifier inicializado")
                return True
            except Exception as e:
                logger.error(f"❌ Error creando Telegram Notifier: {e}")
                return False
        return True
    
    async def send_price_alert(self, alert_data: PriceAlertData, 
                              subscribers: Optional[List[int]] = None) -> bool:
        """
        🔔 Enviar alerta de cambio de precio
        
        Args:
            alert_data: Datos del cambio de precio
            subscribers: Lista de user_ids, si no se proporciona busca en storage
            
        Returns:
            True si se enviaron alertas exitosamente
        """
        if not self.enabled:
            logger.debug("📵 Alertas deshabilitadas - skipping price alert")
            return False
        
        if not await self._ensure_telegram_notifier():
            return False
        
        try:
            # Buscar suscriptores si no se proporcionaron
            if subscribers is None:
                subscribers = self.storage.subscribers_of(alert_data.codigo_interno)
            
            if not subscribers:
                logger.debug(f"📭 No hay suscriptores para {alert_data.codigo_interno}")
                return True
            
            # Formatear mensaje usando templates del bot
            message = self._format_price_alert_message(alert_data)
            
            # Enviar a todos los suscriptores
            sent_count = 0
            for user_id in subscribers:
                try:
                    await self.telegram_notifier.send_markdown(user_id, message)
                    sent_count += 1
                    
                    # Registrar métrica
                    self.storage.incr_hourly_counter("alerts_sent_price")
                    
                except Exception as e:
                    logger.error(f"❌ Error enviando alerta a {user_id}: {e}")
            
            logger.info(f"📤 Alerta de precio enviada a {sent_count}/{len(subscribers)} usuarios")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error en send_price_alert: {e}")
            return False
    
    async def send_arbitrage_alert(self, alert_data: ArbitrageAlertData,
                                  broadcast_to_all: bool = False) -> bool:
        """
        💎 Enviar alerta de oportunidad de arbitraje
        
        Args:
            alert_data: Datos de la oportunidad
            broadcast_to_all: Si True, envía a todos los usuarios activos
            
        Returns:
            True si se enviaron alertas exitosamente
        """
        if not self.enabled:
            logger.debug("📵 Alertas deshabilitadas - skipping arbitrage alert")
            return False
            
        if not await self._ensure_telegram_notifier():
            return False
        
        try:
            # Determinar destinatarios
            if broadcast_to_all:
                # Enviar a todos los usuarios activos (admins/superusers)
                recipients = self.storage.get_all_superusers()
            else:
                # Enviar a suscriptores del producto
                recipients = self.storage.subscribers_of(alert_data.producto_codigo)
            
            if not recipients:
                logger.debug(f"📭 No hay destinatarios para alerta de arbitraje")
                return True
            
            # Formatear mensaje usando templates del bot
            message = self._format_arbitrage_alert_message(alert_data)
            
            # Enviar alertas
            sent_count = 0
            for user_id in recipients:
                try:
                    await self.telegram_notifier.send_markdown(user_id, message)
                    sent_count += 1
                    
                    # Registrar métrica
                    self.storage.incr_hourly_counter("alerts_sent_arbitrage")
                    
                except Exception as e:
                    logger.error(f"❌ Error enviando alerta de arbitraje a {user_id}: {e}")
            
            logger.info(f"💎 Alerta de arbitraje enviada a {sent_count}/{len(recipients)} usuarios")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error en send_arbitrage_alert: {e}")
            return False
    
    def _format_price_alert_message(self, data: PriceAlertData) -> str:
        """Formatear mensaje de alerta de precio usando templates del bot"""
        # Determinar emoji de tendencia
        if data.cambio_porcentaje > 0:
            trend_emoji = PRECIOS_EMOJIS.get("ALZA", "📈")
            movement_type = "SUBIDA"
        else:
            trend_emoji = PRECIOS_EMOJIS.get("BAJA", "📉") 
            movement_type = "BAJADA"
        
        # Formatear precios
        precio_anterior_fmt = fmt_clp(data.precio_anterior)
        precio_actual_fmt = fmt_clp(data.precio_actual)
        cambio_fmt = fmt_clp(abs(data.cambio_absoluto))
        
        return (
            f"{trend_emoji} *CAMBIO DE PRECIO DETECTADO*\n"
            f"┌──────────────────────────────────────┐\n"
            f"│ {movement_type} SIGNIFICATIVA • Master System │\n"
            f"└──────────────────────────────────────┘\n\n"
            f"📦 **SKU:** `{data.codigo_interno}`\n"
            f"🏷️ **Producto:** {data.nombre_producto}\n"
            f"🏪 **Retailer:** {data.retailer}\n"
            f"💳 **Tipo:** {data.tipo_precio.title()}\n\n"
            f"💰 **Cambio de precio:**\n"
            f"├── 🔙 Anterior: *{precio_anterior_fmt}*\n"
            f"├── ✨ Actual: *{precio_actual_fmt}*\n"
            f"├── {trend_emoji} Cambio: *{cambio_fmt}*\n"
            f"└── 📊 Variación: *{data.cambio_porcentaje:+.1f}%*\n\n"
            f"⏰ *Detectado: {data.timestamp.strftime('%d/%m %H:%M')}*"
        )
    
    def _format_arbitrage_alert_message(self, data: ArbitrageAlertData) -> str:
        """Formatear mensaje de alerta de arbitraje usando templates del bot"""
        # Formatear precios y margen
        precio_barato_fmt = fmt_clp(data.precio_barato)
        precio_caro_fmt = fmt_clp(data.precio_caro)
        margen_fmt = fmt_clp(data.margen_clp)
        
        # Emoji según el margen
        if data.margen_clp >= 50000:
            opportunity_emoji = ARBITRAGE_EMOJIS.get("PREMIUM", "💎")
        elif data.margen_clp >= 25000:
            opportunity_emoji = ARBITRAGE_EMOJIS.get("BUENA", "🟡")
        else:
            opportunity_emoji = ARBITRAGE_EMOJIS.get("BASICA", "🔵")
        
        return (
            f"{opportunity_emoji} *OPORTUNIDAD DE ARBITRAJE DETECTADA*\n"
            f"┌──────────────────────────────────────┐\n"
            f"│ Sistema V5 • ML Confidence {data.confidence_score:.0%} │\n"
            f"└──────────────────────────────────────┘\n\n"
            f"📦 **SKU:** `{data.producto_codigo}`\n"
            f"🏷️ **Producto:** {data.nombre_producto}\n\n"
            f"💰 **Oportunidad:**\n"
            f"├── 🛒 **Comprar:** {data.retailer_barato} → *{precio_barato_fmt}*\n"
            f"├── 💸 **Vender:** {data.retailer_caro} → *{precio_caro_fmt}*\n"
            f"├── 💰 **Ganancia:** *{margen_fmt}*\n"
            f"└── 📊 **ROI:** *{data.margen_porcentaje:.1f}%*\n\n"
            f"🎯 *Confianza: {data.confidence_score:.0%} • {data.timestamp.strftime('%d/%m %H:%M')}*"
        )
    
    def is_enabled(self) -> bool:
        """Verificar si el bridge está habilitado y funcional"""
        return self.enabled
    
    def get_subscriber_count(self, codigo_interno: str) -> int:
        """Obtener número de suscriptores de un producto"""
        if not self.enabled:
            return 0
        return len(self.storage.subscribers_of(codigo_interno))
    
    async def test_connection(self) -> bool:
        """Testear conexión completa del sistema de alertas"""
        if not self.enabled:
            return False
        
        try:
            # Test Redis
            redis_ok = self.storage.redis_client.ping()
            
            # Test PostgreSQL
            pg_ok = self.repo.test_connection()
            
            # Test Telegram (si está configurado)
            telegram_ok = await self._ensure_telegram_notifier()
            
            logger.info(f"🧪 Test conexión: Redis={redis_ok}, PostgreSQL={pg_ok}, Telegram={telegram_ok}")
            return redis_ok and pg_ok and telegram_ok
            
        except Exception as e:
            logger.error(f"❌ Error en test_connection: {e}")
            return False

# Instancia global del bridge (singleton pattern)
_alerts_bridge_instance = None

def get_alerts_bridge(enable_telegram: bool = True) -> AlertsBridge:
    """
    Obtener instancia singleton del Alerts Bridge
    
    Args:
        enable_telegram: Habilitar envío por Telegram
        
    Returns:
        Instancia del AlertsBridge
    """
    global _alerts_bridge_instance
    
    if _alerts_bridge_instance is None:
        _alerts_bridge_instance = AlertsBridge(enable_telegram=enable_telegram)
    
    return _alerts_bridge_instance

# Funciones de conveniencia para uso fácil
async def send_price_change_alert(codigo_interno: str, nombre_producto: str, 
                                 retailer: str, precio_anterior: int, 
                                 precio_actual: int, tipo_precio: str = "oferta"):
    """
    Función de conveniencia para enviar alerta de cambio de precio
    
    Usage:
        await send_price_change_alert("CL-SAMS-GALAXY-256GB-RIP-001", 
                                     "Samsung Galaxy S24", "ripley", 
                                     899990, 849990)
    """
    bridge = get_alerts_bridge()
    
    if not bridge.is_enabled():
        return False
    
    cambio_absoluto = precio_actual - precio_anterior
    cambio_porcentaje = (cambio_absoluto / precio_anterior) * 100 if precio_anterior > 0 else 0
    
    alert_data = PriceAlertData(
        codigo_interno=codigo_interno,
        nombre_producto=nombre_producto,
        retailer=retailer,
        precio_anterior=precio_anterior,
        precio_actual=precio_actual,
        cambio_porcentaje=cambio_porcentaje,
        cambio_absoluto=cambio_absoluto,
        tipo_precio=tipo_precio,
        timestamp=datetime.now()
    )
    
    return await bridge.send_price_alert(alert_data)

async def send_arbitrage_opportunity_alert(producto_codigo: str, nombre_producto: str,
                                         retailer_barato: str, precio_barato: int,
                                         retailer_caro: str, precio_caro: int,
                                         confidence_score: float = 0.95):
    """
    Función de conveniencia para enviar alerta de arbitraje
    
    Usage:
        await send_arbitrage_opportunity_alert("CL-SAMS-GALAXY-256GB-RIP-001",
                                              "Samsung Galaxy S24",
                                              "ripley", 899990,
                                              "falabella", 989990)
    """
    bridge = get_alerts_bridge()
    
    if not bridge.is_enabled():
        return False
    
    margen_clp = precio_caro - precio_barato
    margen_porcentaje = (margen_clp / precio_barato) * 100
    
    alert_data = ArbitrageAlertData(
        producto_codigo=producto_codigo,
        nombre_producto=nombre_producto,
        retailer_barato=retailer_barato,
        retailer_caro=retailer_caro,
        precio_barato=precio_barato,
        precio_caro=precio_caro,
        margen_clp=margen_clp,
        margen_porcentaje=margen_porcentaje,
        confidence_score=confidence_score,
        timestamp=datetime.now()
    )
    
    return await bridge.send_arbitrage_alert(alert_data)