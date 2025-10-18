"""
User interactions - favorite toggle and issue reporting
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call, cached_response
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.stations import serializers
from api.stations.models import Station
from api.stations.services import StationService, StationFavoriteService, StationIssueService
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

interaction_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@interaction_router.register("stations/<str:serial_number>/favorite", name="station-favorite")
class StationFavoriteView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.StationListSerializer  # For schema generation
    
    @extend_schema(
        tags=["Stations"],
        summary="Toggle Station Favorite",
        description="Add or remove station from user's favorites",
        parameters=[
            OpenApiParameter("serial_number", OpenApiTypes.STR, OpenApiParameter.PATH, description="Station serial number", required=True)
        ],
        responses={200: serializers.StationFavoriteResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request, serial_number: str) -> Response:
        """Toggle station favorite status"""
        def operation():
            favorite_service = StationFavoriteService()
            result = favorite_service.toggle_favorite(request.user, serial_number)
            return {
                'is_favorite': result['is_favorite'],
                'message': result['message']
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Favorite status updated successfully",
            error_message="Failed to update favorite status"
        )


# ===============================
# STATION ISSUE REPORTING ENDPOINTS
# ===============================


@interaction_router.register("stations/<str:serial_number>/report-issue", name="station-report-issue")
@extend_schema(
    tags=["Stations"],
    summary="Report Station Issue",
    description="Report problems with a charging station",
    parameters=[
        OpenApiParameter("serial_number", OpenApiTypes.STR, OpenApiParameter.PATH, description="Station serial number", required=True)
    ],
    request=serializers.StationIssueCreateSerializer,
    responses={201: serializers.StationIssueResponseSerializer}
)
class StationReportIssueView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.StationIssueCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def post(self, request: Request, serial_number: str) -> Response:
        """Report station issue"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            issue_service = StationIssueService()
            issue = issue_service.report_issue(
                user=request.user,
                station_sn=serial_number,
                validated_data=serializer.validated_data
            )
            
            response_serializer = serializers.StationIssueSerializer(issue)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Issue reported successfully",
            error_message="Failed to report issue",
            success_status=status.HTTP_201_CREATED
        )