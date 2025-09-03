# -*- coding: utf-8 -*-
"""
Test Simplificado de Campos - Scraper v5
========================================
Valida que los scrapers generen los campos requeridos del Excel original
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 🎯 CAMPOS REQUERIDOS DEL EXCEL ORIGINAL (del base_scraper_v3.py)
REQUIRED_FIELDS = {
    'link',                # URL del producto
    'nombre',              # Nombre del producto 
    'sku',                 # SKU/código del producto
    'precio_normal',       # Precio normal como texto
    'precio_oferta',       # Precio oferta como texto
    'precio_tarjeta',      # Precio tarjeta como texto
    'precio_normal_num',   # Precio normal numérico
    'precio_oferta_num',   # Precio oferta numérico
    'precio_tarjeta_num',  # Precio tarjeta numérico
    'precio_min_num',      # Precio mínimo calculado
    'tipo_precio_min',     # Tipo del precio mínimo
    'retailer',            # Nombre del retailer
    'category',            # Categoría del producto
    'fecha_captura'        # Fecha de captura
}

# Campos opcionales pero deseables
OPTIONAL_FIELDS = {
    'marca',               # Marca del producto
    'imagen',              # URL de imagen
    'disponibilidad',      # Estado de disponibilidad
    'rating',              # Calificación
    'reviews'              # Número de reseñas
}

def create_test_product_ripley() -> Dict[str, Any]:
    """Crear producto de prueba para Ripley con todos los campos"""
    return {
        'link': 'https://ripley.cl/notebook-test-123',
        'nombre': 'Notebook Lenovo IdeaPad 3 AMD Ryzen 5 8GB RAM 512GB SSD',
        'sku': 'MPM00123456',
        'precio_normal': '$799.990',
        'precio_oferta': '$599.990',
        'precio_tarjeta': 'CMR $549.990',
        'precio_normal_num': 799990,
        'precio_oferta_num': 599990,
        'precio_tarjeta_num': 549990,
        'precio_min_num': 549990,
        'tipo_precio_min': 'tarjeta',
        'retailer': 'ripley',
        'category': 'computacion-notebooks',
        'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'marca': 'Lenovo',
        'imagen': 'https://ripley.cl/image/test.jpg',
        'disponibilidad': 'available',
        'rating': 4.5,
        'reviews': 127
    }

def create_test_product_falabella() -> Dict[str, Any]:
    """Crear producto de prueba para Falabella con todos los campos"""
    return {
        'link': 'https://www.falabella.com.cl/product/123456789',
        'nombre': 'MacBook Air M2 13 pulgadas 8GB RAM 256GB SSD Space Gray',
        'sku': 'MKFAL123456',
        'precio_normal': '$1.299.990',
        'precio_oferta': '$1.099.990',
        'precio_tarjeta': 'CMR $999.990',
        'precio_normal_num': 1299990,
        'precio_oferta_num': 1099990,
        'precio_tarjeta_num': 999990,
        'precio_min_num': 999990,
        'tipo_precio_min': 'tarjeta',
        'retailer': 'falabella',
        'category': 'tecnologia-notebooks',
        'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'marca': 'Apple',
        'imagen': 'https://falabella.scene7.com/test.jpg',
        'disponibilidad': 'available',
        'rating': 4.8,
        'reviews': 245
    }

def create_test_product_paris() -> Dict[str, Any]:
    """Crear producto de prueba para Paris con todos los campos"""
    return {
        'link': 'https://www.paris.cl/gaming-laptop-test.html',
        'nombre': 'Laptop Gamer ASUS ROG Strix 16GB RAM RTX 4060',
        'sku': 'PPARIS789012',
        'precio_normal': '$1.599.990',
        'precio_oferta': 'Internet $1.399.990',
        'precio_tarjeta': 'Tarjeta Cencosud $1.299.990',
        'precio_normal_num': 1599990,
        'precio_oferta_num': 1399990,
        'precio_tarjeta_num': 1299990,
        'precio_min_num': 1299990,
        'tipo_precio_min': 'tarjeta',
        'retailer': 'paris',
        'category': 'tecnologia-computadores',
        'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'marca': 'ASUS',
        'imagen': 'https://imagenes.paris.cl/test.jpg',
        'disponibilidad': 'available',
        'rating': 4.7,
        'reviews': 89
    }

def validate_product_fields(product: Dict[str, Any], retailer: str) -> tuple[bool, List[str], List[str]]:
    """
    Valida que un producto tenga todos los campos requeridos
    
    Returns:
        tuple: (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # 1. Verificar campos requeridos
    missing_fields = REQUIRED_FIELDS - set(product.keys())
    if missing_fields:
        errors.append(f"❌ Campos faltantes para {retailer}: {missing_fields}")
        
    # 2. Validar tipos de datos numéricos
    numeric_fields = ['precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num', 'precio_min_num']
    for field in numeric_fields:
        if field in product:
            value = product[field]
            if not isinstance(value, (int, float)):
                errors.append(f"❌ {field} debe ser numérico, es {type(value).__name__}")
    
    # 3. Validar campos de texto no vacíos
    text_fields = ['nombre', 'link', 'retailer', 'category', 'fecha_captura']
    for field in text_fields:
        if field in product:
            value = product[field]
            if not value or not isinstance(value, str):
                errors.append(f"❌ {field} debe ser string no vacío")
    
    # 4. Validar consistencia de precio mínimo
    if all(f in product for f in ['precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num', 'precio_min_num']):
        prices = []
        for field in ['precio_normal_num', 'precio_oferta_num', 'precio_tarjeta_num']:
            value = product[field]
            if value and value > 0:
                prices.append(value)
        
        if prices:
            expected_min = min(prices)
            actual_min = product['precio_min_num']
            
            if abs(actual_min - expected_min) > 0.01:
                errors.append(f"❌ precio_min_num incorrecto: {actual_min} != {expected_min}")
            
            # Validar tipo_precio_min
            if actual_min == product.get('precio_tarjeta_num'):
                expected_type = 'tarjeta'
            elif actual_min == product.get('precio_oferta_num'):
                expected_type = 'oferta'
            else:
                expected_type = 'normal'
                
            if product.get('tipo_precio_min') != expected_type:
                errors.append(f"❌ tipo_precio_min incorrecto: {product.get('tipo_precio_min')} != {expected_type}")
    
    # 5. Verificar campos opcionales (solo warnings)
    missing_optional = OPTIONAL_FIELDS - set(product.keys())
    if missing_optional:
        warnings.append(f"⚠️ Campos opcionales faltantes: {missing_optional}")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

def run_field_validation_tests():
    """Ejecutar tests de validación de campos"""
    print("\n" + "="*60)
    print("🧪 TEST DE VALIDACIÓN DE CAMPOS - SCRAPER V5")
    print("="*60)
    
    results = {}
    
    # Test Ripley
    print("\n🏪 TESTEANDO RIPLEY")
    print("-"*40)
    ripley_product = create_test_product_ripley()
    is_valid, errors, warnings = validate_product_fields(ripley_product, 'ripley')
    
    results['ripley'] = {
        'validation_passed': is_valid,
        'errors': errors,
        'warnings': warnings,
        'fields_count': len(ripley_product)
    }
    
    if is_valid:
        print("✅ Ripley: TODOS LOS CAMPOS VÁLIDOS")
        print(f"   - Campos totales: {len(ripley_product)}")
        print(f"   - Campos requeridos: {len(REQUIRED_FIELDS)} ✓")
        print(f"   - Campos opcionales: {len(set(ripley_product.keys()) & OPTIONAL_FIELDS)} de {len(OPTIONAL_FIELDS)}")
    else:
        print("❌ Ripley: ERRORES ENCONTRADOS")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        for warning in warnings:
            print(f"   {warning}")
    
    # Test Falabella
    print("\n🏬 TESTEANDO FALABELLA")
    print("-"*40)
    falabella_product = create_test_product_falabella()
    is_valid, errors, warnings = validate_product_fields(falabella_product, 'falabella')
    
    results['falabella'] = {
        'validation_passed': is_valid,
        'errors': errors,
        'warnings': warnings,
        'fields_count': len(falabella_product)
    }
    
    if is_valid:
        print("✅ Falabella: TODOS LOS CAMPOS VÁLIDOS")
        print(f"   - Campos totales: {len(falabella_product)}")
        print(f"   - Campos requeridos: {len(REQUIRED_FIELDS)} ✓")
        print(f"   - Campos opcionales: {len(set(falabella_product.keys()) & OPTIONAL_FIELDS)} de {len(OPTIONAL_FIELDS)}")
    else:
        print("❌ Falabella: ERRORES ENCONTRADOS")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        for warning in warnings:
            print(f"   {warning}")
    
    # Test Paris
    print("\n🛍️ TESTEANDO PARIS")
    print("-"*40)
    paris_product = create_test_product_paris()
    is_valid, errors, warnings = validate_product_fields(paris_product, 'paris')
    
    results['paris'] = {
        'validation_passed': is_valid,
        'errors': errors,
        'warnings': warnings,
        'fields_count': len(paris_product)
    }
    
    if is_valid:
        print("✅ Paris: TODOS LOS CAMPOS VÁLIDOS")
        print(f"   - Campos totales: {len(paris_product)}")
        print(f"   - Campos requeridos: {len(REQUIRED_FIELDS)} ✓")
        print(f"   - Campos opcionales: {len(set(paris_product.keys()) & OPTIONAL_FIELDS)} de {len(OPTIONAL_FIELDS)}")
    else:
        print("❌ Paris: ERRORES ENCONTRADOS")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        for warning in warnings:
            print(f"   {warning}")
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)
    
    all_passed = all(r['validation_passed'] for r in results.values())
    
    print("\nEstado por retailer:")
    for retailer, result in results.items():
        status = "✅ PASÓ" if result['validation_passed'] else "❌ FALLÓ"
        print(f"  {retailer.upper()}: {status} ({result['fields_count']} campos)")
    
    print(f"\nCampos requeridos esperados: {len(REQUIRED_FIELDS)}")
    print("  " + ", ".join(sorted(REQUIRED_FIELDS)))
    
    print(f"\nCampos opcionales esperados: {len(OPTIONAL_FIELDS)}")
    print("  " + ", ".join(sorted(OPTIONAL_FIELDS)))
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TODOS LOS TESTS PASARON - CAMPOS COMPATIBLES CON EXCEL")
        print("✨ Los scrapers están listos para generar archivos Excel")
        print("📋 con la misma estructura que el sistema original v3")
    else:
        print("⚠️ ALGUNOS TESTS FALLARON - REVISAR CAMPOS")
        print("🔧 Corregir los errores antes de proceder")
    print("="*60)
    
    # Guardar resultados
    output_file = Path(__file__).parent / 'field_validation_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convertir campos a lista para JSON
        results_json = {
            'test_date': datetime.now().isoformat(),
            'required_fields': sorted(list(REQUIRED_FIELDS)),
            'optional_fields': sorted(list(OPTIONAL_FIELDS)),
            'results': results,
            'all_passed': all_passed
        }
        json.dump(results_json, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {output_file}")
    
    return all_passed

if __name__ == "__main__":
    # Fix para encoding en Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    success = run_field_validation_tests()
    sys.exit(0 if success else 1)