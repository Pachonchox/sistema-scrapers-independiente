# 🚀 Sistema de Scrapers Independiente con Campos Completos

Este directorio contiene un sistema completo e independiente de scrapers para retailers chilenos con **EXTRACCIÓN COMPLETA DE CAMPOS** migrados de los scrapers originales.

## ✅ Scrapers Incluidos con Campos Completos

- **🏬 Paris**: 15+ campos (brand, storage, ram, network, color, ratings, discounts, etc.)
- **🛍️ Ripley**: 18+ campos (screen_size, camera, colors, emblems, precios múltiples, etc.)
- **🏪 Hites**: 16+ campos (seller, specs, shipping_options, stock status, etc.)
- **🏪 AbcDin**: 17+ campos (product_id, badges, power reviews, precios múltiples, etc.)
- **🛒 Falabella**: 14+ campos (cmr_price, internet_price, badges, sponsored, etc.)

## 🎯 Características V5 Mejoradas

- ✅ **Extracción de campos COMPLETA**: Todos los selectores de scrapers_port integrados
- ✅ **Sistema totalmente independiente**: Core, utils, configuraciones incluidas
- ✅ **Orquestador avanzado**: Ejecución concurrente, secuencial o individual
- ✅ **Paginación automática**: Máximo productos por scraper (Paris, Ripley confirmados)
- ✅ **Generación multi-formato**: Excel individual + consolidado + JSON
- ✅ **Logging con emojis**: Seguimiento visual del proceso
- ✅ **Métricas de calidad**: Validación de campos extraídos vs esperados

## 📋 Archivos Principales

- **`orchestrator.py`** - ⭐ **ORQUESTADOR PRINCIPAL** (recomendado)
- **`run_complete_system.py`** - Sistema alternativo de ejecución  
- **`scrapers/`** - 5 scrapers con campos completos
- **`core/`** - Módulos base independientes (BaseScraperV5, utils, etc.)
- **`config/`** - Configuraciones por retailer
- **`resultados/`** - Excel generados con todos los campos

## 🚀 Uso del Orquestador (Recomendado)

### Ejecutar todos los scrapers (modo concurrente):
```bash
python orchestrator.py --mode concurrent --max-products 150
```

### Ejecutar scraper específico:
```bash
python orchestrator.py --retailer paris --max-products 200
python orchestrator.py --retailer falabella --max-products 100
```

### Múltiples retailers específicos:
```bash
python orchestrator.py --retailers paris falabella ripley --mode sequential
```

### Modo test (rápido):
```bash
python orchestrator.py --mode test
```

### Ejecución secuencial (más estable):
```bash
python orchestrator.py --mode sequential --max-products 100
```

## 🚀 Uso del Sistema Alternativo

### Ejecutar todos los scrapers:
```bash
python run_complete_system.py --all-retailers --max-products 100
```

### Ejecutar scraper específico:
```bash
python run_complete_system.py --retailer hites --max-products 150
```

## 📊 Resultados con Campos Completos

### Excel Individuales (formato mejorado):
- **`paris_complete_YYYYMMDD_HHMMSS.xlsx`**: 15+ columnas con brand, storage, ram, network, color, old_price, discount_percent, rating, reviews_count, etc.
- **`ripley_complete_YYYYMMDD_HHMMSS.xlsx`**: 18+ columnas con screen_size, camera, colors, emblems, normal_price, internet_price, ripley_price, etc.
- **`hites_complete_YYYYMMDD_HHMMSS.xlsx`**: 16+ columnas con seller, storage, screen_size, front_camera, shipping_options, out_of_stock, etc.
- **`abcdin_complete_YYYYMMDD_HHMMSS.xlsx`**: 17+ columnas con product_id, floating_badges, la_polar_price, internet_price, normal_price, etc.
- **`falabella_complete_YYYYMMDD_HHMMSS.xlsx`**: 14+ columnas con cmr_price, internet_price, rating, reviews_count, badges, is_sponsored, etc.

