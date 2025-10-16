from __future__ import annotations

from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import generate_rental_code, paginate_queryset
from api.rentals.models import (
    Rental, RentalExtension, RentalIssue, RentalLocation, RentalPackage
)
from api.stations.models import Station, StationSlot, PowerBank
from api.common.permissions.base import CanRentPowerBank


class RentalService(CRUDService):
    """Service for rental operations"""
    model = Rental
    
    @transaction.atomic
    def start_rental(self, user, station_sn: str, package_id: str, payment_scenario: str = None) -> Rental:
        """Start a new rental session"""
        try:
            # Validate prerequisites
            self._validate_rental_prerequisites(user)
            
            # Get station and package
            station = Station.objects.get(serial_number=station_sn)
            package = RentalPackage.objects.get(id=package_id, is_active=True)
            
            # Validate station availability
            self._validate_station_availability(station)
            
            # Get available power bank and slot
            power_bank, slot = self._get_available_power_bank_and_slot(station)
            
            # For pre-payment model, check and process payment
            if package.payment_model == 'PREPAID':
                self._process_prepayment(user, package)
            
            # Create rental
            rental = Rental.objects.create(
                user=user,
                station=station,
                slot=slot,
                package=package,
                power_bank=power_bank,
                rental_code=generate_rental_code(),
                due_at=timezone.now() + timezone.timedelta(minutes=package.duration_minutes),
                amount_paid=package.price if package.payment_model == 'PREPAID' else Decimal('0')
            )
            
            # Assign power bank to rental
            from api.stations.services import PowerBankService
            powerbank_service = PowerBankService()
            powerbank_service.assign_power_bank_to_rental(power_bank, rental)
            
            # Start the rental
            rental.status = 'ACTIVE'
            rental.started_at = timezone.now()
            rental.payment_status = 'PAID' if package.payment_model == 'PREPAID' else 'PENDING'
            rental.save(update_fields=['status', 'started_at', 'payment_status'])
            
            # Schedule reminder notification (15 minutes before due)
            reminder_time = rental.due_at - timezone.timedelta(minutes=15)
            if reminder_time > timezone.now():
                from api.notifications.tasks import send_notification_task
                send_notification_task.apply_async(
                    args=[str(user.id), 'rental_reminder', {
                        'rental_id': str(rental.id),
                        'rental_code': rental.rental_code,
                        'due_time': rental.due_at.strftime('%H:%M')
                    }],
                    eta=reminder_time
                )
            
            # Send rental start notification using clean API
            from api.notifications.services import notify
            notify(
                user,
                'rental_started',
                async_send=True,
                powerbank_serial=power_bank.serial_number,
                station_name=station.station_name,
                rental_duration=24
            )
            
            self.log_info(f"Rental started: {rental.rental_code} by {user.username}")
            return rental
            
        except Exception as e:
            self.handle_service_error(e, "Failed to start rental")
    
    def _validate_rental_prerequisites(self, user) -> None:
        """Validate user can start rental"""
        permission = CanRentPowerBank()
        
        # Mock request object for permission check
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(user)
        
        if not permission.has_permission(mock_request, None):
            raise ServiceException(
                detail="User does not meet rental requirements",
                code="rental_prerequisites_not_met"
            )
        
        # Check for active rental
        active_rental = Rental.objects.filter(
            user=user,
            status__in=['PENDING', 'ACTIVE']
        ).first()
        
        if active_rental:
            raise ServiceException(
                detail="You already have an active rental",
                code="active_rental_exists"
            )
    
    def _validate_station_availability(self, station: Station) -> None:
        """Validate station is available for rental"""
        if station.status != 'ONLINE':
            raise ServiceException(
                detail="Station is not online",
                code="station_offline"
            )
        
        if station.is_maintenance:
            raise ServiceException(
                detail="Station is under maintenance",
                code="station_maintenance"
            )
    
    def _get_available_power_bank_and_slot(self, station: Station) -> Tuple[PowerBank, StationSlot]:
        """Get available power bank and slot from station"""
        # Find available slot with good battery level
        available_slot = station.slots.filter(
            status='AVAILABLE'
        ).order_by('-battery_level').first()
        
        if not available_slot:
            raise ServiceException(
                detail="No available slots at this station",
                code="no_available_slots"
            )
        
        # Find power bank in the slot
        power_bank = PowerBank.objects.filter(
            current_station=station,
            current_slot=available_slot,
            status='AVAILABLE',
            battery_level__gte=20  # Minimum 20% battery
        ).first()
        
        if not power_bank:
            raise ServiceException(
                detail="No power bank available with sufficient battery",
                code="no_power_bank_available"
            )
        
        return power_bank, available_slot
    
    def _process_prepayment(self, user, package: RentalPackage) -> None:
        """Process pre-payment for rental"""
        from api.payments.services import PaymentCalculationService, RentalPaymentService
        
        # Calculate payment options
        calc_service = PaymentCalculationService()
        payment_options = calc_service.calculate_payment_options(
            user=user,
            scenario='pre_payment',
            package_id=str(package.id),
            amount=package.price
        )
        
        if not payment_options['is_sufficient']:
            raise ServiceException(
                detail=f"Insufficient balance. Need NPR {payment_options['shortfall']} more.",
                code="insufficient_balance"
            )
        
        # Process payment
        payment_service = RentalPaymentService()
        payment_service.process_rental_payment(
            user=user,
            rental=None,  # Will be set after rental creation
            payment_breakdown=payment_options['payment_breakdown']
        )
    
    @transaction.atomic
    def cancel_rental(self, rental_id: str, user, reason: str = "") -> Rental:
        """Cancel an active rental"""
        try:
            rental = Rental.objects.get(id=rental_id, user=user)
            
            if rental.status not in ['PENDING', 'ACTIVE']:
                raise ServiceException(
                    detail="Rental cannot be cancelled in current status",
                    code="invalid_rental_status"
                )
            
            # Check if rental can be cancelled (e.g., within 5 minutes of start)
            if rental.started_at:
                time_since_start = timezone.now() - rental.started_at
                if time_since_start.total_seconds() > 300:  # 5 minutes
                    raise ServiceException(
                        detail="Rental can only be cancelled within 5 minutes of start",
                        code="cancellation_time_expired"
                    )
            
            # Update rental status
            rental.status = 'CANCELLED'
            rental.ended_at = timezone.now()
            rental.rental_metadata['cancellation_reason'] = reason
            rental.save(update_fields=['status', 'ended_at', 'rental_metadata'])
            
            # Release power bank and slot
            if rental.power_bank:
                rental.power_bank.status = 'AVAILABLE'
                rental.power_bank.save(update_fields=['status'])
            
            if rental.slot:
                rental.slot.status = 'AVAILABLE'
                rental.slot.current_rental = None
                rental.slot.save(update_fields=['status', 'current_rental'])
            
            # Process refund for pre-paid rentals
            if rental.payment_status == 'PAID' and rental.amount_paid > 0:
                from api.payments.services import WalletService
                wallet_service = WalletService()
                wallet_service.add_balance(
                    user=user,
                    amount=rental.amount_paid,
                    description=f"Refund for cancelled rental {rental.rental_code}"
                )
            
            self.log_info(f"Rental cancelled: {rental.rental_code}")
            return rental
            
        except Rental.DoesNotExist:
            raise ServiceException(
                detail="Rental not found",
                code="rental_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to cancel rental")
    
    @transaction.atomic
    def extend_rental(self, rental_id: str, user, package_id: str) -> RentalExtension:
        """Extend rental duration"""
        try:
            rental = Rental.objects.get(id=rental_id, user=user)
            package = RentalPackage.objects.get(id=package_id, is_active=True)
            
            if rental.status != 'ACTIVE':
                raise ServiceException(
                    detail="Only active rentals can be extended",
                    code="invalid_rental_status"
                )
            
            # Check payment for extension
            from api.payments.services import PaymentCalculationService, RentalPaymentService
            
            calc_service = PaymentCalculationService()
            payment_options = calc_service.calculate_payment_options(
                user=user,
                scenario='pre_payment',
                package_id=package_id
            )
            
            if not payment_options['is_sufficient']:
                raise ServiceException(
                    detail=f"Insufficient balance for extension. Need NPR {payment_options['shortfall']} more.",
                    code="insufficient_balance"
                )
            
            # Process payment
            payment_service = RentalPaymentService()
            payment_service.process_rental_payment(
                user=user,
                rental=rental,
                payment_breakdown=payment_options['payment_breakdown']
            )
            
            # Create extension record
            extension = RentalExtension.objects.create(
                rental=rental,
                package=package,
                created_by=user,
                extended_minutes=package.duration_minutes,
                extension_cost=package.price
            )
            
            # Update rental due time
            rental.due_at += timezone.timedelta(minutes=package.duration_minutes)
            rental.amount_paid += package.price
            rental.save(update_fields=['due_at', 'amount_paid'])
            
            self.log_info(f"Rental extended: {rental.rental_code} by {package.duration_minutes} minutes")
            return extension
            
        except (Rental.DoesNotExist, RentalPackage.DoesNotExist):
            raise ServiceException(
                detail="Rental or package not found",
                code="not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to extend rental")
    
    @transaction.atomic
    def return_power_bank(self, rental_id: str, return_station_sn: str, 
                         return_slot_number: int, battery_level: int = 50) -> Rental:
        """Return power bank to station (Internal use - triggered by hardware)"""
        try:
            rental = Rental.objects.get(id=rental_id, status='ACTIVE')
            return_station = Station.objects.get(serial_number=return_station_sn)
            return_slot = return_station.slots.get(slot_number=return_slot_number)
            
            # End rental
            rental.status = 'COMPLETED'
            rental.ended_at = timezone.now()
            rental.return_station = return_station
            
            # Check if returned on time
            rental.is_returned_on_time = rental.ended_at <= rental.due_at
            
            # Calculate overdue charges for post-payment model
            if rental.package.payment_model == 'POSTPAID':
                self._calculate_postpayment_charges(rental)
            elif not rental.is_returned_on_time:
                self._calculate_overdue_charges(rental)
            
            rental.save(update_fields=[
                'status', 'ended_at', 'return_station', 'is_returned_on_time',
                'overdue_amount', 'payment_status'
            ])
            
            # Return power bank to station
            from api.stations.services import PowerBankService
            powerbank_service = PowerBankService()
            powerbank_service.return_power_bank(
                rental.power_bank, return_station, return_slot
            )
            
            # Award completion points
            from api.points.services import award_points
            award_points(
                rental.user,
                50,  # Standard rental completion points
                'RENTAL',
                'Rental completion reward',
                async_send=True,
                rental_id=str(rental.id),
                on_time=rental.is_returned_on_time
            )
            
            # Send completion notification
            from api.notifications.services import notify
            notify(
                rental.user,
                'rental_completed',
                async_send=True,
                powerbank_serial=rental.power_bank.serial_number,
                amount_paid=float(rental.amount_paid),
                rental_code=rental.rental_code
            )
            
            self.log_info(f"Power bank returned: {rental.rental_code}")
            return rental
            
        except Exception as e:
            self.handle_service_error(e, "Failed to return power bank")
    
    def _calculate_postpayment_charges(self, rental: Rental) -> None:
        """Calculate charges for post-payment model"""
        if not rental.ended_at or not rental.started_at:
            return
        
        # Calculate actual usage time
        usage_duration = rental.ended_at - rental.started_at
        usage_minutes = int(usage_duration.total_seconds() / 60)
        
        # Calculate cost based on package rate
        package_rate_per_minute = rental.package.price / rental.package.duration_minutes
        total_cost = Decimal(str(usage_minutes)) * package_rate_per_minute
        
        rental.amount_paid = total_cost
        rental.payment_status = 'PENDING'
    
    def _calculate_overdue_charges(self, rental: Rental) -> None:
        """Calculate overdue charges for late returns"""
        if rental.is_returned_on_time or not rental.ended_at:
            return
        
        # Calculate overdue time using configurable rates
        from api.common.utils.helpers import calculate_overdue_minutes, calculate_late_fee_amount, get_package_rate_per_minute
        overdue_minutes = calculate_overdue_minutes(rental)
        package_rate_per_minute = get_package_rate_per_minute(rental.package)
        rental.overdue_amount = calculate_late_fee_amount(package_rate_per_minute, overdue_minutes)
        
        if rental.overdue_amount > 0:
            rental.payment_status = 'PENDING'
    
    def get_user_rentals(self, user, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get user's rental history with filters"""
        try:
            queryset = Rental.objects.filter(user=user).select_related(
                'station', 'return_station', 'package', 'power_bank'
            )
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                if filters.get('payment_status'):
                    queryset = queryset.filter(payment_status=filters['payment_status'])
                
                if filters.get('start_date'):
                    queryset = queryset.filter(created_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(created_at__lte=filters['end_date'])
                
                if filters.get('station_id'):
                    queryset = queryset.filter(station_id=filters['station_id'])
            
            # Order by latest first
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user rentals")
    
    def get_active_rental(self, user) -> Optional[Rental]:
        """Get user's active rental"""
        try:
            return Rental.objects.filter(
                user=user,
                status__in=['PENDING', 'ACTIVE']
            ).select_related('station', 'package', 'power_bank').first()
        except Exception as e:
            self.handle_service_error(e, "Failed to get active rental")
    
    def get_rental_stats(self, user) -> Dict[str, Any]:
        """Get user's rental statistics"""
        try:
            rentals = Rental.objects.filter(user=user)
            
            # Basic counts
            total_rentals = rentals.count()
            completed_rentals = rentals.filter(status='COMPLETED').count()
            active_rentals = rentals.filter(status__in=['PENDING', 'ACTIVE']).count()
            cancelled_rentals = rentals.filter(status='CANCELLED').count()
            
            # Financial stats
            total_spent = rentals.filter(payment_status='PAID').aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal('0')
            
            # Time stats
            completed_with_time = rentals.filter(
                status='COMPLETED',
                started_at__isnull=False,
                ended_at__isnull=False
            )
            
            total_time_used = 0
            if completed_with_time.exists():
                for rental in completed_with_time:
                    duration = rental.ended_at - rental.started_at
                    total_time_used += int(duration.total_seconds() / 60)
            
            average_duration = total_time_used / completed_rentals if completed_rentals > 0 else 0
            
            # Return stats
            timely_returns = rentals.filter(is_returned_on_time=True).count()
            late_returns = completed_rentals - timely_returns
            timely_return_rate = (timely_returns / completed_rentals * 100) if completed_rentals > 0 else 0
            
            # Favorites
            favorite_station = rentals.values('station__station_name').annotate(
                count=Count('id')
            ).order_by('-count').first()
            
            favorite_package = rentals.values('package__name').annotate(
                count=Count('id')
            ).order_by('-count').first()
            
            # Dates
            first_rental = rentals.order_by('created_at').first()
            last_rental = rentals.order_by('-created_at').first()
            
            return {
                'total_rentals': total_rentals,
                'completed_rentals': completed_rentals,
                'active_rentals': active_rentals,
                'cancelled_rentals': cancelled_rentals,
                'total_spent': total_spent,
                'total_time_used': total_time_used,
                'average_rental_duration': round(average_duration, 1),
                'timely_returns': timely_returns,
                'late_returns': late_returns,
                'timely_return_rate': round(timely_return_rate, 1),
                'favorite_station': favorite_station['station__station_name'] if favorite_station else None,
                'favorite_package': favorite_package['package__name'] if favorite_package else None,
                'first_rental_date': first_rental.created_at if first_rental else None,
                'last_rental_date': last_rental.created_at if last_rental else None
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get rental stats")


class RentalIssueService(CRUDService):
    """Service for rental issue operations"""
    model = RentalIssue
    
    @transaction.atomic
    def report_issue(self, rental_id: str, user, validated_data: Dict[str, Any]) -> RentalIssue:
        """Report issue with rental"""
        try:
            rental = Rental.objects.get(id=rental_id, user=user)
            
            issue = RentalIssue.objects.create(
                rental=rental,
                **validated_data
            )
            
            # Send notification to admin
            from api.notifications.services import notify_bulk
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            
            # Send bulk notification to all admins
            notify_bulk(
                admin_users,
                'rental_issue_reported',
                async_send=True,
                rental_code=rental.rental_code,
                issue_type=issue.get_issue_type_display(),
                user_name=user.username
            )
            
            self.log_info(f"Rental issue reported: {rental.rental_code} - {issue.issue_type}")
            return issue
            
        except Rental.DoesNotExist:
            raise ServiceException(
                detail="Rental not found",
                code="rental_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to report rental issue")


class RentalLocationService(CRUDService):
    """Service for rental location tracking"""
    model = RentalLocation
    
    @transaction.atomic
    def update_location(self, rental_id: str, user, latitude: float, 
                       longitude: float, accuracy: float = 10.0) -> RentalLocation:
        """Update rental location"""
        try:
            rental = Rental.objects.get(id=rental_id, user=user, status='ACTIVE')
            
            location = RentalLocation.objects.create(
                rental=rental,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy
            )
            
            self.log_info(f"Location updated for rental: {rental.rental_code}")
            return location
            
        except Rental.DoesNotExist:
            raise ServiceException(
                detail="Active rental not found",
                code="rental_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to update rental location")


class RentalAnalyticsService(BaseService):
    """Service for rental analytics"""
    
    def get_rental_analytics(self, date_range: Tuple = None) -> Dict[str, Any]:
        """Get comprehensive rental analytics"""
        try:
            if date_range:
                start_date, end_date = date_range
            else:
                # Default to last 30 days
                end_date = timezone.now()
                start_date = end_date - timezone.timedelta(days=30)
            
            rentals = Rental.objects.filter(created_at__range=(start_date, end_date))
            
            # Basic counts
            total_rentals = rentals.count()
            active_rentals = rentals.filter(status='ACTIVE').count()
            completed_rentals = rentals.filter(status='COMPLETED').count()
            cancelled_rentals = rentals.filter(status='CANCELLED').count()
            overdue_rentals = rentals.filter(status='OVERDUE').count()
            
            # Revenue
            total_revenue = rentals.filter(payment_status='PAID').aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal('0')
            
            # Duration stats
            completed_with_duration = rentals.filter(
                status='COMPLETED',
                started_at__isnull=False,
                ended_at__isnull=False
            )
            
            if completed_with_duration.exists():
                durations = []
                for rental in completed_with_duration:
                    duration = rental.ended_at - rental.started_at
                    durations.append(duration.total_seconds() / 60)
                
                average_duration = sum(durations) / len(durations)
            else:
                average_duration = 0
            
            # Return rate
            timely_returns = rentals.filter(is_returned_on_time=True).count()
            timely_return_rate = (timely_returns / completed_rentals * 100) if completed_rentals > 0 else 0
            
            # Popular packages
            popular_packages = list(rentals.values('package__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5])
            
            # Popular stations
            popular_stations = list(rentals.values('station__station_name').annotate(
                count=Count('id')
            ).order_by('-count')[:5])
            
            return {
                'total_rentals': total_rentals,
                'active_rentals': active_rentals,
                'completed_rentals': completed_rentals,
                'cancelled_rentals': cancelled_rentals,
                'overdue_rentals': overdue_rentals,
                'total_revenue': total_revenue,
                'average_rental_duration': round(average_duration, 1),
                'timely_return_rate': round(timely_return_rate, 1),
                'popular_packages': popular_packages,
                'popular_stations': popular_stations,
                'hourly_breakdown': [],  # Can be implemented if needed
                'daily_breakdown': [],   # Can be implemented if needed
                'monthly_breakdown': []  # Can be implemented if needed
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get rental analytics")