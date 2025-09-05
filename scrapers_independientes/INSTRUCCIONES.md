# 📋 INSTRUCCIONES COMPLETAS - Sistema Scrapers Independiente V5

## 🚀 INSTALACIÓN RÁPIDA (3 pasos)

### 1️⃣ Instalar Python (si no lo tienes)
```bash
# Descargar desde: https://www.python.org/downloads/
# Asegúrate de marcar "Add Python to PATH" durante instalación
```

### 2️⃣ Instalar automáticamente
```bash
# En Windows:
python setup.py

# En Linux/Mac:
python3 setup.py
```

### 3️⃣ Ejecutar scrapers
```bash
# Opción 1: Script automático (Windows)
EJECUTAR_SCRAPERS.bat

# Opción 2: Comando directo
python run_scrapers_system.py

# Opción 3: Scraper individual
python run_scrapers_system.py falabella
```

---

## 🛠️ INSTALACIÓN MANUAL (si la automática falla)

### Paso 1: Dependencias
```bash
pip install playwright pandas openpyxl beautifulsoup4 lxml requests fake-useragent colorama
python -m playwright install chromium
```

### Paso 2: Directorios
```bash
mkdir resultados
mkdir logs
```

### Paso 3: Probar
```bash
python test_system.py
```

---

## 🎯 USO DEL SISTEMA

### Ejecutar Todos los Scrapers
```bash
python run_scrapers_system.py
```

### Ejecutar Scraper Individual
```bash
python run_scrapers_system.py falabella
python run_scrapers_system.py paris
python run_scrapers_system.py ripley
python run_scrapers_system.py hites
python run_scrapers_system.py abcdin
python run_scrapers_system.py mercadolibre
```

### Probar el Sistema
```bash
python test_system.py
```

---

## ⚙️ CONFIGURACIÓN

### Editar config.json
```json
{
  "sistema": {
    "max_workers": 1,          // 1=secuencial, >1=paralelo
    "export_excel": true,      // Exportar Excel individuales
    "export_unified": true     // Crear reporte unificado
  },
  "retailers": {
    "falabella": {
      "activo": true,          // true/false para activar/desactivar
      "max_productos": 100     // Máximo productos a extraer
    }
  }
}
```

### Configurar Retailers
- **Activar/Desactivar**: Cambiar `"activo": true/false`
- **Límite productos**: Cambiar `"max_productos": 50`
- **Delays**: Modificar `"delay_min"` y `"delay_max"`

---

## 📊 RESULTADOS

### Archivos Generados
```
resultados/
├── falabella_productos_20240905_143022.xlsx    // Individual
├── paris_productos_20240905_143045.xlsx        // Individual
├── ripley_productos_20240905_143108.xlsx       // Individual
├── resumen_scraping_20240905_143200.xlsx       // Unificado
└── scraping_20240905.log                       // Log completo
```

### Contenido Excel
- **Nombre**: Nombre del producto
- **Precio**: Precio extraído
- **Link**: URL del producto
- **Retailer**: Tienda de origen
- **Timestamp**: Fecha/hora extracción

---

## 🛡️ CARACTERÍSTICAS ANTI-DETECCIÓN

### ✅ Implementadas
- Rotación automática User Agents
- Delays aleatorios entre requests
- Headers realistas de navegador
- Ocultación de webdriver properties
- Reintentos automáticos en caso de error
- Configuración especial por retailer

### 🎯 Especiales por Retailer
- **Ripley**: Navegador visible off-screen + scroll obligatorio
- **AbcDin**: Wait for DOM content loaded
- **Todos**: Timeouts y delays personalizados

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "Python no encontrado"
```bash
# Instalar Python desde python.org
# Asegurarse de marcar "Add to PATH"
# Reiniciar terminal
```

### ❌ Error: "playwright no encontrado"
```bash
pip install playwright
python -m playwright install chromium
```

### ❌ Error: "No products extracted"
```bash
# 1. Verificar conexión internet
# 2. Probar con menos productos (max_productos: 10)
# 3. Verificar logs en resultados/
# 4. Ejecutar test_system.py
```

### ❌ Error: "Config file not found"
```bash
# Verificar que config.json existe en el directorio
# Ejecutar desde el directorio scrapers_independientes/
```

### ⚠️ Pocos productos extraídos
```bash
# Normal: sitios web cambian frecuentemente
# Solución: Actualizar selectores en config.json
# Ver logs para detalles específicos
```

---

## 📈 OPTIMIZACIÓN

### Rendimiento
- **Paralelo**: `max_workers: 3` (máximo recomendado)
- **Secuencial**: `max_workers: 1` (más estable)
- **Productos**: Reducir `max_productos` si hay timeouts

### Estabilidad
- Usar `headless: true` para mejor rendimiento
- Aumentar timeouts si hay errores de red
- Reducir workers en conexiones lentas

---

## 📝 LOGS Y DEBUGGING

### Ver Logs
```bash
# Archivo de log
cat resultados/scraping_YYYYMMDD.log

# En tiempo real (Windows)
type resultados\scraping_YYYYMMDD.log

# Últimas líneas
tail -f resultados/scraping_YYYYMMDD.log
```

### Niveles de Log
- ✅ **INFO**: Operaciones normales
- ⚠️ **WARNING**: Problemas menores
- ❌ **ERROR**: Errores críticos
- 🔍 **DEBUG**: Información detallada

---

## 🔄 MANTENIMIENTO

### Actualizar Selectores
Si un scraper deja de funcionar:

1. Verificar la página web manualmente
2. Inspeccionar elementos (F12)
3. Actualizar selectores en `config.json`
4. Probar con `python test_system.py`

### Backup Configuración
```bash
# Hacer backup antes de cambios
cp config.json config.json.backup
```

---

## 🌟 CARACTERÍSTICAS AVANZADAS

### Ejecutar en Horarios Específicos
```bash
# Windows (Task Scheduler)
schtasks /create /tn "Scrapers" /tr "python run_scrapers_system.py" /sc daily /st 09:00

# Linux (Cron)
echo "0 9 * * * cd /path/to/scrapers && python3 run_scrapers_system.py" | crontab -
```

### Monitoreo de Resultados
```bash
# Contar productos por día
ls resultados/*productos*.xlsx | wc -l

# Ver tamaños de archivos
ls -lh resultados/
```

---

## 📞 SOPORTE

### Archivos Importantes para Debug
- `config.json` - Configuración
- `resultados/scraping_YYYYMMDD.log` - Logs
- `test_system.py` - Diagnóstico

### Información Útil para Reportar Problemas
- Versión Python: `python --version`
- Sistema operativo
- Error exacto del log
- Configuración usada
- Scraper específico que falla

---

## 🎉 ¡LISTO PARA USAR!

El sistema está completamente independiente y funcional. 
Ejecuta `python run_scrapers_system.py` y disfruta de tu sistema de scrapers automatizado. 😊