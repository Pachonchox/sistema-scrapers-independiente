# 🎯 SISTEMA DE TIERS INTELIGENTE V5

## 🌟 Descripción General

El Sistema de Tiers Inteligente V5 es una evolución avanzada del orquestador de scraping que reemplaza los ciclos continuos tradicionales por un sistema de scheduling inteligente basado en frecuencias y anti-detección automática.

### ✨ Características Principales

- **🎚️ Tiers Inteligentes**: 3 niveles de prioridad con frecuencias optimizadas
  - **Tier 1 (Crítico)**: Tecnología - cada 2 horas
  - **Tier 2 (Importante)**: Hogar/Electrodomésticos - cada 6 horas
  - **Tier 3 (Seguimiento)**: Otros productos - cada 24 horas

- **🎭 Anti-detección Avanzada**:
  - Rotación automática de proxies
  - Cambio inteligente de user agents
  - Patrones de navegación humanos
  - Delays aleatorios con jitter temporal

- **🔄 Operación Continua 24/7**:
  - Sin patrones sospechosos de scraping
  - Distribución de carga aleatoria
  - Gestión inteligente de recursos
  - Auto-recuperación de errores

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE TIERS V5                     │
├─────────────────────────────────────────────────────────────┤
│  🚀 start_tiered_system.py                                 │
│  └─ 🎯 OrchestratorV5Tiered                               │
│     └─ 🔗 TieredOrchestratorIntegration                   │
│        ├─ 🧠 IntelligentScheduler                         │
│        │  ├─ 🎚️ AdvancedTierManager                      │
│        │  └─ 🎭 AntiDetectionSystem                       │
│        └─ 📊 OrchestratorV5Robust (base)                  │
└─────────────────────────────────────────────────────────────┘
```

### 📁 Estructura de Archivos

```
scraper_v5_project/
├── 🚀 start_tiered_system.py                    # Script de inicio principal
├── 🎯 orchestrator_v5_tiered.py                 # Orquestador con tiers
├── 📊 orchestrator_v5_robust.py                 # Orquestador base existente
└── portable_orchestrator_v5/core/
    ├── 🧠 intelligent_scheduler.py              # Scheduler principal
    ├── 🎚️ advanced_tier_manager.py              # Gestión de tiers
    ├── 🎭 anti_detection_system.py              # Sistema anti-detección
    └── 🔗 tiered_orchestrator_integration.py    # Integración con base
```

## 🚀 Uso del Sistema

### Inicio Rápido

```bash
# Modo completo (recomendado para producción)
python start_tiered_system.py

# Modo prueba (10 minutos)
python start_tiered_system.py --test

# Retailers específicos
python start_tiered_system.py --retailers ripley falabella

# Tiempo máximo de ejecución
python start_tiered_system.py --max-runtime 8
```

### Opciones Avanzadas

```bash
# Solo una ejecución (no continuo)
python start_tiered_system.py --single-run

# Sin sistema de tiers (modo tradicional)
python start_tiered_system.py --disable-tiers

# Sin arbitraje ML
python start_tiered_system.py --disable-arbitrage

# Sin notificaciones Telegram
python start_tiered_system.py --disable-telegram

# Modo verbose (debug)
python start_tiered_system.py --verbose
```

## 🎚️ Configuración de Tiers

### Tier 1 - Crítico (2 horas)
- **Productos**: Smartphones, tablets, laptops
- **Retailers**: Ripley, Falabella, Paris
- **Páginas**: 2-4 por categoría
- **Prioridad**: 0.9

### Tier 2 - Importante (6 horas)
- **Productos**: Electrodomésticos, TV, gaming
- **Retailers**: Todos los disponibles
- **Páginas**: 1-3 por categoría
- **Prioridad**: 0.7

### Tier 3 - Seguimiento (24 horas)
- **Productos**: Accesorios, otros
- **Retailers**: Hites, AbcDin, MercadoLibre
- **Páginas**: 1-2 por categoría
- **Prioridad**: 0.5

## 🎭 Sistema Anti-detección

### Rotación de Proxies
```python
proxy_config = {
    'rotation_frequency': 50,  # Cada 50 requests
    'health_check_interval': 300,  # 5 minutos
    'timeout': 10,  # 10 segundos
    'max_failures': 3
}
```

### User Agents Inteligentes
- **Desktop**: Chrome, Firefox, Safari, Edge
- **Mobile**: Android Chrome, iOS Safari
- **Rotación**: Cada 100-200 requests
- **Headers**: Realistas por navegador

### Patrones Humanos
```python
human_delays = {
    'page_load_wait': (2.0, 8.0),      # Espera carga página
    'between_clicks': (0.5, 2.0),      # Entre clicks
    'scroll_pause': (1.0, 3.0),        # Pausa scroll
    'category_change': (3.0, 10.0),    # Cambio categoría
    'retailer_change': (30.0, 120.0),  # Cambio retailer
    'session_break': (300.0, 900.0)    # Pausa sesión
}
```

## 📊 Monitoreo y Estadísticas

### Métricas del Sistema
- **Ejecuciones por tier**: Contadores individuales
- **Sesiones de scraping**: Total de ejecuciones
- **Anti-detección**: Activaciones de medidas
- **Rotaciones**: Proxies y user agents
- **Errores**: Manejo y recuperación

### Logs Detallados
```
logs/
├── tiered_system_YYYYMMDD_HHMMSS.log    # Log principal
├── orchestrator_v5_tiered_*.log         # Log orquestador
└── scheduler_*.log                       # Log scheduler
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# PostgreSQL
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=orchestrator
export PGUSER=postgres
export PGPASSWORD=your_password

