"""
Test script for Data Exporters.
Tests JSON and CSV export functionality.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from exporters.json_exporter import JSONExporter
from exporters.csv_exporter import CSVExporter
from database.db_manager import DatabaseManager
from utils import setup_logger

# Setup logging
logger = setup_logger('test_exporters', level='INFO')

print("="*70)
print("DATA EXPORTERS TEST")
print("="*70)
print("\nThis test will:")
print("  1. Export Saudi Aramco (2222.SR) to JSON")
print("  2. Export all stocks to CSV (4 files)")
print("  3. Verify exported files exist")
print()

# Initialize
db_manager = DatabaseManager()
json_exporter = JSONExporter(output_dir='exports')
csv_exporter = CSVExporter(output_dir='exports')

# Test JSON export
print("[1/3] Testing JSON export for 2222.SR...")
try:
    json_path = json_exporter.export_from_database(db_manager, '2222.SR')
    print(f"[OK] JSON exported to: {json_path}")

    # Check file size
    file_size = Path(json_path).stat().st_size
    print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

except Exception as e:
    print(f"[ERROR] JSON export failed: {e}")
    logger.error("JSON export failed", exc_info=True)

# Test CSV export
print("\n[2/3] Testing CSV export (4 files)...")
try:
    csv_paths = csv_exporter.export_all(db_manager)

    print("[OK] CSV files exported:")
    for name, path in csv_paths.items():
        file_size = Path(path).stat().st_size
        print(f"  {name}: {path}")
        print(f"    Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

except Exception as e:
    print(f"[ERROR] CSV export failed: {e}")
    logger.error("CSV export failed", exc_info=True)

# Verify files
print("\n[3/3] Verifying exported files...")
exports_dir = Path('exports')

if not exports_dir.exists():
    print("[ERROR] Exports directory not found!")
else:
    files = list(exports_dir.glob('*'))
    print(f"[OK] Found {len(files)} files in exports directory:")
    for file in files:
        print(f"  - {file.name} ({file.stat().st_size:,} bytes)")

print("\n" + "="*70)
print("DATA EXPORTERS TEST COMPLETE")
print("="*70)
print("\nExported files are in the 'exports' directory")
print("You can open CSV files in Excel to verify the data")
