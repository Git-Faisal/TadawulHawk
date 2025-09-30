"""
Data Validator for Tadawul Hawk.
Validates collected stock data for completeness and consistency.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
from utils import get_logger

logger = get_logger(__name__)


class ValidationResult:
    """Container for validation results."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.is_valid = True
        self.errors = []
        self.warnings = []

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False
        logger.error(f"{self.symbol}: {message}")

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(f"{self.symbol}: {message}")

    def __str__(self):
        status = "VALID" if self.is_valid else "INVALID"
        result = f"Validation Result for {self.symbol}: {status}\n"

        if self.errors:
            result += f"\nErrors ({len(self.errors)}):\n"
            for error in self.errors:
                result += f"  - {error}\n"

        if self.warnings:
            result += f"\nWarnings ({len(self.warnings)}):\n"
            for warning in self.warnings:
                result += f"  - {warning}\n"

        return result


class DataValidator:
    """
    Validates stock data for completeness and consistency.

    Features:
    - Stock metadata validation
    - Price data validation
    - Quarterly vs Annual consistency checks
    - Data completeness checks
    - Data quality checks
    """

    def __init__(self, tolerance_pct: float = 2.0):
        """
        Initialize validator.

        Args:
            tolerance_pct: Tolerance percentage for quarterly vs annual validation (default 2%)
        """
        self.tolerance_pct = tolerance_pct
        logger.info(f"DataValidator initialized with {tolerance_pct}% tolerance")

    def validate_collected_data(self, symbol: str, collected_data: Dict[str, Any],
                                exchange: str = 'Tadawul') -> ValidationResult:
        """
        Validate all collected data for a stock.

        Args:
            symbol: Stock symbol
            collected_data: Data from StockCollector.collect_all_data()
            exchange: Exchange market ('Tadawul' or 'NOMU') - affects validation rules

        Returns:
            ValidationResult object
        """
        logger.info(f"Validating collected data for {symbol} (Exchange: {exchange})")
        result = ValidationResult(symbol)

        # 1. Validate stock info
        self._validate_stock_info(collected_data.get('stock_info', {}), result)

        # 2. Validate current price
        self._validate_current_price(collected_data.get('current_price', {}), result)

        # 3. Validate historical prices
        self._validate_historical_prices(collected_data.get('historical_prices', {}), result)

        # 4. Validate high/low data
        self._validate_high_low(collected_data.get('high_low', {}), result)

        # 5. Validate quarterly fundamentals
        quarterly_data = collected_data.get('quarterly_fundamentals', [])
        self._validate_quarterly_fundamentals(quarterly_data, result)

        # 6. Validate annual fundamentals
        annual_data = collected_data.get('annual_fundamentals', [])
        self._validate_annual_fundamentals(annual_data, result)

        # 7. Validate quarterly vs annual consistency
        if quarterly_data and annual_data:
            self._validate_quarterly_vs_annual(quarterly_data, annual_data, result, exchange)

        logger.info(f"Validation complete for {symbol}: {result.is_valid}")
        return result

    def _validate_stock_info(self, stock_info: Dict[str, Any], result: ValidationResult):
        """Validate stock metadata."""
        if not stock_info:
            result.add_error("Stock info is missing")
            return

        # Check required fields
        if not stock_info.get('company_name'):
            result.add_error("Company name is missing")

        if not stock_info.get('sector'):
            result.add_warning("Sector is missing")

        if not stock_info.get('industry'):
            result.add_warning("Industry is missing")

    def _validate_current_price(self, current_price: Dict[str, Any], result: ValidationResult):
        """Validate current price data."""
        if not current_price:
            result.add_error("Current price data is missing")
            return

        price = current_price.get('last_close_price')
        if price is None:
            result.add_error("Last close price is missing")
        elif price <= 0:
            result.add_error(f"Last close price is invalid: {price}")

        if not current_price.get('data_date'):
            result.add_error("Price data date is missing")

    def _validate_historical_prices(self, historical_prices: Dict[int, float], result: ValidationResult):
        """Validate historical price data."""
        if not historical_prices:
            result.add_warning("No historical prices available")
            return

        expected_periods = [1, 3, 6, 9, 12]
        for period in expected_periods:
            price = historical_prices.get(period)
            if price is None:
                result.add_warning(f"Historical price for {period}m ago is missing")
            elif price <= 0:
                result.add_error(f"Historical price for {period}m ago is invalid: {price}")

    def _validate_high_low(self, high_low: Dict[str, float], result: ValidationResult):
        """Validate high/low price data."""
        if not high_low:
            result.add_warning("No high/low data available")
            return

        # 52-week high/low
        week_52_high = high_low.get('week_52_high')
        week_52_low = high_low.get('week_52_low')

        if week_52_high is None:
            result.add_warning("52-week high is missing")
        elif week_52_high <= 0:
            result.add_error(f"52-week high is invalid: {week_52_high}")

        if week_52_low is None:
            result.add_warning("52-week low is missing")
        elif week_52_low <= 0:
            result.add_error(f"52-week low is invalid: {week_52_low}")

        # Check high >= low
        if week_52_high and week_52_low and week_52_high < week_52_low:
            result.add_error(f"52-week high ({week_52_high}) is less than low ({week_52_low})")

        # 3-year high/low (optional)
        year_3_high = high_low.get('year_3_high')
        year_3_low = high_low.get('year_3_low')
        if year_3_high and year_3_low and year_3_high < year_3_low:
            result.add_error(f"3-year high ({year_3_high}) is less than low ({year_3_low})")

        # 5-year high/low (optional)
        year_5_high = high_low.get('year_5_high')
        year_5_low = high_low.get('year_5_low')
        if year_5_high and year_5_low and year_5_high < year_5_low:
            result.add_error(f"5-year high ({year_5_high}) is less than low ({year_5_low})")

    def _validate_quarterly_fundamentals(self, quarterly_data: List[Dict[str, Any]], result: ValidationResult):
        """Validate quarterly fundamental data."""
        if not quarterly_data:
            result.add_warning("No quarterly fundamental data available")
            return

        for quarter in quarterly_data:
            # Check required fields
            if 'fiscal_year' not in quarter:
                result.add_error("Quarterly record missing fiscal_year")
            if 'fiscal_quarter' not in quarter:
                result.add_error("Quarterly record missing fiscal_quarter")
            elif quarter['fiscal_quarter'] not in [1, 2, 3, 4]:
                result.add_error(f"Invalid fiscal quarter: {quarter['fiscal_quarter']}")

            # Check for at least some financial data
            has_data = any([
                quarter.get('revenue'),
                quarter.get('gross_profit'),
                quarter.get('net_income')
            ])
            if not has_data:
                result.add_warning(f"Q{quarter.get('fiscal_quarter', '?')} {quarter.get('fiscal_year', '?')} has no financial data")

    def _validate_annual_fundamentals(self, annual_data: List[Dict[str, Any]], result: ValidationResult):
        """Validate annual fundamental data."""
        if not annual_data:
            result.add_warning("No annual fundamental data available")
            return

        for year in annual_data:
            # Check required fields
            if 'fiscal_year' not in year:
                result.add_error("Annual record missing fiscal_year")

            # Check for at least some financial data
            has_data = any([
                year.get('revenue'),
                year.get('gross_profit'),
                year.get('net_income')
            ])
            if not has_data:
                result.add_warning(f"Year {year.get('fiscal_year', '?')} has no financial data")

    def _validate_quarterly_vs_annual(self, quarterly_data: List[Dict[str, Any]],
                                     annual_data: List[Dict[str, Any]],
                                     result: ValidationResult,
                                     exchange: str = 'Tadawul'):
        """
        Validate that quarterly data sums match annual data.

        This is a critical check - the sum of 4 quarters should approximately equal the annual figure.

        Note:
        - NOMU stocks only report semiannually, so this validation is skipped for NOMU
        - Validation is skipped when quarters have NaN values (Yahoo Finance data limitation)
        """
        # Skip validation for NOMU stocks (semiannual reporting is normal)
        if exchange == 'NOMU':
            logger.info(f"Skipping quarterly vs annual validation for {result.symbol} (NOMU stocks report semiannually)")
            return

        logger.info(f"Validating quarterly vs annual consistency for {result.symbol}")

        # Group quarterly data by year
        quarters_by_year = {}
        for quarter in quarterly_data:
            year = quarter.get('fiscal_year')
            if year:
                if year not in quarters_by_year:
                    quarters_by_year[year] = []
                quarters_by_year[year].append(quarter)

        # Create annual data lookup
        annual_by_year = {year['fiscal_year']: year for year in annual_data if 'fiscal_year' in year}

        # Check each year that has both quarterly and annual data
        for year, quarters in quarters_by_year.items():
            if year not in annual_by_year:
                continue  # No annual data to compare

            # Check if we have all 4 quarters
            if len(quarters) != 4:
                logger.debug(f"{result.symbol}: Year {year} has {len(quarters)} quarters (need 4 for validation)")
                continue

            # Check if any quarter has NaN values (Yahoo Finance data limitation)
            quarters_with_data = []
            for q in quarters:
                has_data = any([
                    q.get('revenue') is not None,
                    q.get('gross_profit') is not None,
                    q.get('net_income') is not None
                ])
                if has_data:
                    quarters_with_data.append(q)

            if len(quarters_with_data) < 4:
                logger.info(
                    f"{result.symbol}: Year {year} has only {len(quarters_with_data)}/4 quarters with data "
                    f"(Yahoo Finance limitation) - skipping quarterly vs annual validation"
                )
                continue

            annual = annual_by_year[year]

            # Validate Revenue
            self._validate_metric_sum(quarters, annual, year, 'revenue', 'Revenue', result)

            # Validate Gross Profit
            self._validate_metric_sum(quarters, annual, year, 'gross_profit', 'Gross Profit', result)

            # Validate Net Income
            self._validate_metric_sum(quarters, annual, year, 'net_income', 'Net Income', result)

            # Validate Operating Cash Flow
            self._validate_metric_sum(quarters, annual, year, 'operating_cash_flow', 'Operating Cash Flow', result)

            # Validate Free Cash Flow
            self._validate_metric_sum(quarters, annual, year, 'free_cash_flow', 'Free Cash Flow', result)

    def _validate_metric_sum(self, quarters: List[Dict], annual: Dict, year: int,
                            metric_key: str, metric_name: str, result: ValidationResult):
        """
        Validate that quarterly metric sum matches annual metric.

        Args:
            quarters: List of 4 quarterly records
            annual: Annual record
            year: Fiscal year
            metric_key: Key for the metric (e.g., 'revenue')
            metric_name: Human-readable metric name (e.g., 'Revenue')
            result: ValidationResult to update
        """
        # Get quarterly values (skip None)
        quarterly_values = [q.get(metric_key) for q in quarters if q.get(metric_key) is not None]

        # Get annual value
        annual_value = annual.get(metric_key)

        # Skip if we don't have enough data
        if not quarterly_values or annual_value is None:
            return

        # Calculate quarterly sum
        quarterly_sum = sum(quarterly_values)

        # Calculate difference
        diff = abs(quarterly_sum - annual_value)
        diff_pct = (diff / abs(annual_value)) * 100 if annual_value != 0 else 0

        # Check if within tolerance
        if diff_pct > self.tolerance_pct:
            result.add_error(
                f"{metric_name} mismatch for {year}: "
                f"Quarterly sum = {quarterly_sum:,.0f}, Annual = {annual_value:,.0f} "
                f"(Difference: {diff_pct:.1f}%)"
            )
        else:
            logger.debug(
                f"{result.symbol} {year} {metric_name}: "
                f"Quarterly = {quarterly_sum:,.0f}, Annual = {annual_value:,.0f} "
                f"(Difference: {diff_pct:.2f}%) ✓"
            )

    def validate_database_data(self, db_manager, symbol: str) -> ValidationResult:
        """
        Validate data stored in the database for a stock.

        Args:
            db_manager: DatabaseManager instance
            symbol: Stock symbol

        Returns:
            ValidationResult object
        """
        logger.info(f"Validating database data for {symbol}")
        result = ValidationResult(symbol)

        from database.db_manager import Stock, PriceHistory, QuarterlyFundamental, AnnualFundamental

        with db_manager.get_session() as session:
            # Check if stock exists
            stock = session.query(Stock).filter(Stock.symbol == symbol).first()

            if not stock:
                result.add_error("Stock not found in database")
                return result

            # Validate stock metadata
            if not stock.company_name:
                result.add_error("Company name is missing in database")
            if not stock.exchange:
                result.add_warning("Exchange is missing in database")

            # Check price history
            price_count = session.query(PriceHistory).filter(PriceHistory.stock_id == stock.id).count()
            if price_count == 0:
                result.add_warning("No price history in database")

            # Check quarterly fundamentals
            quarterly_count = session.query(QuarterlyFundamental).filter(
                QuarterlyFundamental.stock_id == stock.id
            ).count()
            if quarterly_count == 0:
                result.add_warning("No quarterly fundamentals in database")

            # Check annual fundamentals
            annual_count = session.query(AnnualFundamental).filter(
                AnnualFundamental.stock_id == stock.id
            ).count()
            if annual_count == 0:
                result.add_warning("No annual fundamentals in database")

            logger.info(
                f"{symbol} database status: "
                f"{price_count} price records, "
                f"{quarterly_count} quarterly records, "
                f"{annual_count} annual records"
            )

        return result
