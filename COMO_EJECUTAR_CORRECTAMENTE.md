# 🚀 CÓMO EJECUTAR EL SISTEMA CORRECTAMENTE

## ✅ **PROBLEMA RESUELTO: Entorno Virtual**

### 🎯 **Comandos Correctos para Ejecutar:**

#### **OPCIÓN 1: Usando script BAT (Recomendado)**
```bash
# Ejecutar sistema completo
run_with_venv.bat

# Modo prueba
run_with_venv.bat --test

# Retailers específicos  
run_with_venv.bat --retailers ripley falabella
```

#### **OPCIÓN 2: Usando script PowerShell**
```powershell
# Ejecutar sistema completo
.\run_with_venv.ps1

# Modo prueba
.\run_with_venv.ps1 --test

# Retailers específicos
.\run_with_venv.ps1 --retailers ripley falabella
```

#### **OPCIÓN 3: Manual (si prefieres hacerlo paso a paso)**
```bash
# 1. Activar entorno virtual
venv\Scripts\activate

# 2. Verificar que estás en el venv
where python
# Debería mostrar: D:\portable_orchestrator_github\venv\Scripts\python.exe

# 3. Ejecutar sistema
python start_tiered_system.py
```

### ⚠️ **¿Por qué falló antes?**

- **Problema**: No estabas usando el entorno virtual (`venv`)
- **Causa**: PowerShell usaba Python global en lugar del venv
- **Solución**: Los scripts automáticamente activan el venv correcto

### ✅ **¿Cómo verificar que funciona?**

Cuando ejecutes correctamente, deberías ver:
```
📍 Python actual: D:\portable_orchestrator_github\venv
✅ playwright
✅ psycopg2 (PostgreSQL backend)
✅ redis (Redis caching)
```

### 🎯 **Comandos Disponibles:**

```bash
# Sistema completo (RECOMENDADO)
run_with_venv.bat

# Modo prueba (10 minutos)
run_with_venv.bat --test

# Solo Ripley y Falabella
run_with_venv.bat --retailers ripley falabella

# Máximo 2 horas
run_with_venv.bat --max-runtime 2

# Solo una ejecución (no continuo)
run_with_venv.bat --single-run

# Sin sistema de tiers
run_with_venv.bat --disable-tiers

# Ayuda completa
run_with_venv.bat --help
```

### 🔧 **Si aún tienes problemas:**

1. **Recrear venv** (extremo):
   ```bash
   rmdir /s venv
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   venv\Scripts\python -m playwright install
   ```

2. **Verificar dependencias**:
   ```bash
   venv\Scripts\python -c "import playwright, psycopg2, redis; print('OK')"
   ```

---
**🎉 ¡Ahora el sistema debe funcionar perfectamente!**