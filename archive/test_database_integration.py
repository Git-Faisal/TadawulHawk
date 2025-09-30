"""
Test script for Database Integration.
Tests saving collected stock data to the database.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from collectors.stock_collector import StockCollector
from database.db_manager import DatabaseManager
from utils import setup_logger

# Setup logging
logger = setup_logger('test_db_integration', level='DEBUG')

print("="*70)
print("DATABASE INTEGRATION TEST")
print("="*70)
print("\nThis test will:")
print("  1. Collect data for Saudi Aramco (2222.SR)")
print("  2. Save all data to the database")
print("  3. Verify data was saved correctly")
print()

# Initialize
db_manager = DatabaseManager()
collector = StockCollector('2222.SR')

# Test database connection
print("[1/4] Testing database connection...")
if not db_manager.test_connection():
    print("[ERROR] Database connection failed!")
    sys.exit(1)
print("[OK] Database connection successful")

# Collect data
print("\n[2/4] Collecting data for 2222.SR (Saudi Aramco)...")
collected_data = collector.collect_all_data()

if not collected_data.get('stock_info'):
    print("[ERROR] Failed to collect stock data!")
    sys.exit(1)

print("[OK] Data collected:")
print(f"  Company: {collected_data['stock_info'].get('company_name')}")
print(f"  Sector: {collected_data['stock_info'].get('sector')}")
print(f"  Current Price: {collected_data['current_price'].get('last_close_price')} SAR")
print(f"  Quarterly Records: {len(collected_data.get('quarterly_fundamentals', []))}")
print(f"  Annual Records: {len(collected_data.get('annual_fundamentals', []))}")

# Save to database
print("\n[3/4] Saving data to database...")
success = db_manager.save_collected_data('2222.SR', collected_data, exchange='Tadawul')

if not success:
    print("[ERROR] Failed to save data to database!")
    sys.exit(1)

print("[OK] Data saved successfully")

# Verify saved data
print("\n[4/4] Verifying saved data...")
from database.db_manager import Stock, PriceHistory, QuarterlyFundamental, AnnualFundamental

with db_manager.get_session() as session:
    stock = session.query(Stock).filter(Stock.symbol == '2222.SR').first()

    if not stock:
        print("[ERROR] Stock not found in database!")
        sys.exit(1)

    print(f"[OK] Stock found: {stock.company_name}")
    print(f"  Symbol: {stock.symbol}")
    print(f"  Exchange: {stock.exchange}")
    print(f"  Sector: {stock.sector}")
    print(f"  Industry: {stock.industry}")
    print(f"  Stock ID: {stock.id}")

    # Check price history
    price_count = session.query(PriceHistory).filter(PriceHistory.stock_id == stock.id).count()
    quarterly_count = session.query(QuarterlyFundamental).filter(QuarterlyFundamental.stock_id == stock.id).count()
    annual_count = session.query(AnnualFundamental).filter(AnnualFundamental.stock_id == stock.id).count()

    print(f"  Price History Records: {price_count}")
    print(f"  Quarterly Records: {quarterly_count}")
    print(f"  Annual Records: {annual_count}")

print("\n" + "="*70)
print("DATABASE INTEGRATION TEST COMPLETE")
print("="*70)
print("\nAll data successfully saved and verified!")
print("Check logs/app.log for detailed information")
