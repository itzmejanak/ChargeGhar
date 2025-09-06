from __future__ import annotations

from rest_framework import serializers


class PointsSerializer(serializers.Serializer):
    message = serializers.CharField()
