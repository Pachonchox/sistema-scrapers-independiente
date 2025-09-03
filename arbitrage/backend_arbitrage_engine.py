# -*- coding: utf-8 -*-
"""
🤖 SISTEMA DE ARBITRAJE BACKEND INDEPENDIENTE
===========================================

Motor de arbitraje que funciona independientemente del flujo principal de scraping.
Analiza productos existentes en la base de datos para detectar oportunidades de arbitraje.

Características:
- ✅ Independiente del scraping principal
- ✅ Utiliza ML existente para matching
- ✅ Detección automática de oportunidades
- ✅ Sistema de alertas configurable
- ✅ Persistencia en PostgreSQL
- ✅ Actualizaciones periódicas
"""

import sys
import os
import json
import time
import logging
import schedule
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 no disponible. Instalar con: pip install psycopg2-binary")
    sys.exit(1)

from ml_integration_sync import ArbitrageMLIntegration

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage/arbitrage_engine.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageConfig:
    """Configuración del motor de arbitraje"""
    min_margin_clp: float = 10000.0
    min_percentage: float = 20.0
    min_similarity_score: float = 0.75
    max_price_ratio: float = 3.0
    update_frequency_minutes: int = 60
    enable_auto_alerts: bool = True
    max_opportunities_per_run: int = 50
    retailers_to_compare: List[str] = None
    
    def __post_init__(self):
        if self.retailers_to_compare is None:
            self.retailers_to_compare = ['falabella', 'ripley', 'paris']

