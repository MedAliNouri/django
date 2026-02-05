"""
Custom type hints for the application.

This module provides type aliases and custom types for better type safety.
"""

from typing import Any, Optional, TypeVar

from django.db.models import Model, QuerySet

# Generic model type
ModelType = TypeVar('ModelType', bound=Model)

# Common type aliases
JSONDict = dict[str, Any]
JSONList = list[JSONDict]
OptionalStr = Optional[str]
OptionalInt = Optional[int]

# QuerySet type
QuerySetType = TypeVar('QuerySetType', bound=QuerySet)
