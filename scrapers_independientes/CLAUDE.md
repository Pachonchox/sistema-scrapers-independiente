# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Descripción del Proyecto

**🚀 Sistema de Scrapers Independiente V5** - Sistema completo de scraping autónomo para 6 retailers chilenos principales con soporte completo de emojis UTF-8 y arquitectura V5 optimizada. El sistema incluye orquestador inteligente, extracción de campos completos, anti-detección avanzada y exportación automatizada.

## Comandos de Desarrollo

### 🚀 Instalación y Configuración

```bash
# Instalación automática completa
python setup.py

# Instalación manual de dependencias
pip install -r requirements.txt
python -m playwright install chromium

# Configuración de directorios
mkdir resultados
mkdir logs
```

### 🎯 Ejecución Principal (Orquestador V5)

```bash
# Ejecutar todos los scrapers (modo concurrente)
python orchestrator.py --mode concurrent --max-products 200

# Ejecutar scraper específico
python orchestrator.py --retailer paris --max-products 100
python orchestrator.py --retailer falabella --max-products 150

# Múltiples retailers específicos
python orchestrator.py --retailers paris falabella ripley --mode sequential

# Modo test (rápido para validación)
python orchestrator.py --mode test

# Modo secuencial (más estable)
python orchestrator.py --mode sequential --max-products 100
```

### 🎛️ Sistema Alternativo

```bash
# Ejecutar todos los retailers
python run_complete_system.py --all-retailers --max-products 100

# Retailer específico
python run_complete_system.py --retailer hites --max-products 150

# Sistema legacy
python run_scrapers_system.py
python run_scrapers_system.py falabella

# Windows (un click)
EJECUTAR_SCRAPERS.bat
```

### 🧪 Testing y Validación

```bash
# Test completo del sistema
python test_system.py

# Test scraper individual  
python run_scrapers_system.py falabella

# Validación de configuración
python -c "import json; print('✅ Config OK' if json.load(open('config.json')) else '❌ Config Error')"
```

## Arquitectura del Sistema

### 🏗️ Componentes Principales

El sistema está organizado en múltiples capas de abstracción:

**1. Orquestadores (Puntos de Entrada)**
- `orchestrator.py` - ⭐ **Orquestador Principal V5** (recomendado) - Ejecución concurrente, secuencial o test
- `run_complete_system.py` - Sistema alternativo con extracción de campos completos
- `run_scrapers_system.py` - Sistema legacy para compatibilidad

**2. Core Architecture (`core/`)**
- `base_scraper.py` - Clase base V5 con integración ML completa, anti-detección y auto-recovery
- `utils.py` - Utilidades compartidas para exportación, logging y formateo
- `orchestrator.py` - Orquestador interno del core
- `anti_detection_system.py` - Sistema anti-detección avanzado
- `emoji_support.py` - Soporte completo UTF-8 y emojis multiplataforma
- `field_mapper.py` - Mapeo y transformación de campos de datos
- `intelligent_scheduler.py` - Scheduler inteligente con ML
- `advanced_tier_manager.py` - Gestión avanzada de niveles y prioridades
- `exceptions.py` - Excepciones personalizadas del sistema

**3. Scrapers Específicos (`scrapers/`)**
- `paris_scraper_v5_improved.py` - 15+ campos completos
- `paris_scraper_v5_port_integrated.py` - Versión integrada con campos PORT
- `ripley_scraper_v5_improved.py` - 18+ campos completos  
- `falabella_scraper_v5_improved.py` - 14+ campos completos
- `falabella_scraper_v5_parallel.py` - Versión paralela optimizada
- `hites_scraper_v5_improved.py` - 16+ campos completos
- `abcdin_scraper_v5_improved.py` - 17+ campos completos

### 🧠 Arquitectura de Scrapers

Todos los scrapers heredan de `BaseScraperV5` que proporciona:

- **Anti-detección inteligente**: Rotación de User Agents, delays aleatorios, headers realistas
- **Manejo robusto de errores**: Reintentos automáticos, circuit breakers, fallbacks
- **Extracción de campos completos**: Selectores optimizados para maximizar datos extraídos
- **Soporte emoji nativo**: Logging visual con emojis UTF-8
- **Configuración por retailer**: Timeouts, selectores y comportamiento específico

### 🎯 Modos de Ejecución

| Modo | Archivo | Descripción | Uso Recomendado |
|------|---------|-------------|-----------------|
| **concurrent** | `orchestrator.py` | Múltiples scrapers en paralelo | Máximo rendimiento |
| **sequential** | `orchestrator.py` | Scrapers uno tras otro | Máxima estabilidad |
| **test** | `orchestrator.py` | Pocos productos, validación rápida | Testing y desarrollo |
| **individual** | `orchestrator.py --retailer X` | Un scraper específico | Debugging específico |

