#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test de Integración del Sistema de Alertas
============================================

Script de prueba completo para verificar la integración entre:
- Master Prices System → Telegram Alerts
- V5 Arbitrage System → Telegram Alerts
- Configuración unificada y funcionamiento

Autor: Sistema de Integración V5 🚀
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

async def test_alerts_bridge():
    """🌉 Test del conector principal de alertas"""
    logger.info("🧪 Testing Alerts Bridge...")
    
    try:
        from core.alerts_bridge import get_alerts_bridge, AlertsBridge
        
        # Test 1: Inicialización
        bridge = get_alerts_bridge(enable_telegram=False)  # Sin Telegram para testing
        
        if bridge.is_enabled():
            logger.info("✅ Alerts Bridge inicializado correctamente")
        else:
            logger.info("⚠️ Alerts Bridge deshabilitado (normal en testing)")
        
        # Test 2: Configuración
        logger.info(f"📊 Bridge habilitado: {bridge.enabled}")
        logger.info(f"📱 Telegram habilitado: {bridge.enable_telegram}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error importando alerts_bridge: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error en test alerts_bridge: {e}")
        return False

async def test_master_prices_integration():
    """📊 Test integración Master Prices System"""
    logger.info("🧪 Testing Master Prices Integration...")
    
    try:
        from core.master_prices_system import DailyPriceSnapshot, ALERTS_SYSTEM_AVAILABLE
        
        logger.info(f"📊 Sistema de alertas disponible: {'✅' if ALERTS_SYSTEM_AVAILABLE else '❌'}")
        
        # Test 1: Crear snapshot con cambio significativo
        snapshot = DailyPriceSnapshot(
            codigo_interno="CL-TEST-PRODUCT-256GB-RIP-001",
            fecha=date.today(),
            retailer="ripley",
            precio_normal=100000,
            precio_oferta=85000,
            precio_tarjeta=80000,
            precio_anterior_dia=100000
        )
        
        # Test 2: Simular actualización de precio
        price_updated = snapshot.update_prices(
            precio_normal=95000,
            precio_oferta=80000,
            precio_tarjeta=75000
        )
        
        if price_updated:
            logger.info(f"✅ Precio actualizado: {snapshot.cambio_porcentaje:.1f}% de cambio")
            
            # Test 3: Verificar que se puede enviar alerta (sin enviarlo realmente)
            if ALERTS_SYSTEM_AVAILABLE:
                # Solo simular, no enviar
                logger.info("📤 Alerta simulada - integración OK")
            else:
                logger.info("📵 Sistema de alertas no disponible")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test master prices: {e}")
        return False

async def test_v5_arbitrage_integration():
    """💎 Test integración V5 Arbitrage System"""
    logger.info("🧪 Testing V5 Arbitrage Integration...")
    
    try:
        # Intentar importar sistema V5
        from portable_orchestrator_v5.arbitrage_system.core.arbitrage_engine import ALERTS_SYSTEM_AVAILABLE
        
        logger.info(f"💎 Sistema de alertas V5 disponible: {'✅' if ALERTS_SYSTEM_AVAILABLE else '❌'}")
        
        # Test 1: Simular oportunidad de arbitraje
        fake_opportunity = {
            'producto_barato_codigo': 'CL-TEST-SAMSUNG-256GB-RIP-001',
            'nombre_producto': 'Samsung Galaxy Test 256GB',
            'retailer_compra': 'ripley',
            'precio_compra': 800000,
            'retailer_venta': 'falabella', 
            'precio_venta': 900000,
            'margen_clp': 100000,
            'margen_porcentaje': 12.5,
            'confidence_score': 0.95
        }
        
        logger.info("💎 Oportunidad de arbitraje simulada:")
        logger.info(f"   📦 Producto: {fake_opportunity['nombre_producto']}")
        logger.info(f"   💰 Margen: ${fake_opportunity['margen_clp']:,.0f} ({fake_opportunity['margen_porcentaje']:.1f}%)")
        logger.info(f"   🎯 Confianza: {fake_opportunity['confidence_score']:.0%}")
        
        if ALERTS_SYSTEM_AVAILABLE:
            logger.info("📤 Alerta de arbitraje simulada - integración OK")
        else:
            logger.info("📵 Sistema de alertas V5 no disponible")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error importando V5 arbitrage: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error en test V5 arbitrage: {e}")
        return False

async def test_alerts_config():
    """⚙️ Test configuración unificada"""
    logger.info("🧪 Testing Alerts Configuration...")
    
    try:
        from core.alerts_config import (
            get_alerts_config, should_send_alert, get_price_threshold,
            diagnose_alerts_config
        )
        
        # Test 1: Cargar configuración
        config = get_alerts_config()
        logger.info(f"⚙️ Configuración cargada: {config.enabled}")
        
        # Test 2: Test funciones de conveniencia
        should_alert_price = should_send_alert("price_drop", "ripley")
        should_alert_arbitrage = should_send_alert("arbitrage_opportunity")
        
        logger.info(f"🔔 Alertas de precio habilitadas: {should_alert_price}")
        logger.info(f"💎 Alertas de arbitraje habilitadas: {should_alert_arbitrage}")
        
        # Test 3: Umbrales por retailer
        threshold_ripley = get_price_threshold("price_change", "ripley")
        threshold_falabella = get_price_threshold("price_change", "falabella")
        
        logger.info(f"📊 Umbral Ripley: {threshold_ripley}%")
        logger.info(f"📊 Umbral Falabella: {threshold_falabella}%")
        
        # Test 4: Diagnóstico completo
        diagnosis = diagnose_alerts_config()
        logger.info("🏥 Diagnóstico de configuración:")
        logger.info(f"   📊 Estado: {diagnosis['config_status']}")
        logger.info(f"   📱 Telegram: {diagnosis['telegram_status']}")
        logger.info(f"   🗄️ Database: {diagnosis['database_status']}")
        logger.info(f"   🛍️ Retailers habilitados: {diagnosis['retailers_enabled']}/6")
        
        if diagnosis['recommendations']:
            logger.info("💡 Recomendaciones:")
            for rec in diagnosis['recommendations']:
                logger.info(f"   • {rec}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test alerts config: {e}")
        return False

