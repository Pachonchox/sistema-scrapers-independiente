#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de alerta en vivo
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

async def test_alert():
    """Test simple de alerta"""
    print("Testing price alert...")
    
    try:
        from core.alerts_bridge import send_price_change_alert
        
        sent = await send_price_change_alert(
            codigo_interno="CL-TEST-SAMSUNG-256GB-RIP-001",
            nombre_producto="Samsung Galaxy S24 256GB (TEST)",
            retailer="ripley",
            precio_anterior=899990,
            precio_actual=849990,
            tipo_precio="oferta"
        )
        
        if sent:
            print("SUCCESS: Alert sent to Telegram!")
            return True
        else:
            print("WARNING: Alert not sent")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Starting live alert test...")
    print("Your Telegram config:")
    print(f"Token: {os.getenv('TELEGRAM_BOT_TOKEN', 'NOT SET')[:20]}...")
    print(f"Chat ID: {os.getenv('TELEGRAM_CHAT_ID', 'NOT SET')}")
    
    success = asyncio.run(test_alert())
    if success:
        print("\nSUCCESS! Check your Telegram for the alert message.")
    else:
        print("\nFAILED! Check your configuration.")
    
    sys.exit(0 if success else 1)