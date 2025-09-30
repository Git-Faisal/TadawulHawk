# Tadawul Hawk

**Version:** v0.0
**Project:** Comprehensive Saudi Tadawul Exchange Stock Data Collection System

A Python application for collecting and analyzing stock data from the Saudi Tadawul Exchange (Saudi Stock Exchange) using the `yfinance` library.

## 📊 Project Status

**Current Stage:** Foundation Complete (Stage 1-2)
**Next Stage:** Database Foundation (Stage 3)

See [CLAUDE.md](./CLAUDE.md) for detailed build progress tracking.

---

## 🎯 Features

- **Comprehensive Data Collection:**
  - Current and historical price data (1, 3, 6, 9, 12 months lookback)
  - 52-week, 3-year, and 5-year high/low prices
  - Quarterly fundamentals (5 years)
  - Annual fundamentals (5 years)

- **Robust Architecture:**
  - PostgreSQL database with normalized schema
  - SQLAlchemy ORM for database operations
  - Rate limiting and retry logic with exponential backoff
  - Resume capability for interrupted operations
  - Comprehensive logging with rotating file handlers

- **Multiple Export Formats:**
  - JSON export (structured, nested format)
  - CSV exports (4 separate files for easy analysis)

- **Data Quality:**
  - Multi-tier data validation
  - Quarterly vs annual data consistency checks
  - Comprehensive error handling and logging

---

## 🏗️ Architecture

```
tadawul_hawk/
├── config/              # Configuration management
├── database/            # Database schema and operations
├── collectors/          # Data collection from yfinance
├── validators/          # Data validation logic
├── exporters/           # JSON and CSV export functionality
├── utils/               # Logging and helper utilities
├── data/                # Stock symbol lists
├── exports/             # Output directory (json/ and csv/)
└── logs/                # Application logs
```

---

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tadawul_hawk
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE tadawul_stocks;
```

### 4. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tadawul_stocks
DB_USER=postgres
DB_PASSWORD=your_password_here
```

---

## 📖 Usage

### Initialize Database

```bash
python database/init_db.py
```

### Test with 3 Stocks

```bash
python tadawul_collector.py --test
```

### Collect All Tadawul Stocks

```bash
python tadawul_collector.py --all-stocks
```

### Export Data

```bash
# Export to JSON
python tadawul_collector.py --export json

# Export to CSV
python tadawul_collector.py --export csv
```

### Resume Interrupted Collection

```bash
python tadawul_collector.py --resume
```

---

## 📂 Database Schema

The application uses a normalized PostgreSQL schema with the following tables:

- **stocks**: Stock metadata (symbol, company name, sector, etc.)
- **price_history**: Price data (current, historical, high/low ranges)
- **quarterly_fundamentals**: Quarterly financial metrics
- **annual_fundamentals**: Annual financial metrics
- **data_collection_log**: Audit trail for data collection operations

See [database/schema.sql](./database/schema.sql) for complete schema definition.

---

## 📤 Export Formats

### JSON Export

Single file with nested structure:
- `exports/json/tadawul_stocks_YYYY-MM-DD.json`

### CSV Exports

Four separate CSV files for easy analysis:
- `stocks.csv` - Stock metadata
- `price_history.csv` - Price data (wide format)
- `quarterly_fundamentals.csv` - Quarterly financials (long format)
- `annual_fundamentals.csv` - Annual financials (long format)

---

## 🔧 Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `API_RATE_LIMIT_DELAY` | 0.5 | Seconds between API requests |
| `API_MAX_RETRIES` | 3 | Max retry attempts for failed requests |
| `HISTORICAL_YEARS` | 5 | Years of historical data to collect |
| `LOG_LEVEL` | INFO | Logging verbosity |

See [.env.example](./.env.example) for all available options.

---

## 🧪 Development

### Project Tracking

All build progress is tracked in [CLAUDE.md](./CLAUDE.md). This file contains:
- Detailed implementation plan
- Stage-by-stage progress checklist
- Files created
- Error log
- Time tracking

### Branching Strategy

- `main` - Stable, completed stages
- `stage-N-description` - Development branch for each stage
- Each stage is merged to main after successful testing

### Current Stage Status

✅ **Stage 1-2: Foundation** (Complete)
- Directory structure
- Configuration management
- Logging utilities
- Helper functions

🔴 **Stage 3: Database** (Next)
- Database schema creation
- SQLAlchemy models
- Database manager

---

## 📝 Dependencies

- `yfinance` - Yahoo Finance API wrapper
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL adapter
- `pandas` - Data processing and CSV export
- `python-dotenv` - Environment configuration
- `tqdm` - Progress bars

See [requirements.txt](./requirements.txt) for complete list.

---

## ⚠️ Important Notes

1. **Stock Count:** The exact number of Tadawul-listed stocks is fetched dynamically to ensure complete coverage.

2. **Rate Limiting:** The application uses conservative rate limiting to respect Yahoo Finance API limits.

3. **Resume Capability:** If data collection is interrupted (e.g., network issues), the application can resume from the last successful stock.

4. **Historical Prices:** "1 month ago" means 30 calendar days, rounded to the nearest trading day.

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d tadawul_stocks -c "SELECT 1;"
```

### Check Logs

```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/errors.log
```

---

## 📄 License

[Add your license here]

---

## 📧 Contact

[Add contact information here]