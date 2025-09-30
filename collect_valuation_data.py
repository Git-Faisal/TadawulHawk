"""
Collect Valuation Data for All Stocks.
Fetches market cap, debt, cash, and book value for all 403 stocks in database.
"""

import csv
import time
from pathlib import Path
from tqdm import tqdm
from collectors.stock_collector import StockCollector
from database.db_manager import DatabaseManager, Stock
from utils import setup_logger

logger = setup_logger('valuation_collector', level='INFO')


def collect_valuation_data():
    """Collect valuation data for all stocks in database."""

    # Initialize database
    db = DatabaseManager()

    # Get all stocks and convert to dictionaries
    with db.get_session() as session:
        stocks = session.query(Stock).all()
        # Convert to list of dicts to avoid DetachedInstanceError
        stock_list = [{
            'symbol': s.symbol,
            'company_name': s.company_name,
            'exchange': s.exchange
        } for s in stocks]
        print(f"\nFound {len(stock_list)} stocks in database")

    # Prepare output data
    valuation_records = []

    # Collect data with progress bar
    print("\n" + "="*70)
    print("COLLECTING VALUATION DATA")
    print("="*70 + "\n")

    success_count = 0
    partial_count = 0
    fail_count = 0

    with tqdm(total=len(stock_list), desc="Collecting", unit="stock") as pbar:
        for stock in stock_list:
            pbar.set_description(f"Collecting {stock['symbol']}")

            try:
                # Create collector
                collector = StockCollector(stock['symbol'], rate_limit_delay=0.5)

                # Fetch valuation data
                val_data = collector.fetch_valuation_data()

                # Check if we got data
                if val_data.get('market_cap'):
                    success_count += 1
                    status = "complete"
                elif any(v for k, v in val_data.items() if k != 'market_cap' and v):
                    partial_count += 1
                    status = "partial"
                else:
                    fail_count += 1
                    status = "failed"

                # Add to records
                valuation_records.append({
                    'symbol': stock['symbol'],
                    'company_name': stock['company_name'],
                    'exchange': stock['exchange'],
                    'market_cap': val_data.get('market_cap'),
                    'total_debt': val_data.get('total_debt', 0),
                    'total_cash': val_data.get('total_cash', 0),
                    'book_value': val_data.get('book_value'),
                    'status': status
                })

            except Exception as e:
                logger.error(f"Error collecting {stock['symbol']}: {e}")
                fail_count += 1
                valuation_records.append({
                    'symbol': stock['symbol'],
                    'company_name': stock['company_name'],
                    'exchange': stock['exchange'],
                    'market_cap': None,
                    'total_debt': 0,
                    'total_cash': 0,
                    'book_value': None,
                    'status': 'error'
                })

            pbar.update(1)
            time.sleep(0.2)  # Brief delay

    # Save to CSV
    output_path = Path('exports/valuation_data.csv')
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['symbol', 'company_name', 'exchange', 'market_cap',
                     'total_debt', 'total_cash', 'book_value', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valuation_records)

    # Print summary
    print("\n" + "="*70)
    print("COLLECTION SUMMARY")
    print("="*70)
    print(f"Total stocks:        {len(stock_list)}")
    print(f"Complete data:       {success_count}")
    print(f"Partial data:        {partial_count}")
    print(f"Failed:              {fail_count}")
    print(f"\nOutput: {output_path}")
    print("="*70 + "\n")


if __name__ == '__main__':
    collect_valuation_data()
