"""
Argaam Stock Symbol Scraper for Tadawul Hawk.
Scrapes Argaam.com to get complete list of Tadawul stock symbols.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List
from utils import get_logger, validate_symbol

logger = get_logger(__name__)


class ArgaamScraper:
    """
    Scrapes Argaam.com to get complete list of Saudi stock symbols.
    Supports both Tadawul (main market) and NOMU (parallel market).

    Sources:
    - Tadawul: https://www.argaam.com/en/company/companies-prices/3
    - NOMU: https://www.argaam.com/en/company/companies-prices/14
    """

    def __init__(self, market: str = 'tadawul'):
        """
        Initialize the scraper.

        Args:
            market: 'tadawul' for main market or 'nomu' for parallel market
        """
        self.market = market.lower()
        if self.market == 'tadawul':
            self.url = "https://www.argaam.com/en/company/companies-prices/3"
            self.default_exchange = 'Tadawul'
        elif self.market == 'nomu':
            self.url = "https://www.argaam.com/en/company/companies-prices/14"
            self.default_exchange = 'NOMU'
        else:
            raise ValueError("Market must be 'tadawul' or 'nomu'")

        self.symbols_data: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        logger.info(f"ArgaamScraper initialized for {self.market.upper()} market")

    def scrape_all_symbols(self) -> List[Dict]:
        """
        Scrape all stock symbols from Argaam.

        Returns:
            List of dicts with symbol data: {'symbol': '2222.SR', 'exchange': 'Tadawul', 'company_name': '...'}
        """
        logger.info(f"Scraping Argaam stock list from: {self.url}")

        try:
            # Fetch the page
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            logger.info(f"Successfully fetched page (status: {response.status_code})")

            soup = BeautifulSoup(response.content, 'lxml')

            # Log page title
            if soup.title:
                logger.info(f"Page title: {soup.title.string}")

            # Find the table with stock data
            # Argaam typically uses tables for this data
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables on page")

            if not tables:
                logger.warning("No tables found on page")
                return []

            # Process ALL tables that have symbol columns
            # Don't just process one table - there might be multiple tables with different stocks
            target_tables = []
            for table in tables:
                # Check if this table has the St.Symbol column
                headers = table.find_all('th')
                header_texts = [th.get_text().strip() for th in headers]

                logger.debug(f"Table headers: {header_texts}")

                if any('symbol' in h.lower() for h in header_texts):
                    target_tables.append(table)
                    logger.info(f"Found target table with headers: {header_texts}")

            if not target_tables:
                # If no table with explicit headers, try the largest table
                target_tables = [max(tables, key=lambda t: len(t.find_all('tr')))]
                logger.info(f"Using largest table with {len(target_tables[0].find_all('tr'))} rows")

            logger.info(f"Processing {len(target_tables)} tables")

            # Extract data from each table
            for table_idx, target_table in enumerate(target_tables):
                rows = target_table.find_all('tr')
                logger.info(f"Table {table_idx + 1}: Processing {len(rows)} rows")

                # Get headers
                header_row = rows[0] if rows else None
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    logger.info(f"Column headers: {headers}")

                    # Find column indices
                    symbol_col_idx = None
                    name_col_idx = None
                    exchange_col_idx = None

                    for idx, header in enumerate(headers):
                        header_lower = header.lower()
                        if 'symbol' in header_lower:
                            symbol_col_idx = idx
                        elif 'name' in header_lower or 'company' in header_lower:
                            name_col_idx = idx
                        elif 'exchange' in header_lower or 'market' in header_lower:
                            exchange_col_idx = idx

                    logger.info(f"Column indices - Symbol: {symbol_col_idx}, Name: {name_col_idx}, Exchange: {exchange_col_idx}")

                    # Process data rows
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_all(['td', 'th'])

                        if len(cells) == 0:
                            continue

                        # Extract symbol
                        symbol = None
                        if symbol_col_idx is not None and symbol_col_idx < len(cells):
                            symbol_text = cells[symbol_col_idx].get_text().strip()
                            # Clean symbol (remove any whitespace, special chars)
                            symbol_clean = ''.join(filter(str.isdigit, symbol_text))
                            if symbol_clean and len(symbol_clean) == 4:
                                symbol = f"{symbol_clean}.SR"

                        # Extract company name
                        company_name = None
                        if name_col_idx is not None and name_col_idx < len(cells):
                            company_name = cells[name_col_idx].get_text().strip()

                        # Extract exchange
                        exchange = self.default_exchange  # Default to market being scraped
                        if exchange_col_idx is not None and exchange_col_idx < len(cells):
                            exchange_text = cells[exchange_col_idx].get_text().strip()
                            if 'nomu' in exchange_text.lower():
                                exchange = 'NOMU'
                            elif 'tadawul' in exchange_text.lower():
                                exchange = 'Tadawul'

                        # Add to results
                        if symbol and validate_symbol(symbol):
                            self.symbols_data.append({
                                'symbol': symbol,
                                'company_name': company_name,
                                'exchange': exchange
                            })
                            logger.debug(f"Found: {symbol} - {company_name} ({exchange})")

            logger.info(f"Scraping complete. Found {len(self.symbols_data)} symbols")

            return self.symbols_data

        except Exception as e:
            logger.error(f"Failed to scrape Argaam: {e}", exc_info=True)
            raise

    def save_symbols_to_file(self, filepath: str):
        """
        Save scraped symbols to a file.

        Args:
            filepath: Path to save symbols
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Tadawul & NOMU Stock Symbols\n")
                f.write(f"# Scraped from: {self.url}\n")
                f.write(f"# Total symbols: {len(self.symbols_data)}\n")
                f.write(f"# Format: SYMBOL | COMPANY_NAME | EXCHANGE\n")
                f.write("#\n")

                for data in sorted(self.symbols_data, key=lambda x: x['symbol']):
                    company_name = data.get('company_name', 'N/A')
                    exchange = data.get('exchange', 'Tadawul')
                    f.write(f"{data['symbol']}|{company_name}|{exchange}\n")

            logger.info(f"Symbols saved to {filepath}")
            logger.info(f"Total symbols saved: {len(self.symbols_data)}")

        except Exception as e:
            logger.error(f"Failed to save symbols to file: {e}")
            raise

    def get_symbol_count(self) -> int:
        """Get count of scraped symbols."""
        return len(self.symbols_data)

    def get_symbols_by_exchange(self) -> Dict[str, int]:
        """Get symbol count by exchange."""
        counts = {}
        for data in self.symbols_data:
            exchange = data.get('exchange', 'Tadawul')
            counts[exchange] = counts.get(exchange, 0) + 1
        return counts


