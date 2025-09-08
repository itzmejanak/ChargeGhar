from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.cache import cache

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import calculate_distance, paginate_queryset
from api.stations.models import (
    Station, StationSlot, StationIssue, UserStationFavorite, 
    PowerBank, StationAmenity, StationAmenityMapping
)


class StationService(CRUDService):
    """Service for station operations"""
    model = Station
    
    def get_stations_list(self, filters: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """Get paginated list of stations with filters"""
        try:
            queryset = self.get_queryset().select_related().prefetch_related('slots', 'media')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(station_name__icontains=search_term) |
                        Q(address__icontains=search_term) |
                        Q(landmark__icontains=search_term)
                    )
                
                if filters.get('has_available_slots'):
                    queryset = queryset.annotate(
                        available_count=Count('slots', filter=Q(slots__status='AVAILABLE'))
                    ).filter(available_count__gt=0)
                
                # Location-based filtering
                if all(k in filters for k in ['lat', 'lng', 'radius']):
                    nearby_stations = self._get_nearby_stations(
                        filters['lat'], filters['lng'], filters['radius']
                    )
                    station_ids = [s['id'] for s in nearby_stations]
                    queryset = queryset.filter(id__in=station_ids)
            
            # Exclude maintenance stations for regular users
            if not (user and user.is_staff):
                queryset = queryset.filter(is_maintenance=False)
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
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
        # Get all active stations
        stations = Station.objects.filter(
            status='ONLINE',
            is_maintenance=False
        ).values('id', 'station_name', 'latitude', 'longitude', 'address')
        
        nearby_stations = []
        for station in stations:
            distance = calculate_distance(
                lat, lng,
                float(station['latitude']), float(station['longitude'])
            )
            
            if distance <= radius:
                station['distance'] = round(distance, 2)
                nearby_stations.append(station)
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: x['distance'])
        return nearby_stations
    
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
    
    def get_station_analytics(self, station_id: str, date_range: Tuple[timezone.datetime, timezone.datetime] = None) -> Dict[str, Any]:
        """Get station analytics data"""
        try:
            station = self.get_by_id(station_id)
            
            # Default to last 30 days if no date range provided
            if not date_range:
                end_date = timezone.now()
                start_date = end_date - timezone.timedelta(days=30)
                date_range = (start_date, end_date)
            
            from api.rentals.models import Rental
            from api.payments.models import Transaction
            
            # Get rentals in date range
            rentals = Rental.objects.filter(
                station=station,
                created_at__range=date_range
            )
            
            total_rentals = rentals.count()
            
            # Calculate revenue
            transactions = Transaction.objects.filter(
                related_rental__station=station,
                status='SUCCESS',
                created_at__range=date_range
            )
            total_revenue = sum(t.amount for t in transactions)
            
            # Calculate utilization rate
            total_possible_hours = station.total_slots * 24 * (date_range[1] - date_range[0]).days
            total_rental_hours = sum(
                (r.ended_at - r.started_at).total_seconds() / 3600 
                for r in rentals.filter(ended_at__isnull=False)
            )
            utilization_rate = (total_rental_hours / total_possible_hours * 100) if total_possible_hours > 0 else 0
            
            # Get issues count
            issues_count = StationIssue.objects.filter(
                station=station,
                created_at__range=date_range
            ).count()
            
            return {
                'station_id': station_id,
                'station_name': station.station_name,
                'total_rentals': total_rentals,
                'total_revenue': total_revenue,
                'average_rental_duration': 0,  # Calculate if needed
                'utilization_rate': round(utilization_rate, 2),
                'popular_time_slots': [],  # Calculate if needed
                'issues_count': issues_count,
                'uptime_percentage': 95.0,  # Calculate based on heartbeat data
                'last_maintenance': None  # Get from maintenance logs
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get station analytics")


class StationFavoriteService(BaseService):
    """Service for station favorites"""
    
    @transaction.atomic
    def add_favorite(self, user, station_sn: str) -> Dict[str, Any]:
        """Add station to user favorites"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            
            favorite, created = UserStationFavorite.objects.get_or_create(
                user=user,
                station=station
            )
            
            if created:
                self.log_info(f"Station added to favorites: {user.username} -> {station.station_name}")
                return {'message': 'Station added to favorites', 'created': True}
            else:
                return {'message': 'Station already in favorites', 'created': False}
                
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to add favorite station")
    
    def remove_favorite(self, user, station_sn: str) -> Dict[str, Any]:
        """Remove station from user favorites"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            
            deleted_count = UserStationFavorite.objects.filter(
                user=user,
                station=station
            ).delete()[0]
            
            if deleted_count > 0:
                self.log_info(f"Station removed from favorites: {user.username} -> {station.station_name}")
                return {'message': 'Station removed from favorites', 'removed': True}
            else:
                return {'message': 'Station was not in favorites', 'removed': False}
                
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to remove favorite station")
    
    def get_user_favorites(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get user's favorite stations"""
        try:
            queryset = UserStationFavorite.objects.filter(user=user).select_related('station')
            return paginate_queryset(queryset, page, page_size)
            
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
            
            issue = StationIssue.objects.create(
                station=station,
                reported_by=user,
                **validated_data
            )
            
            # Send notification to admin
            from api.notifications.tasks import send_station_issue_notification
            send_station_issue_notification.delay(issue.id)
            
            self.log_info(f"Issue reported for station: {station.station_name} by {user.username}")
            return issue
            
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to report station issue")
    
    def get_station_issues(self, station_sn: str, user=None) -> List[StationIssue]:
        """Get issues for a station"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            
            queryset = StationIssue.objects.filter(station=station)
            
            # Regular users can only see their own reports
            if not (user and user.is_staff):
                queryset = queryset.filter(reported_by=user)
            
            return queryset.order_by('-created_at')
            
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get station issues")
    
    def get_user_reported_issues(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get issues reported by user"""
        try:
            queryset = StationIssue.objects.filter(reported_by=user).select_related('station')
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user reported issues")


class PowerBankService(CRUDService):
    """Service for power bank operations"""
    model = PowerBank
    
    def get_available_power_bank(self, station: Station) -> Optional[PowerBank]:
        """Get available power bank from station"""
        try:
            # Find available slot with power bank
            available_slot = station.slots.filter(
                status='AVAILABLE',
                battery_level__gte=20  # Minimum 20% battery
            ).order_by('-battery_level').first()
            
            if not available_slot:
                return None
            
            # Get power bank in that slot
            power_bank = PowerBank.objects.filter(
                current_station=station,
                current_slot=available_slot,
                status='AVAILABLE'
            ).first()
            
            return power_bank
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get available power bank")
    
    @transaction.atomic
    def assign_power_bank_to_rental(self, power_bank: PowerBank, rental) -> PowerBank:
        """Assign power bank to rental"""
        try:
            power_bank.status = 'RENTED'
            power_bank.save(update_fields=['status', 'updated_at'])
            
            # Update slot status
            if power_bank.current_slot:
                power_bank.current_slot.status = 'OCCUPIED'
                power_bank.current_slot.current_rental = rental
                power_bank.current_slot.save(update_fields=['status', 'current_rental', 'last_updated'])
            
            self.log_info(f"Power bank assigned to rental: {power_bank.serial_number}")
            return power_bank
            
        except Exception as e:
            self.handle_service_error(e, "Failed to assign power bank to rental")
    
    @transaction.atomic
    def return_power_bank(self, power_bank: PowerBank, return_station: Station, return_slot: StationSlot) -> PowerBank:
        """Return power bank to station"""
        try:
            # Update power bank
            power_bank.status = 'AVAILABLE'
            power_bank.current_station = return_station
            power_bank.current_slot = return_slot
            power_bank.save(update_fields=['status', 'current_station', 'current_slot', 'updated_at'])
            
            # Update slot status
            return_slot.status = 'OCCUPIED'  # Occupied by returned power bank
            return_slot.current_rental = None
            return_slot.save(update_fields=['status', 'current_rental', 'last_updated'])
            
            self.log_info(f"Power bank returned: {power_bank.serial_number}")
            return power_bank
            
        except Exception as e:
            self.handle_service_error(e, "Failed to return power bank")