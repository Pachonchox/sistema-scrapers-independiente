#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test directo de Telegram sin dependencias
"""

import asyncio
import os
import sys

async def test_telegram_direct():
    """Test directo usando python-telegram-bot"""
    print("Testing direct Telegram connection...")
    
    token = "8409617022:AAF2t59JB3cnB2kiPqEAu61k7qPA7e5gjFs"
    chat_id = "7640017914"
    
    try:
        from telegram.ext import Application
        from telegram import Bot
        
        # Crear bot
        bot = Bot(token=token)
        
        # Test mensaje simple
        message = """🧪 TEST DE INTEGRACIÓN - SISTEMA DE ALERTAS V5

📊 ALERTA DE PRECIO DETECTADA
┌──────────────────────────────────────┐
│ BAJADA SIGNIFICATIVA • Master System │
└──────────────────────────────────────┘

📦 SKU: CL-SAMS-GALAXY-256GB-RIP-001
🏷️ Producto: Samsung Galaxy S24 256GB (TEST)
🏪 Retailer: ripley
💳 Tipo: Oferta

💰 Cambio de precio:
├── 🔙 Anterior: $899.990
├── ✨ Actual: $849.990
├── 📉 Cambio: $50.000
└── 📊 Variación: -5.6%

✅ INTEGRACIÓN FUNCIONANDO CORRECTAMENTE!"""
        
        # Enviar mensaje
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=None
        )
        
        print("SUCCESS: Message sent to Telegram!")
        print(f"Check your Telegram chat: {chat_id}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Starting direct Telegram test...")
    
    try:
        success = asyncio.run(test_telegram_direct())
        if success:
            print("\n🎉 SUCCESS! Integration working!")
            print("📱 Check your Telegram for the test message")
        else:
            print("\n❌ FAILED! Check token and chat ID")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)