from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import os
import duckdb

class ProductsRepo:
    def __init__(self, duckdb_path: str, parquet_root: str):
        self.duckdb_path = duckdb_path
        self.parquet_root = parquet_root
        self.con = duckdb.connect(self.duckdb_path, read_only=False)
        self._configure()

    def _configure(self):
        # habilitar globbing
        self.con.execute("PRAGMA enable_object_cache;")
        self.con.execute("INSTALL httpfs; LOAD httpfs;")  # por si acaso
        # setea la ruta por defecto
        self.con.execute(f"SET home_directory='{os.path.abspath(self.parquet_root)}';")

    def ensure_views(self, sql_path: str) -> None:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
        self.con.execute(sql)

    # -------- búsquedas --------
    def search_products(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        # Busca en normalized/products
        sql = f"""
        SELECT
          internal_sku,
          brand,
          model,
          normalized_name
        FROM read_parquet('{self.parquet_root}/normalized/products/*.parquet')
        WHERE LOWER(normalized_name) LIKE '%' || LOWER(?) || '%'
           OR LOWER(brand) LIKE '%' || LOWER(?) || '%'
           OR LOWER(model) LIKE '%' || LOWER(?) || '%'
        LIMIT {limit}
        """
        rows = self.con.execute(sql, [query, query, query]).fetchall()
        cols = [d[0] for d in self.con.description]
        return [dict(zip(cols, r)) for r in rows]

    def search_products_enriched(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Búsqueda con ranking simple por tokens y enriquecimiento de precios/spread.
        - Ranking: coincidencias por tokens ponderadas en brand/model/name
        - Enriquecimiento: LEFT JOIN a v_current_spread
        """
        # preparar tokens
        q = (query or "").strip()
        tokens = [t for t in q.lower().split() if t]
        if not tokens:
            return []

        # construir score en SQL
        score_parts = []
        params: List[Any] = []
        for t in tokens:
            like = f"%{t}%"
            score_parts.append("CASE WHEN LOWER(brand) LIKE LOWER(?) THEN 3 ELSE 0 END")
            params.append(like)
            score_parts.append("CASE WHEN LOWER(model) LIKE LOWER(?) THEN 2 ELSE 0 END")
            params.append(like)
            score_parts.append("CASE WHEN LOWER(normalized_name) LIKE LOWER(?) THEN 1 ELSE 0 END")
            params.append(like)

        score_sql = " + ".join(score_parts) or "0"

        sql = f"""
        WITH cand AS (
          SELECT p.internal_sku, p.brand, p.model, p.normalized_name,
                 ({score_sql}) AS score
          FROM read_parquet('{self.parquet_root}/normalized/products/*.parquet') p
        ), ranked AS (
          SELECT * FROM cand WHERE score > 0
        )
        SELECT r.internal_sku, r.brand, r.model, r.normalized_name, r.score,
               s.min_price, s.max_price, s.spread_pct, s.retailer_count
        FROM ranked r
        LEFT JOIN v_current_spread s ON s.internal_sku = r.internal_sku
        ORDER BY r.score DESC, COALESCE(s.retailer_count,0) DESC
        LIMIT {limit}
        """
        rows = self.con.execute(sql, params).fetchall()
        cols = [d[0] for d in self.con.description]
        return [dict(zip(cols, r)) for r in rows]

    # -------- métricas por SKU --------
    def current_spread(self, internal_sku: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
          internal_sku,
          MIN(price) AS min_price,
          MAX(price) AS max_price,
          (MAX(price)-MIN(price))/MIN(price) AS spread_pct,
          COUNT(DISTINCT retailer) AS retailer_count
        FROM v_current_prices
        WHERE internal_sku = ?
        GROUP BY internal_sku
        HAVING retailer_count >= 2
        """
        row = self.con.execute(sql, [internal_sku]).fetchone()
        if not row:
            return None
        cols = [d[0] for d in self.con.description]
        return dict(zip(cols, row))

    def intraday_delta(self, internal_sku: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
          internal_sku,
          retailer,
          min_24h, max_24h, delta_abs, delta_pct
        FROM v_intraday_delta
        WHERE internal_sku = ?
        ORDER BY delta_pct DESC
        LIMIT 1
        """
        row = self.con.execute(sql, [internal_sku]).fetchone()
        if not row:
            return None
        cols = [d[0] for d in self.con.description]
        return dict(zip(cols, row))

    def price_history_daily(self, internal_sku: str, days: int = 30) -> List[Dict[str, Any]]:
        sql = """
        SELECT day, min_price, max_price, avg_price, obs
        FROM v_price_history_daily
        WHERE internal_sku = ? AND day >= DATE 'now' - INTERVAL ? DAY
        ORDER BY day DESC
        LIMIT 365
        """
        rows = self.con.execute(sql, [internal_sku, days]).fetchall()
        cols = [d[0] for d in self.con.description]
        return [dict(zip(cols, r)) for r in rows]

    # -------- agregados --------
    def top_spreads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Top de spreads actuales usando vista v_current_spread si existe."""
        try:
            sql = f"""
            SELECT internal_sku, min_price, max_price, spread_pct, retailer_count
            FROM v_current_spread
            WHERE retailer_count >= 2
            ORDER BY spread_pct DESC
            LIMIT {int(limit)}
            """
            rows = self.con.execute(sql).fetchall()
            cols = [d[0] for d in self.con.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception:
            return []
