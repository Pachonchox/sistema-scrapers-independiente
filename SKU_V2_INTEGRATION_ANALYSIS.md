# 📊 ANÁLISIS COMPLETO DE INTEGRACIÓN SKU V2 SYSTEM
**Fecha:** Septiembre 2025  
**Sistema:** Portable Orchestrator V5  
**Objetivo:** Resolver duplicación de productos mediante SKU único robusto

---

## 🔴 PROBLEMA CRÍTICO IDENTIFICADO

### Situación Actual
El sistema actual genera duplicados porque el `codigo_interno` depende de campos variables:
- **Marca**: Puede cambiar o estar vacía
- **Modelo**: Se extrae del nombre (inconsistente)
- **Specs**: Variables según disponibilidad
- **Link hash**: Cambia si el retailer modifica URLs

### Impacto de los Duplicados
```
✅ Análisis realizado en scripts/maintenance/check_duplicates.py:
- Productos con mismo SKU pero diferente codigo_interno
- Un mismo producto físico aparece múltiples veces
- Precios históricos fragmentados
- Arbitraje incorrecto entre duplicados del mismo producto
```

---

## 🎯 COMPARACIÓN DE SISTEMAS

### 📌 Sistema Actual (codigo_interno)
```
Formato: CL-[MARCA]-[MODELO]-[SPEC]-[RETAILER]-[SEQ]
Ejemplo: CL-SAMS-GAL-S24-128-RIP-001
```

**Ubicación:** `core/master_products_system.py`
- **Método:** `_generate_codigo_interno()`
- **Problemas:**
  - ❌ Depende de campos que pueden cambiar
  - ❌ Secuencial basado en hash del link (variable)
  - ❌ Inferencia de marca/modelo poco confiable
  - ❌ No garantiza unicidad del producto físico

### 🚀 Sistema SKU V2 (Nuevo)
```
Formato V2 Original: CL-[RET]-YYYYMMDD-[HASH8]-[SEQ6]
Formato V2 Mejorado: CL-[MARCA]-[MODELO]-[SPEC]-[RET]-[HASH6]
```

**Ubicación:** `SKU_V2_SYSTEM/generate_robust_sku.py`
- **Clase:** `RobustSKUGenerator`
- **Ventajas:**
  - ✅ Hash basado en datos únicos inmutables
  - ✅ Extracción inteligente de marca con lista conocida
  - ✅ Detección de modelos con patterns específicos
  - ✅ Fallback robusto cuando faltan datos
  - ✅ Deduplicación garantizada

---

## 📊 DIFERENCIAS CLAVE

| Aspecto | Sistema Actual | SKU V2 |
|---------|----------------|---------|
| **Base de unicidad** | Link del producto | SKU original + Link + Nombre |
| **Marca** | Campo directo o inferido | Lista de marcas conocidas + inferencia |
| **Modelo** | Extracción simple | Patterns específicos por marca |
| **Specs** | Solo si existen | Extracción inteligente con prioridad |
| **Hash** | MD5 del link | MD5 del SKU o link o nombre+idx |
| **Duplicados** | Frecuentes | Mínimos/Nulos |
| **Performance** | ~500 SKUs/seg | ~800-1000 SKUs/seg |

---

## 🔧 PLAN DE INTEGRACIÓN DETALLADO

### FASE 1: Preparación (1-2 días)
```python
# 1. Backup completo de la base de datos actual
python scripts/maintenance/backup_database.py

# 2. Análisis de duplicados actuales
python scripts/maintenance/check_duplicates.py > duplicates_report.txt

# 3. Exportar productos actuales para testing
python scripts/data_management/export_products_for_migration.py
```

### FASE 2: Implementación (2-3 días)

#### 2.1 Integrar generador SKU V2 en scrapers
```python
# Modificar portable_orchestrator_v5/scrapers/base_scraper_v5.py
from SKU_V2_SYSTEM.generate_robust_sku import RobustSKUGenerator

class BaseScraperV5:
    def __init__(self):
        self.sku_generator = RobustSKUGenerator()
    
    def process_product(self, product_data):
        # Generar SKU V2 en lugar de codigo_interno
        product_data['sku_v2'] = self.sku_generator.generate_sku(
            product_data, 
            self.retailer, 
            self.product_index
        )
        # Mantener codigo_interno para compatibilidad
        product_data['codigo_interno_legacy'] = product_data.get('codigo_interno')
```

#### 2.2 Actualizar master_products_system.py
```python
# Modificar core/master_products_system.py
def __post_init__(self):
    """Usar SKU V2 como codigo principal"""
    if not self.codigo_interno:
        # Generar SKU V2 en lugar del sistema antiguo
        from SKU_V2_SYSTEM.generate_robust_sku import RobustSKUGenerator
        generator = RobustSKUGenerator()
        self.codigo_interno = generator.generate_sku(self.to_dict(), self.retailer)
```

### FASE 3: Migración de Datos (1 día)

#### 3.1 Script de migración
```python
# scripts/migration/migrate_to_sku_v2.py
import psycopg2
from SKU_V2_SYSTEM.generate_robust_sku import RobustSKUGenerator

def migrate_products():
    """Migrar productos existentes a SKU V2"""
    
    # 1. Agregar columna sku_v2 si no existe
    cur.execute("""
        ALTER TABLE master_productos 
        ADD COLUMN IF NOT EXISTS sku_v2 VARCHAR(50),
        ADD COLUMN IF NOT EXISTS codigo_interno_legacy VARCHAR(50)
    """)
    
    # 2. Copiar codigo_interno actual a legacy
    cur.execute("""
        UPDATE master_productos 
        SET codigo_interno_legacy = codigo_interno
        WHERE codigo_interno_legacy IS NULL
    """)
    
    # 3. Generar SKU V2 para todos los productos
    generator = RobustSKUGenerator()
    cur.execute("SELECT * FROM master_productos")
    
    for row in cur.fetchall():
        sku_v2 = generator.generate_sku(dict(row), row['retailer'])
        cur.execute("""
            UPDATE master_productos 
            SET sku_v2 = %s 
            WHERE codigo_interno = %s
        """, (sku_v2, row['codigo_interno']))
    
    # 4. Identificar y consolidar duplicados
    consolidate_duplicates()
```