def main():
    """
    Main function to run the scraper standalone.
    Scrapes both Tadawul and NOMU markets.
    """
    print("="*60)
    print("ARGAAM STOCK SYMBOL SCRAPER")
    print("="*60)
    print("\nScraping Argaam stock lists for both markets...")
    print()

    all_symbols_data = []

    # Scrape Tadawul (main market)
    print("TADAWUL MAIN MARKET")
    print("-" * 60)
    print("Source: https://www.argaam.com/en/company/companies-prices/3")
    try:
        tadawul_scraper = ArgaamScraper(market='tadawul')
        tadawul_symbols = tadawul_scraper.scrape_all_symbols()
        all_symbols_data.extend(tadawul_symbols)
        print(f"[OK] Tadawul: {len(tadawul_symbols)} symbols scraped")
    except Exception as e:
        print(f"X Tadawul scraping failed: {e}")
        logger.error(f"Tadawul scraping failed: {e}", exc_info=True)
        return 1

    print()

    # Scrape NOMU (parallel market)
    print("NOMU PARALLEL MARKET")
    print("-" * 60)
    print("Source: https://www.argaam.com/en/company/companies-prices/14")
    try:
        nomu_scraper = ArgaamScraper(market='nomu')
        nomu_symbols = nomu_scraper.scrape_all_symbols()
        all_symbols_data.extend(nomu_symbols)
        print(f"[OK] NOMU: {len(nomu_symbols)} symbols scraped")
    except Exception as e:
        print(f"X NOMU scraping failed: {e}")
        logger.error(f"NOMU scraping failed: {e}", exc_info=True)
        return 1

    print()
    print("="*60)
    print("COMBINED RESULTS")
    print("="*60)
    print(f"\nTotal symbols: {len(all_symbols_data)}")

    # Show breakdown by exchange
    exchange_counts = {}
    for data in all_symbols_data:
        exchange = data.get('exchange', 'Unknown')
        exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1

    print(f"\nBreakdown by exchange:")
    for exchange, count in sorted(exchange_counts.items()):
        print(f"  {exchange}: {count} stocks")

    if all_symbols_data:
        print(f"\nFirst 10 symbols:")
        for data in all_symbols_data[:10]:
            print(f"  {data['symbol']} - {data.get('company_name', 'N/A')} ({data.get('exchange', 'Unknown')})")

        print(f"\nLast 10 symbols:")
        for data in all_symbols_data[-10:]:
            print(f"  {data['symbol']} - {data.get('company_name', 'N/A')} ({data.get('exchange', 'Unknown')})")

    # Save combined file
    output_file = Path(__file__).parent.parent / 'data' / 'tadawul_symbols.txt'

    try:
        # Ensure directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Saudi Stock Market Symbols (Tadawul + NOMU)\n")
            f.write("# Tadawul Source: https://www.argaam.com/en/company/companies-prices/3\n")
            f.write("# NOMU Source: https://www.argaam.com/en/company/companies-prices/14\n")
            f.write(f"# Total symbols: {len(all_symbols_data)}\n")
            f.write(f"# Format: SYMBOL | COMPANY_NAME | EXCHANGE\n")
            f.write("#\n")

            for data in sorted(all_symbols_data, key=lambda x: x['symbol']):
                company_name = data.get('company_name', 'N/A')
                exchange = data.get('exchange', 'Unknown')
                f.write(f"{data['symbol']}|{company_name}|{exchange}\n")

        print(f"\n[OK] Combined symbols saved to: {output_file}")

    except Exception as e:
        print(f"\nX Failed to save symbols: {e}")
        logger.error(f"Failed to save symbols to file: {e}")
        return 1

    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)

    return 0


if __name__ == '__main__':
    from utils import setup_logger

    # Setup logging
    setup_logger('argaam_scraper', level='DEBUG')

    sys.exit(main())