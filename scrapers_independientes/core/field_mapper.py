#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 ETL Field Mapper - Sistema de Reducción y Optimización de Campos
==================================================================

Sistema inteligente de mapeo y reducción de campos para optimizar el pipeline
ETL. Reduce la cantidad de datos procesados manteniendo la información crítica
y mejorando la performance del sistema downstream.

Features:
- 🎯 Reducción inteligente de campos por retailer
- 📊 Normalización automática de nombres de campos
- 🔄 Transformaciones de datos optimizadas
- 🧹 Limpieza y validación automática
- 📈 Optimización para análisis downstream
- 🏷️ Categorización automática de productos

Author: Portable Orchestrator Team
Version: 5.0.0
"""

import sys
import io
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import logging

# Forzar soporte UTF-8 y emojis
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)

@dataclass
class FieldMapping:
    """🗺️ Mapeo de campo con transformaciones"""
    source_field: str
    target_field: str
    required: bool = False
    data_type: str = "string"  # string, float, int, bool, list
    transformations: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    default_value: Any = None

@dataclass
class RetailerFieldConfig:
    """🏪 Configuración de campos específica por retailer"""
    retailer: str
    priority_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_mappings: Dict[str, FieldMapping] = field(default_factory=dict)
    custom_transformations: Dict[str, str] = field(default_factory=dict)

class ETLFieldMapper:
    """
    📊 ETL Field Mapper - Optimizador de Campos para ETL
    
    Sistema profesional de reducción y optimización de campos que:
    
    🎯 **REDUCCIÓN INTELIGENTE:**
    - Mantiene solo campos críticos para análisis
    - Elimina campos redundantes o de baja calidad
    - Prioriza campos con mayor valor analítico
    - Optimiza tamaño de datos para storage
    
    🔄 **NORMALIZACIÓN:**
    - Estandariza nombres de campos entre retailers
    - Aplica transformaciones de datos consistentes
    - Convierte tipos de datos apropiadamente
    - Limpia y valida datos automáticamente
    
    📈 **OPTIMIZACIÓN ETL:**
    - Reduce tiempo de procesamiento downstream
    - Minimiza uso de memoria y storage
    - Mejora performance de queries analíticas
    - Facilita integración con sistemas ML
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        🚀 Inicializar ETL Field Mapper
        
        Args:
            config_path: Ruta opcional al archivo de configuración
        """
        self.config_path = config_path
        self.retailer_configs: Dict[str, RetailerFieldConfig] = {}
        
        # Campos universales críticos (presentes en todos los retailers)
        self.universal_critical_fields = {
            'nombre',           # Nombre del producto
            'precio_final',     # Precio efectivo más bajo
            'marca',           # Marca normalizada
            'categoria',       # Categoría normalizada
            'retailer',        # Retailer source
            'link',            # URL del producto
            'disponible',      # Disponibilidad
            'sku',             # SKU/ID único
            'timestamp'        # Momento de extracción
        }
        
        # Campos opcionales de valor (se incluyen si están disponibles)
        self.universal_optional_fields = {
            'precio_normal',    # Precio normal
            'precio_oferta',    # Precio en oferta
            'precio_tarjeta',   # Precio con tarjeta
            'descuento_pct',    # Porcentaje de descuento
            'rating',           # Rating promedio
            'reviews_count',    # Cantidad de reviews
            'imagen_url',       # URL de imagen principal
            'marca_original',   # Marca sin normalizar
            'modelo',           # Modelo del producto
            'especificaciones'  # Specs técnicas resumidas
        }
        
        # Patrones de limpieza comunes
        self.cleaning_patterns = {
            'precio': re.compile(r'[^\d.,]'),
            'nombre': re.compile(r'\s+'),
            'marca': re.compile(r'[^\w\s-]'),
            'whitespace': re.compile(r'\s+')
        }
        
        # Inicializar configuraciones por defecto
        self._initialize_default_configs()
        
        logger.info("📊 ETL Field Mapper inicializado correctamente")
    
    def _initialize_default_configs(self) -> None:
        """⚙️ Inicializar configuraciones por defecto para retailers chilenos"""
        
        # Configuración para Ripley
        ripley_config = RetailerFieldConfig(
            retailer="ripley",
            priority_fields=[
                'nombre', 'precio_tarjeta', 'precio_normal', 'marca',
                'sku', 'link', 'disponible', 'rating'
            ],
            optional_fields=[
                'precio_oferta', 'reviews_count', 'imagen_url', 
                'modelo', 'descuento_pct'
            ]
        )
        
        # Configuración para Falabella  
        falabella_config = RetailerFieldConfig(
            retailer="falabella",
            priority_fields=[
                'nombre', 'precio_normal', 'precio_oferta', 'marca',
                'sku', 'link', 'disponible'
            ],
            optional_fields=[
                'precio_tarjeta', 'rating', 'reviews_count',
                'imagen_url', 'modelo'
            ]
        )
        
        # Configuración para París
        paris_config = RetailerFieldConfig(
            retailer="paris",
            priority_fields=[
                'nombre', 'precio_normal', 'marca', 'link', 
                'disponible', 'categoria'
            ],
            optional_fields=[
                'precio_oferta', 'precio_tarjeta', 'sku',
                'imagen_url', 'rating'
            ]
        )
        
        # Configuración para Hites
        hites_config = RetailerFieldConfig(
            retailer="hites",
            priority_fields=[
                'nombre', 'precio_normal', 'marca', 'link',
                'categoria', 'disponible'
            ],
            optional_fields=[
                'precio_oferta', 'sku', 'imagen_url', 'rating'
            ]
        )
        
        # Configuración para AbcDin
        abcdin_config = RetailerFieldConfig(
            retailer="abcdin",
            priority_fields=[
                'nombre', 'precio_normal', 'marca', 'link',
                'disponible', 'categoria'
            ],
            optional_fields=[
                'precio_oferta', 'sku', 'imagen_url'
            ]
        )
        
        # Configuración para MercadoLibre
        mercadolibre_config = RetailerFieldConfig(
            retailer="mercadolibre",
            priority_fields=[
                'nombre', 'precio_normal', 'link', 'disponible',
                'rating', 'reviews_count'
            ],
            optional_fields=[
                'marca', 'sku', 'imagen_url', 'categoria'
            ]
        )
        
        # Registrar configuraciones
        self.retailer_configs = {
            'ripley': ripley_config,
            'falabella': falabella_config,
            'paris': paris_config,
            'hites': hites_config,
            'abcdin': abcdin_config,
            'mercadolibre': mercadolibre_config
        }
        
        logger.debug(f"⚙️ Configuraciones inicializadas para {len(self.retailer_configs)} retailers")
    
    def reduce_fields(self, product_data: Dict[str, Any], 
                     retailer: str) -> Dict[str, Any]:
        """
        🎯 Reducir campos de producto para optimización ETL
        
        Args:
            product_data: Datos crudos del producto
            retailer: Nombre del retailer
            
        Returns:
            Dict con campos reducidos y optimizados
        """
        try:
            if not product_data:
                return {}
            
            # Obtener configuración del retailer
            config = self.retailer_configs.get(
                retailer.lower(), 
                self._get_default_config(retailer)
            )
            
            # Aplicar reducción inteligente
            reduced_data = self._apply_field_reduction(product_data, config)
            
            # Normalizar y limpiar datos
            normalized_data = self._normalize_data(reduced_data, retailer)
            
            # Calcular campos derivados
            enriched_data = self._calculate_derived_fields(normalized_data)
            
            # Validar resultado final
            validated_data = self._validate_final_data(enriched_data, retailer)
            
            return validated_data
            
        except Exception as e:
            logger.warning(f"⚠️ Error reduciendo campos para {retailer}: {str(e)}")
            # Fallback: aplicar reducción básica
            return self._apply_basic_reduction(product_data, retailer)
    
    def _apply_field_reduction(self, data: Dict[str, Any], 
                             config: RetailerFieldConfig) -> Dict[str, Any]:
        """🔪 Aplicar reducción de campos según configuración"""
        reduced = {}
        
        # Incluir campos prioritarios
        for field in config.priority_fields:
            if field in data and data[field] is not None:
                reduced[field] = data[field]
        
        # Incluir campos opcionales si están disponibles y tienen valor
        for field in config.optional_fields:
            if field in data and data[field] is not None:
                value = data[field]
                
                # Validar que el valor tenga contenido útil
                if self._is_valuable_field_value(value):
                    reduced[field] = value
        
        # Incluir campos universales críticos siempre
        for field in self.universal_critical_fields:
            if field in data and data[field] is not None:
                reduced[field] = data[field]
        
        return reduced
    
    def _normalize_data(self, data: Dict[str, Any], retailer: str) -> Dict[str, Any]:
        """🧹 Normalizar y limpiar datos"""
        normalized = {}
        
        for field, value in data.items():
            try:
                # Aplicar limpieza específica por tipo de campo
                if field.startswith('precio_'):
                    normalized[field] = self._normalize_price(value)
                elif field == 'nombre':
                    normalized[field] = self._normalize_name(value)
                elif field == 'marca':
                    normalized[field] = self._normalize_brand(value)
                elif field in ['rating']:
                    normalized[field] = self._normalize_numeric(value, min_val=0, max_val=5)
                elif field in ['reviews_count']:
                    normalized[field] = self._normalize_numeric(value, min_val=0)
                elif field == 'disponible':
                    normalized[field] = self._normalize_boolean(value)
                else:
                    # Limpieza general
                    normalized[field] = self._normalize_generic(value)
                    
            except Exception as e:
                logger.debug(f"⚠️ Error normalizando campo {field}: {str(e)}")
                # Mantener valor original si falla la normalización
                normalized[field] = value
        
        # Agregar metadatos de procesamiento
        normalized['_processed_at'] = datetime.now().isoformat()
        normalized['_etl_version'] = '5.0.0'
        
        return normalized
    
    def _calculate_derived_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """📈 Calcular campos derivados optimizados para análisis"""
        enriched = data.copy()
        
        try:
            # Calcular precio final (más bajo disponible)
            prices = []
            for price_field in ['precio_tarjeta', 'precio_oferta', 'precio_normal']:
                price = data.get(price_field)
                if isinstance(price, (int, float)) and price > 0:
                    prices.append(price)
            
            if prices:
                enriched['precio_final'] = min(prices)
                enriched['precio_maximo'] = max(prices)
                
                # Calcular descuento si hay precio normal
                precio_normal = data.get('precio_normal')
                if precio_normal and enriched['precio_final'] < precio_normal:
                    descuento = ((precio_normal - enriched['precio_final']) / precio_normal) * 100
                    enriched['descuento_pct'] = round(descuento, 1)
            
            # Calcular score de calidad del producto
            quality_score = self._calculate_quality_score(data)
            if quality_score > 0:
                enriched['quality_score'] = quality_score
            
            # Extraer características técnicas principales
            specs = self._extract_key_specifications(data.get('nombre', ''))
            if specs:
                enriched['especificaciones'] = specs
            
            # Generar hash único del producto para deduplicación
            product_hash = self._generate_product_hash(data)
            enriched['product_hash'] = product_hash
            
        except Exception as e:
            logger.debug(f"⚠️ Error calculando campos derivados: {str(e)}")
        
        return enriched
    
    def _validate_final_data(self, data: Dict[str, Any], retailer: str) -> Dict[str, Any]:
        """✅ Validar datos finales"""
        validated = {}
        errors = []
        
        # Validar campos críticos
        critical_fields = ['nombre', 'retailer']
        for field in critical_fields:
            if field not in data or not data[field]:
                errors.append(f"Campo crítico faltante: {field}")
            else:
                validated[field] = data[field]
        
        # Validar al menos un precio
        price_fields = ['precio_final', 'precio_normal', 'precio_oferta', 'precio_tarjeta']
        has_price = any(
            field in data and isinstance(data[field], (int, float)) and data[field] > 0
            for field in price_fields
        )
        
        if not has_price:
            errors.append("No hay precio válido")
        
        # Copiar campos validados
        for field, value in data.items():
            if field not in validated and self._is_valid_field_value(value):
                validated[field] = value
        
        # Agregar información de validación
        if errors:
            validated['_validation_errors'] = errors
        
        # Asegurar que retailer esté presente
        if 'retailer' not in validated:
            validated['retailer'] = retailer
        
        return validated
    
    # ==========================================
    # MÉTODOS DE NORMALIZACIÓN ESPECÍFICOS
    # ==========================================
    
    def _normalize_price(self, value: Any) -> Optional[float]:
        """💰 Normalizar campo de precio"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value) if value > 0 else None
            
            if isinstance(value, str):
                # Limpiar precio string
                price_clean = re.sub(r'[^\d.,]', '', value)
                price_clean = price_clean.replace(',', '')
                
                if price_clean:
                    price_float = float(price_clean)
                    return price_float if price_float > 0 else None
            
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _normalize_name(self, value: Any) -> Optional[str]:
        """📝 Normalizar nombre de producto"""
        if not value or not isinstance(value, str):
            return None
        
        # Limpiar espacios excesivos
        name = re.sub(self.cleaning_patterns['nombre'], ' ', value)
        name = name.strip()
        
        # Validar longitud mínima
        if len(name) < 3:
            return None
        
        # Capitalizar apropiadamente
        name = name.title()
        
        # Limpiar caracteres especiales problemáticos
        name = re.sub(r'[^\w\s\-.,()&/]', '', name)
        
        return name[:200]  # Truncar si es muy largo
    
    def _normalize_brand(self, value: Any) -> Optional[str]:
        """🏷️ Normalizar marca"""
        if not value or not isinstance(value, str):
            return None
        
        # Limpiar y normalizar marca
        brand = re.sub(self.cleaning_patterns['marca'], '', value).strip().upper()

        # Limpiar sufijos corporativos comunes
        corporate_suffixes = [' S.A.', ' S A', ' LIMITADA', ' LTDA', ' CHILE']
        for suffix in corporate_suffixes:
            if brand.endswith(suffix):
                brand = brand[:-len(suffix)]

        # Mapeo de marcas comunes (más extenso)
        brand_mappings = {
            'SAMSUNG': 'SAMSUNG',
            'SAMS': 'SAMSUNG',
            'APPLE': 'APPLE',
            'IPHONE': 'APPLE',
            'MOTOROLA': 'MOTOROLA',
            'HUAWEI': 'HUAWEI',
            'XIAOMI': 'XIAOMI',
            'REDMI': 'XIAOMI',
            'LG': 'LG',
            'SONY': 'SONY',
            'LENOVO': 'LENOVO',
            'HP': 'HP',
            'HEWLETT-PACKARD': 'HP',
            'DELL': 'DELL',
            'ASUS': 'ASUS',
            'ACER': 'ACER',
            'NOKIA': 'NOKIA',
            'OPPO': 'OPPO',
            'VIVO': 'VIVO',
            'REALME': 'REALME',
            'GOOGLE': 'GOOGLE',
            'PIXEL': 'GOOGLE',
        }
        
        # Aplicar mapeo si coincide
        for key, mapped_brand in brand_mappings.items():
            if key in brand:
                return mapped_brand
        
        return brand[:50] if brand else None
    
    def _normalize_numeric(self, value: Any, min_val: Optional[float] = None,
                         max_val: Optional[float] = None) -> Optional[float]:
        """🔢 Normalizar campo numérico"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                num_value = float(value)
            elif isinstance(value, str):
                # Extraer primer número del string
                match = re.search(r'(\d+(?:\.\d+)?)', value)
                if not match:
                    return None
                num_value = float(match.group(1))
            else:
                return None
            
            # Aplicar límites si están definidos
            if min_val is not None and num_value < min_val:
                return None
            if max_val is not None and num_value > max_val:
                return None
            
            return num_value
            
        except (ValueError, TypeError):
            return None
    
    def _normalize_boolean(self, value: Any) -> bool:
        """✅ Normalizar campo booleano"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            return value_lower in ['true', '1', 'yes', 'si', 'disponible', 'available', 'in stock']
        
        if isinstance(value, (int, float)):
            return value > 0
        
        return False
    
    def _normalize_generic(self, value: Any) -> Any:
        """🧹 Normalización genérica para otros campos"""
        if isinstance(value, str):
            # Limpiar espacios excesivos
            cleaned = re.sub(self.cleaning_patterns['whitespace'], ' ', value)
            return cleaned.strip() if cleaned.strip() else None
        
        return value
    
    # ==========================================
    # MÉTODOS DE UTILIDAD Y VALIDACIÓN
    # ==========================================
    
    def _is_valuable_field_value(self, value: Any) -> bool:
        """💎 Verificar si un valor de campo tiene valor analítico"""
        if value is None:
            return False
        
        if isinstance(value, str):
            # Strings muy cortos o solo espacios no son valiosos
            cleaned = value.strip()
            if len(cleaned) < 2:
                return False
            
            # Strings que son solo caracteres especiales
            if re.match(r'^[^\w\s]+$', cleaned):
                return False
            
            return True
        
        if isinstance(value, (int, float)):
            # Números negativos o cero en contexto de precios
            return value > 0
        
        if isinstance(value, (list, dict)):
            return len(value) > 0
        
        return True
    
    def _is_valid_field_value(self, value: Any) -> bool:
        """✅ Verificar si un valor de campo es válido"""
        if value is None:
            return False
        
        if isinstance(value, str) and not value.strip():
            return False
        
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        
        return True
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """📊 Calcular score de calidad del producto"""
        score = 0.0
        max_score = 100.0
        
        # Completeness score (40 puntos)
        required_fields = ['nombre', 'precio_final', 'marca', 'link']
        optional_fields = ['rating', 'reviews_count', 'imagen_url', 'disponible']
        
        completeness = 0
        for field in required_fields:
            if field in data and self._is_valid_field_value(data[field]):
                completeness += 10
        
        for field in optional_fields:
            if field in data and self._is_valid_field_value(data[field]):
                completeness += 2.5
        
        score += min(40, completeness)
        
        # Rating quality (30 puntos)
        rating = data.get('rating')
        reviews_count = data.get('reviews_count')
        
        if rating and isinstance(rating, (int, float)):
            if rating >= 4.0:
                score += 20
            elif rating >= 3.0:
                score += 10
            elif rating >= 2.0:
                score += 5
        
        if reviews_count and isinstance(reviews_count, (int, float)):
            if reviews_count >= 100:
                score += 10
            elif reviews_count >= 10:
                score += 5
        
        # Data quality (30 puntos)
        nombre = data.get('nombre', '')
        if len(nombre) > 10:  # Nombre descriptivo
            score += 10
        
        marca = data.get('marca')
        if marca and len(marca) > 2:  # Marca válida
            score += 10
        
        # Disponibilidad
        if data.get('disponible', False):
            score += 10
        
        return round(score, 1)
    
    def _extract_key_specifications(self, product_name: str) -> Dict[str, Any]:
        """🔧 Extraer especificaciones técnicas clave del nombre"""
        specs = {}
        
        if not product_name:
            return specs
        
        name_upper = product_name.upper()
        
        # Extraer almacenamiento
        storage_patterns = [
            r'(\d+)\s*GB',
            r'(\d+)\s*TB',
            r'(\d+)\s*G\b'
        ]
        
        for pattern in storage_patterns:
            match = re.search(pattern, name_upper)
            if match:
                value = int(match.group(1))
                unit = 'TB' if 'TB' in match.group(0) else 'GB'
                specs['storage'] = f"{value}{unit}"
                break
        
        # Extraer RAM
        ram_patterns = [
            r'(\d+)\s*GB\s*RAM',
            r'RAM\s*(\d+)\s*GB',
            r'(\d+)\s*G\s*RAM'
        ]
        
        for pattern in ram_patterns:
            match = re.search(pattern, name_upper)
            if match:
                specs['ram'] = f"{match.group(1)}GB"
                break
        
        # Extraer tamaño de pantalla
        screen_patterns = [
            r'(\d+\.?\d*)\s*["\']',
            r'(\d+\.?\d*)\s*INCH',
            r'(\d+\.?\d*)\s*PULGADAS'
        ]
        
        for pattern in screen_patterns:
            match = re.search(pattern, name_upper)
            if match:
                specs['screen_size'] = f'{match.group(1)}"'
                break
        
        return specs
    
    def _generate_product_hash(self, data: Dict[str, Any]) -> str:
        """🔒 Generar hash único del producto para deduplicación"""
        # Usar campos clave para generar hash
        key_fields = ['nombre', 'marca', 'precio_final', 'retailer']
        hash_string = ""
        
        for field in key_fields:
            value = data.get(field)
            if value:
                hash_string += str(value).lower().strip()
        
        if not hash_string:
            # Fallback: usar timestamp
            hash_string = f"product_{datetime.now().isoformat()}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()[:12]
    
    def _get_default_config(self, retailer: str) -> RetailerFieldConfig:
        """⚙️ Obtener configuración por defecto para retailer desconocido"""
        return RetailerFieldConfig(
            retailer=retailer,
            priority_fields=['nombre', 'precio_normal', 'marca', 'link', 'disponible'],
            optional_fields=['precio_oferta', 'sku', 'imagen_url', 'rating']
        )
    
    def _apply_basic_reduction(self, data: Dict[str, Any], retailer: str) -> Dict[str, Any]:
        """🔪 Aplicar reducción básica como fallback"""
        basic_fields = [
            'nombre', 'precio_normal', 'precio_oferta', 'precio_tarjeta',
            'marca', 'link', 'disponible', 'retailer', 'sku'
        ]
        
        reduced = {}
        for field in basic_fields:
            if field in data and data[field] is not None:
                reduced[field] = data[field]
        
        # Asegurar retailer
        reduced['retailer'] = retailer
        reduced['_processed_at'] = datetime.now().isoformat()
        
        return reduced
    
    # ==========================================
    # MÉTODOS DE ANÁLISIS Y REPORTING
    # ==========================================
    
    def get_reduction_stats(self, original_data: Dict[str, Any],
                           reduced_data: Dict[str, Any]) -> Dict[str, Any]:
        """📊 Obtener estadísticas de reducción"""
        original_size = len(json.dumps(original_data, ensure_ascii=False))
        reduced_size = len(json.dumps(reduced_data, ensure_ascii=False))
        
        return {
            'original_fields': len(original_data),
            'reduced_fields': len(reduced_data),
            'fields_removed': len(original_data) - len(reduced_data),
            'reduction_ratio': 1 - (len(reduced_data) / max(1, len(original_data))),
            'size_reduction_bytes': original_size - reduced_size,
            'size_reduction_ratio': 1 - (reduced_size / max(1, original_size)),
            'removed_fields': list(set(original_data.keys()) - set(reduced_data.keys()))
        }
    
    def analyze_field_usage(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """📈 Analizar uso de campos en conjunto de productos"""
        if not products:
            return {}
        
        field_counts = {}
        total_products = len(products)
        
        # Contar frecuencia de cada campo
        for product in products:
            for field, value in product.items():
                if field not in field_counts:
                    field_counts[field] = 0
                
                if self._is_valid_field_value(value):
                    field_counts[field] += 1
        
        # Calcular estadísticas
        field_stats = {}
        for field, count in field_counts.items():
            coverage = count / total_products
            field_stats[field] = {
                'count': count,
                'coverage': coverage,
                'is_critical': coverage > 0.8,  # >80% de cobertura
                'is_optional': 0.2 < coverage <= 0.8,  # 20-80% cobertura
                'is_rare': coverage <= 0.2  # <=20% cobertura
            }
        
        return {
            'total_products': total_products,
            'total_unique_fields': len(field_counts),
            'field_statistics': field_stats,
            'critical_fields': [f for f, stats in field_stats.items() if stats['is_critical']],
            'optional_fields': [f for f, stats in field_stats.items() if stats['is_optional']],
            'rare_fields': [f for f, stats in field_stats.items() if stats['is_rare']]
        }

# ==========================================
# FUNCIONES DE UTILIDAD
# ==========================================

def create_field_mapper(config_path: Optional[str] = None) -> ETLFieldMapper:
    """
    🚀 Crear instancia de ETL Field Mapper
    
    Args:
        config_path: Ruta opcional al archivo de configuración
        
    Returns:
        ETLFieldMapper: Instancia configurada del mapper
    """
    return ETLFieldMapper(config_path=config_path)

def reduce_product_batch(products: List[Dict[str, Any]], 
                        retailer: str,
                        mapper: Optional[ETLFieldMapper] = None) -> List[Dict[str, Any]]:
    """
    📦 Reducir lote de productos de forma eficiente
    
    Args:
        products: Lista de productos crudos
        retailer: Nombre del retailer
        mapper: Instancia del mapper (se crea una si no se proporciona)
        
    Returns:
        Lista de productos con campos reducidos
    """
    if not products:
        return []
    
    if mapper is None:
        mapper = create_field_mapper()
    
    reduced_products = []
    
    for product in products:
        try:
            reduced_product = mapper.reduce_fields(product, retailer)
            if reduced_product:  # Solo agregar si la reducción fue exitosa
                reduced_products.append(reduced_product)
        except Exception as e:
            logger.warning(f"⚠️ Error reduciendo producto: {str(e)}")
            continue
    
    return reduced_products

def analyze_batch_reduction(original_products: List[Dict[str, Any]],
                          reduced_products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    📊 Analizar reducción de un lote de productos
    
    Args:
        original_products: Productos originales
        reduced_products: Productos después de reducción
        
    Returns:
        Dict con estadísticas de la reducción
    """
    if not original_products or not reduced_products:
        return {}
    
    # Calcular estadísticas agregadas
    original_total_fields = sum(len(p) for p in original_products)
    reduced_total_fields = sum(len(p) for p in reduced_products)
    
    original_size = sum(
        len(json.dumps(p, ensure_ascii=False)) for p in original_products
    )
    reduced_size = sum(
        len(json.dumps(p, ensure_ascii=False)) for p in reduced_products
    )
    
    return {
        'original_products': len(original_products),
        'reduced_products': len(reduced_products),
        'products_lost': len(original_products) - len(reduced_products),
        'avg_fields_before': original_total_fields / len(original_products),
        'avg_fields_after': reduced_total_fields / len(reduced_products) if reduced_products else 0,
        'total_field_reduction': original_total_fields - reduced_total_fields,
        'field_reduction_ratio': 1 - (reduced_total_fields / max(1, original_total_fields)),
        'size_reduction_bytes': original_size - reduced_size,
        'size_reduction_ratio': 1 - (reduced_size / max(1, original_size)),
        'efficiency_score': (reduced_total_fields / max(1, original_total_fields)) * 
                           (len(reduced_products) / max(1, len(original_products)))
    }

if __name__ == "__main__":
    """📊 Ejecutar análisis desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="📊 ETL Field Mapper")
    parser.add_argument('--analyze-file', help='Archivo JSON con productos para analizar')
    parser.add_argument('--retailer', default='test', help='Nombre del retailer')
    parser.add_argument('--output', help='Archivo de salida para resultados')
    
    args = parser.parse_args()
    
    if args.analyze_file:
        try:
            with open(args.analyze_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            mapper = create_field_mapper()
            
            if isinstance(products, list):
                # Analizar lote de productos
                reduced_products = reduce_product_batch(products, args.retailer, mapper)
                analysis = analyze_batch_reduction(products, reduced_products)
                
                print("📊 ANÁLISIS DE REDUCCIÓN ETL")
                print(f"   Productos originales: {analysis.get('original_products', 0)}")
                print(f"   Productos procesados: {analysis.get('reduced_products', 0)}")
                print(f"   Reducción de campos: {analysis.get('field_reduction_ratio', 0):.1%}")
                print(f"   Reducción de tamaño: {analysis.get('size_reduction_ratio', 0):.1%}")
                print(f"   Score de eficiencia: {analysis.get('efficiency_score', 0):.3f}")
                
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump(reduced_products, f, indent=2, ensure_ascii=False)
                    print(f"💾 Resultados guardados en: {args.output}")
            
            else:
                # Analizar producto individual
                reduced = mapper.reduce_fields(products, args.retailer)
                stats = mapper.get_reduction_stats(products, reduced)
                
                print("📊 ANÁLISIS DE PRODUCTO INDIVIDUAL")
                print(f"   Campos originales: {stats['original_fields']}")
                print(f"   Campos finales: {stats['reduced_fields']}")
                print(f"   Campos removidos: {stats['fields_removed']}")
                print(f"   Ratio de reducción: {stats['reduction_ratio']:.1%}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        parser.print_help()