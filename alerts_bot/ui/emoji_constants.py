# -*- coding: utf-8 -*-
"""
🎨 SISTEMA DE EMOJIS PARA BOT DE TELEGRAM
Constantes de emojis organizadas por categoría para consistencia visual
"""
from __future__ import annotations

# ========================================
# 🔍 BÚSQUEDA & EXPLORACIÓN
# ========================================
class SearchEmojis:
    SEARCH = "🔎"
    FILTER = "🔍" 
    RESULTS = "📋"
    NO_RESULTS = "🤷‍♂️"
    TOP = "🏆"
    TRENDING = "📈"
    STATS = "📊"
    
# ========================================
# 💰 ARBITRAJE & OPORTUNIDADES  
# ========================================
class ArbitrageEmojis:
    OPPORTUNITY = "💎"
    PROFIT = "💰"
    BUY = "🛒"
    SELL = "💸"
    MARGIN = "📈"
    ROI = "💹"
    CONFIDENCE = "🎯"
    FLOW = "🔄"
    DETECTION = "🔍"
    ACTIVE = "🟢"
    POTENTIAL = "💎"
    
# ========================================
# 🛎️ SUSCRIPCIONES & ALERTAS
# ========================================  
class SubscriptionEmojis:
    SUBSCRIBE = "➕"
    UNSUBSCRIBE = "❌"
    SUBSCRIBED = "✅"
    MY_SUBS = "📜"
    ALERT = "🚨"
    NOTIFICATION = "🔔"
    BELL_ON = "🔔"
    BELL_OFF = "🔕"
    SPREAD_ALERT = "🔔"
    MOVEMENT_ALERT = "📈"
    
# ========================================
# 👤 USUARIO & CONFIGURACIÓN
# ========================================
class UserEmojis:
    HOME = "🏠"
    MENU = "📱"
    SETTINGS = "⚙️"
    HELP = "❓"
    USER = "👤"
    WELCOME = "🚀"
    THRESHOLDS = "📊"
    PROFILE = "👥"
    
# ========================================
# 🏪 RETAILERS & PRODUCTOS
# ========================================
class RetailerEmojis:
    STORE = "🛍️"
    RETAILER = "🏪"
    PRODUCT = "📦"
    BRAND = "🏷️"
    CATEGORY = "📂"
    PRICE = "💰"
    STOCK = "📦"
    LINK = "🔗"
    
# ========================================
# 📊 ESTADOS & FEEDBACK
# ========================================
class StatusEmojis:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "💡"
    LOADING = "🔄"
    PROCESSING = "⚡"
    COMPLETED = "✨"
    FAILED = "💥"
    TIMEOUT = "⏰"
    
# ========================================
# 🔧 ADMINISTRACIÓN & SISTEMA
# ========================================
class AdminEmojis:
    ADMIN = "👑"
    BROADCAST = "📢"
    METRICS = "📊"
    SYSTEM = "🔧"
    DATABASE = "💾"
    REFRESH = "🔄"
    PROMOTE = "⬆️"
    DEMOTE = "⬇️"
    SUPERUSER = "👑"
    MAINTENANCE = "🛠️"
    
# ========================================
# 🎯 NAVEGACIÓN & CONTROLES
# ========================================
class NavigationEmojis:
    BACK = "⬅️"
    FORWARD = "➡️"
    NEXT = "▶️"
    PREVIOUS = "◀️"
    UP = "⬆️"
    DOWN = "⬇️"
    PAGE = "📄"
    GOTO = "🎯"
    
# ========================================
# 💹 PRECIOS & MÉTRICAS
# ========================================
class PriceEmojis:
    MONEY = "💰"
    INCREASE = "📈"
    DECREASE = "📉"
    SPREAD = "📊"
    DELTA = "📈"
    MIN_PRICE = "🔻"
    MAX_PRICE = "🔺"
    AVERAGE = "📊"
    PERCENTAGE = "📈"
    CURRENCY = "💵"
    
