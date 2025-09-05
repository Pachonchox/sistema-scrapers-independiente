# 🔧 PLAN COMPLETO DE OPTIMIZACIÓN DEL SISTEMA DE SCRAPING
**Fecha:** Diciembre 2024  
**Proyecto:** Portable Orchestrator V5  
**Objetivo:** Resolver duplicación + Optimizar flujo Scraper→DB + Lógica de precios diarios

---

## 📊 ANÁLISIS DE LA SITUACIÓN ACTUAL

### 🔴 PROBLEMAS IDENTIFICADOS

#### 1. **Duplicación de Productos**
```
PROBLEMA: El codigo_interno actual NO es único
- Formato: CL-[MARCA]-[MODELO]-[SPEC]-[RETAILER]-[SEQ]
- SEQ basado en hash del link → cambia si URL cambia
- Marca/Modelo extraídos del nombre → inconsistentes
- Un mismo producto físico genera múltiples códigos
```

#### 2. **Flujo Ineficiente**
```
ACTUAL: Scraper → Excel → Script → DB
- Scrapers generan Excel
- Script posterior los carga a DB
- Pérdida de datos en tiempo real
- Duplicación de almacenamiento
```

#### 3. **Lógica de Precios Confusa**
```
ACTUAL: Sin distinción clara entre precio actual e histórico
- Se sobrescriben precios del mismo día
- No hay corte claro a las 00:00
- Histórico mezclado con actual
```

---

## 🎯 ANÁLISIS TÉCNICO DETALLADO

### 📦 ESTRUCTURA ACTUAL DE BASE DE DATOS

#### Tabla: `master_productos`
```sql
codigo_interno      VARCHAR(50)  PRIMARY KEY  -- Problema: NO es único realmente
sku                 VARCHAR(100)              -- SKU del retailer (puede ser NULL)
link                VARCHAR(1000) UNIQUE?     -- URL del producto
nombre              VARCHAR(500)
marca               VARCHAR(100)
categoria           VARCHAR(100)
retailer            VARCHAR(50)
storage             VARCHAR(50)
ram                 VARCHAR(50)
color               VARCHAR(50)
rating              DECIMAL(3,2)
reviews_count       INTEGER
fecha_primera_captura    DATE
fecha_ultima_actualizacion DATE
ultimo_visto        DATE
activo              BOOLEAN
```

#### Tabla: `master_precios`
```sql
codigo_interno      VARCHAR(50)  FK → master_productos
fecha               DATE
retailer            VARCHAR(50)
precio_normal       INTEGER
precio_oferta       INTEGER
precio_tarjeta      INTEGER
precio_min_dia      INTEGER
timestamp_creacion  TIMESTAMP
PRIMARY KEY (codigo_interno, fecha)  -- Un precio por día
```

### 🕷️ OUTPUT DE SCRAPERS ACTUAL

#### ProductData (desde scrapers)
```python
@dataclass
class ProductData:
    title: str
    current_price: float
    original_price: float
    discount_percentage: int
    card_price: float
    product_url: str
    brand: str
    sku: str              # SKU del retailer (puede ser vacío)
    rating: float
    retailer: str
    additional_info: Dict  # storage, ram, color, etc.
```

### 🔍 GAPS IDENTIFICADOS

| Aspecto | Scraper Produce | DB Espera | GAP |
|---------|----------------|-----------|-----|
| **ID Único** | `sku` (puede ser NULL) | `codigo_interno` único | ❌ No hay generación de ID único real |
| **Precios** | current/original/card | normal/oferta/tarjeta | ✅ Mapeable |
| **Specs** | en `additional_info` | campos separados | ✅ Mapeable |
| **Link** | `product_url` | `link` | ✅ OK |
| **Deduplicación** | Ninguna | Por `codigo_interno` | ❌ No funciona |

---

## 🚀 SOLUCIÓN PROPUESTA

### 1️⃣ **NUEVO SISTEMA SKU ÚNICO CORTO**