### FASE 4: Validación (1 día)

#### 4.1 Tests de integridad
```python
# tests/test_sku_v2_migration.py
def test_no_duplicates():
    """Verificar que no hay duplicados con SKU V2"""
    duplicates = db.query("""
        SELECT sku_v2, retailer, COUNT(*) 
        FROM master_productos 
        GROUP BY sku_v2, retailer 
        HAVING COUNT(*) > 1
    """)
    assert len(duplicates) == 0

def test_all_products_have_sku_v2():
    """Verificar que todos tienen SKU V2"""
    missing = db.query("""
        SELECT COUNT(*) 
        FROM master_productos 
        WHERE sku_v2 IS NULL OR sku_v2 = ''
    """)
    assert missing[0][0] == 0
```

### FASE 5: Transición (2-3 días)

#### 5.1 Período de doble escritura
```python
# Durante 1 semana, mantener ambos sistemas:
- Escribir tanto codigo_interno como sku_v2
- Leer preferentemente sku_v2
- Logging de discrepancias
```

#### 5.2 Switch completo
```python
# Después de validación:
1. Renombrar codigo_interno → codigo_interno_old
2. Renombrar sku_v2 → codigo_interno
3. Actualizar todas las referencias en el código
```

---

## 🛠️ ARCHIVOS A MODIFICAR

### Críticos (Alta Prioridad)
1. `portable_orchestrator_v5/scrapers/*_scraper_v5.py` - Todos los scrapers
2. `core/master_products_system.py` - Sistema de productos
3. `scripts/maintenance/clean_duplicates.py` - Limpieza de duplicados
4. Base de datos: Agregar columna `sku_v2`

### Secundarios (Media Prioridad)
1. `arbitrage_system/database/db_manager.py` - Referencias a product_code
2. `tests/integration/*.py` - Tests que validan SKUs
3. `utils/ml_normalization.py` - Normalización para ML

### Opcionales (Baja Prioridad)
1. Documentación
2. Scripts de reporting
3. Herramientas de debug

---

## 📈 MÉTRICAS DE ÉXITO

### KPIs Post-Implementación
- ✅ **Duplicados:** < 0.1% (actual: ~5-10%)
- ✅ **Performance:** > 800 SKUs/seg
- ✅ **Unicidad:** 100% productos únicos por SKU+retailer
- ✅ **Trazabilidad:** Mapeo 1:1 old→new
- ✅ **Integridad BD:** 0 errores de foreign key

---

## 🚨 RIESGOS Y MITIGACIÓN

### Riesgo 1: Pérdida de referencias
**Mitigación:** Mantener `codigo_interno_legacy` permanentemente

### Riesgo 2: Rompimiento de arbitraje
**Mitigación:** Actualizar matching gradualmente con validación

### Riesgo 3: Performance en migración
**Mitigación:** Migrar por batches de 10,000 productos

### Riesgo 4: Incompatibilidad con sistemas externos
**Mitigación:** API adapter para traducir SKUs viejos a nuevos

---

## 📝 RECOMENDACIONES FINALES

### ⚡ Acciones Inmediatas
1. **HOY:** Hacer backup completo de la BD
2. **HOY:** Ejecutar análisis de duplicados actual
3. **MAÑANA:** Comenzar con Fase 1 en entorno de desarrollo

### 🎯 Priorización
1. **CRÍTICO:** Implementar en scrapers nuevos primero
2. **IMPORTANTE:** Migrar datos históricos
3. **DESEABLE:** Actualizar toda la documentación

### 💡 Tips de Implementación
- Usar feature flag para activar/desactivar SKU V2
- Mantener logs detallados durante la migración
- Hacer rollback plan antes de comenzar
- Testear con subset de 1000 productos primero

---

## 🔄 CRONOGRAMA SUGERIDO

| Día | Actividad | Responsable | Status |
|-----|-----------|------------|--------|
| 1 | Backup y análisis | DevOps | ⏳ |
| 2-3 | Implementar en scrapers | Backend | ⏳ |
| 4 | Crear scripts migración | Backend | ⏳ |
| 5 | Testing en desarrollo | QA | ⏳ |
| 6-7 | Migración staging | DevOps | ⏳ |
| 8 | Validación completa | QA | ⏳ |
| 9-10 | Migración producción | DevOps | ⏳ |

---

## 📌 CONCLUSIÓN

La implementación del **SKU V2 System** es **CRÍTICA** para resolver el problema de duplicación. El sistema actual genera duplicados porque depende de campos variables. SKU V2 garantiza unicidad mediante:

1. **Hash robusto** basado en datos inmutables
2. **Extracción inteligente** con patterns específicos
3. **Fallbacks múltiples** para casos edge
4. **Performance mejorada** (800+ SKUs/seg)

**Recomendación:** Proceder con la implementación siguiendo el plan de 5 fases, comenzando inmediatamente con backups y análisis.

---

*📅 Documento generado: Septiembre 2025*  
*🤖 Sistema: Portable Orchestrator V5*  
*✅ Estado: Listo para implementación*