# ========================================
# 🎨 UTILIDADES Y DECORATIVOS
# ========================================
class DecoEmojis:
    STAR = "⭐"
    FIRE = "🔥"
    SPARKLES = "✨"
    ROCKET = "🚀"
    TARGET = "🎯"
    CROWN = "👑"
    GEM = "💎"
    MAGIC = "🪄"
    CELEBRATION = "🎉"
    
# ========================================
# 📱 INTERFAZ & UX
# ========================================
class UIEmojis:
    BUTTON = "🔘"
    TOGGLE_ON = "🔘"
    TOGGLE_OFF = "⚫"
    SEPARATOR = "│"
    DIVIDER = "━"
    BOX_TOP = "┌"
    BOX_BOTTOM = "└"
    TREE_BRANCH = "├──"
    TREE_END = "└──"
    
# ========================================
# 🚨 FUNCIONES DE UTILIDAD
# ========================================

def format_price_with_emoji(price: float, show_currency: bool = True) -> str:
    """Formatear precio con emoji apropiado"""
    currency = f" {PriceEmojis.CURRENCY}" if show_currency else ""
    return f"{PriceEmojis.MONEY} ${price:,.0f}{currency}".replace(",", ".")

def format_percentage_with_emoji(pct: float, positive_emoji: str = None) -> str:
    """Formatear porcentaje con emoji de tendencia"""
    if positive_emoji is None:
        emoji = PriceEmojis.INCREASE if pct >= 0 else PriceEmojis.DECREASE
    else:
        emoji = positive_emoji if pct >= 0 else PriceEmojis.DECREASE
    return f"{emoji} {pct:+.1f}%"

def create_status_message(status: str, message: str) -> str:
    """Crear mensaje con emoji de estado apropiado"""
    emoji_map = {
        'success': StatusEmojis.SUCCESS,
        'error': StatusEmojis.ERROR, 
        'warning': StatusEmojis.WARNING,
        'info': StatusEmojis.INFO,
        'loading': StatusEmojis.LOADING,
        'processing': StatusEmojis.PROCESSING
    }
    emoji = emoji_map.get(status.lower(), StatusEmojis.INFO)
    return f"{emoji} {message}"

def create_section_header(title: str, emoji: str = None) -> str:
    """Crear header de sección con formato consistente"""
    display_emoji = emoji or DecoEmojis.SPARKLES
    return f"{display_emoji} *{title.upper()}*"

# ========================================
# 🎯 QUICK ACCESS COLLECTIONS
# ========================================

class QuickEmojis:
    """Emojis de acceso rápido para funciones comunes"""
    # Más usados
    SEARCH = SearchEmojis.SEARCH
    HOME = UserEmojis.HOME  
    HELP = UserEmojis.HELP
    SUCCESS = StatusEmojis.SUCCESS
    ERROR = StatusEmojis.ERROR
    MONEY = PriceEmojis.MONEY
    SUBSCRIBE = SubscriptionEmojis.SUBSCRIBE
    
    # Navegación común
    BACK = NavigationEmojis.BACK
    NEXT = NavigationEmojis.NEXT
    MENU = UserEmojis.MENU
    
    # Estados frecuentes
    LOADING = StatusEmojis.LOADING
    WARNING = StatusEmojis.WARNING
    INFO = StatusEmojis.INFO

# ========================================
# 🔄 COMPATIBILIDAD CON DICCIONARIOS
# ========================================
# Para compatibilidad con código legacy que espera diccionarios

PRECIOS_EMOJIS = {
    "ALZA": "📈",
    "BAJA": "📉", 
    "MONEY": "💰",
    "TREND_UP": "📈",
    "TREND_DOWN": "📉",
    "STABLE": "📊"
}

ARBITRAGE_EMOJIS = {
    "PREMIUM": "💎",
    "BUENA": "💰",
    "BASICA": "🔵",
    "BUY": "🛒",
    "SELL": "💸"
}

ALERTAS_EMOJIS = {
    "ALERT": "🚨",
    "NOTIFICATION": "🔔",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "WARNING": "⚠️"
}

ESTADOS_EMOJIS = {
    "SUCCESS": "✅",
    "ERROR": "❌", 
    "WARNING": "⚠️",
    "INFO": "ℹ️",
    "LOADING": "⏳"
}