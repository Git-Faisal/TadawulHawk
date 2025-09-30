"""
Tadawul Hawk - Saudi Stock Data Collector
Main application for collecting stock data from Tadawul and NOMU markets.
"""

import argparse
import sys
from pathlib import Path
from tqdm import tqdm
from typing import List, Set
import time

from collectors.stock_collector import StockCollector
from collectors.argaam_scraper import ArgaamScraper
from database.db_manager import DatabaseManager
from validators.data_validator import DataValidator
from exporters.json_exporter import JSONExporter
from exporters.csv_exporter import CSVExporter
from utils import setup_logger

logger = setup_logger('tadawul_collector', level='INFO')


class TadawulHawk:
    """
    Main application for collecting Saudi stock market data.

    Features:
    - Collect data for all Tadawul and NOMU stocks
    - Resume capability for interrupted collections
    - Test mode for quick validation
    - Progress tracking with tqdm
    - Data validation before saving
    - Export to JSON and CSV
    """

    def __init__(self):
        """Initialize Tadawul Hawk application."""
        self.db_manager = DatabaseManager()
        self.validator = DataValidator(tolerance_pct=2.0)

        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'validation_warnings': 0,
            'validation_errors': 0
        }

    def get_all_symbols(self) -> dict:
        """
        Get all stock symbols from Tadawul and NOMU.

        Returns:
            Dict with 'tadawul' and 'nomu' lists
        """
        logger.info("Fetching all stock symbols...")

        # Scrape Tadawul symbols
        tadawul_scraper = ArgaamScraper(market='tadawul')
        tadawul_data = tadawul_scraper.scrape_symbols()
        tadawul_symbols = [stock['symbol'] for stock in tadawul_data]

        # Scrape NOMU symbols
        nomu_scraper = ArgaamScraper(market='nomu')
        nomu_data = nomu_scraper.scrape_symbols()
        nomu_symbols = [stock['symbol'] for stock in nomu_data]

        logger.info(f"Found {len(tadawul_symbols)} Tadawul stocks, {len(nomu_symbols)} NOMU stocks")

        return {
            'tadawul': tadawul_symbols,
            'nomu': nomu_symbols
        }

    def get_collected_symbols(self) -> Set[str]:
        """
        Get set of symbols that already have data in database.

        Returns:
            Set of symbols
        """
        from database.db_manager import Stock

        with self.db_manager.get_session() as session:
            stocks = session.query(Stock.symbol).all()
            return {stock.symbol for stock in stocks}

    def collect_stock_data(self, symbol: str, exchange: str) -> bool:
        """
        Collect data for a single stock.

        Args:
            symbol: Stock symbol
            exchange: Exchange market ('Tadawul' or 'NOMU')

        Returns:
            True if successful, False otherwise
        """
        try:
            # Collect data
            collector = StockCollector(symbol, rate_limit_delay=0.5)
            collected_data = collector.collect_all_data()

            # Check if we got basic data
            if not collected_data.get('stock_info'):
                logger.error(f"{symbol}: Failed to collect stock info")
                return False

            # Validate data
            validation_result = self.validator.validate_collected_data(
                symbol,
                collected_data,
                exchange=exchange
            )

            # Track validation issues
            if validation_result.warnings:
                self.stats['validation_warnings'] += len(validation_result.warnings)
                for warning in validation_result.warnings:
                    logger.debug(f"{symbol}: {warning}")

            if validation_result.errors:
                self.stats['validation_errors'] += len(validation_result.errors)
                for error in validation_result.errors:
                    logger.warning(f"{symbol}: {error}")

            # Save to database (even if validation has warnings/errors)
            success = self.db_manager.save_collected_data(
                symbol,
                collected_data,
                exchange=exchange
            )

            if success:
                logger.info(f"{symbol}: Successfully collected and saved")
                return True
            else:
                logger.error(f"{symbol}: Failed to save to database")
                return False

        except Exception as e:
            logger.error(f"{symbol}: Collection failed - {e}", exc_info=True)
            return False

    def collect_stocks(self, symbols: List[tuple], mode: str = 'all'):
        """
        Collect data for multiple stocks with progress tracking.

        Args:
            symbols: List of (symbol, exchange) tuples
            mode: Collection mode ('test', 'resume', 'all')
        """
        self.stats['total'] = len(symbols)

        print(f"\n{'='*70}")
        print(f"TADAWUL HAWK - DATA COLLECTION")
        print(f"{'='*70}")
        print(f"Mode: {mode.upper()}")
        print(f"Stocks to collect: {len(symbols)}")
        print(f"{'='*70}\n")

        # Progress bar
        with tqdm(total=len(symbols), desc="Collecting stocks", unit="stock") as pbar:
            for symbol, exchange in symbols:
                pbar.set_description(f"Collecting {symbol}")

                success = self.collect_stock_data(symbol, exchange)

                if success:
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1

                pbar.update(1)

                # Brief delay between stocks
                time.sleep(0.2)

    def run_test_mode(self):
        """Run in test mode - collect data for 3 sample stocks."""
        logger.info("Running in TEST mode")

        # 3 sample stocks from Tadawul
        test_stocks = [
            ('2222.SR', 'Tadawul'),  # Saudi Aramco
            ('1120.SR', 'Tadawul'),  # Al Rajhi Bank
            ('7010.SR', 'Tadawul'),  # STC
        ]

        self.collect_stocks(test_stocks, mode='test')

    def run_resume_mode(self):
        """Run in resume mode - only collect stocks not in database."""
        logger.info("Running in RESUME mode")

        # Get all symbols
        all_symbols = self.get_all_symbols()

        # Get already collected symbols
        collected = self.get_collected_symbols()

        # Filter out already collected
        to_collect = []

        for symbol in all_symbols['tadawul']:
            if symbol not in collected:
                to_collect.append((symbol, 'Tadawul'))

        for symbol in all_symbols['nomu']:
            if symbol not in collected:
                to_collect.append((symbol, 'NOMU'))

        logger.info(f"Already collected: {len(collected)} stocks")
        logger.info(f"Remaining to collect: {len(to_collect)} stocks")

        if not to_collect:
            print("\nAll stocks already collected! Nothing to do.")
            return

        self.stats['skipped'] = len(collected)
        self.collect_stocks(to_collect, mode='resume')

    def run_all_stocks_mode(self):
        """Run in all-stocks mode - collect all 403 stocks."""
        logger.info("Running in ALL-STOCKS mode")

        # Get all symbols
        all_symbols = self.get_all_symbols()

        # Combine all stocks
        to_collect = []

        for symbol in all_symbols['tadawul']:
            to_collect.append((symbol, 'Tadawul'))

        for symbol in all_symbols['nomu']:
            to_collect.append((symbol, 'NOMU'))

        self.collect_stocks(to_collect, mode='all')

    def print_summary(self):
        """Print collection summary statistics."""
        print(f"\n{'='*70}")
        print("COLLECTION SUMMARY")
        print(f"{'='*70}")
        print(f"Total stocks:          {self.stats['total']}")
        print(f"Successfully collected: {self.stats['success']}")
        print(f"Failed:                {self.stats['failed']}")

        if self.stats['skipped'] > 0:
            print(f"Skipped (resume):      {self.stats['skipped']}")

        print(f"\nValidation:")
        print(f"  Warnings:            {self.stats['validation_warnings']}")
        print(f"  Errors:              {self.stats['validation_errors']}")
        print(f"{'='*70}\n")

    def export_data(self, format: str = 'both'):
        """
        Export collected data.

        Args:
            format: Export format ('json', 'csv', 'both')
        """
        print(f"\n{'='*70}")
        print("EXPORTING DATA")
        print(f"{'='*70}\n")

        if format in ['json', 'both']:
            print("Exporting to JSON...")
            json_exporter = JSONExporter(output_dir='exports')
            try:
                path = json_exporter.export_all_from_database(self.db_manager)
                print(f"  Exported to: {path}")
            except Exception as e:
                logger.error(f"JSON export failed: {e}")

        if format in ['csv', 'both']:
            print("Exporting to CSV...")
            csv_exporter = CSVExporter(output_dir='exports')
            try:
                paths = csv_exporter.export_all(self.db_manager)
                print(f"  Exported {len(paths)} CSV files:")
                for name, path in paths.items():
                    print(f"    - {path}")
            except Exception as e:
                logger.error(f"CSV export failed: {e}")

        print(f"\n{'='*70}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Tadawul Hawk - Saudi Stock Market Data Collector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (3 stocks)
  python tadawul_collector.py --test

  # Resume interrupted collection
  python tadawul_collector.py --resume

  # Collect all 403 stocks
  python tadawul_collector.py --all-stocks

  # Collect with export
  python tadawul_collector.py --all-stocks --export json
  python tadawul_collector.py --resume --export both
        """
    )

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--test',
        action='store_true',
        help='Test mode: collect 3 sample stocks (Aramco, Al Rajhi, STC)'
    )
    mode_group.add_argument(
        '--resume',
        action='store_true',
        help='Resume mode: collect only stocks not yet in database'
    )
    mode_group.add_argument(
        '--all-stocks',
        action='store_true',
        help='Collect all 403 stocks (277 Tadawul + 126 NOMU)'
    )

    # Export options
    parser.add_argument(
        '--export',
        choices=['json', 'csv', 'both'],
        help='Export data after collection (optional)'
    )

    # Parse arguments
    args = parser.parse_args()

    # Initialize application
    app = TadawulHawk()

    try:
        # Run selected mode
        if args.test:
            app.run_test_mode()
        elif args.resume:
            app.run_resume_mode()
        elif args.all_stocks:
            app.run_all_stocks_mode()

        # Print summary
        app.print_summary()

        # Export if requested
        if args.export:
            app.export_data(format=args.export)

        print("Collection complete! Check logs/app.log for details.")

    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user.")
        logger.info("Collection interrupted by user")
        app.print_summary()
        sys.exit(1)

    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        logger.error("Fatal error", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