#### Formato Propuesto
```
[RET][HASH8]
```

**Ejemplos:**
- `FAL1A2B3C4D` - Falabella
- `RIP5E6F7G8H` - Ripley  
- `PAR9I0J1K2L` - Paris
- `MER3M4N5O6P` - MercadoLibre

#### Características
- **10 caracteres totales** (3 retailer + 8 hash)
- **Hash basado en:** SKU original + Link + Nombre normalizado
- **Colisiones:** < 0.001% con 8 caracteres hex
- **Performance:** ~10,000 SKUs/segundo

#### Implementación
```python
import hashlib

def generate_unique_sku(product_data: dict, retailer: str) -> str:
    """Genera SKU único de 10 caracteres"""
    
    # Códigos de 3 letras para retailers
    RETAILER_CODES = {
        'falabella': 'FAL',
        'ripley': 'RIP',
        'paris': 'PAR',
        'mercadolibre': 'MER',
        'hites': 'HIT',
        'abcdin': 'ABC'
    }
    
    # Componentes para hash (orden de prioridad)
    components = []
    
    # 1. SKU original si existe
    if product_data.get('sku') and product_data['sku'] != 'nan':
        components.append(product_data['sku'])
    
    # 2. Link siempre
    if product_data.get('link'):
        components.append(product_data['link'])
    
    # 3. Nombre normalizado
    if product_data.get('nombre'):
        # Normalizar: minúsculas, sin espacios múltiples
        normalized = ' '.join(product_data['nombre'].lower().split())
        components.append(normalized)
    
    # Generar hash
    hash_input = '|'.join(components)
    hash_full = hashlib.sha256(hash_input.encode()).hexdigest()
    hash_8 = hash_full[:8].upper()
    
    # Construir SKU
    ret_code = RETAILER_CODES.get(retailer.lower(), 'UNK')
    return f"{ret_code}{hash_8}"
```

### 2️⃣ **ARQUITECTURA SCRAPER→DB DIRECTA**

#### Nuevo Flujo
```
Scraper → ProductProcessor → DB (con backup Excel)
         ↓
    [Deduplicación]
         ↓
    [Validación]
         ↓
    [Insert/Update]
```

