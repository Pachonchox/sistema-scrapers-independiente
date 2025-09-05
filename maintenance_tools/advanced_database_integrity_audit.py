#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔍 AUDITORÍA AVANZADA DE INTEGRIDAD DE BASE DE DATOS
==================================================

Sistema completo de auditoría que verifica:
✅ Duplicados por múltiples métodos (no solo SKU interno)
✅ Integridad completa de datos
✅ Análisis de similitud textual
✅ Detección de productos repetidos por patrones
✅ Validación de consistencia completa
✅ Generación de reportes detallados con emojis

Autor: Sistema V5 Production
Fecha: 04/09/2025
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher
import re
from collections import defaultdict
import json
from typing import Dict, List, Tuple, Any

# Configurar soporte completo de emojis
sys.path.append(str(Path(__file__).parent))
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

# Cargar configuración
from dotenv import load_dotenv
load_dotenv()

class AdvancedDatabaseIntegrityAuditor:
    """🔍 Auditor avanzado de integridad de base de datos con detección múltiple de duplicados"""
    
    def __init__(self):
        """Inicializar auditor avanzado"""
        print("🚀 Inicializando Auditor Avanzado de Integridad...")
        
        # Parámetros de conexión
        self.conn_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': int(os.getenv('PGPORT', '5432')),
            'database': os.getenv('PGDATABASE', 'orchestrator'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', 'postgres')
        }
        
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            print(f"✅ Conectado a PostgreSQL: {self.conn_params['host']}:{self.conn_params['port']}")
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            raise
        
        # Contadores de resultados
        self.critical_violations = []
        self.warnings = []
        self.duplicate_groups = []
        self.stats = {}
        
        # Configuración de similitud
        self.similarity_threshold = 0.85  # 85% similitud
        self.name_similarity_threshold = 0.90  # 90% similitud en nombres
        
    def normalize_text(self, text: str) -> str:
        """🔤 Normalizar texto para comparación"""
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower().strip()
        
        # Remover caracteres especiales y espacios extra
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar palabras comunes
        replacements = {
            'smartphone': 'cel',
            'celular': 'cel',
            'television': 'tv',
            'televisor': 'tv',
            'notebook': 'laptop',
            'computador': 'pc',
            'computadora': 'pc',
            'tablet': 'tab',
            'electrodomestico': 'electro'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """📏 Calcular similitud entre dos textos"""
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def extract_product_specs(self, name: str) -> Dict[str, str]:
        """🔧 Extraer especificaciones del nombre del producto"""
        specs = {
            'brand': '',
            'model': '',
            'storage': '',
            'ram': '',
            'screen_size': '',
            'color': ''
        }
        
        if not name:
            return specs
        
        name_lower = name.lower()
        
        # Extraer marca (primeras palabras comunes)
        brands = ['samsung', 'apple', 'huawei', 'xiaomi', 'lg', 'sony', 'hp', 'lenovo', 'asus', 'dell']
        for brand in brands:
            if brand in name_lower:
                specs['brand'] = brand
                break
        
        # Extraer almacenamiento
        storage_match = re.search(r'(\d+)\s?(gb|tb)', name_lower)
        if storage_match:
            specs['storage'] = f"{storage_match.group(1)}{storage_match.group(2)}"
        
        # Extraer RAM
        ram_match = re.search(r'(\d+)\s?gb.*ram', name_lower)
        if ram_match:
            specs['ram'] = f"{ram_match.group(1)}gb"
        
        # Extraer tamaño pantalla
        screen_match = re.search(r'(\d+\.?\d*)\s?pulgadas?|(\d+\.?\d*)[""]', name_lower)
        if screen_match:
            size = screen_match.group(1) or screen_match.group(2)
            specs['screen_size'] = f"{size}inch"
        
        return specs
    
    def check_duplicate_by_codigo_interno(self):
        """🔍 1. Verificar duplicados por código interno (método base)"""
        print("\n" + "🔍" + "="*70 + "🔍")
        print("1️⃣ VERIFICANDO DUPLICADOS POR CÓDIGO INTERNO")
        print("🔍" + "="*70 + "🔍")
        
        self.cursor.execute("""
            SELECT codigo_interno, COUNT(*) as count
            FROM master_productos
            GROUP BY codigo_interno
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """)
        
        duplicates = self.cursor.fetchall()
        
        if duplicates:
            self.critical_violations.append(f"💥 {len(duplicates)} códigos internos duplicados")
            print(f"❌ VIOLACIÓN CRÍTICA: {len(duplicates)} códigos internos duplicados")
            
            for dup in duplicates[:5]:
                print(f"   📦 {dup['codigo_interno']}: {dup['count']} ocurrencias")
                
                # Mostrar detalles de los duplicados
                self.cursor.execute("""
                    SELECT nombre, retailer, link, created_at
                    FROM master_productos 
                    WHERE codigo_interno = %s
                """, (dup['codigo_interno'],))
                
                details = self.cursor.fetchall()
                for detail in details:
                    print(f"      🏪 {detail['retailer']}: {detail['nombre'][:50]}...")
                    print(f"         📅 {detail['created_at']} | 🔗 {detail['link'][:50]}...")
                print()
        else:
            print("✅ NO hay códigos internos duplicados")
    
    def check_duplicate_by_link(self):
        """🔗 2. Verificar duplicados por link/URL"""
        print("\n" + "🔗" + "="*70 + "🔗")
        print("2️⃣ VERIFICANDO DUPLICADOS POR LINK/URL")
        print("🔗" + "="*70 + "🔗")
        
        self.cursor.execute("""
            SELECT link, COUNT(*) as count, 
                   array_agg(codigo_interno) as codigos,
                   array_agg(retailer) as retailers
            FROM master_productos
            WHERE link IS NOT NULL AND link != ''
            GROUP BY link
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 20
        """)
        
        link_duplicates = self.cursor.fetchall()
        
        if link_duplicates:
            self.critical_violations.append(f"🔗 {len(link_duplicates)} links duplicados")
            print(f"❌ PROBLEMA: {len(link_duplicates)} links duplicados encontrados")
            
            for dup in link_duplicates:
                print(f"   🔗 Link: {dup['link'][:60]}...")
                print(f"   📦 Códigos: {', '.join(dup['codigos'])}")
                print(f"   🏪 Retailers: {', '.join(set(dup['retailers']))}")
                print()
        else:
            print("✅ NO hay links duplicados")
    
    def check_duplicate_by_name_similarity(self):
        """📝 3. Verificar duplicados por similitud de nombres"""
        print("\n" + "📝" + "="*70 + "📝")
        print("3️⃣ VERIFICANDO DUPLICADOS POR SIMILITUD DE NOMBRES")
        print("📝" + "="*70 + "📝")
        
        print("⏳ Cargando productos para análisis de similitud...")
        
        # Obtener productos con información básica
        self.cursor.execute("""
            SELECT codigo_interno, nombre, retailer, marca, categoria
            FROM master_productos
            WHERE nombre IS NOT NULL AND LENGTH(nombre) > 10
            ORDER BY retailer, categoria
        """)
        
        products = self.cursor.fetchall()
        print(f"🔍 Analizando {len(products):,} productos...")
        
        similar_groups = []
        processed = set()
        
        # Comparar productos por similitud de nombres
        for i, product1 in enumerate(products):
            if product1['codigo_interno'] in processed:
                continue
                
            similar_group = [product1]
            processed.add(product1['codigo_interno'])
            
            # Comparar con productos restantes
            for j, product2 in enumerate(products[i+1:], i+1):
                if product2['codigo_interno'] in processed:
                    continue
                
                # Calcular similitud
                similarity = self.calculate_text_similarity(
                    product1['nombre'], 
                    product2['nombre']
                )
                
                # Si son muy similares, agregar al grupo
                if similarity >= self.name_similarity_threshold:
                    similar_group.append(product2)
                    processed.add(product2['codigo_interno'])
            
            # Si encontramos un grupo de similares, guardarlo
            if len(similar_group) > 1:
                similar_groups.append(similar_group)
            
            # Progreso cada 1000 productos
            if (i + 1) % 1000 == 0:
                print(f"   📊 Procesados {i+1:,}/{len(products):,} productos...")
        
        if similar_groups:
            self.warnings.append(f"🔍 {len(similar_groups)} grupos de productos con nombres similares")
            print(f"⚠️ ENCONTRADOS: {len(similar_groups)} grupos de productos con nombres similares")
            
            for idx, group in enumerate(similar_groups[:10]):
                print(f"\n   📦 Grupo {idx+1} ({len(group)} productos similares):")
                for product in group:
                    print(f"      🏪 {product['retailer']} | {product['codigo_interno']}")
                    print(f"         📝 {product['nombre'][:60]}...")
                
                if idx < len(similar_groups) - 1:
                    print(f"      ⚖️ Similitud: {self.calculate_text_similarity(group[0]['nombre'], group[1]['nombre']):.2%}")
                    
            self.duplicate_groups = similar_groups
        else:
            print("✅ NO se encontraron nombres significativamente similares")
    
    def check_duplicate_by_specs(self):
        """🔧 4. Verificar duplicados por especificaciones técnicas"""
        print("\n" + "🔧" + "="*70 + "🔧")
        print("4️⃣ VERIFICANDO DUPLICADOS POR ESPECIFICACIONES")
        print("🔧" + "="*70 + "🔧")
        
        # Obtener productos con especificaciones
        self.cursor.execute("""
            SELECT codigo_interno, nombre, marca, storage, ram, screen, categoria, retailer
            FROM master_productos
            WHERE marca IS NOT NULL 
            AND (storage IS NOT NULL OR ram IS NOT NULL OR screen IS NOT NULL)
        """)
        
        products_with_specs = self.cursor.fetchall()
        print(f"🔍 Analizando {len(products_with_specs):,} productos con especificaciones...")
        
        # Agrupar por especificaciones similares
        spec_groups = defaultdict(list)
        
        for product in products_with_specs:
            # Crear clave única basada en especificaciones
            spec_key = f"{product.get('marca', '').lower()}|" + \
                      f"{product.get('storage', 'N/A')}|" + \
                      f"{product.get('ram', 'N/A')}|" + \
                      f"{product.get('screen', 'N/A')}|" + \
                      f"{product.get('categoria', 'N/A').lower()}"
            
            spec_groups[spec_key].append(product)
        
        # Encontrar grupos con múltiples productos
        duplicate_spec_groups = {k: v for k, v in spec_groups.items() if len(v) > 1}
        
        if duplicate_spec_groups:
            total_duplicates = sum(len(group) for group in duplicate_spec_groups.values())
            self.warnings.append(f"🔧 {len(duplicate_spec_groups)} grupos con especificaciones idénticas")
            print(f"⚠️ ENCONTRADOS: {len(duplicate_spec_groups)} grupos con especificaciones idénticas")
            print(f"   📊 Total productos involucrados: {total_duplicates}")
            
            for idx, (spec_key, group) in enumerate(list(duplicate_spec_groups.items())[:5]):
                print(f"\n   🔧 Grupo {idx+1} - Especificaciones: {spec_key}")
                for product in group:
                    print(f"      🏪 {product['retailer']} | {product['codigo_interno']}")
                    print(f"         📝 {product['nombre'][:50]}...")
        else:
            print("✅ NO se encontraron duplicados por especificaciones")
    
    def check_cross_retailer_duplicates(self):
        """🏪 5. Verificar duplicados entre retailers (mismo producto en múltiples tiendas)"""
        print("\n" + "🏪" + "="*70 + "🏪")
        print("5️⃣ VERIFICANDO DUPLICADOS ENTRE RETAILERS")
        print("🏪" + "="*70 + "🏪")
        
        self.cursor.execute("""
            WITH normalized_products AS (
                SELECT 
                    codigo_interno,
                    LOWER(REGEXP_REPLACE(nombre, '[^a-zA-Z0-9]', ' ', 'g')) as normalized_name,
                    marca,
                    storage,
                    retailer,
                    nombre as original_name
                FROM master_productos
                WHERE marca IS NOT NULL
            )
            SELECT 
                marca,
                normalized_name,
                array_agg(DISTINCT retailer) as retailers,
                array_agg(codigo_interno) as codigos,
                array_agg(original_name) as nombres,
                COUNT(DISTINCT retailer) as retailer_count
            FROM normalized_products
            GROUP BY marca, normalized_name
            HAVING COUNT(DISTINCT retailer) > 1
            ORDER BY COUNT(DISTINCT retailer) DESC
            LIMIT 20
        """)
        
        cross_retailer_duplicates = self.cursor.fetchall()
        
        if cross_retailer_duplicates:
            print(f"🔍 ENCONTRADOS: {len(cross_retailer_duplicates)} productos en múltiples retailers")
            
            for dup in cross_retailer_duplicates:
                print(f"\n   🏷️ Marca: {dup['marca']} | Retailers: {len(dup['retailers'])}")
                print(f"   🏪 Tiendas: {', '.join(dup['retailers'])}")
                print(f"   📝 Nombre ejemplo: {dup['nombres'][0][:60]}...")
                print(f"   📦 Códigos: {len(dup['codigos'])} productos")
                
            self.stats['cross_retailer_duplicates'] = len(cross_retailer_duplicates)
        else:
            print("✅ NO se encontraron productos duplicados entre retailers")
    
    def analyze_price_consistency(self):
        """💰 6. Analizar consistencia de precios"""
        print("\n" + "💰" + "="*70 + "💰")
        print("6️⃣ ANALIZANDO CONSISTENCIA DE PRECIOS")
        print("💰" + "="*70 + "💰")
        
        # Verificar precios inválidos
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_invalid,
                COUNT(CASE WHEN precio_normal <= 0 THEN 1 END) as precio_normal_invalid,
                COUNT(CASE WHEN precio_oferta > precio_normal THEN 1 END) as oferta_mayor,
                COUNT(CASE WHEN precio_tarjeta > precio_normal THEN 1 END) as tarjeta_mayor
            FROM master_precios
            WHERE precio_normal <= 0 
               OR (precio_oferta > precio_normal AND precio_oferta IS NOT NULL)
               OR (precio_tarjeta > precio_normal AND precio_tarjeta IS NOT NULL)
        """)
        
        price_issues = self.cursor.fetchone()
        
        if price_issues and price_issues['total_invalid'] > 0:
            self.critical_violations.append(f"💰 {price_issues['total_invalid']} registros con precios inválidos")
            print(f"❌ PROBLEMAS DE PRECIOS:")
            print(f"   💸 Precios normales ≤ 0: {price_issues['precio_normal_invalid']}")
            print(f"   🔺 Oferta > Normal: {price_issues['oferta_mayor']}")
            print(f"   🔺 Tarjeta > Normal: {price_issues['tarjeta_mayor']}")
        else:
            print("✅ Precios consistentes")
        
        # Verificar constraint diario
        self.cursor.execute("""
            SELECT codigo_interno, fecha, COUNT(*) as registros
            FROM master_precios
            GROUP BY codigo_interno, fecha
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)
        
        daily_violations = self.cursor.fetchall()
        
        if daily_violations:
            self.critical_violations.append(f"📅 {len(daily_violations)} violaciones de constraint diario")
            print(f"❌ VIOLACIÓN CONSTRAINT DIARIO:")
            for violation in daily_violations:
                print(f"   📦 {violation['codigo_interno']}: {violation['registros']} registros el {violation['fecha']}")
        else:
            print("✅ Constraint diario respetado (1 precio/producto/día)")
    
    def analyze_data_quality(self):
        """🎯 7. Análisis de calidad de datos"""
        print("\n" + "🎯" + "="*70 + "🎯")
        print("7️⃣ ANÁLISIS DE CALIDAD DE DATOS")
        print("🎯" + "="*70 + "🎯")
        
        # Productos sin información básica
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_productos,
                COUNT(CASE WHEN nombre IS NULL OR LENGTH(TRIM(nombre)) = 0 THEN 1 END) as sin_nombre,
                COUNT(CASE WHEN marca IS NULL OR LENGTH(TRIM(marca)) = 0 THEN 1 END) as sin_marca,
                COUNT(CASE WHEN categoria IS NULL OR LENGTH(TRIM(categoria)) = 0 THEN 1 END) as sin_categoria,
                COUNT(CASE WHEN link IS NULL OR LENGTH(TRIM(link)) = 0 THEN 1 END) as sin_link
            FROM master_productos
        """)
        
        quality_stats = self.cursor.fetchone()
        
        print(f"📊 ESTADÍSTICAS DE CALIDAD:")
        print(f"   📦 Total productos: {quality_stats['total_productos']:,}")
        print(f"   📝 Sin nombre: {quality_stats['sin_nombre']:,} ({quality_stats['sin_nombre']/quality_stats['total_productos']*100:.1f}%)")
        print(f"   🏷️ Sin marca: {quality_stats['sin_marca']:,} ({quality_stats['sin_marca']/quality_stats['total_productos']*100:.1f}%)")
        print(f"   📂 Sin categoría: {quality_stats['sin_categoria']:,} ({quality_stats['sin_categoria']/quality_stats['total_productos']*100:.1f}%)")
        print(f"   🔗 Sin link: {quality_stats['sin_link']:,} ({quality_stats['sin_link']/quality_stats['total_productos']*100:.1f}%)")
        
        # Identificar posibles problemas
        quality_threshold = 0.05  # 5%
        quality_issues = []
        
        if quality_stats['sin_nombre'] / quality_stats['total_productos'] > quality_threshold:
            quality_issues.append(f"Alto porcentaje sin nombre: {quality_stats['sin_nombre']/quality_stats['total_productos']*100:.1f}%")
            
        if quality_stats['sin_marca'] / quality_stats['total_productos'] > quality_threshold:
            quality_issues.append(f"Alto porcentaje sin marca: {quality_stats['sin_marca']/quality_stats['total_productos']*100:.1f}%")
        
        if quality_issues:
            self.warnings.extend(quality_issues)
            print(f"⚠️ PROBLEMAS DE CALIDAD DETECTADOS:")
            for issue in quality_issues:
                print(f"   • {issue}")
        
        self.stats.update(dict(quality_stats))
    
    def generate_comprehensive_report(self):
        """📋 8. Generar reporte comprehensivo final"""
        print("\n" + "📋" + "="*70 + "📋")
        print("📋 REPORTE COMPREHENSIVO FINAL DE AUDITORÍA")
        print("📋" + "="*70 + "📋")
        
        # Estadísticas generales
        self.cursor.execute("SELECT COUNT(*) as total FROM master_productos")
        total_products = self.cursor.fetchone()['total']
        
        self.cursor.execute("SELECT COUNT(*) as total FROM master_precios")
        total_prices = self.cursor.fetchone()['total']
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   📦 Total productos: {total_products:,}")
        print(f"   💰 Total registros precios: {total_prices:,}")
        print(f"   📅 Fecha auditoría: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Resumen de violaciones críticas
        if self.critical_violations:
            print(f"\n❌ VIOLACIONES CRÍTICAS ({len(self.critical_violations)}):")
            for i, violation in enumerate(self.critical_violations, 1):
                print(f"   {i}. {violation}")
        else:
            print(f"\n✅ NO SE ENCONTRARON VIOLACIONES CRÍTICAS")
        
        # Resumen de advertencias
        if self.warnings:
            print(f"\n⚠️ ADVERTENCIAS Y RECOMENDACIONES ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        # Grupos de duplicados encontrados
        if self.duplicate_groups:
            print(f"\n🔍 GRUPOS DE DUPLICADOS ENCONTRADOS: {len(self.duplicate_groups)}")
            total_duplicated_products = sum(len(group) for group in self.duplicate_groups)
            print(f"   📦 Total productos involucrados: {total_duplicated_products}")
        
        # Recomendaciones de mejora
        print(f"\n💡 RECOMENDACIONES DE MEJORA:")
        
        recommendations = [
            "1. 🚫 Implementar constraint UNIQUE (codigo_interno, fecha) en master_precios",
            "2. 🔗 Agregar constraint UNIQUE en campo link si debe ser único",
            "3. 🔍 Implementar proceso de deduplicación basado en similitud de nombres",
            "4. 🛡️ Agregar validaciones de precios a nivel de aplicación",
            "5. 🎯 Mejorar proceso de normalización de datos de entrada",
            "6. 📊 Configurar monitoreo automático de calidad de datos",
            "7. 🔄 Implementar proceso periódico de limpieza de duplicados",
            "8. 📈 Crear dashboard de métricas de integridad de datos"
        ]
        
        for rec in recommendations:
            print(f"   {rec}")
        
        # Generar archivo de reporte
        report_data = {
            'audit_date': datetime.now().isoformat(),
            'total_products': total_products,
            'total_prices': total_prices,
            'critical_violations': self.critical_violations,
            'warnings': self.warnings,
            'duplicate_groups_count': len(self.duplicate_groups),
            'stats': self.stats,
            'recommendations': recommendations
        }
        
        report_file = f"database_integrity_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 REPORTE GUARDADO: {report_file}")
        
        # Resumen final
        status = "🚨 REQUIERE ATENCIÓN" if self.critical_violations else "✅ SALUDABLE"
        print(f"\n🎯 ESTADO GENERAL DE LA BASE DE DATOS: {status}")
        
        return report_file
    
    def run_complete_audit(self):
        """🚀 Ejecutar auditoría completa"""
        print("🚀" + "="*70 + "🚀")
        print("🔍 INICIANDO AUDITORÍA COMPLETA DE INTEGRIDAD DE BASE DE DATOS")
        print("🚀" + "="*70 + "🚀")
        
        audit_steps = [
            ("🔍 Códigos Internos", self.check_duplicate_by_codigo_interno),
            ("🔗 Links/URLs", self.check_duplicate_by_link),
            ("📝 Similitud de Nombres", self.check_duplicate_by_name_similarity),
            ("🔧 Especificaciones", self.check_duplicate_by_specs),
            ("🏪 Entre Retailers", self.check_cross_retailer_duplicates),
            ("💰 Consistencia Precios", self.analyze_price_consistency),
            ("🎯 Calidad de Datos", self.analyze_data_quality),
            ("📋 Reporte Final", self.generate_comprehensive_report)
        ]
        
        for step_name, step_func in audit_steps:
            try:
                print(f"\n⏳ Ejecutando: {step_name}...")
                result = step_func()
                if result:
                    print(f"✅ {step_name} completado")
            except Exception as e:
                print(f"❌ Error en {step_name}: {e}")
                import traceback
                print(f"🔍 Detalle: {traceback.format_exc()}")
        
        print("\n🎉 AUDITORÍA COMPLETA FINALIZADA")
    
    def close(self):
        """🔚 Cerrar conexiones"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("🔚 Conexiones cerradas")

def main():
    """🚀 Función principal"""
    print("🔍 Iniciando Auditoría Avanzada de Integridad...")
    
    auditor = AdvancedDatabaseIntegrityAuditor()
    
    try:
        auditor.run_complete_audit()
    except KeyboardInterrupt:
        print("\n⏹️ Auditoría interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico durante auditoría: {e}")
        import traceback
        traceback.print_exc()
    finally:
        auditor.close()

if __name__ == "__main__":
    main()