from __future__ import annotations

from rest_framework import serializers


class PaymentsSerializer(serializers.Serializer):
    message = serializers.CharField()
