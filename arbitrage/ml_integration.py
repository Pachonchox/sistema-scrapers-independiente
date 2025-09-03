import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Integration para Sistema de Arbitraje
Wrapper que integra el ML existente con las tablas de arbitraje
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import asyncio
import asyncpg
import json
from datetime import datetime, timedelta

# Agregar paths necesarios
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class ArbitrageMLIntegration:
    """
    Integra el MatchScoringModel existente con el sistema de arbitraje
    """
    
    def __init__(self, db_connection_params: Dict[str, Any]):
        self.db_params = db_connection_params
        self.db_pool = None
        self.match_scorer = None
        
        # Parámetros de arbitraje desde BD
        self.config = {
            'min_margin_clp': 5000,
            'min_percentage': 15.0,
            'min_similarity_score': 0.85,
            'max_price_ratio': 5.0  # Evitar matchings absurdos
        }
        
        self._initialize_ml_scorer()
    
    def _initialize_ml_scorer(self):
        """Inicializa el MatchScoringModel existente"""
        try:
            from scraper_v4.ml.normalization.match_scorer import MatchScoringModel
            self.match_scorer = MatchScoringModel(
                threshold=self.config['min_similarity_score'],
                embedder_name="paraphrase-multilingual-mpnet-base-v2"
            )
            logger.info("✅ MatchScoringModel integrado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando MatchScoringModel: {e}")
            # Fallback a matching básico
            self.match_scorer = None
    
    async def connect(self):
        """Establece conexión con PostgreSQL"""
        try:
            self.db_pool = await asyncpg.create_pool(**self.db_params)
            await self._load_config_from_db()
            logger.info("✅ Conexión establecida con PostgreSQL para arbitraje")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Cierra conexión con PostgreSQL"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("🔌 Conexión PostgreSQL cerrada")
    
    async def _load_config_from_db(self):
        """Carga configuración desde la tabla arbitrage_config"""
        try:
            async with self.db_pool.acquire() as conn:
                config_rows = await conn.fetch(
                    "SELECT config_key, config_value, config_type FROM arbitrage_config WHERE is_active = TRUE"
                )
                
                for row in config_rows:
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
    
    async def find_product_matches(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Encuentra todos los matches posibles entre productos usando el ML existente
        """
        logger.info(f"🔍 Buscando matches de productos (límite: {limit})")
        
        try:
            async with self.db_pool.acquire() as conn:
                # Obtener productos candidatos para matching
                productos = await conn.fetch("""
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
                    LIMIT $1
                """, limit)
                
                logger.info(f"📦 Analizando {len(productos)} productos para matching")
                
                matches_found = []
                processed_pairs = set()
                
                # Comparar cada producto con todos los demás de diferente retailer
                for i, prod_a in enumerate(productos):
                    for j, prod_b in enumerate(productos[i+1:], i+1):
                        
                        # Solo comparar productos de diferentes retailers
                        if prod_a['retailer'] == prod_b['retailer']:
                            continue
                        
                        # Evitar duplicados
                        pair_key = tuple(sorted([prod_a['codigo_interno'], prod_b['codigo_interno']]))
                        if pair_key in processed_pairs:
                            continue
                        processed_pairs.add(pair_key)
                        
                        # Verificar que hay diferencia de precio significativa
                        precio_a = prod_a['precio_oferta'] or prod_a['precio_normal']
                        precio_b = prod_b['precio_oferta'] or prod_b['precio_normal']
                        
                        if not precio_a or not precio_b:
                            continue
                        
                        # Evitar comparaciones de precios muy dispares
                        precio_ratio = max(precio_a, precio_b) / min(precio_a, precio_b)
                        if precio_ratio > self.config['max_price_ratio']:
                            continue
                        
                        # Usar el ML existente para scoring
                        similarity_score = await self._calculate_similarity(prod_a, prod_b)
                        
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
            return []
    
    async def _calculate_similarity(self, prod_a: Dict, prod_b: Dict) -> float:
        """
        Calcula similitud usando el ML existente
        """
        try:
            if self.match_scorer is None:
                # Fallback a matching básico por marca y categoría
                brand_match = prod_a['marca'].lower() == prod_b['marca'].lower()
                category_match = prod_a['categoria'] == prod_b['categoria']
                
                if brand_match and category_match:
                    return 0.9
                elif brand_match or category_match:
                    return 0.7
                else:
                    return 0.5
            
            # Usar el MatchScoringModel existente
            # Convertir a formato esperado por el scorer
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
            logger.warning(f"⚠️ Error calculando similitud ML, usando fallback: {e}")
            # Fallback básico
            brand_match = prod_a['marca'].lower() == prod_b['marca'].lower()
            category_match = prod_a['categoria'] == prod_b['categoria']
            
            if brand_match and category_match:
                return 0.85
            else:
                return 0.6
    
    def _classify_match_type(self, similarity_score: float) -> str:
        """Clasifica el tipo de match basado en el score"""
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
    
    async def save_matches_to_db(self, matches: List[Dict[str, Any]]) -> int:
        """
        Guarda los matches encontrados en la tabla product_matching
        """
        if not matches:
            return 0
        
        try:
            async with self.db_pool.acquire() as conn:
                # Limpiar matches antiguos (opcional, depende de la estrategia)
                await conn.execute("UPDATE product_matching SET is_active = FALSE WHERE updated_at < NOW() - INTERVAL '1 day'")
                
                saved_count = 0
                for match in matches:
                    try:
                        # Insertar o actualizar match
                        await conn.execute("""
                            INSERT INTO product_matching 
                            (codigo_base, codigo_match, similarity_score, match_type, match_confidence, 
                             match_reason, match_features, ml_model_version, is_active)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT (codigo_base, codigo_match) 
                            DO UPDATE SET
                                similarity_score = EXCLUDED.similarity_score,
                                match_type = EXCLUDED.match_type,
                                match_confidence = EXCLUDED.match_confidence,
                                match_reason = EXCLUDED.match_reason,
                                match_features = EXCLUDED.match_features,
                                updated_at = NOW(),
                                is_active = TRUE
                        """, 
                            match['codigo_base'],
                            match['codigo_match'], 
                            match['similarity_score'],
                            match['match_type'],
                            match['match_confidence'],
                            match['match_reason'],
                            json.dumps(match['match_features']),
                            '1.0',
                            True
                        )
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando match individual: {e}")
                        continue
                
                logger.info(f"💾 Guardados {saved_count}/{len(matches)} matches en BD")
                return saved_count
                
        except Exception as e:
            logger.error(f"❌ Error guardando matches: {e}")
            return 0
    
    async def detect_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """
        Detecta oportunidades de arbitraje basándose en los matches existentes
        """
        logger.info("🎯 Detectando oportunidades de arbitraje")
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query para encontrar oportunidades
                opportunities_raw = await conn.fetch("""
                    WITH price_differences AS (
                        SELECT 
                            pm.id as matching_id,
                            pm.similarity_score,
                            pm.match_confidence,
                            
                            -- Producto más barato
                            CASE 
                                WHEN pr1.precio_oferta <= pr2.precio_oferta 
                                THEN pm.codigo_base 
                                ELSE pm.codigo_match 
                            END as codigo_barato,
                            
                            -- Producto más caro
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
                            p1.nombre as nombre_1,
                            p2.nombre as nombre_2,
                            p1.marca as marca_1,
                            p2.marca as marca_2
                            
                        FROM product_matching pm
                        JOIN master_productos p1 ON pm.codigo_base = p1.codigo_interno
                        JOIN master_productos p2 ON pm.codigo_match = p2.codigo_interno
                        JOIN master_precios pr1 ON p1.codigo_interno = pr1.codigo_interno
                        JOIN master_precios pr2 ON p2.codigo_interno = pr2.codigo_interno
                        
                        WHERE pm.is_active = TRUE
                          AND pm.similarity_score >= $1
                          AND pr1.precio_oferta IS NOT NULL
                          AND pr2.precio_oferta IS NOT NULL
                          AND pr1.precio_oferta != pr2.precio_oferta
                    )
                    
                    SELECT *,
                           (diferencia * 100.0 / precio_barato) as diferencia_porcentaje
                    FROM price_differences
                    WHERE diferencia >= $2
                      AND (diferencia * 100.0 / precio_barato) >= $3
                    ORDER BY diferencia DESC, diferencia_porcentaje DESC
                    LIMIT 100
                """, 
                    self.config['min_similarity_score'],
                    self.config['min_margin_clp'],
                    self.config['min_percentage']
                )
                
                opportunities = []
                for row in opportunities_raw:
                    # Calcular métricas adicionales
                    margen_bruto = row['diferencia']
                    costos_estimados = int(row['precio_barato'] * 0.08)  # 8% costos estimados
                    ganancia_neta = margen_bruto - costos_estimados
                    roi_estimado = (ganancia_neta / row['precio_barato']) * 100
                    
                    # Calcular opportunity score
                    opportunity_score = self._calculate_opportunity_score(
                        row['diferencia_porcentaje'],
                        row['similarity_score'],
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
                            'producto_barato_nombre': row['nombre_1'] if row['codigo_barato'] == row.get('codigo_base', '') else row['nombre_2'],
                            'producto_caro_nombre': row['nombre_2'] if row['codigo_barato'] == row.get('codigo_base', '') else row['nombre_1']
                        }
                    }
                    opportunities.append(opportunity)
                
                logger.info(f"🎯 Detectadas {len(opportunities)} oportunidades de arbitraje")
                return opportunities
                
        except Exception as e:
            logger.error(f"❌ Error detectando oportunidades: {e}")
            return []
    
    def _calculate_opportunity_score(self, diferencia_pct: float, similarity_score: float, margen_bruto: int) -> float:
        """Calcula score de oportunidad (0.5 - 1.0)"""
        # Normalizar componentes
        diff_score = min(diferencia_pct / 100.0, 1.0)  # Max 100%
        sim_score = float(similarity_score)
        margin_score = min(margen_bruto / 100000.0, 1.0)  # Max 100k CLP
        
        # Combinar: 40% diferencia, 30% similitud, 30% margen
        combined_score = (diff_score * 0.4) + (sim_score * 0.3) + (margin_score * 0.3)
        
        # Escalar a rango 0.5 - 1.0
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
    
    async def save_opportunities_to_db(self, opportunities: List[Dict[str, Any]]) -> int:
        """
        Guarda oportunidades en la tabla arbitrage_opportunities
        """
        if not opportunities:
            return 0
        
        try:
            async with self.db_pool.acquire() as conn:
                saved_count = 0
                
                for opp in opportunities:
                    try:
                        await conn.execute("""
                            INSERT INTO arbitrage_opportunities
                            (producto_barato_codigo, producto_caro_codigo, matching_id,
                             retailer_compra, retailer_venta, precio_compra, precio_venta,
                             diferencia_absoluta, diferencia_porcentaje, margen_bruto, roi_estimado,
                             opportunity_score, risk_level, detection_method, metadata)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                            ON CONFLICT (producto_barato_codigo, producto_caro_codigo, detected_at::date)
                            DO UPDATE SET
                                precio_compra = EXCLUDED.precio_compra,
                                precio_venta = EXCLUDED.precio_venta,
                                diferencia_absoluta = EXCLUDED.diferencia_absoluta,
                                diferencia_porcentaje = EXCLUDED.diferencia_porcentaje,
                                margen_bruto = EXCLUDED.margen_bruto,
                                roi_estimado = EXCLUDED.roi_estimado,
                                opportunity_score = EXCLUDED.opportunity_score,
                                updated_at = NOW()
                        """,
                            opp['producto_barato_codigo'],
                            opp['producto_caro_codigo'],
                            opp['matching_id'],
                            opp['retailer_compra'],
                            opp['retailer_venta'],
                            opp['precio_compra'],
                            opp['precio_venta'],
                            opp['diferencia_absoluta'],
                            opp['diferencia_porcentaje'],
                            opp['margen_bruto'],
                            opp['roi_estimado'],
                            opp['opportunity_score'],
                            opp['risk_level'],
                            opp['detection_method'],
                            json.dumps(opp['metadata'])
                        )
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando oportunidad: {e}")
                        continue
                
                logger.info(f"💾 Guardadas {saved_count}/{len(opportunities)} oportunidades")
                return saved_count
                
        except Exception as e:
            logger.error(f"❌ Error guardando oportunidades: {e}")
            return 0


# Test function
async def test_ml_integration():
    """Función de test para la integración ML"""
    
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
        await ml_integration.connect()
        
        print("🔍 Buscando matches de productos...")
        matches = await ml_integration.find_product_matches(limit=200)
        print(f"✅ Encontrados {len(matches)} matches")
        
        if matches:
            print("💾 Guardando matches en BD...")
            saved = await ml_integration.save_matches_to_db(matches)
            print(f"✅ Guardados {saved} matches")
            
            print("🎯 Detectando oportunidades de arbitraje...")
            opportunities = await ml_integration.detect_arbitrage_opportunities()
            print(f"✅ Detectadas {len(opportunities)} oportunidades")
            
            if opportunities:
                print("💾 Guardando oportunidades...")
                saved_opp = await ml_integration.save_opportunities_to_db(opportunities)
                print(f"✅ Guardadas {saved_opp} oportunidades")
                
                print("\n🏆 TOP 3 OPORTUNIDADES:")
                for i, opp in enumerate(opportunities[:3], 1):
                    metadata = opp['metadata']
                    print(f"{i}. {metadata.get('producto_barato_nombre', 'N/A')[:50]}")
                    print(f"   Compra en {opp['retailer_compra']}: ${opp['precio_compra']:,}")
                    print(f"   Venta en {opp['retailer_venta']}: ${opp['precio_venta']:,}")
                    print(f"   Margen: ${opp['margen_bruto']:,} ({opp['diferencia_porcentaje']:.1f}%)")
                    print(f"   ROI: {opp['roi_estimado']:.1f}% | Score: {opp['opportunity_score']:.3f}")
                    print(f"   Riesgo: {opp['risk_level']} | Similitud: {metadata['similarity_score']:.3f}")
                    print()
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await ml_integration.disconnect()


if __name__ == "__main__":
    asyncio.run(test_ml_integration())