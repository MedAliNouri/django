"""
Global pytest fixtures.

This module provides fixtures available to all tests.
"""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def disable_signals():
    """Disable Django signals for tests."""
    from django.db.models import signals
    from django.dispatch import Signal

    # Store original signal receivers
    original_receivers = {}
    for signal in [signals.post_save, signals.pre_save, signals.post_delete, signals.pre_delete]:
        original_receivers[signal] = signal.receivers
        signal.receivers = []

    yield

    # Restore original receivers
    for signal, receivers in original_receivers.items():
        signal.receivers = receivers


@pytest.fixture
def mock_celery():
    """Mock Celery tasks for tests."""
    from unittest.mock import patch

    with patch('celery.app.task.Task.apply_async') as mock:
        yield mock
