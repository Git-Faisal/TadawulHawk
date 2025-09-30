# Archive

This directory contains development and test files from the project build stages.

## Contents

### Test Files (Stage Testing)
- `test_stock_collector.py` - Stage 5 test (data collection)
- `test_database_integration.py` - Stage 6 test (database saves)
- `test_data_validator.py` - Stage 7 test (validation)
- `test_exporters.py` - Stage 8 test (JSON/CSV export)
- `test_symbol_provider.py` - Stage 4 test (symbol loading)

### Debug Files (Investigation)
- `debug_jarir.py` - Investigated Jarir Bookstore data quality
- `debug_yfinance_data.py` - Investigated Yahoo Finance data gaps

### Migration Files
- `migrate_database.py` - Database schema migration script (added 'exchange' field)

### Test Export Files
- `2222_SR.json` - Sample JSON export for Saudi Aramco
- `stocks.csv` - Sample stock metadata export
- `price_history.csv` - Sample price data export
- `quarterly_fundamentals.csv` - Sample quarterly data export
- `annual_fundamentals.csv` - Sample annual data export

## Note

These files were used during development and testing. They are kept for reference but are not needed for normal operation of the application.

The main application is `tadawul_collector.py` in the root directory.
