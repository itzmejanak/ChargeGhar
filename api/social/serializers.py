from __future__ import annotations

from rest_framework import serializers


class SocialSerializer(serializers.Serializer):
    message = serializers.CharField()
