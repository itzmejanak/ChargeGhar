from __future__ import annotations

from rest_framework import serializers


class ContentSerializer(serializers.Serializer):
    message = serializers.CharField()
