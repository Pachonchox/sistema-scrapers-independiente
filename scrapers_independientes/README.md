# 🚀 Sistema de Scrapers Independiente V5

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Private-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)](README.md)

Sistema completo de scraping autónomo para 6 retailers chilenos principales. Funciona completamente independiente con anti-detección avanzada y exportación automática.

## 🎯 Características Principales

- **✅ 6 Retailers**: Falabella, Paris, Ripley, Hites, AbcDin, MercadoLibre
- **✅ Completamente Independiente**: No requiere sistema externo
- **✅ Anti-detección Avanzada**: Rotación UA, delays inteligentes, headers realistas
- **✅ Exportación Automática**: Excel individuales + reporte unificado
- **✅ Soporte Emojis**: Logs visuales e intuitivos 😊
- **✅ Configuración Flexible**: Activar/desactivar retailers individualmente
- **✅ Sistema Robusto**: Manejo de errores y reintentos automáticos

## 🚀 Inicio Rápido

### 1. Instalación Automática
```bash
git clone https://github.com/Pachonchox/sistema-scrapers-independiente.git
cd sistema-scrapers-independiente
python setup.py
```

### 2. Ejecutar Sistema
```bash
# Todos los scrapers
python run_scrapers_system.py

# Scraper individual
python run_scrapers_system.py falabella

# Windows (un click)
EJECUTAR_SCRAPERS.bat
```

### 3. Ver Resultados
```bash
ls resultados/
```

## 📊 Retailers Soportados

| Retailer | Estado | Configuración Especial |
|----------|--------|------------------------|
| 🛍️ **Falabella** | ✅ Activo | Configuración estándar |
| 🛍️ **Paris** | ✅ Activo | Selectores PORT integrados |
| 🛍️ **Ripley** | ✅ Activo | Navegador off-screen + scroll |
| 🛍️ **Hites** | ✅ Activo | Optimizado para VTEX |
| 🛍️ **AbcDin** | ✅ Activo | DOMContentLoaded wait |
| 🛍️ **MercadoLibre** | ✅ Activo | Configuración estándar |

## ⚙️ Configuración

### config.json
```json
{
  "sistema": {
    "max_workers": 1,          // 1=secuencial, >1=paralelo
    "export_excel": true,      // Exportar Excel individuales
    "export_unified": true     // Crear reporte unificado
  },
  "retailers": {
    "falabella": {
      "activo": true,          // Activar/desactivar
      "max_productos": 100     // Límite de productos
    }
  }
}
```

### Anti-detección
- **User Agents**: 4+ navegadores reales rotando
- **Delays**: 2-5 segundos aleatorios
- **Headers**: Completos y realistas
- **Webdriver**: Completamente oculto
- **Reintentos**: 3 intentos automáticos

## 📁 Estructura del Proyecto

```
sistema-scrapers-independiente/
├── 🚀 run_scrapers_system.py     # ARCHIVO PRINCIPAL
├── ⚙️ config.json                # Configuración centralizada
├── 🔧 setup.py                   # Instalador automático
├── 🧪 test_system.py             # Sistema de pruebas
├── 📋 requirements.txt           # Dependencias
├── 🖥️ EJECUTAR_SCRAPERS.bat      # Script Windows
├── 📖 INSTRUCCIONES.md           # Manual completo
├── core/                         # Motor principal
│   ├── base_scraper.py          # Clase base scrapers
│   └── utils.py                 # Utilidades compartidas
└── resultados/                   # Archivos generados
    ├── falabella_productos_*.xlsx
    ├── resumen_scraping_*.xlsx
    └── scraping_*.log
```

## 🛡️ Características Anti-Detección

### Implementaciones
- ✅ **Rotación User Agents**: 4+ navegadores reales
- ✅ **Delays Inteligentes**: Aleatorios entre 2-5s
- ✅ **Headers Completos**: Accept, Language, Encoding
- ✅ **Webdriver Ocultado**: Properties eliminadas
- ✅ **Viewport Realista**: 1920x1080
- ✅ **Configuración por Retailer**: Timeouts específicos

### Especiales
- **Ripley**: Navegador visible off-screen (-2000, 0) + scroll obligatorio
- **AbcDin**: Espera DOM content loaded
- **Todos**: Reintentos automáticos y timeouts personalizados