### Archivo Consolidado:
- **`TODOS_RETAILERS_YYYYMMDD_HHMMSS.xlsx`**: Todos los productos de todos los retailers en un solo archivo

### JSON Detallado:
- **`orchestrator_results_YYYYMMDD_HHMMSS.json`**: Datos completos + metadatos + estadísticas

## 🎯 Modos de Ejecución del Orquestador

| Modo | Descripción | Recomendado para |
|------|-------------|------------------|
| **concurrent** | Ejecuta múltiples scrapers en paralelo | Máximo rendimiento |
| **sequential** | Ejecuta scrapers uno tras otro | Máxima estabilidad |
| **test** | Modo rápido con pocos productos | Pruebas y validación |

## ⚙️ Configuración Avanzada

El orquestador incluye configuración específica por retailer:

```python
scrapers_config = {
    'paris': {'max_products': 200, 'timeout': 300, 'expected_fields': 15},
    'ripley': {'max_products': 150, 'timeout': 400, 'expected_fields': 18},
    'falabella': {'max_products': 150, 'timeout': 300, 'expected_fields': 14},
    'hites': {'max_products': 100, 'timeout': 350, 'expected_fields': 16},
    'abcdin': {'max_products': 100, 'timeout': 350, 'expected_fields': 17}
}
```

## 📈 Métricas de Calidad

El sistema valida automáticamente:
- ✅ **Campos esperados vs extraídos**: Porcentaje de completitud
- ✅ **Tiempo de ejecución**: Performance por scraper
- ✅ **Tasa de éxito**: Scrapers exitosos vs fallidos
- ✅ **Productos por segundo**: Eficiencia del sistema

## 🔧 Resolución de Problemas

### Error de imports:
```bash
# Verificar que esté en el directorio scrapers_independientes
cd scrapers_independientes
python orchestrator.py --mode test
```

### Campos faltantes:
- Los scrapers están configurados para extraer **TODOS** los campos de los scrapers_port originales
- Si faltan campos, verificar logs para errores específicos de selectores

### Performance:
- Usar `--mode sequential` si hay timeouts
- Reducir `--max-products` para pruebas rápidas
- Usar `--mode test` para validación

## 📝 Archivos de Log

- **`orchestrator.log`**: Logs detallados del orquestador con emojis
- **`scrapers_system.log`**: Logs del sistema alternativo

## 🎉 Ejemplo de Ejecución Exitosa

```bash
$ python orchestrator.py --mode concurrent --max-products 100

🎯 === ORQUESTADOR INDEPENDIENTE V5 - CAMPOS COMPLETOS ===
🚀 Ejecutando PARIS: max_products: 200, timeout: 300s
🚀 Ejecutando RIPLEY: max_products: 150, timeout: 400s
🚀 Ejecutando FALABELLA: max_products: 150, timeout: 300s
✅ PARIS: 187 productos, 15 campos, 45.2s
✅ RIPLEY: 143 productos, 18 campos, 62.1s
✅ FALABELLA: 128 productos, 14 campos, 38.7s
🎉 === REPORTE FINAL ===
✅ Scrapers exitosos: 3/3
📦 Total productos: 458
⏱️ Tiempo total: 78.3s
📈 Tasa éxito: 100.0%
```

## 🚀 **VENTAJAS DE ESTE SISTEMA INDEPENDIENTE:**

1. **📦 Todo incluido**: Core, utils, scrapers, orquestador
2. **🔍 Campos completos**: 15-18 campos por retailer vs 5-8 básicos
3. **⚡ Múltiples modos**: Concurrente, secuencial, test, individual
4. **📊 Reportes avanzados**: JSON + Excel individual + consolidado
5. **🎯 Configuración flexible**: Por retailer y global
6. **🔧 Fácil mantenimiento**: Sistema autocontenido