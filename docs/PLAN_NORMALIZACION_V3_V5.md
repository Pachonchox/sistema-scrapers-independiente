# Plan de Normalización: Scrapers V3 → V5

## Análisis Comparativo Detallado

### RIPLEY - Diferencias Críticas

#### Selectores V3 (FUNCIONAN)
```python
# V3 usa estos selectores EXACTOS que funcionan:
'.catalog-product-details__name'  # Nombre producto
'.catalog-prices__offer-price'    # Precio oferta
'.catalog-prices__list-price.catalog-prices__line_thru'  # Precio normal
'.catalog-prices__card-price'     # Precio tarjeta
'.brand-logo span, .catalog-product-details__logo-container span'  # Marca
'.catalog-product-details__discount-tag'  # Descuento
```

#### Selectores V5 (NO FUNCIONAN)
```python
# V5 usa selectores GENÉRICOS que no existen:
'.catalog-product-item'           # No existe
'.catalog-product-item__name'     # No existe
'.catalog-product-item__best-price'  # No existe
```

### PROBLEMA PRINCIPAL IDENTIFICADO

**V5 NO está usando los selectores reales de V3**. Los selectores en V5 parecen ser inventados o de una versión antigua del sitio.

## Discrepancias Específicas

### 1. EXTRACCIÓN DE PRODUCTOS (Ripley)

**V3 - Método Real**:
```javascript
// V3 ejecuta JavaScript en el browser para extraer
await page.evaluate(() => {
    const elements = document.querySelectorAll('selector');
    // Extracción detallada con manejo de errores
})
```

**V5 - Método Simplificado**:
```python
# V5 usa query_selector_all directo
product_cards = await page.query_selector_all(selector)
# Falta el contexto de JavaScript
```

### 2. MANEJO DE PRECIOS

**V3 - Extrae 3 tipos de precio**:
- Precio normal (tachado)
- Precio Internet
- Precio Tarjeta Ripley

**V5 - Solo extrae 2**:
- Precio actual
- Precio original

### 3. EXTRACCIÓN DE ESPECIFICACIONES

**V3 - Extrae del texto con regex**:
```python
storageMatch = productName.match(/(\d+)\s*gb(?!\s+ram)/i)
ramMatch = productName.match(/(\d+)\s*gb\s+ram/i)
screenMatch = productName.match(/(\d+\.?\d*)\"/)
```

**V5 - No extrae especificaciones**

## Plan de Normalización Paso a Paso

### PASO 1: Actualizar Selectores (CRÍTICO)

**Archivo**: `portable_orchestrator_v5/scrapers/ripley_scraper_v5.py`

Líneas 50-75, reemplazar con:
```python
self.selectors = {
    'cards': {
        'primary': '[data-product-id]',  # Selector real de V3
        'fallback': '.catalog-product-item'
    },
    'title': {
        'primary': '.catalog-product-details__name',  # REAL V3
        'fallback': '[class*="product-name"]'
    },
    'price': {
        'current': '.catalog-prices__offer-price',  # REAL V3
        'original': '.catalog-prices__list-price.catalog-prices__line_thru',  # REAL V3
        'card': '.catalog-prices__card-price'  # REAL V3
    },
    'brand': '.brand-logo span, .catalog-product-details__logo-container span',  # REAL V3
    'discount': '.catalog-product-details__discount-tag'  # REAL V3
}
```

### PASO 2: Implementar Extracción con JavaScript

Agregar método en Ripley V5:
```python
async def _extract_with_javascript(self, page):
    """Extraer productos ejecutando JavaScript como V3"""
    
    products = await page.evaluate('''() => {
        const cards = document.querySelectorAll('[data-product-id]');
        const results = [];
        
        cards.forEach(card => {
            // Copiar lógica exacta de V3
            const name = card.querySelector('.catalog-product-details__name');
            const price = card.querySelector('.catalog-prices__offer-price');
            // etc...
            
            if (name && price) {
                results.push({
                    nombre: name.textContent.trim(),
                    precio: price.textContent.trim()
                    // etc...
                });
            }
        });
        
        return results;
    }''')
    
    return products
```

### PASO 3: Actualizar Falabella

**Selectores V3 Reales**:
```python
# Falabella V3 usa:
'#testId-searchResults-products a.pod-link'
'.pod-details__product-brand'
'.prices-0'
'.prices-1'
```

**Actualizar en V5** líneas similares.

### PASO 4: Actualizar Paris

**Selectores V3 Reales**:
```python
# Paris V3 usa:
'.product-item'
'.product-name'
'.product-price'
```

## Implementación Inmediata

### 1. Para Ripley (ripley_scraper_v5.py)

**Línea 341-343**: Cambiar selector de título
```python
# ANTES (no funciona):
title_element = await card.query_selector(self.selectors['title']['primary'])

# DESPUÉS (selector real V3):
title_element = await card.query_selector('.catalog-product-details__name')
```

**Línea 353**: Cambiar selector de precio
```python
# ANTES:
price_element = await card.query_selector(self.selectors['price']['current'])

# DESPUÉS:
price_element = await card.query_selector('.catalog-prices__offer-price')
```

### 2. Para Falabella (falabella_scraper_v5.py)

**Actualizar CARD_SELECTORS** (línea 45):
```python
CARD_SELECTORS = {
    'primary': '#testId-searchResults-products a.pod-link',  # V3 REAL
    'fallback': 'a.pod-link',  # V3 REAL
    'tertiary': '.pod-item'
}
```

### 3. Para Paris (paris_scraper_v5.py)

Similar actualización con selectores reales de V3.

## Validación

Después de cada cambio:
1. Ejecutar scraper con 10 productos máximo
2. Verificar que extraiga: nombre, precio, marca
3. Comparar con resultado de V3

## Resumen de Cambios Necesarios

| Archivo | Líneas | Cambio Requerido |
|---------|--------|------------------|
| ripley_scraper_v5.py | 50-75 | Reemplazar selectores con V3 |
| ripley_scraper_v5.py | 341-386 | Usar selectores directos V3 |
| falabella_scraper_v5.py | 45-49 | Actualizar CARD_SELECTORS |
| paris_scraper_v5.py | Similar | Actualizar selectores |

## Conclusión

**El problema principal es que V5 NO está usando los selectores reales de V3**. Los selectores parecen ser genéricos o inventados. La solución es copiar exactamente los selectores de V3 que ya funcionan.