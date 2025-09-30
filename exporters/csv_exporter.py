"""
CSV Exporter for Tadawul Hawk.
Exports stock data to CSV format (4 separate files).
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional
from utils import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """
    Exports stock data to CSV format.

    Generates 4 CSV files:
    1. stocks.csv - Stock metadata
    2. price_history.csv - Price data
    3. quarterly_fundamentals.csv - Quarterly financials
    4. annual_fundamentals.csv - Annual financials
    """

    def __init__(self, output_dir: str = 'exports'):
        """
        Initialize CSV exporter.

        Args:
            output_dir: Directory for exported files (default: 'exports')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CSVExporter initialized (output: {self.output_dir})")

    def export_stocks(self, db_manager, filename: str = 'stocks.csv') -> str:
        """
        Export stock metadata to CSV.

        Args:
            db_manager: DatabaseManager instance
            filename: Output filename (default: 'stocks.csv')

        Returns:
            Path to exported file
        """
        logger.info("Exporting stocks metadata to CSV")

        from database.db_manager import Stock

        output_path = self.output_dir / filename

        try:
            with db_manager.get_session() as session:
                # Query all stocks
                stocks = session.query(Stock).all()

                # Convert to list of dicts
                data = []
                for stock in stocks:
                    data.append({
                        'symbol': stock.symbol,
                        'company_name': stock.company_name,
                        'exchange': stock.exchange,
                        'sector': stock.sector,
                        'industry': stock.industry,
                        'currency': stock.currency,
                        'listing_date': stock.listing_date,
                        'created_at': stock.created_at,
                        'updated_at': stock.updated_at
                    })

                # Create DataFrame
                df = pd.DataFrame(data)

                # Export to CSV
                df.to_csv(output_path, index=False, encoding='utf-8')

                logger.info(f"Exported {len(data)} stocks to {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export stocks to CSV: {e}", exc_info=True)
            raise

    def export_price_history(self, db_manager, filename: str = 'price_history.csv') -> str:
        """
        Export price history to CSV.

        Args:
            db_manager: DatabaseManager instance
            filename: Output filename (default: 'price_history.csv')

        Returns:
            Path to exported file
        """
        logger.info("Exporting price history to CSV")

        from database.db_manager import PriceHistory, Stock

        output_path = self.output_dir / filename

        try:
            with db_manager.get_session() as session:
                # Query all price history with stock symbols
                query = session.query(
                    Stock.symbol,
                    Stock.company_name,
                    Stock.exchange,
                    PriceHistory.data_date,
                    PriceHistory.last_close_price,
                    PriceHistory.price_1m_ago,
                    PriceHistory.price_3m_ago,
                    PriceHistory.price_6m_ago,
                    PriceHistory.price_9m_ago,
                    PriceHistory.price_12m_ago,
                    PriceHistory.week_52_high,
                    PriceHistory.week_52_low,
                    PriceHistory.year_3_high,
                    PriceHistory.year_3_low,
                    PriceHistory.year_5_high,
                    PriceHistory.year_5_low,
                    PriceHistory.created_at,
                    PriceHistory.updated_at
                ).join(Stock, PriceHistory.stock_id == Stock.id).all()

                # Convert to DataFrame
                df = pd.DataFrame(query, columns=[
                    'symbol', 'company_name', 'exchange', 'data_date',
                    'last_close_price', 'price_1m_ago', 'price_3m_ago',
                    'price_6m_ago', 'price_9m_ago', 'price_12m_ago',
                    'week_52_high', 'week_52_low', 'year_3_high', 'year_3_low',
                    'year_5_high', 'year_5_low', 'created_at', 'updated_at'
                ])

                # Export to CSV
                df.to_csv(output_path, index=False, encoding='utf-8')

                logger.info(f"Exported {len(df)} price records to {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export price history to CSV: {e}", exc_info=True)
            raise

    def export_quarterly_fundamentals(self, db_manager,
                                      filename: str = 'quarterly_fundamentals.csv') -> str:
        """
        Export quarterly fundamentals to CSV.

        Args:
            db_manager: DatabaseManager instance
            filename: Output filename (default: 'quarterly_fundamentals.csv')

        Returns:
            Path to exported file
        """
        logger.info("Exporting quarterly fundamentals to CSV")

        from database.db_manager import QuarterlyFundamental, Stock

        output_path = self.output_dir / filename

        try:
            with db_manager.get_session() as session:
                # Query all quarterly fundamentals with stock symbols
                query = session.query(
                    Stock.symbol,
                    Stock.company_name,
                    Stock.exchange,
                    QuarterlyFundamental.fiscal_year,
                    QuarterlyFundamental.fiscal_quarter,
                    QuarterlyFundamental.quarter_end_date,
                    QuarterlyFundamental.revenue,
                    QuarterlyFundamental.gross_profit,
                    QuarterlyFundamental.net_income,
                    QuarterlyFundamental.operating_cash_flow,
                    QuarterlyFundamental.free_cash_flow,
                    QuarterlyFundamental.created_at,
                    QuarterlyFundamental.updated_at
                ).join(Stock, QuarterlyFundamental.stock_id == Stock.id).all()

                # Convert to DataFrame
                df = pd.DataFrame(query, columns=[
                    'symbol', 'company_name', 'exchange', 'fiscal_year',
                    'fiscal_quarter', 'quarter_end_date', 'revenue',
                    'gross_profit', 'net_income', 'operating_cash_flow',
                    'free_cash_flow', 'created_at', 'updated_at'
                ])

                # Sort by symbol, year, quarter
                df = df.sort_values(['symbol', 'fiscal_year', 'fiscal_quarter'],
                                   ascending=[True, False, False])

                # Export to CSV
                df.to_csv(output_path, index=False, encoding='utf-8')

                logger.info(f"Exported {len(df)} quarterly records to {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export quarterly fundamentals to CSV: {e}", exc_info=True)
            raise

    def export_annual_fundamentals(self, db_manager,
                                   filename: str = 'annual_fundamentals.csv') -> str:
        """
        Export annual fundamentals to CSV.

        Args:
            db_manager: DatabaseManager instance
            filename: Output filename (default: 'annual_fundamentals.csv')

        Returns:
            Path to exported file
        """
        logger.info("Exporting annual fundamentals to CSV")

        from database.db_manager import AnnualFundamental, Stock

        output_path = self.output_dir / filename

        try:
            with db_manager.get_session() as session:
                # Query all annual fundamentals with stock symbols
                query = session.query(
                    Stock.symbol,
                    Stock.company_name,
                    Stock.exchange,
                    AnnualFundamental.fiscal_year,
                    AnnualFundamental.year_end_date,
                    AnnualFundamental.revenue,
                    AnnualFundamental.gross_profit,
                    AnnualFundamental.net_income,
                    AnnualFundamental.operating_cash_flow,
                    AnnualFundamental.free_cash_flow,
                    AnnualFundamental.created_at,
                    AnnualFundamental.updated_at
                ).join(Stock, AnnualFundamental.stock_id == Stock.id).all()

                # Convert to DataFrame
                df = pd.DataFrame(query, columns=[
                    'symbol', 'company_name', 'exchange', 'fiscal_year',
                    'year_end_date', 'revenue', 'gross_profit', 'net_income',
                    'operating_cash_flow', 'free_cash_flow', 'created_at', 'updated_at'
                ])

                # Sort by symbol, year
                df = df.sort_values(['symbol', 'fiscal_year'],
                                   ascending=[True, False])

                # Export to CSV
                df.to_csv(output_path, index=False, encoding='utf-8')

                logger.info(f"Exported {len(df)} annual records to {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export annual fundamentals to CSV: {e}", exc_info=True)
            raise

    def export_all(self, db_manager) -> dict:
        """
        Export all data to 4 CSV files.

        Args:
            db_manager: DatabaseManager instance

        Returns:
            Dict with paths to all exported files
        """
        logger.info("Exporting all data to CSV files")

        try:
            paths = {
                'stocks': self.export_stocks(db_manager),
                'price_history': self.export_price_history(db_manager),
                'quarterly_fundamentals': self.export_quarterly_fundamentals(db_manager),
                'annual_fundamentals': self.export_annual_fundamentals(db_manager)
            }

            logger.info(f"Successfully exported all data to {self.output_dir}")
            return paths

        except Exception as e:
            logger.error(f"Failed to export all data to CSV: {e}", exc_info=True)
            raise
