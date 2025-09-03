# 🚀 Portable Orchestrator v5 - Sistema de Scraping Independiente

**Sistema de scraping avanzado con Machine Learning integrado para e-commerce chileno.**

Proyecto completamente independiente con arquitectura robusta, escalable y profesional. Mantiene la compatibilidad con scrapers del sistema v3 existente con nuevas capacidades v5.

## ✨ Características Principales

### 🧠 Machine Learning Integrado
- **Detección Inteligente de Fallos**: Captura automática de screenshots y análisis HTML
- **Optimización de Proxies**: Rotación inteligente basada en performance histórico  
- **Predicción de Bloqueos**: Modelos ML para evitar detección
- **Learning Continuo**: El sistema mejora automáticamente con cada ejecución

### 🏗️ Arquitectura Robusta
- **Orquestador Central Sólido**: Coordina todo el sistema con tier management
- **Circuit Breakers**: Protección automática contra fallos en cascada
- **Sistema de Tiers**: Optimización dinámica de recursos por prioridad
- **Auto-Recovery**: Recuperación automática de errores sin intervención manual

### 🏪 Scrapers Especializados (Adaptados del v3)
- **Ripley Chile** ✅ - Completamente funcional con scroll lento original
- **Falabella Chile** ✅ - Adaptado con selectores y lógica v3 preservada
- **Paris Chile** ✅ - Mantiene timeouts y modales específicos
- **Hites Chile** 🔜 - En desarrollo
- **AbcDin Chile** 🔜 - En desarrollo  
- **MercadoLibre Chile** 🔜 - En desarrollo

### 🎯 Sistema de Tiers Original Preservado
- **Tier Critical** (2h): Smartphones, computadores, smart TV - Alta volatilidad
- **Tier Important** (4h): Consolas, audio, monitores - Cambios regulares
- **Tier Complementary** (12h): Accesorios, almacenamiento - Tracking histórico

## 📁 Estructura del Proyecto

```
portable_orchestrator_v5/
├── 🏗️ core/                    # Componentes centrales
│   ├── orchestrator.py         # Orquestador principal sólido  
│   ├── base_scraper.py         # Base scraper con ML integration
│   ├── exceptions.py           # Sistema robusto de excepciones
│   └── field_mapper.py         # ETL con reducción inteligente de campos
│
├── 🤖 ml/                      # Sistema Machine Learning
│   ├── failure_detector.py     # Detección ML de fallos + screenshots
│   ├── proxy_optimizer.py      # Gestión inteligente de proxies  
│   └── tier_optimizer.py       # Optimización de tiers por ML
│
├── 🏪 scrapers/                # Scrapers por retailer (adaptados del v3)
│   ├── ripley_scraper_v5.py    # Scraper Ripley (funcional completo)
│   ├── falabella_scraper_v5.py # Scraper Falabella (adaptado v3)
│   ├── paris_scraper_v5.py     # Scraper Paris (adaptado v3)
│   ├── hites_scraper_v5.py     # Scraper Hites (placeholder)
│   ├── abcdin_scraper_v5.py    # Scraper AbcDin (placeholder)
│   └── mercadolibre_scraper_v5.py # Scraper MercadoLibre (placeholder)
│
├── 🧪 testing/                 # Framework de testing integrado
│   ├── test_runner.py          # Runner de tests por retailer
│   ├── maintenance_tools.py    # Herramientas de diagnóstico
│   └── validators.py           # Validadores de datos
│
├── ⚙️ config/                  # Configuraciones
│   └── retailers.json          # Configuración por retailer con tiers
│
├── 📄 requirements.txt         # Dependencias Python
├── 🚀 main.py                 # Punto de entrada principal
└── 📖 README.md               # Esta documentación
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.9+
- Node.js 16+ (para Playwright)
- 4GB+ RAM libre
- Conexión estable a internet

### Instalación Rápida

```bash
# Navegar al proyecto
cd portable_orchestrator_v5

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores Playwright
playwright install chromium

