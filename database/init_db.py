"""
Database Initialization Script for Tadawul Hawk.
Creates database and tables, handles schema setup.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from database.db_manager import DatabaseManager
from utils import get_logger
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = get_logger(__name__)


def database_exists(db_name: str) -> bool:
    """
    Check if a PostgreSQL database exists.

    Args:
        db_name: Database name

    Returns:
        True if database exists, False otherwise
    """
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        return exists
    except Exception as e:
        logger.error(f"Error checking if database exists: {e}")
        return False


def create_database(db_name: str):
    """
    Create a PostgreSQL database.

    Args:
        db_name: Database name
    """
    try:
        logger.info(f"Creating database '{db_name}'...")

        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute(f'CREATE DATABASE {db_name}')

        cursor.close()
        conn.close()

        logger.info(f"Database '{db_name}' created successfully")
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


def drop_database(db_name: str):
    """
    Drop a PostgreSQL database (use with caution!).

    Args:
        db_name: Database name
    """
    try:
        logger.warning(f"Dropping database '{db_name}'...")

        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Terminate existing connections to the database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid()
        """)

        cursor.execute(f'DROP DATABASE IF EXISTS {db_name}')

        cursor.close()
        conn.close()

        logger.warning(f"Database '{db_name}' dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database: {e}")
        raise


def init_database(reset: bool = False):
    """
    Initialize the Tadawul Hawk database.
    Creates database if it doesn't exist and sets up schema.

    Args:
        reset: If True, drop and recreate database (CAUTION: data loss!)
    """
    db_name = Config.DB_NAME

    print("="*60)
    print("TADAWUL HAWK - DATABASE INITIALIZATION")
    print("="*60)
    print(f"Database: {db_name}")
    print(f"Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"User: {Config.DB_USER}")
    print("="*60)

    try:
        # Step 1: Check if database exists
        exists = database_exists(db_name)

        if reset and exists:
            # Drop existing database
            confirmation = input(f"\n⚠️  WARNING: This will DELETE all data in '{db_name}'!\nType 'YES' to confirm: ")
            if confirmation == 'YES':
                drop_database(db_name)
                exists = False
                print("✓ Database dropped")
            else:
                print("✗ Reset cancelled")
                return

        # Step 2: Create database if it doesn't exist
        if not exists:
            create_database(db_name)
            print(f"✓ Database '{db_name}' created")
        else:
            print(f"✓ Database '{db_name}' already exists")

        # Step 3: Create tables using SQLAlchemy
        print("\nCreating database tables...")
        db_manager = DatabaseManager()

        if reset:
            db_manager.drop_tables()
            print("✓ Existing tables dropped")

        db_manager.create_tables()
        print("✓ Tables created successfully")

        # Step 4: Test connection
        print("\nTesting database connection...")
        if db_manager.test_connection():
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
            return

        # Step 5: Display summary
        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print("\nDatabase Schema:")
        print("  - stocks (stock metadata)")
        print("  - price_history (price data)")
        print("  - quarterly_fundamentals (quarterly financials)")
        print("  - annual_fundamentals (annual financials)")
        print("  - data_collection_log (audit trail)")
        print("\nNext Steps:")
        print("  1. Run data collection: python tadawul_collector.py --test")
        print("  2. View logs: tail -f logs/app.log")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


def verify_schema():
    """Verify that all tables exist and have correct structure."""
    print("="*60)
    print("SCHEMA VERIFICATION")
    print("="*60)

    try:
        db_manager = DatabaseManager()

        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()

        print("\nExisting Tables:")
        for table in tables:
            print(f"  ✓ {table[0]}")

            # Get column count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = '{table[0]}'
            """)
            column_count = cursor.fetchone()[0]
            print(f"    ({column_count} columns)")

        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print(f"Total Tables: {len(tables)}")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        logger.error(f"Schema verification failed: {e}")


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(
        description='Tadawul Hawk Database Initialization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python init_db.py                 # Initialize database (safe, preserves data)
  python init_db.py --reset         # Reset database (WARNING: deletes all data)
  python init_db.py --verify        # Verify schema
  python init_db.py --config        # Show configuration
        """
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop and recreate database (WARNING: deletes all data)'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify database schema'
    )

    parser.add_argument(
        '--config',
        action='store_true',
        help='Display configuration'
    )

    args = parser.parse_args()

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n✗ Configuration Error:\n{e}\n")
        print("Please check your .env file and ensure all required settings are configured.")
        sys.exit(1)

    # Execute requested action
    if args.config:
        Config.display_config()
    elif args.verify:
        verify_schema()
    else:
        init_database(reset=args.reset)


if __name__ == '__main__':
    main()