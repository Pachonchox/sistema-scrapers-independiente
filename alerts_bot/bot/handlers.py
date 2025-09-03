# -*- coding: utf-8 -*-
from __future__ import annotations
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import math
import hashlib
import json
import time
from ..engine.templates import fmt_clp, pct
from ..maintenance import refresh_bot_tables
from ..ui.emoji_constants import *
from ..ui.emoji_constants import format_price_with_emoji
import psycopg2
from psycopg2.extras import RealDictCursor

def is_admin(storage, uid: int) -> bool:
    return storage.is_superuser(uid)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uname = update.effective_user.username or ""
    storage = context.bot_data["storage"]
    config = context.bot_data["config"]

    storage.register_user(uid, uname)
    # seed superusers only once at boot, but here we can reinforce

    s_th, d_th = storage.get_thresholds(uid, config.default_spread_threshold, config.default_delta_threshold)
    # Mensaje de bienvenida renovado con sistema de emojis
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
        f"{UserEmojis.SETTINGS} **Configuración actual:**\n"
        f"{UIEmojis.TREE_BRANCH} {PriceEmojis.SPREAD} Spread: {int(s_th*100)}%\n"
        f"{UIEmojis.TREE_BRANCH} {PriceEmojis.DELTA} Delta: {int(d_th*100)}%\n"
        f"{UIEmojis.TREE_END} {SubscriptionEmojis.BELL_ON} Alertas: Activas\n\n"
        f"{StatusEmojis.INFO} *Tip: Pulsa {UserEmojis.MENU} /menu para comenzar*"
    )
    try:
        await update.message.reply_markdown(welcome_msg)
    except Exception:
        # Fallback sin emojis si hay problemas de codificación
        simple_msg = (
            "Bienvenido al Bot de Alertas de Precios!\n"
            f"Comandos: /menu /buscar /help\n"
            f"Umbrales: spread={int(s_th*100)}% delta={int(d_th*100)}%"
        )
        await update.message.reply_text(simple_msg)
    try:
        await show_main_menu(update, context)
    except Exception:
        pass

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = (
        f"{UserEmojis.HELP} *CENTRO DE AYUDA*\n"
        f"┌─────────────────────────────────────┐\n"
        f"│ Guía completa de comandos           │\n"
        f"└─────────────────────────────────────┘\n\n"
        f"{SearchEmojis.SEARCH} **BÚSQUEDA & EXPLORACIÓN:**\n"
        f"{UIEmojis.TREE_BRANCH} `/buscar <producto>` — Explorar catálogo\n"
        f"{UIEmojis.TREE_BRANCH} `/top` — {SearchEmojis.TOP} Top spreads del día\n"
        f"{UIEmojis.TREE_END} `/menu` — {UserEmojis.HOME} Panel principal\n\n"
        f"{SubscriptionEmojis.ALERT} **SUSCRIPCIONES:**\n"  
        f"{UIEmojis.TREE_BRANCH} `/subscribe <SKU>` — {SubscriptionEmojis.SUBSCRIBE} Suscribirse\n"
        f"{UIEmojis.TREE_BRANCH} `/unsubscribe <SKU>` — {SubscriptionEmojis.UNSUBSCRIBE} Cancelar\n"
        f"{UIEmojis.TREE_END} `/mysubs` — {SubscriptionEmojis.MY_SUBS} Ver mis alertas\n\n"
        f"{UserEmojis.SETTINGS} **CONFIGURACIÓN:**\n"
        f"{UIEmojis.TREE_BRANCH} `/setspread <5>` — {PriceEmojis.SPREAD} Umbral spread\n"
        f"{UIEmojis.TREE_BRANCH} `/setdelta <10>` — {PriceEmojis.DELTA} Umbral intradía\n"
        f"{UIEmojis.TREE_BRANCH} `/summary_on` — {SubscriptionEmojis.BELL_ON} Resumen diario ON\n"
        f"{UIEmojis.TREE_END} `/summary_off` — {SubscriptionEmojis.BELL_OFF} Resumen diario OFF\n\n"
        f"{ArbitrageEmojis.OPPORTUNITY} **ARBITRAJE:**\n"
        f"{UIEmojis.TREE_BRANCH} `/arbitrage` — {ArbitrageEmojis.PROFIT} Ver oportunidades\n"
        f"{UIEmojis.TREE_END} `/arbitrage_stats` — {AdminEmojis.METRICS} Estadísticas\n\n"
        f"{AdminEmojis.ADMIN} **ADMINISTRACIÓN:**\n"
        f"`/stats` `/broadcast` `/promote` `/demote`\n\n"
        f"{StatusEmojis.INFO} *¿Necesitas ayuda? Usa* {UserEmojis.MENU} `/menu`"
    )
    await update.message.reply_markdown(help_msg)

