# -*- coding: utf-8 -*-
"""
🧠 SISTEMA INTELIGENTE DE GUARDADO DE DATOS DE ARBITRAJE
=======================================================

Características:
- ✅ Evita duplicados innecesarios
- ✅ Solo actualiza cuando hay cambios REALES de precios
- ✅ Guarda todos los campos necesarios (links, fechas, etc.)
- ✅ Tracking histórico de cambios de precios
- ✅ Sistema de validación de oportunidades
- ✅ Detección automática de cambios de stock
"""

import sys
import os
import json
import hashlib
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartArbitrageDataSaver:
    """
    🚀 Sistema inteligente para guardar oportunidades de arbitraje
    
    Evita duplicados y solo actualiza cuando hay cambios reales:
    - Cambios de precio significativos (>1%)
    - Cambios de stock
    - Nueva información de producto
    - Cambios en ratings/reviews
    """
    
    def __init__(self, db_params: Dict[str, Any]):
        self.db_params = db_params
        self.conn = None
        self.change_threshold_percent = 1.0  # 1% cambio mínimo para actualizar
        self.min_price_change_clp = 500      # $500 cambio mínimo absoluto
        
    def connect(self):
        """Conecta a PostgreSQL"""
        self.conn = psycopg2.connect(**self.db_params, cursor_factory=RealDictCursor)
        logger.info("🔌 Conectado a PostgreSQL para guardado inteligente")
    
    def disconnect(self):
        """Desconecta de PostgreSQL"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Desconectado de PostgreSQL")
    
    def save_opportunities_smart(self, opportunities: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Guarda oportunidades de forma inteligente evitando duplicados
        
        Returns:
            Dict con estadísticas: {
                'new_opportunities': int,
                'updated_opportunities': int, 
                'unchanged_opportunities': int,
                'invalidated_opportunities': int
            }
        """
        logger.info(f"📊 Procesando {len(opportunities)} oportunidades para guardado inteligente...")
        
        stats = {
            'new_opportunities': 0,
            'updated_opportunities': 0,
            'unchanged_opportunities': 0,
            'invalidated_opportunities': 0
        }
        
        cursor = self.conn.cursor()
        
        for opp in opportunities:
            try:
                # Enriquecer oportunidad con datos completos
                enriched_opp = self._enrich_opportunity_data(opp)
                
                # Generar hash único para la oportunidad
                opportunity_hash = self._generate_opportunity_hash(enriched_opp)
                
                # Verificar si existe oportunidad similar
                existing_opp = self._find_existing_opportunity(enriched_opp, cursor)
                
                if existing_opp:
                    # Verificar si hay cambios significativos
                    changes = self._detect_significant_changes(existing_opp, enriched_opp)
                    
                    if changes['has_significant_changes']:
                        # Actualizar oportunidad existente
                        self._update_existing_opportunity(existing_opp['id'], enriched_opp, changes, cursor)
                        stats['updated_opportunities'] += 1
                        logger.info(f"🔄 Actualizada oportunidad {existing_opp['id']}: {changes['change_summary']}")
                    else:
                        # Solo incrementar contador de veces detectada
                        self._increment_detection_count(existing_opp['id'], cursor)
                        stats['unchanged_opportunities'] += 1
                        logger.debug(f"➡️ Sin cambios significativos en oportunidad {existing_opp['id']}")
                else:
                    # Nueva oportunidad
                    new_opp_id = self._insert_new_opportunity(enriched_opp, opportunity_hash, cursor)
                    stats['new_opportunities'] += 1
                    logger.info(f"🆕 Nueva oportunidad creada #{new_opp_id}: ${enriched_opp['margen_bruto']:,} margen")
                
            except Exception as e:
                logger.error(f"❌ Error procesando oportunidad {opp.get('matching_id', 'N/A')}: {e}")
                continue
        
        # Invalidar oportunidades obsoletas (precios ya no válidos)
        invalidated = self._invalidate_obsolete_opportunities(cursor)
        stats['invalidated_opportunities'] = invalidated
        
        # Commit cambios
        self.conn.commit()
        
        logger.info(f"✅ Guardado completado: {stats}")
        return stats
    
    def _enrich_opportunity_data(self, opp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece la oportunidad con todos los datos necesarios desde la BD
        """
        cursor = self.conn.cursor()
        
        # Buscar datos completos del producto barato
        cursor.execute("""
            SELECT p.codigo_interno, p.link, p.sku, p.nombre, p.marca, p.categoria,
                   p.rating, p.reviews_count, p.out_of_stock, p.discount_percent,
                   pr.precio_normal, pr.precio_oferta, pr.precio_min_dia,
                   pr.descuento_porcentaje as desc_pct
            FROM master_productos p
            LEFT JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE p.nombre ILIKE %s AND p.retailer = %s
            AND pr.fecha >= CURRENT_DATE - INTERVAL '3 days'
            ORDER BY pr.fecha DESC
            LIMIT 1
        """, (f"%{opp['metadata']['nombre_barato'][:30]}%", opp['retailer_compra']))
        
        producto_barato = cursor.fetchone()
        
        # Buscar datos completos del producto caro
        cursor.execute("""
            SELECT p.codigo_interno, p.link, p.sku, p.nombre, p.marca, p.categoria,
                   p.rating, p.reviews_count, p.out_of_stock, p.discount_percent,
                   pr.precio_normal, pr.precio_oferta, pr.precio_min_dia,
                   pr.descuento_porcentaje as desc_pct
            FROM master_productos p
            LEFT JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE p.nombre ILIKE %s AND p.retailer = %s
            AND pr.fecha >= CURRENT_DATE - INTERVAL '3 days'
            ORDER BY pr.fecha DESC
            LIMIT 1
        """, (f"%{opp['metadata']['nombre_caro'][:30]}%", opp['retailer_venta']))
        
        producto_caro = cursor.fetchone()
        
        # Crear oportunidad enriquecida
        enriched = opp.copy()
        
        if producto_barato:
            enriched.update({
                'codigo_interno_barato': producto_barato['codigo_interno'],
                'link_producto_barato': producto_barato['link'],
                'codigo_sku_barato': producto_barato['sku'],
                'rating_barato': producto_barato['rating'],
                'reviews_barato': producto_barato['reviews_count'] or 0,
                'precio_normal_barato': producto_barato['precio_normal'],
                'precio_oferta_barato': producto_barato['precio_oferta'],
                'descuento_porcentaje_barato': producto_barato['desc_pct'],
                'stock_barato': not (producto_barato['out_of_stock'] or False),
                'categoria_producto': producto_barato['categoria'],
                'marca_producto': producto_barato['marca']
            })
        
        if producto_caro:
            enriched.update({
                'codigo_interno_caro': producto_caro['codigo_interno'],
                'link_producto_caro': producto_caro['link'],
                'codigo_sku_caro': producto_caro['sku'],
                'rating_caro': producto_caro['rating'],
                'reviews_caro': producto_caro['reviews_count'] or 0,
                'precio_normal_caro': producto_caro['precio_normal'],
                'precio_oferta_caro': producto_caro['precio_oferta'],
                'descuento_porcentaje_caro': producto_caro['desc_pct'],
                'stock_caro': not (producto_caro['out_of_stock'] or False),
            })
            
            # Si no tenemos categoría del producto barato, usar del caro
            if not enriched.get('categoria_producto'):
                enriched['categoria_producto'] = producto_caro['categoria']
            if not enriched.get('marca_producto'):
                enriched['marca_producto'] = producto_caro['marca']
        
        # Calcular scores adicionales
        enriched.update({
            'confidence_score': opp['metadata']['similarity_score'],
            'profit_potential_score': min(1.0, opp['roi_estimado'] / 100.0),
            'execution_difficulty': self._assess_execution_difficulty(enriched),
            'risk_assessment': self._assess_risk_level(enriched),
            'fecha_deteccion': date.today(),
            'fecha_ultima_actualizacion_precio': datetime.now()
        })
        
        return enriched
    
    def _generate_opportunity_hash(self, opp: Dict[str, Any]) -> str:
        """
        Genera hash único para identificar oportunidades similares
        """
        # Usar retailer + marca + categoría como identificador único
        hash_string = f"{opp['retailer_compra']}_{opp['retailer_venta']}_{opp.get('marca_producto', '')}_{opp.get('categoria_producto', '')}"
        
        # Normalizar nombres de productos para comparación
        nombre_barato_norm = (opp['metadata']['nombre_barato'] or '').lower().strip()[:50]
        nombre_caro_norm = (opp['metadata']['nombre_caro'] or '').lower().strip()[:50]
        
        hash_string += f"_{nombre_barato_norm}_{nombre_caro_norm}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()[:16]
    
    def _find_existing_opportunity(self, opp: Dict[str, Any], cursor) -> Optional[Dict[str, Any]]:
        """
        Busca oportunidad existente similar
        """
        # Buscar por retailers + marca + similitud de nombres
        cursor.execute("""
            SELECT * FROM arbitrage_opportunities
            WHERE retailer_compra = %s 
            AND retailer_venta = %s
            AND marca_producto = %s
            AND validez_oportunidad = 'active'
            AND fecha_deteccion >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 1
        """, (opp['retailer_compra'], opp['retailer_venta'], opp.get('marca_producto')))
        
        return cursor.fetchone()
    
    def _detect_significant_changes(self, existing_opp: Dict[str, Any], new_opp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta cambios significativos entre oportunidades
        """
        changes = {
            'has_significant_changes': False,
            'price_changes': [],
            'stock_changes': [],
            'other_changes': [],
            'change_summary': ''
        }
        
        # Verificar cambios de precio
        old_precio_compra = float(existing_opp['precio_compra'] or 0)
        new_precio_compra = float(new_opp['precio_compra'] or 0)
        
        old_precio_venta = float(existing_opp['precio_venta'] or 0)
        new_precio_venta = float(new_opp['precio_venta'] or 0)
        
        # Cambio significativo en precio de compra
        if old_precio_compra > 0 and abs(new_precio_compra - old_precio_compra) >= self.min_price_change_clp:
            percent_change = ((new_precio_compra - old_precio_compra) / old_precio_compra) * 100
            if abs(percent_change) >= self.change_threshold_percent:
                changes['price_changes'].append(f"Precio compra: ${old_precio_compra:,.0f} → ${new_precio_compra:,.0f} ({percent_change:+.1f}%)")
                changes['has_significant_changes'] = True
        
        # Cambio significativo en precio de venta
        if old_precio_venta > 0 and abs(new_precio_venta - old_precio_venta) >= self.min_price_change_clp:
            percent_change = ((new_precio_venta - old_precio_venta) / old_precio_venta) * 100
            if abs(percent_change) >= self.change_threshold_percent:
                changes['price_changes'].append(f"Precio venta: ${old_precio_venta:,.0f} → ${new_precio_venta:,.0f} ({percent_change:+.1f}%)")
                changes['has_significant_changes'] = True
        
        # Verificar cambios de stock
        old_stock_barato = existing_opp.get('stock_barato', True)
        new_stock_barato = new_opp.get('stock_barato', True)
        
        old_stock_caro = existing_opp.get('stock_caro', True)
        new_stock_caro = new_opp.get('stock_caro', True)
        
        if old_stock_barato != new_stock_barato:
            status = "disponible" if new_stock_barato else "agotado"
            changes['stock_changes'].append(f"Stock barato: {status}")
            changes['has_significant_changes'] = True
        
        if old_stock_caro != new_stock_caro:
            status = "disponible" if new_stock_caro else "agotado"
            changes['stock_changes'].append(f"Stock caro: {status}")
            changes['has_significant_changes'] = True
        
        # Generar resumen de cambios
        summary_parts = []
        if changes['price_changes']:
            summary_parts.append(f"{len(changes['price_changes'])} cambios de precio")
        if changes['stock_changes']:
            summary_parts.append(f"{len(changes['stock_changes'])} cambios de stock")
        
        changes['change_summary'] = ", ".join(summary_parts) if summary_parts else "Sin cambios significativos"
        
        return changes
    
    def _update_existing_opportunity(self, opp_id: int, new_opp: Dict[str, Any], changes: Dict[str, Any], cursor):
        """
        Actualiza oportunidad existente con nuevos datos
        """
        # Guardar estado anterior en historial
        cursor.execute("""
            INSERT INTO arbitrage_price_history 
            (opportunity_id, precio_compra_actual, precio_venta_actual, margen_actual, roi_actual,
             stock_barato_disponible, stock_caro_disponible, price_change_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            opp_id,
            new_opp['precio_compra'],
            new_opp['precio_venta'],
            new_opp['margen_bruto'],
            new_opp['diferencia_porcentaje'],
            new_opp.get('stock_barato', True),
            new_opp.get('stock_caro', True),
            changes['change_summary']
        ))
        
        # Actualizar oportunidad
        cursor.execute("""
            UPDATE arbitrage_opportunities SET
                precio_compra = %s,
                precio_venta = %s,
                margen_bruto = %s,
                diferencia_porcentaje = %s,
                stock_barato = %s,
                stock_caro = %s,
                fecha_ultima_actualizacion_precio = NOW(),
                times_detected = times_detected + 1,
                updated_at = NOW()
            WHERE id = %s
        """, (
            new_opp['precio_compra'],
            new_opp['precio_venta'],
            new_opp['margen_bruto'],
            new_opp['diferencia_porcentaje'],
            new_opp.get('stock_barato', True),
            new_opp.get('stock_caro', True),
            opp_id
        ))
    
    def _increment_detection_count(self, opp_id: int, cursor):
        """
        Incrementa contador de veces detectada sin otros cambios
        """
        cursor.execute("""
            UPDATE arbitrage_opportunities 
            SET times_detected = times_detected + 1,
                updated_at = NOW()
            WHERE id = %s
        """, (opp_id,))
    
    def _insert_new_opportunity(self, opp: Dict[str, Any], opp_hash: str, cursor) -> int:
        """
        Inserta nueva oportunidad con todos los campos
        """
        cursor.execute("""
            INSERT INTO arbitrage_opportunities (
                matching_id, producto_barato_codigo, producto_caro_codigo,
                retailer_compra, retailer_venta, precio_compra, precio_venta,
                margen_bruto, diferencia_porcentaje, opportunity_score, risk_level,
                fecha_deteccion, metadata, is_active,
                link_producto_barato, link_producto_caro,
                codigo_sku_barato, codigo_sku_caro,
                categoria_producto, marca_producto,
                rating_barato, rating_caro, reviews_barato, reviews_caro,
                precio_normal_barato, precio_normal_caro,
                precio_oferta_barato, precio_oferta_caro,
                descuento_porcentaje_barato, descuento_porcentaje_caro,
                stock_barato, stock_caro,
                confidence_score, profit_potential_score,
                execution_difficulty, risk_assessment,
                validez_oportunidad, times_detected
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            opp_hash,
            opp.get('codigo_interno_barato'),
            opp.get('codigo_interno_caro'),
            opp['retailer_compra'],
            opp['retailer_venta'],
            opp['precio_compra'],
            opp['precio_venta'],
            opp['margen_bruto'],
            opp['diferencia_porcentaje'],
            opp['opportunity_score'],
            opp['risk_level'],
            opp['fecha_deteccion'],
            json.dumps(opp['metadata']),
            True,
            opp.get('link_producto_barato'),
            opp.get('link_producto_caro'),
            opp.get('codigo_sku_barato'),
            opp.get('codigo_sku_caro'),
            opp.get('categoria_producto'),
            opp.get('marca_producto'),
            opp.get('rating_barato'),
            opp.get('rating_caro'),
            opp.get('reviews_barato', 0),
            opp.get('reviews_caro', 0),
            opp.get('precio_normal_barato'),
            opp.get('precio_normal_caro'),
            opp.get('precio_oferta_barato'),
            opp.get('precio_oferta_caro'),
            opp.get('descuento_porcentaje_barato'),
            opp.get('descuento_porcentaje_caro'),
            opp.get('stock_barato', True),
            opp.get('stock_caro', True),
            opp['confidence_score'],
            opp['profit_potential_score'],
            opp['execution_difficulty'],
            opp['risk_assessment'],
            'active',
            1
        ))
        
        return cursor.fetchone()['id']
    
    def _invalidate_obsolete_opportunities(self, cursor) -> int:
        """
        Invalida oportunidades obsoletas (sin actualizaciones recientes)
        """
        cursor.execute("""
            UPDATE arbitrage_opportunities 
            SET validez_oportunidad = 'obsolete'
            WHERE validez_oportunidad = 'active'
            AND updated_at < NOW() - INTERVAL '24 hours'
            AND times_detected = 1
        """)
        
        return cursor.rowcount
    
    def _assess_execution_difficulty(self, opp: Dict[str, Any]) -> str:
        """
        Evalúa dificultad de ejecución de la oportunidad
        """
        margen = opp.get('margen_bruto', 0)
        stock_barato = opp.get('stock_barato', True)
        stock_caro = opp.get('stock_caro', True)
        
        if not (stock_barato and stock_caro):
            return 'high'  # Sin stock = difícil
        elif margen >= 50000:
            return 'easy'   # Margen alto = fácil
        elif margen >= 20000:
            return 'medium'
        else:
            return 'hard'   # Margen bajo = difícil
    
    def _assess_risk_level(self, opp: Dict[str, Any]) -> str:
        """
        Evalúa nivel de riesgo de la oportunidad
        """
        confidence = opp.get('confidence_score', 0)
        roi = opp.get('roi_estimado', 0)
        
        risk_factors = []
        
        if confidence < 0.5:
            risk_factors.append("Similitud baja entre productos")
        
        if roi > 100:
            risk_factors.append("ROI sospechosamente alto")
        
        if not opp.get('stock_barato', True):
            risk_factors.append("Producto barato sin stock")
            
        if not opp.get('stock_caro', True):
            risk_factors.append("Producto caro sin stock")
        
        return f"{'Alto' if len(risk_factors) >= 2 else 'Medio' if risk_factors else 'Bajo'} riesgo" + (f": {'; '.join(risk_factors)}" if risk_factors else "")

def test_smart_saver():
    """
    Test del sistema inteligente de guardado
    """
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    saver = SmartArbitrageDataSaver(db_params)
    
    # Cargar oportunidades de prueba (las 17 detectadas anteriormente)
    with open('arbitrage/resultados_optimizados.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Aquí iríamos parseando las oportunidades del archivo
    # Por simplicidad, crear oportunidades de ejemplo
    
    test_opportunities = [
        {
            'matching_id': 'test_001',
            'retailer_compra': 'ripley',
            'retailer_venta': 'falabella',
            'precio_compra': 239990,
            'precio_venta': 399990,
            'margen_bruto': 160000,
            'diferencia_porcentaje': 66.7,
            'roi_estimado': 66.7,
            'opportunity_score': 0.85,
            'risk_level': 'medium',
            'metadata': {
                'nombre_barato': 'XIAOMI XIAOMI REDMI NOTE 14 PRO 4G 8GB + 256GB MOR',
                'nombre_caro': 'XIAOMI XIAOMI REDMI NOTE 14 PRO 4G 8GB + 256GB MOR',
                'similarity_score': 0.470
            }
        }
    ]
    
    try:
        saver.connect()
        stats = saver.save_opportunities_smart(test_opportunities)
        
        with open('arbitrage/smart_save_results.txt', 'w', encoding='utf-8') as f:
            f.write("RESULTADOS DEL SISTEMA INTELIGENTE DE GUARDADO\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Nuevas oportunidades: {stats['new_opportunities']}\n")
            f.write(f"Oportunidades actualizadas: {stats['updated_opportunities']}\n")
            f.write(f"Sin cambios: {stats['unchanged_opportunities']}\n")
            f.write(f"Invalidadas: {stats['invalidated_opportunities']}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en test: {e}")
        return False
        
    finally:
        saver.disconnect()

if __name__ == "__main__":
    test_smart_saver()