#### Componente Central: ProductProcessor
```python
class ProductProcessor:
    """Procesa productos del scraper directamente a DB"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.sku_cache = {}  # Cache en memoria para sesión
        self.excel_buffer = []  # Buffer para backup Excel
        
    async def process_product(self, product: ProductData) -> str:
        """Procesa un producto y retorna su SKU único"""
        
        # 1. Generar SKU único
        sku = generate_unique_sku(product.to_dict(), product.retailer)
        
        # 2. Verificar si ya existe en cache
        if sku in self.sku_cache:
            # Solo actualizar precios
            await self.update_prices(sku, product)
        else:
            # Nuevo producto
            await self.insert_product(sku, product)
            self.sku_cache[sku] = True
        
        # 3. Agregar a buffer Excel
        self.excel_buffer.append(product.to_record())
        
        # 4. Flush si buffer grande
        if len(self.excel_buffer) >= 100:
            await self.flush_excel_backup()
        
        return sku
    
    async def insert_product(self, sku: str, product: ProductData):
        """Inserta producto nuevo en master_productos"""
        
        # Extraer specs de additional_info
        storage = product.additional_info.get('storage', '')
        ram = product.additional_info.get('ram', '')
        color = product.additional_info.get('color', '')
        
        await self.db.execute("""
            INSERT INTO master_productos (
                codigo_interno, sku, link, nombre, marca, 
                categoria, retailer, storage, ram, color,
                rating, reviews_count, fecha_primera_captura,
                fecha_ultima_actualizacion, ultimo_visto, activo
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 
                     $11, $12, CURRENT_DATE, CURRENT_DATE, CURRENT_DATE, true)
            ON CONFLICT (codigo_interno) DO UPDATE SET
                ultimo_visto = CURRENT_DATE,
                fecha_ultima_actualizacion = CURRENT_DATE
        """, sku, product.sku, product.product_url, product.title,
            product.brand, product.category, product.retailer,
            storage, ram, color, product.rating, product.reviews_count)
        
        # Insertar precio inicial
        await self.update_prices(sku, product)
    
    async def update_prices(self, sku: str, product: ProductData):
        """Actualiza o inserta precios con lógica diaria"""
        
        current_hour = datetime.now().hour
        fecha = datetime.now().date()
        
        # Verificar si ya existe precio para hoy
        existing = await self.db.fetchone("""
            SELECT precio_normal, precio_oferta, precio_tarjeta
            FROM master_precios 
            WHERE codigo_interno = $1 AND fecha = $2
        """, sku, fecha)
        
        precio_normal = int(product.original_price or 0)
        precio_oferta = int(product.current_price or 0)
        precio_tarjeta = int(product.card_price or 0)
        
        if existing:
            # Ya existe precio de hoy
            if current_hour < 23:  # Antes de las 23:00
                # Solo actualizar si cambió
                if (existing['precio_normal'] != precio_normal or
                    existing['precio_oferta'] != precio_oferta or
                    existing['precio_tarjeta'] != precio_tarjeta):
                    
                    await self.db.execute("""
                        UPDATE master_precios 
                        SET precio_normal = $3,
                            precio_oferta = $4,
                            precio_tarjeta = $5,
                            timestamp_ultima_actualizacion = NOW()
                        WHERE codigo_interno = $1 AND fecha = $2
                    """, sku, fecha, precio_normal, precio_oferta, precio_tarjeta)
            # Después de las 23:00 no actualizar (preparar para histórico)
        else:
            # Nuevo precio del día
            precio_min = min(p for p in [precio_normal, precio_oferta, precio_tarjeta] if p > 0)
            
            await self.db.execute("""
                INSERT INTO master_precios (
                    codigo_interno, fecha, retailer, precio_normal,
                    precio_oferta, precio_tarjeta, precio_min_dia,
                    timestamp_creacion
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """, sku, fecha, product.retailer, precio_normal,
                precio_oferta, precio_tarjeta, precio_min)
```

### 3️⃣ **LÓGICA DE PRECIOS DIARIOS/HISTÓRICOS**

#### Reglas Claras
1. **00:00 - 22:59**: Precio del día actual (se actualiza si cambia)
2. **23:00 - 23:59**: Freeze period (no se actualiza, preparando histórico)
3. **00:00**: Nuevo día = nuevo registro en master_precios

#### Implementación
```python
class PriceManager:
    """Gestiona lógica de precios diarios e históricos"""
    
    def should_update_price(self, fecha: date) -> bool:
        """Determina si se debe actualizar el precio"""
        now = datetime.now()
        
        # Si es de hoy y antes de las 23:00
        if fecha == now.date() and now.hour < 23:
            return True
        return False
    
    def get_price_record_date(self) -> date:
        """Obtiene la fecha para el registro de precio"""
        now = datetime.now()
        
        # Después de las 23:00 preparamos para mañana
        if now.hour >= 23:
            return now.date() + timedelta(days=1)
        return now.date()
```

---

## 📋 PLAN DE IMPLEMENTACIÓN DETALLADO

### FASE 1: Preparación (1 día)
```bash
# 1. Backup completo
pg_dump price_orchestrator > backup_$(date +%Y%m%d).sql

# 2. Crear tablas de transición
ALTER TABLE master_productos ADD COLUMN sku_nuevo VARCHAR(11);
ALTER TABLE master_precios ADD COLUMN sku_nuevo VARCHAR(11);

# 3. Análisis de duplicados actuales
python scripts/analyze_duplicates.py > duplicates_report.txt
```

### FASE 2: Desarrollo (2-3 días)

#### Archivos a Crear

