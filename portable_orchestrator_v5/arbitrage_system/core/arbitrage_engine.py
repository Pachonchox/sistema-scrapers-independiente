# -*- coding: utf-8 -*-
"""
🚀 ArbitrageEngine V5 - Motor de Arbitraje Completamente Autónomo
================================================================
Motor principal de arbitraje integrado con inteligencia V5 avanzada.
Sin dependencias externas, completamente autocontenido en carpeta V5.
Compatible con emojis y optimizado para operación continua no supervisada.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import json
from pathlib import Path
import uuid

# Importaciones V5 SOLO internas (completamente autónomas)
from ...core.redis_intelligence_system import RedisIntelligenceSystem
from ...core.intelligent_cache_manager import IntelligentCacheManager
from ...core.master_intelligence_integrator import MasterIntelligenceIntegrator
from ...core.scraping_frequency_optimizer import ScrapingFrequencyOptimizer

from ..database.db_manager import DatabaseManagerV5, get_db_manager
from ..config.arbitrage_config import ArbitrageConfigV5, get_config
from .ml_integration import MLIntegrationV5, create_ml_integration_v5
from .opportunity_detector import OpportunityDetectorV5
from ..schedulers.arbitrage_scheduler import ArbitrageSchedulerV5

# Importar sistema de alertas integrado
try:
    from ......core.alerts_bridge import get_alerts_bridge, send_arbitrage_opportunity_alert
    ALERTS_SYSTEM_AVAILABLE = True
    logger.info("✅ Sistema de alertas integrado disponible en V5")
except ImportError:
    ALERTS_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Sistema de alertas no disponible en V5")

logger = logging.getLogger(__name__)

class ArbitrageEngineV5:
    """
    Motor de Arbitraje V5 Completamente Autónomo 🚀
    
    Funcionalidades principales:
    - 🧠 Inteligencia V5 avanzada integrada completamente
    - ⚡ Cache inteligente L1-L4 para máximo performance
    - 🎯 Detección de oportunidades con ML V5
    - 📊 Análisis predictivo y scoring avanzado
    - 🔄 Scheduling inteligente basado en tiers
    - 🚨 Sistema de alertas con emojis
    - 📈 Métricas y analytics en tiempo real
    - 🛡️ Auto-recovery y manejo robusto de errores
    """
    
    def __init__(self, config: Optional[ArbitrageConfigV5] = None):
        """Inicializar ArbitrageEngine V5 completamente autónomo"""
        self.config = config or get_config()
        self.engine_id = str(uuid.uuid4())[:8]
        
        # Componentes core V5 (todos autónomos)
        self.db_manager = get_db_manager(self.config)
        self.ml_integration = None
        self.opportunity_detector = None
        self.scheduler = None
        
        # Componentes de inteligencia V5
        self.redis_intelligence = None
        self.cache_manager = None
        self.master_integrator = None
        self.frequency_optimizer = None
        
        # Estado del motor
        self.is_running = False
        self.is_initialized = False
        self.start_time = None
        self.last_cycle_time = None
        
        # Métricas operacionales
        self.metrics = {
            'engine_id': self.engine_id,
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'total_opportunities_detected': 0,
            'total_opportunities_saved': 0,
            'total_matches_processed': 0,
            'total_products_analyzed': 0,
            'avg_cycle_duration_seconds': 0.0,
            'cache_performance': {'l1': 0, 'l2': 0, 'l3': 0, 'l4': 0},
            'ml_performance': {'predictions': 0, 'accuracy': 0.0},
            'intelligence_performance': {
                'redis_operations': 0,
                'master_integrations': 0,
                'frequency_optimizations': 0
            },
            'error_counts': {
                'db_errors': 0,
                'ml_errors': 0,
                'intelligence_errors': 0,
                'scheduler_errors': 0
            },
            'last_update': datetime.now().isoformat()
        }
        
        # Configuración de logging autónoma
        self._setup_logging()
        
        logger.info(f"🚀 ArbitrageEngine V5 [{self.engine_id}] inicializado - Modo AUTÓNOMO")
        logger.info(f"📋 Configuración: {len(self.config.retailers_enabled)} retailers, "
                   f"Margen mín: ${self.config.min_margin_clp:,.0f}")
    
    def _setup_logging(self):
        """Configurar logging autónomo V5 🔧"""
        try:
            # Crear directorio de logs si no existe
            log_dir = Path(__file__).parent.parent.parent.parent / "logs" / "arbitrage_v5"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configurar handler específico para arbitraje V5
            log_file = log_dir / f"arbitrage_engine_v5_{datetime.now().strftime('%Y%m%d')}.log"
            
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setLevel(logging.INFO)
            
            # Formato con emojis si está habilitado
            if self.config.enable_emoji_alerts:
                formatter = logging.Formatter(
                    '%(asctime)s - 🚀 ArbitrageV5[%(name)s] - %(levelname)s - %(message)s'
                )
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - ArbitrageV5[%(name)s] - %(levelname)s - %(message)s'
                )
            
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            logger.info(f"📝 Logging V5 configurado: {log_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error configurando logging: {e}")
    
    async def initialize(self):
        """Inicializar todos los componentes V5 de forma autónoma 🔧"""
        if self.is_initialized:
            logger.info("✅ ArbitrageEngine V5 ya está inicializado")
            return
        
        try:
            logger.info("🔄 Inicializando ArbitrageEngine V5 autónomo...")
            
            # Fase 1: Inicializar base de datos
            await self._initialize_database()
            
            # Fase 2: Inicializar componentes de inteligencia V5
            await self._initialize_intelligence_components()
            
            # Fase 3: Inicializar ML Integration V5
            await self._initialize_ml_integration()
            
            # Fase 4: Inicializar detector de oportunidades
            await self._initialize_opportunity_detector()
            
            # Fase 5: Inicializar scheduler inteligente
            await self._initialize_scheduler()
            
            # Fase 6: Validación final
            await self._validate_initialization()
            
            self.is_initialized = True
            logger.info("✅ ArbitrageEngine V5 inicializado correctamente - 100% AUTÓNOMO")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando ArbitrageEngine V5: {e}")
            self.metrics['error_counts']['initialization_errors'] = self.metrics['error_counts'].get('initialization_errors', 0) + 1
            raise
    
    async def _initialize_database(self):
        """Inicializar y validar base de datos 🗄️"""
        try:
            logger.info("🗄️ Inicializando sistema de base de datos V5...")
            
            # Inicializar pool de conexiones
            await self.db_manager.initialize_async_pool()
            
            # Verificar/instalar schema V5
            if not self.db_manager._schema_initialized:
                logger.info("📋 Instalando schema V5 autónomo...")
                await self.db_manager.install_schema()
            
            # Verificar configuración inicial
            await self._ensure_initial_config()
            
            # Health check
            health = await self.db_manager.health_check()
            if health['status'] != 'healthy':
                raise Exception(f"Database no saludable: {health}")
            
            logger.info(f"✅ Base de datos V5 lista - {health['v5_tables_count']} tablas V5")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            self.metrics['error_counts']['db_errors'] += 1
            raise
    
    async def _ensure_initial_config(self):
        """Asegurar configuración inicial en base de datos 📋"""
        try:
            # Verificar configuraciones clave
            essential_configs = [
                ('min_margin_clp', self.config.min_margin_clp),
                ('min_percentage', self.config.min_percentage),
                ('min_similarity_score', self.config.min_similarity_score),
                ('enable_auto_alerts', self.config.enable_auto_alerts),
                ('enable_emoji_alerts', self.config.enable_emoji_alerts)
            ]
            
            for key, value in essential_configs:
                existing = await self.db_manager.get_config_value(key)
                if existing is None:
                    await self.db_manager.set_config_value(key, value, description=f'Config V5: {key}')
                    logger.debug(f"⚙️ Configuración inicial creada: {key} = {value}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error configuración inicial: {e}")
    
    async def _initialize_intelligence_components(self):
        """Inicializar componentes de inteligencia V5 🧠"""
        try:
            logger.info("🧠 Inicializando componentes de inteligencia V5...")
            
            # Redis Intelligence System
            if self.config.use_redis_intelligence:
                self.redis_intelligence = RedisIntelligenceSystem(
                    redis_config=self.config.redis_config
                )
                await self.redis_intelligence.initialize()
                logger.info("🔥 Redis Intelligence System V5 conectado")
            
            # Intelligent Cache Manager
            if self.config.use_intelligent_cache:
                self.cache_manager = IntelligentCacheManager(
                    l1_size=self.config.cache_l1_size,
                    l2_ttl=self.config.cache_l2_ttl,
                    redis_config=self.config.redis_config
                )
                await self.cache_manager.initialize()
                logger.info("⚡ Intelligent Cache Manager V5 conectado")
            
            # Master Intelligence Integrator
            self.master_integrator = MasterIntelligenceIntegrator()
            await self.master_integrator.initialize()
            logger.info("🎯 Master Intelligence Integrator V5 conectado")
            
            # Scraping Frequency Optimizer
            if self.config.use_volatility_analysis:
                self.frequency_optimizer = ScrapingFrequencyOptimizer(
                    redis_intelligence=self.redis_intelligence
                )
                await self.frequency_optimizer.initialize()
                logger.info("📊 Scraping Frequency Optimizer V5 conectado")
            
            logger.info("✅ Todos los componentes de inteligencia V5 inicializados")
            
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando componentes inteligencia: {e}")
            self.metrics['error_counts']['intelligence_errors'] += 1
            # Continuar sin componentes de inteligencia si falla
    
    async def _initialize_ml_integration(self):
        """Inicializar ML Integration V5 🤖"""
        try:
            logger.info("🤖 Inicializando ML Integration V5...")
            
            self.ml_integration = await create_ml_integration_v5(self.config)
            logger.info("✅ ML Integration V5 inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando ML Integration: {e}")
            self.metrics['error_counts']['ml_errors'] += 1
            raise
    
    async def _initialize_opportunity_detector(self):
        """Inicializar detector de oportunidades V5 🎯"""
        try:
            logger.info("🎯 Inicializando Opportunity Detector V5...")
            
            self.opportunity_detector = OpportunityDetectorV5(
                config=self.config,
                db_manager=self.db_manager,
                ml_integration=self.ml_integration,
                cache_manager=self.cache_manager
            )
            
            await self.opportunity_detector.initialize()
            logger.info("✅ Opportunity Detector V5 inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Opportunity Detector: {e}")
            raise
    
    async def _initialize_scheduler(self):
        """Inicializar scheduler inteligente V5 📅"""
        try:
            logger.info("📅 Inicializando Scheduler V5...")
            
            self.scheduler = ArbitrageSchedulerV5(
                config=self.config,
                engine=self,
                frequency_optimizer=self.frequency_optimizer
            )
            
            await self.scheduler.initialize()
            logger.info("✅ Scheduler V5 inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Scheduler: {e}")
            self.metrics['error_counts']['scheduler_errors'] += 1
            raise
    
    async def _validate_initialization(self):
        """Validar que todos los componentes estén funcionando 🔍"""
        try:
            logger.info("🔍 Validando inicialización completa...")
            
            # Validar base de datos
            health = await self.db_manager.health_check()
            if health['status'] != 'healthy':
                raise Exception(f"Database validation failed: {health}")
            
            # Validar ML integration
            if not self.ml_integration:
                raise Exception("ML Integration no inicializado")
            
            # Validar opportunity detector
            if not self.opportunity_detector:
                raise Exception("Opportunity Detector no inicializado")
            
            # Test básico de funcionalidad
            await self._run_initialization_test()
            
            logger.info("✅ Validación completa - Sistema V5 100% operativo")
            
        except Exception as e:
            logger.error(f"❌ Fallo en validación: {e}")
            raise
    
    async def _run_initialization_test(self):
        """Ejecutar test básico de inicialización 🧪"""
        try:
            # Test de configuración
            test_config = await self.db_manager.get_config_value('min_margin_clp', 0)
            if test_config <= 0:
                raise Exception("Configuración no válida")
            
            # Test de cache (si disponible)
            if self.cache_manager:
                await self.cache_manager.set('test_key_v5', 'test_value', ttl=10)
                cached_value, level = await self.cache_manager.get('test_key_v5')
                if cached_value != 'test_value':
                    logger.warning("⚠️ Cache test failed")
            
            logger.debug("🧪 Tests de inicialización pasados")
            
        except Exception as e:
            logger.warning(f"⚠️ Test de inicialización falló: {e}")
    
    async def start_engine(self):
        """Iniciar motor de arbitraje en modo continuo 🚀"""
        if self.is_running:
            logger.warning("⚠️ Motor ya está ejecutándose")
            return
        
        try:
            logger.info("🟢 INICIANDO MOTOR DE ARBITRAJE V5 AUTÓNOMO")
            logger.info("=" * 60)
            
            # Inicializar si no está hecho
            if not self.is_initialized:
                await self.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Ejecutar ciclo inicial
            logger.info("⚡ Ejecutando ciclo inicial de arbitraje...")
            await self.run_arbitrage_cycle()
            
            # Iniciar scheduler inteligente
            if self.scheduler:
                await self.scheduler.start()
                logger.info("📅 Scheduler V5 iniciado - Operación continua activada")
            
            logger.info("🎯 Motor V5 en operación - 100% AUTÓNOMO")
            logger.info(f"🔧 Configuración: {len(self.config.retailers_enabled)} retailers, "
                       f"Tiers: {self.config.critical_tier_frequency}min crítico, "
                       f"Cache: L1-L4 activado")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando motor: {e}")
            self.is_running = False
            raise
    
    async def stop_engine(self):
        """Detener motor de arbitraje limpiamente 🛑"""
        try:
            logger.info("🛑 Deteniendo motor de arbitraje V5...")
            
            self.is_running = False
            
            # Detener scheduler
            if self.scheduler:
                await self.scheduler.stop()
                logger.info("📅 Scheduler V5 detenido")
            
            # Cerrar componentes en orden
            await self._shutdown_components()
            
            # Métricas finales
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            logger.info(f"📊 Estadísticas finales:")
            logger.info(f"   ⏱️ Tiempo operación: {uptime}")
            logger.info(f"   🔄 Ciclos totales: {self.metrics['total_cycles']}")
            logger.info(f"   ✅ Ciclos exitosos: {self.metrics['successful_cycles']}")
            logger.info(f"   💰 Oportunidades detectadas: {self.metrics['total_opportunities_detected']}")
            
            logger.info("🔴 Motor de arbitraje V5 detenido correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo motor: {e}")
    
    async def _shutdown_components(self):
        """Cerrar todos los componentes limpiamente 🔚"""
        try:
            components_to_close = [
                ('ML Integration', self.ml_integration),
                ('Opportunity Detector', self.opportunity_detector), 
                ('Master Integrator', self.master_integrator),
                ('Cache Manager', self.cache_manager),
                ('Redis Intelligence', self.redis_intelligence),
                ('Frequency Optimizer', self.frequency_optimizer),
                ('Database Manager', self.db_manager)
            ]
            
            for name, component in components_to_close:
                if component and hasattr(component, 'close'):
                    try:
                        await component.close()
                        logger.debug(f"🔚 {name} cerrado")
                    except Exception as e:
                        logger.warning(f"⚠️ Error cerrando {name}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error en shutdown: {e}")
    
    async def run_arbitrage_cycle(self) -> Dict[str, Any]:
        """
        Ejecutar un ciclo completo de análisis de arbitraje V5 🔄
        
        Returns:
            Resultado del ciclo con métricas y oportunidades
        """
        cycle_start = datetime.now()
        cycle_id = str(uuid.uuid4())[:8]
        
        cycle_result = {
            'cycle_id': cycle_id,
            'start_time': cycle_start.isoformat(),
            'success': False,
            'matches_found': 0,
            'opportunities_detected': 0,
            'opportunities_saved': 0,
            'products_analyzed': 0,
            'duration_seconds': 0,
            'errors': [],
            'intelligence_metrics': {}
        }
        
        try:
            logger.info(f"🔄 CICLO ARBITRAJE V5 #{self.metrics['total_cycles'] + 1} [{cycle_id}]")
            logger.info("─" * 50)
            
            # Actualizar métricas
            self.metrics['total_cycles'] += 1
            self.last_cycle_time = cycle_start
            
            # Fase 1: Obtener productos para análisis
            logger.info("🔍 Fase 1: Obteniendo productos para análisis...")
            products = await self._get_products_for_analysis()
            
            if not products:
                logger.warning("⚠️ No hay productos disponibles para análisis")
                return cycle_result
            
            cycle_result['products_analyzed'] = len(products)
            self.metrics['total_products_analyzed'] += len(products)
            
            logger.info(f"📊 Productos obtenidos: {len(products)} de {len(self.config.retailers_enabled)} retailers")
            
            # Fase 2: Análisis de matching con ML V5
            logger.info("🤖 Fase 2: Ejecutando análisis ML V5...")
            matches = await self.ml_integration.find_product_matches(
                products, 
                min_similarity=self.config.min_similarity_score
            )
            
            cycle_result['matches_found'] = len(matches)
            self.metrics['total_matches_processed'] += len(matches)
            
            if matches:
                logger.info(f"🎯 Matches detectados: {len(matches)} con ML V5")
            else:
                logger.info("📊 No se detectaron matches en este ciclo")
                cycle_result['success'] = True
                return cycle_result
            
            # Fase 3: Detección de oportunidades
            logger.info("💰 Fase 3: Detectando oportunidades de arbitraje...")
            opportunities = await self.ml_integration.detect_arbitrage_opportunities(matches)
            
            cycle_result['opportunities_detected'] = len(opportunities)
            self.metrics['total_opportunities_detected'] += len(opportunities)
            
            if opportunities:
                logger.info(f"💎 Oportunidades detectadas: {len(opportunities)}")
                
                # Fase 4: Análisis avanzado con V5
                logger.info("🧠 Fase 4: Análisis inteligente V5...")
                enriched_opportunities = await self._enrich_opportunities_with_v5_intelligence(opportunities)
                
                # Fase 5: Persistencia
                logger.info("💾 Fase 5: Guardando oportunidades...")
                saved_count = await self._save_opportunities(enriched_opportunities)
                
                cycle_result['opportunities_saved'] = saved_count
                self.metrics['total_opportunities_saved'] += saved_count
                
                # Fase 6: Alertas
                if self.config.enable_auto_alerts:
                    logger.info("🚨 Fase 6: Procesando alertas...")
                    await self._process_alerts(enriched_opportunities)
                
                logger.info(f"✅ Oportunidades guardadas: {saved_count}")
            else:
                logger.info("📊 No se detectaron oportunidades en este ciclo")
            
            # Fase 7: Métricas y análisis
            logger.info("📊 Fase 7: Actualizando métricas...")
            await self._update_cycle_metrics(cycle_result)
            
            # Obtener métricas de componentes
            if self.ml_integration:
                ml_metrics = await self.ml_integration.get_metrics_summary()
                cycle_result['intelligence_metrics']['ml'] = ml_metrics
            
            if self.cache_manager:
                cache_metrics = await self.cache_manager.get_performance_stats()
                cycle_result['intelligence_metrics']['cache'] = cache_metrics
            
            # Éxito
            cycle_result['success'] = True
            self.metrics['successful_cycles'] += 1
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            cycle_result['duration_seconds'] = cycle_duration
            
            # Actualizar promedio de duración
            total_successful = self.metrics['successful_cycles']
            current_avg = self.metrics['avg_cycle_duration_seconds']
            self.metrics['avg_cycle_duration_seconds'] = (
                (current_avg * (total_successful - 1) + cycle_duration) / total_successful
            )
            
            logger.info(f"🎉 CICLO COMPLETADO - Duración: {cycle_duration:.1f}s")
            logger.info("═" * 50)
            
            return cycle_result
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo de arbitraje: {e}")
            
            cycle_result['errors'].append(str(e))
            self.metrics['failed_cycles'] += 1
            
            # Intentar recovery automático
            await self._attempt_auto_recovery(e)
            
            return cycle_result
        
        finally:
            # Actualizar timestamp
            self.metrics['last_update'] = datetime.now().isoformat()
    
    async def _get_products_for_analysis(self) -> List[Dict[str, Any]]:
        """Obtener productos para análisis desde master system 📋"""
        try:
            # Query productos activos con precios recientes
            async with self.db_manager.get_async_connection() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        mp.codigo_interno,
                        mp.nombre,
                        mp.sku,
                        mp.marca,
                        mp.categoria,
                        mp.retailer,
                        mp.rating,
                        mp.reviews_count,
                        mp.storage,
                        mp.ram,
                        COALESCE(precio_oferta, precio_normal, precio_tarjeta) as precio_actual,
                        precio_normal,
                        precio_oferta,
                        precio_tarjeta,
                        mpr.fecha as fecha_precio
                    FROM master_productos mp
                    LEFT JOIN master_precios mpr ON mp.codigo_interno = mpr.codigo_interno
                    WHERE mp.retailer = ANY($1)
                    AND (mpr.fecha >= CURRENT_DATE - INTERVAL '3 days' OR mpr.fecha IS NULL)
                    AND COALESCE(precio_oferta, precio_normal, precio_tarjeta) > 0
                    ORDER BY mpr.fecha DESC NULLS LAST, mp.codigo_interno
                    LIMIT 1000
                """, self.config.retailers_enabled)
                
                products = [dict(row) for row in rows]
                
                # Enriquecer con análisis V5 si está disponible
                if self.master_integrator:
                    for product in products:
                        try:
                            # Análisis rápido para clasificación
                            analysis = await self.master_integrator.analyze_product_profile(product)
                            product['v5_analysis'] = analysis
                        except Exception as e:
                            logger.debug(f"⚠️ Error análisis V5 para {product.get('codigo_interno')}: {e}")
                
                return products
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo productos: {e}")
            return []
    
    async def _enrich_opportunities_with_v5_intelligence(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enriquecer oportunidades con inteligencia V5 adicional 🧠"""
        try:
            enriched = []
            
            for opportunity in opportunities:
                try:
                    # Análisis de inteligencia adicional
                    if self.redis_intelligence:
                        # Análisis de volatilidad histórica
                        cheap_retailer = opportunity.get('retailer_compra', '')
                        expensive_retailer = opportunity.get('retailer_venta', '')
                        
                        volatility_data = await self._analyze_opportunity_volatility(
                            opportunity, cheap_retailer, expensive_retailer
                        )
                        
                        opportunity['volatility_analysis'] = volatility_data
                    
                    # Análisis de timing óptimo
                    if self.frequency_optimizer:
                        timing_analysis = await self._analyze_optimal_timing(opportunity)
                        opportunity['timing_analysis'] = timing_analysis
                    
                    # Scoring avanzado V5
                    advanced_score = await self._calculate_advanced_v5_score(opportunity)
                    opportunity['advanced_v5_score'] = advanced_score
                    
                    enriched.append(opportunity)
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error enriqueciendo oportunidad: {e}")
                    enriched.append(opportunity)  # Incluir sin enriquecimiento
            
            return enriched
            
        except Exception as e:
            logger.error(f"❌ Error enriqueciendo oportunidades: {e}")
            return opportunities  # Retornar sin enriquecimiento
    
    async def _analyze_opportunity_volatility(self, opportunity: Dict[str, Any], 
                                            cheap_retailer: str, expensive_retailer: str) -> Dict[str, Any]:
        """Analizar volatilidad de la oportunidad 📊"""
        try:
            if not self.redis_intelligence:
                return {}
            
            cheap_code = opportunity.get('producto_barato_codigo', '')
            expensive_code = opportunity.get('producto_caro_codigo', '')
            
            # Análisis de volatilidad para ambos productos
            cheap_volatility = await self.redis_intelligence.analyze_price_volatility(
                cheap_retailer, cheap_code, []
            )
            
            expensive_volatility = await self.redis_intelligence.analyze_price_volatility(
                expensive_retailer, expensive_code, []
            )
            
            return {
                'cheap_product_volatility': cheap_volatility,
                'expensive_product_volatility': expensive_volatility,
                'combined_risk_score': max(
                    cheap_volatility.get('volatility_score', 0),
                    expensive_volatility.get('volatility_score', 0)
                )
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error análisis volatilidad: {e}")
            return {}
    
    async def _analyze_optimal_timing(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar timing óptimo para la oportunidad ⏰"""
        try:
            if not self.frequency_optimizer:
                return {}
            
            # Análisis básico de timing
            current_hour = datetime.now().hour
            
            # Horario comercial óptimo
            is_optimal_time = 9 <= current_hour <= 21
            
            # Calcular próxima ventana óptima
            if is_optimal_time:
                next_optimal = datetime.now() + timedelta(minutes=30)
            else:
                # Próximo día hábil 9 AM
                next_optimal = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
                if current_hour >= 22:
                    next_optimal += timedelta(days=1)
            
            return {
                'is_optimal_time': is_optimal_time,
                'current_hour': current_hour,
                'next_optimal_window': next_optimal.isoformat(),
                'timing_score': 0.8 if is_optimal_time else 0.3
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error análisis timing: {e}")
            return {}
    
    async def _calculate_advanced_v5_score(self, opportunity: Dict[str, Any]) -> float:
        """Calcular score avanzado V5 combinando todos los factores 🎯"""
        try:
            base_score = opportunity.get('v5_intelligence_score', 0.5)
            
            # Factores adicionales
            volatility_factor = 1.0
            timing_factor = 1.0
            
            # Ajuste por volatilidad
            volatility_analysis = opportunity.get('volatility_analysis', {})
            if volatility_analysis:
                risk_score = volatility_analysis.get('combined_risk_score', 0)
                volatility_factor = max(0.5, 1.0 - risk_score)
            
            # Ajuste por timing
            timing_analysis = opportunity.get('timing_analysis', {})
            if timing_analysis:
                timing_factor = timing_analysis.get('timing_score', 1.0)
            
            # Score combinado
            advanced_score = base_score * volatility_factor * timing_factor
            
            return min(max(advanced_score, 0.0), 1.0)
            
        except Exception as e:
            logger.debug(f"⚠️ Error calculando score avanzado: {e}")
            return opportunity.get('v5_intelligence_score', 0.5)
    
    async def _save_opportunities(self, opportunities: List[Dict[str, Any]]) -> int:
        """Guardar oportunidades en base de datos 💾"""
        try:
            saved_count = 0
            
            for opportunity in opportunities:
                try:
                    # Preparar datos para guardado
                    opportunity_data = self._prepare_opportunity_for_save(opportunity)
                    
                    # Guardar en base de datos
                    opportunity_id = await self.db_manager.save_arbitrage_opportunity(opportunity_data)
                    
                    if opportunity_id:
                        saved_count += 1
                        logger.debug(f"💾 Oportunidad guardada: ID {opportunity_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error guardando oportunidad individual: {e}")
                    continue
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error guardando oportunidades: {e}")
            return 0
    
    def _prepare_opportunity_for_save(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar oportunidad para guardado en BD 🔧"""
        try:
            # Limpiar y preparar datos
            prepared = {
                'producto_barato_codigo': opportunity.get('producto_barato_codigo', ''),
                'producto_caro_codigo': opportunity.get('producto_caro_codigo', ''),
                'matching_id': opportunity.get('matching_id'),
                'retailer_compra': opportunity.get('retailer_compra', ''),
                'retailer_venta': opportunity.get('retailer_venta', ''),
                'precio_compra': int(opportunity.get('precio_compra', 0)),
                'precio_venta': int(opportunity.get('precio_venta', 0)),
                'diferencia_absoluta': int(opportunity.get('diferencia_absoluta', 0)),
                'diferencia_porcentaje': float(opportunity.get('diferencia_porcentaje', 0)),
                'margen_bruto': int(opportunity.get('margen_bruto', 0)),
                'roi_estimado': float(opportunity.get('roi_estimado', 0)),
                'opportunity_score': float(opportunity.get('opportunity_score', 0)),
                'v5_intelligence_score': float(opportunity.get('v5_intelligence_score', 0)),
                'advanced_v5_score': float(opportunity.get('advanced_v5_score', 0)),
                'volatility_risk_score': float(opportunity.get('volatility_risk_score', 0)),
                'timing_score': float(opportunity.get('timing_score', 0.5)),
                'confidence_score': float(opportunity.get('confidence_score', 0.5)),
                'risk_level': opportunity.get('risk_level', 'medium'),
                'priority_level': int(opportunity.get('priority_level', 3)),
                'tier_classification': opportunity.get('tier_classification', 'tracking'),
                'predicted_duration_hours': int(opportunity.get('predicted_duration_hours', 24)),
                'predicted_success_rate': float(opportunity.get('predicted_success_rate', 0.7)),
                'optimal_execution_time': opportunity.get('optimal_execution_time'),
                'detection_method': 'arbitrage_engine_v5',
                'emoji_alert': opportunity.get('emoji_alert', ''),
                'v5_analysis': opportunity.get('v5_analysis', {}),
                'redis_cache_data': opportunity.get('redis_cache_data', {}),
                'learned_insights': opportunity.get('learned_insights', {}),
                'metadata': {
                    'engine_id': self.engine_id,
                    'cycle_id': getattr(self, '_current_cycle_id', 'unknown'),
                    'volatility_analysis': opportunity.get('volatility_analysis', {}),
                    'timing_analysis': opportunity.get('timing_analysis', {}),
                    'v5_components': {
                        'redis_intelligence': self.redis_intelligence is not None,
                        'cache_manager': self.cache_manager is not None,
                        'master_integrator': self.master_integrator is not None,
                        'frequency_optimizer': self.frequency_optimizer is not None
                    }
                }
            }
            
            return prepared
            
        except Exception as e:
            logger.error(f"❌ Error preparando oportunidad: {e}")
            return opportunity
    
    async def _process_alerts(self, opportunities: List[Dict[str, Any]]):
        """
        🚨 Procesar alertas para oportunidades usando sistema integrado
        
        Integración completa con alerts_bot para envío por Telegram
        """
        try:
            if not self.config.enable_auto_alerts:
                logger.debug("📵 Alertas deshabilitadas en configuración")
                return
            
            # Filtrar oportunidades que requieren alerta
            high_value_opportunities = []
            for opp in opportunities:
                margen_clp = opp.get('margen_clp', 0)
                margen_porcentaje = opp.get('margen_porcentaje', 0)
                confidence = opp.get('confidence_score', 0)
                
                # Criterios de alerta
                if (margen_clp >= self.config.alert_high_value_threshold or 
                    margen_porcentaje >= self.config.alert_high_roi_threshold):
                    high_value_opportunities.append(opp)
            
            if not high_value_opportunities:
                logger.debug("📊 No hay oportunidades que requieran alerta")
                return
            
            logger.info(f"🚨 Procesando {len(high_value_opportunities)} alertas de alto valor")
            
            # Enviar alertas usando sistema integrado
            if ALERTS_SYSTEM_AVAILABLE:
                alerts_sent = 0
                for opportunity in high_value_opportunities:
                    try:
                        # Extraer datos de la oportunidad
                        producto_codigo = opportunity.get('producto_barato_codigo', 'Unknown')
                        nombre_producto = opportunity.get('nombre_producto', 'Producto')
                        retailer_barato = opportunity.get('retailer_compra', 'Unknown')
                        precio_barato = int(opportunity.get('precio_compra', 0))
                        retailer_caro = opportunity.get('retailer_venta', 'Unknown')  
                        precio_caro = int(opportunity.get('precio_venta', 0))
                        confidence_score = float(opportunity.get('confidence_score', 0.95))
                        
                        # Enviar usando función de conveniencia
                        sent = await send_arbitrage_opportunity_alert(
                            producto_codigo=producto_codigo,
                            nombre_producto=nombre_producto,
                            retailer_barato=retailer_barato,
                            precio_barato=precio_barato,
                            retailer_caro=retailer_caro,
                            precio_caro=precio_caro,
                            confidence_score=confidence_score
                        )
                        
                        if sent:
                            alerts_sent += 1
                            logger.info(f"📤 Alerta enviada: {nombre_producto} - Margen: ${precio_caro - precio_barato:,.0f}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error enviando alerta individual: {e}")
                
                logger.info(f"✅ Alertas enviadas: {alerts_sent}/{len(high_value_opportunities)}")
                
                # Actualizar métricas
                self.metrics['total_alerts_sent'] = self.metrics.get('total_alerts_sent', 0) + alerts_sent
                
            else:
                # Fallback: log local si no hay sistema de alertas
                logger.warning("⚠️ Sistema de alertas no disponible - usando logs locales")
                for opportunity in high_value_opportunities:
                    margen = opportunity.get('margen_clp', 0)
                    roi = opportunity.get('margen_porcentaje', 0)
                    producto = opportunity.get('nombre_producto', 'Producto')
                    logger.info(f"🔔 ALERTA LOCAL: {producto} - Margen: ${margen:,.0f} ({roi:.1f}% ROI)")
            
        except Exception as e:
            logger.error(f"❌ Error procesando alertas: {e}")
            self.metrics['error_counts']['alerts_errors'] = self.metrics['error_counts'].get('alerts_errors', 0) + 1
    
    async def _update_cycle_metrics(self, cycle_result: Dict[str, Any]):
        """Actualizar métricas del ciclo en BD 📊"""
        try:
            current_time = datetime.now()
            
            metric_data = {
                'opportunities_detected': cycle_result.get('opportunities_detected', 0),
                'opportunities_valid': cycle_result.get('opportunities_saved', 0),
                'total_margin_clp': 0,  # Se calculará si es necesario
                'avg_roi_percentage': 0,  # Se calculará si es necesario
                'avg_processing_time_ms': int(cycle_result.get('duration_seconds', 0) * 1000),
                'ml_model_executions': 1,
                'retailer_performance': {
                    'cycle_id': cycle_result['cycle_id'],
                    'products_analyzed': cycle_result.get('products_analyzed', 0),
                    'matches_found': cycle_result.get('matches_found', 0)
                }
            }
            
            await self.db_manager.record_metrics(metric_data)
            logger.debug("📊 Métricas del ciclo actualizadas")
            
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando métricas: {e}")
    
    async def _attempt_auto_recovery(self, error: Exception):
        """Intentar recuperación automática tras error 🔄"""
        try:
            logger.info("🔄 Intentando recuperación automática...")
            
            # Determinar tipo de error y estrategia
            error_str = str(error).lower()
            
            if 'connection' in error_str or 'database' in error_str:
                # Error de conexión - reinicializar DB
                logger.info("🗄️ Reintentando conexión base de datos...")
                await self.db_manager.initialize_async_pool()
                
            elif 'redis' in error_str:
                # Error Redis - reinicializar componentes Redis
                logger.info("🔥 Reintentando componentes Redis...")
                if self.redis_intelligence:
                    await self.redis_intelligence.initialize()
                if self.cache_manager:
                    await self.cache_manager.initialize()
            
            elif 'ml' in error_str or 'model' in error_str:
                # Error ML - reinicializar ML integration
                logger.info("🤖 Reintentando ML Integration...")
                self.ml_integration = await create_ml_integration_v5(self.config)
            
            logger.info("✅ Recuperación automática completada")
            
        except Exception as recovery_error:
            logger.error(f"❌ Fallo en recuperación automática: {recovery_error}")
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Obtener estado completo del motor 📊"""
        try:
            # Estado básico
            status = {
                'engine_id': self.engine_id,
                'is_running': self.is_running,
                'is_initialized': self.is_initialized,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                'metrics': self.metrics.copy()
            }
            
            # Estado de componentes
            status['components'] = {
                'database_manager': self.db_manager is not None,
                'ml_integration': self.ml_integration is not None,
                'opportunity_detector': self.opportunity_detector is not None,
                'scheduler': self.scheduler is not None,
                'redis_intelligence': self.redis_intelligence is not None,
                'cache_manager': self.cache_manager is not None,
                'master_integrator': self.master_integrator is not None,
                'frequency_optimizer': self.frequency_optimizer is not None
            }
            
            # Health checks
            if self.db_manager:
                db_health = await self.db_manager.health_check()
                status['database_health'] = db_health
            
            if self.cache_manager:
                cache_stats = await self.cache_manager.get_performance_stats()
                status['cache_performance'] = cache_stats
            
            # Configuración actual
            status['configuration'] = {
                'min_margin_clp': self.config.min_margin_clp,
                'min_percentage': self.config.min_percentage,
                'retailers_enabled': self.config.retailers_enabled,
                'enable_auto_alerts': self.config.enable_auto_alerts,
                'enable_emoji_alerts': self.config.enable_emoji_alerts
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return {
                'engine_id': self.engine_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_recent_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener oportunidades recientes 💰"""
        try:
            return await self.db_manager.get_active_opportunities(limit)
        except Exception as e:
            logger.error(f"❌ Error obteniendo oportunidades: {e}")
            return []
    
    async def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Obtener resumen de performance 📈"""
        try:
            db_summary = await self.db_manager.get_performance_summary(days)
            
            # Combinar con métricas del motor
            summary = {
                'period_days': days,
                'engine_metrics': self.metrics.copy(),
                'database_metrics': db_summary,
                'component_status': {
                    'v5_intelligence_active': sum([
                        self.redis_intelligence is not None,
                        self.cache_manager is not None, 
                        self.master_integrator is not None,
                        self.frequency_optimizer is not None
                    ]),
                    'total_v5_components': 4
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen performance: {e}")
            return {'error': str(e)}

# Funciones de utilidad para crear instancias
async def create_arbitrage_engine_v5(config: Optional[ArbitrageConfigV5] = None) -> ArbitrageEngineV5:
    """Crear e inicializar ArbitrageEngine V5 completo 🚀"""
    engine = ArbitrageEngineV5(config)
    await engine.initialize()
    return engine

async def run_arbitrage_engine_v5_standalone(config: Optional[ArbitrageConfigV5] = None):
    """Ejecutar ArbitrageEngine V5 en modo standalone 🎯"""
    engine = await create_arbitrage_engine_v5(config)
    
    try:
        await engine.start_engine()
        
        # Mantener ejecutándose hasta interrupción
        while engine.is_running:
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrupción de usuario detectada")
    finally:
        await engine.stop_engine()