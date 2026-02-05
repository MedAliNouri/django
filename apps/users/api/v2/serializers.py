"""
API v2 serializers for User endpoints.

This module contains serializers for the User API v2.
In v2, we might have enhanced features or different response formats.
"""

from apps.users.api.v1.serializers import *


# V2 might have enhanced serializers with additional fields
# or different validation logic

class UserDetailSerializerV2(UserDetailSerializer):
    """
    Enhanced User detail serializer for V2.

    Could include additional computed fields, relationships, etc.
    """
    pass
