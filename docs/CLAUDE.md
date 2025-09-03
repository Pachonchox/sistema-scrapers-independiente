# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview 📊

**Scraper v5 Project** - Sistema autónomo de scraping de nueva generación con inteligencia artificial integrada, detección de arbitraje, y análisis de precios en tiempo real para retailers chilenos.

**Características principales:**
- 🤖 Sistema V5 con ML integrado y cache multi-nivel 
- 🎯 Detección automática de oportunidades de arbitraje
- 🏗️ Arquitectura tier-based con scheduling inteligente
- 📊 Backend PostgreSQL + Redis con análisis predictivo
- 🚀 Operación 24/7 completamente autónoma
- 📱 Soporte para 6 retailers chilenos principales

## Architecture 🏗️

### Core Systems

**Scraper v5 (`portable_orchestrator_v5/`)**
- `main.py` - Entry point principal con CLI completo
- `core/orchestrator.py` - Orchestrador principal V5
- `scrapers/` - Scrapers especializados por retailer
- `testing/` - Framework de testing integrado

**Master System (`core/`)**
- `integrated_master_system.py` - Sistema integrado principal
- `master_products_system.py` - Gestión de productos con códigos únicos
- `master_prices_system.py` - Snapshots de precios y alertas
- `ml_utils.py` - Utilidades ML y análisis predictivo

**Arbitrage System (`arbitrage/`)**
- `backend_arbitrage_engine.py` - Motor de detección de arbitraje
- `ml_integration_sync.py` - Integración ML para matching de productos
- `save_opportunities_simple.py` - Persistencia de oportunidades
- `start_arbitrage_engine.py` - Launcher del sistema de arbitraje

**Data & Analytics**
- `analyze_*.py` - Scripts de análisis de datos
- `load_excel_*.py` - Carga de datos desde Excel
- `test_*.py` - Suite completa de tests
- `utils/` - Utilidades compartidas

### Database Schema

**PostgreSQL Backend:**
- `master_productos` - Productos con códigos internos únicos
- `master_precios` - Snapshots de precios históricos
- `arbitrage_opportunities` - Oportunidades detectadas con ML scoring

**Redis Cache:**
- Multi-nivel (L1-L4) con análisis predictivo
- Cache inteligente de productos y precios
- Optimización de frecuencias de scraping

## Commands 🚀

### Quick Start

```bash
# Inicio rápido del sistema completo
python start_tiered_system.py

# O usando batch files (Windows)
quick_start.bat

# Modo test (10 minutos)
test_system.bat
```

### Scraping Individual

```bash
# Scraper V5 independiente
cd portable_orchestrator_v5
python main.py --retailer ripley --category celulares --max-products 50 --export-excel

# Búsqueda específica
python main.py --retailer falabella --search "notebook gaming" --max-products 30

# Health check completo
python main.py --health-check

# Testing de retailer específico
python main.py --test --retailer ripley --test-type full --verbose
```

### Sistema Integrado

```bash
# Sistema master completo con PostgreSQL
python run_integrated_v5.py --enable-arbitrage --enable-postgres

# Orchestrador robusto con recovery
python orchestrator_v5_robust.py --retailers ripley,falabella --max-runtime 180

# Sistema tiered con scheduling inteligente
python orchestrator_v5_tiered.py --tier-critical 30 --tier-important 360
```

### Arbitrage Detection

```bash
# Detectar oportunidades de arbitraje
python arbitrage/test_optimized_simple.py

# Guardar oportunidades en PostgreSQL
python arbitrage/save_opportunities_simple.py

# Motor independiente de arbitraje
python arbitrage/start_arbitrage_engine.py

# Re-entrenar modelos ML
python arbitrage/ml_retraining_system.py
```

### Database Operations

```bash
# Cargar Excel a sistema master
python load_excel_final.py data/excel/ripley_2025_01_01_120000.xlsx

# Análisis de integridad de datos
python analyze_and_fix_db.py

# Auditoría de base de datos
python audit_database.py

# Verificar duplicados
python check_duplicates.py
```

### Analytics & Monitoring

```bash
# Análisis completo de retailers
python analyze_all_retailers_final.py

# Detector de anomalías de precios
python price_anomaly_detector.py

# Investigar anomalías específicas
python investigate_price_anomaly.py

# Sistema completo de tests
python test_complete_system_v5.py
```

## Configuration ⚙️

### Environment Setup (.env)

```env
# Base de Datos
DATABASE_URL=postgresql://postgres:password@localhost:5434/orchestrator
PGHOST=localhost
PGPORT=5434
PGDATABASE=orchestrator

# Redis
REDIS_URL=redis://localhost:6380/0
REDIS_HOST=localhost
REDIS_PORT=6380

# Sistema V5
ARBITRAGE_V5_ENABLED=true
MIN_MARGIN_CLP=5000
MIN_SIMILARITY_SCORE=0.7
RETAILERS_ENABLED=falabella,ripley,paris,hites,abcdin

# ML & Intelligence
USE_REDIS_INTELLIGENCE=true
USE_PREDICTIVE_CACHING=true
ML_BATCH_SIZE=100
ML_SIMILARITY_THRESHOLD=0.7

# Scheduling
TIER_CRITICAL_MINUTES=30
TIER_IMPORTANT_MINUTES=360
TIER_TRACKING_MINUTES=1440

# Logging con emojis
ENABLE_EMOJI_LOGGING=true
ENABLE_EMOJI_ALERTS=true
```