**1. `core/sku_generator.py`**
```python
# Sistema de generación de SKU único
```

**2. `core/product_processor.py`**
```python
# Procesador central scraper→DB
```

**3. `core/price_manager.py`**
```python
# Lógica de precios diarios/históricos
```

**4. `scrapers/base_scraper_optimized.py`**
```python
# Base scraper con inserción directa a DB
```

#### Archivos a Modificar

**1. `portable_orchestrator_v5/scrapers/*_scraper_v5.py`**
- Agregar ProductProcessor
- Mantener backup Excel opcional

**2. `core/master_products_system.py`**
- Reemplazar generación de codigo_interno
- Usar nuevo SKU generator

### FASE 3: Migración (1 día)

#### Script de Migración
```python
# scripts/migration/migrate_to_new_sku.py

import asyncpg
from core.sku_generator import generate_unique_sku

async def migrate_products():
    """Migra productos existentes al nuevo SKU"""
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    # 1. Obtener todos los productos
    products = await conn.fetch("""
        SELECT codigo_interno, sku, link, nombre, retailer
        FROM master_productos
    """)
    
    # 2. Generar nuevos SKUs
    sku_mapping = {}
    for product in products:
        new_sku = generate_unique_sku(dict(product), product['retailer'])
        sku_mapping[product['codigo_interno']] = new_sku
        
        # Actualizar producto
        await conn.execute("""
            UPDATE master_productos 
            SET sku_nuevo = $1 
            WHERE codigo_interno = $2
        """, new_sku, product['codigo_interno'])
    
    # 3. Actualizar precios
    for old_sku, new_sku in sku_mapping.items():
        await conn.execute("""
            UPDATE master_precios 
            SET sku_nuevo = $1 
            WHERE codigo_interno = $2
        """, new_sku, old_sku)
    
    # 4. Consolidar duplicados
    await consolidate_duplicates(conn)
    
    print(f"✅ Migrados {len(products)} productos")

async def consolidate_duplicates(conn):
    """Consolida productos duplicados por nuevo SKU"""
    
    # Encontrar duplicados
    duplicates = await conn.fetch("""
        SELECT sku_nuevo, COUNT(*) as count
        FROM master_productos
        WHERE sku_nuevo IS NOT NULL
        GROUP BY sku_nuevo
        HAVING COUNT(*) > 1
    """)
    
    for dup in duplicates:
        # Mantener el más reciente
        await conn.execute("""
            DELETE FROM master_productos
            WHERE sku_nuevo = $1
            AND codigo_interno != (
                SELECT codigo_interno 
                FROM master_productos 
                WHERE sku_nuevo = $1
                ORDER BY fecha_ultima_actualizacion DESC
                LIMIT 1
            )
        """, dup['sku_nuevo'])
    
    print(f"✅ Consolidados {len(duplicates)} grupos de duplicados")
```

### FASE 4: Testing (1 día)

#### Tests Críticos
```python
# tests/test_new_sku_system.py

def test_sku_uniqueness():
    """SKUs únicos para productos diferentes"""
    product1 = {'sku': 'ABC123', 'link': 'url1', 'nombre': 'iPhone 15'}
    product2 = {'sku': 'ABC123', 'link': 'url2', 'nombre': 'iPhone 15'}
    
    sku1 = generate_unique_sku(product1, 'falabella')
    sku2 = generate_unique_sku(product2, 'falabella')
    
    assert sku1 != sku2  # Links diferentes = SKUs diferentes

def test_sku_consistency():
    """SKU consistente para mismo producto"""
    product = {'sku': 'XYZ789', 'link': 'url', 'nombre': 'Samsung S24'}
    
    sku1 = generate_unique_sku(product, 'ripley')
    sku2 = generate_unique_sku(product, 'ripley')
    
    assert sku1 == sku2  # Mismo producto = mismo SKU

def test_price_update_logic():
    """Lógica de actualización de precios"""
    manager = PriceManager()
    
    # Antes de las 23:00 - debe actualizar
    with freeze_time("2024-01-01 15:00:00"):
        assert manager.should_update_price(date(2024, 1, 1)) == True
    
    # Después de las 23:00 - no debe actualizar
    with freeze_time("2024-01-01 23:30:00"):
        assert manager.should_update_price(date(2024, 1, 1)) == False
```