# Redis
export REDIS_URL=redis://localhost:6379/0

# Telegram
export TELEGRAM_BOT_TOKEN=your_token
export SUPERUSERS=123456789

# Tiers
export TIER_CRITICAL_HOURS=2
export TIER_IMPORTANT_HOURS=6
export TIER_TRACKING_HOURS=24
export ANTI_DETECTION_ENABLED=true
```

### Configuración JSON
```json
{
  "tiers": {
    "critical": {
      "frequency_hours": 2,
      "pages_range": [2, 4],
      "priority": 0.9,
      "categories": ["celulares", "tablets", "computadores"]
    },
    "important": {
      "frequency_hours": 6,
      "pages_range": [1, 3],
      "priority": 0.7,
      "categories": ["televisores", "electrodomesticos"]
    },
    "tracking": {
      "frequency_hours": 24,
      "pages_range": [1, 2],
      "priority": 0.5,
      "categories": ["accesorios", "otros"]
    }
  }
}
```

## 🛠️ Troubleshooting

### Problemas Comunes

**Error: Módulos no encontrados**
```bash
# Verificar paths Python
python -c "import sys; print('\\n'.join(sys.path))"

# Instalar dependencias
pip install -r requirements.txt
```

**Error: No se pueden importar scrapers**
```bash
# Verificar estructura de archivos
ls -la portable_orchestrator_v5/scrapers/
```

**Error: Anti-detección no funciona**
```bash
# Verificar configuración de proxies
python -c "from portable_orchestrator_v5.core.anti_detection_system import AntiDetectionSystem; ads = AntiDetectionSystem(); print(ads.proxy_pool.get_status())"
```

### Modo Debug
```bash
# Ejecutar con logging detallado
python start_tiered_system.py --verbose --test

# Ver logs en tiempo real
tail -f logs/tiered_system_*.log
```

## 📈 Ventajas del Sistema de Tiers

### vs. Ciclos Continuos Tradicionales

| Aspecto | Tradicional | Tiers Inteligente |
|---------|-------------|-------------------|
| **Detección** | Alta probabilidad | Muy baja probabilidad |
| **Eficiencia** | Desperdicio recursos | Optimización inteligente |
| **Flexibilidad** | Fija | Adaptativa |
| **Escalabilidad** | Limitada | Alta |
| **Mantenimiento** | Manual | Automático |

### Beneficios Operacionales

1. **🎯 Eficiencia**: Solo scraping cuando es necesario
2. **🎭 Stealth**: Patrones impredecibles y humanos
3. **📈 Escalabilidad**: Fácil agregar retailers/categorías
4. **🔄 Robustez**: Auto-recuperación de errores
5. **📊 Observabilidad**: Métricas detalladas

## 🔮 Próximas Mejoras

- **🤖 ML Adaptativo**: Ajuste automático de frecuencias
- **🌐 Proxies Dinámicos**: Rotación geográfica inteligente
- **📱 Mobile First**: Prioridad dispositivos móviles
- **🎨 UI Dashboard**: Interfaz web para monitoreo
- **📈 Predictive Scaling**: Escalado predictivo de recursos

## 📞 Soporte

Para problemas o mejoras, contactar al equipo de desarrollo:
- **Logs**: Revisar archivos en `/logs/`
- **Debug**: Usar `--verbose` para información detallada
- **Test**: Usar `--test` para verificación rápida

---

🎯 **Sistema de Tiers Inteligente V5** - Scraping de nueva generación con IA