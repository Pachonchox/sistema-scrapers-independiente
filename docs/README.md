# 🚀 Sistema de Arbitraje V5 - Autónomo y Completo

**Sistema avanzado de detección de oportunidades de arbitraje** completamente autónomo con inteligencia ML, cache multi-nivel y operación continua no supervisada.

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Flujos de Funcionamiento](#-flujos-de-funcionamiento)
- [Componentes Técnicos](#-componentes-técnicos)
- [Monitoreo y Logs](#-monitoreo-y-logs)
- [API y Integraciones](#-api-y-integraciones)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Características Principales

### ✨ **Autonomía Completa**
- **100% Auto-contenido**: Sin dependencias externas al directorio V5
- **Operación No Supervisada**: Funciona 24/7 sin intervención humana
- **Recuperación Automática**: Manejo inteligente de errores y reconexiones

### 🧠 **Inteligencia Avanzada V5**
- **ML Integrado**: 3 adaptadores ML especializados (Matching, Detección de Glitches, Normalización)
- **Cache Multi-Nivel**: L1 (memoria), L2 (Redis), L3 (predictivo), L4 (analytics)
- **Análisis de Volatilidad**: Predicción inteligente de frecuencias de scraping
- **Scoring Avanzado**: Algoritmos de matching con 85%+ de precisión

### ⚡ **Performance Optimizado**
- **Pool de Conexiones Async**: PostgreSQL con conexiones persistentes
- **Redis Intelligence**: Cache distribuido con análisis predictivo
- **Tier-based Scheduling**: Crítico (30min), Importante (6h), Seguimiento (24h)
- **Procesamiento Paralelo**: Análisis ML concurrente de productos

### 📊 **Monitoreo Integral**
- **Métricas en Tiempo Real**: Dashboard de performance y estado
- **Alertas con Emojis**: Sistema de notificaciones visuales
- **Logs Estructurados**: Logging completo con rotación automática
- **Health Checks**: Validación continua de componentes

---

## 🏗️ Arquitectura del Sistema

```
portable_orchestrator_v5/
├── arbitrage_system/           # 🎯 Sistema Principal de Arbitraje
│   ├── core/                  # 🔧 Componentes Core
│   │   ├── arbitrage_engine.py    # Motor principal de arbitraje
│   │   ├── ml_integration.py      # Integración ML V5
│   │   └── opportunity_detector.py # Detector de oportunidades
│   ├── schedulers/            # 📅 Schedulers Inteligentes
│   │   └── arbitrage_scheduler.py # Scheduler tier-based
│   ├── database/              # 🗄️ Gestión de Base de Datos
│   │   ├── db_manager.py         # Manager PostgreSQL V5
│   │   └── schema_v5.sql         # Schema optimizado V5
│   ├── config/                # ⚙️ Configuraciones
│   │   └── arbitrage_config.py   # Config centralizada V5
│   ├── ml/                    # 🤖 Machine Learning
│   │   └── adapters.py           # Adaptadores ML autónomos
│   └── start_arbitrage_v5.py  # 🚀 Script de inicio
├── core/                      # 🧠 Inteligencia V5
│   ├── redis_intelligence_system.py
│   ├── intelligent_cache_manager.py
│   ├── master_intelligence_integrator.py
│   └── scraping_frequency_optimizer.py
├── data/                      # 📊 Datos y Métricas
├── logs/                      # 📝 Sistema de Logs
└── utils/                     # 🔧 Utilidades
```

### 🔗 **Flujo de Datos Principal**

```
🌐 Retailers → 🗄️ PostgreSQL → 🤖 ML Analysis → 🎯 Opportunity Detection → 📊 Intelligence V5 → 💰 Arbitrage Results
                     ↑                                                                              ↓
               ⚡ Redis Cache ←←←←←←←←←←←←←← 📈 Performance Metrics ←←←←←←←←←←←←←←←← 🚨 Alerts & Notifications
```
- `python -m playwright install chromium`

## Uso (independiente)
Ejecutar desde `scraper_v5_project/portable_orchestrator_v5`:

```
python main.py --retailer ripley --category celulares --max-products 20 --export-excel
```

- Genera `data/excel/<retailer>_YYYY_MM_DD_HHMMSS.xlsx` con columnas:
  `nombre, marca, sku, categoria, retailer, link, precio_normal_num, precio_oferta_num, precio_tarjeta_num, rating, reviews_count, storage, ram, screen, fecha_archivo`.

## Siguientes pasos
- Validar retailers: ripley, falabella, paris, hites, abcdin, mercadolibre.
- Ajustar categorías/URLs en `portable_orchestrator_v5/config/retailers.json` si aplica.
- Ejecutar `--test` por retailer para smoke básico.
