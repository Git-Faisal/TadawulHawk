"""
Simple database migration script to recreate tables with new schema.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from utils import setup_logger

logger = setup_logger('migrate_db', level='INFO')

print("="*70)
print("DATABASE MIGRATION")
print("="*70)
print("\nThis will drop all existing tables and recreate them with the new schema.")
print("WARNING: All existing data will be lost!")
print()

response = input("Type 'YES' to confirm: ")
if response != 'YES':
    print("Migration cancelled.")
    sys.exit(0)

print("\n[1/2] Dropping all existing tables...")
db_manager = DatabaseManager()
db_manager.drop_tables()
print("[OK] Tables dropped")

print("\n[2/2] Creating tables with new schema...")
db_manager.create_tables()
print("[OK] Tables created")

print("\n" + "="*70)
print("MIGRATION COMPLETE")
print("="*70)
print("\nDatabase has been recreated with the new schema including 'exchange' field.")