async def cmd_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Alias a /buscar
    context.args = context.args or []
    return await cmd_buscar(update, context)

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        usage_msg = (
            f"{StatusEmojis.INFO} **Uso del comando buscar:**\n\n"
            f"{SearchEmojis.SEARCH} `/buscar <producto>`\n\n"
            f"**Ejemplos:**\n"
            f"{UIEmojis.TREE_BRANCH} `/buscar samsung s24`\n"
            f"{UIEmojis.TREE_BRANCH} `/buscar iphone 15 256gb`\n" 
            f"{UIEmojis.TREE_END} `/buscar notebook lenovo`\n\n"
            f"{StatusEmojis.INFO} *Tip: Sé específico para mejores resultados*"
        )
        await update.message.reply_markdown(usage_msg)
        return
    query = " ".join(context.args)
    repo = context.bot_data["repo"]
    storage = context.bot_data["storage"]

    try:
        results = repo.search_products_enriched(query, limit=50)
    except Exception:
        results = []
    if not results:
        no_results_msg = (
            f"{SearchEmojis.NO_RESULTS} **No se encontraron resultados**\n\n"
            f"Para: *{query}*\n\n"
            f"{StatusEmojis.INFO} **Sugerencias:**\n"
            f"{UIEmojis.TREE_BRANCH} Intenta términos más generales\n"
            f"{UIEmojis.TREE_BRANCH} Verifica la ortografía\n"
            f"{UIEmojis.TREE_END} Usa marcas conocidas: Samsung, Apple, LG...\n\n"
            f"{SearchEmojis.SEARCH} *Inténtalo de nuevo con otros términos*"
        )
        await update.message.reply_markdown(no_results_msg)
        return

    # métricas
    try:
        storage.incr_hourly_counter("search_queries")
    except Exception:
        pass

    # cachear resultados (solo SKUs y campos necesarios)
    skus = [r["internal_sku"] for r in results]
    cache = {
        "q": query,
        "skus": skus,
        "page": 0,
        "ts": int(time.time())
    }
    uid = update.effective_user.id
    cache_hash = hashlib.md5(("|".join(skus)).encode("utf-8")).hexdigest()[:10]
    cache_key = f"search:last:{uid}:{cache_hash}"
    try:
        storage.r.setex(cache_key, 600, json.dumps(cache))
    except Exception:
        cache_key = None

    # render primera página
    await _render_search_page(update, context, results, query, page=0, cache_key=cache_key)

async def _render_search_page(update: Update, context: ContextTypes.DEFAULT_TYPE, results, query: str, page: int, cache_key: str | None):
    page_size = 10
    start = page * page_size
    end = min(len(results), start + page_size)
    subset = results[start:end]
    if not subset:
        await update.message.reply_text("Sin resultados en esta página.")
        return

    # Header mejorado para resultados
    total_pages = math.ceil(len(results)/page_size)
    lines = [
        f"{SearchEmojis.RESULTS} **RESULTADOS DE BÚSQUEDA**",
        f"┌─────────────────────────────────────┐",
        f"│ {SearchEmojis.SEARCH} Query: *{query}*{' ' * (24 - len(query))}│",
        f"│ {NavigationEmojis.PAGE} Página {page+1}/{total_pages}{' ' * (22 - len(str(page+1)) - len(str(total_pages)))}│",
        f"└─────────────────────────────────────┘\n"
    ]
    
    buttons = []
    for idx, r in enumerate(subset, start=1 + start):
        name = r.get('normalized_name') or f"{r.get('brand','') or ''} {r.get('model','') or ''}".strip()
        sku = r['internal_sku']
        minp = r.get('min_price')
        maxp = r.get('max_price')
        spread = r.get('spread_pct')
        rc = r.get('retailer_count') or 0
        
        # Formato mejorado de precios
        price_str = ""
        if isinstance(minp, (int, float)) and isinstance(maxp, (int, float)) and minp and maxp:
            price_str = f" {PriceEmojis.MONEY} {fmt_clp(minp)}–{fmt_clp(maxp)}"
        
        spread_str = f" {PriceEmojis.SPREAD} {pct(spread)}" if isinstance(spread, (int, float)) and spread is not None else ""
        
        line = f"**{idx}.** `{sku}`\n   {RetailerEmojis.PRODUCT} {name}\n   {RetailerEmojis.STORE} {rc} retailers{spread_str}{price_str}\n"
        lines.append(line)
        buttons.append([InlineKeyboardButton(text=f"{SubscriptionEmojis.SUBSCRIBE} Suscribirse", callback_data=f"sub:{sku}:{page}")])

    # Navegación mejorada
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=f"{NavigationEmojis.PREVIOUS} Anterior", callback_data=f"pg:{page-1}:{cache_key or ''}"))
    if end < len(results):
        nav.append(InlineKeyboardButton(text=f"Siguiente {NavigationEmojis.NEXT}", callback_data=f"pg:{page+1}:{cache_key or ''}"))
    if nav:
        buttons.append(nav)
    
    # Botón de vuelta al menú
    buttons.append([InlineKeyboardButton(text=f"{NavigationEmojis.BACK} Volver al Menú", callback_data="menu:home")])

    text = "\n".join(lines)
    await update.message.reply_markdown(text, reply_markup=InlineKeyboardMarkup(buttons))

