"""
Admin management - station CRUD operations
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


from api.common.routers import CustomViewRouter
from api.stations import serializers
from api.stations.models import Station
from api.stations.services import StationService
from api.users.permissions import IsStaffPermission
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    pass

admin_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_router.register("admin/stations", name="admin-stations")
@extend_schema_view(
    list=extend_schema(
        tags=["Admin"], 
        summary="List All Stations (Admin)",
        description="Returns all stations including maintenance mode (Staff only)"
    ),
    create=extend_schema(
        tags=["Admin"], 
        summary="Create Station (Admin)",
        description="Creates new charging station (Staff only)"
    ),
    retrieve=extend_schema(
        tags=["Admin"], 
        summary="Get Station (Admin)",
        description="Retrieves specific station details (Staff only)"
    ),
    update=extend_schema(
        tags=["Admin"], 
        summary="Update Station (Admin)",
        description="Updates station information (Staff only)"
    ),
    partial_update=extend_schema(
        tags=["Admin"], 
        summary="Partial Update Station (Admin)",
        description="Partially updates station information (Staff only)"
    )
)
class AdminStationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """Admin-only station management ViewSet"""
    serializer_class = serializers.StationDetailSerializer
    queryset = Station.objects.all()
    permission_classes = (IsStaffPermission,)
    lookup_field = 'serial_number'
    
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.StationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.StationUpdateSerializer
        return serializers.StationDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset with related objects"""
        return Station.objects.select_related().prefetch_related(
            'slots', 'amenity_mappings__amenity', 'media__media_upload'
        )
    
    def perform_create(self, serializer):
        """Create station using service layer"""
        try:
            station_service = StationService()
            station = station_service.create_station(serializer.validated_data)
            return station
        except ServiceException as e:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'detail': str(e)})