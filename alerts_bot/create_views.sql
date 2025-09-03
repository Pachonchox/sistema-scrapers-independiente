-- Vistas SQL para el bot de alertas
-- Adaptadas para trabajar con las tablas de normalización

-- Vista de precios desde la tabla normalized_products
-- Usamos el campo 'precio_min_num' como precio canónico
CREATE OR REPLACE VIEW v_price_ticks AS
SELECT 
    internal_sku, 
    retailer, 
    timestamp AS ts, 
    CAST(precio_min_num AS DOUBLE) AS price
FROM normalized_products
WHERE precio_min_num > 0;

CREATE OR REPLACE VIEW v_current_prices AS
WITH last_ts AS (
  SELECT internal_sku, retailer, MAX(ts) AS max_ts
  FROM v_price_ticks
  GROUP BY 1,2
)
SELECT t.*
FROM v_price_ticks t
JOIN last_ts m
  ON t.internal_sku = m.internal_sku
 AND t.retailer     = m.retailer
 AND t.ts           = m.max_ts;

CREATE OR REPLACE VIEW v_current_spread AS
SELECT
  internal_sku,
  MIN(price) AS min_price,
  MAX(price) AS max_price,
  (MAX(price)-MIN(price))/MIN(price) AS spread_pct,
  COUNT(DISTINCT retailer) AS retailer_count
FROM v_current_prices
GROUP BY internal_sku
HAVING retailer_count >= 2;

CREATE OR REPLACE VIEW v_intraday_delta AS
SELECT
  internal_sku,
  retailer,
  MIN(price) AS min_24h,
  MAX(price) AS max_24h,
  MAX(price) - MIN(price) AS delta_abs,
  (MAX(price) - MIN(price))/NULLIF(MIN(price),0) AS delta_pct
FROM v_price_ticks
WHERE ts >= NOW() - INTERVAL '24 hours'
GROUP BY internal_sku, retailer
HAVING COUNT(*) >= 2;

CREATE OR REPLACE VIEW v_price_history_daily AS
SELECT
  internal_sku,
  retailer,
  DATE_TRUNC('day', ts) AS day,
  MIN(price) AS min_price,
  MAX(price) AS max_price,
  AVG(price) AS avg_price,
  COUNT(*)   AS obs
FROM v_price_ticks
GROUP BY 1,2,3;
