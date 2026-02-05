"""
Factory Boy factories for User models.

This module provides factories for creating test data.
"""

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_verified = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return

        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('TestPass123!')


class ActiveUserFactory(UserFactory):
    """Factory for creating active verified users."""

    is_active = True
    is_verified = True


class StaffUserFactory(UserFactory):
    """Factory for creating staff users."""

    is_staff = True
    is_active = True


class SuperUserFactory(UserFactory):
    """Factory for creating superusers."""

    is_staff = True
    is_superuser = True
    is_active = True
