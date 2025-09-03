import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Integration para Sistema de Arbitraje - Versión Síncrona
Usa psycopg2 que ya está instalado en el sistema
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import psycopg2
import psycopg2.extras
import json
from datetime import datetime, timedelta

# Agregar paths necesarios
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ArbitrageMLIntegration:
    """
    Integra el MatchScoringModel existente con el sistema de arbitraje
    Versión síncrona usando psycopg2
    """
    
    def __init__(self, db_connection_params: Dict[str, Any]):
        self.db_params = db_connection_params
        self.db_conn = None
        self.match_scorer = None
        
        # Parámetros de arbitraje
        self.config = {
            'min_margin_clp': 5000,
            'min_percentage': 15.0,
            'min_similarity_score': 0.85,
            'max_price_ratio': 5.0
        }
        
        self._initialize_ml_scorer()
    
    def _initialize_ml_scorer(self):
        """Inicializa el MatchScoringModel usando adapter V5 avanzado"""
        try:
            # Usar adapter que conecta con sistema V5 avanzado
            from ..utils.ml_adapters import MatchScoringAdapter as MatchScoringModel
            self.match_scorer = MatchScoringModel(
                threshold=self.config['min_similarity_score'],
                embedder_name="paraphrase-multilingual-mpnet-base-v2"
            )
            logger.info("✅ MatchScoringModel integrado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando MatchScoringModel: {e}")
            self.match_scorer = None
    
    def connect(self):
        """Establece conexión con PostgreSQL"""
        try:
            conn_string = f"host={self.db_params['host']} port={self.db_params['port']} dbname={self.db_params['database']} user={self.db_params['user']} password={self.db_params['password']}"
            self.db_conn = psycopg2.connect(conn_string)
            self.db_conn.autocommit = True
            self._load_config_from_db()
            logger.info("✅ Conexión establecida con PostgreSQL para arbitraje")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        """Cierra conexión con PostgreSQL"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("🔌 Conexión PostgreSQL cerrada")
    
    def _load_config_from_db(self):
        """Carga configuración desde la tabla arbitrage_config"""
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT config_key, config_value, config_type 
                    FROM arbitrage_config 
                    WHERE is_active = TRUE
                """)
                
                for row in cur.fetchall():
                    key = row['config_key']
                    value = row['config_value']
                    value_type = row['config_type']
                    
                    # Convertir según tipo
                    if value_type == 'number':
                        self.config[key] = float(value)
                    elif value_type == 'boolean':
                        self.config[key] = value.lower() == 'true'
                    else:
                        self.config[key] = value
                
                logger.info(f"📊 Configuración cargada: {self.config}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error cargando configuración, usando valores por defecto: {e}")
    
    def find_product_matches(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Encuentra matches de productos usando el ML existente
        """
        logger.info(f"🔍 Buscando matches de productos (límite: {limit})")
        
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Obtener productos candidatos
                cur.execute("""
                    SELECT 
                        p.codigo_interno,
                        p.nombre,
                        p.marca,
                        p.categoria,
                        p.retailer,
                        pr.precio_oferta,
                        pr.precio_normal
                    FROM master_productos p
                    LEFT JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
                    WHERE pr.precio_oferta IS NOT NULL 
                    ORDER BY p.retailer, p.categoria, p.marca
                    LIMIT %s
                """, (limit,))
                
                productos = cur.fetchall()
                
                logger.info(f"📦 Analizando {len(productos)} productos para matching")
                
                matches_found = []
                processed_pairs = set()
                
                # Comparar productos de diferentes retailers
                for i, prod_a in enumerate(productos):
                    for j in range(i+1, len(productos)):
                        prod_b = productos[j]
                        
                        # Solo comparar productos de diferentes retailers
                        if prod_a['retailer'] == prod_b['retailer']:
                            continue
                        
                        # Evitar duplicados
                        pair_key = tuple(sorted([prod_a['codigo_interno'], prod_b['codigo_interno']]))
                        if pair_key in processed_pairs:
                            continue
                        processed_pairs.add(pair_key)
                        
                        # Verificar precios válidos
                        precio_a = prod_a['precio_oferta'] or prod_a['precio_normal']
                        precio_b = prod_b['precio_oferta'] or prod_b['precio_normal']
                        
                        if not precio_a or not precio_b:
                            continue
                        
                        # Evitar comparaciones absurdas
                        precio_ratio = max(precio_a, precio_b) / min(precio_a, precio_b)
                        if precio_ratio > self.config['max_price_ratio']:
                            continue
                        
                        # Calcular similitud ML
                        similarity_score = self._calculate_similarity(dict(prod_a), dict(prod_b))
                        
                        if similarity_score >= self.config['min_similarity_score']:
                            match_data = {
                                'codigo_base': prod_a['codigo_interno'],
                                'codigo_match': prod_b['codigo_interno'],
                                'similarity_score': similarity_score,
                                'match_type': self._classify_match_type(similarity_score),
                                'match_confidence': self._classify_confidence(similarity_score),
                                'match_reason': f"ML Score: {similarity_score:.4f}",
                                'match_features': {
                                    'brand_match': prod_a['marca'].lower() == prod_b['marca'].lower(),
                                    'category_match': prod_a['categoria'] == prod_b['categoria'],
                                    'price_ratio': precio_ratio,
                                    'retailer_a': prod_a['retailer'],
                                    'retailer_b': prod_b['retailer']
                                }
                            }
                            matches_found.append(match_data)
                
                logger.info(f"✅ Encontrados {len(matches_found)} matches potenciales")
                return matches_found
                
        except Exception as e:
            logger.error(f"❌ Error buscando matches: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _calculate_similarity(self, prod_a: Dict, prod_b: Dict) -> float:
        """
        Calcula similitud usando el ML existente
        """
        try:
            if self.match_scorer is None:
                # Fallback básico
                brand_match = prod_a['marca'].lower() == prod_b['marca'].lower()
                category_match = prod_a['categoria'] == prod_b['categoria']
                
                if brand_match and category_match:
                    return 0.9
                elif brand_match:
                    return 0.85  # Misma marca es buen indicador
                elif category_match:
                    return 0.7
                else:
                    return 0.6
            
            # Usar el MatchScoringModel existente
            product_a = {
                'nombre': prod_a['nombre'],
                'marca': prod_a['marca'],
                'categoria': prod_a['categoria'],
                'retailer': prod_a['retailer']
            }
            
            product_b = {
                'nombre': prod_b['nombre'],
                'marca': prod_b['marca'],
                'categoria': prod_b['categoria'],
                'retailer': prod_b['retailer']
            }
            
            # Calcular similitud usando el ML
            is_match, score = self.match_scorer.predict(product_a, product_b)
            return float(score)
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculando similitud ML: {e}")
            # Fallback seguro
            brand_match = prod_a['marca'].lower() == prod_b['marca'].lower()
            category_match = prod_a['categoria'] == prod_b['categoria']
            
            if brand_match and category_match:
                return 0.87
            elif brand_match:
                return 0.85
            else:
                return 0.6
    
    def _classify_match_type(self, similarity_score: float) -> str:
        """Clasifica el tipo de match"""
        if similarity_score >= 0.95:
            return 'exact'
        elif similarity_score >= 0.90:
            return 'similar'
        elif similarity_score >= 0.85:
            return 'variant'
        else:
            return 'category'
    
    def _classify_confidence(self, similarity_score: float) -> str:
        """Clasifica la confianza del match"""
        if similarity_score >= 0.93:
            return 'high'
        elif similarity_score >= 0.87:
            return 'medium'
        else:
            return 'low'
    
    def save_matches_to_db(self, matches: List[Dict[str, Any]]) -> int:
        """
        Guarda matches en la tabla product_matching
        """
        if not matches:
            return 0
        
        try:
            with self.db_conn.cursor() as cur:
                # Limpiar matches antiguos
                cur.execute("UPDATE product_matching SET is_active = FALSE WHERE updated_at < NOW() - INTERVAL '1 day'")
                
                saved_count = 0
                for match in matches:
                    try:
                        cur.execute("""
                            INSERT INTO product_matching 
                            (codigo_base, codigo_match, similarity_score, match_type, match_confidence, 
                             match_reason, match_features, ml_model_version, is_active)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (codigo_base, codigo_match) 
                            DO UPDATE SET
                                similarity_score = EXCLUDED.similarity_score,
                                match_type = EXCLUDED.match_type,
                                match_confidence = EXCLUDED.match_confidence,
                                match_reason = EXCLUDED.match_reason,
                                match_features = EXCLUDED.match_features,
                                updated_at = NOW(),
                                is_active = TRUE
                        """, (
                            match['codigo_base'],
                            match['codigo_match'], 
                            match['similarity_score'],
                            match['match_type'],
                            match['match_confidence'],
                            match['match_reason'],
                            json.dumps(match['match_features']),
                            '1.0',
                            True
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando match individual: {e}")
                        continue
                
                logger.info(f"💾 Guardados {saved_count}/{len(matches)} matches en BD")
                return saved_count
                
        except Exception as e:
            logger.error(f"❌ Error guardando matches: {e}")
            return 0
    
    def detect_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """
        Detecta oportunidades de arbitraje
        """
        logger.info("🎯 Detectando oportunidades de arbitraje")
        
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    WITH price_differences AS (
                        SELECT 
                            pm.id as matching_id,
                            pm.similarity_score,
                            pm.match_confidence,
                            
                            -- Determinar producto más barato y más caro
                            CASE 
                                WHEN pr1.precio_oferta <= pr2.precio_oferta 
                                THEN pm.codigo_base 
                                ELSE pm.codigo_match 
                            END as codigo_barato,
                            
                            CASE 
                                WHEN pr1.precio_oferta <= pr2.precio_oferta 
                                THEN pm.codigo_match 
                                ELSE pm.codigo_base 
                            END as codigo_caro,
                            
                            -- Precios
                            LEAST(pr1.precio_oferta, pr2.precio_oferta) as precio_barato,
                            GREATEST(pr1.precio_oferta, pr2.precio_oferta) as precio_caro,
                            
                            -- Retailers
                            CASE 
                                WHEN pr1.precio_oferta <= pr2.precio_oferta 
                                THEN p1.retailer 
                                ELSE p2.retailer 
                            END as retailer_compra,
                            
                            CASE 
                                WHEN pr1.precio_oferta <= pr2.precio_oferta 
                                THEN p2.retailer 
                                ELSE p1.retailer 
                            END as retailer_venta,
                            
                            -- Diferencias
                            GREATEST(pr1.precio_oferta, pr2.precio_oferta) - LEAST(pr1.precio_oferta, pr2.precio_oferta) as diferencia,
                            
                            -- Info productos
                            p1.nombre as nombre_1, p2.nombre as nombre_2
                            
                        FROM product_matching pm
                        JOIN master_productos p1 ON pm.codigo_base = p1.codigo_interno
                        JOIN master_productos p2 ON pm.codigo_match = p2.codigo_interno
                        JOIN master_precios pr1 ON p1.codigo_interno = pr1.codigo_interno
                        JOIN master_precios pr2 ON p2.codigo_interno = pr2.codigo_interno
                        
                        WHERE pm.is_active = TRUE
                          AND pm.similarity_score >= %s
                          AND pr1.precio_oferta IS NOT NULL
                          AND pr2.precio_oferta IS NOT NULL
                          AND pr1.precio_oferta != pr2.precio_oferta
                    )
                    
                    SELECT *,
                           (diferencia * 100.0 / precio_barato) as diferencia_porcentaje
                    FROM price_differences
                    WHERE diferencia >= %s
                      AND (diferencia * 100.0 / precio_barato) >= %s
                    ORDER BY diferencia DESC, diferencia_porcentaje DESC
                    LIMIT 20
                """, (
                    self.config['min_similarity_score'],
                    self.config['min_margin_clp'],
                    self.config['min_percentage']
                ))
                
                opportunities_raw = cur.fetchall()
                
                opportunities = []
                for row in opportunities_raw:
                    # Calcular métricas
                    margen_bruto = row['diferencia']
                    costos_estimados = int(row['precio_barato'] * 0.08)  # 8% costos
                    ganancia_neta = margen_bruto - costos_estimados
                    roi_estimado = (ganancia_neta / row['precio_barato']) * 100
                    
                    opportunity_score = self._calculate_opportunity_score(
                        float(row['diferencia_porcentaje']),
                        float(row['similarity_score']),
                        margen_bruto
                    )
                    
                    opportunity = {
                        'matching_id': row['matching_id'],
                        'producto_barato_codigo': row['codigo_barato'],
                        'producto_caro_codigo': row['codigo_caro'],
                        'retailer_compra': row['retailer_compra'],
                        'retailer_venta': row['retailer_venta'],
                        'precio_compra': row['precio_barato'],
                        'precio_venta': row['precio_caro'],
                        'diferencia_absoluta': row['diferencia'],
                        'diferencia_porcentaje': float(row['diferencia_porcentaje']),
                        'margen_bruto': margen_bruto,
                        'roi_estimado': roi_estimado,
                        'opportunity_score': opportunity_score,
                        'risk_level': self._calculate_risk_level(row['match_confidence'], roi_estimado),
                        'detection_method': 'ml_price_difference',
                        'metadata': {
                            'similarity_score': float(row['similarity_score']),
                            'match_confidence': row['match_confidence'],
                            'nombre_barato': row['nombre_1'],
                            'nombre_caro': row['nombre_2']
                        }
                    }
                    opportunities.append(opportunity)
                
                logger.info(f"🎯 Detectadas {len(opportunities)} oportunidades de arbitraje")
                return opportunities
                
        except Exception as e:
            logger.error(f"❌ Error detectando oportunidades: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _calculate_opportunity_score(self, diferencia_pct: float, similarity_score: float, margen_bruto: int) -> float:
        """Calcula score de oportunidad"""
        diff_score = min(diferencia_pct / 100.0, 1.0)
        sim_score = float(similarity_score)
        margin_score = min(margen_bruto / 100000.0, 1.0)
        
        combined_score = (diff_score * 0.4) + (sim_score * 0.3) + (margin_score * 0.3)
        return 0.5 + (combined_score * 0.5)
    
    def _calculate_risk_level(self, match_confidence: str, roi_estimado: float) -> str:
        """Calcula nivel de riesgo"""
        if match_confidence == 'high' and roi_estimado > 30:
            return 'low'
        elif match_confidence == 'medium' and roi_estimado > 20:
            return 'medium'
        elif roi_estimado > 10:
            return 'medium'
        else:
            return 'high'


# Test function
def test_ml_integration():
    """Test de la integración ML"""
    
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    ml_integration = ArbitrageMLIntegration(db_params)
    
    try:
        print("🔌 Conectando a PostgreSQL...")
        ml_integration.connect()
        
        print("🔍 Buscando matches de productos con ML...")
        matches = ml_integration.find_product_matches(limit=100)
        print(f"✅ Encontrados {len(matches)} matches")
        
        if matches:
            print("💾 Guardando matches en BD...")
            saved = ml_integration.save_matches_to_db(matches)
            print(f"✅ Guardados {saved} matches")
            
            print("🎯 Detectando oportunidades de arbitraje...")
            opportunities = ml_integration.detect_arbitrage_opportunities()
            print(f"✅ Detectadas {len(opportunities)} oportunidades")
            
            if opportunities:
                print("\n🏆 TOP OPORTUNIDADES DETECTADAS:")
                print("=" * 70)
                
                for i, opp in enumerate(opportunities[:5], 1):
                    metadata = opp['metadata']
                    print(f"{i}. OPORTUNIDAD #{opp['matching_id']}")
                    print(f"   📦 Producto: {metadata.get('nombre_barato', 'N/A')[:50]}...")
                    print(f"   🛒 Comprar en {opp['retailer_compra']}: ${opp['precio_compra']:,}")
                    print(f"   💰 Vender en {opp['retailer_venta']}: ${opp['precio_venta']:,}")
                    print(f"   📈 Margen: ${opp['margen_bruto']:,} ({opp['diferencia_porcentaje']:.1f}%)")
                    print(f"   🎯 ROI: {opp['roi_estimado']:.1f}% | Score: {opp['opportunity_score']:.3f}")
                    print(f"   ⚖️ Riesgo: {opp['risk_level']} | ML Similitud: {metadata['similarity_score']:.3f}")
                    print("   " + "-" * 65)
                
                print(f"\n📊 ESTADÍSTICAS:")
                total_margin = sum(opp['margen_bruto'] for opp in opportunities)
                avg_roi = sum(opp['roi_estimado'] for opp in opportunities) / len(opportunities)
                print(f"   💰 Margen total potencial: ${total_margin:,}")
                print(f"   📈 ROI promedio: {avg_roi:.1f}%")
                print(f"   🎯 Score promedio: {sum(opp['opportunity_score'] for opp in opportunities) / len(opportunities):.3f}")
            else:
                print("ℹ️ No se detectaron oportunidades con los criterios actuales")
                print(f"   Criterios: Margen mín ${ml_integration.config['min_margin_clp']:,}, {ml_integration.config['min_percentage']}% mín")
        else:
            print("ℹ️ No se encontraron matches de productos")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        ml_integration.disconnect()


if __name__ == "__main__":
    test_ml_integration()