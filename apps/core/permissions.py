"""
Custom permission classes for the API.

This module provides reusable permission classes for fine-grained
access control.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access it.

    Assumes the model has a 'user' or 'owner' field.
    """

    def has_object_permission(self, request, view, obj):
        """Check if the user is the owner of the object."""
        # Check for common owner field names
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to everyone,
    but write access only to the owner.
    """

    def has_object_permission(self, request, view, obj):
        """Check permissions for object-level access."""
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to everyone,
    but write access only to admin users.
    """

    def has_permission(self, request, view):
        """Check permissions for the request."""
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for admin users
        return request.user and request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users to access.
    """

    def has_permission(self, request, view):
        """Check if user is admin."""
        return request.user and request.user.is_staff


class IsSuperUser(permissions.BasePermission):
    """
    Permission to only allow superusers to access.
    """

    def has_permission(self, request, view):
        """Check if user is superuser."""
        return request.user and request.user.is_superuser


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to everyone,
    but write access only to authenticated users.
    """

    def has_permission(self, request, view):
        """Check permissions for the request."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
