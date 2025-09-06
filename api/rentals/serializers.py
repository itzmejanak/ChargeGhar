from __future__ import annotations

from rest_framework import serializers


class RentalsSerializer(serializers.Serializer):
    message = serializers.CharField()
