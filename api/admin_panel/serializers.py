from __future__ import annotations

from rest_framework import serializers


class AdminPanelSerializer(serializers.Serializer):
    message = serializers.CharField()
