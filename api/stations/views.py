from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.common.services.base import ServiceException
from api.common.decorators import cached_response, log_api_call
from api.stations import serializers
from api.stations.models import Station, UserStationFavorite, StationIssue
from api.stations.services import StationService, StationFavoriteService, StationIssueService
from api.users.permissions import IsStaffPermission

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

logger = logging.getLogger(__name__)


# ===============================
# STATION ENDPOINTS
# ===============================

@router.register(r"stations", name="stations-list")
@extend_schema(
    tags=["Stations"],
    summary="List Stations",
    description="Lists all active stations with real-time status and proper pagination.",
    parameters=[
        OpenApiParameter("lat", OpenApiTypes.FLOAT, description="User latitude for distance calculation"),
        OpenApiParameter("lng", OpenApiTypes.FLOAT, description="User longitude for distance calculation"),
        OpenApiParameter("radius", OpenApiTypes.FLOAT, description="Search radius in kilometers (default: 5km)"),
        OpenApiParameter("status", OpenApiTypes.STR, description="Filter by station status"),
        OpenApiParameter("search", OpenApiTypes.STR, description="Search by station name or address"),
        OpenApiParameter("has_available_slots", OpenApiTypes.BOOL, description="Filter stations with available slots"),
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page (max 100)"),
    ],
    responses={200: serializers.StationListResponseSerializer}
)
class StationListView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use MVP serializer for list performance"""
        return serializers.StationListSerializer
    
    def get_queryset(self):
        """Get optimized queryset for real-time data"""
        from django.db.models import Q, Count
        
        # Base queryset with minimal joins for list performance
        queryset = Station.objects.filter(status__in=['ONLINE', 'OFFLINE']).prefetch_related('slots')
        
        # Apply filters using mixins
        queryset = self.apply_status_filter(queryset, self.request)
        
        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(station_name__icontains=search) |
                Q(address__icontains=search) |
                Q(landmark__icontains=search)
            )
        
        # Available slots filter
        if self.request.query_params.get('has_available_slots') == 'true':
            queryset = queryset.annotate(
                available_count=Count('slots', filter=Q(slots__status='AVAILABLE'))
            ).filter(available_count__gt=0)
        
        return queryset.order_by('station_name')
    
    def get(self, request: Request) -> Response:
        """Get paginated stations list with real-time data"""
        def operation():
            queryset = self.get_queryset()
            
            # Location-based filtering
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            radius = request.query_params.get('radius')
            
            if lat and lng:
                try:
                    lat = float(lat)
                    lng = float(lng)
                    radius = float(radius) if radius else 5.0
                    
                    # Use service for location-based filtering
                    service = StationService()
                    nearby_stations = service.get_nearby_stations(lat, lng, radius)
                    station_ids = [s['id'] for s in nearby_stations]
                    queryset = queryset.filter(id__in=station_ids)
                except (ValueError, TypeError):
                    raise ServiceException(
                        detail="Invalid coordinates or radius",
                        code="invalid_location_params"
                    )
            
            # Use pagination mixin for consistent pagination
            paginated_data = self.paginate_response(
                queryset, 
                request, 
                serializer_class=self.get_serializer_class()
            )
            
            return paginated_data
        
        return self.handle_service_operation(
            operation,
            success_message="Stations retrieved successfully",
            error_message="Failed to retrieve stations"
        )


@router.register(r"stations/detail/{sn}", name="station-detail")
@extend_schema(
    tags=["Stations"],
    summary="Station Detail",
    description="Returns detailed real-time station data: location, slot availability, battery levels, and online status.",
    parameters=[
        OpenApiParameter("sn", OpenApiTypes.STR, OpenApiParameter.PATH, description="Station serial number", required=True),
        OpenApiParameter("lat", OpenApiTypes.FLOAT, description="User latitude for distance calculation"),
        OpenApiParameter("lng", OpenApiTypes.FLOAT, description="User longitude for distance calculation"),
    ],
    responses={200: serializers.StationDetailResponseSerializer}
)
class StationDetailView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.StationDetailSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request, sn: str) -> Response:
        """Get real-time station details"""
        def operation():
            station_service = StationService()
            station = station_service.get_station_detail(sn, request.user)
            
            serializer = self.get_serializer(station, context={'request': request})
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Station details retrieved successfully",
            error_message="Failed to retrieve station details"
        )


@router.register(r"stations/nearby", name="stations-nearby")
@extend_schema(
    tags=["Stations"],
    summary="Nearby Stations",
    description="Fetches stations within radius for map integration (params: lat, lng, radius)",
    responses={200: serializers.StationListResponseSerializer}
)
class NearbyStationsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.NearbyStationsSerializer
    permission_classes = [AllowAny]
    
    @cached_response(timeout=30)  # 5 minutes cache for nearby stations
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get nearby stations with caching for performance"""
        def operation():
            # Validate query parameters
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            radius = request.query_params.get('radius', 5.0)
            
            if not lat or not lng:
                raise ServiceException(
                    detail="Latitude and longitude are required",
                    code="missing_coordinates"
                )
            
            # Validate with serializer
            input_serializer = self.get_serializer(data={
                'lat': lat,
                'lng': lng,
                'radius': radius
            })
            input_serializer.is_valid(raise_exception=True)
            
            station_service = StationService()
            nearby_stations = station_service.get_nearby_stations(
                lat=input_serializer.validated_data['lat'],
                lng=input_serializer.validated_data['lng'],
                radius=input_serializer.validated_data['radius']
            )
            
            # Get full station objects for the nearby stations
            station_ids = [station['id'] for station in nearby_stations]
            stations = Station.objects.filter(id__in=station_ids).select_related().prefetch_related('slots', 'media')
            
            # Serialize stations
            output_serializer = serializers.StationListSerializer(
                stations, 
                many=True, 
                context={'request': request}
            )
            
            return {
                'count': len(output_serializer.data),
                'center': {
                    'lat': input_serializer.validated_data['lat'],
                    'lng': input_serializer.validated_data['lng']
                },
                'radius_km': input_serializer.validated_data['radius'],
                'results': output_serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Nearby stations retrieved successfully",
            error_message="Failed to retrieve nearby stations"
        )


