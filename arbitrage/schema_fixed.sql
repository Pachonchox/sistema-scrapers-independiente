-- ARBITRAGE SYSTEM SCHEMA - FIXED VERSION
-- Eliminando conflictos y corrigiendo sintaxis

-- Limpiar tablas existentes si existen
DROP TABLE IF EXISTS arbitrage_tracking CASCADE;
DROP TABLE IF EXISTS arbitrage_opportunities CASCADE;  
DROP TABLE IF EXISTS product_matching CASCADE;
DROP TABLE IF EXISTS arbitrage_config CASCADE;

-- 1. CONFIGURACIÓN DEL SISTEMA
CREATE TABLE arbitrage_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. MATCHING DE PRODUCTOS  
CREATE TABLE product_matching (
    id SERIAL PRIMARY KEY,
    codigo_base VARCHAR(50) REFERENCES master_productos(codigo_interno),
    codigo_match VARCHAR(50) REFERENCES master_productos(codigo_interno),
    
    -- Scoring ML
    similarity_score DECIMAL(5,4) NOT NULL,
    match_type VARCHAR(20) NOT NULL,
    match_confidence VARCHAR(20) NOT NULL,
    
    -- Metadatos
    match_reason TEXT,
    match_features JSONB,
    ml_model_version VARCHAR(20) DEFAULT '1.0',
    
    -- Control
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    verified_manually BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT unique_product_match UNIQUE(codigo_base, codigo_match)
);

-- 3. OPORTUNIDADES DE ARBITRAJE
CREATE TABLE arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    
    -- Productos
    producto_barato_codigo VARCHAR(50) REFERENCES master_productos(codigo_interno),
    producto_caro_codigo VARCHAR(50) REFERENCES master_productos(codigo_interno),
    matching_id INTEGER REFERENCES product_matching(id),
    
    -- Retailers
    retailer_compra VARCHAR(20) NOT NULL,
    retailer_venta VARCHAR(20) NOT NULL,
    
    -- Precios
    precio_compra BIGINT NOT NULL,
    precio_venta BIGINT NOT NULL,
    diferencia_absoluta BIGINT NOT NULL,
    diferencia_porcentaje DECIMAL(6,2) NOT NULL,
    
    -- Análisis
    margen_bruto BIGINT NOT NULL,
    roi_estimado DECIMAL(6,2),
    opportunity_score DECIMAL(5,4) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    priority_level INTEGER DEFAULT 3,
    
    -- Estado
    status VARCHAR(20) DEFAULT 'detected',
    detection_method VARCHAR(50),
    metadata JSONB,
    
    -- Control temporal
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. SEGUIMIENTO HISTÓRICO
CREATE TABLE arbitrage_tracking (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id) ON DELETE CASCADE,
    
    -- Snapshot
    fecha_snapshot DATE NOT NULL,
    precio_compra_actual BIGINT,
    precio_venta_actual BIGINT,
    diferencia_actual BIGINT,
    
    -- Estado
    still_valid BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_opportunity_snapshot UNIQUE(opportunity_id, fecha_snapshot)
);

-- ÍNDICES BÁSICOS
CREATE INDEX idx_matching_similarity ON product_matching(similarity_score DESC);
CREATE INDEX idx_matching_active ON product_matching(is_active);
CREATE INDEX idx_opportunities_score ON arbitrage_opportunities(opportunity_score DESC);
CREATE INDEX idx_opportunities_status ON arbitrage_opportunities(status);
CREATE INDEX idx_opportunities_margin ON arbitrage_opportunities(margen_bruto DESC);
CREATE INDEX idx_tracking_opportunity ON arbitrage_tracking(opportunity_id);

-- CONFIGURACIÓN INICIAL
INSERT INTO arbitrage_config (config_key, config_value, config_type, description) VALUES
('min_margin_clp', '5000', 'number', 'Margen mínimo en CLP'),
('min_percentage', '15.0', 'number', 'Porcentaje mínimo de diferencia'),
('min_similarity_score', '0.85', 'number', 'Score mínimo de similitud'),
('update_frequency_minutes', '30', 'number', 'Frecuencia de actualización'),
('enable_auto_alerts', 'true', 'boolean', 'Alertas automáticas');

-- VISTA DE OPORTUNIDADES ACTIVAS
CREATE VIEW active_opportunities AS
SELECT 
    ao.*,
    pb.nombre as producto_barato_nombre,
    pb.marca as producto_barato_marca,
    pc.nombre as producto_caro_nombre,  
    pc.marca as producto_caro_marca,
    pm.similarity_score,
    pm.match_type
FROM arbitrage_opportunities ao
JOIN master_productos pb ON ao.producto_barato_codigo = pb.codigo_interno
JOIN master_productos pc ON ao.producto_caro_codigo = pc.codigo_interno
LEFT JOIN product_matching pm ON ao.matching_id = pm.id
WHERE ao.status IN ('detected', 'validated')
ORDER BY ao.opportunity_score DESC;