### 📊 Sistema de Exportación

**Archivos Generados:**
- **Excel individuales**: `retailer_complete_YYYYMMDD_HHMMSS.xlsx` con 14-18 campos por retailer
- **Excel consolidado**: `TODOS_RETAILERS_YYYYMMDD_HHMMSS.xlsx` con datos unificados
- **JSON detallado**: `orchestrator_results_YYYYMMDD_HHMMSS.json` con metadatos y estadísticas
- **Logs con emojis**: `orchestrator.log` y `scrapers_system.log` con seguimiento visual

## Configuración del Sistema

### 🔧 Archivo Principal (`config.json`)

```json
{
  "sistema": {
    "emoji_support": true,        // Soporte emojis forzado
    "max_workers": 1,             // 1=secuencial, >1=paralelo  
    "export_excel": true,         // Exportar Excel individuales
    "export_unified": true        // Crear reporte unificado
  },
  "anti_deteccion": {
    "user_agents": [...],         // 4+ navegadores reales
    "delay_min": 1,               // Delay mínimo entre requests
    "delay_max": 3,               // Delay máximo entre requests
    "max_reintentos": 3,          // Reintentos automáticos
    "headless": true              // Navegador invisible
  },
  "retailers": {
    "falabella": {
      "activo": true,             // Activar/desactivar retailer
      "max_productos": 20,        // Límite productos por ejecución
      "selectores": {...},        // Selectores CSS específicos
      "browser_config": {...}     // Configuración navegador específica
    }
  }
}
```

### ⚙️ Configuraciones Específicas por Retailer

- **Ripley**: Navegador visible off-screen (-2000, 0) + scroll obligatorio para carga dinámica
- **AbcDin**: Wait for DOM content loaded antes de extraer datos
- **Todos**: Timeouts personalizados y configuración específica de selectores

## Características Anti-Detección

### 🛡️ Implementaciones V5

- **Rotación User Agents**: 4+ navegadores reales (Chrome, Firefox, Safari) con versiones actualizadas
- **Delays Inteligentes**: Aleatorios entre 1-3s configurables por retailer
- **Headers Completos**: Accept, Language, Encoding, Referer realistas
- **Webdriver Ocultado**: Properties de automation eliminadas completamente
- **Viewport Realista**: 1920x1080 como configuración estándar
- **Configuración Específica**: Por retailer con timeouts y comportamientos únicos

### 🎯 Sistemas Especiales

- **Ripley**: Navegador visible en posición off-screen con scroll automático
- **AbcDin**: Espera DOM content loaded para evitar timeouts
- **Todos**: Sistema de reintentos con backoff exponencial

## Desarrollo y Mantenimiento

### 📝 Guías de Desarrollo

**Estándares de Código:**
- **Soporte Emojis Obligatorio**: Todos los scripts deben soportar UTF-8 y emojis 😊
- **Logging con Emojis**: Usar emojis contextuales para identificación visual rápida
- **Error Handling Robusto**: try-catch con mensajes descriptivos y emojis de estado
- **Async/Await Preferido**: Para operaciones I/O intensivas
- **Type Hints**: Incluir anotaciones de tipo para mejor claridad
- **Documentación Inline**: Docstrings completos con descripción, parámetros y retorno

### 🔧 Actualización de Selectores

Si un scraper deja de funcionar:

1. **Inspeccionar la página manualmente** (F12 en navegador)
2. **Actualizar selectores en `config.json`** o archivos de scraper específicos
3. **Probar con modo test**: `python orchestrator.py --mode test`
4. **Validar extracción completa**: Verificar que todos los campos esperados se extraen

### 🧪 Testing del Sistema

```bash
# Validación completa del sistema
python test_system.py

# Test rápido del orquestador (modo test - 10 productos)
python orchestrator.py --mode test

# Test scraper individual con pocos productos
python orchestrator.py --retailer paris --max-products 10

# Test de retailers específicos disponibles
python orchestrator.py --retailers paris falabella abcdin --mode sequential --max-products 20

# Verificar scrapers disponibles desde el código
python -c "from orchestrator import SCRAPERS_MAPPING; print('🕷️ Scrapers disponibles:', list(SCRAPERS_MAPPING.keys()))"

# Verificar emojis y UTF-8
python -c "print('✅ 🚀 😊 💰 📊 Emojis funcionando correctamente')"

# Test específico para debugging
python debug_extraction_flow.py
python debug_paris_selectors.py
```

### 📊 Métricas y Monitoreo

**Métricas Incluidas:**
- **Productos por segundo**: Eficiencia de extracción
- **Campos extraídos vs esperados**: Porcentaje de completitud de datos
- **Tiempo por retailer**: Performance individual
- **Tasa de éxito**: Scrapers exitosos vs fallidos
- **Calidad de datos**: Validación de campos obligatorios

