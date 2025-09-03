# -*- coding: utf-8 -*-
"""
🗄️ Database Manager V5 - Gestor de Base de Datos Autónomo
========================================================
Gestor de conexiones PostgreSQL optimizado para sistema de arbitraje V5.
Compatible con emojis y integrado con inteligencia avanzada.
"""

import logging
import asyncio
import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import asynccontextmanager, contextmanager
from typing import Dict, List, Any, Optional, AsyncGenerator, Generator, Union
import json
from datetime import datetime, date
from pathlib import Path

from ..config.arbitrage_config import ArbitrageConfigV5, get_config

logger = logging.getLogger(__name__)

class DatabaseManagerV5:
    """
    Gestor de base de datos V5 con inteligencia avanzada 🧠
    
    Características:
    - 🔌 Conexiones síncronas y asíncronas  
    - 🎯 Pool de conexiones optimizado
    - 📊 Métricas integradas
    - 🔄 Reconexión automática
    - 🛡️ Manejo robusto de errores
    - 💾 Cache de queries frecuentes
    """
    
    def __init__(self, config: Optional[ArbitrageConfigV5] = None):
        """Inicializar database manager"""
        self.config = config or get_config()
        self.db_config = self.config.database_config
        
        # Pool de conexiones
        self._async_pool = None
        self._sync_connections = {}
        
        # Métricas
        self.connection_attempts = 0
        self.successful_connections = 0
        self.query_count = 0
        self.error_count = 0
        
        # Cache de queries
        self._query_cache = {}
        self._schema_initialized = False
        
        logger.info("🗄️ DatabaseManager V5 inicializado con pool optimizado")
    
    async def initialize_async_pool(self):
        """Inicializar pool de conexiones asíncronas 🔌"""
        try:
            self.connection_attempts += 1
            
            self._async_pool = await asyncpg.create_pool(
                host=self.db_config['host'],
                port=self.db_config['port'], 
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                min_size=2,
                max_size=self.db_config.get('max_connections', 10),
                command_timeout=60,
                server_settings={
                    'application_name': 'arbitrage_v5',
                    'search_path': 'public'
                }
            )
            
            self.successful_connections += 1
            logger.info("✅ Pool de conexiones async inicializado correctamente")
            
            # Verificar schema
            await self._verify_schema()
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Error inicializando pool async: {e}")
            raise
    
    @asynccontextmanager
    async def get_async_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Context manager para conexión asíncrona 🔄"""
        if not self._async_pool:
            await self.initialize_async_pool()
        
        async with self._async_pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"⚠️ Error en conexión async: {e}")
                raise
            finally:
                self.query_count += 1
    
    @contextmanager  
    def get_sync_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Context manager para conexión síncrona 🔗"""
        conn = None
        try:
            self.connection_attempts += 1
            
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'], 
                user=self.db_config['user'],
                password=self.db_config['password'],
                cursor_factory=RealDictCursor,
                application_name='arbitrage_v5_sync'
            )
            
            self.successful_connections += 1
            yield conn
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Error en conexión sync: {e}")
            if conn:
                conn.rollback()
            raise
            
        finally:
            if conn:
                conn.close()
            self.query_count += 1
    
    async def _verify_schema(self):
        """Verificar que el schema V5 esté instalado 🔍"""
        try:
            async with self.get_async_connection() as conn:
                # Verificar tablas principales
                tables_to_check = [
                    'arbitrage_config_v5',
                    'arbitrage_intelligence_v5', 
                    'product_matching_v5',
                    'arbitrage_opportunities_v5'
                ]
                
                for table in tables_to_check:
                    exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    
                    if not exists:
                        logger.warning(f"⚠️ Tabla {table} no existe - schema V5 no instalado")
                        self._schema_initialized = False
                        return
                
                self._schema_initialized = True
                logger.info("✅ Schema V5 verificado correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error verificando schema: {e}")
            self._schema_initialized = False
    
    async def install_schema(self, force: bool = False):
        """Instalar schema V5 desde archivo SQL 🛠️"""
        if self._schema_initialized and not force:
            logger.info("📋 Schema V5 ya está instalado")
            return
        
        try:
            schema_file = Path(__file__).parent / "schema_v5.sql"
            
            if not schema_file.exists():
                raise FileNotFoundError(f"Archivo schema no encontrado: {schema_file}")
            
            schema_sql = schema_file.read_text(encoding='utf-8')
            
            async with self.get_async_connection() as conn:
                # Ejecutar en transacción
                async with conn.transaction():
                    await conn.execute(schema_sql)
                
                logger.info("✅ Schema V5 instalado correctamente")
                self._schema_initialized = True
                
        except Exception as e:
            logger.error(f"❌ Error instalando schema: {e}")
            raise
    
    # === OPERACIONES DE CONFIGURACIÓN ===
    
    async def get_config_value(self, config_key: str, default: Any = None) -> Any:
        """Obtener valor de configuración 🔧"""
        try:
            async with self.get_async_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT config_value, config_type FROM arbitrage_config_v5 WHERE config_key = $1 AND is_active = TRUE",
                    config_key
                )
                
                if not row:
                    return default
                
                value = row['config_value']
                config_type = row['config_type']
                
                # Convertir tipo
                if config_type == 'number':
                    return float(value) if '.' in value else int(value)
                elif config_type == 'boolean':
                    return value.lower() in ('true', '1', 'yes')
                elif config_type == 'json':
                    return json.loads(value)
                else:
                    return value
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo config {config_key}: {e}")
            return default
    
    async def set_config_value(self, config_key: str, value: Any, config_type: str = 'string', description: str = ''):
        """Establecer valor de configuración ⚙️"""
        try:
            # Convertir valor a string
            if isinstance(value, (dict, list)):
                str_value = json.dumps(value)
                config_type = 'json'
            elif isinstance(value, bool):
                str_value = str(value).lower()
                config_type = 'boolean'
            elif isinstance(value, (int, float)):
                str_value = str(value)
                config_type = 'number'
            else:
                str_value = str(value)
            
            async with self.get_async_connection() as conn:
                await conn.execute("""
                    INSERT INTO arbitrage_config_v5 (config_key, config_value, config_type, description, v5_component)
                    VALUES ($1, $2, $3, $4, 'user_defined')
                    ON CONFLICT (config_key) 
                    DO UPDATE SET 
                        config_value = EXCLUDED.config_value,
                        config_type = EXCLUDED.config_type,
                        description = EXCLUDED.description,
                        updated_at = NOW()
                """, config_key, str_value, config_type, description)
                
                logger.info(f"⚙️ Configuración actualizada: {config_key} = {value}")
                
        except Exception as e:
            logger.error(f"❌ Error estableciendo config {config_key}: {e}")
            raise
    
    # === OPERACIONES DE INTELIGENCIA ===
    
    async def get_product_intelligence(self, product_code: str, retailer: str) -> Optional[Dict[str, Any]]:
        """Obtener datos de inteligencia de producto 🧠"""
        try:
            async with self.get_async_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM arbitrage_intelligence_v5 
                    WHERE product_code = $1 AND retailer = $2
                """, product_code, retailer)
                
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo inteligencia producto {product_code}: {e}")
            return None
    
    async def update_product_intelligence(self, product_code: str, retailer: str, intelligence_data: Dict[str, Any]):
        """Actualizar datos de inteligencia de producto 🔄"""
        try:
            async with self.get_async_connection() as conn:
                await conn.execute("""
                    INSERT INTO arbitrage_intelligence_v5 
                    (product_code, retailer, volatility_score, popularity_score, prediction_confidence, 
                     tier_classification, cache_l3_predictions, cache_l4_analytics, learned_patterns, 
                     success_history, timing_patterns)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (product_code, retailer)
                    DO UPDATE SET
                        volatility_score = EXCLUDED.volatility_score,
                        popularity_score = EXCLUDED.popularity_score,
                        prediction_confidence = EXCLUDED.prediction_confidence,
                        tier_classification = EXCLUDED.tier_classification,
                        cache_l3_predictions = EXCLUDED.cache_l3_predictions,
                        cache_l4_analytics = EXCLUDED.cache_l4_analytics,
                        learned_patterns = EXCLUDED.learned_patterns,
                        success_history = EXCLUDED.success_history,
                        timing_patterns = EXCLUDED.timing_patterns,
                        updated_at = NOW(),
                        last_analysis = NOW()
                """, 
                product_code, retailer,
                intelligence_data.get('volatility_score'),
                intelligence_data.get('popularity_score'), 
                intelligence_data.get('prediction_confidence'),
                intelligence_data.get('tier_classification'),
                json.dumps(intelligence_data.get('cache_l3_predictions', {})),
                json.dumps(intelligence_data.get('cache_l4_analytics', {})),
                json.dumps(intelligence_data.get('learned_patterns', {})),
                json.dumps(intelligence_data.get('success_history', {})),
                json.dumps(intelligence_data.get('timing_patterns', {}))
                )
                
                logger.debug(f"🧠 Inteligencia actualizada: {product_code} ({retailer})")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando inteligencia: {e}")
            raise
    
    # === OPERACIONES DE MATCHING ===
    
    async def save_product_match(self, match_data: Dict[str, Any]) -> int:
        """Guardar matching de productos 🎯"""
        try:
            async with self.get_async_connection() as conn:
                match_id = await conn.fetchval("""
                    INSERT INTO product_matching_v5 
                    (codigo_base, codigo_match, similarity_score, v5_intelligence_score,
                     brand_match_score, model_match_score, specs_match_score, semantic_similarity,
                     match_type, match_confidence, match_reason, match_features, v5_analysis,
                     ml_model_version, redis_cache_key)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (codigo_base, codigo_match)
                    DO UPDATE SET
                        similarity_score = EXCLUDED.similarity_score,
                        v5_intelligence_score = EXCLUDED.v5_intelligence_score,
                        updated_at = NOW()
                    RETURNING id
                """,
                match_data['codigo_base'], match_data['codigo_match'],
                match_data['similarity_score'], match_data.get('v5_intelligence_score'),
                match_data.get('brand_match_score'), match_data.get('model_match_score'),
                match_data.get('specs_match_score'), match_data.get('semantic_similarity'),
                match_data['match_type'], match_data['match_confidence'],
                match_data.get('match_reason'), json.dumps(match_data.get('match_features', {})),
                json.dumps(match_data.get('v5_analysis', {})), 
                match_data.get('ml_model_version', 'v5.0.0'),
                match_data.get('redis_cache_key')
                )
                
                logger.debug(f"🎯 Match guardado: {match_data['codigo_base']} <-> {match_data['codigo_match']}")
                return match_id
                
        except Exception as e:
            logger.error(f"❌ Error guardando match: {e}")
            raise
    
    async def get_product_matches(self, product_code: str, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Obtener matches de un producto 📋"""
        try:
            async with self.get_async_connection() as conn:
                rows = await conn.fetch("""
                    SELECT pm.*, mp.nombre, mp.marca, mp.retailer
                    FROM product_matching_v5 pm
                    JOIN master_productos mp ON pm.codigo_match = mp.codigo_interno
                    WHERE pm.codigo_base = $1 
                    AND pm.similarity_score >= $2
                    AND pm.is_active = TRUE
                    ORDER BY pm.v5_intelligence_score DESC, pm.similarity_score DESC
                """, product_code, min_similarity)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo matches: {e}")
            return []
    
    # === OPERACIONES DE OPORTUNIDADES ===
    
    async def save_arbitrage_opportunity(self, opportunity: Dict[str, Any]) -> int:
        """Guardar oportunidad de arbitraje 💰"""
        try:
            async with self.get_async_connection() as conn:
                opp_id = await conn.fetchval("""
                    INSERT INTO arbitrage_opportunities_v5
                    (producto_barato_codigo, producto_caro_codigo, matching_id,
                     retailer_compra, retailer_venta, precio_compra, precio_venta,
                     diferencia_absoluta, diferencia_porcentaje, margen_bruto, roi_estimado,
                     opportunity_score, v5_intelligence_score, volatility_risk_score,
                     timing_score, confidence_score, risk_level, priority_level,
                     tier_classification, predicted_duration_hours, predicted_success_rate,
                     optimal_execution_time, detection_method, emoji_alert,
                     v5_analysis, redis_cache_data, learned_insights, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28)
                    RETURNING id
                """,
                opportunity['producto_barato_codigo'], opportunity['producto_caro_codigo'],
                opportunity.get('matching_id'), opportunity['retailer_compra'], opportunity['retailer_venta'],
                opportunity['precio_compra'], opportunity['precio_venta'],
                opportunity['diferencia_absoluta'], opportunity['diferencia_porcentaje'],
                opportunity['margen_bruto'], opportunity.get('roi_estimado'),
                opportunity['opportunity_score'], opportunity.get('v5_intelligence_score'),
                opportunity.get('volatility_risk_score'), opportunity.get('timing_score'),
                opportunity.get('confidence_score'), opportunity['risk_level'],
                opportunity.get('priority_level', 3), opportunity.get('tier_classification'),
                opportunity.get('predicted_duration_hours'), opportunity.get('predicted_success_rate'),
                opportunity.get('optimal_execution_time'), opportunity.get('detection_method'),
                opportunity.get('emoji_alert'), json.dumps(opportunity.get('v5_analysis', {})),
                json.dumps(opportunity.get('redis_cache_data', {})),
                json.dumps(opportunity.get('learned_insights', {})),
                json.dumps(opportunity.get('metadata', {}))
                )
                
                logger.info(f"💰 Oportunidad guardada: ID {opp_id} - Margen ${opportunity['margen_bruto']:,.0f}")
                return opp_id
                
        except Exception as e:
            logger.error(f"❌ Error guardando oportunidad: {e}")
            raise
    
    async def get_active_opportunities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener oportunidades activas 📊"""
        try:
            async with self.get_async_connection() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM active_opportunities_v5 
                    WHERE status IN ('detected', 'validated', 'confirmed')
                    ORDER BY v5_intelligence_score DESC, opportunity_score DESC
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo oportunidades activas: {e}")
            return []
    
    # === MÉTRICAS Y ESTADÍSTICAS ===
    
    async def record_metrics(self, metric_data: Dict[str, Any]):
        """Registrar métricas del sistema 📈"""
        try:
            current_time = datetime.now()
            metric_date = current_time.date()
            metric_hour = current_time.hour
            
            async with self.get_async_connection() as conn:
                await conn.execute("""
                    INSERT INTO arbitrage_metrics_v5 
                    (metric_date, metric_hour, opportunities_detected, opportunities_valid,
                     total_margin_clp, avg_roi_percentage, cache_hit_rate_l1, cache_hit_rate_l2,
                     intelligence_accuracy, prediction_accuracy, critical_tier_opportunities,
                     important_tier_opportunities, tracking_tier_opportunities,
                     avg_processing_time_ms, redis_operations_count, ml_model_executions,
                     retailer_performance)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    ON CONFLICT (metric_date, metric_hour)
                    DO UPDATE SET
                        opportunities_detected = EXCLUDED.opportunities_detected,
                        opportunities_valid = EXCLUDED.opportunities_valid,
                        total_margin_clp = EXCLUDED.total_margin_clp,
                        avg_roi_percentage = EXCLUDED.avg_roi_percentage,
                        updated_at = NOW()
                """,
                metric_date, metric_hour,
                metric_data.get('opportunities_detected', 0),
                metric_data.get('opportunities_valid', 0), 
                metric_data.get('total_margin_clp', 0),
                metric_data.get('avg_roi_percentage', 0),
                metric_data.get('cache_hit_rate_l1', 0),
                metric_data.get('cache_hit_rate_l2', 0),
                metric_data.get('intelligence_accuracy', 0),
                metric_data.get('prediction_accuracy', 0),
                metric_data.get('critical_tier_opportunities', 0),
                metric_data.get('important_tier_opportunities', 0),
                metric_data.get('tracking_tier_opportunities', 0),
                metric_data.get('avg_processing_time_ms', 0),
                metric_data.get('redis_operations_count', 0),
                metric_data.get('ml_model_executions', 0),
                json.dumps(metric_data.get('retailer_performance', {}))
                )
                
                logger.debug(f"📈 Métricas registradas para {metric_date} {metric_hour}:00")
                
        except Exception as e:
            logger.error(f"❌ Error registrando métricas: {e}")
    
    async def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Obtener resumen de performance 📊"""
        try:
            async with self.get_async_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        SUM(opportunities_detected) as total_opportunities,
                        SUM(opportunities_valid) as total_valid,
                        SUM(total_margin_clp) as total_margin,
                        AVG(avg_roi_percentage) as avg_roi,
                        AVG(cache_hit_rate_l1) as avg_cache_l1,
                        AVG(cache_hit_rate_l2) as avg_cache_l2,
                        AVG(intelligence_accuracy) as avg_intelligence,
                        AVG(prediction_accuracy) as avg_prediction,
                        AVG(avg_processing_time_ms) as avg_processing_time
                    FROM arbitrage_metrics_v5 
                    WHERE metric_date >= CURRENT_DATE - INTERVAL '%s days'
                """, days)
                
                if row:
                    summary = dict(row)
                    summary['period_days'] = days
                    summary['success_rate'] = (summary['total_valid'] / summary['total_opportunities'] 
                                             if summary['total_opportunities'] > 0 else 0)
                    return summary
                else:
                    return {'period_days': days, 'total_opportunities': 0}
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen performance: {e}")
            return {'error': str(e)}
    
    # === UTILIDADES ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud de la base de datos 🏥"""
        health = {
            'status': 'unknown',
            'connection_attempts': self.connection_attempts,
            'successful_connections': self.successful_connections,
            'query_count': self.query_count,
            'error_count': self.error_count,
            'schema_initialized': self._schema_initialized,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            async with self.get_async_connection() as conn:
                # Test simple query
                result = await conn.fetchval('SELECT 1')
                
                if result == 1:
                    health['status'] = 'healthy'
                    
                    # Verificar tablas principales
                    tables_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name LIKE 'arbitrage_%_v5'
                    """)
                    
                    health['v5_tables_count'] = tables_count
                    
                    # Contar registros recientes
                    opportunities_today = await conn.fetchval("""
                        SELECT COUNT(*) FROM arbitrage_opportunities_v5 
                        WHERE DATE(created_at) = CURRENT_DATE
                    """)
                    
                    health['opportunities_today'] = opportunities_today
                    
                else:
                    health['status'] = 'unhealthy'
                    
        except Exception as e:
            health['status'] = 'error'
            health['error'] = str(e)
            logger.error(f"❌ Health check falló: {e}")
        
        return health
    
    async def close(self):
        """Cerrar conexiones y liberar recursos 🔚"""
        try:
            if self._async_pool:
                await self._async_pool.close()
                logger.info("🔚 Pool async cerrado correctamente")
            
            # Limpiar cache
            self._query_cache.clear()
            
            logger.info(f"📊 Estadísticas finales - Queries: {self.query_count}, Errores: {self.error_count}")
            
        except Exception as e:
            logger.error(f"❌ Error cerrando database manager: {e}")

# Instancia global para uso singleton
_db_manager_instance = None

def get_db_manager(config: Optional[ArbitrageConfigV5] = None) -> DatabaseManagerV5:
    """Obtener instancia singleton del database manager 🎯"""
    global _db_manager_instance
    
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManagerV5(config)
    
    return _db_manager_instance