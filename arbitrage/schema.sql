-- ARBITRAGE SYSTEM SCHEMA
-- Sistema de arbitraje separado del flujo principal
-- Optimizado para matching ML y detección de oportunidades

-- 1. TABLA DE MATCHING DE PRODUCTOS
CREATE TABLE IF NOT EXISTS product_matching (
    id SERIAL PRIMARY KEY,
    codigo_base VARCHAR(50) REFERENCES master_productos(codigo_interno),
    codigo_match VARCHAR(50) REFERENCES master_productos(codigo_interno),
    
    -- Scoring ML
    similarity_score DECIMAL(5,4) NOT NULL CHECK (similarity_score >= 0.7 AND similarity_score <= 1.0),
    match_type VARCHAR(20) NOT NULL CHECK (match_type IN ('exact', 'similar', 'variant', 'category')),
    match_confidence VARCHAR(20) NOT NULL CHECK (match_confidence IN ('high', 'medium', 'low')),
    
    -- Metadatos del matching
    match_reason TEXT,
    match_features JSONB,
    ml_model_version VARCHAR(20) DEFAULT '1.0',
    
    -- Control temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    verified_manually BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT unique_product_match UNIQUE(codigo_base, codigo_match),
    CONSTRAINT no_self_match CHECK (codigo_base != codigo_match)
);

-- 2. TABLA DE OPORTUNIDADES DE ARBITRAJE
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    
    -- Productos y matching
    producto_barato_codigo VARCHAR(50) REFERENCES master_productos(codigo_interno),
    producto_caro_codigo VARCHAR(50) REFERENCES master_productos(codigo_interno),
    matching_id INTEGER REFERENCES product_matching(id),
    
    -- Información de retailers
    retailer_compra VARCHAR(20) NOT NULL,
    retailer_venta VARCHAR(20) NOT NULL,
    
    -- Precios actuales
    precio_compra BIGINT NOT NULL CHECK (precio_compra > 0),
    precio_venta BIGINT NOT NULL CHECK (precio_venta > precio_compra),
    diferencia_absoluta BIGINT NOT NULL,
    diferencia_porcentaje DECIMAL(6,2) NOT NULL,
    
    -- Análisis de arbitraje
    margen_bruto BIGINT NOT NULL,
    roi_estimado DECIMAL(6,2),
    costos_estimados BIGINT DEFAULT 0,
    ganancia_neta BIGINT,
    
    -- Scoring de oportunidad
    opportunity_score DECIMAL(5,4) NOT NULL CHECK (opportunity_score >= 0.5 AND opportunity_score <= 1.0),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    priority_level INTEGER DEFAULT 3 CHECK (priority_level BETWEEN 1 AND 5),
    
    -- Estado y validez
    status VARCHAR(20) DEFAULT 'detected' CHECK (status IN ('detected', 'validated', 'monitoring', 'expired', 'executed')),
    expiry_date TIMESTAMPTZ,
    confidence_level DECIMAL(3,2) DEFAULT 0.85,
    
    -- Metadatos
    detection_method VARCHAR(50),
    metadata JSONB,
    alerts_sent INTEGER DEFAULT 0,
    
    -- Control temporal
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ,
    last_price_check TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints únicos
    CONSTRAINT unique_daily_opportunity UNIQUE(producto_barato_codigo, producto_caro_codigo, detected_at::date),
    CONSTRAINT different_retailers CHECK (retailer_compra != retailer_venta)
);

-- 3. TABLA DE SEGUIMIENTO HISTÓRICO
CREATE TABLE IF NOT EXISTS arbitrage_tracking (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id) ON DELETE CASCADE,
    
    -- Snapshot temporal
    fecha_snapshot DATE NOT NULL,
    precio_compra_actual BIGINT,
    precio_venta_actual BIGINT,
    diferencia_actual BIGINT,
    margen_actual BIGINT,
    
    -- Estado de validez
    still_valid BOOLEAN NOT NULL DEFAULT TRUE,
    oportunidad_perdida BOOLEAN DEFAULT FALSE,
    
    -- Cambios vs snapshot anterior
    precio_change_compra BIGINT DEFAULT 0,
    precio_change_venta BIGINT DEFAULT 0,
    cambio_porcentual DECIMAL(5,2) DEFAULT 0,
    
    -- Metadatos del snapshot
    snapshot_reason VARCHAR(50),
    data_quality_score DECIMAL(3,2) DEFAULT 1.0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_opportunity_snapshot UNIQUE(opportunity_id, fecha_snapshot)
);

