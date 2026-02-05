"""
Admin configuration for User models.

This module configures the Django admin interface for User models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.core.admin import BaseModelAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin, BaseModelAdmin):
    """
    Admin configuration for User model.
    """

    list_display = (
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_verified',
        'is_staff',
        'created_at'
    )
    list_filter = (
        'is_active',
        'is_verified',
        'is_staff',
        'is_superuser',
        'created_at'
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'last_login',
        'email_verified_at'
    )

    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'phone_number',
                'date_of_birth',
                'avatar',
                'bio'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_verified',
                'groups',
                'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': (
                'last_login',
                'email_verified_at',
                'created_at',
                'updated_at'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'last_login_ip')
        }),
    )

    add_fieldsets = (
        ('Authentication', {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )

    def get_queryset(self, request):
        """Include soft-deleted users in admin."""
        return User.objects.with_deleted()


@admin.register(UserProfile)
class UserProfileAdmin(BaseModelAdmin):
    """
    Admin configuration for UserProfile model.
    """

    list_display = (
        'user',
        'company',
        'job_title',
        'location',
        'timezone',
        'created_at'
    )
    list_filter = ('newsletter_subscribed', 'created_at')
    search_fields = ('user__email', 'company', 'job_title', 'location')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('company', 'job_title', 'website', 'location')
        }),
        ('Social Links', {
            'fields': ('twitter_url', 'linkedin_url', 'github_url')
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'newsletter_subscribed')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )
