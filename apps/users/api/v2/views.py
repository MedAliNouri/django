"""
API v2 views for User endpoints.

This module contains viewsets for the User API v2.
V2 might have enhanced features or different behavior.
"""

from apps.users.api.v1.views import UserViewSet as UserViewSetV1
from .serializers import UserDetailSerializerV2


class UserViewSet(UserViewSetV1):
    """
    V2 of UserViewSet with potential enhancements.

    Currently inherits from V1 but could be extended with new features.
    """

    # Override serializers for V2 if needed
    serializer_classes = {
        **UserViewSetV1.serializer_classes,
        'retrieve': UserDetailSerializerV2,
    }
