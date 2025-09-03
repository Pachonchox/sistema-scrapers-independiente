-- 🤖 ARBITRAGE SYSTEM V5 SCHEMA - VERSIÓN AUTÓNOMA AVANZADA
-- Schema optimizado para integración completa con sistema V5 e inteligencia avanzada

-- Limpiar tablas existentes si existen
DROP TABLE IF EXISTS arbitrage_tracking_v5 CASCADE;
DROP TABLE IF EXISTS arbitrage_opportunities_v5 CASCADE;  
DROP TABLE IF EXISTS product_matching_v5 CASCADE;
DROP TABLE IF EXISTS arbitrage_config_v5 CASCADE;
DROP TABLE IF EXISTS arbitrage_intelligence_v5 CASCADE;
DROP TABLE IF EXISTS arbitrage_metrics_v5 CASCADE;

-- 1. CONFIGURACIÓN DEL SISTEMA V5 🔧
CREATE TABLE arbitrage_config_v5 (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(30) DEFAULT 'string',
    description TEXT,
    
    -- Integración V5
    v5_component VARCHAR(50),        -- Componente V5 relacionado
    intelligence_level VARCHAR(20) DEFAULT 'basic',
    emoji_enabled BOOLEAN DEFAULT TRUE,
    
    -- Control
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. INTELIGENCIA Y CACHE V5 🧠
CREATE TABLE arbitrage_intelligence_v5 (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    product_code VARCHAR(50) NOT NULL,
    retailer VARCHAR(20) NOT NULL,
    
    -- Inteligencia V5
    volatility_score DECIMAL(5,4),           -- Score volatilidad
    popularity_score DECIMAL(5,4),           -- Score popularidad  
    prediction_confidence DECIMAL(5,4),      -- Confianza predicción
    tier_classification VARCHAR(20),         -- critical/important/tracking
    
    -- Cache inteligente
    cache_l1_hits INTEGER DEFAULT 0,
    cache_l2_hits INTEGER DEFAULT 0,
    cache_l3_predictions JSONB,              -- Predicciones L3
    cache_l4_analytics JSONB,                -- Analytics L4
    
    -- Patrones aprendidos
    learned_patterns JSONB,                  -- Patrones detectados
    success_history JSONB,                   -- Histórico éxitos
    timing_patterns JSONB,                   -- Patrones temporales
    
    -- Control temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_analysis TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_product_intelligence UNIQUE(product_code, retailer)
);

-- 3. MATCHING DE PRODUCTOS CON ML V5 🎯  
CREATE TABLE product_matching_v5 (
    id SERIAL PRIMARY KEY,
    
    -- Productos
    codigo_base VARCHAR(50) NOT NULL,
    codigo_match VARCHAR(50) NOT NULL,
    
    -- ML Scoring V5
    similarity_score DECIMAL(5,4) NOT NULL,
    v5_intelligence_score DECIMAL(5,4),      -- Score inteligencia V5
    ml_model_version VARCHAR(30) DEFAULT 'v5.0.0',
    
    -- Análisis V5 avanzado
    brand_match_score DECIMAL(5,4),          -- Score marca
    model_match_score DECIMAL(5,4),          -- Score modelo
    specs_match_score DECIMAL(5,4),          -- Score specs técnicas
    semantic_similarity DECIMAL(5,4),        -- Similaridad semántica
    
    -- Metadatos enriquecidos
    match_type VARCHAR(30) NOT NULL,
    match_confidence VARCHAR(30) NOT NULL,
    match_reason TEXT,
    match_features JSONB,
    v5_analysis JSONB,                       -- Análisis completo V5
    
    -- Redis cache info
    redis_cache_key VARCHAR(100),
    cache_ttl INTEGER,
    
    -- Control
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    verified_manually BOOLEAN DEFAULT FALSE,
    intelligence_verified BOOLEAN DEFAULT FALSE,  -- Verificado por V5
    
    CONSTRAINT unique_product_match_v5 UNIQUE(codigo_base, codigo_match)
);

-- 4. OPORTUNIDADES DE ARBITRAJE V5 💰
CREATE TABLE arbitrage_opportunities_v5 (
    id SERIAL PRIMARY KEY,
    
    -- Productos y matching
    producto_barato_codigo VARCHAR(50) NOT NULL,
    producto_caro_codigo VARCHAR(50) NOT NULL,
    matching_id INTEGER REFERENCES product_matching_v5(id),
    intelligence_id_barato INTEGER REFERENCES arbitrage_intelligence_v5(id),
    intelligence_id_caro INTEGER REFERENCES arbitrage_intelligence_v5(id),
    
    -- Retailers
    retailer_compra VARCHAR(30) NOT NULL,
    retailer_venta VARCHAR(30) NOT NULL,
    
    -- Precios y análisis financiero
    precio_compra BIGINT NOT NULL,
    precio_venta BIGINT NOT NULL,
    diferencia_absoluta BIGINT NOT NULL,
    diferencia_porcentaje DECIMAL(8,2) NOT NULL,
    margen_bruto BIGINT NOT NULL,
    roi_estimado DECIMAL(8,2),
    
    -- Scoring V5 avanzado
    opportunity_score DECIMAL(5,4) NOT NULL,
    volatility_risk_score DECIMAL(5,4),      -- Riesgo volatilidad
    timing_score DECIMAL(5,4),               -- Score timing óptimo
    confidence_score DECIMAL(5,4),           -- Confianza total
    
    -- Clasificación inteligente
    risk_level VARCHAR(30) NOT NULL,
    priority_level INTEGER DEFAULT 3,
    tier_classification VARCHAR(20),         -- Basado en tiers V5
    
    -- Análisis predictivo V5
    predicted_duration_hours INTEGER,        -- Duración estimada
    predicted_success_rate DECIMAL(5,4),     -- Tasa éxito estimada
    optimal_execution_time TIMESTAMPTZ,      -- Momento óptimo ejecución
    
    -- Estado y seguimiento
    status VARCHAR(30) DEFAULT 'detected',
    detection_method VARCHAR(80),
    alert_sent BOOLEAN DEFAULT FALSE,
    emoji_alert TEXT,                        -- Texto alerta con emojis
    
    -- Metadatos V5
    v5_analysis JSONB,                       -- Análisis completo V5
    redis_cache_data JSONB,                  -- Datos cache Redis
    learned_insights JSONB,                  -- Insights aprendidos
    metadata JSONB,
    
    -- Control temporal
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,                  -- Expiración estimada
    
    -- Índice para búsquedas rápidas
    search_vector tsvector
);

-- 5. SEGUIMIENTO HISTÓRICO V5 📊
CREATE TABLE arbitrage_tracking_v5 (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities_v5(id) ON DELETE CASCADE,
    
    -- Snapshot temporal
    fecha_snapshot DATE NOT NULL,
    timestamp_snapshot TIMESTAMPTZ DEFAULT NOW(),
    
    -- Precios actuales
    precio_compra_actual BIGINT,
    precio_venta_actual BIGINT,
    diferencia_actual BIGINT,
    margen_actual BIGINT,
    
    -- Estado y validez
    still_valid BOOLEAN DEFAULT TRUE,
    validity_reason TEXT,
    
    -- Análisis V5 snapshot
    volatility_snapshot DECIMAL(5,4),
    popularity_snapshot DECIMAL(5,4),
    intelligence_snapshot JSONB,
    
    -- Métricas performance
    cache_hit_rate DECIMAL(5,4),
    processing_time_ms INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_opportunity_snapshot_v5 UNIQUE(opportunity_id, fecha_snapshot)
);

-- 6. MÉTRICAS DEL SISTEMA V5 📈
CREATE TABLE arbitrage_metrics_v5 (
    id SERIAL PRIMARY KEY,
    
    -- Período
    metric_date DATE NOT NULL,
    metric_hour INTEGER NOT NULL,  -- 0-23
    
    -- Métricas operacionales
    opportunities_detected INTEGER DEFAULT 0,
    opportunities_valid INTEGER DEFAULT 0,
    total_margin_clp BIGINT DEFAULT 0,
    avg_roi_percentage DECIMAL(8,2) DEFAULT 0,
    
    -- Métricas V5 inteligencia
    cache_hit_rate_l1 DECIMAL(5,4) DEFAULT 0,
    cache_hit_rate_l2 DECIMAL(5,4) DEFAULT 0,
    intelligence_accuracy DECIMAL(5,4) DEFAULT 0,
    prediction_accuracy DECIMAL(5,4) DEFAULT 0,
    
    -- Métricas por tier
    critical_tier_opportunities INTEGER DEFAULT 0,
    important_tier_opportunities INTEGER DEFAULT 0,
    tracking_tier_opportunities INTEGER DEFAULT 0,
    
    -- Performance
    avg_processing_time_ms INTEGER DEFAULT 0,
    redis_operations_count INTEGER DEFAULT 0,
    ml_model_executions INTEGER DEFAULT 0,
    
    -- Retailers
    retailer_performance JSONB,  -- Performance por retailer
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_metric_period UNIQUE(metric_date, metric_hour)
);

-- ÍNDICES OPTIMIZADOS PARA V5 🚀
CREATE INDEX idx_matching_v5_similarity ON product_matching_v5(similarity_score DESC);
CREATE INDEX idx_matching_v5_intelligence ON product_matching_v5(v5_intelligence_score DESC);
CREATE INDEX idx_matching_v5_active ON product_matching_v5(is_active, intelligence_verified);

CREATE INDEX idx_opportunities_v5_score ON arbitrage_opportunities_v5(opportunity_score DESC);
-- Índice para intelligence score se hace a través de matching
-- CREATE INDEX idx_opportunities_v5_intelligence ON arbitrage_opportunities_v5(v5_intelligence_score DESC);
CREATE INDEX idx_opportunities_v5_status ON arbitrage_opportunities_v5(status);
CREATE INDEX idx_opportunities_v5_margin ON arbitrage_opportunities_v5(margen_bruto DESC);
CREATE INDEX idx_opportunities_v5_tier ON arbitrage_opportunities_v5(tier_classification);
CREATE INDEX idx_opportunities_v5_timing ON arbitrage_opportunities_v5(optimal_execution_time);

CREATE INDEX idx_intelligence_v5_product ON arbitrage_intelligence_v5(product_code, retailer);
CREATE INDEX idx_intelligence_v5_tier ON arbitrage_intelligence_v5(tier_classification);
CREATE INDEX idx_intelligence_v5_volatility ON arbitrage_intelligence_v5(volatility_score DESC);

CREATE INDEX idx_tracking_v5_opportunity ON arbitrage_tracking_v5(opportunity_id);
CREATE INDEX idx_tracking_v5_date ON arbitrage_tracking_v5(fecha_snapshot);

CREATE INDEX idx_metrics_v5_date ON arbitrage_metrics_v5(metric_date, metric_hour);

-- FULL TEXT SEARCH para búsquedas rápidas
CREATE INDEX idx_opportunities_v5_search ON arbitrage_opportunities_v5 USING gin(search_vector);

-- CONFIGURACIÓN INICIAL V5 🔧
INSERT INTO arbitrage_config_v5 (config_key, config_value, config_type, description, v5_component, intelligence_level, emoji_enabled) VALUES
-- Parámetros básicos
('min_margin_clp', '15000', 'number', 'Margen mínimo en CLP', 'core', 'advanced', true),
('min_percentage', '12.0', 'number', 'Porcentaje mínimo de diferencia', 'core', 'advanced', true),
('min_similarity_score', '0.80', 'number', 'Score mínimo de similitud ML', 'ml_integration', 'advanced', true),

-- Integración V5
('use_redis_intelligence', 'true', 'boolean', 'Usar Redis Intelligence System', 'redis_intelligence', 'advanced', true),
('use_intelligent_cache', 'true', 'boolean', 'Usar Intelligent Cache Manager', 'cache_manager', 'advanced', true),
('use_volatility_analysis', 'true', 'boolean', 'Usar análisis de volatilidad', 'volatility_analyzer', 'advanced', true),

-- Scheduling inteligente
('critical_tier_frequency', '30', 'number', 'Frecuencia tier crítico (min)', 'scheduler', 'advanced', true),
('important_tier_frequency', '120', 'number', 'Frecuencia tier importante (min)', 'scheduler', 'advanced', true),
('tracking_tier_frequency', '360', 'number', 'Frecuencia tier tracking (min)', 'scheduler', 'advanced', true),

-- Alertas y emojis
('enable_auto_alerts', 'true', 'boolean', 'Alertas automáticas', 'alerts', 'advanced', true),
('enable_emoji_alerts', 'true', 'boolean', 'Emojis en alertas', 'alerts', 'basic', true),
('alert_high_value_threshold', '50000', 'number', 'Umbral alertas alto valor', 'alerts', 'advanced', true),

-- Cache y performance  
('cache_l1_size', '1000', 'number', 'Tamaño cache L1', 'cache_manager', 'advanced', true),
('cache_l2_ttl', '1800', 'number', 'TTL cache L2 (seg)', 'cache_manager', 'advanced', true),
('max_parallel_workers', '4', 'number', 'Workers paralelos máximos', 'core', 'advanced', true);

-- VISTAS OPTIMIZADAS V5 📊

-- Vista de oportunidades activas con inteligencia V5
CREATE VIEW active_opportunities_v5 AS
SELECT 
    ao.*,
    pb.nombre as producto_barato_nombre,
    pb.marca as producto_barato_marca,
    pb.categoria as categoria,
    pc.nombre as producto_caro_nombre,  
    pc.marca as producto_caro_marca,
    pm.similarity_score,
    pm.v5_intelligence_score as match_intelligence_score,
    pm.match_type,
    ib.volatility_score as volatility_barato,
    ic.volatility_score as volatility_caro,
    ib.tier_classification as tier_barato,
    ic.tier_classification as tier_caro
FROM arbitrage_opportunities_v5 ao
JOIN master_productos pb ON ao.producto_barato_codigo = pb.codigo_interno
JOIN master_productos pc ON ao.producto_caro_codigo = pc.codigo_interno
LEFT JOIN product_matching_v5 pm ON ao.matching_id = pm.id
LEFT JOIN arbitrage_intelligence_v5 ib ON ao.intelligence_id_barato = ib.id
LEFT JOIN arbitrage_intelligence_v5 ic ON ao.intelligence_id_caro = ic.id
WHERE ao.status IN ('detected', 'validated', 'confirmed')
ORDER BY pm.v5_intelligence_score DESC, ao.opportunity_score DESC;

-- Vista de top oportunidades por retailer
CREATE VIEW top_opportunities_by_retailer_v5 AS
SELECT 
    retailer_compra,
    retailer_venta,
    COUNT(*) as total_opportunities,
    SUM(margen_bruto) as total_margin_clp,
    AVG(roi_estimado) as avg_roi,
    AVG(opportunity_score) as avg_intelligence_score,
    MAX(opportunity_score) as max_opportunity_score
FROM arbitrage_opportunities_v5 
WHERE status = 'detected' AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY retailer_compra, retailer_venta
ORDER BY avg_intelligence_score DESC, total_margin_clp DESC;

-- Vista de performance V5
CREATE VIEW arbitrage_performance_v5 AS
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as opportunities_detected,
    COUNT(CASE WHEN status = 'validated' THEN 1 END) as opportunities_validated,
    SUM(margen_bruto) as total_margin,
    AVG(opportunity_score) as avg_intelligence,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN alert_sent THEN 1 END) as alerts_sent