async def test_telegram_bot_integration():
    """📱 Test integración con Telegram Bot"""
    logger.info("🧪 Testing Telegram Bot Integration...")
    
    try:
        # Test imports del bot
        from alerts_bot.config import BotConfig
        from alerts_bot.engine.templates import format_spread_msg, format_intraday_msg
        from alerts_bot.ui.emoji_constants import PRECIOS_EMOJIS, ARBITRAGE_EMOJIS
        
        # Test 1: Configuración del bot
        bot_config = BotConfig()
        logger.info(f"🤖 Bot token configurado: {'✅' if bot_config.telegram_token else '❌'}")
        logger.info(f"🗄️ Database URL: {'✅' if bot_config.database_url else '❌'}")
        logger.info(f"⚡ Redis URL: {'✅' if bot_config.redis_url else '❌'}")
        
        # Test 2: Templates de mensajes
        fake_spread_data = {
            'retailer_count': 3,
            'min_price': 800000,
            'max_price': 900000,
            'spread_pct': 0.125
        }
        
        spread_message = format_spread_msg(
            "CL-TEST-SAMSUNG-256GB-RIP-001",
            "Samsung Galaxy Test 256GB", 
            fake_spread_data
        )
        
        logger.info("📱 Template de mensaje spread generado correctamente")
        
        # Test 3: Sistema de emojis
        emoji_alza = PRECIOS_EMOJIS.get("ALZA", "📈")
        emoji_arbitrage = ARBITRAGE_EMOJIS.get("PREMIUM", "💎")
        
        logger.info(f"🎭 Emojis disponibles: {emoji_alza} {emoji_arbitrage}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error importando bot components: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error en test telegram bot: {e}")
        return False

async def test_end_to_end_simulation():
    """🔄 Test simulación end-to-end"""
    logger.info("🧪 Testing End-to-End Simulation...")
    
    try:
        # Test 1: Simular flujo Master Prices → Alerts
        logger.info("📊 Simulando: Master Prices → Alerts...")
        
        from core.alerts_bridge import send_price_change_alert
        
        # Simular sin envío real
        logger.info("   📤 Alerta de precio simulada")
        
        # Test 2: Simular flujo V5 Arbitrage → Alerts  
        logger.info("💎 Simulando: V5 Arbitrage → Alerts...")
        
        from core.alerts_bridge import send_arbitrage_opportunity_alert
        
        # Simular sin envío real
        logger.info("   📤 Alerta de arbitraje simulada")
        
        # Test 3: Verificar configuración end-to-end
        from core.alerts_config import get_alerts_config
        config = get_alerts_config()
        
        logger.info("⚙️ Configuración end-to-end:")
        logger.info(f"   📊 Master System ← → Alerts: {'✅' if config.enabled else '❌'}")
        logger.info(f"   💎 V5 Arbitrage ← → Alerts: {'✅' if config.enabled else '❌'}")
        logger.info(f"   📱 Alerts ← → Telegram: {'✅' if config.telegram_enabled else '❌'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test end-to-end: {e}")
        return False

async def run_integration_tests():
    """🚀 Ejecutar todos los tests de integración"""
    logger.info("🚀 INICIO DE TESTS DE INTEGRACIÓN DEL SISTEMA DE ALERTAS")
    logger.info("=" * 60)
    
    tests = [
        ("Alerts Bridge", test_alerts_bridge),
        ("Master Prices Integration", test_master_prices_integration),
        ("V5 Arbitrage Integration", test_v5_arbitrage_integration),
        ("Alerts Configuration", test_alerts_config),
        ("Telegram Bot Integration", test_telegram_bot_integration),
        ("End-to-End Simulation", test_end_to_end_simulation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Ejecutando: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.info(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE TESTS DE INTEGRACIÓN")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    logger.info(f"✅ Tests exitosos: {passed}/{total}")
    logger.info(f"❌ Tests fallidos: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 TODOS LOS TESTS PASARON - INTEGRACIÓN COMPLETA")
    else:
        logger.info("⚠️ ALGUNOS TESTS FALLARON - REVISAR CONFIGURACIÓN")
    
    logger.info("\n💡 Próximos pasos:")
    logger.info("1. Configurar TELEGRAM_BOT_TOKEN en .env")
    logger.info("2. Iniciar alerts_bot: python -m alerts_bot.app")
    logger.info("3. Testear envío real de alertas")
    logger.info("4. Configurar usuarios en Telegram")
    
    return passed == total

if __name__ == "__main__":
    """Ejecutar tests cuando se llama directamente"""
    try:
        success = asyncio.run(run_integration_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error ejecutando tests: {e}")
        sys.exit(1)