## 📊 Resultados y Exportación

### Archivos Generados
- **`retailer_productos_YYYYMMDD_HHMMSS.xlsx`**: Excel individual por retailer
- **`resumen_scraping_YYYYMMDD_HHMMSS.xlsx`**: Reporte unificado con:
  - Hoja "Resumen": Estadísticas por retailer
  - Hoja "Todos_Productos": Base de datos completa
  - Hojas individuales por retailer
- **`scraping_YYYYMMDD.log`**: Log completo con emojis

### Formato de Datos
```json
{
  "nombre": "Samsung Galaxy S24 256GB",
  "precio_texto": "$599.990",
  "precio_numero": 599990,
  "link": "https://...",
  "retailer": "falabella",
  "categoria": "smartphones",
  "timestamp": "2024-09-05T14:30:22"
}
```

## 🧪 Testing y Validación

### Pruebas Automáticas
```bash
# Test completo del sistema
python test_system.py

# Test scraper individual
python run_scrapers_system.py falabella
```

### Validaciones
- ✅ **Imports**: Todas las dependencias
- ✅ **Configuración**: Validación completa config.json
- ✅ **Estructura**: Directorios y archivos necesarios
- ✅ **Scraper**: Prueba real de extracción

## 🔧 Troubleshooting

### Errores Comunes

**Python no encontrado**
```bash
# Instalar Python 3.8+ desde python.org
# Marcar "Add Python to PATH"
```

**Playwright falla**
```bash
pip install playwright
python -m playwright install chromium
```

**Sin productos extraídos**
- Verificar conexión internet
- Reducir `max_productos` a 10 para prueba
- Revisar logs en `resultados/`

### Logs y Debugging
- 📄 **Logs**: `resultados/scraping_YYYYMMDD.log`
- 🔍 **Niveles**: INFO, WARNING, ERROR, DEBUG
- 🎨 **Emojis**: Identificación visual rápida

## 📈 Optimización y Rendimiento

### Configuraciones Recomendadas

**Para Estabilidad**
```json
{
  "max_workers": 1,
  "delay_min": 3,
  "delay_max": 6,
  "headless": true
}
```

**Para Velocidad**
```json
{
  "max_workers": 2,
  "delay_min": 1,
  "delay_max": 3,
  "headless": true
}
```

### Métricas
- **Velocidad**: ~10-20 productos/minuto por scraper
- **Éxito**: 85-95% tasa de éxito típica
- **Memoria**: <500MB uso típico
- **CPU**: Uso moderado durante ejecución

## 🔄 Mantenimiento

### Actualizar Selectores
Si un scraper deja de funcionar:
1. Verificar página web manualmente
2. Inspeccionar elementos (F12 en navegador)
3. Actualizar selectores en `config.json`
4. Probar: `python test_system.py`

### Monitoreo
```bash
# Contar archivos generados
ls resultados/*.xlsx | wc -l

# Ver últimos logs
tail -f resultados/scraping_$(date +%Y%m%d).log
```

## 🌟 Uso Avanzado

### Programación Automática
```bash
# Windows Task Scheduler
schtasks /create /tn "Scrapers" /tr "python run_scrapers_system.py" /sc daily /st 09:00

# Linux Cron
0 9 * * * cd /path/to/scrapers && python3 run_scrapers_system.py
```

### Integración API
El sistema puede integrarse fácilmente con APIs externas modificando las funciones de exportación en `core/utils.py`.

## 📞 Soporte y Contribuciones

### Reportar Issues
Para reportar problemas, incluir:
- Versión Python: `python --version`
- Sistema operativo
- Error completo del log
- Configuración utilizada

### Desarrollo
- **Código**: Seguir PEP 8
- **Commits**: Usar emojis y descripciones claras
- **Testing**: Probar con `test_system.py` antes de commit

## 📄 Licencia

Este proyecto es privado y confidencial. Todos los derechos reservados.

---

## 🎉 Estado del Proyecto

**✅ PRODUCCIÓN**: Sistema completamente funcional y probado.

**Última actualización**: Septiembre 2024  
**Versión**: 1.0.0  
**Estado**: Mantenimiento activo