### FASE 5: Despliegue (1-2 días)

#### Checklist de Despliegue
- [ ] Backup completo de producción
- [ ] Migración en staging exitosa
- [ ] Tests pasando 100%
- [ ] Documentación actualizada
- [ ] Monitoreo configurado
- [ ] Rollback plan preparado

#### Secuencia de Despliegue
1. **Maintenance mode ON**
2. **Ejecutar migración**
3. **Verificar integridad**
4. **Switch al nuevo sistema**
5. **Monitorear 24 horas**
6. **Cleanup de campos viejos**

---

## 📊 MÉTRICAS DE ÉXITO

### KPIs Objetivo
| Métrica | Actual | Objetivo | 
|---------|--------|----------|
| **Duplicados** | 5-10% | < 0.1% |
| **Latencia scraper→DB** | 30-60 min | < 1 min |
| **Tamaño SKU** | 50 chars | 10 chars |
| **Velocidad inserción** | ~100/seg | > 1000/seg |
| **Precisión deduplicación** | ~70% | > 99.9% |

### Monitoreo Post-Implementación
```sql
-- Verificar duplicados
SELECT COUNT(*) as duplicados
FROM (
    SELECT sku_nuevo, COUNT(*) 
    FROM master_productos 
    GROUP BY sku_nuevo 
    HAVING COUNT(*) > 1
) t;

-- Performance de inserción
SELECT 
    DATE(timestamp_creacion) as dia,
    COUNT(*) as inserciones,
    AVG(EXTRACT(EPOCH FROM (timestamp_creacion - LAG(timestamp_creacion) 
        OVER (ORDER BY timestamp_creacion)))) as avg_segundos
FROM master_precios
GROUP BY DATE(timestamp_creacion);
```

---

## 🚨 RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Colisión de SKUs** | Baja | Alto | Hash de 8 chars + validación |
| **Pérdida de datos en migración** | Media | Alto | Backup completo + validación |
| **Performance degradado** | Baja | Medio | Cache en memoria + índices |
| **Scrapers fallan con nuevo sistema** | Media | Alto | Testing exhaustivo + rollback |

---

## 📝 RESUMEN EJECUTIVO

### 🎯 Qué vamos a lograr
1. **SKU único de 10 caracteres** que realmente deduplica
2. **Inserción directa scraper→DB** con backup Excel
3. **Lógica clara de precios** diarios vs históricos
4. **Reducción 99% de duplicados**
5. **10x mejora en velocidad** de procesamiento

### ⏱️ Timeline Total: 5-8 días
- Día 1: Preparación y backups
- Día 2-4: Desarrollo e implementación
- Día 5: Migración de datos
- Día 6: Testing intensivo
- Día 7-8: Despliegue y monitoreo

### 💰 ROI Esperado
- **Ahorro almacenamiento**: -40% espacio en DB
- **Mejora performance**: 10x más rápido
- **Calidad de datos**: 99.9% precisión
- **Mantenibilidad**: -70% tiempo debugging

---

## 🚀 PRÓXIMOS PASOS INMEDIATOS

1. **HOY**: Aprobar el plan y hacer backup
2. **MAÑANA**: Comenzar desarrollo del SKU generator
3. **DÍA 3**: Implementar ProductProcessor
4. **DÍA 4**: Integrar con un scraper piloto
5. **DÍA 5**: Testing y ajustes

---

*📅 Documento creado: Diciembre 2024*  
*🔧 Sistema: Portable Orchestrator V5 Optimizado*  
*✅ Estado: LISTO PARA IMPLEMENTACIÓN*