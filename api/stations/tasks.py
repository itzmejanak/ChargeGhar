from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from typing import Dict, Any

from api.common.tasks.base import BaseTask, NotificationTask
from api.stations.models import Station, StationSlot, StationIssue, PowerBank


@shared_task(base=BaseTask, bind=True)
def update_station_heartbeat(self, station_imei: str, heartbeat_data: Dict[str, Any]):
    """Update station heartbeat and status"""
    try:
        station = Station.objects.get(imei=station_imei)
        
        # Update heartbeat timestamp
        station.last_heartbeat = timezone.now()
        
        # Update status based on heartbeat
        if heartbeat_data.get('online', False):
            station.status = 'ONLINE'
        else:
            station.status = 'OFFLINE'
        
        # Update hardware info if provided
        if heartbeat_data.get('hardware_info'):
            station.hardware_info.update(heartbeat_data['hardware_info'])
        
        station.save(update_fields=['last_heartbeat', 'status', 'hardware_info', 'updated_at'])
        
        # Update slot information if provided
        if heartbeat_data.get('slots'):
            self._update_slot_status(station, heartbeat_data['slots'])
        
        self.logger.info(f"Heartbeat updated for station: {station.station_name}")
        return {
            'station_id': str(station.id),
            'status': station.status,
            'last_heartbeat': station.last_heartbeat.isoformat()
        }
        
    except Station.DoesNotExist:
        self.logger.error(f"Station not found with IMEI: {station_imei}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to update station heartbeat: {str(e)}")
        raise
    
    def _update_slot_status(self, station: Station, slots_data: list):
        """Update individual slot status"""
        for slot_data in slots_data:
            try:
                slot = station.slots.get(slot_number=slot_data['slot_number'])
                slot.status = slot_data.get('status', slot.status)
                slot.battery_level = slot_data.get('battery_level', slot.battery_level)
                
                if slot_data.get('metadata'):
                    slot.slot_metadata.update(slot_data['metadata'])
                
                slot.save(update_fields=['status', 'battery_level', 'slot_metadata', 'last_updated'])
                
            except StationSlot.DoesNotExist:
                self.logger.warning(f"Slot not found: {slot_data['slot_number']} for station {station.station_name}")


