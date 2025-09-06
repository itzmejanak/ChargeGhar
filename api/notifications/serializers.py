from __future__ import annotations

from rest_framework import serializers


class NotificationsSerializer(serializers.Serializer):
    message = serializers.CharField()