async def cb_search_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Navegación de páginas de búsqueda"""
    storage = context.bot_data["storage"]
    repo = context.bot_data["repo"]
    if not update.callback_query:
        return
    await update.callback_query.answer()
    data = update.callback_query.data or ""
    parts = data.split(":", 2)
    if len(parts) < 3:
        return
    _, page_str, cache_key = parts
    try:
        page = int(page_str)
    except Exception:
        page = 0
    # cargar cache
    try:
        raw = storage.r.get(cache_key)
        cache = json.loads(raw) if raw else {}
    except Exception:
        cache = {}
    skus = cache.get("skus") or []
    query = cache.get("q") or ""
    # reconstruir resultados mínimos para mostrar (agnóstico de backend)
    results = []
    for sku in skus:
        try:
            spread = None
            try:
                spread = context.bot_data["repo"].current_spread(sku)
            except Exception:
                spread = None
            row = {
                "internal_sku": sku,
                "brand": None,
                "model": None,
                "normalized_name": sku,
                "min_price": (spread or {}).get("min_price"),
                "max_price": (spread or {}).get("max_price"),
                "spread_pct": (spread or {}).get("spread_pct"),
                "retailer_count": (spread or {}).get("retailer_count"),
            }
            results.append(row)
        except Exception:
            results.append({"internal_sku": sku, "brand": None, "model": None, "normalized_name": sku})
    # editar mensaje con la página
    try:
        # reutilizar función de render: necesitamos objeto con message context; usaremos edit_message_text
        page_size = 10
        start = page * page_size
        end = min(len(results), start + page_size)
        subset = results[start:end]
        lines = [f"Resultados para: *{query}* (página {page+1}/{math.ceil(len(results)/page_size)})\n"]
        buttons = []
        for idx, r in enumerate(subset, start=1 + start):
            name = r.get('normalized_name') or f"{r.get('brand','') or ''} {r.get('model','') or ''}".strip()
            sku = r['internal_sku']
            minp = r.get('min_price')
            maxp = r.get('max_price')
            spread = r.get('spread_pct')
            rc = r.get('retailer_count') or 0
            price_str = ""
            if isinstance(minp, (int, float)) and isinstance(maxp, (int, float)) and minp and maxp:
                price_str = f" | {fmt_clp(minp)}–{fmt_clp(maxp)}"
            spread_str = f" • {pct(spread)}" if isinstance(spread, (int, float)) and spread is not None else ""
            line = f"{idx}. `{sku}` — {name} (🛍️ {rc}{spread_str}{price_str})"
            lines.append(line)
            buttons.append([InlineKeyboardButton(text=f"➕ Suscribirse {sku}", callback_data=f"sub:{sku}:{page}")])
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="◀️ Anterior", callback_data=f"pg:{page-1}:{cache_key}"))
        if end < len(results):
            nav.append(InlineKeyboardButton(text="Siguiente ▶️", callback_data=f"pg:{page+1}:{cache_key}"))
        if nav:
            buttons.append(nav)
        text = "\n".join(lines)
        await update.callback_query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        pass

async def cb_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    parts = data.split(":")
    if len(parts) < 2:
        return
    _, sku, *rest = parts
    uid = update.effective_user.id
    try:
        storage.subscribe(uid, sku)
        storage.incr_hourly_counter("search_subscribe_clicks")
        success_msg = f"{StatusEmojis.SUCCESS} ¡Suscrito a {sku}! Recibirás alertas de cambios."
    except Exception:
        success_msg = f"{StatusEmojis.ERROR} Error al suscribir a {sku}"
        
    await update.callback_query.answer(text=success_msg, show_alert=False)

async def cb_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    parts = data.split(":")
    if len(parts) < 2:
        return
    _, sku, *rest = parts
    uid = update.effective_user.id
    try:
        storage.unsubscribe(uid, sku)
        storage.incr_hourly_counter("unsubscribe_clicks")
        success_msg = f"{StatusEmojis.SUCCESS} Te has desuscrito de {sku}"
    except Exception:
        success_msg = f"{StatusEmojis.ERROR} Error al desuscribir de {sku}"
        
    await update.callback_query.answer(text=success_msg, show_alert=False)

def _menu_keyboard(summary_on: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔎 Buscar", callback_data="menu:buscar"),
         InlineKeyboardButton(text="📜 Mis suscripciones", callback_data="menu:mysubs")],
        [InlineKeyboardButton(text="➕ Suscribirse por SKU", callback_data="menu:subscribe_prompt")],
        [InlineKeyboardButton(text="⚙️ Umbrales", callback_data="menu:thresholds"),
         InlineKeyboardButton(text=("🔕 Resumen OFF" if summary_on else "🔔 Resumen ON"), callback_data="menu:summary_toggle")],
        [InlineKeyboardButton(text="❓ Ayuda", callback_data="menu:help")],
    ]
    return InlineKeyboardMarkup(rows)

def _menu_keyboard_v2(summary_on: bool) -> InlineKeyboardMarkup:
    """Menú principal rediseñado con sistema de emojis mejorado"""
    summary_emoji = SubscriptionEmojis.BELL_OFF if summary_on else SubscriptionEmojis.BELL_ON
    summary_text = "🔕 Resumen OFF" if summary_on else "🔔 Resumen ON"
    
    rows = [
        [InlineKeyboardButton(text=f"{SearchEmojis.TOP} Top del Día", callback_data="menu:top"),
         InlineKeyboardButton(text=f"{SearchEmojis.SEARCH} Buscar", callback_data="menu:buscar")],
        [InlineKeyboardButton(text=f"{SubscriptionEmojis.MY_SUBS} Mis Suscripciones", callback_data="menu:mysubsv2")],
        [InlineKeyboardButton(text=f"{SubscriptionEmojis.SUBSCRIBE} Suscribirse por SKU", callback_data="menu:subscribe_prompt")],
        [InlineKeyboardButton(text=f"{UserEmojis.SETTINGS} Umbrales", callback_data="menu:thresholds"),
         InlineKeyboardButton(text=summary_text, callback_data="menu:summary_toggle")],
        [InlineKeyboardButton(text=f"{ArbitrageEmojis.OPPORTUNITY} Arbitraje", callback_data="menu:arbitrage")],
        [InlineKeyboardButton(text=f"{UserEmojis.HELP} Ayuda", callback_data="menu:help")],
    ]
    return InlineKeyboardMarkup(rows)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    config = context.bot_data["config"]
    uid = update.effective_user.id
    s_th, d_th = storage.get_thresholds(uid, config.default_spread_threshold, config.default_delta_threshold)
    user = storage.get_user(uid)
    summary_on = str(user.get("summary_on", "0")) == "1"
    
    # Menú principal rediseñado
    menu_text = (
        f"{UserEmojis.HOME} *PANEL PRINCIPAL*\n"
        f"┌─────────────────────────────────────┐\n"
        f"│ {ArbitrageEmojis.ACTIVE} Centro de Control Inteligente     │\n"  
        f"│ Elige tu próxima acción             │\n"
        f"└─────────────────────────────────────┘\n\n"
        f"{UserEmojis.SETTINGS} **Estado actual:**\n"
        f"{UIEmojis.TREE_BRANCH} {PriceEmojis.SPREAD} Spread: *{int(s_th*100)}%*\n"
        f"{UIEmojis.TREE_BRANCH} {PriceEmojis.DELTA} Delta: *{int(d_th*100)}%*\n"
        f"{UIEmojis.TREE_END} {SubscriptionEmojis.BELL_ON if summary_on else SubscriptionEmojis.BELL_OFF} Resumen: {'ON' if summary_on else 'OFF'}\n\n"
        f"{StatusEmojis.INFO} *Selecciona una opción del menú:*"
    )
    await update.message.reply_markdown(menu_text, reply_markup=_menu_keyboard_v2(summary_on))

async def cb_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    config = context.bot_data["config"]
    q = update.callback_query
    if not q:
        return
    await q.answer()
    uid = update.effective_user.id
    data = q.data or ""
    action = data.split(":", 1)[1] if ":" in data else data
    def kb():
        return _menu_keyboard_v2(str(storage.get_user(uid).get("summary_on","0")) == "1")
    if action == "mysubsv2":
        subs = storage.list_subscriptions(uid)
        if not subs:
            await q.edit_message_text(text="No tienes suscripciones. Usa /buscar y suscríbete con un botón.", parse_mode="Markdown", reply_markup=kb())
            return
        lines = ["*Tus suscripciones:*\n"]
        buttons = []
        for s in subs:
            lines.append(f"`{s}`")
            buttons.append([InlineKeyboardButton(text=f"❌ Desuscribirse {s}", callback_data=f"unsub:{s}")])
        buttons.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:home")])
        await q.edit_message_text(text="\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return
    if action == "top":
        try:
            top = context.bot_data["repo"].top_spreads(limit=10)
        except Exception:
            top = []
        if not top:
            await q.edit_message_text(text="No hay datos suficientes para el top del día.", reply_markup=kb())
            return
        lines = ["*Top spreads del día*\n"]
        buttons = []
        for i, r in enumerate(top, start=1):
            sku = r.get('internal_sku')
            minp = r.get('min_price')
            maxp = r.get('max_price')
            spread = r.get('spread_pct')
            rc = r.get('retailer_count') or 0
            price_str = ""
            if isinstance(minp, (int, float)) and isinstance(maxp, (int, float)) and minp and maxp:
                price_str = f" | {fmt_clp(minp)}-{fmt_clp(maxp)}"
            spread_str = f" {pct(spread)}" if isinstance(spread, (int, float)) and spread is not None else ""
            lines.append(f"{i}. `{sku}` ({rc} retailers){spread_str}{price_str}")
            buttons.append([InlineKeyboardButton(text=f"📬 Suscribirse {sku}", callback_data=f"sub:{sku}:0")])
        await q.edit_message_text(text="\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return
    if action == "home":
        try:
            summary_on2 = str(storage.get_user(uid).get("summary_on","0")) == "1"
        except Exception:
            summary_on2 = False
        await q.edit_message_text(text="Elige una opción:", reply_markup=_menu_keyboard_v2(summary_on2))
        return
    if action == "buscar":
        txt = (
            "🔎 Para buscar, escribe:\n"
            "`/buscar <marca|modelo|producto>`\n"
            "Ejemplos: `/buscar s24 256`, `/buscar iphone 15 256`"
        )
        await q.edit_message_text(text=txt, parse_mode="Markdown", reply_markup=kb())
        return
    if action == "mysubs":
        subs = storage.list_subscriptions(uid)
        txt = ("No tienes suscripciones. Usa /buscar y suscríbete con un botón." if not subs
               else "*Tus suscripciones:*\n" + "\n".join(f"`{s}`" for s in subs))
        await q.edit_message_text(text=txt, parse_mode="Markdown", reply_markup=kb())
        return
    if action == "subscribe_prompt":
        await q.edit_message_text(text="Escribe: `/subscribe <INTERNAL_SKU>`", parse_mode="Markdown", reply_markup=kb())
        return
    if action == "thresholds":
        s_th, d_th = storage.get_thresholds(uid, config.default_spread_threshold, config.default_delta_threshold)
        txt = (
            f"⚙️ Umbrales actuales:\n• spread: {int(s_th*100)}%\n• delta: {int(d_th*100)}%\n\n"
            "Para cambiar: `/setspread 5` o `/setdelta 10`"
        )
        await q.edit_message_text(text=txt, parse_mode="Markdown", reply_markup=kb())
        return
    if action == "summary_toggle":
        user = storage.get_user(uid)
        current = str(user.get("summary_on", "0")) == "1"
        storage.set_summary(uid, not current)
        status = "activado" if not current else "desactivado"
        await q.edit_message_text(text=f"Resumen diario {status}.", reply_markup=_menu_keyboard_v2(not current))
        return
    if action == "arbitrage":
        # Mostrar opciones de arbitraje
        arbitrage_msg = (
            f"{ArbitrageEmojis.OPPORTUNITY} **SISTEMA DE ARBITRAJE**\n"
            f"┌─────────────────────────────────────┐\n"
            f"│ {DecoEmojis.FIRE} Centro de oportunidades         │\n"
            f"│ de ganancia en tiempo real          │\n" 
            f"└─────────────────────────────────────┘\n\n"
            f"{StatusEmojis.INFO} **Opciones disponibles:**\n"
            f"{UIEmojis.TREE_BRANCH} `/arbitrage` - {ArbitrageEmojis.PROFIT} Ver oportunidades\n"
            f"{UIEmojis.TREE_BRANCH} `/arbitrage_stats` - {AdminEmojis.METRICS} Estadísticas\n"
            f"{UIEmojis.TREE_END} `/arbitrage_by_retailer <retailer>` - Por tienda\n\n"
            f"{DecoEmojis.TARGET} *Detectamos automáticamente las mejores oportunidades*"
        )
        await q.edit_message_text(text=arbitrage_msg, parse_mode="Markdown", reply_markup=kb())
        return
        
    if action == "help":
        help_menu_msg = (
            f"{UserEmojis.HELP} **CENTRO DE AYUDA RÁPIDA**\n"
            f"┌─────────────────────────────────────┐\n"
            f"│ Comandos principales del sistema    │\n"
            f"└─────────────────────────────────────┘\n\n"
            f"{SearchEmojis.SEARCH} **Búsqueda:**\n"
            f"`/buscar <producto>` - Explorar catálogo\n"
            f"`/top` - {SearchEmojis.TOP} Top del día\n\n"
            f"{SubscriptionEmojis.ALERT} **Suscripciones:**\n" 
            f"`/subscribe <SKU>` - {SubscriptionEmojis.SUBSCRIBE} Activar alertas\n"
            f"`/mysubs` - {SubscriptionEmojis.MY_SUBS} Ver mis alertas\n\n"
            f"{UserEmojis.SETTINGS} **Configuración:**\n"
            f"`/setspread <5>` - Umbral spread\n"
            f"`/setdelta <10>` - Umbral intradía\n\n"
            f"{StatusEmojis.INFO} *Usa el menú para acceso rápido*"
        )
        await q.edit_message_text(text=help_menu_msg, parse_mode="Markdown", reply_markup=kb())
        return

async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        usage_msg = (
            f"{StatusEmojis.INFO} **Uso del comando suscribirse:**\n\n"
            f"{SubscriptionEmojis.SUBSCRIBE} `/subscribe <INTERNAL_SKU>`\n\n"
            f"**Ejemplo:**\n"
            f"`/subscribe CL-SAMS-GALAXY-256GB-RIP-001`\n\n"
            f"{StatusEmojis.INFO} *Tip: Obtén SKUs usando* {SearchEmojis.SEARCH} `/buscar`"
        )
        await update.message.reply_markdown(usage_msg)
        return
        
    sku = context.args[0].strip()
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    
    try:
        storage.subscribe(uid, sku)
        success_msg = (
            f"{StatusEmojis.SUCCESS} *¡SUSCRIPCIÓN ACTIVADA!*\n\n"
            f"📦 **SKU:** `{sku}`\n"
            f"{SubscriptionEmojis.BELL_ON} Recibirás alertas cuando:\n"
            f"├── 💎 Haya oportunidades de arbitraje\n"
            f"└── 📈 Ocurran movimientos de precio\n\n"
            f"{UserEmojis.MENU} *Ve tus suscripciones en* `/mysubs`"
        )
        await update.message.reply_markdown(success_msg)
    except Exception as e:
        error_msg = f"{StatusEmojis.ERROR} Error al suscribirse a `{sku}`: {str(e)}"
        await update.message.reply_markdown(error_msg)

async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        usage_msg = (
            f"{StatusEmojis.INFO} **Uso del comando desuscribirse:**\n\n"
            f"{SubscriptionEmojis.UNSUBSCRIBE} `/unsubscribe <INTERNAL_SKU>`\n\n"
            f"**Ejemplo:**\n"
            f"`/unsubscribe CL-SAMS-GALAXY-256GB-RIP-001`\n\n"
            f"{StatusEmojis.INFO} *Ver suscripciones actuales:* {SubscriptionEmojis.MY_SUBS} `/mysubs`"
        )
        await update.message.reply_markdown(usage_msg)
        return
        
    sku = context.args[0].strip()
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    
    try:
        storage.unsubscribe(uid, sku)
        success_msg = (
            f"{StatusEmojis.SUCCESS} *SUSCRIPCIÓN CANCELADA*\n\n"
            f"📦 **SKU:** `{sku}`\n"
            f"{SubscriptionEmojis.BELL_OFF} Ya no recibirás alertas de este producto\n\n"
            f"{UserEmojis.MENU} *Ver suscripciones restantes:* `/mysubs`"
        )
        await update.message.reply_markdown(success_msg)
    except Exception as e:
        error_msg = f"{StatusEmojis.ERROR} Error al desuscribirse de `{sku}`: {str(e)}"
        await update.message.reply_markdown(error_msg)

async def cmd_mysubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    subs = storage.list_subscriptions(uid)
    
    if not subs:
        no_subs_msg = (
            f"{SubscriptionEmojis.MY_SUBS} **MIS SUSCRIPCIONES**\n"
            f"┌─────────────────────────────────────┐\n"
            f"│ {StatusEmojis.INFO} No tienes suscripciones activas     │\n"
            f"└─────────────────────────────────────┘\n\n"
            f"{StatusEmojis.INFO} **Para comenzar:**\n"
            f"{UIEmojis.TREE_BRANCH} {SearchEmojis.SEARCH} Usa `/buscar <producto>` para explorar\n"
            f"{UIEmojis.TREE_END} {SubscriptionEmojis.SUBSCRIBE} Pulsa suscribirse en los resultados\n\n"
            f"{UserEmojis.MENU} *Volver al menú principal:* `/menu`"
        )
        await update.message.reply_markdown(no_subs_msg)
        return
        
    # Mostrar suscripciones con botones para desuscribirse
    subs_msg = (
        f"{SubscriptionEmojis.MY_SUBS} **MIS SUSCRIPCIONES ACTIVAS**\n"
        f"┌─────────────────────────────────────┐\n"  
        f"│ {len(subs)} productos monitoreados          │\n"
        f"└─────────────────────────────────────┘\n\n"
        f"{SubscriptionEmojis.BELL_ON} **Recibes alertas de:**\n"
    )
    
    buttons = []
    for i, sub in enumerate(subs, 1):
        subs_msg += f"{UIEmojis.TREE_BRANCH if i < len(subs) else UIEmojis.TREE_END} `{sub}`\n"
        buttons.append([InlineKeyboardButton(text=f"{SubscriptionEmojis.UNSUBSCRIBE} Desuscribir {sub[:20]}...", callback_data=f"unsub:{sub}")])
    
    subs_msg += f"\n{StatusEmojis.INFO} *Usa los botones para gestionar suscripciones*"
    
    # Agregar botón de vuelta al menú
    buttons.append([InlineKeyboardButton(text=f"{NavigationEmojis.BACK} Volver al Menú", callback_data="menu:home")])
    
    await update.message.reply_markdown(subs_msg, reply_markup=InlineKeyboardMarkup(buttons))

async def cmd_setspread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /setspread <porcentaje>, ej: 5")
        return
    try:
        pct = float(context.args[0]) / 100.0
    except Exception:
        await update.message.reply_text("Valor inválido.")
        return
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    storage.set_thresholds(uid, spread=pct)
    await update.message.reply_text(f"Umbral spread fijado en {int(pct*100)}%.")

async def cmd_setdelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /setdelta <porcentaje>, ej: 10")
        return
    try:
        pct = float(context.args[0]) / 100.0
    except Exception:
        await update.message.reply_text("Valor inválido.")
        return
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    storage.set_thresholds(uid, delta=pct)
    await update.message.reply_text(f"Umbral intradía fijado en {int(pct*100)}%.")

async def cmd_summary_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    storage.set_summary(uid, True)
    await update.message.reply_text("Resumen diario activado.")

async def cmd_summary_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    storage.set_summary(uid, False)
    await update.message.reply_text("Resumen diario desactivado.")

# ----- admin -----
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    if not is_admin(storage, uid):
        await update.message.reply_text("No autorizado.")
        return
    n_users = len(storage.all_users())
    n_skus = len(storage.all_subscribed_skus())
    await update.message.reply_text(f"Usuarios: {n_users} | SKUs suscritos: {n_skus}")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    if not is_admin(storage, uid):
        await update.message.reply_text("No autorizado.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /broadcast <texto>")
        return
    txt = " ".join(context.args)
    for u in storage.all_users():
        try:
            await context.application.bot.send_message(chat_id=u, text=txt)
        except Exception:
            pass
    await update.message.reply_text("Broadcast enviado.")

async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    if not is_admin(storage, uid):
        await update.message.reply_text("No autorizado.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Uso: /promote <user_id>")
        return
    target = int(context.args[0])
    storage.promote(target)
    await update.message.reply_text(f"Usuario {target} promovido.")

async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    if not is_admin(storage, uid):
        await update.message.reply_text("No autorizado.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Uso: /demote <user_id>")
        return
    target = int(context.args[0])
    storage.demote(target)
    await update.message.reply_text(f"Usuario {target} degradado.")


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra top de spreads del día con botones para suscribirse."""
    repo = context.bot_data["repo"]
    try:
        top = repo.top_spreads(limit=10)
    except Exception:
        top = []
    if not top:
        await update.message.reply_text("No hay suficientes datos para el top del día.")
        return
    lines = ["*Top spreads del día*\n"]
    buttons = []
    for i, r in enumerate(top, start=1):
        sku = r.get('internal_sku')
        minp = r.get('min_price')
        maxp = r.get('max_price')
        spread = r.get('spread_pct')
        rc = r.get('retailer_count') or 0
        price_str = ""
        if isinstance(minp, (int, float)) and isinstance(maxp, (int, float)) and minp and maxp:
            price_str = f" | {fmt_clp(minp)}-{fmt_clp(maxp)}"
        spread_str = f" {pct(spread)}" if isinstance(spread, (int, float)) and spread is not None else ""
        lines.append(f"{i}. `{sku}` ({rc} retailers){spread_str}{price_str}")
        buttons.append([InlineKeyboardButton(text=f"? Suscribirse {sku}", callback_data=f"sub:{sku}:0")])
    await update.message.reply_markdown("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))

async def cmd_refresh_bot_tables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    if not storage.is_superuser(uid):
        await update.message.reply_text("No autorizado.")
        return
    await update.message.reply_text("Refrescando tablas del bot...")
    try:
        import asyncio
        cfg = context.bot_data["config"]
        res = await asyncio.to_thread(refresh_bot_tables, cfg.database_url)
        if res.get("success"):
            await update.message.reply_text("✅ Tablas bot.* refrescadas")
        else:
            await update.message.reply_text("⚠️ No se pudo refrescar tablas bot.*")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_sysmetrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage = context.bot_data["storage"]
    uid = update.effective_user.id
    if not storage.is_superuser(uid):
        await update.message.reply_text("No autorizado.")
        return
    repo = context.bot_data["repo"]
    try:
        m = repo.system_metrics(limit_samples=5)
    except Exception as e:
        await update.message.reply_text(f"❌ Error obteniendo métricas: {e}")
        return

    # Mensaje 1: resumen y retailers
    s = m.get('stats', {})
    lines = ["*Métricas del Sistema*",
             f"Productos totales: {s.get('total_products')}",
             f"Activos: {s.get('active_products','-')}",
             f"Con precio hoy: {s.get('products_priced_today','-')}",
             f"Cambios de precio hoy: {s.get('price_changes_today','-')}"
    ]
    br = m.get('by_retailer', [])
    if br:
        lines.append("""
*Por retailer (hoy):*
""".strip())
        for r in br[:10]:
            lines.append(f"- {r.get('retailer')}: {r.get('products')} productos")
    await update.message.reply_markdown("\n".join(lines))

    # Mensaje 2: cambios (top drops/increases)
    drops = m.get('top_drops', [])
    incs = m.get('top_increases', [])
    if drops or incs:
        l2 = ["*Top Cambios 24h*", "_Bajadas:_"]
        for d in drops:
            l2.append(f"- `{d.get('internal_sku')}` {d.get('retailer','')} ({d.get('delta_pct',0):+.1f}%)")
        l2.append("_Subidas:_")
        for x in incs:
            l2.append(f"- `{x.get('internal_sku')}` {x.get('retailer','')} ({x.get('delta_pct',0):+.1f}%)")
        await update.message.reply_markdown("\n".join(l2))

    # Mensaje 3: scrapers por hora
    hourly = m.get('scrapers_hourly', [])
    if hourly:
        l3 = ["*Scrapers por hora (hoy)*"]
        for h in hourly[:12]:
            l3.append(f"- {h.get('hour')}: rows={h.get('rows')} productos={h.get('products')}")
        await update.message.reply_markdown("\n".join(l3))

    # Mensaje 4: issues de links
    li = m.get('link_issues', {})
    if li:
        l4 = ["*Issues de links / datos (heurísticas)*"]
        for k, v in li.items():
            label = {
                'null_or_empty': 'Links nulos/vacíos',
                'non_http': 'Links no http(s)',
                'no_price_today': 'Productos sin precio hoy',
                'stale_3d': 'Productos stale (>3 días)'
            }.get(k, k)
            l4.append(f"- {label}: {v}")
        await update.message.reply_markdown("\n".join(l4))

# ===============================
# 💰 COMANDOS DE ARBITRAJE
# ===============================

def _get_arbitrage_connection():
    """Get connection to PostgreSQL arbitrage database"""
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="price_orchestrator", 
        user="orchestrator",
        password="orchestrator_2025",
        cursor_factory=RealDictCursor
    )

