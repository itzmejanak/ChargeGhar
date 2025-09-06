from __future__ import annotations

from rest_framework import serializers


class PromotionsSerializer(serializers.Serializer):
    message = serializers.CharField()
