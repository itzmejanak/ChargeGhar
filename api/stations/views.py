from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.services.base import ServiceException
from api.common.decorators import log_api_call
from api.stations import serializers
from api.stations.models import Station
from api.stations.services import StationService, StationFavoriteService, StationIssueService
from api.users.permissions import IsStaffPermission

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

logger = logging.getLogger(__name__)


# ===============================
# STATION ENDPOINTS
# ===============================

@router.register("stations", name="stations-list")
@extend_schema(
    tags=["Stations"],
    summary="List Stations",
    description="Get list of active charging stations with basic info and availability",
    parameters=[
        OpenApiParameter("lat", OpenApiTypes.FLOAT, description="User latitude for distance calculation"),
        OpenApiParameter("lng", OpenApiTypes.FLOAT, description="User longitude for distance calculation"),
        OpenApiParameter("search", OpenApiTypes.STR, description="Search by station name or address"),
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page (max 50)"),
    ],
    responses={200: serializers.StationListResponseSerializer}
)
class StationListView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.StationListSerializer
    
    def get(self, request: Request) -> Response:
        """Get paginated list of active stations"""
        def operation():
            # Build filters from query params
            filters = {
                'page': int(request.query_params.get('page', 1)),
                'page_size': min(int(request.query_params.get('page_size', 20)), 50),
            }
            
            # Add optional filters
            if request.query_params.get('search'):
                filters['search'] = request.query_params.get('search')
            
            if request.query_params.get('lat') and request.query_params.get('lng'):
                try:
                    filters['lat'] = float(request.query_params.get('lat'))
                    filters['lng'] = float(request.query_params.get('lng'))
                    filters['radius'] = 10.0  # Fixed 10km radius for list
                except (ValueError, TypeError):
                    raise ServiceException(
                        detail="Invalid coordinates",
                        code="invalid_coordinates"
                    )
            
            # Get stations from service
            service = StationService()
            result = service.get_stations_list(filters, request.user)
            
            # Serialize results
            serializer = self.get_serializer(
                result['results'], 
                many=True, 
                context={'request': request}
            )
            
            return {
                'count': result['pagination']['total_count'],
                'next': result['pagination']['has_next'],
                'previous': result['pagination']['has_previous'],
                'results': serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Stations retrieved successfully",
            error_message="Failed to retrieve stations"
        )


@router.register("stations/nearby", name="stations-nearby")
@extend_schema(
    tags=["Stations"],
    summary="Nearby Stations",
    description="Get stations within specified radius for map display",
    parameters=[
        OpenApiParameter("lat", OpenApiTypes.FLOAT, description="Latitude", required=True),
        OpenApiParameter("lng", OpenApiTypes.FLOAT, description="Longitude", required=True),
        OpenApiParameter("radius", OpenApiTypes.FLOAT, description="Search radius in km (default: 5, max: 20)"),
    ],
    responses={200: serializers.StationListResponseSerializer}
)
class NearbyStationsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.NearbyStationsSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get nearby stations for map display"""
        def operation():
            # Validate input
            input_serializer = self.get_serializer(data={
                'lat': request.query_params.get('lat'),
                'lng': request.query_params.get('lng'),
                'radius': request.query_params.get('radius', 5.0)
            })
            input_serializer.is_valid(raise_exception=True)
            
            # Get nearby stations
            station_service = StationService()
            nearby_stations = station_service.get_nearby_stations(
                lat=input_serializer.validated_data['lat'],
                lng=input_serializer.validated_data['lng'],
                radius=min(input_serializer.validated_data['radius'], 20.0)  # Max 20km
            )
            
            # Get full station objects
            station_ids = [station['id'] for station in nearby_stations]
            stations = Station.objects.filter(id__in=station_ids).prefetch_related('slots')
            
            # Serialize results
            serializer = serializers.StationListSerializer(
                stations, 
                many=True, 
                context={'request': request}
            )
            
            return {
                'count': len(serializer.data),
                'results': serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Nearby stations retrieved successfully",
            error_message="Failed to retrieve nearby stations"
        )


@router.register("stations/favorites", name="user-favorite-stations")
@extend_schema(
    tags=["Stations"],
    summary="My Favorite Stations",
    description="Get user's favorite stations list",
    parameters=[
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page (max 50)"),
    ],
    responses={200: serializers.UserFavoriteStationsResponseSerializer}
)
class UserFavoriteStationsView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's favorite stations"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 50)
            
            favorite_service = StationFavoriteService()
            result = favorite_service.get_user_favorites(request.user, page, page_size)
            
            # Serialize stations
            serializer = serializers.StationListSerializer(
                result.get('results', []), 
                many=True, 
                context={'request': request}
            )
            
            return {
                'count': result['pagination']['total_count'],
                'next': result['pagination']['has_next'],
                'previous': result['pagination']['has_previous'],
                'results': serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Favorite stations retrieved successfully",
            error_message="Failed to retrieve favorite stations"
        )


# ===============================
# USER STATION REPORTS (must be before <str:serial_number> route)
# ===============================

@router.register("stations/my-reports", name="user-station-reports")
@extend_schema(
    tags=["Stations"],
    summary="My Issue Reports",
    description="Get issues reported by the authenticated user",
    parameters=[
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page (max 50)"),
    ],
    responses={200: serializers.UserStationReportsResponseSerializer}
)
class UserStationReportsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.StationIssueSerializer
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's reported issues"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 50)
            
            issue_service = StationIssueService()
            result = issue_service.get_user_reported_issues(request.user, page, page_size)
            
            serializer = self.get_serializer(
                result.get('results', []), 
                many=True, 
                context={'request': request}
            )
            
            return {
                'count': result['pagination']['total_count'],
                'next': result['pagination']['has_previous'],
                'previous': result['pagination']['has_previous'],
                'results': serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Reports retrieved successfully",
            error_message="Failed to retrieve reports"
        )


@router.register("stations/<str:serial_number>", name="station-detail")
@extend_schema(
    tags=["Stations"],
    summary="Station Detail",
    description="Get detailed station information including slots, amenities, and real-time status",
    parameters=[
        OpenApiParameter("serial_number", OpenApiTypes.STR, OpenApiParameter.PATH, description="Station serial number", required=True),
        OpenApiParameter("lat", OpenApiTypes.FLOAT, description="User latitude for distance calculation"),
        OpenApiParameter("lng", OpenApiTypes.FLOAT, description="User longitude for distance calculation"),
    ],
    responses={200: serializers.StationDetailResponseSerializer}
)
class StationDetailView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.StationDetailSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request, serial_number: str) -> Response:
        """Get detailed station information"""
        def operation():
            station_service = StationService()
            station = station_service.get_station_detail(serial_number, request.user)
            
            serializer = self.get_serializer(station, context={'request': request})
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Station details retrieved successfully",
            error_message="Failed to retrieve station details"
        )


# ===============================
# STATION FAVORITES ENDPOINTS
# ===============================

@router.register("stations/<str:serial_number>/favorite", name="station-favorite")
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

@router.register("stations/<str:serial_number>/report-issue", name="station-report-issue")
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


# ===============================
# ADMIN ENDPOINTS (Staff Only)  
# ===============================

@router.register("admin/stations", name="admin-stations")
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
