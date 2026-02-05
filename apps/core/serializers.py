"""
Base serializers for the API.

This module provides base serializer classes with common functionality
for all API serializers.
"""

from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for models with common fields.

    Provides read-only timestamp fields and consistent field ordering.
    """

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True
        read_only_fields = ('id', 'created_at', 'updated_at')


class WriteableModelSerializer(BaseModelSerializer):
    """
    Base serializer for write operations.

    Separates write and read operations for better control over
    data validation and serialization.
    """

    class Meta(BaseModelSerializer.Meta):
        abstract = True

    def to_representation(self, instance):
        """
        Use a read serializer for output if available.

        Override this method in subclasses to specify a read_serializer_class.
        """
        if hasattr(self.Meta, 'read_serializer_class'):
            return self.Meta.read_serializer_class(instance, context=self.context).data
        return super().to_representation(instance)


class EmptySerializer(serializers.Serializer):
    """
    Empty serializer for actions that don't require input.
    """

    pass