FROM arbitrage_opportunities_v5
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY fecha DESC;

-- TRIGGERS PARA MANTENIMIENTO AUTOMÁTICO ⚙️

-- Actualizar search_vector automáticamente
CREATE OR REPLACE FUNCTION update_opportunity_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        to_tsvector('spanish', COALESCE(NEW.emoji_alert, '')) ||
        to_tsvector('spanish', COALESCE(NEW.detection_method, '')) ||
        to_tsvector('spanish', COALESCE(NEW.retailer_compra, '')) ||
        to_tsvector('spanish', COALESCE(NEW.retailer_venta, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_search_vector_trigger
    BEFORE INSERT OR UPDATE ON arbitrage_opportunities_v5
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_search_vector();

-- Actualizar timestamps automáticamente
CREATE OR REPLACE FUNCTION update_timestamps() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_config_timestamp
    BEFORE UPDATE ON arbitrage_config_v5
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamps();

CREATE TRIGGER update_intelligence_timestamp  
    BEFORE UPDATE ON arbitrage_intelligence_v5
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamps();

CREATE TRIGGER update_matching_timestamp
    BEFORE UPDATE ON product_matching_v5
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamps();

CREATE TRIGGER update_opportunity_timestamp
    BEFORE UPDATE ON arbitrage_opportunities_v5
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamps();

-- Comentarios para documentación
COMMENT ON TABLE arbitrage_config_v5 IS '🔧 Configuración sistema arbitraje V5 con inteligencia avanzada';
COMMENT ON TABLE arbitrage_intelligence_v5 IS '🧠 Inteligencia y cache V5 para productos y retailers';
COMMENT ON TABLE product_matching_v5 IS '🎯 Matching productos con ML V5 y análisis avanzado';  
COMMENT ON TABLE arbitrage_opportunities_v5 IS '💰 Oportunidades arbitraje con scoring V5 inteligente';
COMMENT ON TABLE arbitrage_tracking_v5 IS '📊 Seguimiento histórico con métricas V5';
COMMENT ON TABLE arbitrage_metrics_v5 IS '📈 Métricas sistema y performance V5';

-- Schema listo para operación V5 autónoma con inteligencia avanzada 🚀