### Docker Setup

```bash
# Iniciar servicios de backend
docker compose up -d postgres redis

# Verificar estado de servicios
docker compose ps

# Ver logs
docker compose logs postgres redis
```

## Development Workflow 🔧

### Dependencies

```bash
# Instalar dependencias principales
pip install -r requirements.txt

# Instalar Playwright para scraping
python -m playwright install chromium

# Verificar instalación
python -c "import playwright; print('✅ Playwright OK')"
```

### Testing Strategy

```bash
# Test rápido de retailer individual
python portable_orchestrator_v5/main.py --test --retailer ripley

# Test completo del sistema (3-5 minutos)
python test_v5_complete_flow.py

# Test de integración con base de datos
python test_v5_complete_with_db.py

# Test de producción limitado (5 minutos)
python test_v5_production_5min.py
```

### Code Structure Patterns

**Scrapers Pattern:**
- Cada retailer tiene su scraper específico en `portable_orchestrator_v5/scrapers/`
- Registro centralizado en `SCRAPER_REGISTRY`
- Soporte para categorías dinámicas y búsquedas específicas

**ML Integration:**
- Modelos pre-entrenados en `arbitrage/models/`
- Feature engineering automático
- Cross-retailer matching con 85%+ precisión

**Tier System:**
- **Crítico**: 30 minutos (productos hot, alta demanda)
- **Importante**: 6 horas (productos estables, seguimiento medio)
- **Seguimiento**: 24 horas (productos de baja rotación)

## Data Flow 📊

```
Web Retailers → V5 Scrapers → ML Normalization → Master Products → Internal Codes
                                    ↓
PostgreSQL Storage ← Price Snapshots ← Master Prices ← Arbitrage Detection
                                    ↓
Analytics Dashboard ← Redis Cache ← Intelligent Scheduling ← Tier Classification
```

**Códigos Internos Format:**
`CL-[BRAND]-[MODEL]-[SPEC]-[RETAILER]-[SEQ]`

Ejemplo: `CL-SAMS-GALAXY-256GB-RIP-001`

## Important Files 📁

### Configuration
- `.env.example` - Template de configuración completa
- `docker-compose.yml` - PostgreSQL + Redis setup
- `requirements.txt` - Dependencias Python

### Entry Points
- `portable_orchestrator_v5/main.py` - Scraper V5 CLI principal
- `start_tiered_system.py` - Sistema tiered completo
- `run_integrated_v5.py` - Sistema integrado con PostgreSQL
- `orchestrator_v5_robust.py` - Version con recovery automático

### Key Scripts
- `arbitrage/test_optimized_simple.py` - Detección de arbitraje optimizada
- `core/integrated_master_system.py` - Sistema master integrado
- `analyze_all_retailers_final.py` - Análisis completo multi-retailer

### Batch Files (Windows)
- `quick_start.bat` - Inicio rápido
- `test_system.bat` - Modo test 10 minutos
- `start_tiered_system.bat` - Sistema tiered con GUI

## Retailers Supported 🛍️

1. **Ripley** - Productos generales, electrónicos
2. **Falabella** - Retail completo, alta precisión ML
3. **Paris** - Moda, productos lifestyle  
4. **Hites** - Electrónicos, hogar
5. **AbcDin** - Productos económicos, ofertas
6. **MercadoLibre** - Marketplace, productos variados

## ML Features 🤖

- **Product Matching**: 19 features, 85%+ precisión
- **Price Anomaly Detection**: Detecta glitches y errores
- **Brand Normalization**: Standardización automática
- **Similarity Scoring**: Matching cross-retailer inteligente
- **Predictive Caching**: Optimización de scraping frequencies

## Troubleshooting 🔧

### Common Issues

**Playwright Setup:**
```bash
python -m playwright install chromium
# Si falla, verificar permisos o usar --force
```

**Database Connection:**
```bash
# Verificar PostgreSQL
docker compose up -d postgres
psql -h localhost -p 5434 -U orchestrator -d orchestrator -c "SELECT version();"
```

**Redis Issues:**
```bash
# Test Redis
docker compose up -d redis
redis-cli -h localhost -p 6380 ping
```

**ML Models Missing:**
```bash
# Re-entrenar modelos si faltan
python arbitrage/ml_retraining_system.py
```

### Debug Commands

```bash
# Debug completo del sistema
python portable_orchestrator_v5/main.py --health-check --verbose

# Análisis de problemas V5
python analyze_v5_config_problems.py

# Verificar diferencias de datos
python verify_falabella_difference.py
```

### Performance Tips

- Usar SSD para PostgreSQL data volume
- Configurar `DB_POOL_SIZE=10` para alta concurrencia
- Redis con `CACHE_L1_SIZE=1000` para mejor performance
- Ejecutar en modo test antes de producción: `--test --max-runtime 5`