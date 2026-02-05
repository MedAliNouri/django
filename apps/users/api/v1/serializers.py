"""
API v1 serializers for User endpoints.

This module contains serializers for the User API v1.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.serializers import BaseModelSerializer, WriteableModelSerializer
from apps.users.models import User, UserProfile


class UserProfileSerializer(BaseModelSerializer):
    """
    Serializer for UserProfile model.
    """

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'company',
            'job_title',
            'website',
            'location',
            'twitter_url',
            'linkedin_url',
            'github_url',
            'timezone',
            'language',
            'newsletter_subscribed',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class UserListSerializer(BaseModelSerializer):
    """
    Serializer for User list view (minimal fields).
    """

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'is_active',
            'is_verified',
            'avatar',
            'created_at',
        )
        read_only_fields = fields


class UserDetailSerializer(BaseModelSerializer):
    """
    Serializer for User detail view (all fields).
    """

    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone_number',
            'date_of_birth',
            'avatar',
            'bio',
            'is_active',
            'is_verified',
            'is_email_verified',
            'profile',
            'last_login',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'full_name',
            'is_verified',
            'is_email_verified',
            'last_login',
            'created_at',
            'updated_at',
        )


class UserCreateSerializer(WriteableModelSerializer):
    """
    Serializer for user registration.
    """

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = (
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone_number',
        )
        read_serializer_class = UserDetailSerializer

    def validate(self, attrs):
        """
        Validate passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        """
        Create user using service layer.
        """
        from apps.users.services import UserService

        # Remove password_confirm from validated data
        validated_data.pop('password_confirm')

        # Use service to create user
        user = UserService.create_user(**validated_data)
        return user


class UserUpdateSerializer(WriteableModelSerializer):
    """
    Serializer for user update.
    """

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'avatar',
            'bio',
        )
        read_serializer_class = UserDetailSerializer

    def update(self, instance, validated_data):
        """
        Update user using service layer.
        """
        from apps.users.services import UserService

        user = UserService.update_user(instance, **validated_data)
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile update.
    """

    class Meta:
        model = UserProfile
        fields = (
            'company',
            'job_title',
            'website',
            'location',
            'twitter_url',
            'linkedin_url',
            'github_url',
            'timezone',
            'language',
            'newsletter_subscribed',
        )

    def update(self, instance, validated_data):
        """
        Update user profile using service layer.
        """
        from apps.users.services import UserService

        profile = UserService.update_user_profile(instance.user, **validated_data)
        return profile


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """

    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password], style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """
        Validate new passwords match.
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match'})
        return attrs

    def save(self, **kwargs):
        """
        Change password using service layer.
        """
        from apps.users.services import UserService

        user = self.context['request'].user
        UserService.change_password(user, self.validated_data['old_password'], self.validated_data['new_password'])
        return user


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer for user statistics.
    """

    total = serializers.IntegerField()
    active = serializers.IntegerField()
    verified = serializers.IntegerField()
    staff = serializers.IntegerField()
    inactive = serializers.IntegerField()
    unverified = serializers.IntegerField()