-- 4. TABLA DE CONFIGURACIÓN Y PARÁMETROS
CREATE TABLE IF NOT EXISTS arbitrage_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (config_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ÍNDICES OPTIMIZADOS PARA PERFORMANCE

-- Índices para product_matching
CREATE INDEX IF NOT EXISTS idx_matching_similarity ON product_matching(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_matching_type ON product_matching(match_type);
CREATE INDEX IF NOT EXISTS idx_matching_active ON product_matching(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_matching_base_code ON product_matching(codigo_base);
CREATE INDEX IF NOT EXISTS idx_matching_match_code ON product_matching(codigo_match);
CREATE INDEX IF NOT EXISTS idx_matching_updated ON product_matching(updated_at DESC);

-- Índices para arbitrage_opportunities
CREATE INDEX IF NOT EXISTS idx_arbitrage_score ON arbitrage_opportunities(opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_margin ON arbitrage_opportunities(margen_bruto DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_roi ON arbitrage_opportunities(roi_estimado DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_status ON arbitrage_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_arbitrage_priority ON arbitrage_opportunities(priority_level, opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_retailer_compra ON arbitrage_opportunities(retailer_compra);
CREATE INDEX IF NOT EXISTS idx_arbitrage_retailer_venta ON arbitrage_opportunities(retailer_venta);
CREATE INDEX IF NOT EXISTS idx_arbitrage_detected ON arbitrage_opportunities(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_active ON arbitrage_opportunities(status) WHERE status IN ('detected', 'validated', 'monitoring');

-- Índices para arbitrage_tracking
CREATE INDEX IF NOT EXISTS idx_tracking_opportunity ON arbitrage_tracking(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_tracking_date ON arbitrage_tracking(fecha_snapshot DESC);
CREATE INDEX IF NOT EXISTS idx_tracking_valid ON arbitrage_tracking(still_valid) WHERE still_valid = TRUE;

-- Índices compuestos para queries complejas
CREATE INDEX IF NOT EXISTS idx_opportunities_score_status ON arbitrage_opportunities(status, opportunity_score DESC, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_matching_active_score ON product_matching(is_active, similarity_score DESC) WHERE is_active = TRUE;

-- CONFIGURACIÓN INICIAL
INSERT INTO arbitrage_config (config_key, config_value, config_type, description) VALUES
('min_margin_clp', '5000', 'number', 'Margen mínimo en CLP para considerar oportunidad'),
('min_percentage', '15.0', 'number', 'Porcentaje mínimo de diferencia para oportunidad'),
('min_similarity_score', '0.85', 'number', 'Score mínimo de similitud para matching'),
('max_risk_tolerance', 'medium', 'string', 'Nivel máximo de riesgo aceptable'),
('update_frequency_minutes', '30', 'number', 'Frecuencia de actualización en minutos'),
('max_opportunities_per_day', '50', 'number', 'Máximo de oportunidades a detectar por día'),
('enable_auto_alerts', 'true', 'boolean', 'Habilitar alertas automáticas'),
('default_costs_percentage', '8.5', 'number', 'Porcentaje de costos por defecto (shipping, fees, etc)')
ON CONFLICT (config_key) DO NOTHING;

-- FUNCIONES AUXILIARES

-- Función para limpiar oportunidades expiradas
CREATE OR REPLACE FUNCTION cleanup_expired_opportunities()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Marcar como expiradas las oportunidades viejas
    UPDATE arbitrage_opportunities 
    SET status = 'expired', updated_at = NOW()
    WHERE status IN ('detected', 'validated')
    AND detected_at < NOW() - INTERVAL '24 hours';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para calcular score de oportunidad
CREATE OR REPLACE FUNCTION calculate_opportunity_score(
    p_diferencia_porcentaje DECIMAL,
    p_similarity_score DECIMAL,
    p_margen_bruto BIGINT
) RETURNS DECIMAL AS $$
BEGIN
    -- Score basado en: 40% diferencia, 30% similitud, 30% margen absoluto
    RETURN LEAST(1.0, 
        (p_diferencia_porcentaje / 100.0 * 0.4) +
        (p_similarity_score * 0.3) +
        (LEAST(p_margen_bruto / 100000.0, 1.0) * 0.3)
    );
END;
$$ LANGUAGE plpgsql;

-- TRIGGERS PARA AUTOMATIZACIÓN

-- Trigger para actualizar opportunity_score automáticamente
CREATE OR REPLACE FUNCTION update_opportunity_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.opportunity_score = calculate_opportunity_score(
        NEW.diferencia_porcentaje,
        COALESCE((SELECT similarity_score FROM product_matching WHERE id = NEW.matching_id), 0.85),
        NEW.margen_bruto
    );
    
    NEW.updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_opportunity_score
    BEFORE INSERT OR UPDATE ON arbitrage_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_score();

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_matching_updated_at
    BEFORE UPDATE ON product_matching
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- VIEWS ÚTILES

-- Vista de oportunidades activas con información completa
CREATE OR REPLACE VIEW active_opportunities AS
SELECT 
    ao.*,
    pb.nombre as producto_barato_nombre,
    pb.marca as producto_barato_marca,
    pc.nombre as producto_caro_nombre,  
    pc.marca as producto_caro_marca,
    pm.similarity_score,
    pm.match_type,
    pm.match_confidence
FROM arbitrage_opportunities ao
JOIN master_productos pb ON ao.producto_barato_codigo = pb.codigo_interno
JOIN master_productos pc ON ao.producto_caro_codigo = pc.codigo_interno
LEFT JOIN product_matching pm ON ao.matching_id = pm.id
WHERE ao.status IN ('detected', 'validated', 'monitoring')
ORDER BY ao.opportunity_score DESC, ao.margen_bruto DESC;

-- Vista de estadísticas de arbitraje
CREATE OR REPLACE VIEW arbitrage_stats AS
SELECT 
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN status = 'detected' THEN 1 END) as detected_count,
    COUNT(CASE WHEN status = 'validated' THEN 1 END) as validated_count,
    COUNT(CASE WHEN status = 'monitoring' THEN 1 END) as monitoring_count,
    AVG(opportunity_score) as avg_opportunity_score,
    AVG(diferencia_porcentaje) as avg_percentage_diff,
    SUM(margen_bruto) as total_potential_margin,
    MAX(detected_at) as last_detection,
    COUNT(DISTINCT retailer_compra) as unique_buy_retailers,
    COUNT(DISTINCT retailer_venta) as unique_sell_retailers
FROM arbitrage_opportunities
WHERE detected_at >= CURRENT_DATE - INTERVAL '7 days';

COMMENT ON TABLE product_matching IS 'Matching ML entre productos de diferentes retailers';
COMMENT ON TABLE arbitrage_opportunities IS 'Oportunidades de arbitraje detectadas automáticamente';  
COMMENT ON TABLE arbitrage_tracking IS 'Seguimiento histórico de oportunidades';
COMMENT ON TABLE arbitrage_config IS 'Configuración del sistema de arbitraje';