"""
API v1 views for User endpoints.

This module contains viewsets for the User API v1.
Views are thin orchestrators that call services and selectors.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.views import BaseModelViewSet
from apps.core.permissions import IsOwner
from apps.users.models import User
from apps.users import selectors, services
from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    UserStatsSerializer,
)


class UserFilter(filters.FilterSet):
    """
    Filter class for User queryset.
    """

    email = filters.CharFilter(lookup_expr='icontains')
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_verified = filters.BooleanFilter()
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_verified',
            'created_after',
            'created_before',
        ]


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Get a paginated list of users with optional filters",
        tags=["Users"]
    ),
    retrieve=extend_schema(
        summary="Get user details",
        description="Retrieve detailed information about a specific user",
        tags=["Users"]
    ),
    create=extend_schema(
        summary="Create user",
        description="Register a new user account",
        tags=["Users"]
    ),
    update=extend_schema(
        summary="Update user",
        description="Update user information (full update)",
        tags=["Users"]
    ),
    partial_update=extend_schema(
        summary="Partially update user",
        description="Update specific user fields",
        tags=["Users"]
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Soft delete a user account",
        tags=["Users"]
    ),
)
class UserViewSet(BaseModelViewSet):
    """
    ViewSet for User CRUD operations.

    Provides standard CRUD endpoints plus custom actions.
    """

    queryset = User.objects.all()
    filterset_class = UserFilter
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']

    # Per-action serializers
    serializer_classes = {
        'list': UserListSerializer,
        'retrieve': UserDetailSerializer,
        'create': UserCreateSerializer,
        'update': UserUpdateSerializer,
        'partial_update': UserUpdateSerializer,
    }

    # Per-action permissions
    permission_classes_by_action = {
        'create': [AllowAny],
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'update': [IsOwner],
        'partial_update': [IsOwner],
        'destroy': [IsOwner],
    }

    def get_queryset(self):
        """
        Get queryset using selector.
        """
        # Use selector for read operations
        is_active = self.request.query_params.get('is_active')
        is_verified = self.request.query_params.get('is_verified')
        search = self.request.query_params.get('search')

        if is_active is not None:
            is_active = is_active.lower() == 'true'
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'

        return selectors.get_user_list(
            is_active=is_active,
            is_verified=is_verified,
            search=search
        )

    @extend_schema(
        summary="Get current user",
        description="Get the currently authenticated user's information",
        responses={200: UserDetailSerializer},
        tags=["Users"]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user's information.
        """
        serializer = UserDetailSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        })

    @extend_schema(
        summary="Update current user's profile",
        description="Update the currently authenticated user's profile information",
        request=UserProfileUpdateSerializer,
        responses={200: UserDetailSerializer},
        tags=["Users"]
    )
    @action(
        detail=False,
        methods=['patch'],
        permission_classes=[IsAuthenticated],
        url_path='me/profile'
    )
    def update_my_profile(self, request):
        """
        Update current user's profile.
        """
        profile = selectors.get_user_profile(request.user)
        serializer = UserProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return updated user
        user_serializer = UserDetailSerializer(request.user)
        return Response({
            'success': True,
            'data': user_serializer.data,
            'meta': {}
        })

    @extend_schema(
        summary="Change password",
        description="Change the current user's password",
        request=ChangePasswordSerializer,
        responses={200: None},
        tags=["Users"]
    )
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='me/change-password'
    )
    def change_password(self, request):
        """
        Change current user's password.
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'data': {'message': 'Password changed successfully'},
            'meta': {}
        })

    @extend_schema(
        summary="Deactivate account",
        description="Deactivate the current user's account",
        responses={200: None},
        tags=["Users"]
    )
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='me/deactivate'
    )
    def deactivate_account(self, request):
        """
        Deactivate current user's account.
        """
        services.UserService.deactivate_user(request.user)

        return Response({
            'success': True,
            'data': {'message': 'Account deactivated successfully'},
            'meta': {}
        })

    @extend_schema(
        summary="Get user statistics",
        description="Get aggregate statistics about all users",
        responses={200: UserStatsSerializer},
        tags=["Users"]
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='stats'
    )
    def stats(self, request):
        """
        Get user statistics.
        """
        stats = selectors.get_user_stats()
        serializer = UserStatsSerializer(stats)

        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        })

    def perform_destroy(self, instance):
        """
        Soft delete user using service.
        """
        services.UserService.delete_user(instance)