### 🔄 Resolución de Problemas Comunes

**Python no encontrado:**
```bash
# Descargar desde python.org, asegurar "Add to PATH"
python --version  # Verificar instalación
```

**Playwright/navegadores faltantes:**
```bash
pip install playwright
python -m playwright install chromium
```

**Emojis no se muestran correctamente:**
- Terminal: Verificar soporte UTF-8
- Windows: Usar Windows Terminal o configurar codepage UTF-8
- Logs: Los archivos siempre guardan correctamente en UTF-8

**Sin productos extraídos:**
- Verificar conexión internet
- Reducir `max_productos` para testing
- Revisar logs detallados en `resultados/`
- Actualizar selectores si la página web cambió

### 🌟 Optimización de Performance

**Para Máximo Rendimiento:**
```json
{
  "max_workers": 3,
  "delay_min": 1,
  "delay_max": 2,
  "headless": true
}
```

**Para Máxima Estabilidad:**
```json
{
  "max_workers": 1,
  "delay_min": 3,
  "delay_max": 6,
  "headless": true
}
```

## Estructura de Archivos Clave

```
scrapers_independientes/
├── orchestrator.py              # 🚀 ORQUESTADOR PRINCIPAL V5
├── run_complete_system.py       # Sistema alternativo
├── run_scrapers_system.py       # Sistema legacy
├── config.json                  # Configuración centralizada
├── setup.py                     # Instalador automático
├── EJECUTAR_SCRAPERS.bat       # Script Windows
├── core/                        # Motor V5
│   ├── base_scraper.py         # Clase base con ML
│   ├── utils.py                # Utilidades compartidas
│   ├── anti_detection_system.py # Anti-detección avanzado
│   └── emoji_support.py        # Soporte UTF-8 completo
├── scrapers/                    # Scrapers específicos V5
│   ├── paris_scraper_v5_improved.py    # 15+ campos
│   ├── paris_scraper_v5_port_integrated.py # Integración PORT
│   ├── ripley_scraper_v5_improved.py   # 18+ campos
│   ├── falabella_scraper_v5_improved.py # 14+ campos
│   ├── falabella_scraper_v5_parallel.py # Versión paralela
│   ├── hites_scraper_v5_improved.py    # 16+ campos
│   └── abcdin_scraper_v5_improved.py   # 17+ campos
├── config/
│   └── retailers.json           # Configuración detallada
└── resultados/                  # Archivos generados
    ├── *.xlsx                   # Excel con campos completos
    ├── *.json                   # Datos + metadatos
    └── *.log                    # Logs con emojis
```

## Notas Importantes

- **🎯 Punto de Entrada Recomendado**: `orchestrator.py` con modo concurrent para mejor performance
- **😊 Emojis Obligatorios**: Todos los scripts fuerzan soporte UTF-8 y emojis nativos
- **🛡️ Anti-detección Activa**: Sistema robusto con rotaciones y delays inteligentes
- **📊 Datos Completos**: 14-18 campos por retailer vs 5-8 básicos de sistemas anteriores
- **🔧 Mantenimiento Simple**: Sistema autocontenido sin dependencias externas complejas
- **⚡ Performance Optimizada**: Modos concurrent/sequential para diferentes necesidades

El sistema está diseñado para ser completamente autónomo y funcional desde la primera ejecución, con capacidades avanzadas de extracción de datos y soporte completo de emojis para mejor experiencia visual.

## Estado Actual de los Scrapers

### 🟢 Scrapers Activos y Funcionales
Según el archivo `orchestrator.py`, los scrapers actualmente disponibles son:

- **Paris**: `paris_scraper_v5_port_integrated.py` (integrado con campos PORT)
- **Falabella**: `falabella_scraper_v5_parallel.py` (versión paralela optimizada)  
- **AbcDin**: `abcdin_scraper_v5_improved.py` (campos completos)

### 🟡 Scrapers en Desarrollo/Desactivados
- **Ripley**: Comentado temporalmente en orchestrator.py
- **Hites**: Comentado temporalmente en orchestrator.py

### 📊 Configuración de Retailers en config.json

Según la configuración actual:
- **Falabella**: ✅ Activo
- **Paris**: ✅ Activo  
- **Ripley**: ✅ Activo (configurado pero con navegador visible off-screen)
- **Hites**: ❌ Desactivado (`"activo": false`)
- **AbcDin**: ❌ Desactivado (`"activo": false`)
- **MercadoLibre**: ✅ Activo

**Nota**: Existe una discrepancia entre la configuración JSON y los scrapers importados en el orquestador. Para activar todos los scrapers, es necesario:
1. Activar los retailers desactivados en `config.json`
2. Descomentar las importaciones en `orchestrator.py`
3. Verificar que todos los archivos de scraper existan y funcionen correctamente