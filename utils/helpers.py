"""
Helper utility functions for Tadawul Stock Collector.
"""

import re
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd


def format_currency(amount: Optional[float], currency: str = 'SAR', decimals: int = 2) -> str:
    """
    Format a number as currency.

    Args:
        amount: The amount to format
        currency: Currency code (default: SAR)
        decimals: Number of decimal places

    Returns:
        Formatted currency string
    """
    if amount is None:
        return 'N/A'

    return f"{amount:,.{decimals}f} {currency}"


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """
    Format a number as percentage.

    Args:
        value: The value to format (e.g., 0.15 for 15%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    if value is None:
        return 'N/A'

    return f"{value * 100:.{decimals}f}%"


def calculate_percentage_change(old_value: Optional[float], new_value: Optional[float]) -> Optional[float]:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Original value
        new_value: New value

    Returns:
        Percentage change as decimal (e.g., 0.15 for 15% increase)
        None if either value is None or old_value is 0
    """
    if old_value is None or new_value is None or old_value == 0:
        return None

    return (new_value - old_value) / old_value


def get_trading_day(reference_date: datetime, days_ago: int) -> datetime:
    """
    Get a trading day (approximate) by going back N calendar days.
    This is a simple approximation - doesn't account for actual market holidays.

    For more accurate results, you would need a calendar of actual trading days.
    For our purposes, we subtract days and let yfinance handle finding the nearest trading day.

    Args:
        reference_date: The reference date (usually today)
        days_ago: Number of days to go back (e.g., 30 for 1 month)

    Returns:
        datetime object for the approximate trading day
    """
    target_date = reference_date - timedelta(days=days_ago)
    return target_date


def validate_symbol(symbol: str) -> bool:
    """
    Validate that a stock symbol is in the correct format for Tadawul (.SR suffix).

    Args:
        symbol: Stock symbol to validate

    Returns:
        True if valid, False otherwise
    """
    if not symbol:
        return False

    # Check if symbol ends with .SR
    if not symbol.endswith('.SR'):
        return False

    # Check if the part before .SR is numeric (Tadawul symbols are numeric)
    base_symbol = symbol[:-3]  # Remove .SR
    if not base_symbol.isdigit():
        return False

    # Valid symbol
    return True


def normalize_symbol(symbol: str) -> Optional[str]:
    """
    Normalize a stock symbol to the correct format.
    Adds .SR suffix if missing.

    Args:
        symbol: Stock symbol to normalize

    Returns:
        Normalized symbol or None if invalid
    """
    if not symbol:
        return None

    # Strip whitespace
    symbol = symbol.strip().upper()

    # If already has .SR suffix, validate and return
    if symbol.endswith('.SR'):
        return symbol if validate_symbol(symbol) else None

    # Try to add .SR suffix
    potential_symbol = f"{symbol}.SR"
    return potential_symbol if validate_symbol(potential_symbol) else None


def safe_float(value, default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert a value to float, returning default if conversion fails.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: Optional[int] = None) -> Optional[int]:
    """
    Safely convert a value to int, returning default if conversion fails.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def chunks(lst: list, n: int):
    """
    Yield successive n-sized chunks from lst.

    Args:
        lst: List to chunk
        n: Chunk size

    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def format_date(date_obj: Optional[datetime], format_str: str = '%Y-%m-%d') -> Optional[str]:
    """
    Format a datetime object as a string.

    Args:
        date_obj: Datetime object to format
        format_str: Format string (default: ISO 8601 date)

    Returns:
        Formatted date string or None
    """
    if date_obj is None:
        return None

    if isinstance(date_obj, str):
        return date_obj

    return date_obj.strftime(format_str)