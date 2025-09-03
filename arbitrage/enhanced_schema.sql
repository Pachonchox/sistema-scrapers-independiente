-- SCHEMA EXPANDIDO PARA SISTEMA DE ARBITRAJE COMPLETO
-- ===================================================

-- Actualizar tabla de oportunidades con todos los campos necesarios
ALTER TABLE arbitrage_opportunities ADD COLUMN IF NOT EXISTS
    link_producto_barato TEXT,
    link_producto_caro TEXT,
    codigo_sku_barato VARCHAR(100),
    codigo_sku_caro VARCHAR(100),
    categoria_producto VARCHAR(100),
    marca_producto VARCHAR(100),
    rating_barato DECIMAL(3,2),
    rating_caro DECIMAL(3,2),
    reviews_barato INTEGER DEFAULT 0,
    reviews_caro INTEGER DEFAULT 0,
    precio_normal_barato BIGINT,
    precio_normal_caro BIGINT,
    precio_oferta_barato BIGINT,
    precio_oferta_caro BIGINT,
    descuento_porcentaje_barato DECIMAL(5,2),
    descuento_porcentaje_caro DECIMAL(5,2),
    stock_barato BOOLEAN DEFAULT TRUE,
    stock_caro BOOLEAN DEFAULT TRUE,
    fecha_ultima_actualizacion_precio TIMESTAMP DEFAULT NOW(),
    validez_oportunidad VARCHAR(20) DEFAULT 'active',
    confidence_score DECIMAL(5,4),
    times_detected INTEGER DEFAULT 1,
    profit_potential_score DECIMAL(5,4),
    risk_assessment TEXT,
    execution_difficulty VARCHAR(20) DEFAULT 'medium',
    market_trend VARCHAR(20) DEFAULT 'stable',
    competitor_analysis JSONB,
    historical_prices JSONB,
    alerts_sent INTEGER DEFAULT 0,
    last_alert_sent TIMESTAMP,
    user_notes TEXT,
    execution_status VARCHAR(30) DEFAULT 'pending',
    execution_date DATE,
    actual_profit BIGINT,
    execution_notes TEXT;

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_arbitrage_fecha_deteccion ON arbitrage_opportunities(fecha_deteccion DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_margen_bruto ON arbitrage_opportunities(margen_bruto DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_roi ON arbitrage_opportunities(diferencia_porcentaje DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_validez ON arbitrage_opportunities(validez_oportunidad) WHERE validez_oportunidad = 'active';
CREATE INDEX IF NOT EXISTS idx_arbitrage_retailer_compra ON arbitrage_opportunities(retailer_compra);
CREATE INDEX IF NOT EXISTS idx_arbitrage_retailer_venta ON arbitrage_opportunities(retailer_venta);
CREATE INDEX IF NOT EXISTS idx_arbitrage_categoria ON arbitrage_opportunities(categoria_producto);
CREATE INDEX IF NOT EXISTS idx_arbitrage_marca ON arbitrage_opportunities(marca_producto);
CREATE INDEX IF NOT EXISTS idx_arbitrage_execution ON arbitrage_opportunities(execution_status);

-- Tabla para tracking histórico de precios de oportunidades
CREATE TABLE IF NOT EXISTS arbitrage_price_history (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id) ON DELETE CASCADE,
    fecha_check TIMESTAMP DEFAULT NOW(),
    precio_compra_actual BIGINT,
    precio_venta_actual BIGINT,
    margen_actual BIGINT,
    roi_actual DECIMAL(7,2),
    still_valid BOOLEAN DEFAULT TRUE,
    price_change_reason TEXT,
    stock_barato_disponible BOOLEAN DEFAULT TRUE,
    stock_caro_disponible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla para alertas generadas
CREATE TABLE IF NOT EXISTS arbitrage_alerts (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id) ON DELETE CASCADE,
    alert_type VARCHAR(30) NOT NULL, -- 'new_opportunity', 'price_change', 'stock_out', 'validation_failed'
    alert_title VARCHAR(255),
    alert_message TEXT,
    alert_priority VARCHAR(10) DEFAULT 'medium', -- 'high', 'medium', 'low'
    alert_channel VARCHAR(20) DEFAULT 'system', -- 'telegram', 'email', 'webhook', 'system'
    sent_successfully BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de configuración de alertas por usuario/sistema
CREATE TABLE IF NOT EXISTS arbitrage_alert_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(50) UNIQUE NOT NULL,
    min_margin_for_alert BIGINT DEFAULT 10000,
    min_roi_for_alert DECIMAL(5,2) DEFAULT 20.0,
    alert_frequency_minutes INTEGER DEFAULT 60,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    telegram_chat_id VARCHAR(50),
    email_enabled BOOLEAN DEFAULT FALSE,
    email_address VARCHAR(255),
    webhook_enabled BOOLEAN DEFAULT FALSE,
    webhook_url TEXT,
    categories_filter TEXT[], -- Array de categorías a monitorear
    retailers_filter TEXT[], -- Array de retailers a monitorear
    max_alerts_per_hour INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insertar configuración por defecto
INSERT INTO arbitrage_alert_config (config_name, min_margin_for_alert, min_roi_for_alert, alert_frequency_minutes)
VALUES ('default_config', 10000, 20.0, 60)
ON CONFLICT (config_name) DO NOTHING;

-- Tabla para estadísticas y métricas del sistema
CREATE TABLE IF NOT EXISTS arbitrage_stats (
    id SERIAL PRIMARY KEY,
    fecha DATE DEFAULT CURRENT_DATE,
    total_opportunities_detected INTEGER DEFAULT 0,
    total_margin_potential BIGINT DEFAULT 0,
    avg_roi DECIMAL(7,2) DEFAULT 0.0,
    opportunities_by_retailer JSONB,
    opportunities_by_category JSONB,
    top_performing_categories JSONB,
    execution_success_rate DECIMAL(5,2) DEFAULT 0.0,
    total_actual_profit BIGINT DEFAULT 0,
    alerts_sent INTEGER DEFAULT 0,
    system_uptime_hours DECIMAL(10,2) DEFAULT 0.0,
    ml_accuracy DECIMAL(5,4) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fecha)
);

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_arbitrage_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para auto-actualizar updated_at
CREATE TRIGGER update_arbitrage_opportunities_updated_at 
    BEFORE UPDATE ON arbitrage_opportunities 
    FOR EACH ROW EXECUTE FUNCTION update_arbitrage_updated_at_column();

-- Vista para análisis rápido de oportunidades activas
CREATE OR REPLACE VIEW vw_active_opportunities AS
SELECT 
    o.id,
    o.fecha_deteccion,
    o.retailer_compra,
    o.retailer_venta,
    o.marca_producto,
    o.categoria_producto,
    o.precio_compra,
    o.precio_venta,
    o.margen_bruto,
    o.diferencia_porcentaje as roi,
    o.opportunity_score,
    o.confidence_score,
    o.link_producto_barato,
    o.link_producto_caro,
    o.stock_barato,
    o.stock_caro,
    o.execution_status,
    CASE 
        WHEN o.margen_bruto >= 50000 THEN 'HIGH'
        WHEN o.margen_bruto >= 20000 THEN 'MEDIUM'  
        ELSE 'LOW'
    END as profit_tier,
    CASE
        WHEN o.diferencia_porcentaje >= 100 THEN 'EXCELLENT'
        WHEN o.diferencia_porcentaje >= 50 THEN 'GOOD'
        WHEN o.diferencia_porcentaje >= 20 THEN 'FAIR'
        ELSE 'POOR'
    END as roi_tier,
    o.times_detected,
    o.created_at
FROM arbitrage_opportunities o
WHERE o.validez_oportunidad = 'active'
  AND o.stock_barato = TRUE 
  AND o.stock_caro = TRUE
ORDER BY o.margen_bruto DESC;

-- Vista para dashboard ejecutivo
CREATE OR REPLACE VIEW vw_arbitrage_dashboard AS
SELECT 
    COUNT(*) as total_opportunities,
    SUM(margen_bruto) as total_margin_potential,
    AVG(diferencia_porcentaje) as avg_roi,
    MAX(margen_bruto) as best_margin,
    MIN(fecha_deteccion) as first_opportunity,
    MAX(fecha_deteccion) as latest_opportunity,
    COUNT(DISTINCT retailer_compra) as retailers_compra,
    COUNT(DISTINCT retailer_venta) as retailers_venta,
    COUNT(DISTINCT marca_producto) as brands_detected,
    COUNT(DISTINCT categoria_producto) as categories_detected,
    COUNT(*) FILTER (WHERE execution_status = 'executed') as executed_count,
    COUNT(*) FILTER (WHERE execution_status = 'pending') as pending_count,
    SUM(actual_profit) FILTER (WHERE actual_profit IS NOT NULL) as total_actual_profit
FROM arbitrage_opportunities 
WHERE validez_oportunidad = 'active';

-- Comentarios para documentación
COMMENT ON TABLE arbitrage_opportunities IS 'Tabla principal de oportunidades de arbitraje con información completa';
COMMENT ON TABLE arbitrage_price_history IS 'Historial de cambios de precios para tracking de validez';
COMMENT ON TABLE arbitrage_alerts IS 'Log de alertas enviadas por el sistema';
COMMENT ON TABLE arbitrage_alert_config IS 'Configuración de alertas por usuario/sistema';
COMMENT ON TABLE arbitrage_stats IS 'Estadísticas diarias del sistema de arbitraje';
COMMENT ON VIEW vw_active_opportunities IS 'Vista de oportunidades activas con categorización de rentabilidad';
COMMENT ON VIEW vw_arbitrage_dashboard IS 'Vista resumen para dashboard ejecutivo';