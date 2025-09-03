# -*- coding: utf-8 -*-
"""
ML Normalization - Sistema V5 Autónomo
======================================
Sistema de normalización simplificado para operación autónoma.
Compatible con emojis y optimizado para el sistema V5.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
import hashlib
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NormalizationResult:
    """Resultado de normalización con soporte de emojis 📊"""
    skus_generated: int = 0
    matches_found: int = 0
    opportunities: List[Dict[str, Any]] = None
    alerts: List[Dict[str, Any]] = None
    success: bool = True
    error_message: str = ""
    
    def __post_init__(self):
        if self.opportunities is None:
            self.opportunities = []
        if self.alerts is None:
            self.alerts = []

class SimpleNormalizationHub:
    """
    Hub de normalización simplificado para V5 🧠
    
    Características:
    - 📝 Normalización básica de marcas y modelos
    - 🔍 Detección de productos similares
    - 🎯 Generación de SKUs internos
    - 📊 Análisis de oportunidades básicas
    - 🚨 Sistema de alertas integrado
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Inicializar hub con configuración 🚀"""
        self.config = config or {}
        self.brand_normalizer = SimpleBrandNormalizer()
        self.sku_generator = SimpleSkuGenerator()
        self.opportunity_detector = SimpleOpportunityDetector()
        
        logger.info("🧠 SimpleNormalizationHub inicializado correctamente")
    
    async def process_batch(self, products: List[Dict[str, Any]]) -> NormalizationResult:
        """
        Procesar lote de productos con normalización completa 📊
        
        Args:
            products: Lista de productos a normalizar
            
        Returns:
            Resultado de normalización con métricas
        """
        result = NormalizationResult()
        
        try:
            if not products:
                logger.warning("📝 No hay productos para procesar")
                return result
            
            logger.info(f"🔄 Procesando {len(products)} productos...")
            
            # Paso 1: Normalizar marcas y modelos
            normalized_products = []
            for product in products:
                normalized = await self._normalize_product(product)
                normalized_products.append(normalized)
            
            # Paso 2: Generar SKUs únicos
            sku_results = await self._generate_skus(normalized_products)
            result.skus_generated = sku_results['generated_count']
            
            # Paso 3: Detectar matches entre retailers
            match_results = await self._find_matches(normalized_products)
            result.matches_found = match_results['match_count']
            
            # Paso 4: Detectar oportunidades de arbitraje
            opportunities = await self._detect_opportunities(normalized_products, match_results['matches'])
            result.opportunities = opportunities
            
            # Paso 5: Generar alertas
            alerts = await self._generate_alerts(normalized_products, opportunities)
            result.alerts = alerts
            
            result.success = True
            
            logger.info(f"✅ Normalización completada: {result.skus_generated} SKUs, {result.matches_found} matches, {len(result.opportunities)} oportunidades")
            
        except Exception as e:
            logger.error(f"❌ Error en normalización: {e}")
            result.success = False
            result.error_message = str(e)
        
        return result
    
    async def _normalize_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar un producto individual 🔧"""
        normalized = product.copy()
        
        # Normalizar marca
        brand = product.get('marca', '') or product.get('brand', '')
        if brand:
            normalized['marca_normalizada'] = self.brand_normalizer.normalize(brand)
        
        # Normalizar nombre/modelo
        name = product.get('nombre', '') or product.get('titulo', '')
        if name:
            normalized['modelo_normalizado'] = self._normalize_model(name)
            normalized['categoria_inferida'] = self._infer_category(name)
        
        # Agregar timestamp de normalización
        normalized['fecha_normalizacion'] = datetime.now().isoformat()
        
        return normalized
    
    async def _generate_skus(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar SKUs únicos para productos 📋"""
        generated_count = 0
        
        for product in products:
            sku = self.sku_generator.generate_sku(product)
            if sku:
                product['sku_interno_v5'] = sku
                generated_count += 1
        
        return {'generated_count': generated_count}
    
    async def _find_matches(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Encontrar productos similares entre retailers 🎯"""
        matches = []
        match_count = 0
        
        # Agrupar por marca y modelo normalizado
        product_groups = {}
        for product in products:
            key = f"{product.get('marca_normalizada', '')}-{product.get('modelo_normalizado', '')}"
            if key not in product_groups:
                product_groups[key] = []
            product_groups[key].append(product)
        
        # Encontrar grupos con múltiples retailers
        for key, group in product_groups.items():
            if len(group) > 1:
                retailers = set(p.get('retailer', '') for p in group)
                if len(retailers) > 1:
                    matches.append({
                        'match_key': key,
                        'products': group,
                        'retailer_count': len(retailers),
                        'confidence': 0.8  # Confianza básica
                    })
                    match_count += len(group)
        
        return {'matches': matches, 'match_count': match_count}
    
    async def _detect_opportunities(self, products: List[Dict[str, Any]], matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detectar oportunidades de arbitraje 💰"""
        opportunities = []
        
        for match in matches:
            group_products = match['products']
            prices = []
            
            for product in group_products:
                price = self._extract_best_price(product)
                if price > 0:
                    prices.append({
                        'product': product,
                        'price': price,
                        'retailer': product.get('retailer', '')
                    })
            
            if len(prices) >= 2:
                # Ordenar por precio
                prices.sort(key=lambda x: x['price'])
                lowest = prices[0]
                highest = prices[-1]
                
                # Calcular diferencia
                price_diff = highest['price'] - lowest['price']
                diff_pct = (price_diff / lowest['price']) * 100
                
                # Solo considerar oportunidades significativas (>5%)
                if diff_pct > 5:
                    opportunities.append({
                        'tipo': 'arbitraje_precio',
                        'producto_barato': lowest,
                        'producto_caro': highest,
                        'diferencia_clp': price_diff,
                        'diferencia_pct': diff_pct,
                        'confianza': match['confidence'],
                        'timestamp': datetime.now().isoformat()
                    })
        
        return opportunities
    
    async def _generate_alerts(self, products: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generar alertas basadas en productos y oportunidades 🚨"""
        alerts = []
        
        # Alerta por oportunidades de alto valor
        high_value_opps = [o for o in opportunities if o.get('diferencia_clp', 0) > 50000]
        if high_value_opps:
            alerts.append({
                'tipo': 'oportunidad_alto_valor',
                'mensaje': f'🔥 Detectadas {len(high_value_opps)} oportunidades de arbitraje >$50k',
                'cantidad': len(high_value_opps),
                'severidad': 'high',
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta por productos sin precio
        no_price_products = [p for p in products if self._extract_best_price(p) == 0]
        if no_price_products:
            alerts.append({
                'tipo': 'productos_sin_precio',
                'mensaje': f'⚠️ {len(no_price_products)} productos sin precio válido',
                'cantidad': len(no_price_products),
                'severidad': 'medium',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _normalize_model(self, name: str) -> str:
        """Normalizar nombre/modelo de producto 🔧"""
        if not name:
            return ""
        
        # Limpiar texto básico
        model = name.lower().strip()
        
        # Remover palabras comunes
        stopwords = ['smartphone', 'celular', 'notebook', 'laptop', 'tablet', 'tv', 'televisor']
        for word in stopwords:
            model = model.replace(word, ' ')
        
        # Limpiar espacios múltiples
        model = re.sub(r'\s+', ' ', model).strip()
        
        return model[:50]  # Limitar longitud
    
    def _infer_category(self, name: str) -> str:
        """Inferir categoría básica del nombre 📱"""
        if not name:
            return "sin_categoria"
        
        name_lower = name.lower()
        
        # Categorías básicas
        if any(word in name_lower for word in ['iphone', 'samsung', 'huawei', 'xiaomi', 'smartphone', 'celular']):
            return "celulares"
        elif any(word in name_lower for word in ['notebook', 'laptop', 'macbook', 'thinkpad']):
            return "computadores"
        elif any(word in name_lower for word in ['tablet', 'ipad']):
            return "tablets"
        elif any(word in name_lower for word in ['tv', 'televisor', 'smart tv']):
            return "televisores"
        else:
            return "otros"
    
    def _extract_best_price(self, product: Dict[str, Any]) -> float:
        """Extraer el mejor precio disponible 💰"""
        price_fields = [
            'precio_min_num', 'precio_oferta_num', 'precio_tarjeta_num', 
            'precio_normal_num', 'precio', 'normal_num', 'oferta_num'
        ]
        
        valid_prices = []
        for field in price_fields:
            price = product.get(field, 0)
            if isinstance(price, (int, float)) and price > 0:
                valid_prices.append(price)
        
        return min(valid_prices) if valid_prices else 0.0
    
    async def close(self):
        """Cerrar conexiones del hub 🔚"""
        logger.info("🔚 SimpleNormalizationHub cerrado")
        pass  # No hay conexiones que cerrar en la versión simplificada

class SimpleBrandNormalizer:
    """Normalizador simple de marcas 🏷️"""
    
    def __init__(self):
        # Mapeo básico de marcas comunes
        self.brand_mapping = {
            'samsung': ['samsung', 'samsumg', 'samung'],
            'apple': ['apple', 'aple', 'iphone', 'ipad', 'macbook'],
            'huawei': ['huawei', 'hawuei', 'huwei'],
            'xiaomi': ['xiaomi', 'xiami', 'redmi'],
            'lg': ['lg', 'l.g'],
            'sony': ['sony', 'sony ericsson'],
            'hp': ['hp', 'hewlett', 'hewlett-packard'],
            'dell': ['dell', 'del'],
            'lenovo': ['lenovo', 'lenovvo', 'thinkpad'],
            'asus': ['asus', 'azus'],
            'acer': ['acer', 'acer aspire'],
        }
    
    def normalize(self, brand: str) -> str:
        """Normalizar marca 🏷️"""
        if not brand:
            return ""
        
        brand_lower = brand.lower().strip()
        
        # Buscar en mapeo
        for normalized, variants in self.brand_mapping.items():
            if any(variant in brand_lower for variant in variants):
                return normalized
        
        # Si no se encuentra, devolver limpio
        return re.sub(r'[^a-zA-Z0-9\s]', '', brand_lower)[:20]

class SimpleSkuGenerator:
    """Generador simple de SKUs internos 📋"""
    
    def generate_sku(self, product: Dict[str, Any]) -> str:
        """
        Generar SKU interno único
        Formato: V5-{RETAILER}-{BRAND}-{HASH}
        """
        retailer = (product.get('retailer', '') or 'UNK')[:3].upper()
        brand = (product.get('marca_normalizada', '') or 'UNK')[:4].upper()
        
        # Crear hash único basado en nombre + retailer
        name = product.get('nombre', '') or product.get('titulo', '')
        unique_string = f"{retailer}-{name}-{brand}"
        hash_part = hashlib.md5(unique_string.encode()).hexdigest()[:8].upper()
        
        return f"V5-{retailer}-{brand}-{hash_part}"

class SimpleOpportunityDetector:
    """Detector simple de oportunidades 💰"""
    
    def __init__(self):
        self.min_price_diff_pct = 5  # 5% mínimo
        self.min_absolute_diff = 5000  # CLP 5,000 mínimo
    
    def detect_opportunities(self, product_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detectar oportunidades simples de arbitraje 💰"""
        opportunities = []
        
        for match in product_matches:
            products = match.get('products', [])
            if len(products) < 2:
                continue
            
            # Extraer precios válidos
            price_data = []
            for product in products:
                price = self._get_best_price(product)
                if price > 0:
                    price_data.append({
                        'product': product,
                        'price': price,
                        'retailer': product.get('retailer', '')
                    })
            
            if len(price_data) >= 2:
                # Encontrar min/max
                price_data.sort(key=lambda x: x['price'])
                cheapest = price_data[0]
                most_expensive = price_data[-1]
                
                diff_abs = most_expensive['price'] - cheapest['price']
                diff_pct = (diff_abs / cheapest['price']) * 100
                
                if (diff_pct >= self.min_price_diff_pct and 
                    diff_abs >= self.min_absolute_diff):
                    
                    opportunities.append({
                        'type': 'price_arbitrage',
                        'buy_from': cheapest,
                        'sell_to': most_expensive,
                        'profit_clp': diff_abs,
                        'profit_pct': diff_pct,
                        'confidence': match.get('confidence', 0.5)
                    })
        
        return opportunities
    
    def _get_best_price(self, product: Dict[str, Any]) -> float:
        """Obtener mejor precio de un producto 💰"""
        prices = []
        
        price_fields = ['precio_min_num', 'precio_oferta_num', 'precio_normal_num', 'precio']
        for field in price_fields:
            price = product.get(field, 0)
            if isinstance(price, (int, float)) and price > 0:
                prices.append(price)
        
        return min(prices) if prices else 0.0