#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis Comparativo Exhaustivo: Scrapers V3 vs V5
===================================================

Compara línea por línea la lógica de extracción, selectores y métodos
entre las versiones v3 (funcionales) y v5 (parcialmente funcionales).
"""

import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Paths de los scrapers
V3_BASE = Path("D:/portable_orchestrator_clean/scraper_v3/scrapers")
V5_BASE = Path("D:/portable_orchestrator_clean/scraper_v5_project/portable_orchestrator_v5/scrapers")

def extract_selectors(content: str, version: str) -> Dict[str, List[str]]:
    """Extraer todos los selectores CSS del código"""
    selectors = {
        'product_cards': [],
        'name': [],
        'price': [],
        'brand': [],
        'sku': [],
        'links': [],
        'otros': []
    }
    
    # Patterns para encontrar selectores
    patterns = {
        'querySelector': r'querySelector(?:All)?\(["\']([^"\']+)["\']\)',
        'locator': r'\.locator\(["\']([^"\']+)["\']\)',
        'waitForSelector': r'waitForSelector\(["\']([^"\']+)["\']\)',
        'page.$': r'page\.\$\(["\']([^"\']+)["\']\)',
        'page.$$': r'page\.\$\$\(["\']([^"\']+)["\']\)',
        'dict_selector': r'["\']([\.#\[][^"\']+)["\']:\s*["\']',
        'variable_selector': r'=\s*["\']([\.#\[][^"\']+)["\']'
    }
    
    for line_num, line in enumerate(content.split('\n'), 1):
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, line)
            for match in matches:
                # Categorizar selector
                if 'card' in match.lower() or 'product' in match.lower() or 'item' in match.lower():
                    selectors['product_cards'].append(f"L{line_num}: {match}")
                elif 'name' in match.lower() or 'title' in match.lower() or 'nombre' in match.lower():
                    selectors['name'].append(f"L{line_num}: {match}")
                elif 'price' in match.lower() or 'precio' in match.lower() or 'value' in match.lower():
                    selectors['price'].append(f"L{line_num}: {match}")
                elif 'brand' in match.lower() or 'marca' in match.lower():
                    selectors['brand'].append(f"L{line_num}: {match}")
                elif 'sku' in match.lower() or 'code' in match.lower():
                    selectors['sku'].append(f"L{line_num}: {match}")
                elif 'link' in match.lower() or 'href' in match.lower() or 'url' in match.lower():
                    selectors['links'].append(f"L{line_num}: {match}")
                else:
                    selectors['otros'].append(f"L{line_num}: {match}")
    
    return selectors

def extract_methods(content: str) -> Dict[str, Tuple[int, str]]:
    """Extraer métodos principales de extracción"""
    methods = {}
    
    # Buscar definiciones de métodos
    method_pattern = r'(async\s+)?def\s+(\w+)\s*\([^)]*\):'
    
    for match in re.finditer(method_pattern, content):
        is_async = bool(match.group(1))
        method_name = match.group(2)
        line_num = content[:match.start()].count('\n') + 1
        
        # Extraer las primeras 5 líneas del método
        method_start = match.end()
        lines_after = content[method_start:].split('\n')[:5]
        preview = '\n'.join(lines_after)
        
        methods[method_name] = (line_num, preview[:200])
    
    return methods

def compare_scraper(retailer: str):
    """Comparar un scraper específico entre v3 y v5"""
    v3_file = V3_BASE / f"{retailer}_scraper_v3.py"
    v5_file = V5_BASE / f"{retailer}_scraper_v5.py"
    
    if not v3_file.exists() or not v5_file.exists():
        print(f"[AVISO] No se encontraron ambos archivos para {retailer}")
        return None
    
    # Leer contenidos
    with open(v3_file, 'r', encoding='utf-8') as f:
        v3_content = f.read()
    
    with open(v5_file, 'r', encoding='utf-8') as f:
        v5_content = f.read()
    
    # Extraer selectores
    v3_selectors = extract_selectors(v3_content, 'v3')
    v5_selectors = extract_selectors(v5_content, 'v5')
    
    # Extraer métodos
    v3_methods = extract_methods(v3_content)
    v5_methods = extract_methods(v5_content)
    
    return {
        'v3_selectors': v3_selectors,
        'v5_selectors': v5_selectors,
        'v3_methods': v3_methods,
        'v5_methods': v5_methods,
        'v3_lines': len(v3_content.split('\n')),
        'v5_lines': len(v5_content.split('\n'))
    }

def analyze_extraction_logic(retailer: str):
    """Analizar la lógica específica de extracción"""
    v3_file = V3_BASE / f"{retailer}_scraper_v3.py"
    v5_file = V5_BASE / f"{retailer}_scraper_v5.py"
    
    if not v3_file.exists() or not v5_file.exists():
        return None
    
    with open(v3_file, 'r', encoding='utf-8') as f:
        v3_content = f.read()
    
    with open(v5_file, 'r', encoding='utf-8') as f:
        v5_content = f.read()
    
    # Buscar patrones de extracción específicos
    extraction_patterns = {
        'text_extraction': [
            r'\.text_content\(\)',
            r'\.inner_text\(\)',
            r'\.textContent',
            r'\.innerText',
            r'\.get_text\(\)'
        ],
        'attribute_extraction': [
            r'\.get_attribute\(["\']([^"\']+)["\']\)',
            r'\[["\'](href|src|data-[^"\']+)["\']\]',
            r'\.getAttribute\(["\']([^"\']+)["\']\)'
        ],
        'price_parsing': [
            r're\.sub\([^)]+\)',
            r'\.replace\([^)]+\)',
            r'int\(|float\(',
            r'\$[\d.,]+',
            r'precio.*=.*\d+'
        ],
        'error_handling': [
            r'try:',
            r'except.*:',
            r'if\s+.*is\s+None',
            r'if\s+not\s+',
            r'continue',
            r'pass'
        ]
    }
    
    results = {'v3': {}, 'v5': {}}
    
    for pattern_type, patterns in extraction_patterns.items():
        for version, content in [('v3', v3_content), ('v5', v5_content)]:
            count = 0
            examples = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                count += len(matches)
                if matches and len(examples) < 3:
                    examples.extend(matches[:3-len(examples)])
            results[version][pattern_type] = {'count': count, 'examples': examples}
    
    return results

def generate_comparison_report():
    """Generar reporte completo de comparación"""
    print("="*80)
    print("ANÁLISIS COMPARATIVO EXHAUSTIVO: V3 vs V5")
    print("="*80)
    
    retailers = ['ripley', 'falabella', 'paris']
    
    for retailer in retailers:
        print(f"\n{'='*80}")
        print(f"{retailer.upper()}: COMPARACIÓN V3 vs V5")
        print(f"{'='*80}")
        
        comparison = compare_scraper(retailer)
        
        if not comparison:
            continue
        
        # Tamaño de archivos
        print(f"\n📏 TAMAÑO DE ARCHIVOS:")
        print(f"  V3: {comparison['v3_lines']} líneas")
        print(f"  V5: {comparison['v5_lines']} líneas")
        
        # Comparación de selectores
        print(f"\n🎯 SELECTORES CSS:")
        print("-"*40)
        
        for category in ['product_cards', 'name', 'price', 'brand']:
            v3_sels = comparison['v3_selectors'][category]
            v5_sels = comparison['v5_selectors'][category]
            
            print(f"\n{category.upper()}:")
            print(f"  V3 ({len(v3_sels)} selectores):")
            for sel in v3_sels[:3]:
                print(f"    {sel}")
            
            print(f"  V5 ({len(v5_sels)} selectores):")
            for sel in v5_sels[:3]:
                print(f"    {sel}")
            
            # Verificar si son diferentes
            if set(s.split(': ')[1] for s in v3_sels if ': ' in s) != \
               set(s.split(': ')[1] for s in v5_sels if ': ' in s):
                print(f"  ⚠️ DIFERENCIA DETECTADA!")
        
        # Comparación de métodos
        print(f"\n🔧 MÉTODOS DE EXTRACCIÓN:")
        print("-"*40)
        
        v3_methods = set(comparison['v3_methods'].keys())
        v5_methods = set(comparison['v5_methods'].keys())
        
        print(f"  Métodos solo en V3: {v3_methods - v5_methods}")
        print(f"  Métodos solo en V5: {v5_methods - v3_methods}")
        print(f"  Métodos comunes: {len(v3_methods & v5_methods)}")
        
        # Análisis de lógica de extracción
        extraction_analysis = analyze_extraction_logic(retailer)
        
        if extraction_analysis:
            print(f"\n📊 ANÁLISIS DE LÓGICA DE EXTRACCIÓN:")
            print("-"*40)
            
            for pattern_type in ['text_extraction', 'attribute_extraction', 'price_parsing']:
                v3_data = extraction_analysis['v3'][pattern_type]
                v5_data = extraction_analysis['v5'][pattern_type]
                
                print(f"\n{pattern_type.replace('_', ' ').title()}:")
                print(f"  V3: {v3_data['count']} ocurrencias")
                print(f"  V5: {v5_data['count']} ocurrencias")
                
                if abs(v3_data['count'] - v5_data['count']) > 5:
                    print(f"  ⚠️ DIFERENCIA SIGNIFICATIVA!")

def generate_normalization_plan():
    """Generar plan de normalización detallado"""
    print("\n" + "="*80)
    print("PLAN DE NORMALIZACIÓN V3 → V5")
    print("="*80)
    
    plan = """