# Verificar instalación
python main.py --health-check
```

## 💻 Uso del Sistema

### Ejecución Básica

```bash
# Scraping de Ripley (completamente funcional)
python main.py --retailer ripley --category celulares --max-products 20

# Búsqueda en Falabella
python main.py --retailer falabella --search "notebook" --max-products 15

# Scraping de Paris
python main.py --retailer paris --category computadores --max-products 10

# Modo test para cualquier retailer
python main.py --test --retailer ripley --verbose
```

### Ejemplos de Uso

```python
# Uso programático
import asyncio
from core.orchestrator import ScraperV5Orchestrator

async def scrape_products():
    orchestrator = ScraperV5Orchestrator()
    
    # Scraping con Ripley (100% funcional)
    result = await orchestrator.scrape_category(
        retailer="ripley",
        category="celulares", 
        max_products=50
    )
    
    print(f"✅ Extraídos {result.total_found} productos de Ripley")
    return result.products

# Ejecutar
products = asyncio.run(scrape_products())
```

### Testing y Validación

```bash
# Test completo de Ripley
python -c "
import asyncio
from scrapers.ripley_scraper_v5 import RipleyScraperV5

async def test():
    scraper = RipleyScraperV5()
    result = await scraper.scrape_category('celulares', max_products=3)
    print(f'✅ Test: {result.success}, Productos: {len(result.products)}')

asyncio.run(test())
"

# Health check del sistema
python main.py --health-check

# Diagnóstico de problemas
python -c "
from testing.maintenance_tools import MaintenanceToolkit
import asyncio

async def diagnose():
    toolkit = MaintenanceToolkit()
    report = await toolkit.full_system_diagnostic()
    print(f'🏥 Estado: {report[\"overall_health\"]}')

asyncio.run(diagnose())
"
```

## 🔧 Configuración Avanzada

### Configuración de Retailers

El archivo `config/retailers.json` contiene todas las configuraciones específicas por retailer:

```json
{
  "retailers": {
    "ripley": {
      "name": "Ripley Chile",
      "base_url": "https://simple.ripley.cl",
      "categories": {
        "celulares": {
          "url": "https://simple.ripley.cl/tecno/celulares",
          "priority": 0.9
        }
      }
    }
  },
  "tier_system": {
    "critical": {
      "frequency_hours": 2,
      "priority": 0.9,
      "retailers": ["falabella", "paris", "ripley"]
    }
  }
}
```

### Sistema de Proxies

```python
from ml.proxy_optimizer import IntelligentProxyManager
import asyncio

async def setup_proxies():
    proxy_manager = IntelligentProxyManager()
    
    # Obtener proxy óptimo para retailer
    proxy_id, config = await proxy_manager.get_optimal_proxy("ripley")
    
    print(f"🌐 Proxy asignado: {proxy_id}")
    return config

config = asyncio.run(setup_proxies())
```

## 📊 Estado Actual de Scrapers

### ✅ Completamente Funcionales
- **Ripley Chile**: Scraper completo con scroll lento y selectores v3 preservados
  - ✅ Scraping por categoría
  - ✅ Búsqueda por término
  - ✅ Validación automática
  - ✅ Manejo de lazy loading
  - ✅ Paginación específica

### ✅ Adaptados del v3 (Listos para uso)
- **Falabella Chile**: Lógica v3 preservada con selectores exactos
  - ✅ Modales automáticos
  - ✅ Scroll progresivo
  - ✅ Element handles
  - ✅ Procesamiento por lotes

- **Paris Chile**: Timeouts y configuración específica mantenida
  - ✅ Timeouts de 60s
  - ✅ Modales específicos de Paris
  - ✅ Selectores preservados

### 🔜 En Desarrollo
- **Hites Chile**: Placeholder creado, pendiente adaptación v3
- **AbcDin Chile**: Placeholder creado, pendiente adaptación v3
- **MercadoLibre Chile**: Placeholder creado, pendiente adaptación v3

## 🧪 Testing

### Tests Individuales

```bash
# Test rápido de funcionalidad
python -c "
import asyncio
from scrapers.ripley_scraper_v5 import RipleyScraperV5

