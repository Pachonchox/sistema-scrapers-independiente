from __future__ import annotations
"""
Mantenimiento del Bot: refrescar tablas materializadas en PostgreSQL
sin tocar tablas principales de scraping.
"""

import os
import psycopg2


def _dsn_from_env() -> str:
    dsn = os.getenv('DATABASE_URL') or os.getenv('PG_DSN')
    if dsn:
        return dsn
    host = os.getenv('PGHOST', 'localhost')
    port = os.getenv('PGPORT', '5432')
    user = os.getenv('PGUSER', 'postgres')
    password = os.getenv('PGPASSWORD', '')
    db = os.getenv('PGDATABASE', 'postgres')
    auth = f":{password}@" if password else '@'
    return f"postgresql://{user}{auth}{host}:{port}/{db}"


def _available_columns(cur, table: str) -> set:
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        """,
        (table,),
    )
    return {r[0] for r in cur.fetchall()}


def _price_expr(cols: set) -> str:
    order = ['precio_min', 'precio_min_dia', 'precio_oferta', 'precio_tarjeta', 'precio_normal']
    chosen = [c for c in order if c in cols]
    return 'COALESCE(' + ','.join(chosen) + ')' if chosen else '0'


def refresh_bot_tables(database_url: str | None = None) -> dict:
    """Refresca bot.current_spread y bot.intraday_delta.

    Crea schema y tablas si no existen. No modifica tablas principales.
    """
    dsn = database_url or _dsn_from_env()
    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()
        cols = _available_columns(cur, 'master_precios')
        price = _price_expr(cols)

        cur.execute("CREATE SCHEMA IF NOT EXISTS bot")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS bot.current_spread (
              internal_sku TEXT PRIMARY KEY,
              min_price NUMERIC,
              max_price NUMERIC,
              spread_pct DOUBLE PRECISION,
              retailer_count INTEGER,
              refreshed_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS bot.intraday_delta (
              internal_sku TEXT,
              retailer TEXT,
              min_24h NUMERIC,
              max_24h NUMERIC,
              delta_abs NUMERIC,
              delta_pct DOUBLE PRECISION,
              refreshed_at TIMESTAMP DEFAULT NOW(),
              PRIMARY KEY (internal_sku, retailer)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bot_current_spread_pct ON bot.current_spread(spread_pct DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bot_intraday_delta_pct ON bot.intraday_delta(delta_pct DESC)")

        # Refresh
        cur.execute("TRUNCATE bot.current_spread")
        cur.execute(
            f"""
            INSERT INTO bot.current_spread(internal_sku, min_price, max_price, spread_pct, retailer_count, refreshed_at)
            SELECT codigo_interno AS internal_sku,
                   MIN({price}) AS min_price,
                   MAX({price}) AS max_price,
                   CASE WHEN MIN({price})>0 THEN (MAX({price})-MIN({price}))::float/NULLIF(MIN({price}),0) ELSE 0 END AS spread_pct,
                   COUNT(DISTINCT retailer) AS retailer_count,
                   NOW()
            FROM master_precios
            WHERE fecha = CURRENT_DATE
            GROUP BY codigo_interno
            HAVING COUNT(DISTINCT retailer) >= 2
            """
        )

        cur.execute("TRUNCATE bot.intraday_delta")
        cur.execute(
            f"""
            WITH today AS (
              SELECT codigo_interno AS internal_sku, retailer, {price} AS price
              FROM master_precios
              WHERE fecha = CURRENT_DATE
            )
            INSERT INTO bot.intraday_delta(internal_sku, retailer, min_24h, max_24h, delta_abs, delta_pct, refreshed_at)
            SELECT internal_sku,
                   retailer,
                   MIN(price) AS min_24h,
                   MAX(price) AS max_24h,
                   (MAX(price)-MIN(price)) AS delta_abs,
                   CASE WHEN MIN(price)>0 THEN (MAX(price)-MIN(price))::float/NULLIF(MIN(price),0) ELSE 0 END AS delta_pct,
                   NOW()
            FROM today
            GROUP BY internal_sku, retailer
            """
        )

        conn.commit()
        return {"success": True}
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

