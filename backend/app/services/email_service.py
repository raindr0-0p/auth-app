from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # In development, we just log. In production, we would use a real email provider.
        if settings.ENVIRONMENT == "development":
            logger.info("EmailService initialized in development mode (logging only)")
        else:
            # In production, we would initialize a real email client (e.g., SMTP, SendGrid, etc.)
            # For now, we'll just log that we are in production mode.
            logger.info("EmailService initialized in production mode")

    async def send_verification_email(self, email: str, token: str) -> None:
        """
        Send an email verification email.
        In development, we log the verification link.
        In production, we would send an actual email.
        """
        # Construct the verification URL
        # Note: In a real application, you would use a frontend URL from settings.
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        if settings.ENVIRONMENT == "development":
            logger.info(f"Verification email for {email}: {verification_url}")
        else:
            # Production: send actual email
            # We would use an email library like aiosmtplib or a service like SendGrid
            # For now, we'll just log (but in production, we would really send)
            logger.info(f"Sending verification email to {email} with link: {verification_url}")
            # TODO: Implement actual email sending

    async def send_password_reset_email(self, email: str, token: str) -> None:
        """
        Send a password reset email.
        In development, we log the reset link.
        In production, we would send an actual email.
        """
        # Construct the reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        if settings.ENVIRONMENT == "development":
            logger.info(f"Password reset email for {email}: {reset_url}")
        else:
            # Production: send actual email
            logger.info(f"Sending password reset email to {email} with link: {reset_url}")
            # TODO: Implement actual email sending

# Create a singleton instance
email_service = EmailService()