"""
Logging configuration for Tadawul Stock Collector.
Provides rotating file handlers and console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import Config


def setup_logger(name='tadawul_collector', level=None):
    """
    Set up and configure logger with both file and console handlers.

    Args:
        name: Logger name
        level: Logging level (defaults to Config.LOG_LEVEL)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Set level
    log_level = level or Config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ============================================
    # Console Handler (INFO and above)
    # ============================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # ============================================
    # Main Log File Handler (all levels)
    # ============================================
    main_log_file = Config.LOG_FILE_PATH / 'app.log'
    file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # ============================================
    # Error Log File Handler (ERROR and above)
    # ============================================
    error_log_file = Config.LOG_FILE_PATH / 'errors.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # Log initial setup message
    logger.debug(f"Logger '{name}' initialized with level {log_level}")

    return logger


def get_logger(name='tadawul_collector'):
    """
    Get an existing logger or create a new one.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)

    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        return setup_logger(name)

    return logger


# Create a module-level logger for utilities
_logger = setup_logger('tadawul_collector.utils')