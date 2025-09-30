"""
Tadawul Stock Symbol Scraper for Tadawul Hawk.
Scrapes the official Saudi Exchange (Tadawul) issuer directory to get complete stock list.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Set, List
from utils import get_logger, validate_symbol

logger = get_logger(__name__)


class TadawulScraper:
    """
    Scrapes Saudi Exchange (Tadawul) website to get complete list of stock symbols.
    """

    def __init__(self):
        self.base_url = "https://www.saudiexchange.sa"
        self.issuer_directory_url = f"{self.base_url}/wps/portal/saudiexchange/trading/participants-directory/issuer-directory"
        self.symbols: Set[str] = set()
        self.session = requests.Session()
        # Use more realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        logger.info("TadawulScraper initialized")

    def scrape_all_symbols(self) -> List[str]:
        """
        Scrape all stock symbols from Tadawul issuer directory.

        Returns:
            List of stock symbols in .SR format
        """
        logger.info(f"Starting to scrape Tadawul issuer directory...")
        logger.info(f"URL: {self.issuer_directory_url}")

        try:
            # Fetch the main page
            response = self.session.get(self.issuer_directory_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Log the page structure for debugging
            logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")

            # Try multiple strategies to extract stock symbols
            self._extract_symbols_strategy_1(soup)  # Look for tables
            self._extract_symbols_strategy_2(soup)  # Look for specific divs/sections
            self._extract_symbols_strategy_3(soup)  # Look for ticker patterns in text

            # Try to find and follow pagination links
            self._follow_pagination_links(soup)

            logger.info(f"Scraping complete. Found {len(self.symbols)} unique symbols")

            # Convert to sorted list
            symbol_list = sorted(list(self.symbols))

            return symbol_list

        except Exception as e:
            logger.error(f"Failed to scrape Tadawul website: {e}")
            raise

    def _extract_symbols_strategy_1(self, soup: BeautifulSoup):
        """Strategy 1: Look for data in HTML tables."""
        logger.debug("Trying strategy 1: Extracting from tables...")

        tables = soup.find_all('table')
        logger.debug(f"Found {len(tables)} tables")

        for idx, table in enumerate(tables):
            rows = table.find_all('tr')
            logger.debug(f"Table {idx}: {len(rows)} rows")

            for row in rows:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text().strip()

                    # Look for 4-digit codes (Tadawul symbols are typically 4 digits)
                    matches = re.findall(r'\b(\d{4})\b', text)
                    for match in matches:
                        symbol = f"{match}.SR"
                        if validate_symbol(symbol):
                            self.symbols.add(symbol)
                            logger.debug(f"Found symbol (table): {symbol}")

    def _extract_symbols_strategy_2(self, soup: BeautifulSoup):
        """Strategy 2: Look for specific div/section structures."""
        logger.debug("Trying strategy 2: Extracting from divs/sections...")

        # Look for common div classes that might contain company listings
        potential_containers = soup.find_all(['div', 'section', 'article'])

        for container in potential_containers:
            # Get all text from container
            text = container.get_text()

            # Look for 4-digit ticker patterns
            matches = re.findall(r'\b(\d{4})\b', text)
            for match in matches:
                symbol = f"{match}.SR"
                if validate_symbol(symbol):
                    self.symbols.add(symbol)
                    logger.debug(f"Found symbol (div): {symbol}")

    def _extract_symbols_strategy_3(self, soup: BeautifulSoup):
        """Strategy 3: Look for ticker patterns anywhere in text."""
        logger.debug("Trying strategy 3: Pattern matching in all text...")

        # Get all text from page
        page_text = soup.get_text()

        # Find all 4-digit numbers (potential tickers)
        matches = re.findall(r'\b(\d{4})\b', page_text)

        # Filter to reasonable range for Tadawul symbols
        # Tadawul symbols typically range from 1000-9999
        for match in matches:
            ticker_num = int(match)
            if 1000 <= ticker_num <= 9999:
                symbol = f"{match}.SR"
                if validate_symbol(symbol):
                    self.symbols.add(symbol)
                    logger.debug(f"Found symbol (pattern): {symbol}")

    def _follow_pagination_links(self, soup: BeautifulSoup):
        """Try to find and follow pagination links."""
        logger.debug("Looking for pagination...")

        # Look for common pagination patterns
        pagination_links = []

        # Strategy 1: Look for "next" buttons/links
        next_links = soup.find_all(['a', 'button'], text=re.compile(r'next|Next|NEXT|›|»', re.I))
        pagination_links.extend(next_links)

        # Strategy 2: Look for numbered page links
        page_links = soup.find_all('a', text=re.compile(r'^\d+$'))
        pagination_links.extend(page_links)

        # Strategy 3: Look for common pagination class names
        pagination_divs = soup.find_all(['div', 'nav'], class_=re.compile(r'pag', re.I))
        for div in pagination_divs:
            links = div.find_all('a')
            pagination_links.extend(links)

        logger.debug(f"Found {len(pagination_links)} potential pagination links")

        # Try to follow pagination links (limit to avoid infinite loops)
        max_pages = 20
        pages_visited = 1

        for link in pagination_links[:max_pages]:
            href = link.get('href')
            if not href:
                continue

            # Make absolute URL
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = f"{self.base_url}{href}"
            else:
                url = f"{self.issuer_directory_url}/{href}"

            try:
                logger.debug(f"Following pagination link: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'lxml')

                # Extract symbols from this page
                self._extract_symbols_strategy_1(soup)
                self._extract_symbols_strategy_2(soup)

                pages_visited += 1
                time.sleep(1)  # Be polite, wait between requests

                if pages_visited >= max_pages:
                    logger.warning(f"Reached max pages limit ({max_pages})")
                    break

            except Exception as e:
                logger.warning(f"Failed to fetch pagination page {url}: {e}")
                continue

    def save_symbols_to_file(self, filepath: str):
        """
        Save scraped symbols to a file.

        Args:
            filepath: Path to save symbols
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w') as f:
                f.write("# Tadawul Stock Symbols\n")
                f.write(f"# Scraped from: {self.issuer_directory_url}\n")
                f.write(f"# Total symbols: {len(self.symbols)}\n")
                f.write(f"# Format: XXXX.SR (where XXXX is the 4-digit ticker)\n")
                f.write("#\n")

                for symbol in sorted(self.symbols):
                    f.write(f"{symbol}\n")

            logger.info(f"Symbols saved to {filepath}")
            logger.info(f"Total symbols saved: {len(self.symbols)}")

        except Exception as e:
            logger.error(f"Failed to save symbols to file: {e}")
            raise

    def get_symbol_count(self) -> int:
        """Get count of scraped symbols."""
        return len(self.symbols)


def main():
    """
    Main function to run the scraper standalone.
    """
    print("="*60)
    print("TADAWUL STOCK SYMBOL SCRAPER")
    print("="*60)
    print("\nScraping Saudi Exchange (Tadawul) issuer directory...")
    print("This may take a few minutes...\n")

    scraper = TadawulScraper()

    try:
        # Scrape all symbols
        symbols = scraper.scrape_all_symbols()

        print(f"\n✓ Successfully scraped {len(symbols)} symbols")

        if symbols:
            print(f"\nFirst 10 symbols:")
            for symbol in symbols[:10]:
                print(f"  - {symbol}")

            print(f"\nLast 10 symbols:")
            for symbol in symbols[-10:]:
                print(f"  - {symbol}")

        # Save to file
        output_file = Path(__file__).parent.parent / 'data' / 'tadawul_symbols.txt'
        scraper.save_symbols_to_file(str(output_file))

        print(f"\n✓ Symbols saved to: {output_file}")
        print("\n" + "="*60)
        print("SCRAPING COMPLETE")
        print("="*60)

    except Exception as e:
        print(f"\nX Scraping failed: {e}")
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    from utils import setup_logger

    # Setup logging
    setup_logger('tadawul_scraper', level='DEBUG')

    sys.exit(main())