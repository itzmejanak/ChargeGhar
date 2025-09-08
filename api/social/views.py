from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.social import serializers

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"social/achievements", name="social-achievements")
class SocialAchievementView(GenericAPIView):
    serializer_class = serializers.AchievementSerializer

    def get(self, request: Request) -> Response:
        """Get user achievements"""
        achievements = serializers.AchievementSerializer([], many=True)
        return Response(achievements.data)

    def post(self, request: Request) -> Response:
        """Update achievement progress"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
