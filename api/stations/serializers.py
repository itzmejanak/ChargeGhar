from __future__ import annotations

from rest_framework import serializers


class StationsSerializer(serializers.Serializer):
    message = serializers.CharField()
