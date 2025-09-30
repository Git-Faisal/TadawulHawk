"""
Test script for DataValidator.
Tests validation of collected stock data and database data.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from collectors.stock_collector import StockCollector
from validators.data_validator import DataValidator
from database.db_manager import DatabaseManager
from utils import setup_logger

# Setup logging
logger = setup_logger('test_validator', level='DEBUG')

print("="*70)
print("DATA VALIDATOR TEST")
print("="*70)
print("\nThis test will:")
print("  1. Collect data for Saudi Aramco (2222.SR)")
print("  2. Validate collected data")
print("  3. Validate database data")
print()

# Initialize
collector = StockCollector('2222.SR')
validator = DataValidator(tolerance_pct=2.0)
db_manager = DatabaseManager()

# Collect data
print("[1/3] Collecting data for 2222.SR...")
collected_data = collector.collect_all_data()

if not collected_data.get('stock_info'):
    print("[ERROR] Failed to collect stock data!")
    sys.exit(1)

print("[OK] Data collected")
print(f"  Company: {collected_data['stock_info'].get('company_name')}")
print(f"  Quarterly Records: {len(collected_data.get('quarterly_fundamentals', []))}")
print(f"  Annual Records: {len(collected_data.get('annual_fundamentals', []))}")

# Validate collected data
print("\n[2/3] Validating collected data...")
validation_result = validator.validate_collected_data('2222.SR', collected_data)

print(f"\nValidation Status: {'VALID [OK]' if validation_result.is_valid else 'INVALID [ERROR]'}")

if validation_result.errors:
    print(f"\nErrors ({len(validation_result.errors)}):")
    for error in validation_result.errors:
        print(f"  [X] {error}")

if validation_result.warnings:
    print(f"\nWarnings ({len(validation_result.warnings)}):")
    for warning in validation_result.warnings:
        print(f"  [!] {warning}")

if not validation_result.errors and not validation_result.warnings:
    print("\n[OK] No errors or warnings found!")

# Validate database data
print("\n[3/3] Validating database data...")
db_validation = validator.validate_database_data(db_manager, '2222.SR')

print(f"\nDatabase Validation Status: {'VALID [OK]' if db_validation.is_valid else 'INVALID [ERROR]'}")

if db_validation.errors:
    print(f"\nDatabase Errors ({len(db_validation.errors)}):")
    for error in db_validation.errors:
        print(f"  [X] {error}")

if db_validation.warnings:
    print(f"\nDatabase Warnings ({len(db_validation.warnings)}):")
    for warning in db_validation.warnings:
        print(f"  [!] {warning}")

if not db_validation.errors and not db_validation.warnings:
    print("\n[OK] No database errors or warnings found!")

print("\n" + "="*70)
print("DATA VALIDATOR TEST COMPLETE")
print("="*70)
print("\nSummary:")
print(f"  Collected Data: {'VALID [OK]' if validation_result.is_valid else 'INVALID [ERROR]'}")
print(f"  Database Data:  {'VALID [OK]' if db_validation.is_valid else 'INVALID [ERROR]'}")
print("\nCheck logs/app.log for detailed information")
