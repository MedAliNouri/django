"""
Custom throttling classes for rate limiting.

This module provides custom throttle classes for different use cases.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Throttle for burst requests.

    Limits short-term burst of requests from a user.
    """
    scope = 'user_burst'

    def allow_request(self, request, view):
        """
        Allow anonymous users to have their own burst rate.
        """
        if request.user.is_authenticated:
            self.scope = 'user_burst'
        else:
            self.scope = 'anon_burst'

        return super().allow_request(request, view)


class SustainedRateThrottle(UserRateThrottle):
    """
    Throttle for sustained requests over a longer period.

    Limits the total number of requests a user can make per hour.
    """
    scope = 'user_sustained'

    def allow_request(self, request, view):
        """
        Allow anonymous users to have their own sustained rate.
        """
        if request.user.is_authenticated:
            self.scope = 'user_sustained'
        else:
            self.scope = 'anon_sustained'

        return super().allow_request(request, view)


class StrictAnonRateThrottle(AnonRateThrottle):
    """
    Stricter rate limit for anonymous users.
    """
    rate = '5/min'


class AuthenticationThrottle(AnonRateThrottle):
    """
    Special throttle for authentication endpoints.

    More restrictive to prevent brute force attacks.
    """
    scope = 'auth'
    rate = '5/min'