async def cmd_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar top oportunidades de arbitraje activas"""
    try:
        conn = _get_arbitrage_connection()
        cursor = conn.cursor()
        
        # Top 10 oportunidades por margen
        cursor.execute("""
            SELECT 
                marca_producto,
                categoria_producto,
                retailer_compra,
                retailer_venta,
                precio_compra,
                precio_venta,
                margen_bruto,
                diferencia_porcentaje as roi,
                confidence_score,
                times_detected,
                fecha_deteccion
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
            ORDER BY margen_bruto DESC 
            LIMIT 10
        """)
        
        opportunities = cursor.fetchall()
        conn.close()
        
        if not opportunities:
            no_opp_msg = (
                f"{ArbitrageEmojis.OPPORTUNITY} **SISTEMA DE ARBITRAJE**\n"
                f"┌─────────────────────────────────────┐\n"
                f"│ {StatusEmojis.INFO} No hay oportunidades activas       │\n"
                f"│ en este momento                     │\n"
                f"└─────────────────────────────────────┘\n\n"
                f"{StatusEmojis.INFO} **El sistema está monitoreando...**\n"
                f"{UIEmojis.TREE_BRANCH} {ArbitrageEmojis.DETECTION} Detectando diferencias de precios\n"
                f"{UIEmojis.TREE_BRANCH} {ArbitrageEmojis.CONFIDENCE} Validando confiabilidad\n"  
                f"{UIEmojis.TREE_END} {StatusEmojis.LOADING} Actualizando cada minuto\n\n"
                f"{StatusEmojis.INFO} *Vuelve a intentar en unos minutos*"
            )
            await update.message.reply_markdown(no_opp_msg)
            return
        
        # Header mejorado
        lines = [
            f"{ArbitrageEmojis.OPPORTUNITY} **TOP OPORTUNIDADES DE ARBITRAJE**",
            f"┌─────────────────────────────────────┐",
            f"│ {len(opportunities)} oportunidades detectadas        │",
            f"│ {DecoEmojis.FIRE} Máximo potencial de ganancia      │",
            f"└─────────────────────────────────────┘\n"
        ]
        
        total_potential = 0
        
        for i, opp in enumerate(opportunities, 1):
            total_potential += opp['margen_bruto']
            confidence_emoji = DecoEmojis.TARGET if opp['confidence_score'] > 0.8 else ArbitrageEmojis.CONFIDENCE
            
            lines.append(
                f"**{i}. {RetailerEmojis.BRAND} {opp['marca_producto']}**\n"
                f"   {RetailerEmojis.CATEGORY} {opp['categoria_producto']}\n"
                f"   {ArbitrageEmojis.BUY} **Comprar:** {opp['retailer_compra']} → {format_price_with_emoji(opp['precio_compra'], False)}\n"
                f"   {ArbitrageEmojis.SELL} **Vender:** {opp['retailer_venta']} → {format_price_with_emoji(opp['precio_venta'], False)}\n"
                f"   {ArbitrageEmojis.PROFIT} **Ganancia:** *{format_price_with_emoji(opp['margen_bruto'], False)}* ({opp['roi']:.1f}% ROI)\n"
                f"   {confidence_emoji} Confianza: {opp['confidence_score']:.0%} • Detectada: {opp['times_detected']}x\n"
            )
        
        lines.extend([
            f"\n{ArbitrageEmojis.POTENTIAL} **Potencial total: {format_price_with_emoji(total_potential)} CLP**",
            f"\n{StatusEmojis.LOADING} Actualizado: {str(opportunities[0]['fecha_deteccion'])}",
            f"\n{StatusEmojis.INFO} *Usa* `/arbitrage_stats` *para más análisis*"
        ])
        
        await update.message.reply_markdown("\n".join(lines))
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error consultando arbitraje: {e}")

async def cmd_arbitrage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Estadísticas del sistema de arbitraje"""
    try:
        conn = _get_arbitrage_connection()
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as oportunidades_activas,
                SUM(margen_bruto) as potencial_total,
                AVG(margen_bruto) as margen_promedio,
                AVG(diferencia_porcentaje) as roi_promedio,
                MAX(margen_bruto) as mejor_margen,
                COUNT(DISTINCT marca_producto) as marcas_detectadas,
                COUNT(DISTINCT categoria_producto) as categorias_detectadas,
                COUNT(DISTINCT retailer_compra) as retailers_compra,
                COUNT(DISTINCT retailer_venta) as retailers_venta
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
        """)
        
        stats = cursor.fetchone()
        
        # Top retailers
        cursor.execute("""
            SELECT 
                retailer_compra || ' → ' || retailer_venta as flujo,
                COUNT(*) as oportunidades,
                SUM(margen_bruto) as potencial_total
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
            GROUP BY retailer_compra, retailer_venta
            ORDER BY potencial_total DESC
            LIMIT 5
        """)
        
        top_flows = cursor.fetchall()
        conn.close()
        
        if not stats or stats['oportunidades_activas'] == 0:
            await update.message.reply_text("📊 No hay estadísticas de arbitraje disponibles.")
            return
        
        lines = [
            "📊 *ESTADÍSTICAS DE ARBITRAJE*",
            "",
            f"🎯 Oportunidades activas: *{stats['oportunidades_activas']}*",
            f"💰 Potencial total: *${stats['potencial_total']:,} CLP*",
            f"💵 Margen promedio: *${stats['margen_promedio']:,.0f}*",
            f"📈 ROI promedio: *{stats['roi_promedio']:.1f}%*",
            f"🏆 Mejor margen: *${stats['mejor_margen']:,}*",
            "",
            f"🏪 Marcas detectadas: {stats['marcas_detectadas']}",
            f"📂 Categorías: {stats['categorias_detectadas']}",
            f"🛒 Retailers (compra): {stats['retailers_compra']}",
            f"💸 Retailers (venta): {stats['retailers_venta']}",
        ]
        
        if top_flows:
            lines.extend(["", "🔥 *TOP FLUJOS DE ARBITRAJE:*"])
            for flow in top_flows:
                lines.append(f"   {flow['flujo']}: {flow['oportunidades']} opp (${flow['potencial_total']:,})")
        
        await update.message.reply_markdown("\n".join(lines))
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error consultando estadísticas: {e}")

async def cmd_arbitrage_by_retailer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oportunidades por retailer específico"""
    if not context.args:
        await update.message.reply_text("💡 Uso: /arbitrage_retailer <retailer>\nEjemplo: /arbitrage_retailer ripley")
        return
    
    retailer = context.args[0].lower()
    
    try:
        conn = _get_arbitrage_connection()
        cursor = conn.cursor()
        
        # Buscar oportunidades donde aparezca este retailer
        cursor.execute("""
            SELECT 
                marca_producto,
                categoria_producto,
                retailer_compra,
                retailer_venta,
                precio_compra,
                precio_venta,
                margen_bruto,
                diferencia_porcentaje as roi,
                confidence_score
            FROM arbitrage_opportunities 
            WHERE validez_oportunidad = 'active'
            AND (LOWER(retailer_compra) = %s OR LOWER(retailer_venta) = %s)
            ORDER BY margen_bruto DESC 
            LIMIT 15
        """, (retailer, retailer))
        
        opportunities = cursor.fetchall()
        conn.close()
        
        if not opportunities:
            await update.message.reply_text(f"🤷‍♂️ No hay oportunidades de arbitraje para *{retailer.title()}*")
            return
        
        lines = [f"🏪 *OPORTUNIDADES EN {retailer.upper()}*", ""]
        
        buy_opportunities = [opp for opp in opportunities if opp['retailer_compra'].lower() == retailer]
        sell_opportunities = [opp for opp in opportunities if opp['retailer_venta'].lower() == retailer]
        
        if buy_opportunities:
            lines.extend(["🛒 *COMPRAR EN " + retailer.upper() + ":*"])
            for opp in buy_opportunities[:5]:
                lines.append(
                    f"• {opp['marca_producto']}: ${opp['precio_compra']:,} → "
                    f"vender en {opp['retailer_venta'].title()} (${opp['margen_bruto']:,})"
                )
            lines.append("")
        
        if sell_opportunities:
            lines.extend(["💸 *VENDER EN " + retailer.upper() + ":*"])
            for opp in sell_opportunities[:5]:
                lines.append(
                    f"• {opp['marca_producto']}: comprar en {opp['retailer_compra'].title()} → "
                    f"${opp['precio_venta']:,} (${opp['margen_bruto']:,})"
                )
        
        total_margin = sum(opp['margen_bruto'] for opp in opportunities)
        lines.append(f"\n💰 Potencial total en {retailer.title()}: *${total_margin:,} CLP*")
        
        await update.message.reply_markdown("\n".join(lines))
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error consultando {retailer}: {e}")