@shared_task(base=BaseTask, bind=True)
def check_offline_stations(self):
    """Check for stations that haven't sent heartbeat recently"""
    try:
        # Consider stations offline if no heartbeat for 10 minutes
        cutoff_time = timezone.now() - timezone.timedelta(minutes=10)
        
        offline_stations = Station.objects.filter(
            Q(last_heartbeat__lt=cutoff_time) | Q(last_heartbeat__isnull=True),
            status='ONLINE'
        )
        
        updated_count = 0
        for station in offline_stations:
            station.status = 'OFFLINE'
            station.save(update_fields=['status', 'updated_at'])
            updated_count += 1
            
            # Send notification to admin
            from api.notifications.tasks import send_station_offline_notification
            send_station_offline_notification.delay(station.id)
        
        self.logger.info(f"Marked {updated_count} stations as offline")
        return {'offline_stations_count': updated_count}
        
    except Exception as e:
        self.logger.error(f"Failed to check offline stations: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def sync_power_bank_status(self, power_bank_data: Dict[str, Any]):
    """Sync power bank status from hardware"""
    try:
        power_bank = PowerBank.objects.get(serial_number=power_bank_data['serial_number'])
        
        # Update power bank status
        power_bank.battery_level = power_bank_data.get('battery_level', power_bank.battery_level)
        power_bank.status = power_bank_data.get('status', power_bank.status)
        
        if power_bank_data.get('hardware_info'):
            power_bank.hardware_info.update(power_bank_data['hardware_info'])
        
        power_bank.save(update_fields=['battery_level', 'status', 'hardware_info', 'last_updated'])
        
        self.logger.info(f"Power bank status synced: {power_bank.serial_number}")
        return {
            'power_bank_id': str(power_bank.id),
            'status': power_bank.status,
            'battery_level': power_bank.battery_level
        }
        
    except PowerBank.DoesNotExist:
        self.logger.error(f"Power bank not found: {power_bank_data['serial_number']}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to sync power bank status: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_station_analytics_report(self, station_id: str, date_range: tuple = None):
    """Generate comprehensive analytics report for a station"""
    try:
        from api.stations.services import StationService
        
        service = StationService()
        
        # Convert date strings back to datetime if provided
        if date_range:
            from datetime import datetime
            start_date = datetime.fromisoformat(date_range[0])
            end_date = datetime.fromisoformat(date_range[1])
            date_range = (start_date, end_date)
        
        analytics = service.get_station_analytics(station_id, date_range)
        
        # Cache the analytics report
        from django.core.cache import cache
        cache_key = f"station_analytics:{station_id}"
        cache.set(cache_key, analytics, timeout=3600)  # 1 hour
        
        self.logger.info(f"Analytics report generated for station: {station_id}")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate station analytics: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def cleanup_resolved_issues(self):
    """Clean up old resolved issues (older than 6 months)"""
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=180)
        
        deleted_count = StationIssue.objects.filter(
            status='RESOLVED',
            resolved_at__lt=cutoff_date
        ).delete()[0]
        
        self.logger.info(f"Cleaned up {deleted_count} resolved issues")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup resolved issues: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_station_maintenance_reminder(self, station_id: str):
    """Send maintenance reminder for station"""
    try:
        station = Station.objects.get(id=station_id)
        
        # Send notification to admin users
        from django.contrib.auth import get_user_model
        from api.notifications.models import Notification
        
        User = get_user_model()
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                title="Station Maintenance Required",
                message=f"Station {station.station_name} requires maintenance check.",
                notification_type="MAINTENANCE_REMINDER",
                data={
                    'station_id': str(station.id),
                    'station_name': station.station_name,
                    'action': 'schedule_maintenance'
                }
            )
        
        self.logger.info(f"Maintenance reminder sent for station: {station.station_name}")
        return {'station_id': station_id, 'notifications_sent': admin_users.count()}
        
    except Station.DoesNotExist:
        self.logger.error(f"Station not found: {station_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send maintenance reminder: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def optimize_power_bank_distribution(self):
    """Optimize power bank distribution across stations"""
    try:
        # Get stations with low power bank availability
        low_availability_stations = Station.objects.annotate(
            available_count=Count('slots', filter=Q(slots__status='AVAILABLE'))
        ).filter(
            status='ONLINE',
            is_maintenance=False,
            available_count__lt=2  # Less than 2 available slots
        )
        
        # Get stations with high availability
        high_availability_stations = Station.objects.annotate(
            available_count=Count('slots', filter=Q(slots__status='AVAILABLE'))
        ).filter(
            status='ONLINE',
            is_maintenance=False,
            available_count__gt=5  # More than 5 available slots
        )
        
        optimization_suggestions = []
        
        for low_station in low_availability_stations:
            for high_station in high_availability_stations:
                # Calculate distance between stations
                from api.common.utils.helpers import calculate_distance
                distance = calculate_distance(
                    float(low_station.latitude), float(low_station.longitude),
                    float(high_station.latitude), float(high_station.longitude)
                )
                
                # Suggest redistribution if stations are within 5km
                if distance <= 5.0:
                    optimization_suggestions.append({
                        'from_station': {
                            'id': str(high_station.id),
                            'name': high_station.station_name,
                            'available_count': high_station.available_count
                        },
                        'to_station': {
                            'id': str(low_station.id),
                            'name': low_station.station_name,
                            'available_count': low_station.available_count
                        },
                        'distance': round(distance, 2),
                        'suggested_transfer': min(2, high_station.available_count - 3)
                    })
        
        # Send optimization report to admin
        if optimization_suggestions:
            from api.notifications.tasks import send_optimization_report
            send_optimization_report.delay(optimization_suggestions)
        
        self.logger.info(f"Power bank optimization completed. {len(optimization_suggestions)} suggestions generated")
        return {
            'suggestions_count': len(optimization_suggestions),
            'suggestions': optimization_suggestions
        }
        
    except Exception as e:
        self.logger.error(f"Failed to optimize power bank distribution: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def update_station_popularity_score(self):
    """Update popularity scores for stations based on usage"""
    try:
        from api.rentals.models import Rental
        
        # Calculate popularity based on last 30 days rentals
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        stations = Station.objects.all()
        updated_count = 0
        
        for station in stations:
            rental_count = Rental.objects.filter(
                station=station,
                created_at__gte=thirty_days_ago
            ).count()
            
            # Simple popularity score calculation
            # You can make this more sophisticated based on your needs
            popularity_score = min(rental_count * 10, 1000)  # Max score of 1000
            
            # Store in hardware_info for now, you might want a dedicated field
            station.hardware_info['popularity_score'] = popularity_score
            station.save(update_fields=['hardware_info', 'updated_at'])
            updated_count += 1
        
        self.logger.info(f"Updated popularity scores for {updated_count} stations")
        return {'updated_stations': updated_count}
        
    except Exception as e:
        self.logger.error(f"Failed to update station popularity scores: {str(e)}")
        raise