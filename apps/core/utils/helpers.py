"""
Helper utility functions.

This module provides common utility functions used across the application.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from django.utils import timezone
from django.core.cache import cache
from django.db.models import QuerySet


def generate_random_string(length: int = 32, include_digits: bool = True, include_special: bool = False) -> str:
    """
    Generate a random string of specified length.

    Args:
        length: Length of the string to generate
        include_digits: Whether to include digits
        include_special: Whether to include special characters

    Returns:
        Random string
    """
    characters = string.ascii_letters
    if include_digits:
        characters += string.digits
    if include_special:
        characters += string.punctuation

    return ''.join(random.choice(characters) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Args:
        length: Length of the token

    Returns:
        Secure random token
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))


def get_client_ip(request) -> str:
    """
    Get client IP address from request.

    Args:
        request: Django request object

    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def truncate_string(text: str, length: int = 100, suffix: str = '...') -> str:
    """
    Truncate a string to specified length with suffix.

    Args:
        text: String to truncate
        length: Maximum length
        suffix: Suffix to append if truncated

    Returns:
        Truncated string
    """
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Yield successive n-sized chunks from list.

    Args:
        lst: List to chunk
        n: Chunk size

    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_or_set_cache(key: str, callback, timeout: int = 300) -> Any:
    """
    Get value from cache or set it using callback.

    Args:
        key: Cache key
        callback: Function to call if cache miss
        timeout: Cache timeout in seconds

    Returns:
        Cached or fresh value
    """
    value = cache.get(key)
    if value is None:
        value = callback()
        cache.set(key, value, timeout)
    return value


def invalidate_cache(pattern: str):
    """
    Invalidate cache keys matching pattern.

    Args:
        pattern: Cache key pattern to match
    """
    cache.delete_pattern(pattern)


def queryset_to_dict(queryset: QuerySet, key_field: str = 'id', value_field: Optional[str] = None) -> Dict:
    """
    Convert queryset to dictionary.

    Args:
        queryset: Django queryset
        key_field: Field to use as dictionary key
        value_field: Field to use as dictionary value (if None, uses entire object)

    Returns:
        Dictionary representation of queryset
    """
    if value_field:
        return {getattr(obj, key_field): getattr(obj, value_field) for obj in queryset}
    return {getattr(obj, key_field): obj for obj in queryset}


def get_date_range(days: int = 7, end_date: Optional[datetime] = None) -> tuple:
    """
    Get date range for specified number of days.

    Args:
        days: Number of days in range
        end_date: End date (defaults to now)

    Returns:
        Tuple of (start_date, end_date)
    """
    if end_date is None:
        end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default on division by zero.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero

    Returns:
        Division result or default
    """
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return default


def percentage(part: float, whole: float, decimals: int = 2) -> float:
    """
    Calculate percentage.

    Args:
        part: Part value
        whole: Whole value
        decimals: Number of decimal places

    Returns:
        Percentage value
    """
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, decimals)
