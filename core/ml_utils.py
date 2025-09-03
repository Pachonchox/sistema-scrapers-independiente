# -*- coding: utf-8 -*-
"""
ML Utils - Sistema V5 Autónomo
===============================
Utilidades de ML simplificadas para operación autónoma sin dependencias externas.
"""

import logging
from typing import Dict, List, Any, Optional
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SimpleGlitchDetection:
    """
    Sistema simplificado de detección de anomalías de precios
    
    Implementa lógica básica sin dependencias ML externas:
    - Detección de cambios extremos (>90% arriba/abajo)
    - Análisis de volatilidad histórica
    - Identificación de precios irreales (outliers extremos)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_price_change_pct = self.config.get('max_price_change_pct', 90)
        self.min_valid_price = self.config.get('min_valid_price', 1000)  # CLP
        self.max_valid_price = self.config.get('max_valid_price', 50000000)  # 50M CLP
        
    def detect_glitch(self, current_price: float, historical_prices: List[float], 
                     product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detectar anomalías en precios actuales vs históricos
        
        Args:
            current_price: Precio actual
            historical_prices: Lista de precios históricos
            product_data: Datos adicionales del producto
            
        Returns:
            Resultado de detección con score y razones
        """
        result = {
            'is_glitch': False,
            'glitch_score': 0.0,
            'reasons': [],
            'confidence': 0.0,
            'recommendation': 'accept'
        }
        
        if not current_price or current_price <= 0:
            result.update({
                'is_glitch': True,
                'glitch_score': 1.0,
                'reasons': ['precio_invalido_cero'],
                'confidence': 1.0,
                'recommendation': 'reject'
            })
            return result
        
        # Verificar rangos válidos
        if current_price < self.min_valid_price or current_price > self.max_valid_price:
            result.update({
                'is_glitch': True,
                'glitch_score': 0.9,
                'reasons': ['precio_fuera_rango_valido'],
                'confidence': 0.9,
                'recommendation': 'review'
            })
            return result
        
        # Análisis histórico si hay datos
        if historical_prices:
            historical_prices = [p for p in historical_prices if p > 0]
            
            if historical_prices:
                # Calcular estadísticas básicas
                avg_price = statistics.mean(historical_prices)
                median_price = statistics.median(historical_prices)
                
                if len(historical_prices) > 1:
                    std_price = statistics.stdev(historical_prices)
                else:
                    std_price = 0
                
                # Detectar cambio extremo vs promedio
                if avg_price > 0:
                    change_pct = abs(current_price - avg_price) / avg_price * 100
                    
                    if change_pct > self.max_price_change_pct:
                        result['reasons'].append(f'cambio_extremo_vs_promedio_{change_pct:.1f}pct')
                        result['glitch_score'] += 0.6
                
                # Detectar outlier extremo (más de 3 desviaciones estándar)
                if std_price > 0 and len(historical_prices) > 2:
                    z_score = abs(current_price - avg_price) / std_price
                    
                    if z_score > 3:
                        result['reasons'].append(f'outlier_estadistico_z_{z_score:.1f}')
                        result['glitch_score'] += 0.4
                
                # Detectar precio demasiado bajo vs histórico
                min_historical = min(historical_prices)
                if current_price < min_historical * 0.1:  # 90% menor que el mínimo histórico
                    result['reasons'].append('precio_excesivamente_bajo')
                    result['glitch_score'] += 0.7
                
                # Detectar precio demasiado alto vs histórico  
                max_historical = max(historical_prices)
                if current_price > max_historical * 10:  # 10x mayor que el máximo histórico
                    result['reasons'].append('precio_excesivamente_alto')
                    result['glitch_score'] += 0.7
        
        # Determinar si es glitch
        if result['glitch_score'] >= 0.5:
            result['is_glitch'] = True
            result['confidence'] = min(result['glitch_score'], 1.0)
            
            if result['glitch_score'] >= 0.8:
                result['recommendation'] = 'reject'
            else:
                result['recommendation'] = 'review'
        else:
            result['confidence'] = 1.0 - result['glitch_score']
            result['recommendation'] = 'accept'
        
        return result
    
    def batch_detect(self, price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detección en lote para múltiples productos
        
        Args:
            price_data: Lista de datos de precios con formato:
                       [{'current_price': float, 'historical': [floats], 'product_data': dict}]
        
        Returns:
            Lista de resultados de detección
        """
        results = []
        
        for item in price_data:
            current = item.get('current_price', 0)
            historical = item.get('historical', [])
            product_data = item.get('product_data', {})
            
            detection_result = self.detect_glitch(current, historical, product_data)
            
            # Agregar contexto del producto
            detection_result.update({
                'product_sku': product_data.get('sku', ''),
                'product_name': product_data.get('nombre', ''),
                'retailer': product_data.get('retailer', ''),
                'current_price': current,
                'historical_count': len(historical)
            })
            
            results.append(detection_result)
        
        return results
    
    def get_summary_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generar estadísticas resumen de detecciones
        
        Args:
            results: Resultados de batch_detect
            
        Returns:
            Estadísticas resumidas
        """
        if not results:
            return {'total': 0, 'glitches': 0, 'glitch_rate': 0.0}
        
        total = len(results)
        glitches = sum(1 for r in results if r.get('is_glitch', False))
        
        # Contar por tipo de razón
        reason_counts = {}
        for result in results:
            for reason in result.get('reasons', []):
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Calcular confianza promedio
        avg_confidence = statistics.mean([r.get('confidence', 0) for r in results])
        
        return {
            'total_analyzed': total,
            'glitches_detected': glitches,
            'glitch_rate': glitches / total if total > 0 else 0.0,
            'clean_products': total - glitches,
            'avg_confidence': avg_confidence,
            'reason_breakdown': reason_counts,
            'timestamp': datetime.now().isoformat()
        }

class SimpleAnomalyDetector:
    """
    Detector de anomalías simplificado para patrones de scraping
    """
    
    def __init__(self):
        self.recent_patterns = {}  # retailer -> lista de métricas recientes
        
    def analyze_scraping_pattern(self, retailer: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizar patrones anómalos en métricas de scraping
        
        Args:
            retailer: Nombre del retailer
            metrics: Métricas de la ejecución (productos, tiempo, errores, etc.)
            
        Returns:
            Análisis de anomalías
        """
        if retailer not in self.recent_patterns:
            self.recent_patterns[retailer] = []
        
        # Mantener solo últimas 20 ejecuciones
        self.recent_patterns[retailer].append(metrics)
        self.recent_patterns[retailer] = self.recent_patterns[retailer][-20:]
        
        recent = self.recent_patterns[retailer]
        
        anomalies = []
        
        if len(recent) >= 3:
            # Analizar productos scrapeados
            product_counts = [r.get('products_count', 0) for r in recent]
            current_products = metrics.get('products_count', 0)
            
            if product_counts:
                avg_products = statistics.mean(product_counts)
                
                # Detectar caída drástica en productos
                if current_products < avg_products * 0.3:  # 70% menos productos
                    anomalies.append({
                        'type': 'productos_muy_bajo',
                        'severity': 'high',
                        'current': current_products,
                        'expected': avg_products,
                        'deviation': (current_products - avg_products) / avg_products
                    })
                
                # Detectar aumento anómalo
                elif current_products > avg_products * 3:  # 3x más productos
                    anomalies.append({
                        'type': 'productos_muy_alto', 
                        'severity': 'medium',
                        'current': current_products,
                        'expected': avg_products,
                        'deviation': (current_products - avg_products) / avg_products
                    })
            
            # Analizar tiempo de ejecución
            execution_times = [r.get('execution_time', 0) for r in recent if r.get('execution_time', 0) > 0]
            current_time = metrics.get('execution_time', 0)
            
            if execution_times and current_time > 0:
                avg_time = statistics.mean(execution_times)
                
                # Detectar lentitud anómala (3x más lento)
                if current_time > avg_time * 3:
                    anomalies.append({
                        'type': 'ejecucion_muy_lenta',
                        'severity': 'medium',
                        'current': current_time,
                        'expected': avg_time,
                        'deviation': (current_time - avg_time) / avg_time
                    })
        
        return {
            'has_anomalies': len(anomalies) > 0,
            'anomaly_count': len(anomalies),
            'anomalies': anomalies,
            'retailer': retailer,
            'analysis_timestamp': datetime.now().isoformat()
        }