async def quick_test():
    scraper = RipleyScraperV5()
    result = await scraper.scrape_category('celulares', max_products=2)
    
    if result.success and result.products:
        print('✅ ÉXITO: Scraper funcionando correctamente')
        print(f'📱 Productos: {len(result.products)}')
        print(f'⏱️ Tiempo: {result.execution_time:.1f}s')
    else:
        print('❌ ERROR: Scraper no funcional')
        print(f'Error: {result.error_message}')

asyncio.run(quick_test())
"
```

### Framework de Testing

```python
from testing.test_runner import RetailerTestRunner
import asyncio

async def run_tests():
    runner = RetailerTestRunner()
    
    # Test específico por retailer
    results = await runner.run_retailer_tests(
        retailer="ripley",
        test_type="basic"
    )
    
    print(f"Tests: {results['passed']}/{results['total']}")
```

## 🚨 Troubleshooting

### Problemas Comunes

#### Error de Dependencias
```bash
# Reinstalar dependencias
pip uninstall -y playwright beautifulsoup4 requests aiohttp
pip install -r requirements.txt
playwright install chromium
```

#### Scraper No Funciona
```bash
# Verificar configuración
python -c "
from config.retailers import get_retailer_config
config = get_retailer_config('ripley')
print(f'Config: {config}')
"

# Test de conectividad
python main.py --health-check
```

#### Problemas de Proxies
```bash
# Verificar proxies
python -c "
from ml.proxy_optimizer import IntelligentProxyManager
import asyncio

async def check_proxies():
    manager = IntelligentProxyManager()
    health = await manager.perform_health_checks()
    print(f'Proxies saludables: {health[\"healthy_proxies\"]}/{health[\"total_proxies\"]}')

asyncio.run(check_proxies())
"
```

## 🔄 Roadmap

### v1.1.0 - Scrapers Completos
- [ ] Completar adaptación Hites scraper del v3
- [ ] Completar adaptación AbcDin scraper del v3  
- [ ] Completar adaptación MercadoLibre scraper del v3
- [ ] Tests automatizados para todos los retailers

### v1.2.0 - Optimización ML
- [ ] Entrenamiento de modelos con datos históricos
- [ ] Predicción de mejores horarios de scraping
- [ ] Auto-optimización de configuraciones

### v1.3.0 - Integración Avanzada
- [ ] API REST completa
- [ ] Dashboard web de monitoreo
- [ ] Integración con sistemas de alertas

## 📞 Soporte

- **Logs**: Revisar `logs/` para troubleshooting detallado
- **Testing**: Usar `python main.py --test --retailer [nombre]` para diagnósticos
- **Health Check**: `python main.py --health-check` para verificar estado

---

## 🎯 Diferencias Clave con el Proyecto Original

### ✅ Ventajas del v5 Independiente
- **Proyecto Separado**: No interfiere con el sistema v3 existente
- **ML Integrado**: Detección inteligente de fallos desde el día uno
- **Arquitectura Robusta**: Orquestador sólido y manejo de excepciones
- **Testing Integrado**: Framework de testing desde el desarrollo
- **Scrapers Adaptados**: Mantiene funcionalidad v3 con mejoras v5

### 🔄 Compatibilidad
- **Selectores Preservados**: Scrapers mantienen selectores exactos del v3
- **Lógica Original**: Comportamientos específicos por retailer mantenidos
- **Configuraciones**: Sistema de tiers y categorías idéntico al original
- **Performance**: Mismos o mejores tiempos de extracción

### 🚀 Mejoras Implementadas
- **Robustez**: Mejor manejo de errores y recuperación automática  
- **Monitoreo**: Métricas y diagnósticos integrados
- **Escalabilidad**: Arquitectura preparada para crecimiento
- **Mantenibilidad**: Código mejor organizado y documentado

---

*Desarrollado con ❤️ para la comunidad de e-commerce chileno* 🇨🇱

**Portable Orchestrator v5** - Sistema independiente y robusto de scraping con ML integrado.