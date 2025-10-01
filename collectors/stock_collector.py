"""
Stock Data Collector for Tadawul Hawk.
Fetches price data and fundamentals using yfinance.
"""

import yfinance as yf
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from utils import get_logger

logger = get_logger(__name__)


class StockCollector:
    """
    Collects stock data from Yahoo Finance for Saudi stocks.

    Features:
    - Current and historical price data
    - 52-week, 3-year, 5-year high/low prices
    - Quarterly fundamentals (last 5 years)
    - Annual fundamentals (last 5 years)
    - Rate limiting and retry logic
    """

    def __init__(self, symbol: str, rate_limit_delay: float = 0.5):
        """
        Initialize the stock collector.

        Args:
            symbol: Stock symbol (e.g., '2222.SR')
            rate_limit_delay: Delay between API calls in seconds (default 0.5s)
        """
        self.symbol = symbol
        self.rate_limit_delay = rate_limit_delay
        self.ticker = None
        self.last_request_time = 0

        logger.info(f"StockCollector initialized for {symbol}")

    def _rate_limit(self):
        """Apply rate limiting between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _retry_with_backoff(self, func, max_attempts: int = 4, *args, **kwargs):
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: Function to execute
            max_attempts: Maximum number of retry attempts (default 4)
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result or None if all attempts fail
        """
        for attempt in range(max_attempts):
            try:
                self._rate_limit()
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Attempt {attempt + 1} failed for {self.symbol}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} attempts failed for {self.symbol}: {e}")
                    return None

    def _get_ticker(self):
        """Get or create yfinance Ticker object."""
        if self.ticker is None:
            self.ticker = yf.Ticker(self.symbol)
        return self.ticker

    def fetch_stock_info(self) -> Dict[str, Any]:
        """
        Fetch basic stock information (name, sector, industry, etc.).

        Returns:
            Dict with stock metadata
        """
        logger.info(f"Fetching stock info for {self.symbol}")

        def _fetch():
            ticker = self._get_ticker()
            info = ticker.info
            return {
                'symbol': self.symbol,
                'company_name': info.get('longName') or info.get('shortName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'currency': info.get('currency', 'SAR')
            }

        result = self._retry_with_backoff(_fetch)
        if result:
            logger.info(f"Successfully fetched info for {self.symbol}: {result.get('company_name')}")
        return result or {}

    def fetch_price_data(self) -> Dict[str, Any]:
        """
        Fetch current price data.

        Returns:
            Dict with current price information
        """
        logger.info(f"Fetching current price for {self.symbol}")

        def _fetch():
            ticker = self._get_ticker()
            hist = ticker.history(period='5d')  # Get last 5 days to ensure we have recent data

            if hist.empty:
                logger.warning(f"No price history available for {self.symbol}")
                return None

            # Get most recent close price
            last_close = hist['Close'].iloc[-1]

            return {
                'symbol': self.symbol,
                'last_close_price': float(last_close),
                'data_date': hist.index[-1].date()
            }

        result = self._retry_with_backoff(_fetch)
        if result:
            logger.info(f"Current price for {self.symbol}: {result.get('last_close_price')}")
        return result or {}

    def fetch_historical_prices(self, months_ago: List[int] = [1, 3, 6, 9, 12]) -> Dict[int, float]:
        """
        Fetch historical prices for specified months ago (30 calendar days lookback).

        Args:
            months_ago: List of months to look back (default [1, 3, 6, 9, 12])

        Returns:
            Dict mapping months_ago to prices
        """
        logger.info(f"Fetching historical prices for {self.symbol}")

        def _fetch():
            ticker = self._get_ticker()

            # Fetch 2 years of history to cover all requested periods
            hist = ticker.history(period='2y')

            if hist.empty:
                logger.warning(f"No historical data available for {self.symbol}")
                return {}

            prices = {}
            today = pd.Timestamp.now(tz=hist.index.tz)  # Use same timezone as hist.index

            for months in months_ago:
                # Calculate target date (months ago, rounded to 30 calendar days)
                target_date = today - pd.Timedelta(days=months * 30)

                # Find closest available trading day (within 7 days tolerance)
                tolerance = pd.Timedelta(days=7)
                mask = (hist.index >= target_date - tolerance) & (hist.index <= target_date + tolerance)
                available_dates = hist[mask]

                if not available_dates.empty:
                    # Get closest date
                    time_diffs = abs(available_dates.index - target_date)
                    closest_idx = time_diffs.argmin()
                    closest_date = available_dates.index[closest_idx]
                    price = float(available_dates.loc[closest_date, 'Close'])
                    prices[months] = price
                    logger.debug(f"{self.symbol}: {months}m ago = {price} (date: {closest_date.date()})")
                else:
                    logger.warning(f"No data found for {self.symbol} at {months}m ago")
                    prices[months] = None

            return prices

        result = self._retry_with_backoff(_fetch)
        return result or {}

    def calculate_high_low(self) -> Dict[str, Any]:
        """
        Calculate high/low prices for 52-week, 3-year, and 5-year periods.

        Returns:
            Dict with high/low prices for each period
        """
        logger.info(f"Calculating high/low for {self.symbol}")

        def _fetch():
            ticker = self._get_ticker()

            # Fetch enough history for all periods
            hist = ticker.history(period='5y')

            if hist.empty:
                logger.warning(f"No historical data for high/low calculation: {self.symbol}")
                return {}

            today = pd.Timestamp.now(tz=hist.index.tz)  # Use same timezone as hist.index
            results = {}

            # 52-week (1 year)
            one_year_ago = today - pd.Timedelta(days=365)
            mask_52w = hist.index >= one_year_ago
            if mask_52w.any():
                results['week_52_high'] = float(hist[mask_52w]['High'].max())
                results['week_52_low'] = float(hist[mask_52w]['Low'].min())

            # 3-year
            three_years_ago = today - pd.Timedelta(days=3*365)
            mask_3y = hist.index >= three_years_ago
            if mask_3y.any():
                results['year_3_high'] = float(hist[mask_3y]['High'].max())
                results['year_3_low'] = float(hist[mask_3y]['Low'].min())

            # 5-year
            five_years_ago = today - pd.Timedelta(days=5*365)
            mask_5y = hist.index >= five_years_ago
            if mask_5y.any():
                results['year_5_high'] = float(hist[mask_5y]['High'].max())
                results['year_5_low'] = float(hist[mask_5y]['Low'].min())

            logger.info(f"High/low calculated for {self.symbol}: 52w=[{results.get('week_52_low')}-{results.get('week_52_high')}]")
            return results

        result = self._retry_with_backoff(_fetch)
        return result or {}

    def fetch_quarterly_fundamentals(self, years: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch quarterly fundamental data for the last N years.

        Args:
            years: Number of years to fetch (default 5)

        Returns:
            List of dicts with quarterly financial data
        """
        logger.info(f"Fetching quarterly fundamentals for {self.symbol} (last {years} years)")

        def _fetch():
            ticker = self._get_ticker()

            try:
                # Get quarterly financials
                quarterly_income = ticker.quarterly_financials
                quarterly_cashflow = ticker.quarterly_cashflow

                if quarterly_income is None or quarterly_income.empty:
                    logger.warning(f"No quarterly financials available for {self.symbol}")
                    return []

                results = []
                cutoff_date = datetime.now() - timedelta(days=years*365)

                # Process each quarter
                for col in quarterly_income.columns:
                    quarter_date = col

                    # Skip if older than cutoff
                    if quarter_date < cutoff_date:
                        continue

                    # Extract financial metrics
                    quarter_data = {
                        'symbol': self.symbol,
                        'fiscal_year': quarter_date.year,
                        'fiscal_quarter': (quarter_date.month - 1) // 3 + 1,  # Calculate quarter (1-4)
                        'quarter_end_date': quarter_date.date(),
                    }

                    # Revenue (Total Revenue or Operating Revenue)
                    if 'Total Revenue' in quarterly_income.index:
                        quarter_data['revenue'] = float(quarterly_income.loc['Total Revenue', col]) if pd.notna(quarterly_income.loc['Total Revenue', col]) else None

                    # Gross Profit
                    if 'Gross Profit' in quarterly_income.index:
                        quarter_data['gross_profit'] = float(quarterly_income.loc['Gross Profit', col]) if pd.notna(quarterly_income.loc['Gross Profit', col]) else None

                    # Net Income
                    if 'Net Income' in quarterly_income.index:
                        quarter_data['net_income'] = float(quarterly_income.loc['Net Income', col]) if pd.notna(quarterly_income.loc['Net Income', col]) else None

                    # Operating Cash Flow
                    if quarterly_cashflow is not None and not quarterly_cashflow.empty:
                        if 'Operating Cash Flow' in quarterly_cashflow.index and col in quarterly_cashflow.columns:
                            quarter_data['operating_cash_flow'] = float(quarterly_cashflow.loc['Operating Cash Flow', col]) if pd.notna(quarterly_cashflow.loc['Operating Cash Flow', col]) else None

                        # Capital Expenditure
                        if 'Capital Expenditure' in quarterly_cashflow.index and col in quarterly_cashflow.columns:
                            quarter_data['capital_expenditure'] = float(quarterly_cashflow.loc['Capital Expenditure', col]) if pd.notna(quarterly_cashflow.loc['Capital Expenditure', col]) else None

                        # Free Cash Flow
                        if 'Free Cash Flow' in quarterly_cashflow.index and col in quarterly_cashflow.columns:
                            quarter_data['free_cash_flow'] = float(quarterly_cashflow.loc['Free Cash Flow', col]) if pd.notna(quarterly_cashflow.loc['Free Cash Flow', col]) else None

                    results.append(quarter_data)

                logger.info(f"Fetched {len(results)} quarters of data for {self.symbol}")
                return results

            except Exception as e:
                logger.error(f"Error fetching quarterly fundamentals for {self.symbol}: {e}")
                return []

        result = self._retry_with_backoff(_fetch)
        return result or []

    def fetch_annual_fundamentals(self, years: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch annual fundamental data for the last N years.

        Args:
            years: Number of years to fetch (default 5)

        Returns:
            List of dicts with annual financial data
        """
        logger.info(f"Fetching annual fundamentals for {self.symbol} (last {years} years)")

        def _fetch():
            ticker = self._get_ticker()

            try:
                # Get annual financials
                annual_income = ticker.financials  # This gives annual by default
                annual_cashflow = ticker.cashflow

                if annual_income is None or annual_income.empty:
                    logger.warning(f"No annual financials available for {self.symbol}")
                    return []

                results = []
                cutoff_date = datetime.now() - timedelta(days=years*365)

                # Process each year
                for col in annual_income.columns:
                    year_date = col

                    # Skip if older than cutoff
                    if year_date < cutoff_date:
                        continue

                    # Extract financial metrics
                    year_data = {
                        'symbol': self.symbol,
                        'fiscal_year': year_date.year,
                        'year_end_date': year_date.date(),
                    }

                    # Revenue (Total Revenue or Operating Revenue)
                    if 'Total Revenue' in annual_income.index:
                        year_data['revenue'] = float(annual_income.loc['Total Revenue', col]) if pd.notna(annual_income.loc['Total Revenue', col]) else None

                    # Gross Profit
                    if 'Gross Profit' in annual_income.index:
                        year_data['gross_profit'] = float(annual_income.loc['Gross Profit', col]) if pd.notna(annual_income.loc['Gross Profit', col]) else None

                    # Net Income
                    if 'Net Income' in annual_income.index:
                        year_data['net_income'] = float(annual_income.loc['Net Income', col]) if pd.notna(annual_income.loc['Net Income', col]) else None

                    # Operating Cash Flow
                    if annual_cashflow is not None and not annual_cashflow.empty:
                        if 'Operating Cash Flow' in annual_cashflow.index and col in annual_cashflow.columns:
                            year_data['operating_cash_flow'] = float(annual_cashflow.loc['Operating Cash Flow', col]) if pd.notna(annual_cashflow.loc['Operating Cash Flow', col]) else None

                        # Capital Expenditure
                        if 'Capital Expenditure' in annual_cashflow.index and col in annual_cashflow.columns:
                            year_data['capital_expenditure'] = float(annual_cashflow.loc['Capital Expenditure', col]) if pd.notna(annual_cashflow.loc['Capital Expenditure', col]) else None

                        # Free Cash Flow
                        if 'Free Cash Flow' in annual_cashflow.index and col in annual_cashflow.columns:
                            year_data['free_cash_flow'] = float(annual_cashflow.loc['Free Cash Flow', col]) if pd.notna(annual_cashflow.loc['Free Cash Flow', col]) else None

                    results.append(year_data)

                logger.info(f"Fetched {len(results)} years of data for {self.symbol}")
                return results

            except Exception as e:
                logger.error(f"Error fetching annual fundamentals for {self.symbol}: {e}")
                return []

        result = self._retry_with_backoff(_fetch)
        return result or []

    def fetch_valuation_data(self) -> Dict[str, Any]:
        """
        Fetch valuation data (market cap, debt, cash, book value) for analysis.

        Returns:
            Dict with valuation metrics
        """
        logger.info(f"Fetching valuation data for {self.symbol}")

        def _fetch():
            ticker = self._get_ticker()
            info = ticker.info

            # Get market cap
            market_cap = info.get('marketCap')

            # Get debt (try multiple field names)
            total_debt = (info.get('totalDebt') or
                         info.get('longTermDebt', 0) + info.get('shortLongTermDebt', 0))

            # Get cash
            total_cash = info.get('totalCash') or info.get('cash', 0)

            # Get TOTAL book value (stockholders equity) - NOT per share
            # Try multiple approaches in order of preference
            book_value = None
            balance_sheet_date = None

            # 1. Try to get from balance sheet (most reliable for TOTAL value)
            try:
                balance_sheet = ticker.balance_sheet
                if balance_sheet is not None and not balance_sheet.empty:
                    # Get the most recent balance sheet date (first column)
                    balance_sheet_date = str(balance_sheet.columns[0].date())

                    if 'Stockholders Equity' in balance_sheet.index:
                        # Get most recent value (first column)
                        book_value = float(balance_sheet.loc['Stockholders Equity'].iloc[0])
                        if pd.notna(book_value):
                            logger.debug(f"{self.symbol}: Got book value from balance sheet: {book_value}")
            except Exception as e:
                logger.debug(f"{self.symbol}: Could not get book value from balance sheet: {e}")

            # 2. Try from info dict (totalStockholderEquity is total, not per share)
            if book_value is None:
                book_value = info.get('totalStockholderEquity')
                if book_value:
                    logger.debug(f"{self.symbol}: Got book value from info: {book_value}")

            # 3. Last resort: calculate from bookValue (per share) × shares outstanding
            if book_value is None:
                book_value_per_share = info.get('bookValue')
                shares_outstanding = info.get('sharesOutstanding')
                if book_value_per_share and shares_outstanding:
                    book_value = book_value_per_share * shares_outstanding
                    logger.debug(f"{self.symbol}: Calculated book value = {book_value_per_share} × {shares_outstanding} = {book_value}")

            return {
                'market_cap': market_cap,
                'total_debt': total_debt if total_debt else 0,
                'total_cash': total_cash if total_cash else 0,
                'book_value': book_value,
                'balance_sheet_date': balance_sheet_date
            }

        result = self._retry_with_backoff(_fetch)
        if result and result.get('market_cap'):
            logger.info(f"Successfully fetched valuation data for {self.symbol}")
        else:
            logger.warning(f"Limited valuation data available for {self.symbol}")
        return result or {'market_cap': None, 'total_debt': 0, 'total_cash': 0, 'book_value': None, 'balance_sheet_date': None}

    def collect_all_data(self) -> Dict[str, Any]:
        """
        Collect all data for this stock (info, prices, fundamentals).

        Returns:
            Dict containing all collected data
        """
        logger.info(f"Collecting all data for {self.symbol}")

        data = {
            'symbol': self.symbol,
            'stock_info': self.fetch_stock_info(),
            'current_price': self.fetch_price_data(),
            'historical_prices': self.fetch_historical_prices(),
            'high_low': self.calculate_high_low(),
            'quarterly_fundamentals': self.fetch_quarterly_fundamentals(),
            'annual_fundamentals': self.fetch_annual_fundamentals(),
            'valuation_data': self.fetch_valuation_data()
        }

        logger.info(f"Data collection complete for {self.symbol}")
        return data
