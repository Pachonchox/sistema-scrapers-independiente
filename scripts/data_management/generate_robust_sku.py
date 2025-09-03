#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador Robusto de SKU Único
================================

Estrategia mejorada para generar SKUs únicos basados en:
1. Extracción inteligente de marca del nombre
2. Extracción de modelo/características clave
3. Hash del link o nombre para unicidad
4. Manejo de casos especiales (MercadoLibre sin SKU)
"""

import re
import hashlib
from typing import Dict, Optional

class RobustSKUGenerator:
    """Generador robusto de SKUs únicos"""
    
    # Marcas conocidas para mejor extracción
    KNOWN_BRANDS = [
        'SAMSUNG', 'APPLE', 'XIAOMI', 'MOTOROLA', 'HUAWEI', 'HONOR', 'OPPO', 
        'REALME', 'NOKIA', 'LG', 'SONY', 'ASUS', 'HP', 'LENOVO', 'DELL', 
        'ACER', 'MSI', 'RAZER', 'ALIENWARE', 'TOSHIBA', 'PHILIPS', 'TCL',
        'HISENSE', 'PANASONIC', 'JBL', 'BOSE', 'LOGITECH', 'CORSAIR',
        'KINGSTON', 'SANDISK', 'WESTERN', 'SEAGATE', 'CRUCIAL', 'INTEL',
        'AMD', 'NVIDIA', 'GIGABYTE', 'ASROCK', 'BIOSTAR', 'ZOTAC'
    ]
    
    # Modelos/Series comunes
    KNOWN_MODELS = [
        'GALAXY', 'IPHONE', 'REDMI', 'NOTE', 'PRO', 'PLUS', 'ULTRA', 'MAX',
        'LITE', 'MINI', 'AIR', 'MACBOOK', 'THINKPAD', 'PAVILION', 'INSPIRON',
        'VOSTRO', 'LATITUDE', 'ELITEBOOK', 'PROBOOK', 'OMEN', 'PREDATOR',
        'ROG', 'TUF', 'GAMING', 'EDGE', 'MOTO', 'PIXEL', 'XPERIA'
    ]
    
    # Especificaciones técnicas pattern
    SPECS_PATTERNS = [
        r'\d+GB',  # RAM/Storage
        r'\d+TB',
        r'\d+\.\d+"',  # Screen size
        r'\d+MP',  # Camera
        r'\d+MAH',  # Battery
        r'I\d',  # Intel series
        r'RYZEN\s?\d',  # AMD series
        r'RTX\s?\d+',  # NVIDIA
        r'GTX\s?\d+',
        r'\d+W',  # Watts
        r'5G|4G|LTE',  # Network
        r'WIFI\s?6',
        r'M\d+',  # Apple M series
        r'A\d+',  # Apple A series
    ]
    
    def __init__(self):
        # Compilar patterns para eficiencia
        self.specs_regex = re.compile('|'.join(self.SPECS_PATTERNS), re.IGNORECASE)
        
    def extract_brand(self, nombre: str, marca_field: str = None) -> str:
        """Extraer marca inteligentemente"""
        nombre_upper = nombre.upper()
        
        # 1. Buscar marcas conocidas en el nombre
        for brand in self.KNOWN_BRANDS:
            if brand in nombre_upper:
                return brand[:4]
        
        # 2. Si hay campo marca y no es genérico
        if marca_field and marca_field not in ['nan', 'LAPTOP', 'NOTEBOOK', 'CELULAR', '15', 'TABLET']:
            # Limpiar y usar primeras 4 letras
            marca_clean = re.sub(r'[^A-Z0-9]', '', marca_field.upper())
            if marca_clean:
                return marca_clean[:4]
        
        # 3. Intentar extraer primera palabra significativa del nombre
        words = nombre_upper.split()
        for word in words:
            # Ignorar palabras genéricas
            if len(word) >= 3 and word not in ['LAPTOP', 'NOTEBOOK', 'CELULAR', 'SMARTPHONE', 
                                                'TABLET', 'MONITOR', 'SMART', 'TELEFONO']:
                return word[:4]
        
        return 'UNKN'
    
    def extract_model(self, nombre: str) -> str:
        """Extraer modelo o característica principal"""
        nombre_upper = nombre.upper()
        
        # 1. Buscar modelos conocidos
        for model in self.KNOWN_MODELS:
            if model in nombre_upper:
                # Buscar número después del modelo
                pattern = model + r'\s?(\d+\w*)'
                match = re.search(pattern, nombre_upper)
                if match:
                    return (model + match.group(1))[:10]
                return model[:10]
        
        # 2. Buscar pattern de modelo (letra + números)
        model_pattern = r'\b([A-Z]+\d+[A-Z0-9]*)\b'
        matches = re.findall(model_pattern, nombre_upper)
        if matches:
            # Tomar el más largo/significativo
            return max(matches, key=len)[:10]
        
        # 3. Extraer segunda palabra significativa
        words = nombre_upper.split()
        significant_words = [w for w in words if len(w) > 3 and not w.isdigit()]
        if len(significant_words) >= 2:
            return significant_words[1][:10]
        
        return 'PROD'
    
    def extract_specs(self, nombre: str) -> str:
        """Extraer especificaciones clave"""
        specs_found = self.specs_regex.findall(nombre)
        
        if specs_found:
            # Tomar las 2 specs más relevantes
            # Priorizar GB/TB sobre otros
            priority_specs = []
            other_specs = []
            
            for spec in specs_found[:4]:  # Máximo 4 specs
                spec_upper = spec.upper()
                if 'GB' in spec_upper or 'TB' in spec_upper:
                    priority_specs.append(spec_upper)
                else:
                    other_specs.append(spec_upper)
            
            # Combinar con prioridad
            all_specs = (priority_specs + other_specs)[:2]
            if all_specs:
                return '-'.join(all_specs)[:15]
        
        return 'NA'
    
    def generate_hash(self, text: str, length: int = 6) -> str:
        """Generar hash único de texto"""
        if not text or text == 'nan':
            text = str(hashlib.md5().hexdigest())
        
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return hash_obj.hexdigest()[:length].upper()
    
    def generate_sku(self, row: Dict, retailer: str, idx: int = 0) -> str:
        """
        Generar SKU único robusto
        
        Formato: CL-[MARCA]-[MODELO]-[SPEC]-[RET]-[HASH]
        """
        nombre = str(row.get('nombre', '')).strip()
        marca_field = str(row.get('marca', ''))
        sku_original = str(row.get('sku', ''))
        link = str(row.get('link', ''))
        
        # Si tiene SKU válido, usarlo para el hash
        if sku_original and sku_original not in ['nan', '', None]:
            hash_part = self.generate_hash(sku_original, 6)
        # Si no, usar link o nombre
        elif link and link not in ['nan', '', None]:
            hash_part = self.generate_hash(link, 6)
        else:
            # Usar nombre + índice para garantizar unicidad
            hash_part = self.generate_hash(f"{nombre}{idx}", 6)
        
        # Extraer componentes
        marca = self.extract_brand(nombre, marca_field)
        modelo = self.extract_model(nombre)
        specs = self.extract_specs(nombre)
        
        # Código de retailer
        ret_codes = {
            'ripley': 'RIP',
            'falabella': 'FAL',
            'paris': 'PAR',
            'mercadolibre': 'ML',
            'hites': 'HIT',
            'abcdin': 'ABC'
        }
        ret_code = ret_codes.get(retailer.lower(), 'UNK')
        
        # Construir SKU
        # Limitar longitud de cada parte
        marca = marca[:4]
        modelo = modelo[:8]
        specs = specs[:10] if specs != 'NA' else specs
        
        # Formato final
        sku = f"CL-{marca}-{modelo}"
        
        # Agregar specs si existen
        if specs != 'NA':
            sku += f"-{specs}"
        
        sku += f"-{ret_code}-{hash_part}"
        
        # Limpiar caracteres no válidos
        sku = re.sub(r'[^A-Z0-9\-]', '', sku.upper())
        
        # Limitar longitud total
        return sku[:50]

# Función de test
def test_generator():
    """Probar el generador con casos de ejemplo"""
    generator = RobustSKUGenerator()
    
    test_cases = [
        {
            'nombre': 'Laptop Auusda Intel N150 32gb Ram 1tb Ssd Windows 11 Silver',
            'marca': 'LAPTOP',
            'sku': 'nan',
            'link': 'https://mercadolibre.cl/123'
        },
        {
            'nombre': 'Samsung Galaxy S24 Ultra 256GB Negro',
            'marca': 'SAMSUNG',
            'sku': '12345',
            'link': 'https://falabella.cl/456'
        },
        {
            'nombre': 'Notebook HP Gamer Victus 15-fa0025la Intel Core I5 8gb Ram 512GB',
            'marca': 'NOTEBOOK',
            'sku': 'nan',
            'link': 'https://ripley.cl/789'
        },
        {
            'nombre': 'iPhone 15 Pro Max 256GB Titanio Natural',
            'marca': 'APPLE',
            'sku': 'APL123',
            'link': ''
        },
        {
            'nombre': 'Celular Xiaomi Redmi Note 13 Pro 5G 256GB 8GB RAM',
            'marca': 'XIAOMI',
            'sku': 'nan',
            'link': 'nan'
        }
    ]
    
    print("="*70)
    print("TEST DE GENERACION DE SKU ROBUSTO")
    print("="*70)
    
    for i, test in enumerate(test_cases):
        sku = generator.generate_sku(test, 'mercadolibre', i)
        print(f"\nCaso {i+1}:")
        print(f"  Nombre: {test['nombre'][:50]}...")
        print(f"  Marca: {test['marca']}")
        print(f"  SKU Original: {test['sku']}")
        print(f"  SKU Generado: {sku}")
        
        # Verificar componentes
        parts = sku.split('-')
        print(f"  Componentes:")
        print(f"    País: {parts[0]}")
        print(f"    Marca: {parts[1]}")
        print(f"    Modelo: {parts[2]}")
        if len(parts) > 5:
            print(f"    Specs: {parts[3]}")
            print(f"    Retailer: {parts[4]}")
            print(f"    Hash: {parts[5]}")
        else:
            print(f"    Retailer: {parts[3]}")
            print(f"    Hash: {parts[4]}")

if __name__ == "__main__":
    test_generator()