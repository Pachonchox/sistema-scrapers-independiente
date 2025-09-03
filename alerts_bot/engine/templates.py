# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any

def pct(x: float) -> str:
    """Formatear porcentaje con símbolo"""
    return f"{x*100:.1f}%"

def fmt_clp(x: float) -> str:
    """Formatear precio en pesos chilenos"""
    try:
        return f"${int(round(x)):,.0f}".replace(",", ".")
    except Exception:
        return str(x)

def fmt_price_with_trend(current: float, previous: float = None) -> str:
    """Formatear precio con indicador de tendencia si está disponible"""
    price_str = fmt_clp(current)
    if previous and previous != current:
        trend = "📈" if current > previous else "📉"
        change_pct = ((current - previous) / previous) * 100
        return f"💰 {price_str} {trend} ({change_pct:+.1f}%)"
    return f"💰 {price_str}"

def format_spread_msg(internal_sku: str, canonical_name: str, spread_stats: Dict[str, Any]) -> str:
    """Formatear mensaje de alerta de spread con diseño mejorado"""
    return (
        f"💎 *OPORTUNIDAD DE ARBITRAJE DETECTADA*\n"
        f"┌──────────────────────────────────────┐\n"
        f"│ {spread_stats['retailer_count']} retailers • Spread significativo   │\n"
        f"└──────────────────────────────────────┘\n\n"
        f"📦 **SKU:** `{internal_sku}`\n"
        f"🏷️ **Producto:** {canonical_name}\n\n"
        f"💰 **Rango de precios:**\n"
        f"├── 🔻 Mínimo: *{fmt_clp(spread_stats['min_price'])}*\n"
        f"├── 🔺 Máximo: *{fmt_clp(spread_stats['max_price'])}*\n"
        f"└── 📊 Spread: *{pct(spread_stats['spread_pct'])}*\n\n"
        f"🚨 *¡Oportunidad de arbitraje activa!*"
    )

def format_intraday_msg(internal_sku: str, canonical_name: str, delta_stats: Dict[str, Any]) -> str:
    """Formatear mensaje de alerta de movimiento intradía con diseño mejorado"""
    delta_pct = delta_stats['delta_pct']
    trend_emoji = "📈" if delta_pct > 0 else "📉"
    movement_type = "SUBIDA" if delta_pct > 0 else "BAJADA"
    
    return (
        f"{trend_emoji} *MOVIMIENTO INTRADÍA DETECTADO*\n"
        f"┌──────────────────────────────────────┐\n"
        f"│ {movement_type} SIGNIFICATIVA • 24h        │\n"
        f"└──────────────────────────────────────┘\n\n"
        f"📦 **SKU:** `{internal_sku}`\n"
        f"🏷️ **Producto:** {canonical_name}\n"
        f"🏪 **Retailer:** {delta_stats.get('retailer','?')}\n\n"
        f"📊 **Análisis 24h:**\n"
        f"├── 🔻 Mínimo: *{fmt_clp(delta_stats['min_24h'])}*\n"
        f"├── 🔺 Máximo: *{fmt_clp(delta_stats['max_24h'])}*\n"
        f"└── {trend_emoji} Cambio: *{pct(delta_pct)}*\n\n"
        f"⚡ *¡Movimiento de precio relevante!*"
    )
