from __future__ import annotations

import logging
from typing import List, Optional

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self, from_email: Optional[str] = None):
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL

    def send_email(
        self,
        subject: str,
        recipient_list: List[str],
        template_name: str,
        context: dict,
        fail_silently: bool = False,
    ) -> None:
        """
        Send an email using a template.

        Args:
            subject: The subject of the email.
            recipient_list: A list of recipient email addresses.
            template_name: The path to the email template file.
            context: A dictionary of context data for the template.
            fail_silently: Whether to raise an exception on failure.
        """
        try:
            html_message = render_to_string(template_name, context)
            send_mail(
                subject,
                message="",  # Plain text message (optional)
                from_email=self.from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=fail_silently,
            )
            logger.info(f"Email sent to {recipient_list} with subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            if not fail_silently:
                raise
