#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Test Simple del Bot de Telegram - Diagnóstico de Comandos
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Configurar encoding para Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar logging con emojis 😊
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Importar telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Obtener configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN no configurado en .env")
    sys.exit(1)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    logger.info(f"📱 Comando /start recibido de {update.effective_user.id}")
    
    message = """🤖 ¡Bot de Alertas V5 Activo!
    
✅ El bot está funcionando correctamente
🎯 Comandos disponibles:
├── /start - Iniciar bot
├── /help - Ver ayuda  
├── /test - Mensaje de prueba
└── /ping - Verificar conexión

📊 Sistema: Portable Orchestrator V5
🔗 Estado: CONECTADO ✅"""
    
    await update.message.reply_text(message)
    logger.info("✅ Respuesta /start enviada")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    logger.info(f"❓ Comando /help recibido de {update.effective_user.id}")
    
    message = """❓ AYUDA - Bot de Alertas V5

🎯 COMANDOS BÁSICOS:
├── /start - Inicializar bot
├── /help - Esta ayuda
├── /test - Mensaje de prueba  
├── /ping - Verificar estado
└── /info - Información del sistema

🔧 DIAGNÓSTICO:
├── Estado: Bot funcionando ✅
├── Versión: V5 Sistema Optimizado
├── Conectividad: Telegram API OK
└── Encoding: UTF-8 compatible 😊

📞 Si tienes problemas, verifica:
1. Token configurado correctamente
2. Chat ID válido
3. Conexión a internet estable"""
    
    await update.message.reply_text(message)
    logger.info("✅ Respuesta /help enviada")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test"""
    logger.info(f"🧪 Comando /test recibido de {update.effective_user.id}")
    
    message = """🧪 MENSAJE DE PRUEBA

📊 DATOS DEL TEST:
┌─────────────────────────────┐
│ Bot Response Test           │
│ ✅ Recepción: OK            │  
│ ✅ Procesamiento: OK        │
│ ✅ Respuesta: OK            │
└─────────────────────────────┘

🎯 Estado del Sistema:
├── 🤖 Bot: Activo
├── 📡 Conexión: Estable  
├── 💬 Chat: Funcional
├── ⚙️ Handlers: OK
└── 😊 Emojis: Compatible

🎉 ¡TEST EXITOSO!"""
    
    await update.message.reply_text(message)
    logger.info("✅ Respuesta /test enviada")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ping"""
    logger.info(f"🏓 Comando /ping recibido de {update.effective_user.id}")
    
    import time
    start_time = time.time()
    
    message = f"""🏓 PONG!

⏱️ Tiempo de respuesta: {int((time.time() - start_time) * 1000)}ms
📡 Estado: CONECTADO ✅
🤖 Bot ID: {context.bot.id}
👤 Usuario: {update.effective_user.first_name}
💬 Chat: {update.effective_chat.id}

🎯 Todo funcionando correctamente! 🎉"""
    
    await update.message.reply_text(message)
    logger.info("✅ Respuesta /ping enviada")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /info"""
    logger.info(f"ℹ️ Comando /info recibido de {update.effective_user.id}")
    
    message = f"""ℹ️ INFORMACIÓN DEL SISTEMA

🚀 PORTABLE ORCHESTRATOR V5
├── 🤖 Bot Version: 5.0
├── 📊 Sistema: Alertas Inteligentes  
├── 🔗 API: Telegram Bot API
└── 😊 Encoding: UTF-8

👤 USUARIO ACTUAL:
├── ID: {update.effective_user.id}
├── Nombre: {update.effective_user.first_name}
├── Usuario: @{update.effective_user.username or 'No disponible'}
└── Chat ID: {update.effective_chat.id}

⚙️ CONFIGURACIÓN:
├── Token: Configurado ✅
├── Handlers: Activos ✅  
├── Logging: Habilitado ✅
└── Emojis: Soporte completo 😊

🎯 ¡Sistema funcionando perfectamente!"""
    
    await update.message.reply_text(message)
    logger.info("✅ Respuesta /info enviada")

def main():
    """Función principal del bot de prueba"""
    logger.info("🚀 Iniciando Bot de Prueba - Diagnóstico de Comandos...")
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("info", info_command))
    
    # Información de inicio
    logger.info("🤖 Bot configurado con comandos:")
    logger.info("   📱 /start - Inicializar bot")
    logger.info("   ❓ /help - Mostrar ayuda")
    logger.info("   🧪 /test - Mensaje de prueba")
    logger.info("   🏓 /ping - Verificar conexión")
    logger.info("   ℹ️ /info - Información del sistema")
    
    logger.info("📡 Iniciando polling...")
    logger.info("💬 Envía un comando en Telegram para probar!")
    
    try:
        # Iniciar bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error en bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()