class BackendArbitrageEngine:
    """
    🚀 MOTOR DE ARBITRAJE BACKEND INDEPENDIENTE
    
    Motor principal que:
    1. Se conecta directamente a PostgreSQL
    2. Utiliza el ML existente para matching
    3. Detecta oportunidades de arbitraje
    4. Guarda resultados en tablas específicas
    5. Funciona independiente del scraping
    """
    
    def __init__(self, db_params: Dict[str, Any], config: ArbitrageConfig = None):
        self.db_params = db_params
        self.config = config or ArbitrageConfig()
        self.ml_integration = ArbitrageMLIntegration(db_params)
        self.is_running = False
        self.last_run = None
        self.stats = {
            'total_runs': 0,
            'total_opportunities_found': 0,
            'total_matches_created': 0,
            'last_run_duration': 0
        }
        
        logger.info(f"🚀 Motor de arbitraje inicializado")
        logger.info(f"📊 Configuración: {self.config}")
    
    def start_engine(self):
        """Inicia el motor de arbitraje en modo continuo"""
        logger.info("🟢 INICIANDO MOTOR DE ARBITRAJE BACKEND")
        logger.info("=" * 50)
        
        self.is_running = True
        
        # Configurar scheduling
        schedule.every(self.config.update_frequency_minutes).minutes.do(self.run_arbitrage_cycle)
        
        # Ejecutar inmediatamente
        logger.info("⚡ Ejecutando ciclo inicial...")
        self.run_arbitrage_cycle()
        
        # Loop principal
        logger.info(f"🔄 Programado cada {self.config.update_frequency_minutes} minutos")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo motor de arbitraje...")
            self.stop_engine()
    
    def stop_engine(self):
        """Detiene el motor de arbitraje"""
        self.is_running = False
        self.ml_integration.disconnect()
        logger.info("🔴 Motor de arbitraje detenido")
    
    def run_arbitrage_cycle(self):
        """Ejecuta un ciclo completo de análisis de arbitraje"""
        start_time = time.time()
        logger.info(f"🔄 INICIANDO CICLO DE ARBITRAJE #{self.stats['total_runs'] + 1}")
        
        try:
            # Conectar ML integration
            self.ml_integration.connect()
            
            # Fase 1: Encontrar matches de productos
            logger.info("🔍 Fase 1: Buscando matches de productos con ML...")
            matches = self.ml_integration.find_product_matches(
                limit=200,
                min_similarity=self.config.min_similarity_score
            )
            
            if not matches:
                logger.warning("⚠️ No se encontraron matches de productos")
                return
            
            logger.info(f"✅ Encontrados {len(matches)} matches de productos")
            
            # Fase 2: Guardar matches en BD
            logger.info("💾 Fase 2: Guardando matches en base de datos...")
            saved_matches = self.ml_integration.save_matches_to_db(matches)
            logger.info(f"✅ Guardados {saved_matches} matches")
            
            # Fase 3: Detectar oportunidades de arbitraje
            logger.info("🎯 Fase 3: Detectando oportunidades de arbitraje...")
            opportunities = self.ml_integration.detect_arbitrage_opportunities()
            
            if not opportunities:
                logger.info("ℹ️ No se encontraron oportunidades de arbitraje")
                return
            
            logger.info(f"💰 Encontradas {len(opportunities)} oportunidades")
            
            # Fase 4: Procesar y guardar oportunidades
            logger.info("💾 Fase 4: Guardando oportunidades...")
            saved_opportunities = self._save_opportunities(opportunities[:self.config.max_opportunities_per_run])
            
            # Fase 5: Generar alertas si están habilitadas
            if self.config.enable_auto_alerts:
                logger.info("🔔 Fase 5: Generando alertas...")
                self._generate_alerts(opportunities[:5])  # Top 5
            
            # Actualizar estadísticas
            duration = time.time() - start_time
            self.stats.update({
                'total_runs': self.stats['total_runs'] + 1,
                'total_opportunities_found': self.stats['total_opportunities_found'] + len(opportunities),
                'total_matches_created': self.stats['total_matches_created'] + saved_matches,
                'last_run_duration': duration
            })
            
            self.last_run = datetime.now()
            
            logger.info(f"✅ CICLO COMPLETADO en {duration:.2f}s")
            logger.info(f"📊 Stats: {self.stats}")
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo de arbitraje: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        finally:
            self.ml_integration.disconnect()
    
    def _save_opportunities(self, opportunities: List[Dict[str, Any]]) -> int:
        """Guarda oportunidades de arbitraje en la base de datos"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            saved_count = 0
            
            for opp in opportunities:
                try:
                    # Buscar códigos internos
                    cursor.execute("""
                        SELECT codigo_interno FROM master_productos 
                        WHERE nombre ILIKE %s AND retailer = %s LIMIT 1
                    """, (f"%{opp['metadata']['nombre_barato'][:30]}%", opp['retailer_compra']))
                    
                    result_barato = cursor.fetchone()
                    if not result_barato:
                        continue
                    
                    cursor.execute("""
                        SELECT codigo_interno FROM master_productos 
                        WHERE nombre ILIKE %s AND retailer = %s LIMIT 1
                    """, (f"%{opp['metadata']['nombre_caro'][:30]}%", opp['retailer_venta']))
                    
                    result_caro = cursor.fetchone()
                    if not result_caro:
                        continue
                    
                    # Insertar oportunidad
                    cursor.execute("""
                        INSERT INTO arbitrage_opportunities 
                        (matching_id, producto_barato_codigo, producto_caro_codigo,
                         retailer_compra, retailer_venta, precio_compra, precio_venta,
                         margen_bruto, diferencia_porcentaje, opportunity_score, risk_level,
                         fecha_deteccion, metadata, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                        ON CONFLICT (matching_id, fecha_deteccion) DO UPDATE SET
                        precio_compra = EXCLUDED.precio_compra,
                        precio_venta = EXCLUDED.precio_venta,
                        margen_bruto = EXCLUDED.margen_bruto,
                        opportunity_score = EXCLUDED.opportunity_score,
                        updated_at = NOW()
                    """, (
                        opp['matching_id'],
                        result_barato[0],
                        result_caro[0], 
                        opp['retailer_compra'],
                        opp['retailer_venta'],
                        int(opp['precio_compra']),
                        int(opp['precio_venta']),
                        int(opp['margen_bruto']),
                        float(opp['diferencia_porcentaje']),
                        float(opp['opportunity_score']),
                        opp['risk_level'],
                        date.today(),
                        json.dumps(opp['metadata']),
                    ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error guardando oportunidad {opp.get('matching_id', 'N/A')}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            logger.error(f"Error guardando oportunidades: {e}")
            return 0
    
    def _generate_alerts(self, top_opportunities: List[Dict[str, Any]]):
        """Genera alertas para las mejores oportunidades"""
        try:
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'opportunities_count': len(top_opportunities),
                'top_opportunities': []
            }
            
            for opp in top_opportunities:
                alert_data['top_opportunities'].append({
                    'producto': opp['metadata']['nombre_barato'][:40],
                    'comprar_en': opp['retailer_compra'],
                    'vender_en': opp['retailer_venta'],
                    'margen': f"${opp['margen_bruto']:,}",
                    'roi': f"{opp['diferencia_porcentaje']:.1f}%",
                    'score': f"{opp['opportunity_score']:.3f}"
                })
            
            # Guardar alerta en archivo
            with open('arbitrage/latest_alerts.json', 'w', encoding='utf-8') as f:
                json.dump(alert_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"🔔 Generadas alertas para {len(top_opportunities)} oportunidades")
            
        except Exception as e:
            logger.error(f"Error generando alertas: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del motor"""
        return {
            'is_running': self.is_running,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'stats': self.stats,
            'config': {
                'min_margin_clp': self.config.min_margin_clp,
                'min_percentage': self.config.min_percentage,
                'update_frequency_minutes': self.config.update_frequency_minutes,
                'retailers': self.config.retailers_to_compare
            }
        }
    
    def run_manual_cycle(self) -> Dict[str, Any]:
        """Ejecuta un ciclo manual para testing"""
        logger.info("🔧 Ejecutando ciclo manual...")
        start_time = time.time()
        
        self.run_arbitrage_cycle()
        
        return {
            'success': True,
            'duration': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Función principal para ejecutar el motor de arbitraje"""
    
    # Configuración de base de datos - Use environment variables or default to Docker port
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434')),  # Updated to match docker-compose.yml
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    # Configuración personalizable
    config = ArbitrageConfig(
        min_margin_clp=15000.0,  # Margen mínimo $15K
        min_percentage=25.0,     # ROI mínimo 25%
        min_similarity_score=0.75,  # Similitud mínima 75%
        update_frequency_minutes=60,  # Cada hora
        enable_auto_alerts=True,
        max_opportunities_per_run=30,
        retailers_to_compare=['falabella', 'ripley', 'paris']
    )
    
    # Crear y ejecutar motor
    engine = BackendArbitrageEngine(db_params, config)
    
    try:
        engine.start_engine()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo motor de arbitraje...")
        engine.stop_engine()

if __name__ == "__main__":
    main()