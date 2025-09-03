from __future__ import annotations
from typing import List, Dict, Any, Optional
try:
    import psycopg
    from psycopg.rows import dict_row as _psycopg_dict_row
    _PSYCOPG_V3 = True
except Exception:
    _PSYCOPG_V3 = False
try:
    import psycopg2  # type: ignore
    import psycopg2.extras  # type: ignore
    _PSYCOPG2 = True
except Exception:
    _PSYCOPG2 = False


class PostgresRepo:
    """Repositorio de lectura para PostgreSQL.

    Provee las mismas operaciones clave que `ProductsRepo` (DuckDB):
    - search_products_enriched(query, limit)
    - current_spread(internal_sku)
    - intraday_delta(internal_sku)
    - price_history_daily(internal_sku, days)

    Asume que existen al menos tablas maestras:
      - master_productos(codigo_interno, nombre, marca, ...)
      - master_precios(codigo_interno, retailer, fecha, ... precios ...)

    Si existen vistas de compatibilidad:
      - v_current_spread(internal_sku, min_price, max_price, spread_pct, retailer_count)
      - v_intraday_delta(internal_sku, retailer, min_24h, max_24h, delta_abs, delta_pct)
    se usan preferentemente. Caso contrario, se calculan sobre master_precios.
    """

    def __init__(self, dsn: str):
        if not dsn:
            raise RuntimeError("DATABASE_URL/PG_DSN no configurado para PostgresRepo")
        self.dsn = dsn

        if _PSYCOPG_V3:
            self.con = psycopg.connect(dsn)
            self.cur = self.con.cursor(row_factory=_psycopg_dict_row)
        elif _PSYCOPG2:
            self.con = psycopg2.connect(dsn)
            self.con.autocommit = True
            self.cur = self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            # Fallback a pg8000 si no hay psycopg
            import re
            from urllib.parse import urlparse
            import pg8000.dbapi as pg
            u = urlparse(dsn)
            user = u.username or 'postgres'
            password = u.password or ''
            host = u.hostname or 'localhost'
            port = int(u.port or 5432)
            db = (u.path or '/postgres').lstrip('/')
            self.con = pg.connect(user=user, password=password, host=host, port=port, database=db)
            self.cur = self.con.cursor()

        # detectar disponibilidad de objetos
        # Forzar uso de master_productos (tiene los datos reales)
        self.has_np = False  # self._has_table('normalized_products')
        # Tablas materializadas del bot (preferidas si existen)
        self.has_bot_current = self._has_table('bot.current_spread') or self._has_table('bot_current_spread')
        self.has_bot_intraday = self._has_table('bot.intraday_delta') or self._has_table('bot_intraday_delta')
        # Vistas (fallback)
        self.has_view_current_spread = self._has_table('v_current_spread')
        self.has_view_intraday = self._has_table('v_intraday_delta')
        # columnas de precio disponibles en master_precios
        self.price_cols = self._detect_price_columns()

    def _has_table(self, name: str) -> bool:
        self.cur.execute("SELECT to_regclass(%s) IS NOT NULL AS exists", (name,))
        row = self.cur.fetchone()
        return bool(row and row.get('exists'))

    def _detect_price_columns(self) -> List[str]:
        cols = []
        self.cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'master_precios'
            """
        )
        available = {r['column_name'] for r in self.cur.fetchall()}
        # orden de preferencia
        for c in ['precio_min', 'precio_min_dia', 'precio_oferta', 'precio_tarjeta', 'precio_normal']:
            if c in available:
                cols.append(c)
        return cols or ['precio_min']

    def _price_expr(self) -> str:
        # COALESCE en el orden detectado
        coalesce = ','.join(self.price_cols)
        return f"COALESCE({coalesce})"

    # ---------- búsquedas ----------
    def search_products_enriched(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        q = (query or '').strip()
        if not q:
            return []

        tokens = [t for t in q.lower().split() if t]
        params: List[Any] = []

        # seleccionar fuente de productos
        if self.has_np:
            table = 'normalized_products'
            # columnas estándar
            cols = {
                'sku': 'internal_sku',
                'brand': 'brand',
                'model': 'model',
                'name': 'normalized_name'
            }
        else:
            table = 'master_productos'
            cols = {
                'sku': 'codigo_interno',
                'brand': 'marca',
                'model': "split_part(nombre,' ',2)",  # mejor esfuerzo
                'name': 'nombre'
            }

        # score simple por tokens en brand/model/name
        score_parts = []
        for t in tokens:
            like = f"%{t}%"
            score_parts.append(f"CASE WHEN lower({cols['brand']}) LIKE lower(%s) THEN 3 ELSE 0 END")
            params.append(like)
            score_parts.append(f"CASE WHEN lower({cols['model']}) LIKE lower(%s) THEN 2 ELSE 0 END")
            params.append(like)
            score_parts.append(f"CASE WHEN lower({cols['name']}) LIKE lower(%s) THEN 1 ELSE 0 END")
            params.append(like)
        score_sql = ' + '.join(score_parts) or '0'

        # preferir vista v_current_spread para enriquecer
        if self.has_bot_current:
            # Preferir tabla materializada
            table_name = 'bot.current_spread' if self._has_table('bot.current_spread') else 'bot_current_spread'
            enrich_join = (
                f"LEFT JOIN {table_name} s ON s.internal_sku = p.%s" % cols['sku']
            )
            enrich_cols = (
                "s.min_price, s.max_price, s.spread_pct, s.retailer_count"
            )
        elif self.has_view_current_spread:
            enrich_join = (
                "LEFT JOIN v_current_spread s ON s.internal_sku = p.%s" % cols['sku']
            )
            enrich_cols = (
                "s.min_price, s.max_price, s.spread_pct, s.retailer_count"
            )
        else:
            # calcular spread on-the-fly para hoy
            price_expr = self._price_expr()
            enrich_join = (
                "LEFT JOIN (" +
                f" SELECT codigo_interno AS internal_sku, MIN({price_expr}) AS min_price, " +
                f"MAX({price_expr}) AS max_price, " +
                f"CASE WHEN MIN({price_expr})>0 THEN (MAX({price_expr})-MIN({price_expr}))::float/NULLIF(MIN({price_expr}),0) ELSE 0 END AS spread_pct, " +
                f"COUNT(DISTINCT retailer) AS retailer_count " +
                f"FROM master_precios WHERE fecha = CURRENT_DATE GROUP BY codigo_interno" +
                ") s ON s.internal_sku = p.%s" % cols['sku']
            )
            enrich_cols = "s.min_price, s.max_price, s.spread_pct, s.retailer_count"

        sql = (
            f"WITH cand AS (\n"
            f"  SELECT p.{cols['sku']} AS internal_sku, p.{cols['brand']} AS brand, "
            f"         {cols['model']} AS model, p.{cols['name']} AS normalized_name, ({score_sql}) AS score\n"
            f"  FROM {table} p\n"
            f"), ranked AS (\n"
            f"  SELECT * FROM cand WHERE score > 0\n"
            f")\n"
            f"SELECT r.internal_sku, r.brand, r.model, r.normalized_name, r.score, {enrich_cols}\n"
            f"FROM ranked r\n"
            f"JOIN {table} p ON p.{cols['sku']} = r.internal_sku\n"
            f"{enrich_join}\n"
            f"ORDER BY r.score DESC, COALESCE(s.retailer_count,0) DESC\n"
            f"LIMIT {int(limit)}"
        )
        self.cur.execute(sql, params)
        rows = self.cur.fetchall() or []
        return [dict(r) for r in rows]

    # ---------- métricas por SKU ----------
    def current_spread(self, internal_sku: str) -> Optional[Dict[str, Any]]:
        if self.has_bot_current:
            table_name = 'bot.current_spread' if self._has_table('bot.current_spread') else 'bot_current_spread'
            self.cur.execute(
                f"""
                SELECT internal_sku, min_price, max_price, spread_pct, retailer_count
                FROM {table_name} WHERE internal_sku = %s LIMIT 1
                """,
                (internal_sku,)
            )
            row = self.cur.fetchone()
            return dict(row) if row else None
        elif self.has_view_current_spread:
            self.cur.execute(
                """
                SELECT internal_sku, min_price, max_price, spread_pct, retailer_count
                FROM v_current_spread WHERE internal_sku = %s LIMIT 1
                """,
                (internal_sku,)
            )
            row = self.cur.fetchone()
            return dict(row) if row else None

        price_expr = self._price_expr()
        self.cur.execute(
            f"""
            WITH p AS (
              SELECT {price_expr} AS price, retailer
              FROM master_precios
              WHERE codigo_interno = %s AND fecha = CURRENT_DATE
            )
            SELECT %s AS internal_sku,
                   MIN(price) AS min_price,
                   MAX(price) AS max_price,
                   CASE WHEN MIN(price)>0 THEN (MAX(price)-MIN(price))::float/NULLIF(MIN(price),0) ELSE 0 END AS spread_pct,
                   COUNT(DISTINCT retailer) AS retailer_count
            FROM p
            """,
            (internal_sku, internal_sku)
        )
        row = self.cur.fetchone()
        return dict(row) if row and row.get('max_price') is not None else None

    def intraday_delta(self, internal_sku: str) -> Optional[Dict[str, Any]]:
        if self.has_bot_intraday:
            table_name = 'bot.intraday_delta' if self._has_table('bot.intraday_delta') else 'bot_intraday_delta'
            self.cur.execute(
                f"""
                SELECT internal_sku, retailer, min_24h, max_24h, delta_abs, delta_pct
                FROM {table_name} WHERE internal_sku = %s ORDER BY delta_pct DESC LIMIT 1
                """,
                (internal_sku,)
            )
            row = self.cur.fetchone()
            return dict(row) if row else None
        elif self.has_view_intraday:
            self.cur.execute(
                """
                SELECT internal_sku, retailer, min_24h, max_24h, delta_abs, delta_pct
                FROM v_intraday_delta WHERE internal_sku = %s ORDER BY delta_pct DESC LIMIT 1
                """,
                (internal_sku,)
            )
            row = self.cur.fetchone()
            return dict(row) if row else None

        price_expr = self._price_expr()
        self.cur.execute(
            f"""
            WITH d AS (
              SELECT codigo_interno, retailer, fecha, {price_expr} AS price
              FROM master_precios
              WHERE codigo_interno = %s AND fecha >= CURRENT_DATE - INTERVAL '1 day'
            ), agg AS (
              SELECT codigo_interno, retailer,
                     MIN(price) AS min_24h, MAX(price) AS max_24h
              FROM d GROUP BY codigo_interno, retailer
            )
            SELECT codigo_interno AS internal_sku, retailer, min_24h, max_24h,
                   (max_24h - min_24h) AS delta_abs,
                   CASE WHEN min_24h>0 THEN (max_24h - min_24h)::float/NULLIF(min_24h,0) ELSE 0 END AS delta_pct
            FROM agg
            ORDER BY delta_pct DESC
            LIMIT 1
            """,
            (internal_sku,)
        )
        row = self.cur.fetchone()
        return dict(row) if row else None

    def price_history_daily(self, internal_sku: str, days: int = 30) -> List[Dict[str, Any]]:
        price_expr = self._price_expr()
        self.cur.execute(
            f"""
            SELECT fecha AS day,
                   MIN({price_expr}) AS min_price,
                   MAX({price_expr}) AS max_price,
                   AVG({price_expr}) AS avg_price,
                   COUNT(*) AS obs
            FROM master_precios
            WHERE codigo_interno = %s AND fecha >= CURRENT_DATE - INTERVAL %s
            GROUP BY fecha
            ORDER BY day DESC
            LIMIT 365
            """,
            (internal_sku, f"'{int(days)} days'"),
        )
        rows = self.cur.fetchall() or []
        return [dict(r) for r in rows]

    # ---------- agregados ----------
    def top_spreads(self, limit: int = 10) -> List[Dict[str, Any]]:
        if self.has_bot_current:
            table_name = 'bot.current_spread' if self._has_table('bot.current_spread') else 'bot_current_spread'
            self.cur.execute(
                f"""
                SELECT internal_sku, min_price, max_price, spread_pct, retailer_count
                FROM {table_name}
                WHERE retailer_count >= 2
                ORDER BY spread_pct DESC
                LIMIT %s
                """,
                (int(limit),)
            )
            rows = self.cur.fetchall() or []
            return [dict(r) for r in rows]
        elif self.has_view_current_spread:
            self.cur.execute(
                """
                SELECT internal_sku, min_price, max_price, spread_pct, retailer_count
                FROM v_current_spread
                WHERE retailer_count >= 2
                ORDER BY spread_pct DESC
                LIMIT %s
                """,
                (int(limit),)
            )
            rows = self.cur.fetchall() or []
            return [dict(r) for r in rows]

        price_expr = self._price_expr()
        self.cur.execute(
            f"""
            WITH today AS (
              SELECT codigo_interno AS internal_sku, retailer, {price_expr} AS price
              FROM master_precios WHERE fecha = CURRENT_DATE
            )
            SELECT internal_sku,
                   MIN(price) AS min_price,
                   MAX(price) AS max_price,
                   CASE WHEN MIN(price)>0 THEN (MAX(price)-MIN(price))::float/NULLIF(MIN(price),0) ELSE 0 END AS spread_pct,
                   COUNT(DISTINCT retailer) AS retailer_count
            FROM today
            GROUP BY internal_sku
            HAVING COUNT(DISTINCT retailer) >= 2
            ORDER BY spread_pct DESC
            LIMIT %s
            """,
            (int(limit),)
        )
        rows = self.cur.fetchall() or []
        return [dict(r) for r in rows]

    # ---------- métricas del sistema ----------
    def _table_has_cols(self, table: str, cols: List[str]) -> Dict[str, bool]:
        sql = (
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema IN ('public','bot') AND table_name = %s"
        )
        self.cur.execute(sql, (table.split('.')[-1],))
        have = {r['column_name'] for r in self.cur.fetchall()}
        return {c: (c in have) for c in cols}

    def system_metrics(self, limit_samples: int = 5) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {"stats": {}, "by_retailer": [], "scrapers_hourly": [],
                                   "top_drops": [], "top_increases": [], "link_issues": {}}
        # Totales productos
        try:
            self.cur.execute("SELECT COUNT(*) AS c FROM master_productos")
            metrics["stats"]["total_products"] = int(self.cur.fetchone()["c"])
        except Exception:
            metrics["stats"]["total_products"] = None

        # Productos activos si existe columna
        try:
            if self._table_has_cols('master_productos', ['activo']).get('activo'):
                self.cur.execute("SELECT COUNT(*) AS c FROM master_productos WHERE activo = TRUE")
                metrics["stats"]["active_products"] = int(self.cur.fetchone()["c"])
        except Exception:
            pass

        # Productos con precio hoy
        try:
            self.cur.execute(
                "SELECT COUNT(DISTINCT codigo_interno) AS c FROM master_precios WHERE fecha = CURRENT_DATE"
            )
            metrics["stats"]["products_priced_today"] = int(self.cur.fetchone()["c"])
        except Exception:
            metrics["stats"]["products_priced_today"] = None

        # Cambios de precio hoy
        try:
            if self.has_bot_intraday:
                table_name = 'bot.intraday_delta' if self._has_table('bot.intraday_delta') else 'bot_intraday_delta'
                self.cur.execute(
                    f"SELECT COUNT(*) AS c FROM {table_name} WHERE ABS(delta_pct) > 0.0001"
                )
                metrics["stats"]["price_changes_today"] = int(self.cur.fetchone()["c"])
            else:
                # Fallback por agrupación en master_precios
                price_expr = self._price_expr()
                self.cur.execute(
                    f"""
                    WITH agg AS (
                      SELECT codigo_interno, MIN({price_expr}) AS minp, MAX({price_expr}) AS maxp
                      FROM master_precios
                      WHERE fecha = CURRENT_DATE
                      GROUP BY codigo_interno
                    )
                    SELECT COUNT(*) AS c FROM agg WHERE maxp > minp AND minp > 0
                    """
                )
                metrics["stats"]["price_changes_today"] = int(self.cur.fetchone()["c"])
        except Exception:
            metrics["stats"]["price_changes_today"] = None

        # Por retailer hoy
        try:
            self.cur.execute(
                """
                SELECT retailer, COUNT(DISTINCT codigo_interno) AS products
                FROM master_precios
                WHERE fecha = CURRENT_DATE
                GROUP BY retailer
                ORDER BY products DESC
                """
            )
            metrics["by_retailer"] = [dict(r) for r in self.cur.fetchall()]
        except Exception:
            pass

        # Scrapers por hora (si existe timestamp)
        try:
            # Detectar columna de timestamp
            cols = self._table_has_cols('master_precios', ['hora_actualizacion', 'timestamp'])
            if cols.get('hora_actualizacion'):
                self.cur.execute(
                    """
                    SELECT date_trunc('hour', hora_actualizacion) AS hour,
                           COUNT(*) AS rows,
                           COUNT(DISTINCT codigo_interno) AS products
                    FROM master_precios
                    WHERE fecha = CURRENT_DATE
                    GROUP BY 1
                    ORDER BY 1 DESC
                    LIMIT 24
                    """
                )
                metrics["scrapers_hourly"] = [
                    {"hour": str(r["hour"]), "rows": int(r["rows"]), "products": int(r["products"])}
                    for r in self.cur.fetchall()
                ]
        except Exception:
            pass

        # Top drops / increases
        try:
            if self.has_bot_intraday:
                table = 'bot.intraday_delta' if self._has_table('bot.intraday_delta') else 'bot_intraday_delta'
                self.cur.execute(
                    f"SELECT internal_sku, retailer, min_24h, max_24h, delta_pct FROM {table} ORDER BY delta_pct ASC LIMIT %s",
                    (limit_samples,)
                )
                metrics["top_drops"] = [dict(r) for r in self.cur.fetchall()]
                self.cur.execute(
                    f"SELECT internal_sku, retailer, min_24h, max_24h, delta_pct FROM {table} ORDER BY delta_pct DESC LIMIT %s",
                    (limit_samples,)
                )
                metrics["top_increases"] = [dict(r) for r in self.cur.fetchall()]
        except Exception:
            pass

        # Link issues
        li = {}
        try:
            # enlaces nulos/vacíos
            self.cur.execute("SELECT COUNT(*) AS c FROM master_productos WHERE link IS NULL OR link = ''")
            li["null_or_empty"] = int(self.cur.fetchone()["c"])
        except Exception:
            pass
        try:
            # no http(s)
            self.cur.execute("SELECT COUNT(*) AS c FROM master_productos WHERE link IS NOT NULL AND link <> '' AND link !~ '^(?i)https?://'")
            li["non_http"] = int(self.cur.fetchone()["c"])
        except Exception:
            pass
        try:
            # sin precio hoy
            self.cur.execute(
                """
                SELECT COUNT(*) AS c
                FROM master_productos p
                WHERE NOT EXISTS (
                  SELECT 1 FROM master_precios pr
                  WHERE pr.codigo_interno = p.codigo_interno AND pr.fecha = CURRENT_DATE
                )
                """
            )
            li["no_price_today"] = int(self.cur.fetchone()["c"])
        except Exception:
            pass
        try:
            # stale (ultimo_visto < hoy - 3d) si columna existe
            if self._table_has_cols('master_productos', ['ultimo_visto']).get('ultimo_visto'):
                self.cur.execute(
                    "SELECT COUNT(*) AS c FROM master_productos WHERE ultimo_visto < CURRENT_DATE - INTERVAL '3 days'"
                )
                li["stale_3d"] = int(self.cur.fetchone()["c"])
        except Exception:
            pass
        metrics["link_issues"] = li

        return metrics

    def close(self):
        try:
            self.cur.close()
        except Exception:
            pass
        try:
            self.con.close()
        except Exception:
            pass
