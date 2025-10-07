from __future__ import annotations

import base64
import json
from django.core.management.base import BaseCommand, CommandParser
from api.users.models import User
from api.notifications.services import FCMService, ServiceException


class Command(BaseCommand):
    """
    Django management command to send a test FCM notification.
    """
    help = "Sends a test FCM notification to a user."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            'user_id', type=str, help='The ID of the user to send the notification to.')

    def handle(self, *args, **options):
        user_id = options['user_id']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"User with ID '{user_id}' not found."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found user: {user.username}"))

        # NOTE: The credentials should be loaded securely from environment variables.
        # This command now relies on the FIREBASE_CREDENTIALS_BASE64 environment
        # variable being set in the environment where the command is run.
        from django.conf import settings
        if not hasattr(settings, 'FIREBASE_CREDENTIALS_BASE64') or not settings.FIREBASE_CREDENTIALS_BASE64:
            self.stdout.write(self.style.ERROR(
                "FIREBASE_CREDENTIALS_BASE64 setting is not configured."
            ))
            return

        self.stdout.write("Attempting to send notification...")
        try:
            fcm_service = FCMService()
            result = fcm_service.send_push_notification(
                user=user,
                title="Test Notification",
                message="This is a test notification from the Django management command.",
                data={'test_key': 'test_value'}
            )

            if result.get('sent_count', 0) > 0:
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully sent notifications to {result['sent_count']} device(s)."
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"No devices found for user or sending failed. Result: {result}"
                ))

        except ServiceException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"An unexpected error occurred: {e}"))
