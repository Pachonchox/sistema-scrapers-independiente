# 🧪 Tests - Sistema Orchestrator V5

## 📁 Estructura de Tests

### 🔗 **integration/** - Tests de Integración
Tests que verifican la integración entre componentes:
- `test_alerts_integration.py` - Test completo del sistema de alertas
- `test_v5_complete_flow.py` - Flow completo del sistema V5
- `test_direct_telegram.py` - Test directo de Telegram
- `test_*_v5.py` - Tests específicos de retailers

### 🔧 **unit/** - Tests Unitarios  
Tests de componentes individuales (pendientes de implementar)

### ⚡ **performance/** - Tests de Rendimiento
Tests de performance y benchmarks (pendientes de implementar)

## 🚀 Ejecutar Tests

```bash
# Test completo de alertas
python tests/integration/test_alerts_integration.py

# Test rápido (3 minutos)
python tests/integration/test_v5_production_3min.py

# Test de Telegram
python tests/integration/test_direct_telegram.py
```