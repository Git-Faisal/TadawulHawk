"""
Test script for SymbolProvider to explore yfinance capabilities.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from collectors.symbol_provider import SymbolProvider
from utils import setup_logger

# Setup logging
logger = setup_logger('test_symbol_provider', level='DEBUG')

print("="*60)
print("SYMBOL PROVIDER TEST")
print("="*60)

# Initialize provider
provider = SymbolProvider()

# Get all symbols
print("\nFetching Tadawul symbols...")
symbols = provider.get_all_symbols()

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"Total symbols found: {len(symbols)}")

if symbols:
    print(f"\nFirst 10 symbols:")
    for symbol in symbols[:10]:
        print(f"  - {symbol}")

    print(f"\nLast 10 symbols:")
    for symbol in symbols[-10:]:
        print(f"  - {symbol}")

    # Validate a sample
    print("\n" + "="*60)
    print("VALIDATION TEST")
    print("="*60)
    results = provider.validate_sample(sample_size=5)
    print(f"Valid: {results['valid']}/{results['total_sampled']}")
    print(f"Success rate: {results['success_rate']:.1f}%")

print("\n" + "="*60)
print("Check logs/app.log for detailed information")
print("="*60)