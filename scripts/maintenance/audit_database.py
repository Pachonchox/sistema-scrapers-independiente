#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auditoría Completa de Base de Datos PostgreSQL
===============================================

Verifica:
1. Constraints críticos del README
2. Lógica de snapshots diarios (1 precio por producto por día)
3. Actualización a medianoche (00:00)
4. Integridad referencial
5. Duplicados y violaciones

CONSTRAINT CRÍTICO: Solo puede haber 1 registro por producto por día en master_precios
"""

import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class DatabaseAuditor:
    def __init__(self):
        """Inicializar auditor de base de datos"""
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'price_orchestrator'),
            user=os.getenv('PGUSER', 'orchestrator'),
            password=os.getenv('PGPASSWORD', 'orchestrator_2025')
        )
        self.cursor = self.conn.cursor()
        self.violations = []
        self.warnings = []
        self.stats = {}
        
    def audit_master_productos_constraints(self):
        """Verificar constraints de master_productos"""
        print("\n" + "="*70)
        print("1. AUDITANDO MASTER_PRODUCTOS")
        print("="*70)
        
        # 1.1 Verificar PRIMARY KEY (codigo_interno)
        self.cursor.execute("""
            SELECT COUNT(*), COUNT(DISTINCT codigo_interno) 
            FROM master_productos
        """)
        total, unique = self.cursor.fetchone()
        
        if total != unique:
            self.violations.append(f"VIOLACIÓN PK: {total-unique} códigos internos duplicados")
        else:
            print("[OK] PRIMARY KEY (codigo_interno): OK")
            
        # 1.2 Verificar UNIQUE constraint en link
        self.cursor.execute("""
            SELECT link, COUNT(*) as cnt
            FROM master_productos
            GROUP BY link
            HAVING COUNT(*) > 1
        """)
        duplicated_links = self.cursor.fetchall()
        
        if duplicated_links:
            self.violations.append(f"VIOLACIÓN UNIQUE: {len(duplicated_links)} links duplicados")
            for link, count in duplicated_links[:3]:
                print(f"  [AVISO] Link duplicado {count} veces: {link[:50]}...")
        else:
            print("[OK] UNIQUE (link): OK")
            
        # 1.3 Verificar formato código interno (CL-MARCA-MODELO-SPEC-RET-SEQ)
        self.cursor.execute("""
            SELECT codigo_interno
            FROM master_productos
            WHERE codigo_interno NOT LIKE 'CL-%-%-%-%-%'
            LIMIT 5
        """)
        invalid_codes = self.cursor.fetchall()
        
        if invalid_codes:
            self.warnings.append(f"FORMATO: {len(invalid_codes)} códigos no siguen formato CL-X-X-X-X-X")
            for code in invalid_codes:
                print(f"  [AVISO] Código inválido: {code[0]}")
        else:
            print("[OK] Formato códigos internos: OK")
            
        # Estadísticas
        self.cursor.execute("""
            SELECT retailer, COUNT(*) 
            FROM master_productos 
            GROUP BY retailer
        """)
        retailer_stats = self.cursor.fetchall()
        
        print("\nProductos por retailer:")
        for retailer, count in retailer_stats:
            print(f"  {retailer}: {count:,} productos")
            
    def audit_master_precios_constraints(self):
        """Verificar constraints críticos de master_precios"""
        print("\n" + "="*70)
        print("2. AUDITANDO MASTER_PRECIOS - CONSTRAINT CRÍTICO")
        print("="*70)
        
        # 2.1 CONSTRAINT CRÍTICO: Solo 1 precio por producto por día
        print("\n[AVISO] VERIFICANDO CONSTRAINT CRÍTICO: 1 precio por producto por día")
        
        self.cursor.execute("""
            SELECT codigo_interno, fecha, COUNT(*) as registros
            FROM master_precios
            GROUP BY codigo_interno, fecha
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        duplicated_prices = self.cursor.fetchall()
        
        if duplicated_prices:
            total_violations = len(duplicated_prices)
            self.violations.append(f"VIOLACIÓN CRÍTICA: {total_violations} productos con múltiples precios el mismo día")
            print(f"\n[ERROR] VIOLACIÓN DETECTADA: {total_violations} casos de múltiples precios por día")
            print("\nEjemplos de violaciones:")
            for codigo, fecha, count in duplicated_prices[:5]:
                print(f"  Producto {codigo}: {count} precios el {fecha}")
        else:
            print("[CUMPLIDO] CONSTRAINT CRÍTICO CUMPLIDO: Solo 1 precio por producto por día")
            
        # 2.2 Verificar lógica de snapshots diarios
        print("\n[AVISO] VERIFICANDO LÓGICA DE SNAPSHOTS DIARIOS")
        
        # Últimos 7 días con datos
        self.cursor.execute("""
            SELECT fecha, 
                   COUNT(DISTINCT codigo_interno) as productos,
                   COUNT(*) as registros,
                   MIN(timestamp_creacion::time) as primera_hora,
                   MAX(timestamp_creacion::time) as ultima_hora
            FROM master_precios
            WHERE fecha >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY fecha
            ORDER BY fecha DESC
        """)
        daily_stats = self.cursor.fetchall()
        
        print("\nSnapshots últimos 7 días:")
        for fecha, productos, registros, primera, ultima in daily_stats:
            ratio = registros / productos if productos > 0 else 0
            status = "[CUMPLIDO]" if ratio == 1.0 else "[AVISO]️"
            print(f"  {fecha}: {productos:,} productos, {registros:,} registros "
                  f"(ratio: {ratio:.2f}) {status}")
            print(f"    Primera: {primera}, Última: {ultima}")
            
        # 2.3 Verificar cambios intradiarios
        print("\n[AVISO] VERIFICANDO ACTUALIZACIONES INTRADIARIAS")
        
        self.cursor.execute("""
            SELECT fecha, codigo_interno, cambios_en_dia
            FROM master_precios
            WHERE cambios_en_dia > 1
            AND fecha >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY cambios_en_dia DESC
            LIMIT 10
        """)
        intraday_changes = self.cursor.fetchall()
        
        if intraday_changes:
            print(f"\n{len(intraday_changes)} productos con cambios intradiarios:")
            for fecha, codigo, cambios in intraday_changes[:5]:
                print(f"  {fecha}: {codigo} tuvo {cambios} cambios")
        else:
            print("No hay cambios intradiarios registrados")
            
    def audit_midnight_logic(self):
        """Verificar lógica de cierre a medianoche"""
        print("\n" + "="*70)
        print("3. AUDITANDO LÓGICA DE MEDIANOCHE (00:00)")
        print("="*70)
        
        # Verificar distribución horaria
        self.cursor.execute("""
            SELECT 
                EXTRACT(HOUR FROM timestamp_creacion) as hora,
                COUNT(*) as registros
            FROM master_precios
            WHERE fecha >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY hora
            ORDER BY hora
        """)
        hourly_dist = self.cursor.fetchall()
        
        print("\nDistribución horaria de registros (últimos 7 días):")
        for hora, count in hourly_dist:
            bar = "#" * min(50, count // 100)
            print(f"  {int(hora):02d}:00: {count:,} {bar}")
            
        # Verificar registros cerca de medianoche
        self.cursor.execute("""
            SELECT fecha,
                   COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp_creacion) >= 23) as antes_medianoche,
                   COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp_creacion) < 1) as despues_medianoche
            FROM master_precios
            WHERE fecha >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY fecha
        """)
        midnight_stats = self.cursor.fetchall()
        
        print("\nRegistros alrededor de medianoche:")
        for fecha, antes, despues in midnight_stats:
            print(f"  {fecha}: {antes} antes (23:00-23:59), {despues} después (00:00-00:59)")
            
    def audit_data_integrity(self):
        """Verificar integridad general de datos"""
        print("\n" + "="*70)
        print("4. AUDITANDO INTEGRIDAD DE DATOS")
        print("="*70)
        
        # 4.1 Productos sin precios
        self.cursor.execute("""
            SELECT p.codigo_interno, p.nombre, p.retailer
            FROM master_productos p
            LEFT JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno
            WHERE pr.codigo_interno IS NULL
            LIMIT 10
        """)
        orphan_products = self.cursor.fetchall()
        
        if orphan_products:
            self.warnings.append(f"INTEGRIDAD: {len(orphan_products)} productos sin precios")
            print(f"\n[AVISO] {len(orphan_products)} productos sin precios:")
            for codigo, nombre, retailer in orphan_products[:3]:
                print(f"  {codigo}: {nombre[:50]}... ({retailer})")
                
        # 4.2 Precios sin productos (violación FK)
        self.cursor.execute("""
            SELECT pr.codigo_interno, COUNT(*)
            FROM master_precios pr
            LEFT JOIN master_productos p ON pr.codigo_interno = p.codigo_interno
            WHERE p.codigo_interno IS NULL
            GROUP BY pr.codigo_interno
            LIMIT 10
        """)
        orphan_prices = self.cursor.fetchall()
        
        if orphan_prices:
            self.violations.append(f"VIOLACIÓN FK: Precios sin productos")
            print(f"\n[ERROR] Precios sin productos (violación FK):")
            for codigo, count in orphan_prices[:3]:
                print(f"  {codigo}: {count} precios huérfanos")
                
        # 4.3 Validación de precios
        self.cursor.execute("""
            SELECT codigo_interno, fecha, precio_normal, precio_oferta, precio_tarjeta
            FROM master_precios
            WHERE (precio_normal < 0 OR precio_oferta < 0 OR precio_tarjeta < 0)
               OR (precio_oferta > precio_normal AND precio_oferta IS NOT NULL)
               OR (precio_tarjeta > precio_normal AND precio_tarjeta IS NOT NULL)
            LIMIT 10
        """)
        invalid_prices = self.cursor.fetchall()
        
        if invalid_prices:
            self.violations.append("VALIDACIÓN: Precios con valores inválidos")
            print(f"\n[ERROR] Precios con valores inválidos:")
            for row in invalid_prices[:3]:
                print(f"  {row[0]} ({row[1]}): Normal={row[2]}, Oferta={row[3]}, Tarjeta={row[4]}")
                
    def generate_report(self):
        """Generar reporte final de auditoría"""
        print("\n" + "="*70)
        print(" REPORTE FINAL DE AUDITORÍA")
        print("="*70)
        
        # Estadísticas generales
        self.cursor.execute("SELECT COUNT(*) FROM master_productos")
        total_products = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM master_precios")
        total_prices = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(DISTINCT fecha) FROM master_precios")
        days_with_data = self.cursor.fetchone()[0]
        
        print(f"\n[STATS] ESTADÍSTICAS GENERALES:")
        print(f"  Total productos: {total_products:,}")
        print(f"  Total registros precios: {total_prices:,}")
        print(f"  Días con datos: {days_with_data}")
        print(f"  Promedio precios/día: {total_prices/days_with_data if days_with_data > 0 else 0:,.0f}")
        
        # Violaciones críticas
        if self.violations:
            print(f"\n[ERROR] VIOLACIONES CRÍTICAS ENCONTRADAS: {len(self.violations)}")
            for violation in self.violations:
                print(f"  • {violation}")
        else:
            print("\n[CUMPLIDO] NO SE ENCONTRARON VIOLACIONES CRÍTICAS")
            
        # Advertencias
        if self.warnings:
            print(f"\n[AVISO]️ ADVERTENCIAS: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  • {warning}")
                
        # Recomendaciones
        print("\n[TIPS] RECOMENDACIONES:")
        
        if any("múltiples precios" in v for v in self.violations):
            print("  1. CRÍTICO: Implementar UNIQUE constraint (codigo_interno, fecha) en master_precios")
            print("     ALTER TABLE master_precios ADD CONSTRAINT unique_price_per_day UNIQUE (codigo_interno, fecha);")
            
        print("  2. Implementar trigger para midnight_closure automático")
        print("  3. Agregar constraint CHECK para validación de precios")
        print("  4. Configurar particionado por fecha para mejor performance")
        
    def close(self):
        """Cerrar conexión"""
        self.cursor.close()
        self.conn.close()

def main():
    """Ejecutar auditoría completa"""
    print("INICIANDO AUDITORIA DE BASE DE DATOS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    auditor = DatabaseAuditor()
    
    try:
        auditor.audit_master_productos_constraints()
        auditor.audit_master_precios_constraints()
        auditor.audit_midnight_logic()
        auditor.audit_data_integrity()
        auditor.generate_report()
    finally:
        auditor.close()
    
    print("\nAuditoria completada")

if __name__ == "__main__":
    main()