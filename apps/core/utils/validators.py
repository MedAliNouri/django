"""
Custom validators for data validation.

This module provides reusable validator functions for common validation needs.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value):
    """
    Validate phone number format.

    Accepts formats like: +1234567890, +1-234-567-8900, (123) 456-7890
    """
    phone_regex = re.compile(r'^\+?1?\d{9,15}$')
    if not phone_regex.match(value.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')):
        raise ValidationError(
            _('Invalid phone number format. Use format: +1234567890'),
            code='invalid_phone'
        )


def validate_alphanumeric(value):
    """
    Validate that value contains only alphanumeric characters.
    """
    if not value.isalnum():
        raise ValidationError(
            _('Value must contain only alphanumeric characters.'),
            code='invalid_alphanumeric'
        )


def validate_no_special_chars(value):
    """
    Validate that value contains no special characters.
    """
    pattern = re.compile(r'^[a-zA-Z0-9\s]+$')
    if not pattern.match(value):
        raise ValidationError(
            _('Value must not contain special characters.'),
            code='invalid_special_chars'
        )


def validate_min_words(min_words):
    """
    Validator factory for minimum word count.
    """
    def validator(value):
        word_count = len(value.split())
        if word_count < min_words:
            raise ValidationError(
                _(f'Value must contain at least {min_words} words.'),
                code='min_words'
            )
    return validator


def validate_max_words(max_words):
    """
    Validator factory for maximum word count.
    """
    def validator(value):
        word_count = len(value.split())
        if word_count > max_words:
            raise ValidationError(
                _(f'Value must not exceed {max_words} words.'),
                code='max_words'
            )
    return validator


def validate_file_size(max_size_mb):
    """
    Validator factory for file size.

    Args:
        max_size_mb: Maximum file size in megabytes
    """
    def validator(file):
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            raise ValidationError(
                _(f'File size must not exceed {max_size_mb}MB.'),
                code='file_too_large'
            )
    return validator


def validate_file_extension(allowed_extensions):
    """
    Validator factory for file extensions.

    Args:
        allowed_extensions: List of allowed file extensions (e.g., ['pdf', 'doc', 'docx'])
    """
    def validator(file):
        ext = file.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise ValidationError(
                _(f'File extension must be one of: {", ".join(allowed_extensions)}'),
                code='invalid_extension'
            )
    return validator
