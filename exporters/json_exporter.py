"""
JSON Exporter for Tadawul Hawk.
Exports stock data to JSON format.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from utils import get_logger

logger = get_logger(__name__)


class JSONExporter:
    """
    Exports stock data to JSON format.

    Features:
    - Exports single stock data to JSON file
    - Exports multiple stocks data to single JSON file
    - Pretty-printed JSON with proper formatting
    - Handles date serialization automatically
    """

    def __init__(self, output_dir: str = 'exports'):
        """
        Initialize JSON exporter.

        Args:
            output_dir: Directory for exported files (default: 'exports')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSONExporter initialized (output: {self.output_dir})")

    def _serialize_dates(self, obj: Any) -> Any:
        """
        Convert date/datetime/Decimal objects to JSON-serializable types.

        Args:
            obj: Object to serialize

        Returns:
            Serialized object
        """
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_dates(item) for item in obj]
        else:
            return obj

    def export_stock(self, symbol: str, stock_data: Dict[str, Any],
                     filename: Optional[str] = None) -> str:
        """
        Export single stock data to JSON file.

        Args:
            symbol: Stock symbol
            stock_data: Stock data dictionary (from DatabaseManager.export_stock_data)
            filename: Custom filename (optional, defaults to {symbol}.json)

        Returns:
            Path to exported file
        """
        logger.info(f"Exporting {symbol} to JSON")

        # Generate filename
        if filename is None:
            filename = f"{symbol.replace('.', '_')}.json"

        output_path = self.output_dir / filename

        # Serialize dates
        serialized_data = self._serialize_dates(stock_data)

        # Write JSON file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {symbol} to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export {symbol} to JSON: {e}", exc_info=True)
            raise

    def export_multiple_stocks(self, stocks_data: List[Dict[str, Any]],
                               filename: str = 'all_stocks.json') -> str:
        """
        Export multiple stocks data to single JSON file.

        Args:
            stocks_data: List of stock data dictionaries
            filename: Output filename (default: 'all_stocks.json')

        Returns:
            Path to exported file
        """
        logger.info(f"Exporting {len(stocks_data)} stocks to JSON")

        output_path = self.output_dir / filename

        # Serialize dates
        serialized_data = self._serialize_dates(stocks_data)

        # Write JSON file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(stocks_data)} stocks to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export multiple stocks to JSON: {e}", exc_info=True)
            raise

    def export_from_database(self, db_manager, symbol: str,
                            filename: Optional[str] = None) -> str:
        """
        Export stock data directly from database to JSON.

        Args:
            db_manager: DatabaseManager instance
            symbol: Stock symbol
            filename: Custom filename (optional)

        Returns:
            Path to exported file
        """
        logger.info(f"Exporting {symbol} from database to JSON")

        # Get data from database
        stock_data = db_manager.export_stock_data(symbol)

        if not stock_data:
            raise ValueError(f"No data found for {symbol} in database")

        # Export to JSON
        return self.export_stock(symbol, stock_data, filename)

    def export_all_from_database(self, db_manager,
                                 filename: str = 'all_stocks.json') -> str:
        """
        Export all stocks from database to single JSON file.

        Args:
            db_manager: DatabaseManager instance
            filename: Output filename (default: 'all_stocks.json')

        Returns:
            Path to exported file
        """
        logger.info("Exporting all stocks from database to JSON")

        from database.db_manager import Stock

        # Get all stock symbols
        with db_manager.get_session() as session:
            stocks = session.query(Stock).all()
            symbols = [stock.symbol for stock in stocks]

        logger.info(f"Found {len(symbols)} stocks in database")

        # Export each stock
        all_stocks_data = []
        for symbol in symbols:
            try:
                stock_data = db_manager.export_stock_data(symbol)
                if stock_data:
                    all_stocks_data.append(stock_data)
            except Exception as e:
                logger.error(f"Failed to export {symbol}: {e}")

        # Write to file
        return self.export_multiple_stocks(all_stocks_data, filename)