📋 PLAN DE ACCIÓN PARA NORMALIZAR V5 CON V3

1. RIPLEY
---------
✅ SELECTORES A ACTUALIZAR:
  - Product cards: Cambiar a selector exacto de v3
  - Precios: Usar método de extracción v3 con regex
  - SKU: Extraer del link como hace v3
  
❌ LÓGICA A CORREGIR:
  - Implementar scroll lento progresivo (crítico para Ripley)
  - Añadir esperas después de scroll
  - Usar navegador visible (headless=False)

2. FALABELLA
------------
✅ SELECTORES A ACTUALIZAR:
  - Cards: '#testId-searchResults-products' (v3)
  - Precios: Usar element handles como v3
  - Modal handling: Cerrar modales al inicio
  
❌ LÓGICA A CORREGIR:
  - Implementar procesamiento por lotes
  - Añadir manejo de modales
  - Usar element handles para evitar stale elements

3. PARIS
--------
✅ SELECTORES A ACTUALIZAR:
  - Cards: Selector específico de v3
  - Precios: Múltiples selectores fallback
  
❌ LÓGICA A CORREGIR:
  - Implementar esperas específicas
  - Añadir lógica de retry

PASOS DE IMPLEMENTACIÓN:
========================

PASO 1: Copiar selectores exactos de v3
  - Abrir ambos archivos lado a lado
  - Copiar línea por línea los selectores
  - Mantener orden y fallbacks