# ===============================
# STATION FAVORITES ENDPOINTS
# ===============================

@router.register(r"stations/<str:sn>/favorite", name="station-favorite")
class StationFavoriteView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserStationFavoriteSerializer
    
    @extend_schema(
        tags=["Stations"],
        summary="Add Station to Favorites",
        description="Add station to user's favorite list",
        operation_id="station_favorite_add",
        parameters=[
            OpenApiParameter(
                name="sn",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Station serial number",
                required=True
            )
        ],
        responses={200: serializers.StationFavoriteResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request, sn: str) -> Response:
        """Add station to favorites"""
        def operation():
            favorite_service = StationFavoriteService()
            return favorite_service.add_favorite(request.user, sn)
        
        return self.handle_service_operation(
            operation,
            success_message="Station added to favorites successfully",
            error_message="Failed to add station to favorites"
        )
    
    @extend_schema(
        tags=["Stations"],
        summary="Remove Station from Favorites",
        description="Remove station from user's favorite list",
        operation_id="station_favorite_remove",
        parameters=[
            OpenApiParameter(
                name="sn",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Station serial number",
                required=True
            )
        ],
        responses={200: serializers.StationFavoriteResponseSerializer}
    )
    @log_api_call()
    def delete(self, request: Request, sn: str) -> Response:
        """Remove station from favorites"""
        def operation():
            favorite_service = StationFavoriteService()
            return favorite_service.remove_favorite(request.user, sn)
        
        return self.handle_service_operation(
            operation,
            success_message="Station removed from favorites successfully",
            error_message="Failed to remove station from favorites"
        )


@router.register(r"stations/favorites", name="user-favorite-stations")
@extend_schema(
    tags=["Stations"],
    summary="User Favorite Stations",
    description="Returns all stations marked as favorites by the user",
    responses={200: serializers.UserFavoriteStationsResponseSerializer}
)
class UserFavoriteStationsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserStationFavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's favorite stations - real-time data, no caching"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            favorite_service = StationFavoriteService()
            result = favorite_service.get_user_favorites(request.user, page, page_size)
            
            serializer = self.get_serializer(
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
# STATION ISSUE REPORTING ENDPOINTS
# ===============================

@router.register(r"stations/<str:sn>/report-issue", name="station-report-issue")
@extend_schema(
    tags=["Stations"],
    summary="Report Station Issue",
    description="Report station issues (offline, damaged, dirty, location wrong, etc.)",
    parameters=[
        OpenApiParameter(
            name="sn",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="Station serial number",
            required=True
        )
    ],
    responses={201: serializers.StationIssueResponseSerializer}
)
class StationReportIssueView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.StationIssueCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def post(self, request: Request, sn: str) -> Response:
        """Report station issue - real-time operation, no caching"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            issue_service = StationIssueService()
            issue = issue_service.report_issue(
                user=request.user,
                station_sn=sn,
                validated_data=serializer.validated_data
            )
            
            response_serializer = serializers.StationIssueSerializer(issue)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Station issue reported successfully",
            error_message="Failed to report station issue",
            success_status=status.HTTP_201_CREATED
        )


@router.register(r"stations/my-reports", name="user-station-reports")
@extend_schema(
    tags=["Stations"],
    summary="My Reported Issues",
    description="Returns all issues reported by the authenticated user",
    responses={200: serializers.UserStationReportsResponseSerializer}
)
class UserStationReportsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.StationIssueSerializer
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's reported issues - real-time data, no caching"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            issue_service = StationIssueService()
            result = issue_service.get_user_reported_issues(request.user, page, page_size)
            
            serializer = self.get_serializer(
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
            success_message="Reported issues retrieved successfully",
            error_message="Failed to retrieve reported issues"
        )


# ===============================
# ADMIN ENDPOINTS (Staff Only)  
# ===============================

@router.register(r"admin/stations", name="admin-stations")
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
