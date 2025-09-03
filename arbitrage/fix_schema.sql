-- CORRECCIÓN DEL SCHEMA DE ARBITRAJE
-- ===================================

-- Agregar columnas una por una para evitar errores de sintaxis
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS link_producto_barato TEXT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS link_producto_caro TEXT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS codigo_sku_barato VARCHAR(100);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS codigo_sku_caro VARCHAR(100);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS categoria_producto VARCHAR(100);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS marca_producto VARCHAR(100);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS rating_barato DECIMAL(3,2);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS rating_caro DECIMAL(3,2);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS reviews_barato INTEGER DEFAULT 0;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS reviews_caro INTEGER DEFAULT 0;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS precio_normal_barato BIGINT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS precio_normal_caro BIGINT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS precio_oferta_barato BIGINT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS precio_oferta_caro BIGINT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS descuento_porcentaje_barato DECIMAL(5,2);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS descuento_porcentaje_caro DECIMAL(5,2);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS stock_barato BOOLEAN DEFAULT TRUE;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS stock_caro BOOLEAN DEFAULT TRUE;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS fecha_ultima_actualizacion_precio TIMESTAMP DEFAULT NOW();
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS validez_oportunidad VARCHAR(20) DEFAULT 'active';
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,4);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS times_detected INTEGER DEFAULT 1;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS profit_potential_score DECIMAL(5,4);
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS risk_assessment TEXT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS execution_difficulty VARCHAR(20) DEFAULT 'medium';
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS market_trend VARCHAR(20) DEFAULT 'stable';
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS competitor_analysis JSONB;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS historical_prices JSONB;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS alerts_sent INTEGER DEFAULT 0;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS last_alert_sent TIMESTAMP;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS user_notes TEXT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS execution_status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS execution_date DATE;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS actual_profit BIGINT;
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS execution_notes TEXT;

-- Crear índices (solo si las columnas existen)
CREATE INDEX IF NOT EXISTS idx_arbitrage_validez ON arbitrage_opportunities(validez_oportunidad) WHERE validez_oportunidad = 'active';
CREATE INDEX IF NOT EXISTS idx_arbitrage_categoria ON arbitrage_opportunities(categoria_producto);
CREATE INDEX IF NOT EXISTS idx_arbitrage_marca ON arbitrage_opportunities(marca_producto);
CREATE INDEX IF NOT EXISTS idx_arbitrage_execution ON arbitrage_opportunities(execution_status);