async def cmd_arbitrage_detect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecutar detección de arbitraje manualmente (solo admins)"""
    uid = update.effective_user.id
    storage = context.bot_data["storage"]
    
    if not is_admin(storage, uid):
        await update.message.reply_text("🔒 Comando solo disponible para administradores.")
        return
    
    await update.message.reply_text("🔍 Iniciando detección de arbitraje...")
    
    try:
        import subprocess
        import sys
        from pathlib import Path
        
        # Ejecutar script de detección
        result = subprocess.run([
            sys.executable, 
            "arbitrage/test_optimized_simple.py"
        ], cwd=Path(__file__).parent.parent.parent, 
           capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Ejecutar guardado
            save_result = subprocess.run([
                sys.executable,
                "arbitrage/save_opportunities_simple.py"
            ], cwd=Path(__file__).parent.parent.parent,
               capture_output=True, text=True, timeout=60)
            
            if save_result.returncode == 0:
                output = save_result.stdout.strip()
                await update.message.reply_text(f"✅ Detección completada:\n{output}")
                
                # Mostrar nuevas oportunidades
                await cmd_arbitrage(update, context)
            else:
                await update.message.reply_text(f"⚠️ Error al guardar: {save_result.stderr}")
        else:
            await update.message.reply_text(f"❌ Error en detección: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ Timeout: La detección está tomando más tiempo del esperado.")
    except Exception as e:
        await update.message.reply_text(f"💥 Error ejecutando detección: {e}")

