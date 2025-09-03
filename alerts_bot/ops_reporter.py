from __future__ import annotations
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from pathlib import Path

from .config import BotConfig
from core.url_failure_monitor import get_url_monitor


def _bool_env(name: str, default: str = "false") -> bool:
    return str(os.getenv(name, default)).strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def within_active_window(now: datetime, start_hour: int, end_hour: int) -> bool:
    # [start, end) en hora local
    return start_hour <= now.hour < end_hour


def human_pct(x: float) -> str:
    try:
        return f"{x*100:.1f}%"
    except Exception:
        return "N/A"


def human_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def collect_status(storage, repo, window: str = "1h") -> Dict[str, Any]:
    """Recolecta métricas operacionales. Tolerante a fallos parcial.
    window: '1h' | '24h' | 'overnight'
    """
    snap: Dict[str, Any] = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window": window,
    }

    # Redis
    try:
        t0 = time.perf_counter()
        ok = storage.r.ping()
        snap["redis_ok"] = bool(ok)
        snap["redis_ms"] = int((time.perf_counter() - t0) * 1000)
    except Exception:
        snap["redis_ok"] = False
        snap["redis_ms"] = None

    # DuckDB & datos
    try:
        # Verificación rápida
        repo.con.execute("SELECT 1")
        snap["duckdb_ok"] = True

        # Frescura
        max_ts = None
        try:
            row = repo.con.execute("SELECT MAX(ts) FROM v_price_ticks").fetchone()
            if row:
                max_ts = row[0]
        except Exception:
            max_ts = None
        if max_ts:
            # DuckDB devuelve str o datetime; intentar parsear
            try:
                if isinstance(max_ts, str):
                    max_dt = datetime.fromisoformat(max_ts.replace("Z", ""))
                else:
                    max_dt = max_ts
                snap["freshness_minutes"] = max(0, int((datetime.now() - max_dt).total_seconds() // 60))
            except Exception:
                snap["freshness_minutes"] = None
        else:
            snap["freshness_minutes"] = None

        # Precios vigentes
        try:
            row = repo.con.execute("SELECT COUNT(*) FROM v_current_prices").fetchone()
            snap["current_prices_count"] = int(row[0]) if row else 0
        except Exception:
            snap["current_prices_count"] = None

        # Volúmenes por ventana
        def counts_since(delta_hours: int) -> Tuple[int, int]:
            try:
                q = (
                    "SELECT COUNT(*) AS ticks, COUNT(DISTINCT internal_sku) AS skus "
                    "FROM v_price_ticks WHERE ts >= NOW() - INTERVAL ? HOUR"
                )
                row = repo.con.execute(q, [delta_hours]).fetchone()
                return int(row[0]), int(row[1])
            except Exception:
                return -1, -1

        ticks_1h, skus_1h = counts_since(1)
        ticks_24h, skus_24h = counts_since(24)
        snap.update({
            "ticks_1h": ticks_1h,
            "skus_1h": skus_1h,
            "ticks_24h": ticks_24h,
            "skus_24h": skus_24h,
        })

        # Por retailer (top 5 últimos 60 minutos)
        try:
            q = (
                "SELECT retailer, COUNT(*) AS ticks, COUNT(DISTINCT internal_sku) AS skus "
                "FROM v_price_ticks WHERE ts >= NOW() - INTERVAL 1 HOUR "
                "GROUP BY retailer ORDER BY ticks DESC LIMIT 5"
            )
            rows = repo.con.execute(q).fetchall()
            cols = [d[0] for d in repo.con.description]
            snap["top_retailers_1h"] = [dict(zip(cols, r)) for r in rows]
        except Exception:
            snap["top_retailers_1h"] = []

        # Oportunidades por spread (umbral configurable)
        try:
            spread_th = float(os.getenv("ALERT_SPREAD_THRESHOLD_DEFAULT", "0.05"))
        except Exception:
            spread_th = 0.05
        try:
            q = (
                "SELECT COUNT(*) FROM v_current_spread WHERE spread_pct >= ?"
            )
            row = repo.con.execute(q, [spread_th]).fetchone()
            snap["spread_opps_count"] = int(row[0]) if row else 0
            q2 = (
                "SELECT internal_sku, min_price, max_price, spread_pct, retailer_count "
                "FROM v_current_spread ORDER BY spread_pct DESC LIMIT 5"
            )
            rows = repo.con.execute(q2).fetchall()
            cols = [d[0] for d in repo.con.description]
            snap["top_spreads"] = [dict(zip(cols, r)) for r in rows]
        except Exception:
            snap["spread_opps_count"] = None
            snap["top_spreads"] = []

        # Volatilidad intradía
        try:
            delta_th = float(os.getenv("ALERT_DELTA_THRESHOLD_DEFAULT", "0.10"))
        except Exception:
            delta_th = 0.10
        try:
            q = (
                "SELECT COUNT(*) FROM v_intraday_delta WHERE delta_pct >= ?"
            )
            row = repo.con.execute(q, [delta_th]).fetchone()
            snap["intraday_high_moves"] = int(row[0]) if row else 0
            q2 = (
                "SELECT internal_sku, retailer, delta_pct, min_24h, max_24h "
                "FROM v_intraday_delta ORDER BY delta_pct DESC LIMIT 5"
            )
            rows = repo.con.execute(q2).fetchall()
            cols = [d[0] for d in repo.con.description]
            snap["top_intraday"] = [dict(zip(cols, r)) for r in rows]
        except Exception:
            snap["intraday_high_moves"] = None
            snap["top_intraday"] = []
    except Exception:
        snap["duckdb_ok"] = False

    # Parquet files
    try:
        root = Path(repo.parquet_root)
        cnt = 0
        for p in root.rglob("*.parquet"):
            cnt += 1
            if cnt > 10_000:
                break
        snap["parquet_files_count"] = cnt
    except Exception:
        snap["parquet_files_count"] = None

    # Usuarios y suscripciones
    try:
        users = storage.all_users()
        snap["users_count"] = len(users)
        snap["subscribed_skus_count"] = len(storage.all_subscribed_skus())
        # costo O(U); aceptable 1 vez/hora
        total_subs = 0
        for u in users[:5000]:  # safety cap
            try:
                total_subs += len(storage.list_subscriptions(u))
            except Exception:
                pass
        snap["subs_per_user_avg"] = round(total_subs / max(1, len(users)), 2)
    except Exception:
        snap["users_count"] = None
        snap["subscribed_skus_count"] = None
        snap["subs_per_user_avg"] = None

    # Alertas enviadas (requiere engine incrementando counters)
    try:
        snap["alerts_sent_1h"] = storage.hourly_counter_sum("alerts_sent", last_n=1)
        snap["alerts_sent_24h"] = storage.hourly_counter_sum("alerts_sent", last_n=24)
        snap["alerts_spread_1h"] = storage.hourly_counter_sum("alerts_sent_spread", last_n=1)
        snap["alerts_intraday_1h"] = storage.hourly_counter_sum("alerts_sent_intraday", last_n=1)
    except Exception:
        snap["alerts_sent_1h"] = None
        snap["alerts_sent_24h"] = None

    # Duración último job de alertas
    try:
        v = storage.get_metric_value("last_alert_job_ms")
        snap["last_alert_job_ms"] = int(v) if v else None
    except Exception:
        snap["last_alert_job_ms"] = None

    # URL failures / proxies (si está disponible)
    try:
        monitor = get_url_monitor()
        dash = monitor.get_dashboard_metrics()
        snap["url_fail_total"] = int(dash.get("total_problematic_urls", 0))
        snap["url_fail_1h"] = int(dash.get("failures_last_hour", 0))
        snap["url_fail_top5"] = dash.get("top_5_failures", [])
        # Extra proxy efectiveness from executive summary if needed
        try:
            exec_summary = monitor.get_executive_summary()
            pva = exec_summary.get("proxy_vs_direct_analysis", {})
            snap["proxy_failure_proxy"] = int(pva.get("proxy_failure_rate", 0))
            snap["proxy_failure_direct"] = int(pva.get("direct_failure_rate", 0))
            snap["proxy_recommendation"] = pva.get("recommendation", "")
            # Top retailers con fallos (24h)
            ra = exec_summary.get("retailer_analysis", {})
            ranked = []
            for rname, info in ra.items():
                ranked.append({
                    "retailer": rname,
                    "total_failures": int(info.get("total_failures", 0)),
                    "proxy_failures": int(info.get("proxy_failures", 0)),
                    "direct_failures": int(info.get("direct_failures", 0)),
                    "proxy_effectiveness": float(info.get("proxy_effectiveness", 0.0)),
                })
            ranked.sort(key=lambda x: x.get("total_failures", 0), reverse=True)
            snap["retailer_fail_top5"] = ranked[:5]
            snap["priority_retailers"] = [x["retailer"] for x in ranked[:3]]
        except Exception:
            snap["retailer_fail_top5"] = []
            snap["priority_retailers"] = []
    except Exception:
        snap["url_fail_total"] = None
        snap["url_fail_1h"] = None

    return snap


def score_health(s: Dict[str, Any]) -> Tuple[str, str]:
    """Devuelve (emoji, estado textual)."""
    critical = []
    warn = []

    if not s.get("redis_ok"):
        critical.append("Redis")
    if not s.get("duckdb_ok"):
        critical.append("DuckDB")
    fm = s.get("freshness_minutes")
    if isinstance(fm, int):
        if fm >= 60:
            critical.append("Frescura≥60m")
        elif fm >= 30:
            warn.append("Frescura≥30m")

    if critical:
        return "❌", "Incidente: " + ", ".join(critical)
    if warn:
        return "⚠️", "Degradado: " + ", ".join(warn)
    return "✅", "OK"


def format_hourly_markdown(s: Dict[str, Any], shard_text: str) -> List[str]:
    icon, status = score_health(s)
    lines1 = [
        f"{icon} *Estado Operacional* — {status}",
        f"🕒 {s['ts']} | {shard_text}",
        "",
        "• Datos: "
        f"Freshness: {s.get('freshness_minutes','N/A')}m | "
        f"Vigentes: {human_int(s.get('current_prices_count') or 0)} | "
        f"Ticks 1h: {human_int(s.get('ticks_1h') or 0)} ({human_int(s.get('skus_1h') or 0)} SKUs)",
        "• Alertas: "
        f"1h: {human_int(s.get('alerts_sent_1h') or 0)} (📈 {human_int(s.get('alerts_spread_1h') or 0)} | ⚡ {human_int(s.get('alerts_intraday_1h') or 0)}) | "
        f"24h: {human_int(s.get('alerts_sent_24h') or 0)}",
        "• Usuarios: "
        f"Activos: {human_int(s.get('users_count') or 0)} | SKUs suscritos: {human_int(s.get('subscribed_skus_count') or 0)} | "
        f"Subs/usuario: {s.get('subs_per_user_avg','N/A')}",
        "• Infra: "
        f"Redis: {'OK' if s.get('redis_ok') else 'FAIL'} {s.get('redis_ms') or '—'}ms | DuckDB: {'OK' if s.get('duckdb_ok') else 'FAIL'} | Parquet: {human_int(s.get('parquet_files_count') or 0)}",
    ]

    # Recomendación breve
    rec = ""
    fm = s.get("freshness_minutes")
    if isinstance(fm, int) and fm >= 30:
        rec = "Revisar schedulers/scrapers; evaluar backfill/rate-limit."
    elif s.get("redis_ok") is False:
        rec = "Verificar Redis (servicio/credenciales/red)."
    elif s.get("duckdb_ok") is False:
        rec = "Verificar DuckDB/parquet y vistas SQL."
    else:
        rec = "Sin acciones urgentes. Monitoreo continuo."

    lines1 += ["", f"🧭 {rec}"]

    # Retailers top línea
    tr = s.get("top_retailers_1h") or []
    if tr:
        top_line = ", ".join(
            f"{t['retailer']}: {human_int(t['ticks'])}/{human_int(t['skus'])}" for t in tr
        )
        lines1 += [f"• Retailers (1h): {top_line}"]

    text1 = "\n".join(lines1)

    # Mensaje 2: Top spreads e intradía si existen
    msgs: List[str] = [text1]
    tops = []
    ts = s.get("top_spreads") or []
    if ts:
        tops.append("📈 Top spreads: " + "; ".join(
            f"`{x['internal_sku']}` {x['spread_pct']*100:.1f}%" for x in ts
        ))
    ti = s.get("top_intraday") or []
    if ti:
        tops.append("⚡ Intradía: " + "; ".join(
            f"`{x['internal_sku']}` {x['retailer']}: {x['delta_pct']*100:.1f}%" for x in ti
        ))
    if tops:
        msgs.append("\n".join(["🗂️ *Movimientos Destacados*", *tops]))

    # Mensaje 3: URL failures/proxies si hay
    uf = s.get("url_fail_1h")
    if uf is not None:
        proxy_line = ""
        if s.get("proxy_recommendation"):
            proxy_line = f" | Recomendación proxy: {s.get('proxy_recommendation')}"
        msg3 = (
            f"🧪 *Calidad Scrap*") + "\n" + \
            (f"Fallos URL 1h: {human_int(uf)} (total: {human_int(s.get('url_fail_total') or 0)})" + proxy_line)
        msgs.append(msg3)

    return msgs


def format_overnight_markdown(s: Dict[str, Any], shard_text: str) -> List[str]:
    icon, status = score_health(s)
    lines = [
        f"🌙 *Resumen Nocturno* — {status}",
        f"🕘 Ventana: 22:00 → 09:00 | {shard_text}",
        "",
        f"• Ticks Noche: {human_int(s.get('ticks_24h') or 0)} | SKUs: {human_int(s.get('skus_24h') or 0)}",
        f"• Alertas 24h: {human_int(s.get('alerts_sent_24h') or 0)}",
        f"• Frescura: {s.get('freshness_minutes','N/A')}m | Vigentes: {human_int(s.get('current_prices_count') or 0)}",
        f"• Usuarios: {human_int(s.get('users_count') or 0)} | SKUs suscritos: {human_int(s.get('subscribed_skus_count') or 0)}",
        f"• Infra: Redis {'OK' if s.get('redis_ok') else 'FAIL'} | DuckDB {'OK' if s.get('duckdb_ok') else 'FAIL'}",
        "",
        "🧭 Sugerencias: revisar retailers con baja actividad; validar proxys y calidad de fuentes.",
    ]
    msgs = ["\n".join(lines)]
    # Agregar tops si existen
    ts = s.get("top_spreads") or []
    ti = s.get("top_intraday") or []
    blocks = []
    if ts:
        blocks.append("📈 Top spreads noche:\n" + "\n".join(
            f"- `{x['internal_sku']}` {x['spread_pct']*100:.1f}% (min {int(x['min_price']):,} / max {int(x['max_price']):,})".replace(",",".") for x in ts
        ))
    if ti:
        blocks.append("⚡ Cambios intradía:\n" + "\n".join(
            f"- `{x['internal_sku']}` {x['retailer']}: {x['delta_pct']*100:.1f}%" for x in ti
        ))
    # Retailers con fallos y prioridades
    rf = s.get("retailer_fail_top5") or []
    if rf:
        blocks.append("🚩 Retailers con fallos (24h):\n" + "\n".join(
            f"- {x['retailer']}: {x['total_failures']} fallos (proxy {x['proxy_failures']}/direct {x['direct_failures']})" for x in rf
        ))
    pr = s.get("priority_retailers") or []
    if pr:
        blocks.append("🎯 Prioridades del día:\n" + "\n".join(
            f"- {r}: revisar parsers, política de proxy y bloqueos" for r in pr
        ))
    if blocks:
        msgs.append("\n\n".join(blocks))
    return msgs


async def send_report(application, storage, repo, kind: str, start_hour: int, end_hour: int) -> None:
    config = application.bot_data.get("config") or BotConfig()

    # Destinatarios
    chat_id = os.getenv("OPS_REPORT_CHAT_ID", "").strip()
    if chat_id.isdigit():
        recipients = [int(chat_id)]
    else:
        # enviar a superusuarios si no hay chat específico
        try:
            recipients = storage.superusers_list()
        except Exception:
            recipients = []

    if not recipients:
        return

    # Recolectar y formatear
    snap = collect_status(storage, repo, window=("overnight" if kind == "overnight" else "1h"))
    shard_text = f"Shard {config.shard_index}/{config.shard_total}"
    messages = format_overnight_markdown(snap, shard_text) if kind == "overnight" else format_hourly_markdown(snap, shard_text)

    # Enviar
    notifier = application.bot_data["engine"].notifier
    for uid in recipients:
        for msg in messages:
            try:
                await notifier.send_markdown(uid, msg)
            except Exception:
                # best effort
                pass


async def ops_report_job(context):
    application = context.application
    config = application.bot_data.get("config") or BotConfig()
    storage = application.bot_data["storage"]
    repo = application.bot_data["repo"]

    enabled = _bool_env("OPS_REPORT_ENABLED", "true")
    if not enabled:
        return

    start_h = _int_env("OPS_REPORT_START_HOUR", 9)
    end_h = _int_env("OPS_REPORT_END_HOUR", 22)
    now = datetime.now()
    if within_active_window(now, start_h, end_h):
        await send_report(application, storage, repo, kind="hourly", start_hour=start_h, end_hour=end_h)


async def overnight_report_job(context):
    application = context.application
    storage = application.bot_data["storage"]
    repo = application.bot_data["repo"]
    await send_report(application, storage, repo, kind="overnight", start_hour=9, end_hour=22)
