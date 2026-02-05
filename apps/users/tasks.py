"""
Celery tasks for User operations.

This module contains asynchronous tasks for User-related operations.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """
    Send welcome email to new user.

    Args:
        user_id: User UUID
    """
    try:
        from .models import User

        user = User.objects.get(id=user_id)

        subject = 'Welcome to Our Platform!'
        message = f"""
        Hello {user.get_full_name()},

        Welcome to our platform! We're excited to have you on board.

        Best regards,
        The Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user.email}")

    except Exception as exc:
        logger.error(f"Failed to send welcome email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, verification_token):
    """
    Send email verification link to user.

    Args:
        user_id: User UUID
        verification_token: Verification token
    """
    try:
        from .models import User

        user = User.objects.get(id=user_id)

        subject = 'Verify Your Email Address'
        # In production, this would be a proper URL
        verification_url = f"https://example.com/verify/{verification_token}"
        message = f"""
        Hello {user.get_full_name()},

        Please verify your email address by clicking the link below:

        {verification_url}

        Best regards,
        The Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {user.email}")

    except Exception as exc:
        logger.error(f"Failed to send verification email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_unverified_users():
    """
    Clean up unverified users older than 30 days.

    This task should be run periodically (e.g., daily via Celery Beat).
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import User

    cutoff_date = timezone.now() - timedelta(days=30)

    deleted_count = User.objects.filter(
        is_verified=False,
        created_at__lt=cutoff_date
    ).delete()[0]

    logger.info(f"Cleaned up {deleted_count} unverified users")
    return deleted_count


@shared_task
def send_password_reset_email(user_id, reset_token):
    """
    Send password reset email to user.

    Args:
        user_id: User UUID
        reset_token: Password reset token
    """
    try:
        from .models import User

        user = User.objects.get(id=user_id)

        subject = 'Reset Your Password'
        reset_url = f"https://example.com/reset-password/{reset_token}"
        message = f"""
        Hello {user.get_full_name()},

        You requested to reset your password. Click the link below to proceed:

        {reset_url}

        If you didn't request this, please ignore this email.

        Best regards,
        The Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Password reset email sent to {user.email}")

    except Exception as exc:
        logger.error(f"Failed to send password reset email: {exc}")
