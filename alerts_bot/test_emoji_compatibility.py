#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧪 Test de Compatibilidad de Emojis
Script para verificar que todos los emojis se rendericen correctamente
"""
import sys
import os

# Agregar el directorio padre al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerts_bot.ui.emoji_constants import *

def test_emoji_rendering():
    """Test básico de renderizado de emojis"""
    print("🧪 TESTING EMOJI COMPATIBILITY")
    print("=" * 50)
    
    print("\n📱 UI EMOJIS:")
    print(f"Home: {UserEmojis.HOME}")
    print(f"Search: {SearchEmojis.SEARCH}")  
    print(f"Help: {UserEmojis.HELP}")
    print(f"Success: {StatusEmojis.SUCCESS}")
    print(f"Error: {StatusEmojis.ERROR}")
    print(f"Loading: {StatusEmojis.LOADING}")
    
    print("\n💰 ARBITRAGE EMOJIS:")
    print(f"Opportunity: {ArbitrageEmojis.OPPORTUNITY}")
    print(f"Profit: {ArbitrageEmojis.PROFIT}")
    print(f"Buy: {ArbitrageEmojis.BUY}")
    print(f"Sell: {ArbitrageEmojis.SELL}")
    print(f"Confidence: {ArbitrageEmojis.CONFIDENCE}")
    
    print("\n🛎️ SUBSCRIPTION EMOJIS:")
    print(f"Subscribe: {SubscriptionEmojis.SUBSCRIBE}")
    print(f"Unsubscribe: {SubscriptionEmojis.UNSUBSCRIBE}")
    print(f"My Subs: {SubscriptionEmojis.MY_SUBS}")
    print(f"Bell On: {SubscriptionEmojis.BELL_ON}")
    print(f"Bell Off: {SubscriptionEmojis.BELL_OFF}")
    
    print("\n🎯 NAVIGATION EMOJIS:")
    print(f"Back: {NavigationEmojis.BACK}")
    print(f"Forward: {NavigationEmojis.FORWARD}")
    print(f"Previous: {NavigationEmojis.PREVIOUS}")
    print(f"Next: {NavigationEmojis.NEXT}")
    
    print("\n📊 PRICE EMOJIS:")
    print(f"Money: {PriceEmojis.MONEY}")
    print(f"Increase: {PriceEmojis.INCREASE}")
    print(f"Decrease: {PriceEmojis.DECREASE}")
    print(f"Spread: {PriceEmojis.SPREAD}")
    
    print("\n🎨 DECORATIVE EMOJIS:")
    print(f"Star: {DecoEmojis.STAR}")
    print(f"Fire: {DecoEmojis.FIRE}")
    print(f"Sparkles: {DecoEmojis.SPARKLES}")
    print(f"Target: {DecoEmojis.TARGET}")
    print(f"Gem: {DecoEmojis.GEM}")

def test_formatting_functions():
    """Test de funciones de formato"""
    print("\n🔧 TESTING FORMATTING FUNCTIONS")
    print("=" * 50)
    
    # Test format_price_with_emoji
    price_test = format_price_with_emoji(125990.0)
    print(f"Price format: {price_test}")
    
    # Test format_percentage_with_emoji  
    pct_test = format_percentage_with_emoji(15.2)
    print(f"Percentage format: {pct_test}")
    
    # Test create_status_message
    status_test = create_status_message("success", "Operation completed")
    print(f"Status message: {status_test}")
    
    # Test create_section_header
    header_test = create_section_header("RESULTADOS DE BÚSQUEDA", SearchEmojis.RESULTS)
    print(f"Section header: {header_test}")

def test_mock_bot_messages():
    """Test de mensajes completos del bot"""
    print("\n📱 TESTING COMPLETE BOT MESSAGES")
    print("=" * 50)
    
    # Mensaje de bienvenida simulado
    welcome_msg = (
        f"{UserEmojis.WELCOME} *¡BIENVENIDO AL ASISTENTE INTELIGENTE!*\n"
        f"┌────────────────────────────────────┐\n"
        f"│ {ArbitrageEmojis.OPPORTUNITY} Tu centro de comando para        │\n"
        f"│ oportunidades de arbitraje         │\n"
        f"│ en tiempo real                     │\n"
        f"└────────────────────────────────────┘\n\n"
        f"{UIEmojis.TREE_BRANCH} {SearchEmojis.SEARCH} *Comandos principales:*\n"
        f"{UIEmojis.TREE_BRANCH} {SubscriptionEmojis.SUBSCRIBE} `/buscar <producto>` - Explorar catálogo\n"
        f"{UIEmojis.TREE_BRANCH} {UserEmojis.MENU} `/menu` - Panel de control\n"
        f"{UIEmojis.TREE_END} {UserEmojis.HELP} `/help` - Centro de ayuda\n\n"
        f"{StatusEmojis.INFO} *Tip: Pulsa {UserEmojis.MENU} /menu para comenzar*"
    )
    print("WELCOME MESSAGE:")
    print(welcome_msg)
    
    # Mensaje de resultado de búsqueda simulado
    search_msg = (
        f"{SearchEmojis.RESULTS} **RESULTADOS DE BÚSQUEDA**\n"
        f"┌─────────────────────────────────────┐\n"
        f"│ {SearchEmojis.SEARCH} Query: *samsung s24*              │\n"
        f"│ {NavigationEmojis.PAGE} Página 1/3                       │\n"
        f"└─────────────────────────────────────┘\n\n"
        f"**1.** `CL-SAMS-GALAXY-256GB-RIP-001`\n"
        f"   {RetailerEmojis.PRODUCT} Samsung Galaxy S24 256GB\n"
        f"   {RetailerEmojis.STORE} 3 retailers {PriceEmojis.SPREAD} 8.5% {PriceEmojis.MONEY} $899.990–$989.990\n"
    )
    print("\nSEARCH RESULTS MESSAGE:")
    print(search_msg)
    
    # Mensaje de arbitraje simulado
    arbitrage_msg = (
        f"{ArbitrageEmojis.OPPORTUNITY} **TOP OPORTUNIDADES DE ARBITRAJE**\n"
        f"┌─────────────────────────────────────┐\n"
        f"│ 5 oportunidades detectadas          │\n"
        f"│ {DecoEmojis.FIRE} Máximo potencial de ganancia      │\n"
        f"└─────────────────────────────────────┘\n\n"
        f"**1. {RetailerEmojis.BRAND} Samsung**\n"
        f"   {RetailerEmojis.CATEGORY} Electrónicos\n"
        f"   {ArbitrageEmojis.BUY} **Comprar:** Ripley → {PriceEmojis.MONEY} $899.990\n"
        f"   {ArbitrageEmojis.SELL} **Vender:** Falabella → {PriceEmojis.MONEY} $989.990\n"
        f"   {ArbitrageEmojis.PROFIT} **Ganancia:** *{PriceEmojis.MONEY} $90.000* (10.0% ROI)\n"
        f"   {DecoEmojis.TARGET} Confianza: 95% • Detectada: 3x\n"
    )
    print("\nARBITRAGE MESSAGE:")
    print(arbitrage_msg)

if __name__ == "__main__":
    try:
        print("🚀 Iniciando test de compatibilidad de emojis...")
        print(f"Python version: {sys.version}")
        print(f"Encoding: {sys.stdout.encoding}")
        print()
        
        test_emoji_rendering()
        test_formatting_functions()
        test_mock_bot_messages()
        
        print(f"\n{StatusEmojis.SUCCESS} ¡Todos los tests de emojis pasaron correctamente!")
        print(f"{StatusEmojis.INFO} El bot está listo para usar con la nueva interfaz mejorada.")
        
    except Exception as e:
        print(f"\n{StatusEmojis.ERROR} Error en el test: {e}")
        print("Posible problema de encoding o compatibilidad de emojis.")
        sys.exit(1)