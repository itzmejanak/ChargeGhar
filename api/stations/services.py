from __future__ import annotations

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
# Removed unused cache import

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import calculate_distance, paginate_queryset
from api.stations.models import (
    Station, StationSlot, StationIssue, UserStationFavorite, 
    StationAmenity, StationAmenityMapping
)


class StationService(CRUDService):
    """Service for station operations"""
    model = Station
    
    def get_stations_list(self, filters: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """Get paginated list of stations with filters"""
        try:
            # Base queryset with optimized joins
            queryset = self.get_queryset().prefetch_related('slots').order_by('station_name')
            
            # Apply filters
            if filters:
                # Search filter
                if filters.get('search'):
                    search_term = filters['search'].strip()
                    if search_term:
                        queryset = queryset.filter(
                            Q(station_name__icontains=search_term) |
                            Q(address__icontains=search_term) |
                            Q(landmark__icontains=search_term)
                        )
                
                # Location-based filtering (has priority over other filters)
                if all(k in filters for k in ['lat', 'lng', 'radius']):
                    nearby_stations = self._get_nearby_stations(
                        filters['lat'], filters['lng'], filters['radius']
                    )
                    if nearby_stations:
                        station_ids = [s['id'] for s in nearby_stations]
                        queryset = queryset.filter(id__in=station_ids)
                        # Order by distance when location filtering is applied
                        queryset = queryset.extra(
                            select={'distance_order': f"CASE WHEN id IN ({','.join(['%s'] * len(station_ids))}) THEN 1 ELSE 2 END"},
                            select_params=station_ids
                        ).order_by('distance_order', 'station_name')
                    else:
                        # No nearby stations found, return empty queryset
                        queryset = queryset.none()
            
            # Exclude maintenance stations for regular users
            if not (user and user.is_staff):
                queryset = queryset.filter(
                    is_maintenance=False,
                    status__in=['ONLINE', 'OFFLINE']  # Exclude other statuses
                )
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = min(filters.get('page_size', 20) if filters else 20, 50)  # Max 50 per page
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get stations list")
    
    def get_station_detail(self, station_sn: str, user=None) -> Station:
        """Get station detail by serial number"""
        try:
            station = Station.objects.select_related().prefetch_related(
                'slots', 'amenity_mappings__amenity', 'media__media_upload'
            ).get(serial_number=station_sn)
            
            # Check if station is accessible
            if station.is_maintenance and not (user and user.is_staff):
                raise ServiceException(
                    detail="Station is under maintenance",
                    code="station_maintenance"
                )
            
            return station
            
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get station detail")
    
    def get_nearby_stations(self, lat: float, lng: float, radius: float = 5.0) -> List[Dict[str, Any]]:
        """Get stations within radius"""
        try:
            return self._get_nearby_stations(lat, lng, radius)
        except Exception as e:
            self.handle_service_error(e, "Failed to get nearby stations")
    
    def _get_nearby_stations(self, lat: float, lng: float, radius: float) -> List[Dict[str, Any]]:
        """Internal method to calculate nearby stations"""
        try:
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise ServiceException(
                    detail="Invalid coordinates",
                    code="invalid_coordinates"
                )
            
            # Get all active stations
            stations = Station.objects.filter(
                status__in=['ONLINE', 'OFFLINE'],
                is_maintenance=False
            ).values('id', 'station_name', 'latitude', 'longitude', 'address')
            
            nearby_stations = []
            for station in stations:
                try:
                    distance = calculate_distance(
                        lat, lng,
                        float(station['latitude']), float(station['longitude'])
                    )
                    
                    if distance <= radius:
                        station['distance'] = round(distance, 2)
                        nearby_stations.append(station)
                except (ValueError, TypeError):
                    # Skip stations with invalid coordinates
                    continue
            
            # Sort by distance
            nearby_stations.sort(key=lambda x: x['distance'])
            return nearby_stations
            
        except ServiceException:
            raise
        except Exception as e:
            self.handle_service_error(e, "Failed to calculate nearby stations")
    
    @transaction.atomic
    def create_station(self, validated_data: Dict[str, Any]) -> Station:
        """Create new station with slots"""
        try:
            # Create station
            station = Station.objects.create(**validated_data)
            
            # Create slots
            total_slots = validated_data['total_slots']
            slots = []
            for slot_num in range(1, total_slots + 1):
                slots.append(StationSlot(
                    station=station,
                    slot_number=slot_num,
                    status='AVAILABLE'
                ))
            
            StationSlot.objects.bulk_create(slots)
            
            self.log_info(f"Station created: {station.station_name}")
            return station
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create station")
    
    @transaction.atomic
    def update_station_status(self, station_id: str, status: str, is_maintenance: bool = None) -> Station:
        """Update station status"""
        try:
            station = self.get_by_id(station_id)
            station.status = status
            
            if is_maintenance is not None:
                station.is_maintenance = is_maintenance
            
            station.save(update_fields=['status', 'is_maintenance', 'updated_at'])
            
            self.log_info(f"Station status updated: {station.station_name} -> {status}")
            return station
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update station status")

class StationFavoriteService(BaseService):
    """Service for station favorites"""
    
    @transaction.atomic
    def toggle_favorite(self, user, station_sn: str) -> Dict[str, Any]:
        """Toggle station favorite status"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            
            favorite = UserStationFavorite.objects.filter(
                user=user,
                station=station
            ).first()
            
            if favorite:
                # Remove from favorites
                favorite.delete()
                self.log_info(f"Station removed from favorites: {user.username} -> {station.station_name}")
                return {
                    'is_favorite': False,
                    'message': 'Station removed from favorites'
                }
            else:
                # Add to favorites
                UserStationFavorite.objects.create(
                    user=user,
                    station=station
                )
                self.log_info(f"Station added to favorites: {user.username} -> {station.station_name}")
                return {
                    'is_favorite': True,
                    'message': 'Station added to favorites'
                }
                
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to toggle favorite station")
    
    def get_user_favorites(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get user's favorite stations"""
        try:
            # Get favorite stations as queryset with proper ordering
            favorites = UserStationFavorite.objects.filter(
                user=user
            ).select_related('station').order_by('-created_at')
            
            # Get station IDs from favorites to maintain order
            station_ids = list(favorites.values_list('station_id', flat=True))
            
            # Get stations queryset maintaining the favorite order
            stations = Station.objects.filter(id__in=station_ids)
            
            # Preserve the order from favorites
            if station_ids:
                stations = stations.extra(
                    select={'favorite_order': f"array_position(ARRAY{station_ids}::uuid[], id)"},
                    order_by=['favorite_order']
                )
            
            # Apply pagination to queryset
            return paginate_queryset(stations, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get favorite stations")


class StationIssueService(CRUDService):
    """Service for station issues"""
    model = StationIssue
    
    @transaction.atomic
    def report_issue(self, user, station_sn: str, validated_data: Dict[str, Any]) -> StationIssue:
        """Report station issue"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            
            # Check for duplicate recent reports from same user
            recent_issue = StationIssue.objects.filter(
                station=station,
                reported_by=user,
                issue_type=validated_data.get('issue_type'),
                status__in=['REPORTED', 'ACKNOWLEDGED'],
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).first()
            
            if recent_issue:
                raise ServiceException(
                    detail="You have already reported a similar issue for this station in the last 24 hours",
                    code="duplicate_issue_report"
                )
            
            # Create the issue
            issue = StationIssue.objects.create(
                station=station,
                reported_by=user,
                **validated_data
            )
            
            # Send notification to admin (async)
            try:
                from api.notifications.tasks import send_station_issue_notification
                send_station_issue_notification.delay(issue.id)
            except ImportError:
                # Notification task not available, log warning
                self.log_warning(f"Could not send notification for issue {issue.id}")
            
            self.log_info(f"Issue reported for station: {station.station_name} by {user.username}")
            return issue
            
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except ServiceException:
            raise
        except Exception as e:
            self.handle_service_error(e, "Failed to report station issue")
    
# REMOVED: get_station_issues - No corresponding view implemented
    
    def get_user_reported_issues(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get issues reported by user"""
        try:
            queryset = StationIssue.objects.filter(
                reported_by=user
            ).select_related('station').order_by('-created_at')
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user reported issues")


# REMOVED: PowerBankService - Not used in current station views, belongs in rentals app