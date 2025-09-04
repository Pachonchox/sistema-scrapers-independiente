#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔍 INVESTIGACIÓN DE PROBLEMAS DE INTEGRIDAD DE DATOS
===================================================

Análisis específico de los 3 problemas críticos encontrados:
1. 🔗 Link duplicado (76 ocurrencias)
2. 💸 Precios inválidos (oferta > precio normal)
3. 📝 Códigos con formato incorrecto

Este script identifica las causas raíz y propone soluciones.

Autor: Sistema V5 Production
Fecha: 04/09/2025
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Any
import re

# Configurar soporte completo de emojis
sys.path.append(str(Path(__file__).parent))
from portable_orchestrator_v5.core.emoji_support import force_emoji_support
force_emoji_support()

# Cargar configuración
from dotenv import load_dotenv
load_dotenv()

class DataIntegrityIssueInvestigator:
    """🔍 Investigador de problemas específicos de integridad de datos"""
    
    def __init__(self):
        """Inicializar investigador"""
        print("🔍 Inicializando Investigador de Problemas de Integridad...")
        
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
        
        # Resultados de investigación
        self.findings = {
            'duplicate_links': {},
            'invalid_prices': {},
            'invalid_codes': {},
            'root_causes': [],
            'solutions': []
        }
    
    def investigate_duplicate_links(self):
        """🔗 1. Investigar links duplicados (76 ocurrencias)"""
        print("\n" + "🔗" + "="*80 + "🔗")
        print("🔍 INVESTIGANDO LINKS DUPLICADOS (76 OCURRENCIAS)")
        print("🔗" + "="*80 + "🔗")
        
        # Encontrar el link específico con 76 duplicados
        self.cursor.execute("""
            SELECT link, COUNT(*) as count,
                   array_agg(codigo_interno) as codigos,
                   array_agg(nombre) as nombres,
                   array_agg(retailer) as retailers,
                   array_agg(created_at) as fechas_creacion
            FROM master_productos
            WHERE link IS NOT NULL AND link != ''
            GROUP BY link
            HAVING COUNT(*) > 10
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)
        
        duplicate_links = self.cursor.fetchall()
        
        print(f"🔍 Encontrados {len(duplicate_links)} links con más de 10 duplicados:")
        
        for dup in duplicate_links:
            print(f"\n📊 ANÁLISIS DEL LINK:")
            print(f"   🔗 Link: {dup['link']}")
            print(f"   📦 Duplicados: {dup['count']}")
            print(f"   🏪 Retailers: {set(dup['retailers'])}")
            print(f"   📅 Rango fechas: {min(dup['fechas_creacion'])} - {max(dup['fechas_creacion'])}")
            
            # Analizar patrones en los nombres
            nombres_unicos = set(dup['nombres'])
            print(f"   📝 Nombres únicos: {len(nombres_unicos)}")
            
            if len(nombres_unicos) <= 5:
                for nombre in list(nombres_unicos)[:5]:
                    print(f"      • {nombre[:80]}...")
            
            # Analizar códigos internos
            print(f"   🔧 Códigos afectados:")
            for i, codigo in enumerate(dup['codigos'][:5]):
                print(f"      {i+1}. {codigo}")
            
            if dup['count'] == 76:  # El caso específico
                self.findings['duplicate_links']['main_case'] = {
                    'link': dup['link'],
                    'count': dup['count'],
                    'codigos': dup['codigos'],
                    'retailers': list(set(dup['retailers'])),
                    'nombres_unicos': len(nombres_unicos),
                    'fecha_primera': min(dup['fechas_creacion']),
                    'fecha_ultima': max(dup['fechas_creacion'])
                }
        
        # Analizar causa raíz del link duplicado
        print(f"\n🔍 ANÁLISIS DE CAUSA RAÍZ - LINKS DUPLICADOS:")
        
        main_case = self.findings['duplicate_links'].get('main_case')
        if main_case:
            link_pattern = main_case['link']
            
            # Verificar si es un link genérico o placeholder
            generic_patterns = [
                'javascript:void(0)',
                '#',
                'about:blank',
                'null',
                'undefined',
                '',
                'N/A',
                'no-link'
            ]
            
            is_generic = any(pattern in link_pattern.lower() for pattern in generic_patterns)
            
            if is_generic:
                cause = "🎯 CAUSA RAÍZ: Link genérico/placeholder usado cuando el scraper no encuentra URL válida"
                solution = "Mejorar validación de URLs en scrapers y usar NULL en lugar de placeholders"
            else:
                cause = "🎯 CAUSA RAÍZ: Mismo producto extraído múltiples veces con la misma URL"
                solution = "Implementar deduplicación por URL antes de insertar en base de datos"
            
            print(f"   {cause}")
            self.findings['root_causes'].append(cause)
            self.findings['solutions'].append(solution)
        
        print(f"\n💡 RECOMENDACIÓN INMEDIATA:")
        print(f"   1. Revisar scrapers que generan URLs genéricas")
        print(f"   2. Implementar constraint UNIQUE en link (con manejo de NULL)")
        print(f"   3. Agregar validación de URL en proceso de scraping")
    
    def investigate_invalid_prices(self):
        """💸 2. Investigar precios inválidos (oferta > precio normal)"""
        print("\n" + "💸" + "="*80 + "💸")
        print("🔍 INVESTIGANDO PRECIOS INVÁLIDOS (OFERTA > PRECIO NORMAL)")
        print("💸" + "="*80 + "💸")
        
        # Encontrar casos específicos de precios inválidos
        self.cursor.execute("""
            SELECT p.codigo_interno, p.nombre, p.retailer, p.marca, p.categoria,
                   pr.fecha, pr.precio_normal, pr.precio_oferta, pr.precio_tarjeta,
                   pr.timestamp_creacion,
                   (pr.precio_oferta - pr.precio_normal) as diferencia_oferta,
                   ((pr.precio_oferta - pr.precio_normal) / pr.precio_normal * 100) as porcentaje_incremento
            FROM master_productos p
            JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE pr.precio_oferta > pr.precio_normal
            AND pr.precio_oferta IS NOT NULL
            ORDER BY porcentaje_incremento DESC
            LIMIT 20
        """)
        
        invalid_prices = self.cursor.fetchall()
        
        print(f"🔍 Encontrados {len(invalid_prices)} casos de precios inválidos:")
        
        total_cases = 0
        retailer_patterns = {}
        category_patterns = {}
        
        for case in invalid_prices:
            total_cases += 1
            
            print(f"\n📊 CASO {total_cases}:")
            print(f"   📦 Producto: {case['codigo_interno']}")
            print(f"   📝 Nombre: {case['nombre'][:60]}...")
            print(f"   🏪 Retailer: {case['retailer']}")
            print(f"   📂 Categoría: {case['categoria']}")
            print(f"   📅 Fecha: {case['fecha']}")
            print(f"   💰 Normal: ${case['precio_normal']:,.0f}")
            print(f"   🔺 Oferta: ${case['precio_oferta']:,.0f}")
            print(f"   📈 Incremento: {case['porcentaje_incremento']:.1f}%")
            print(f"   🕐 Creado: {case['timestamp_creacion']}")
            
            # Acumular patrones por retailer
            retailer = case['retailer']
            if retailer not in retailer_patterns:
                retailer_patterns[retailer] = []
            retailer_patterns[retailer].append({
                'codigo': case['codigo_internal'],
                'incremento': case['porcentaje_incremento'],
                'diferencia': case['diferencia_oferta']
            })
            
            # Acumular patrones por categoría
            categoria = case['categoria'] or 'Sin categoría'
            if categoria not in category_patterns:
                category_patterns[categoria] = 0
            category_patterns[categoria] += 1
        
        # Análisis de patrones
        print(f"\n🔍 ANÁLISIS DE PATRONES - PRECIOS INVÁLIDOS:")
        
        print(f"📊 POR RETAILER:")
        for retailer, casos in retailer_patterns.items():
            avg_increment = sum(c['incremento'] for c in casos) / len(casos)
            print(f"   🏪 {retailer}: {len(casos)} casos, incremento promedio: {avg_increment:.1f}%")
        
        print(f"📊 POR CATEGORÍA:")
        for categoria, count in category_patterns.items():
            print(f"   📂 {categoria}: {count} casos")
        
        # Determinar causa raíz
        print(f"\n🎯 ANÁLISIS DE CAUSA RAÍZ - PRECIOS INVÁLIDOS:")
        
        # Verificar si hay patrón temporal
        self.cursor.execute("""
            SELECT DATE(timestamp_creacion) as fecha,
                   COUNT(*) as casos_invalidos
            FROM master_precios
            WHERE precio_oferta > precio_normal
            AND precio_oferta IS NOT NULL
            GROUP BY DATE(timestamp_creacion)
            ORDER BY fecha DESC
        """)
        
        temporal_pattern = self.cursor.fetchall()
        
        if temporal_pattern:
            print(f"📅 Patrón temporal de casos inválidos:")
            for pattern in temporal_pattern:
                print(f"   {pattern['fecha']}: {pattern['casos_invalidos']} casos")
        
        # Posibles causas
        possible_causes = [
            "🎯 CAUSA 1: Error en scraping - extrayendo precio con descuento como 'normal'",
            "🎯 CAUSA 2: Problema en mapeo de campos - precio_normal y precio_oferta intercambiados",
            "🎯 CAUSA 3: Precios con formatos especiales no procesados correctamente",
            "🎯 CAUSA 4: Promociones especiales donde 'oferta' incluye beneficios adicionales"
        ]
        
        for cause in possible_causes:
            print(f"   {cause}")
            
        self.findings['root_causes'].extend(possible_causes)
        self.findings['invalid_prices'] = {
            'total_cases': total_cases,
            'by_retailer': retailer_patterns,
            'by_category': category_patterns,
            'temporal_pattern': temporal_pattern
        }
    
    def investigate_invalid_codes(self):
        """📝 3. Investigar códigos con formato incorrecto"""
        print("\n" + "📝" + "="*80 + "📝")
        print("🔍 INVESTIGANDO CÓDIGOS CON FORMATO INCORRECTO")
        print("📝" + "="*80 + "📝")
        
        # Formato correcto esperado: CL-BRAND-MODEL-SPEC-RET-SEQ
        print("📋 Formato esperado: CL-BRAND-MODEL-SPEC-RET-SEQ")
        
        # Encontrar códigos con formato incorrecto
        self.cursor.execute("""
            SELECT codigo_interno, nombre, retailer, marca, categoria, created_at
            FROM master_productos
            WHERE codigo_interno NOT LIKE 'CL-%-%-%-%-%'
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        invalid_codes = self.cursor.fetchall()
        
        print(f"🔍 Encontrados {len(invalid_codes)} códigos con formato incorrecto:")
        
        # Analizar patrones de códigos incorrectos
        pattern_analysis = {
            'missing_cl': 0,
            'insufficient_parts': 0,
            'too_many_parts': 0,
            'empty_parts': 0,
            'special_chars': 0
        }
        
        retailer_issues = {}
        
        for i, code_info in enumerate(invalid_codes[:20]):  # Solo mostrar primeros 20
            codigo = code_info['codigo_interno']
            
            print(f"\n📦 CÓDIGO INVÁLIDO {i+1}:")
            print(f"   🔧 Código: {codigo}")
            print(f"   📝 Producto: {code_info['nombre'][:50]}...")
            print(f"   🏪 Retailer: {code_info['retailer']}")
            print(f"   🏷️ Marca: {code_info['marca']}")
            print(f"   📂 Categoría: {code_info['categoria']}")
            print(f"   📅 Creado: {code_info['created_at']}")
            
            # Analizar el patrón específico
            parts = codigo.split('-')
            
            if not codigo.startswith('CL-'):
                pattern_analysis['missing_cl'] += 1
                print(f"   ❌ Problema: No empieza con 'CL-'")
            
            if len(parts) < 6:
                pattern_analysis['insufficient_parts'] += 1
                print(f"   ❌ Problema: Partes insuficientes ({len(parts)}/6)")
            elif len(parts) > 6:
                pattern_analysis['too_many_parts'] += 1
                print(f"   ❌ Problema: Demasiadas partes ({len(parts)}/6)")
            
            if any(part == '' for part in parts):
                pattern_analysis['empty_parts'] += 1
                print(f"   ❌ Problema: Partes vacías")
            
            if re.search(r'[^A-Z0-9\-]', codigo):
                pattern_analysis['special_chars'] += 1
                print(f"   ❌ Problema: Caracteres especiales")
            
            # Acumular por retailer
            retailer = code_info['retailer']
            if retailer not in retailer_issues:
                retailer_issues[retailer] = 0
            retailer_issues[retailer] += 1
        
        # Resumen de patrones
        print(f"\n📊 RESUMEN DE PATRONES - CÓDIGOS INVÁLIDOS:")
        print(f"   📦 Total códigos inválidos: {len(invalid_codes)}")
        print(f"   ❌ Sin prefijo 'CL-': {pattern_analysis['missing_cl']}")
        print(f"   📏 Partes insuficientes: {pattern_analysis['insufficient_parts']}")
        print(f"   📏 Demasiadas partes: {pattern_analysis['too_many_parts']}")
        print(f"   🔳 Partes vacías: {pattern_analysis['empty_parts']}")
        print(f"   🔣 Caracteres especiales: {pattern_analysis['special_chars']}")
        
        print(f"\n🏪 POR RETAILER:")
        for retailer, count in retailer_issues.items():
            print(f"   {retailer}: {count} códigos inválidos")
        
        # Verificar lógica de generación de códigos
        print(f"\n🔍 ANÁLISIS DE CAUSA RAÍZ - CÓDIGOS INVÁLIDOS:")
        
        root_causes = [
            "🎯 CAUSA 1: Algoritmo de generación no maneja correctamente marcas/modelos con caracteres especiales",
            "🎯 CAUSA 2: Campos vacíos o NULL no se reemplazan adecuadamente en el formato",
            "🎯 CAUSA 3: Secuencias hexadecimales muy largas que rompen el formato",
            "🎯 CAUSA 4: Validación insuficiente antes de insertar en base de datos"
        ]
        
        for cause in root_causes:
            print(f"   {cause}")
        
        self.findings['root_causes'].extend(root_causes)
        self.findings['invalid_codes'] = {
            'total_count': len(invalid_codes),
            'pattern_analysis': pattern_analysis,
            'retailer_breakdown': retailer_issues,
            'sample_codes': [c['codigo_interno'] for c in invalid_codes[:10]]
        }
    
    def create_prevention_plan(self):
        """📋 4. Crear plan detallado de prevención"""
        print("\n" + "📋" + "="*80 + "📋")
        print("📋 PLAN DETALLADO DE PREVENCIÓN DE PROBLEMAS")
        print("📋" + "="*80 + "📋")
        
        prevention_plan = {
            "immediate_actions": [],
            "validation_improvements": [],
            "database_constraints": [],
            "monitoring_systems": [],
            "process_improvements": []
        }
        
        # 1. Acciones Inmediatas
        print(f"\n🚨 1. ACCIONES INMEDIATAS (PRÓXIMAS 24H):")
        
        immediate_actions = [
            "🔗 Limpiar links duplicados existentes con UPDATE/DELETE",
            "💸 Corregir precios inválidos intercambiando normal ↔ oferta donde sea lógico",
            "📝 Regenerar códigos internos inválidos con algoritmo mejorado",
            "🛡️ Implementar validación temporal en scrapers para prevenir nuevos casos"
        ]
        
        for action in immediate_actions:
            print(f"   {action}")
            prevention_plan["immediate_actions"].append(action)
        
        # 2. Mejoras de Validación
        print(f"\n🛡️ 2. MEJORAS DE VALIDACIÓN EN SCRAPERS:")
        
        validation_improvements = [
            "🔗 URL Validation: Validar que links sean URLs válidas o usar NULL",
            "💰 Price Logic: Validar que precio_oferta ≤ precio_normal siempre",
            "📝 Code Format: Validar formato CL-X-X-X-X-X antes de insertar",
            "🔍 Duplicate Check: Verificar duplicados por URL antes de insertar",
            "📊 Data Sanitization: Limpiar caracteres especiales en campos texto"
        ]
        
        for improvement in validation_improvements:
            print(f"   {improvement}")
            prevention_plan["validation_improvements"].append(improvement)
        
        # 3. Constraints de Base de Datos
        print(f"\n🗄️ 3. CONSTRAINTS DE BASE DE DATOS:")
        
        db_constraints = [
            "UNIQUE constraint en link (ignorando NULL)",
            "CHECK constraint para precio_oferta ≤ precio_normal",
            "CHECK constraint para formato de codigo_interno con regex",
            "TRIGGER para validación automática en INSERT/UPDATE",
            "PARTIAL INDEX en links no nulos para mejor rendimiento"
        ]
        
        for constraint in db_constraints:
            print(f"   • {constraint}")
            prevention_plan["database_constraints"].append(constraint)
        
        # 4. Sistema de Monitoreo
        print(f"\n📊 4. SISTEMA DE MONITOREO CONTINUO:")
        
        monitoring_systems = [
            "🔍 Daily Audit: Script diario que detecte problemas automáticamente",
            "📧 Alert System: Notificaciones cuando se detecten anomalías",
            "📈 Dashboard: Métricas de calidad de datos en tiempo real",
            "🏥 Health Check: Endpoint de salud que incluya integridad de datos",
            "📋 Weekly Report: Reporte semanal de calidad de datos"
        ]
        
        for system in monitoring_systems:
            print(f"   {system}")
            prevention_plan["monitoring_systems"].append(system)
        
        # 5. Mejoras de Proceso
        print(f"\n🔄 5. MEJORAS DE PROCESO DE SCRAPING:")
        
        process_improvements = [
            "🎯 Staging Area: Área temporal para validar datos antes de insertar",
            "🔄 Rollback System: Capacidad de deshacer inserts problemáticos",
            "📝 Data Pipeline: Pipeline con validaciones en múltiples etapas",
            "🧪 Testing Framework: Tests automáticos para validar scrapers",
            "📊 Quality Metrics: KPIs de calidad de datos por retailer"
        ]
        
        for improvement in process_improvements:
            print(f"   {improvement}")
            prevention_plan["process_improvements"].append(improvement)
        
        # Timeline de implementación
        print(f"\n⏰ 6. TIMELINE DE IMPLEMENTACIÓN:")
        
        timeline = [
            ("Día 1", "Acciones inmediatas + constraints básicos"),
            ("Semana 1", "Mejoras de validación en scrapers"),
            ("Semana 2", "Sistema de monitoreo básico"),
            ("Mes 1", "Pipeline completo + dashboard"),
            ("Mes 2", "Testing framework + automatización completa")
        ]
        
        for period, tasks in timeline:
            print(f"   📅 {period}: {tasks}")
        
        # Guardar plan en archivo
        prevention_plan["timeline"] = timeline
        prevention_plan["creation_date"] = datetime.now().isoformat()
        
        plan_file = f"data_integrity_prevention_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(prevention_plan, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 PLAN GUARDADO EN: {plan_file}")
        
        return prevention_plan
    
    def generate_sql_fixes(self):
        """🛠️ Generar SQL para correcciones inmediatas"""
        print("\n" + "🛠️" + "="*80 + "🛠️")
        print("🛠️ GENERANDO SQL PARA CORRECCIONES INMEDIATAS")
        print("🛠️" + "="*80 + "🛠️")
        
        sql_fixes = []
        
        # 1. SQL para limpiar links duplicados
        sql_fixes.append({
            "name": "Limpiar Links Duplicados",
            "sql": """
-- 1. Limpiar links duplicados manteniendo solo el más reciente
WITH duplicated_links AS (
    SELECT link, 
           codigo_interno,
           created_at,
           ROW_NUMBER() OVER (PARTITION BY link ORDER BY created_at DESC) as rn
    FROM master_productos
    WHERE link IS NOT NULL 
    AND link != ''
    AND link IN (
        SELECT link 
        FROM master_productos 
        WHERE link IS NOT NULL 
        GROUP BY link 
        HAVING COUNT(*) > 1
    )
)
UPDATE master_productos 
SET link = NULL 
WHERE codigo_interno IN (
    SELECT codigo_interno 
    FROM duplicated_links 
    WHERE rn > 1
);
            """,
            "description": "Mantiene solo el registro más reciente para cada link duplicado"
        })
        
        # 2. SQL para corregir precios inválidos
        sql_fixes.append({
            "name": "Corregir Precios Inválidos",
            "sql": """
-- 2. Intercambiar precio_normal y precio_oferta cuando oferta > normal
UPDATE master_precios 
SET 
    precio_normal = precio_oferta,
    precio_oferta = precio_normal
WHERE precio_oferta > precio_normal 
AND precio_oferta IS NOT NULL
AND precio_normal IS NOT NULL;

-- Agregar comentario de corrección
UPDATE master_precios 
SET observaciones = COALESCE(observaciones || '; ', '') || 'Precios intercambiados por corrección automática'
WHERE precio_oferta > precio_normal 
AND precio_oferta IS NOT NULL;
            """,
            "description": "Intercambia precios normal y oferta cuando la lógica está invertida"
        })
        
        # 3. SQL para agregar constraints
        sql_fixes.append({
            "name": "Agregar Constraints de Validación",
            "sql": """
-- 3. Agregar constraints de validación
-- UNIQUE constraint para links (ignorando NULL)
CREATE UNIQUE INDEX CONCURRENTLY idx_unique_link 
ON master_productos (link) 
WHERE link IS NOT NULL AND link != '';

-- CHECK constraint para precios
ALTER TABLE master_precios 
ADD CONSTRAINT chk_precio_oferta_valido 
CHECK (precio_oferta IS NULL OR precio_oferta <= precio_normal);

-- CHECK constraint para formato de código interno
ALTER TABLE master_productos 
ADD CONSTRAINT chk_codigo_formato 
CHECK (codigo_interno ~ '^CL-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z]+-[A-Z0-9]+$');
            """,
            "description": "Agrega constraints para prevenir problemas futuros"
        })
        
        # 4. SQL para monitoreo
        sql_fixes.append({
            "name": "Crear Vistas de Monitoreo",
            "sql": """
-- 4. Crear vistas para monitoreo continuo
CREATE OR REPLACE VIEW v_data_quality_dashboard AS
SELECT 
    'Links Duplicados' as issue_type,
    COUNT(*) as count
FROM (
    SELECT link 
    FROM master_productos 
    WHERE link IS NOT NULL 
    GROUP BY link 
    HAVING COUNT(*) > 1
) duplicates

UNION ALL

SELECT 
    'Precios Inválidos' as issue_type,
    COUNT(*) as count
FROM master_precios 
WHERE precio_oferta > precio_normal

UNION ALL

SELECT 
    'Códigos Inválidos' as issue_type,
    COUNT(*) as count
FROM master_productos 
WHERE codigo_interno NOT LIKE 'CL-%-%-%-%-%';

-- Vista para productos sin precios
CREATE OR REPLACE VIEW v_productos_sin_precios AS
SELECT p.codigo_interno, p.nombre, p.retailer, p.created_at
FROM master_productos p
LEFT JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
WHERE pr.codigo_interno IS NULL;
            """,
            "description": "Crea vistas para monitoreo continuo de calidad de datos"
        })
        
        # Guardar SQLs en archivo
        sql_file = f"data_integrity_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- SQL PARA CORRECCIONES DE INTEGRIDAD DE DATOS\n")
            f.write(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for fix in sql_fixes:
                f.write(f"-- {fix['name']}\n")
                f.write(f"-- {fix['description']}\n")
                f.write(fix['sql'])
                f.write("\n\n")
        
        print(f"💾 SQL GUARDADO EN: {sql_file}")
        
        for fix in sql_fixes:
            print(f"\n🛠️ {fix['name']}:")
            print(f"   📝 {fix['description']}")
        
        return sql_fixes
    
    def run_investigation(self):
        """🚀 Ejecutar investigación completa"""
        print("🔍" + "="*80 + "🔍")
        print("🚀 INVESTIGACIÓN COMPLETA DE PROBLEMAS DE INTEGRIDAD")
        print("🔍" + "="*80 + "🔍")
        
        investigation_steps = [
            ("🔗 Links Duplicados", self.investigate_duplicate_links),
            ("💸 Precios Inválidos", self.investigate_invalid_prices),
            ("📝 Códigos Incorrectos", self.investigate_invalid_codes),
            ("📋 Plan de Prevención", self.create_prevention_plan),
            ("🛠️ SQL Fixes", self.generate_sql_fixes)
        ]
        
        for step_name, step_func in investigation_steps:
            try:
                print(f"\n⏳ Ejecutando: {step_name}...")
                step_func()
                print(f"✅ {step_name} completado")
            except Exception as e:
                print(f"❌ Error en {step_name}: {e}")
                import traceback
                print(f"🔍 Detalle: {traceback.format_exc()}")
        
        print("\n🎉 INVESTIGACIÓN COMPLETA FINALIZADA")
        print("📋 RESUMEN DE ARCHIVOS GENERADOS:")
        print("   📄 Plan de prevención: data_integrity_prevention_plan_*.json")
        print("   🛠️ Correcciones SQL: data_integrity_fixes_*.sql")
    
    def close(self):
        """🔚 Cerrar conexiones"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("🔚 Conexiones cerradas")

def main():
    """🚀 Función principal"""
    print("🔍 Iniciando Investigación de Problemas de Integridad...")
    
    investigator = DataIntegrityIssueInvestigator()
    
    try:
        investigator.run_investigation()
    except KeyboardInterrupt:
        print("\n⏹️ Investigación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico durante investigación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        investigator.close()

if __name__ == "__main__":
    main()