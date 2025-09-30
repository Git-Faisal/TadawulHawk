"""
Configuration management for Tadawul Stock Collector.
Loads settings from environment variables using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """
    Configuration class that holds all application settings.
    Settings are loaded from environment variables with sensible defaults.
    """

    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'tadawul_stocks')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    @classmethod
    def get_database_url(cls):
        """
        Returns the PostgreSQL connection URL.
        Format: postgresql://user:password@host:port/database
        """
        return (
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )

    # ============================================
    # API CONFIGURATION
    # ============================================
    API_RATE_LIMIT_DELAY = float(os.getenv('API_RATE_LIMIT_DELAY', 0.5))
    API_MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', 3))
    API_BATCH_DELAY = float(os.getenv('API_BATCH_DELAY', 5.0))
    API_BATCH_SIZE = int(os.getenv('API_BATCH_SIZE', 50))

    # ============================================
    # EXPORT CONFIGURATION
    # ============================================
    EXPORT_JSON_PATH = Path(os.getenv('EXPORT_JSON_PATH', './exports/json/'))
    EXPORT_CSV_PATH = Path(os.getenv('EXPORT_CSV_PATH', './exports/csv/'))

    @classmethod
    def ensure_export_directories(cls):
        """Create export directories if they don't exist."""
        cls.EXPORT_JSON_PATH.mkdir(parents=True, exist_ok=True)
        cls.EXPORT_CSV_PATH.mkdir(parents=True, exist_ok=True)

    # ============================================
    # LOGGING CONFIGURATION
    # ============================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = Path(os.getenv('LOG_FILE_PATH', './logs/'))
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

    @classmethod
    def ensure_log_directory(cls):
        """Create log directory if it doesn't exist."""
        cls.LOG_FILE_PATH.mkdir(parents=True, exist_ok=True)

    # ============================================
    # DATA COLLECTION CONFIGURATION
    # ============================================
    HISTORICAL_YEARS = int(os.getenv('HISTORICAL_YEARS', 5))
    TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
    TEST_SYMBOLS = os.getenv('TEST_SYMBOLS', '2222.SR,1120.SR,7010.SR').split(',')

    # ============================================
    # VALIDATION
    # ============================================
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present.
        Raises ValueError if any required config is missing.
        """
        errors = []

        # Check required database fields
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD is not set")

        if not cls.DB_NAME:
            errors.append("DB_NAME is not set")

        if not cls.DB_USER:
            errors.append("DB_USER is not set")

        # Check that numeric values are reasonable
        if cls.API_RATE_LIMIT_DELAY < 0:
            errors.append("API_RATE_LIMIT_DELAY must be non-negative")

        if cls.API_MAX_RETRIES < 1:
            errors.append("API_MAX_RETRIES must be at least 1")

        if cls.HISTORICAL_YEARS < 1 or cls.HISTORICAL_YEARS > 10:
            errors.append("HISTORICAL_YEARS must be between 1 and 10")

        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    @classmethod
    def display_config(cls):
        """Display current configuration (without sensitive data)."""
        print("\n" + "="*60)
        print("TADAWUL STOCK COLLECTOR - CONFIGURATION")
        print("="*60)
        print(f"Database: {cls.DB_USER}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        print(f"API Rate Limit: {cls.API_RATE_LIMIT_DELAY}s delay, {cls.API_MAX_RETRIES} retries")
        print(f"Historical Data: {cls.HISTORICAL_YEARS} years")
        print(f"Test Mode: {cls.TEST_MODE}")
        if cls.TEST_MODE:
            print(f"Test Symbols: {', '.join(cls.TEST_SYMBOLS)}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"Exports: JSON={cls.EXPORT_JSON_PATH}, CSV={cls.EXPORT_CSV_PATH}")
        print("="*60 + "\n")


# Initialize directories on module import
Config.ensure_export_directories()
Config.ensure_log_directory()