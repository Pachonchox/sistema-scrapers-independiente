# 🚀 Portable Orchestrator V5

**Advanced multi-retailer scraping system with ML normalization, PostgreSQL backend, Telegram alerts, and arbitrage detection for Chilean e-commerce.**

## 🎯 Key Features

- **🕷️ Advanced Scraping**: V5 scrapers with ML-powered detection and optimization
- **🤖 ML Normalization**: Cross-retailer product matching with semantic embeddings  
- **💾 PostgreSQL Backend**: Robust database with price snapshots and historical tracking
- **📦 Parquet Backup**: Automatic raw data backup in optimized Parquet format
- **💰 Arbitrage Detection**: ML-powered opportunity detection with 85%+ precision
- **🚨 Telegram Integration**: Real-time alerts with premium UX and emoji support
- **📊 Master Systems**: Unified product and price management with unique internal codes
- **🔄 Intelligent Orchestration**: Tiered scheduling and frequency optimization

## 🏗️ System Architecture

```mermaid
graph TD
    A[🕷️ Scrapers V5] --> B[📊 Raw Data]
    B --> C[💾 PostgreSQL]
    B --> D[📦 Parquet Backup]
    
    C --> E[🧠 ML Normalization]
    E --> F[🔗 Product Matching]
    F --> G[💰 Arbitrage Engine]
    
    G --> H[📈 Opportunity Detection]
    H --> I[🚨 Telegram Alerts]
    
    C --> J[📊 Master Products]
    C --> K[💰 Master Prices]
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (optional, for caching)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/portable-orchestrator-v5.git
cd portable-orchestrator-v5

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and database settings
```

### Quick Test (3 minutes)
```bash
# Test system integration
python tests/integration/test_v5_production_3min.py

# Test Telegram alerts
python tests/integration/test_direct_telegram.py
```

### Production Start
```bash
# Complete tiered system
python start_tiered_system.py

# Specific retailers
python start_tiered_system.py --retailers ripley,falabella --max-runtime 180
```

## 📊 System Components

### Core Systems
- **`core/`**: Master products, prices, alerts integration
- **`portable_orchestrator_v5/`**: V5 arbitrage system with ML
- **`alerts_bot/`**: Telegram bot with premium UX
- **`scripts/`**: Maintenance and analysis utilities

### Key Features

#### 🧠 **ML-Powered Intelligence**
- Semantic product matching across retailers
- Cross-retailer price comparison with 85%+ accuracy
- Predictive caching and frequency optimization

#### 📦 **Parquet Backup System**
- Automatic raw data backup in compressed Parquet format
- Organized by retailer/date/category
- Analytics-ready with 70-90% storage savings vs CSV

#### 💰 **Arbitrage Detection**
- Real-time opportunity detection with configurable thresholds
- ML scoring with confidence intervals
- Automatic Telegram notifications for high-value opportunities

#### 🏪 **Multi-Retailer Support**
Currently supports 6 major Chilean retailers:
- Ripley, Falabella, Paris (primary)
- MercadoLibre, Hites, AbcDin (secondary)

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/price_orchestrator

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id
SUPERUSERS=admin_chat_id

# System Settings
ALERTS_ENABLED=true
PRICE_CHANGE_THRESHOLD=5.0
ARBITRAGE_MIN_MARGIN=15000
```

### Database Setup
```bash
# Create database
createdb price_orchestrator

# Initialize schema
psql -d price_orchestrator -f arbitrage/schema_fixed.sql
```

## 📱 Telegram Bot Commands

- `/start` - Initialize bot registration
- `/buscar [product]` - Search products across retailers
- `/arbitrage` - View current arbitrage opportunities
- `/stats` - System performance metrics
- `/subscribe` - Set up product price alerts

## 📈 Data Flow

1. **Scraping**: V5 scrapers extract raw product data
2. **Storage**: Data stored in PostgreSQL + Parquet backup
3. **Normalization**: ML processing for cross-retailer matching
4. **Arbitrage**: Opportunity detection with profit analysis
5. **Alerts**: Automatic notifications via Telegram

## 🛠️ Management Tools

### Parquet Manager
```bash
# View backup statistics
python scripts/maintenance/parquet_manager.py stats

# Convert to Excel for analysis
python scripts/maintenance/parquet_manager.py to-excel backup.parquet

# Clean old backups
python scripts/maintenance/parquet_manager.py cleanup --days 30
```

### Database Maintenance
```bash
# Check for duplicates
python scripts/maintenance/clean_duplicates.py

# Audit database integrity
python scripts/maintenance/audit_database.py
```

## 📊 Performance Metrics

- **Scraping Rate**: 500-1000 products/minute
- **ML Processing**: ~5.6 products/second normalization
- **Database Operations**: <100ms average query time
- **Arbitrage Detection**: ~17 opportunities per cycle
- **Storage Efficiency**: 60% reduction vs Excel/CSV

## 🧪 Testing

```bash
# Integration tests
python tests/integration/test_alerts_integration.py
python tests/integration/test_parquet_backup.py

# Production test (5 minutes)
python tests/integration/test_v5_production_5min.py
```

## 📚 Documentation

- **[System Flow](docs/SYSTEM_FLOW.md)** - Complete architecture overview
- **[Parquet Backup System](docs/PARQUET_BACKUP_SYSTEM.md)** - Backup system details
- **[Quick Start Guide](QUICK_START_GUIDE.md)** - Comprehensive usage guide

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] Additional retailer integrations
- [ ] Advanced ML models for better matching
- [ ] Web dashboard for monitoring
- [ ] API endpoints for external integration
- [ ] Mobile app for alerts

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/portable-orchestrator-v5/issues)
- **Documentation**: [Docs Folder](docs/)
- **Logs**: Check `logs/` directory for debugging

---

**🎉 Built with ❤️ for efficient e-commerce price monitoring and arbitrage detection**