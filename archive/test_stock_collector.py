"""
Test script for StockCollector.
Tests with 3 sample stocks: Saudi Aramco, Al Rajhi Bank, STC.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from collectors.stock_collector import StockCollector
from utils import setup_logger
import json

# Setup logging
logger = setup_logger('test_stock_collector', level='DEBUG')

print("="*70)
print("STOCK COLLECTOR TEST")
print("="*70)
print("\nTesting with 3 sample stocks:")
print("  1. 2222.SR - Saudi Aramco")
print("  2. 1120.SR - Al Rajhi Bank")
print("  3. 7010.SR - STC")
print()

test_symbols = ['2222.SR', '1120.SR', '7010.SR']

for i, symbol in enumerate(test_symbols, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}/3: {symbol}")
    print(f"{'='*70}")

    try:
        collector = StockCollector(symbol, rate_limit_delay=0.5)

        # Test stock info
        print(f"\n[1/6] Fetching stock info...")
        info = collector.fetch_stock_info()
        if info:
            print(f"  Company: {info.get('company_name')}")
            print(f"  Sector: {info.get('sector')}")
            print(f"  Industry: {info.get('industry')}")
        else:
            print("  [WARNING] No stock info retrieved")

        # Test current price
        print(f"\n[2/6] Fetching current price...")
        price_data = collector.fetch_price_data()
        if price_data:
            print(f"  Last Close: {price_data.get('last_close_price')} SAR")
            print(f"  Date: {price_data.get('data_date')}")
        else:
            print("  [WARNING] No price data retrieved")

        # Test historical prices
        print(f"\n[3/6] Fetching historical prices...")
        hist_prices = collector.fetch_historical_prices()
        if hist_prices:
            for months, price in sorted(hist_prices.items()):
                if price:
                    print(f"  {months}m ago: {price:.2f} SAR")
                else:
                    print(f"  {months}m ago: N/A")
        else:
            print("  [WARNING] No historical prices retrieved")

        # Test high/low
        print(f"\n[4/6] Calculating high/low...")
        high_low = collector.calculate_high_low()
        if high_low:
            print(f"  52-week: {high_low.get('week_52_low'):.2f} - {high_low.get('week_52_high'):.2f} SAR")
            if 'year_3_high' in high_low:
                print(f"  3-year:  {high_low.get('year_3_low'):.2f} - {high_low.get('year_3_high'):.2f} SAR")
            if 'year_5_high' in high_low:
                print(f"  5-year:  {high_low.get('year_5_low'):.2f} - {high_low.get('year_5_high'):.2f} SAR")
        else:
            print("  [WARNING] No high/low data retrieved")

        # Test quarterly fundamentals
        print(f"\n[5/6] Fetching quarterly fundamentals...")
        quarterly = collector.fetch_quarterly_fundamentals()
        if quarterly:
            print(f"  Retrieved {len(quarterly)} quarters")
            print(f"  Most recent quarter:")
            latest = quarterly[0] if quarterly else {}
            print(f"    Q{latest.get('fiscal_quarter')} {latest.get('fiscal_year')}")
            print(f"    Revenue: {latest.get('revenue')}")
            print(f"    Net Income: {latest.get('net_income')}")
        else:
            print("  [WARNING] No quarterly data retrieved")

        # Test annual fundamentals
        print(f"\n[6/6] Fetching annual fundamentals...")
        annual = collector.fetch_annual_fundamentals()
        if annual:
            print(f"  Retrieved {len(annual)} years")
            print(f"  Most recent year:")
            latest = annual[0] if annual else {}
            print(f"    Year: {latest.get('fiscal_year')}")
            print(f"    Revenue: {latest.get('revenue')}")
            print(f"    Net Income: {latest.get('net_income')}")
        else:
            print("  [WARNING] No annual data retrieved")

        print(f"\n[OK] Test completed for {symbol}")

    except Exception as e:
        print(f"\n[ERROR] Test failed for {symbol}: {e}")
        logger.error(f"Test failed for {symbol}", exc_info=True)

print(f"\n{'='*70}")
print("ALL TESTS COMPLETE")
print(f"{'='*70}")
print("\nCheck logs/app.log for detailed information")