PASO 2: Copiar métodos de extracción
  - Copiar _extract_product_data completo
  - Copiar lógica de parsing de precios
  - Copiar manejo de errores

PASO 3: Ajustar para arquitectura v5
  - Mantener herencia de BaseScraperV5
  - Adaptar return types a ScrapingResult
  - Mantener field_mapper para compatibilidad

PASO 4: Validar extracción
  - Probar con 10 productos
  - Verificar que todos los campos se extraen
  - Comparar con resultados v3
    """
    
    print(plan)

def main():
    """Ejecutar análisis completo"""
    # Generar comparación
    generate_comparison_report()
    
    # Generar plan
    generate_normalization_plan()
    
    print("\n" + "="*80)
    print("RESUMEN EJECUTIVO")
    print("="*80)
    
    print("""
PRINCIPALES DIFERENCIAS ENCONTRADAS:
====================================

1. SELECTORES:
   - V3 usa selectores más específicos y probados
   - V5 tiene selectores genéricos que no funcionan
   
2. LÓGICA DE EXTRACCIÓN:
   - V3 tiene manejo robusto de errores
   - V3 usa element handles para evitar stale elements
   - V5 simplifica demasiado y pierde funcionalidad

3. CONFIGURACIÓN:
   - V3 tiene timeouts y esperas calibradas
   - V5 usa valores por defecto que no funcionan

RECOMENDACIÓN:
=============
Copiar exactamente la lógica de v3 a v5, manteniendo solo
la estructura de clases de v5 para compatibilidad.
    """)

if __name__ == "__main__":
    main()