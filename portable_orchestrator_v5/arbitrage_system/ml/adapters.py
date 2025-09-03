# -*- coding: utf-8 -*-
"""
🔌 ML Adapters V5 - Adaptadores para Integración ML Autónoma
==========================================================
Adaptadores para conectar sistema V5 autónomo con componentes ML internos.
Compatible con emojis y optimizado para operación continua no supervisada.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class MatchScoringAdapter:
    """
    Adaptador para scoring de matching V5 🎯
    
    Conecta con sistema de matching interno del V5 manteniendo autonomía
    """
    
    def __init__(self):
        # Configuración de scoring V5 optimizada
        self.scoring_weights = {
            'brand_similarity': 0.25,
            'model_similarity': 0.30,
            'price_proximity': 0.20,
            'category_match': 0.15,
            'specifications': 0.10
        }
        
        self.min_confidence_threshold = 0.75
        logger.info("✅ MatchScoringAdapter V5 inicializado")
    
    def calculate_match_score(self, product_1: Dict[str, Any], 
                            product_2: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calcula score de matching entre productos 🔢
        
        Args:
            product_1: Producto 1 para comparar
            product_2: Producto 2 para comparar
            
        Returns:
            Tuple[score, detalles]: Score y detalles del matching
        """
        try:
            scores = {}
            
            # Similaridad de marca (normalizada)
            brand_1 = str(product_1.get('marca', '')).lower().strip()
            brand_2 = str(product_2.get('marca', '')).lower().strip()
            scores['brand_similarity'] = self._calculate_string_similarity(brand_1, brand_2)
            
            # Similaridad de modelo
            model_1 = str(product_1.get('modelo', '')).lower().strip()
            model_2 = str(product_2.get('modelo', '')).lower().strip()
            scores['model_similarity'] = self._calculate_string_similarity(model_1, model_2)
            
            # Proximidad de precios
            price_1 = product_1.get('precio_oferta') or product_1.get('precio_normal') or product_1.get('precio_actual') or 0
            price_2 = product_2.get('precio_oferta') or product_2.get('precio_normal') or product_2.get('precio_actual') or 0
            
            price_1 = float(price_1) if price_1 is not None else 0.0
            price_2 = float(price_2) if price_2 is not None else 0.0
            scores['price_proximity'] = self._calculate_price_proximity(price_1, price_2)
            
            # Match de categoría
            cat_1 = str(product_1.get('categoria', '')).lower().strip()
            cat_2 = str(product_2.get('categoria', '')).lower().strip()
            scores['category_match'] = 1.0 if cat_1 == cat_2 else 0.3
            
            # Especificaciones técnicas
            specs_1 = {
                'storage': str(product_1.get('storage', '')),
                'ram': str(product_1.get('ram', '')),
                'screen': str(product_1.get('screen', ''))
            }
            specs_2 = {
                'storage': str(product_2.get('storage', '')),
                'ram': str(product_2.get('ram', '')),
                'screen': str(product_2.get('screen', ''))
            }
            scores['specifications'] = self._calculate_specs_similarity(specs_1, specs_2)
            
            # Score final ponderado
            final_score = sum(
                score * self.scoring_weights[key] 
                for key, score in scores.items()
            )
            
            details = {
                'scores': scores,
                'weights': self.scoring_weights,
                'final_score': final_score,
                'confidence_level': 'high' if final_score >= 0.8 else 'medium' if final_score >= 0.6 else 'low',
                'timestamp': datetime.now().isoformat()
            }
            
            return final_score, details
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculando match score: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calcula similaridad entre strings usando algoritmo optimizado"""
        if not str1 or not str2:
            return 0.0
        
        if str1 == str2:
            return 1.0
        
        # Algoritmo de distancia de Levenshtein simplificado
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Palabras comunes
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if words1 & words2:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union if union > 0 else 0.0
        
        return 0.1  # Similaridad mínima
    
    def _calculate_price_proximity(self, price1: float, price2: float) -> float:
        """Calcula proximidad de precios"""
        if price1 <= 0 or price2 <= 0:
            return 0.0
        
        min_price = min(price1, price2)
        max_price = max(price1, price2)
        
        if min_price == max_price:
            return 1.0
        
        # Tolerancia de ±20% se considera alta proximidad
        ratio = min_price / max_price
        if ratio >= 0.8:
            return 1.0
        elif ratio >= 0.6:
            return 0.7
        elif ratio >= 0.4:
            return 0.4
        else:
            return 0.1
    
    def _calculate_specs_similarity(self, specs1: Dict, specs2: Dict) -> float:
        """Calcula similaridad de especificaciones"""
        total_specs = len(specs1)
        if total_specs == 0:
            return 0.0
        
        matches = 0
        for key in specs1:
            val1 = specs1[key].lower().strip()
            val2 = specs2.get(key, '').lower().strip()
            
            if val1 and val2 and val1 == val2:
                matches += 1
        
        return matches / total_specs


class GlitchDetectionAdapter:
    """
    Adaptador para detección de glitches V5 🐛
    
    Detecta anomalías y problemas en datos de productos manteniendo autonomía
    """
    
    def __init__(self):
        # Configuración de detección V5
        self.price_thresholds = {
            'min_price': 1000,      # CLP
            'max_price': 50000000,  # CLP  
            'max_change_ratio': 5.0  # 500% cambio máximo
        }
        
        self.anomaly_patterns = {
            'zero_prices': 0,
            'negative_prices': 0,
            'extreme_prices': 0,
            'invalid_brands': 0,
            'missing_data': 0
        }
        
        logger.info("✅ GlitchDetectionAdapter V5 inicializado")
    
    def detect_product_anomalies(self, product: Dict[str, Any], 
                                historical_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Detecta anomalías en producto 🔍
        
        Args:
            product: Datos del producto a analizar
            historical_data: Datos históricos para comparación
            
        Returns:
            Dict con anomalías detectadas y nivel de confianza
        """
        try:
            anomalies = {
                'detected_anomalies': [],
                'severity': 'normal',
                'confidence_score': 1.0,
                'recommendations': []
            }
            
            # Verificar precios
            price_issues = self._check_price_anomalies(product)
            if price_issues:
                anomalies['detected_anomalies'].extend(price_issues)
                anomalies['severity'] = 'medium'
                anomalies['confidence_score'] *= 0.7
            
            # Verificar datos faltantes
            missing_data = self._check_missing_data(product)
            if missing_data:
                anomalies['detected_anomalies'].extend(missing_data)
                if anomalies['severity'] == 'normal':
                    anomalies['severity'] = 'low'
                anomalies['confidence_score'] *= 0.9
            
            # Verificar consistencia de marca/modelo
            brand_issues = self._check_brand_consistency(product)
            if brand_issues:
                anomalies['detected_anomalies'].extend(brand_issues)
                anomalies['confidence_score'] *= 0.8
            
            # Comparación histórica si disponible
            if historical_data:
                historical_issues = self._check_historical_consistency(product, historical_data)
                if historical_issues:
                    anomalies['detected_anomalies'].extend(historical_issues)
                    anomalies['severity'] = 'high'
                    anomalies['confidence_score'] *= 0.5
            
            # Generar recomendaciones
            anomalies['recommendations'] = self._generate_recommendations(anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Error detectando anomalías: {e}")
            return {
                'detected_anomalies': [f"Error en detección: {e}"],
                'severity': 'high',
                'confidence_score': 0.0,
                'recommendations': ['Reintentar detección de anomalías']
            }
    
    def _check_price_anomalies(self, product: Dict[str, Any]) -> List[str]:
        """Verifica anomalías en precios"""
        issues = []
        
        precio_normal = product.get('precio_normal', 0)
        precio_oferta = product.get('precio_oferta', 0)
        
        # Precios cero o negativos
        if precio_normal <= 0:
            issues.append("Precio normal inválido (≤0)")
        
        if precio_oferta < 0:
            issues.append("Precio oferta negativo")
        
        # Precios extremos
        if precio_normal > self.price_thresholds['max_price']:
            issues.append(f"Precio normal extremo: ${precio_normal:,.0f}")
        
        if precio_normal < self.price_thresholds['min_price']:
            issues.append(f"Precio normal muy bajo: ${precio_normal:,.0f}")
        
        # Relación precio oferta/normal
        if precio_oferta > 0 and precio_normal > 0:
            if precio_oferta > precio_normal:
                issues.append("Precio oferta mayor que precio normal")
        
        return issues
    
    def _check_missing_data(self, product: Dict[str, Any]) -> List[str]:
        """Verifica datos faltantes críticos"""
        issues = []
        
        required_fields = ['nombre', 'marca', 'categoria', 'retailer']
        
        for field in required_fields:
            value = product.get(field)
            if not value or str(value).strip() == '':
                issues.append(f"Campo requerido faltante: {field}")
        
        return issues
    
    def _check_brand_consistency(self, product: Dict[str, Any]) -> List[str]:
        """Verifica consistencia de marca y modelo"""
        issues = []
        
        marca = str(product.get('marca', '')).lower()
        nombre = str(product.get('nombre', '')).lower()
        
        # Marca debería aparecer en el nombre del producto
        if marca and nombre and marca not in nombre:
            # Algunas excepciones comunes
            brand_aliases = {
                'samsung': ['sams', 'galaxy'],
                'apple': ['iphone', 'ipad', 'mac'],
                'lg': ['lg electronics'],
                'sony': ['sony ericsson', 'xperia']
            }
            
            found_alias = False
            for brand, aliases in brand_aliases.items():
                if marca == brand:
                    for alias in aliases:
                        if alias in nombre:
                            found_alias = True
                            break
            
            if not found_alias:
                issues.append(f"Marca '{marca}' no aparece consistente en nombre del producto")
        
        return issues
    
    def _check_historical_consistency(self, product: Dict[str, Any], 
                                    historical_data: List[Dict]) -> List[str]:
        """Verifica consistencia con datos históricos"""
        issues = []
        
        if not historical_data:
            return issues
        
        current_price = product.get('precio_normal', 0)
        if current_price <= 0:
            return issues
        
        # Analizar últimos precios
        recent_prices = [float(item.get('precio_normal', 0)) for item in historical_data[-5:]]
        valid_prices = [p for p in recent_prices if p > 0]
        
        if valid_prices:
            avg_historical = sum(valid_prices) / len(valid_prices)
            
            # Cambio extremo
            change_ratio = abs(current_price - avg_historical) / avg_historical
            if change_ratio > self.price_thresholds['max_change_ratio']:
                issues.append(f"Cambio de precio extremo: {change_ratio*100:.1f}%")
        
        return issues
    
    def _generate_recommendations(self, anomalies: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en anomalías detectadas"""
        recommendations = []
        
        if anomalies['severity'] == 'high':
            recommendations.append("🚨 Revisar producto manualmente antes de usar en arbitraje")
            recommendations.append("📊 Verificar fuente de datos y proceso de scraping")
        
        elif anomalies['severity'] == 'medium':
            recommendations.append("⚠️ Aplicar filtros adicionales de validación")
            recommendations.append("🔄 Reintentar scraping en próximo ciclo")
        
        elif anomalies['detected_anomalies']:
            recommendations.append("✅ Continuar con precaución adicional")
            recommendations.append("📝 Registrar en logs para monitoreo")
        
        return recommendations


class NormalizationHubAdapter:
    """
    Adaptador para hub de normalización V5 🔄
    
    Normaliza datos de productos manteniendo autonomía del sistema V5
    """
    
    def __init__(self):
        # Configuración de normalización V5
        self.brand_mappings = {
            'sams': 'samsung', 'samsumg': 'samsung', 'samsyng': 'samsung',
            'appl': 'apple', 'aple': 'apple',
            'huaw': 'huawei', 'hauwei': 'huawei',
            'xiao': 'xiaomi', 'xiomi': 'xiaomi',
            'iph': 'apple', 'iphon': 'apple',
            'gala': 'samsung', 'galxy': 'samsung'
        }
        
        self.category_mappings = {
            'smartphone': 'Smartphones',
            'telefono': 'Smartphones', 
            'celular': 'Smartphones',
            'movil': 'Smartphones',
            'tablet': 'Tablets',
            'ipad': 'Tablets',
            'notebook': 'Notebooks',
            'laptop': 'Notebooks',
            'portatil': 'Notebooks'
        }
        
        logger.info("✅ NormalizationHubAdapter V5 inicializado")
    
    def normalize_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza datos de producto 🔄
        
        Args:
            product: Datos originales del producto
            
        Returns:
            Producto normalizado
        """
        try:
            normalized = product.copy()
            
            # Normalizar marca
            if 'marca' in normalized:
                normalized['marca'] = self._normalize_brand(normalized['marca'])
            
            # Normalizar categoría
            if 'categoria' in normalized:
                normalized['categoria'] = self._normalize_category(normalized['categoria'])
            
            # Normalizar especificaciones
            normalized = self._normalize_specifications(normalized)
            
            # Limpiar campos de texto
            normalized = self._clean_text_fields(normalized)
            
            # Agregar metadatos de normalización
            normalized['_normalization_metadata'] = {
                'normalized_at': datetime.now().isoformat(),
                'version': 'v5',
                'adapters': ['brand', 'category', 'specifications', 'text_cleanup']
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"❌ Error normalizando producto: {e}")
            return product  # Retornar original si hay error
    
    def _normalize_brand(self, brand: str) -> str:
        """Normaliza nombre de marca"""
        if not brand:
            return ''
        
        brand_lower = str(brand).lower().strip()
        
        # Buscar en mapeos directos
        for key, normalized in self.brand_mappings.items():
            if key in brand_lower:
                return normalized.title()
        
        # Normalizaciones específicas
        if 'samsung' in brand_lower or 'galaxy' in brand_lower:
            return 'Samsung'
        elif 'apple' in brand_lower or 'iphone' in brand_lower:
            return 'Apple'
        elif 'huawei' in brand_lower:
            return 'Huawei'
        elif 'xiaomi' in brand_lower:
            return 'Xiaomi'
        elif 'lg' in brand_lower:
            return 'LG'
        elif 'sony' in brand_lower:
            return 'Sony'
        
        # Si no se encuentra, capitalizar apropiadamente
        return brand.title()
    
    def _normalize_category(self, category: str) -> str:
        """Normaliza categoría"""
        if not category:
            return 'General'
        
        category_lower = str(category).lower().strip()
        
        # Buscar en mapeos
        for key, normalized in self.category_mappings.items():
            if key in category_lower:
                return normalized
        
        # Capitalization apropiada
        return category.title()
    
    def _normalize_specifications(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza especificaciones técnicas"""
        
        # Normalizar almacenamiento
        if 'storage' in product:
            product['storage'] = self._normalize_storage(product['storage'])
        
        # Normalizar RAM
        if 'ram' in product:
            product['ram'] = self._normalize_ram(product['ram'])
        
        # Normalizar pantalla
        if 'screen' in product:
            product['screen'] = self._normalize_screen(product['screen'])
        
        return product
    
    def _normalize_storage(self, storage: str) -> str:
        """Normaliza especificación de almacenamiento"""
        if not storage:
            return ''
        
        storage_str = str(storage).lower()
        
        # Extraer números
        import re
        numbers = re.findall(r'\d+', storage_str)
        
        if numbers:
            value = int(numbers[0])
            
            if 'tb' in storage_str or value >= 1000:
                if value >= 1000:
                    return f"{value//1000}TB"
                return f"{value}TB"
            else:
                return f"{value}GB"
        
        return storage
    
    def _normalize_ram(self, ram: str) -> str:
        """Normaliza especificación de RAM"""
        if not ram:
            return ''
        
        ram_str = str(ram).lower()
        
        import re
        numbers = re.findall(r'\d+', ram_str)
        
        if numbers:
            value = int(numbers[0])
            return f"{value}GB"
        
        return ram
    
    def _normalize_screen(self, screen: str) -> str:
        """Normaliza especificación de pantalla"""
        if not screen:
            return ''
        
        screen_str = str(screen).lower()
        
        import re
        # Buscar medidas en pulgadas
        inch_match = re.search(r'(\d+\.?\d*)"', screen_str)
        if inch_match:
            return f"{inch_match.group(1)}\""
        
        # Buscar solo números
        numbers = re.findall(r'\d+\.?\d*', screen_str)
        if numbers:
            return f"{numbers[0]}\""
        
        return screen
    
    def _clean_text_fields(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia campos de texto"""
        text_fields = ['nombre', 'descripcion', 'marca', 'modelo']
        
        for field in text_fields:
            if field in product and product[field]:
                # Limpiar espacios múltiples
                product[field] = ' '.join(str(product[field]).split())
                
                # Remover caracteres especiales problemáticos
                product[field] = product[field].replace('\n', ' ').replace('\t', ' ')
        
        return product