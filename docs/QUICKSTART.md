# ⚡ QUICKSTART - Sistema de Arbitraje V5

**Guía rápida para poner en marcha el sistema en 5 minutos** 🚀

---

## 🎯 Inicio Rápido (5 minutos)

### 1️⃣ **Verificar Prerequisitos**
```bash
# Verificar Python
python --version  # Debe ser 3.8+

# Verificar PostgreSQL (debe estar corriendo en puerto 5434)
pg_isready -h localhost -p 5434

# Verificar Redis (debe estar corriendo en puerto 6380)
redis-cli -p 6380 ping  # Debe responder: PONG
```

### 2️⃣ **Instalar Dependencias**
```bash
cd D:\portable_orchestrator_clean\scraper_v5_project
pip install asyncio asyncpg redis python-dotenv pathlib numpy
```

### 3️⃣ **Configurar Base de Datos**
```bash
python -c "
import asyncio
from portable_orchestrator_v5.arbitrage_system.database.db_manager import get_db_manager
from portable_orchestrator_v5.arbitrage_system.config.arbitrage_config import DEVELOPMENT_CONFIG
async def setup():
    db = get_db_manager(DEVELOPMENT_CONFIG)
    await db.initialize_async_pool()
    await db.install_schema()
    print('✅ Schema V5 instalado')
    await db.close()
asyncio.run(setup())
"
```

### 4️⃣ **Ejecutar Test**
```bash
python portable_orchestrator_v5/arbitrage_system/start_arbitrage_v5.py --test --minutes 1
```

### 5️⃣ **¡Sistema Listo!**
```bash
# Modo producción
python portable_orchestrator_v5/arbitrage_system/start_arbitrage_v5.py
```

---

## 🚨 Comandos de Emergencia

### **Si algo no funciona:**

#### **Error: Pool is closed**
```bash
python -c "
import asyncio
from portable_orchestrator_v5.arbitrage_system.database.db_manager import get_db_manager
from portable_orchestrator_v5.arbitrage_system.config.arbitrage_config import DEVELOPMENT_CONFIG
async def fix():
    db = get_db_manager(DEVELOPMENT_CONFIG)
    await db.initialize_async_pool()
    print('✅ Pool reinicializado')
    await db.close()
asyncio.run(fix())
"
```

#### **Error: Redis connection**
```bash
redis-server --port 6380 --daemonize yes
redis-cli -p 6380 ping
```

#### **Error: Schema V5**
```bash
python -c "
import asyncio
from portable_orchestrator_v5.arbitrage_system.database.db_manager import get_db_manager
from portable_orchestrator_v5.arbitrage_system.config.arbitrage_config import DEVELOPMENT_CONFIG
async def reinstall():
    db = get_db_manager(DEVELOPMENT_CONFIG)
    await db.initialize_async_pool()
    await db.install_schema()
    print('✅ Schema reinstalado')
    await db.close()
asyncio.run(reinstall())
"
```

---

## 📊 Verificar que Todo Funciona

### **Ver Estado:**
```bash
python portable_orchestrator_v5/arbitrage_system/start_arbitrage_v5.py --status
```

### **Ver Métricas en Vivo:**
```bash
watch -n 5 'cat data/scheduler_metrics.json | python -m json.tool'
```

### **Ver Logs:**
```bash
tail -f logs/arbitrage_v5/arbitrage_engine_v5_$(date +%Y%m%d).log
```

---

## 🎮 Comandos Principales

| **Comando** | **Descripción** | **Uso** |
|-------------|----------------|----------|
| `--test --minutes N` | Test por N minutos | Validación rápida |
| `--dev` | Modo desarrollo | Debug y testing |
| `--status` | Ver estado | Diagnóstico |
| Sin parámetros | Modo producción | Operación 24/7 |

---

## ✅ Checklist de Verificación

- [ ] Python 3.8+ instalado
- [ ] PostgreSQL corriendo en puerto 5434
- [ ] Redis corriendo en puerto 6380
- [ ] Dependencias instaladas (`pip install ...`)
- [ ] Schema V5 instalado correctamente
- [ ] Test de 1 minuto ejecutado exitosamente
- [ ] Logs generándose en `logs/arbitrage_v5/`
- [ ] Métricas actualizándose en `data/scheduler_metrics.json`

---

## 🆘 Ayuda Rápida

### **¿El sistema no inicia?**
1. Verificar prerequisitos arriba
2. Ejecutar comandos de emergencia
3. Revisar logs en `logs/errors/`

### **¿Rendimiento lento?**
1. Verificar conexiones DB/Redis
2. Revisar logs de performance
3. Ejecutar en modo `--dev` para debug

### **¿Necesitas más información?**
- 📖 **Documentación completa**: `README_ARBITRAGE_V5.md`
- 🔧 **Documentación técnica**: `portable_orchestrator_v5/arbitrage_system/TECHNICAL_DOCS.md`
- 📊 **Métricas**: `data/scheduler_metrics.json`

---

**🎉 ¡Listo! Sistema V5 operativo en minutos**

*Para más detalles, revisa la documentación completa.*