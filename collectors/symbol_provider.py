"""
Stock Symbol Provider for Tadawul Hawk.
Fetches Tadawul (Saudi Stock Exchange) stock symbols using yfinance/Yahoo Finance.
"""

import yfinance as yf
from typing import List, Set, Optional
from utils import get_logger, validate_symbol

logger = get_logger(__name__)


class SymbolProvider:
    """
    Provides Tadawul stock symbols using Yahoo Finance API.

    Strategy:
    1. Use yfinance to query Tadawul exchange stocks (if available)
    2. Fall back to comprehensive static list if API method unavailable
    """

    def __init__(self):
        self.symbols: Set[str] = set()
        logger.info("SymbolProvider initialized")

    def get_all_symbols(self) -> List[str]:
        """
        Get all Tadawul stock symbols.

        Returns:
            List of validated stock symbols (e.g., ['2222.SR', '1120.SR', ...])
        """
        logger.info("Fetching Tadawul symbols using yfinance...")

        # Try to use yfinance's screener or exchange listing feature
        try:
            self._fetch_from_yfinance()
        except Exception as e:
            logger.warning(f"yfinance exchange listing not available: {e}")
            logger.info("Falling back to static symbol list")
            self._load_static_symbols()

        # Convert to list and sort
        symbol_list = sorted(list(self.symbols))

        logger.info(f"Total symbols loaded: {len(symbol_list)}")
        if symbol_list:
            logger.info(f"Symbol range: {symbol_list[0]} to {symbol_list[-1]}")

        return symbol_list

    def _fetch_from_yfinance(self):
        """
        Attempt to fetch all Tadawul stocks using yfinance.

        This method explores yfinance capabilities to get exchange listings.
        Note: This is experimental and may not work if yfinance doesn't
        support exchange-level queries for Tadawul.
        """
        logger.info("Attempting to fetch symbols from Yahoo Finance API...")

        # Method 1: Try using yfinance Screener (if available)
        try:
            # Check if yfinance has a Screener class
            if hasattr(yf, 'Screener'):
                screener = yf.Screener()
                # Try to get Tadawul stocks
                # Note: This is speculative - may not work
                screener.set_body({
                    'query': {'operator': 'EQ', 'operands': ['exchange', 'SAU']}
                })
                data = screener.response
                if data and 'quotes' in data:
                    for quote in data['quotes']:
                        symbol = quote.get('symbol')
                        if symbol:
                            self.symbols.add(symbol)
                    logger.info(f"Fetched {len(self.symbols)} symbols from yfinance Screener")
                    return
        except Exception as e:
            logger.debug(f"Screener method failed: {e}")

        # Method 2: Try querying a known index ticker
        # Tadawul All Share Index (TASI) - might have constituents
        try:
            tasi = yf.Ticker('TASI.SR')  # or '^TASI'
            # Some index tickers expose their constituents
            if hasattr(tasi, 'constituents'):
                constituents = tasi.constituents
                if constituents:
                    self.symbols.update(constituents)
                    logger.info(f"Fetched {len(self.symbols)} symbols from TASI constituents")
                    return
        except Exception as e:
            logger.debug(f"Index constituents method failed: {e}")

        # If we reach here, yfinance doesn't support exchange listing
        raise Exception("yfinance does not support Tadawul exchange listing")

    def _load_static_symbols(self):
        """
        Load symbols from static file or built-in list.
        This is the fallback when yfinance exchange listing is not available.
        """
        # First try to load from file
        try:
            from pathlib import Path
            symbol_file = Path(__file__).parent.parent / 'data' / 'tadawul_symbols.txt'

            if symbol_file.exists():
                with open(symbol_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith('#'):
                            continue
                        # Handle pipe-delimited format: SYMBOL|COMPANY_NAME|EXCHANGE
                        if '|' in line:
                            parts = line.split('|')
                            symbol = parts[0].strip() if parts else None
                        else:
                            # Handle simple format: just symbol
                            symbol = line

                        if symbol and validate_symbol(symbol):
                            self.symbols.add(symbol)

                logger.info(f"Loaded {len(self.symbols)} symbols from {symbol_file}")
                return
        except Exception as e:
            logger.debug(f"Could not load from file: {e}")

        # Fall back to built-in list of major Tadawul stocks
        logger.info("Using built-in symbol list (major Tadawul stocks)")
        self._add_builtin_symbols()

    def _add_builtin_symbols(self):
        """
        Built-in list of major Tadawul stocks.

        Note: This is a starter list covering major companies.
        Should be replaced with complete list via research or file.
        """
        # Major Tadawul stocks by sector
        major_symbols = [
            # Energy & Petrochemicals
            '2222.SR',  # Saudi Aramco
            '2010.SR',  # SABIC
            '2020.SR',  # SABIC Agri-Nutrients
            '2090.SR',  # Rabigh Refining
            '2060.SR',  # Advanced Petrochemical
            '2310.SR',  # Sipchem
            '2350.SR',  # Saudi Kayan

            # Banking
            '1180.SR',  # Al Rajhi Bank
            '1120.SR',  # Al Rajhi Banking
            '1010.SR',  # Riyad Bank
            '1020.SR',  # Bank AlBilad
            '1030.SR',  # Saudi Investment Bank
            '1050.SR',  # Banque Saudi Fransi
            '1060.SR',  # Bank AlJazira
            '1080.SR',  # Arab National Bank
            '1140.SR',  # Alinma Bank

            # Telecommunications
            '7010.SR',  # Saudi Telecom Company (STC)
            '7020.SR',  # Etihad Etisalat (Mobily)
            '7030.SR',  # Zain Saudi Arabia

            # Retail & Consumer
            '4001.SR',  # Jarir Marketing
            '4050.SR',  # Herfy Food Services
            '4061.SR',  # Abdullah Al Othaim Markets

            # Real Estate
            '4150.SR',  # Emaar The Economic City
            '4160.SR',  # Jabal Omar Development

            # Industrial
            '2110.SR',  # Saudi Basic Industries
            '2250.SR',  # Maaden
            '2270.SR',  # Savola Group
            '2280.SR',  # Almarai Company

            # Insurance (sample)
            '8010.SR',  # Tawuniya
            '8012.SR',  # Bupa Arabia
            '8020.SR',  # Malath Insurance
            '8030.SR',  # Medgulf
            '8050.SR',  # Salama Insurance
        ]

        for symbol in major_symbols:
            if validate_symbol(symbol):
                self.symbols.add(symbol)

        logger.warning(f"Using built-in list with {len(major_symbols)} major stocks")
        logger.warning("For complete coverage, provide full symbol list in data/tadawul_symbols.txt")

    def validate_sample(self, sample_size: int = 5) -> dict:
        """
        Validate a sample of symbols using yfinance to ensure they're real.

        Args:
            sample_size: Number of symbols to validate

        Returns:
            Dict with validation results
        """
        if not self.symbols:
            return {'valid': 0, 'invalid': 0, 'success_rate': 0.0}

        logger.info(f"Validating sample of {min(sample_size, len(self.symbols))} symbols...")

        valid_count = 0
        invalid_count = 0

        import random
        sample = random.sample(list(self.symbols), min(sample_size, len(self.symbols)))

        for symbol in sample:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                if info and ('symbol' in info or 'shortName' in info or 'longName' in info):
                    valid_count += 1
                    logger.debug(f"✓ {symbol} is valid")
                else:
                    invalid_count += 1
                    logger.debug(f"✗ {symbol} appears invalid")

            except Exception as e:
                invalid_count += 1
                logger.debug(f"✗ {symbol} validation failed: {e}")

        success_rate = (valid_count / len(sample)) * 100 if sample else 0

        results = {
            'valid': valid_count,
            'invalid': invalid_count,
            'total_sampled': len(sample),
            'success_rate': success_rate
        }

        logger.info(f"Validation: {valid_count}/{len(sample)} valid ({success_rate:.1f}% success rate)")

        return results

    def get_symbol_count(self) -> int:
        """Get total number of symbols."""
        return len(self.symbols)

    def save_symbols_to_file(self, filepath: str):
        """Save symbols to a text file for reference."""
        try:
            with open(filepath, 'w') as f:
                for symbol in sorted(self.symbols):
                    f.write(f"{symbol}\n")
            logger.info(f"Symbols saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save symbols to file: {e}")

    def load_symbols_from_file(self, filepath: str) -> List[str]:
        """Load symbols from a text file."""
        try:
            with open(filepath, 'r') as f:
                symbols = [line.strip() for line in f if line.strip() and validate_symbol(line.strip())]
            logger.info(f"Loaded {len(symbols)} symbols from {filepath}")
            self.symbols.update(symbols)
            return symbols
        except Exception as e:
            logger.error(f"Failed to load symbols from file: {e}")
            return []