# 🚀 GUÍA RÁPIDA DE USO - SISTEMA ORCHESTRATOR V5

## 📋 ÍNDICE
- [Inicio Rápido (5 minutos)](#-inicio-rápido-5-minutos)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Comandos Principales](#-comandos-principales)  
- [Sistema de Alertas](#-sistema-de-alertas)
- [Logs y Debug](#-logs-y-debug)
- [Tests](#-tests)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 INICIO RÁPIDO (5 minutos)

### ⚡ **Setup Básico**
```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu TELEGRAM_BOT_TOKEN

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar sistema
python -c "from core.logging_config import setup_project_logging; setup_project_logging()"
```

### 🧪 **Test Rápido**
```bash
# Test del sistema completo (3 minutos)
python tests/integration/test_v5_production_3min.py

# Test de alertas con Telegram
python tests/integration/test_direct_telegram.py
```

### 🚀 **Ejecutar Sistema Productivo**
```bash
# Modo producción completo
python start_tiered_system.py

# Modo test (5 minutos)  
python start_tiered_system.py --test --max-runtime 5
```

---

## 📁 ESTRUCTURA DEL PROYECTO

```
scraper_v5_project/
├── 📊 core/                          # Sistemas principales
│   ├── alerts_bridge.py              # 🌉 Bridge de alertas
│   ├── alerts_config.py              # ⚙️ Configuración alertas  
│   ├── logging_config.py             # 🗂️ Sistema de logs
│   ├── master_prices_system.py       # 📊 Master de precios
│   └── integrated_master_system.py   # 🎯 Sistema integrado
│
├── 💎 portable_orchestrator_v5/      # Sistema V5 Arbitrage
│   ├── arbitrage_system/            # 💰 Motor de arbitraje
│   ├── core/                        # 🧠 Inteligencia V5
│   └── scrapers/                    # 🕷️ Scrapers V5
│
├── 📱 alerts_bot/                    # Bot de Telegram  
│   ├── app.py                       # 🤖 Entry point del bot
│   ├── engine/                      # 🔧 Motor de alertas
│   └── ui/                          # 🎨 Templates y emojis
│
├── 🧪 tests/                        # Tests organizados
│   ├── integration/                 # Tests de integración
│   ├── unit/                       # Tests unitarios  
│   └── performance/                 # Tests de rendimiento
│
├── 📜 scripts/                      # Scripts de utilidad
│   ├── analysis/                   # 📊 Análisis de datos
│   ├── data_management/            # 💾 Gestión de datos
│   └── maintenance/                # 🔧 Mantenimiento
│
├── 📂 logs/                         # Logs centralizados
│   ├── system/                     # 🔧 Logs del sistema
│   ├── alerts/                     # 🔔 Logs de alertas
│   ├── scraping/                   # 🕷️ Logs de scraping
│   ├── arbitrage/                  # 💎 Logs de arbitraje
│   └── debug/                      # 🔍 Logs de debug
│
└── 📚 docs/                         # Documentación
```

---

## ⚡ COMANDOS PRINCIPALES

### 🏭 **Sistemas de Producción**

```bash
# Sistema Tiered completo (recomendado)
python start_tiered_system.py
  --retailers ripley,falabella     # Retailers específicos
  --max-runtime 180               # Tiempo máximo (minutos)
  --test                          # Modo test

# Sistema integrado con PostgreSQL
python run_integrated_v5.py --enable-arbitrage

# Sistema V5 independiente
cd portable_orchestrator_v5
python main.py --retailer ripley --category celulares
```

### 🔔 **Sistema de Alertas**

```bash
# Iniciar bot de Telegram
python -m alerts_bot.app

# Test de alertas
python tests/integration/test_alerts_integration.py

# Envío manual de alerta
python -c "
import asyncio
from core.alerts_bridge import send_price_change_alert
asyncio.run(send_price_change_alert(
    'CL-TEST-PROD-256GB-RIP-001', 
    'Producto Test', 'ripley', 
    100000, 90000
))
"
```

### 📊 **Análisis y Mantenimiento**

```bash
# Análisis completo de retailers
python scripts/analysis/analyze_all_retailers_final.py

# Auditoría de base de datos
python scripts/maintenance/audit_database.py

# Limpieza de precios anómalos  
python scripts/maintenance/auto_price_cleaner.py
```

---

## 🔔 SISTEMA DE ALERTAS

### **📱 Configuración Telegram**
```bash
# En .env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id
SUPERUSERS=chat_id_admin

# Habilitar alertas
ALERTS_ENABLED=true
PRICE_CHANGE_THRESHOLD=5.0        # % mínimo para alertar
ARBITRAGE_MIN_MARGIN=15000       # CLP mínimo para arbitraje
```

### **🔄 Flujos de Alertas**

1. **📊 Master Prices → Telegram**
   - Cambios de precio > 5% → Alerta automática
   - Usa templates premium con emojis

2. **💎 V5 Arbitrage → Telegram**  
   - Oportunidades > $15k CLP → Alerta automática
   - Broadcast a superusuarios

3. **📱 Bot Independiente**
   - `/start` - Iniciar bot
   - `/buscar producto` - Buscar y suscribirse
   - `/arbitrage` - Ver oportunidades

### **⚙️ Configuración por Retailer**
```python
from core.alerts_config import get_alerts_config

config = get_alerts_config()
# Ripley: umbral 6%, Falabella: umbral 5%
```

---

## 📂 LOGS Y DEBUG

### **📊 Sistema de Logs Centralizado**

```bash
# Configurar logging para componente
python -c "
from core.logging_config import get_system_logger
logger = get_system_logger('mi_componente')
logger.info('Test log message')
"

# Ver estado de logs
python -c "
from core.logging_config import get_logs_status
import json
print(json.dumps(get_logs_status(), indent=2))
"
```

### **📁 Ubicación de Logs**
```
logs/
├── system/         # Logs principales del sistema
├── alerts/         # Logs del sistema de alertas  
├── scraping/       # Logs de scrapers
├── arbitrage/      # Logs de arbitraje V5
├── analysis/       # Logs de scripts de análisis
└── debug/          # Logs detallados de debug
```

### **🔍 Monitoreo en Tiempo Real**
```bash
# Logs del sistema principal
tail -f logs/system/orchestrator_v5_$(date +%Y%m%d).log

# Logs de alertas
tail -f logs/alerts/alerts_bridge_$(date +%Y%m%d).log

# Logs de arbitraje V5
tail -f logs/arbitrage/v5_arbitrage_$(date +%Y%m%d).log
```

---

## 🧪 TESTS

### **🔧 Tests de Integración**
```bash
# Test completo del sistema
python tests/integration/test_v5_complete_flow.py

# Test de alertas
python tests/integration/test_alerts_integration.py

# Test de arbitraje V5
python tests/integration/test_v5_systems_integration.py

# Test específico de retailer
python tests/integration/test_falabella_v5_fixed.py
```

### **⚡ Tests Rápidos**
```bash
# Test de 3 minutos
python tests/integration/test_v5_production_3min.py

# Test de conectividad Telegram
python tests/integration/test_direct_telegram.py
```

### **📊 Tests de Rendimiento**
```bash
# Test de eficiencia de scraping
python scripts/analysis/analisis_scraping_efficiency.py

# Monitoreo del sistema
python scripts/analysis/monitor_system.py
```

---

## ⚙️ CONFIGURACIÓN AVANZADA

### **🗄️ Base de Datos**
```bash
# PostgreSQL (recomendado)
DATABASE_URL=postgresql://user:pass@localhost:5434/orchestrator

# Redis para cache
REDIS_URL=redis://localhost:6380/0
```

### **🧠 Sistema V5**
```bash
# Inteligencia V5
USE_REDIS_INTELLIGENCE=true
USE_PREDICTIVE_CACHING=true
ML_MATCHING_THRESHOLD=0.45

# Arbitraje V5
ARBITRAGE_V5_ENABLED=true
MIN_SIMILARITY_SCORE=0.7
```

### **🎯 Tiers del Sistema**
```bash
# Crítico: cada 30 min
TIER_CRITICAL_MINUTES=30

# Importante: cada 6 horas  
TIER_IMPORTANT_MINUTES=360

# Seguimiento: cada 24 horas
TIER_TRACKING_MINUTES=1440
```

---

## 🔧 TROUBLESHOOTING

### **❌ Problemas Comunes**

#### **"No module named 'core.connection_manager'"**
```bash
# Solución: Importaciones opcionales ya configuradas
python -c "from core.alerts_bridge import get_alerts_bridge; print('OK')"
```

#### **"Redis connection failed"**  
```bash
# Verificar Redis
redis-cli -p 6380 ping

# Iniciar Redis si no está corriendo
redis-server --port 6380
```

#### **"PostgreSQL connection error"**
```bash
# Verificar PostgreSQL
psql -h localhost -p 5434 -U orchestrator -d price_orchestrator

# Crear base de datos si no existe
createdb -h localhost -p 5434 -U postgres price_orchestrator
```

#### **"Telegram bot not responding"**
```bash
# Verificar token
python tests/integration/test_direct_telegram.py

# Verificar configuración
python -c "
from core.alerts_config import diagnose_alerts_config
import json
print(json.dumps(diagnose_alerts_config(), indent=2))
"
```

### **🧪 Comandos de Diagnóstico**

```bash
# Estado general del sistema
python -c "
from core.logging_config import get_logs_status
from core.alerts_config import diagnose_alerts_config
print('LOGS:', get_logs_status())
print('ALERTS:', diagnose_alerts_config())
"

# Test de conectividad completo
python tests/integration/test_alerts_integration.py

# Verificar estructura del proyecto  
ls -la core/ alerts_bot/ portable_orchestrator_v5/
```

---

## 🚀 FLUJO DE TRABAJO TÍPICO

### **🌅 Setup Inicial (Una vez)**
```bash
1. cp .env.example .env
2. # Configurar TELEGRAM_BOT_TOKEN
3. pip install -r requirements.txt  
4. python tests/integration/test_alerts_integration.py
```

### **📊 Uso Diario**
```bash
1. python start_tiered_system.py      # Sistema principal
2. python -m alerts_bot.app           # Bot de Telegram
3. tail -f logs/system/*.log          # Monitorear logs
```

### **🔧 Mantenimiento Semanal**
```bash
1. python scripts/maintenance/audit_database.py
2. python scripts/analysis/analyze_all_retailers_final.py  
3. python -c "from core.logging_config import cleanup_old_logs; cleanup_old_logs()"
```

---

## 📞 SOPORTE

- **📚 Documentación completa:** `docs/CLAUDE.md`
- **🧪 Tests:** `tests/integration/`
- **📂 Logs:** `logs/*/`  
- **⚙️ Configuración:** `.env` y `core/alerts_config.py`

---

**🎉 ¡Sistema listo para usar en producción!** 🚀