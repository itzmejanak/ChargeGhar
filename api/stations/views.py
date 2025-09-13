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
from api.common.services.base import ServiceException
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

@router.register(r"stations/list", name="stations-list")
@extend_schema(
    tags=["Stations"],
    summary="List Stations",
    description="Lists all active stations with real-time status (slots, location, online/offline)"
)
class StationListView(GenericAPIView):
    serializer_class = serializers.StationListSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        try:
            # Extract query parameters
            filters = {
                'status': request.query_params.get('status'),
                'search': request.query_params.get('search'),
                'has_available_slots': request.query_params.get('has_available_slots') == 'true',
                'page': int(request.query_params.get('page', 1)),
                'page_size': int(request.query_params.get('page_size', 20))
            }
            
            # Add location filters if provided
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            radius = request.query_params.get('radius')
            
            if lat and lng:
                try:
                    filters.update({
                        'lat': float(lat),
                        'lng': float(lng),
                        'radius': float(radius) if radius else 5.0
                    })
                except ValueError:
                    return Response(
                        {'detail': 'Invalid coordinates or radius'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Clean empty filters
            filters = {k: v for k, v in filters.items() if v is not None and v != ''}
            
            station_service = StationService()
            result = station_service.get_stations_list(filters, request.user)
            
            # Serialize the results
            serializer = self.get_serializer(
                result.get('results', []), 
                many=True, 
                context={'request': request}
            )
            
            return Response({
                'count': result['pagination']['total_count'],
                'next': result['pagination']['has_next'],
                'previous': result['pagination']['has_previous'],
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to list stations: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve stations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"stations/<str:sn>", name="station-detail")
@extend_schema(
    tags=["Stations"],
    summary="Station Detail",
    description="Returns detailed station data: location, slot availability, battery levels, and online status",
    parameters=[
        OpenApiParameter(
            name="sn",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="Station serial number",
            required=True
        )
    ]
)
class StationDetailView(GenericAPIView):
    serializer_class = serializers.StationDetailSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request, sn: str) -> Response:
        try:
            station_service = StationService()
            station = station_service.get_station_detail(sn, request.user)
            
            serializer = self.get_serializer(station, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get station detail: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve station details'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"stations/nearby", name="stations-nearby")
@extend_schema(
    tags=["Stations"],
    summary="Nearby Stations",
    description="Fetches stations within radius for map integration (params: lat, lng, radius)"
)
class NearbyStationsView(GenericAPIView):
    serializer_class = serializers.NearbyStationsSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        # Validate query parameters
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 5.0)
        
        if not lat or not lng:
            return Response(
                {'detail': 'Latitude and longitude are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate with serializer
        input_serializer = self.get_serializer(data={
            'lat': lat,
            'lng': lng,
            'radius': radius
        })
        input_serializer.is_valid(raise_exception=True)
        
        try:
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
            
            return Response({
                'count': len(output_serializer.data),
                'center': {
                    'lat': input_serializer.validated_data['lat'],
                    'lng': input_serializer.validated_data['lng']
                },
                'radius_km': input_serializer.validated_data['radius'],
                'results': output_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get nearby stations: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve nearby stations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===============================
# STATION FAVORITES ENDPOINTS
# ===============================

@router.register(r"stations/<str:sn>/favorite", name="station-favorite")
class StationFavoriteView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserStationFavoriteSerializer  # Add missing serializer
    
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
        ]
    )
    def post(self, request: Request, sn: str) -> Response:
        """Add station to favorites"""
        try:
            favorite_service = StationFavoriteService()
            result = favorite_service.add_favorite(request.user, sn)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to add favorite: {str(e)}")
            return Response(
                {'detail': 'Failed to add station to favorites'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        ]
    )
    def delete(self, request: Request, sn: str) -> Response:
        """Remove station from favorites"""
        try:
            favorite_service = StationFavoriteService()
            result = favorite_service.remove_favorite(request.user, sn)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to remove favorite: {str(e)}")
            return Response(
                {'detail': 'Failed to remove station from favorites'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"stations/favorites", name="user-favorite-stations")
@extend_schema(
    tags=["Stations"],
    summary="User Favorite Stations",
    description="Returns all stations marked as favorites by the user"
)
class UserFavoriteStationsView(GenericAPIView):
    serializer_class = serializers.UserStationFavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            favorite_service = StationFavoriteService()
            result = favorite_service.get_user_favorites(request.user, page, page_size)
            
            serializer = self.get_serializer(
                result.get('results', []), 
                many=True, 
                context={'request': request}
            )
            
            return Response({
                'count': result['pagination']['total_count'],
                'next': result['pagination']['has_next'],
                'previous': result['pagination']['has_previous'],
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get user favorites: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve favorite stations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    ]
)
class StationReportIssueView(GenericAPIView):
    serializer_class = serializers.StationIssueCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request, sn: str) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            issue_service = StationIssueService()
            issue = issue_service.report_issue(
                user=request.user,
                station_sn=sn,
                validated_data=serializer.validated_data
            )
            
            response_serializer = serializers.StationIssueSerializer(issue)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to report station issue: {str(e)}")
            return Response(
                {'detail': 'Failed to report station issue'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"stations/my-reports", name="user-station-reports")
@extend_schema(
    tags=["Stations"],
    summary="My Reported Issues",
    description="Returns all issues reported by the authenticated user"
)
class UserStationReportsView(GenericAPIView):
    serializer_class = serializers.StationIssueSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            issue_service = StationIssueService()
            result = issue_service.get_user_reported_issues(request.user, page, page_size)
            
            serializer = self.get_serializer(
                result.get('results', []), 
                many=True, 
                context={'request': request}
            )
            
            return Response({
                'count': result['pagination']['total_count'],
                'next': result['pagination']['has_next'],
                'previous': result['pagination']['has_previous'],
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get user reports: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve reported issues'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
