"""
Station operations and management - control station maintenance, commands and configurations
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin import serializers
from api.admin.services import AdminStationService
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.stations.serializers import StationListSerializer
from api.users.permissions import IsStaffPermission

station_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@station_router.register(r"admin/stations", name="admin-stations")
@extend_schema(
    tags=["Admin"],
    summary="Station Management",
    description="Get list of stations with filters (Staff only)",
    request=serializers.StationFiltersSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminStationsView(GenericAPIView, BaseAPIView):
    """Station management"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get stations list"""
        def operation():
            filter_serializer = serializers.StationFiltersSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = AdminStationService()
            result = service.get_stations_list(filter_serializer.validated_data)
            
            # Serialize the stations in the results
            if result and 'results' in result:
                serialized_stations = StationListSerializer(result['results'], many=True).data
                result['results'] = serialized_stations
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Stations retrieved successfully",
            "Failed to retrieve stations"
        )

@station_router.register(r"admin/stations/<str:station_sn>/maintenance", name="admin-station-maintenance")
@extend_schema(
    tags=["Admin"],
    summary="Toggle Maintenance Mode",
    description="Enable/disable station maintenance mode (Staff only)",
    request=serializers.ToggleMaintenanceSerializer,
    responses={200: BaseResponseSerializer}
)
class ToggleMaintenanceView(GenericAPIView, BaseAPIView):
    """Toggle station maintenance mode"""
    serializer_class = serializers.ToggleMaintenanceSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, station_sn: str) -> Response:
        """Toggle maintenance mode"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminStationService()
            station = service.toggle_maintenance_mode(
                station_sn,
                serializer.validated_data['is_maintenance'],
                serializer.validated_data['reason'],
                request.user
            )
            
            return {
                'station_id': str(station.id),
                'station_name': station.station_name,
                'is_maintenance': station.is_maintenance,
                'message': f'Maintenance mode {"enabled" if station.is_maintenance else "disabled"}'
            }
        
        return self.handle_service_operation(
            operation,
            "Maintenance mode toggled successfully",
            "Failed to toggle maintenance mode"
        )

@station_router.register(r"admin/stations/<str:station_sn>/command", name="admin-station-command")
@extend_schema(
    tags=["Admin"],
    summary="Send Remote Command",
    description="Send remote command to station (Staff only)",
    request=serializers.RemoteCommandSerializer,
    responses={200: BaseResponseSerializer}
)
class SendRemoteCommandView(GenericAPIView, BaseAPIView):
    """Send remote command to station"""
    serializer_class = serializers.RemoteCommandSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, station_sn: str) -> Response:
        """Send remote command"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminStationService()
            result = service.send_remote_command(
                station_sn,
                serializer.validated_data['command'],
                serializer.validated_data.get('parameters', {}),
                request.user
            )
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Command sent successfully",
            "Failed to send command"
        )