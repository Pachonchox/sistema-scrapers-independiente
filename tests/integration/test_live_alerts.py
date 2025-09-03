#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Test de Alertas en Vivo - Sistema Integrado
==============================================

Prueba real de envío de alertas usando tu token de Telegram configurado.
Envía alertas de prueba para verificar que toda la integración funciona.

Autor: Sistema de Integración V5 🚀
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

async def test_price_alert_live():
    """📊 Test de alerta de precio en vivo"""
    logger.info("🧪 Testing Price Alert - ENVÍO REAL...")
    
    try:
        from core.alerts_bridge import send_price_change_alert
        
        # Envío REAL de alerta de precio
        logger.info("📤 Enviando alerta de precio REAL a Telegram...")
        
        sent = await send_price_change_alert(
            codigo_interno="CL-SAMS-GALAXY-256GB-RIP-001",
            nombre_producto="🧪 Samsung Galaxy S24 256GB (TEST)",
            retailer="ripley",
            precio_anterior=899990,
            precio_actual=849990,  # 5.6% de descuento
            tipo_precio="oferta"
        )
        
        if sent:
            logger.info("✅ Alerta de precio enviada exitosamente!")
            logger.info("   📱 Revisa tu chat de Telegram para ver el mensaje")
            return True
        else:
            logger.warning("⚠️ Alerta no enviada - posible configuración")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error enviando alerta de precio: {e}")
        return False

async def test_arbitrage_alert_live():
    """💎 Test de alerta de arbitraje en vivo"""
    logger.info("🧪 Testing Arbitrage Alert - ENVÍO REAL...")
    
    try:
        from core.alerts_bridge import send_arbitrage_opportunity_alert
        
        # Envío REAL de alerta de arbitraje
        logger.info("📤 Enviando alerta de arbitraje REAL a Telegram...")
        
        sent = await send_arbitrage_opportunity_alert(
            producto_codigo="CL-APPL-IPHONE-128GB-FAL-002",
            nombre_producto="🧪 iPhone 15 128GB (TEST)",
            retailer_barato="ripley",
            precio_barato=1199990,
            retailer_caro="falabella",
            precio_caro=1349990,  # $150k de margen
            confidence_score=0.98
        )
        
        if sent:
            logger.info("✅ Alerta de arbitraje enviada exitosamente!")
            logger.info("   📱 Revisa tu chat de Telegram para ver el mensaje")
            return True
        else:
            logger.warning("⚠️ Alerta no enviada - posible configuración")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error enviando alerta de arbitraje: {e}")
        return False

async def test_bridge_connectivity():
    """🌉 Test de conectividad del bridge"""
    logger.info("🧪 Testing Bridge Connectivity...")
    
    try:
        from core.alerts_bridge import get_alerts_bridge
        
        # Crear bridge con Telegram habilitado
        bridge = get_alerts_bridge(enable_telegram=True)
        
        logger.info(f"🌉 Bridge habilitado: {bridge.is_enabled()}")
        logger.info(f"📱 Telegram habilitado: {bridge.enable_telegram}")
        
        if bridge.is_enabled():
            # Test de conectividad
            connected = await bridge.test_connection()
            logger.info(f"🔗 Conectividad: {'✅ OK' if connected else '❌ FAILED'}")
            return connected
        else:
            logger.warning("⚠️ Bridge deshabilitado")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testando conectividad: {e}")
        return False

async def test_configuration_diagnosis():
    """⚙️ Diagnóstico completo de configuración"""
    logger.info("🧪 Testing Configuration Diagnosis...")
    
    try:
        from core.alerts_config import diagnose_alerts_config
        
        diagnosis = diagnose_alerts_config()
        
        logger.info("🏥 DIAGNÓSTICO COMPLETO:")
        logger.info(f"   📊 Estado General: {diagnosis['config_status']}")
        logger.info(f"   📱 Telegram: {diagnosis['telegram_status']}")
        logger.info(f"   ⚡ Redis: {diagnosis['redis_status']}")
        logger.info(f"   🗄️ Database: {diagnosis['database_status']}")
        logger.info(f"   🛍️ Retailers: {diagnosis['retailers_enabled']}/6")
        logger.info(f"   🔔 Alert Types: {diagnosis['alert_types_enabled']}")
        
        # Mostrar umbrales
        thresholds = diagnosis['thresholds']
        logger.info("📊 UMBRALES CONFIGURADOS:")
        logger.info(f"   💰 Cambio de precio: {thresholds['price_change']}%")
        logger.info(f"   💎 Margen arbitraje: ${thresholds['arbitrage_margin']:,.0f} CLP")
        logger.info(f"   📈 ROI arbitraje: {thresholds['arbitrage_roi']}%")
        
        if diagnosis['recommendations']:
            logger.info("💡 RECOMENDACIONES:")
            for rec in diagnosis['recommendations']:
                logger.info(f"   • {rec}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en diagnóstico: {e}")
        return False

async def run_live_tests():
    """🚀 Ejecutar todos los tests en vivo"""
    logger.info("🚀 INICIO DE TESTS DE ALERTAS EN VIVO")
    logger.info("=" * 50)
    logger.info("📱 Usando tu configuración de Telegram real")
    logger.info("   Token: 8409617022:AAF...")
    logger.info("   Chat ID: 7640017914")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration Diagnosis", test_configuration_diagnosis),
        ("Bridge Connectivity", test_bridge_connectivity),
        ("Price Alert Live", test_price_alert_live),
        ("Arbitrage Alert Live", test_arbitrage_alert_live)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Ejecutando: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.info(f"❌ {test_name}: FAILED")
                
            # Pausa entre tests para no saturar
            await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Resumen final
    logger.info("\n" + "=" * 50)
    logger.info("📊 RESUMEN DE TESTS EN VIVO")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    logger.info(f"✅ Tests exitosos: {passed}/{total}")
    logger.info(f"❌ Tests fallidos: {total - passed}/{total}")
    
    if passed >= 3:  # Al menos configuración + conectividad + una alerta
        logger.info("🎉 SISTEMA DE ALERTAS FUNCIONANDO!")
        logger.info("📱 Deberías haber recibido mensajes en Telegram")
    else:
        logger.info("⚠️ ALGUNOS TESTS FALLARON")
        logger.info("🔧 Revisar configuración de Telegram Bot")
    
    logger.info("\n💡 Próximos pasos:")
    logger.info("1. ✅ Configuración completa")
    logger.info("2. 🚀 Usar sistema en producción")
    logger.info("3. 📊 Master System enviará alertas automáticamente")
    logger.info("4. 💎 V5 Arbitrage enviará oportunidades")
    
    return passed >= 3

if __name__ == "__main__":
    """Ejecutar tests en vivo"""
    try:
        print("🚀 INICIANDO TESTS DE ALERTAS EN VIVO...")
        print("📱 Se enviarán mensajes REALES a tu Telegram!")
        
        # Confirmación del usuario
        confirm = input("\n¿Continuar con envío real? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes', 'si', 's']:
            print("❌ Tests cancelados por el usuario")
            sys.exit(0)
        
        success = asyncio.run(run_live_tests())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error ejecutando tests: {e}")
        sys.exit(1)