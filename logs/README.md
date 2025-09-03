# 📂 Logs - Sistema de Logging Centralizado

## 📁 Estructura de Logs

### 🔧 **system/** - Logs del Sistema Principal
- `orchestrator_v5_YYYYMMDD.log` - Log principal del sistema
- `master_prices_YYYYMMDD.log` - Logs del master de precios
- `integrated_master_system_YYYYMMDD.log` - Sistema integrado

### 🔔 **alerts/** - Logs del Sistema de Alertas  
- `alerts_bridge_YYYYMMDD.log` - Bridge de alertas
- `telegram_bot_YYYYMMDD.log` - Bot de Telegram
- `alert_engine_YYYYMMDD.log` - Motor de alertas

### 🕷️ **scraping/** - Logs de Scrapers
- `scraper_v5_YYYYMMDD.log` - Scrapers V5
- `retailer_*_YYYYMMDD.log` - Logs específicos por retailer

### 💎 **arbitrage/** - Logs de Arbitraje V5
- `v5_arbitrage_YYYYMMDD.log` - Motor de arbitraje V5
- `ml_integration_YYYYMMDD.log` - Integración ML
- `opportunity_detector_YYYYMMDD.log` - Detector de oportunidades

### 📊 **analysis/** - Logs de Scripts de Análisis
- `analysis_*_YYYYMMDD.log` - Scripts de análisis

### 🧪 **tests/** - Logs de Tests
- `test_*_YYYYMMDD.log` - Logs de tests

### 🔍 **debug/** - Logs de Debug Detallados
- `debug_*_YYYYMMDD.log` - Logs de debug con nivel DEBUG

## ⚙️ Configuración

El sistema de logs se configura automáticamente con:
- **Rotación automática:** Archivos de máximo 10MB
- **Backup:** 5 archivos de respaldo
- **Formato con emojis:** En consola
- **Formato detallado:** En archivos
- **UTF-8 encoding:** Para compatibilidad con emojis

## 🔍 Monitoreo

```bash
# Logs en tiempo real
tail -f logs/system/orchestrator_v5_$(date +%Y%m%d).log

# Logs de alertas
tail -f logs/alerts/alerts_bridge_$(date +%Y%m%d).log

# Estado de logs
python -c "
from core.logging_config import get_logs_status
import json
print(json.dumps(get_logs_status(), indent=2))
"

# Limpieza de logs antiguos
python -c "
from core.logging_config import cleanup_old_logs
cleanup_old_logs(30)  # Mantener 30 días
"
```