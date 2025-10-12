from __future__ import annotations

import random
import string
from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Sum, Q


from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset
from api.promotions.models import Coupon, CouponUsage


class CouponService(CRUDService):
    """Service for coupon operations"""
    model = Coupon
    
    def get_active_coupons(self) -> List[Coupon]:
        """Get currently active and valid coupons"""
        try:
            now = timezone.now()
            coupons = Coupon.objects.filter(
                status=Coupon.StatusChoices.ACTIVE,
                valid_from__lte=now,
                valid_until__gte=now
            ).order_by('-points_value')
            
            return coupons

        except Exception as e:
            self.log_error(f"Failed to get active coupons: {str(e)}")
            return []
    
    def validate_coupon(self, coupon_code: str, user) -> Dict[str, Any]:
        """Validate if a coupon can be used by the user"""
        try:
            # Convert code to uppercase and strip whitespace
            coupon_code = coupon_code.strip().upper()
            
            coupon = Coupon.objects.select_related().get(code=coupon_code)
            
            now = timezone.now()
            
            # Check if coupon exists and is active
            if not coupon or coupon.status != Coupon.StatusChoices.ACTIVE:
                return {
                    'valid': False,
                    'coupon_code': coupon_code,
                    'points_value': 0,
                    'message': 'Invalid or inactive coupon code',
                    'can_use': False,
                    'uses_remaining': 0
                }
            
            # Check date validity
            if now < coupon.valid_from or now > coupon.valid_until:
                return {
                    'valid': False,
                    'coupon_code': coupon_code,
                    'points_value': 0,
                    'message': 'Coupon has expired or is not yet valid',
                    'can_use': False,
                    'uses_remaining': 0
                }
            
            # Check user's usage count
            user_usage_count = CouponUsage.objects.filter(
                coupon=coupon,
                user=user
            ).count()
            
            uses_remaining = max(0, coupon.max_uses_per_user - user_usage_count)
            
            if uses_remaining <= 0:
                return {
                    'valid': True,
                    'coupon_code': coupon_code,
                    'points_value': coupon.points_value,
                    'message': 'You have already used this coupon the maximum number of times',
                    'can_use': False,
                    'uses_remaining': 0
                }
            
            return {
                'valid': True,
                'coupon_code': coupon_code,
                'points_value': coupon.points_value,
                'message': f'Coupon is valid! You will receive {coupon.points_value} points.',
                'can_use': True,
                'uses_remaining': uses_remaining
            }
            
        except Coupon.DoesNotExist:
            return {
                'valid': False,
                'coupon_code': coupon_code,
                'points_value': 0,
                'message': 'Invalid coupon code',
                'can_use': False,
                'uses_remaining': 0
            }
        except Exception as e:
            self.log_error(f"Failed to validate coupon: {str(e)}")
            raise ServiceException("Failed to validate coupon")
    
    @transaction.atomic
    def apply_coupon(self, coupon_code: str, user) -> Dict[str, Any]:
        """Apply coupon and award points to user"""
        try:
            # First validate the coupon
            validation = self.validate_coupon(coupon_code, user)
            
            if not validation['can_use']:
                raise ServiceException(
                    detail=validation['message'],
                    code="coupon_not_usable"
                )
            
            coupon = Coupon.objects.get(code=coupon_code.upper())
            
            # Create coupon usage record
            coupon_usage = CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                points_awarded=coupon.points_value
            )
            
            # Award points to user
            from api.points.services import PointsService
            points_service = PointsService()
            
            points_service.award_points(
                user=user,
                points=coupon.points_value,
                source='COUPON',
                description=f'Coupon applied: {coupon.name}',
                metadata={
                    'coupon_code': coupon.code,
                    'coupon_usage_id': str(coupon_usage.id)
                }
            )
            
            # Send coupon notification asynchronously via task
            from api.notifications.tasks import send_push_notification_task
            send_push_notification_task.delay(
                str(user.id),
                "🎉 Coupon Applied!",
                f"You've successfully applied coupon '{coupon.code}' and received {coupon.points_value} points!"
            )
            
            self.log_info(f"Coupon applied: {coupon.code} by {user.username}")
            
            return {
                'success': True,
                'coupon_code': coupon.code,
                'coupon_name': coupon.name,
                'points_awarded': coupon.points_value,
                'message': f'Coupon applied successfully! You received {coupon.points_value} points.'
            }
            
        except Coupon.DoesNotExist:
            raise ServiceException(
                detail="Invalid coupon code",
                code="invalid_coupon"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to apply coupon")
    
    def get_user_coupon_history(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get user's coupon usage history"""
        try:
            queryset = CouponUsage.objects.filter(user=user).select_related('coupon')
            queryset = queryset.order_by('-used_at')
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user coupon history")
    
    @transaction.atomic
    def create_coupon(self, code: str, name: str, points_value: int, max_uses_per_user: int,
                     valid_from: timezone.datetime, valid_until: timezone.datetime,
                     admin_user) -> Coupon:
        """Create new coupon (Admin)"""
        try:
            coupon = Coupon.objects.create(
                code=code.upper(),
                name=name,
                points_value=points_value,
                max_uses_per_user=max_uses_per_user,
                valid_from=valid_from,
                valid_until=valid_until,
                status=Coupon.StatusChoices.ACTIVE
            )
            
            # Cache clearing moved to view decorators
            
            # Log admin action
            from api.admin_panel.models import AdminActionLog
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='CREATE_COUPON',
                target_model='Coupon',
                target_id=str(coupon.id),
                changes={
                    'code': code,
                    'name': name,
                    'points_value': points_value,
                    'max_uses_per_user': max_uses_per_user
                },
                description=f"Created coupon: {code}",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Coupon created: {code}")
            return coupon
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create coupon")
    
    @transaction.atomic
    def bulk_create_coupons(self, name_prefix: str, points_value: int, max_uses_per_user: int,
                           valid_from: timezone.datetime, valid_until: timezone.datetime,
                           quantity: int, code_length: int, admin_user) -> List[Coupon]:
        """Bulk create coupons (Admin)"""
        try:
            created_coupons = []
            
            for i in range(quantity):
                # Generate unique code
                while True:
                    code = self._generate_coupon_code(code_length)
                    if not Coupon.objects.filter(code=code).exists():
                        break
                
                coupon = Coupon(
                    code=code,
                    name=f"{name_prefix} #{i+1}",
                    points_value=points_value,
                    max_uses_per_user=max_uses_per_user,
                    valid_from=valid_from,
                    valid_until=valid_until,
                    status=Coupon.StatusChoices.ACTIVE
                )
                created_coupons.append(coupon)
            
            # Bulk create
            Coupon.objects.bulk_create(created_coupons)
            
            # Cache clearing moved to view decorators
            
            # Log admin action
            from api.admin_panel.models import AdminActionLog
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='BULK_CREATE_COUPONS',
                target_model='Coupon',
                target_id='bulk',
                changes={
                    'name_prefix': name_prefix,
                    'points_value': points_value,
                    'quantity': quantity
                },
                description=f"Bulk created {quantity} coupons",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Bulk created {quantity} coupons with prefix: {name_prefix}")
            return created_coupons
            
        except Exception as e:
            self.handle_service_error(e, "Failed to bulk create coupons")
    
    def _generate_coupon_code(self, length: int) -> str:
        """Generate random coupon code"""
        characters = string.ascii_uppercase + string.digits
        # Exclude confusing characters
        characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1')
        return ''.join(random.choices(characters, k=length))
    
    def get_coupons_list(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get paginated list of coupons with filters (Admin)"""
        try:
            queryset = Coupon.objects.all()
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(code__icontains=search_term) |
                        Q(name__icontains=search_term)
                    )
                
                if filters.get('start_date'):
                    queryset = queryset.filter(valid_from__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(valid_until__lte=filters['end_date'])
            
            # Order by latest first
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get coupons list")


class PromotionAnalyticsService(BaseService):
    """Service for promotion analytics"""
    
    def get_coupon_analytics(self) -> Dict[str, Any]:
        """Get comprehensive coupon analytics"""
        try:
            # Basic counts
            total_coupons = Coupon.objects.count()
            active_coupons = Coupon.objects.filter(status=Coupon.StatusChoices.ACTIVE).count()
            expired_coupons = Coupon.objects.filter(status=Coupon.StatusChoices.EXPIRED).count()
            
            # Usage statistics
            total_uses = CouponUsage.objects.count()
            total_points_awarded = CouponUsage.objects.aggregate(
                total=Sum('points_awarded')
            )['total'] or 0
            
            # Most used coupons
            most_used = Coupon.objects.annotate(
                usage_count=Count('usages')
            ).order_by('-usage_count')[:5]
            
            most_used_coupons = [
                {
                    'code': coupon.code,
                    'name': coupon.name,
                    'usage_count': coupon.usage_count,
                    'points_value': coupon.points_value
                }
                for coupon in most_used
            ]
            
            # Daily usage for last 7 days
            daily_usage = []
            for i in range(7):
                date = timezone.now().date() - timezone.timedelta(days=i)
                usage_count = CouponUsage.objects.filter(
                    used_at__date=date
                ).count()
                
                daily_usage.append({
                    'date': date.isoformat(),
                    'usage_count': usage_count
                })
            
            daily_usage.reverse()  # Show oldest to newest
            
            # User engagement
            unique_users = CouponUsage.objects.values('user').distinct().count()
            avg_uses_per_user = total_uses / unique_users if unique_users > 0 else 0
            
            return {
                'total_coupons': total_coupons,
                'active_coupons': active_coupons,
                'expired_coupons': expired_coupons,
                'total_uses': total_uses,
                'total_points_awarded': total_points_awarded,
                'most_used_coupons': most_used_coupons,
                'daily_usage': daily_usage,
                'unique_users': unique_users,
                'average_uses_per_user': round(avg_uses_per_user, 2),
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get coupon analytics")
    
    def get_coupon_performance(self, coupon_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific coupon"""
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            
            # Usage statistics
            usages = CouponUsage.objects.filter(coupon=coupon)
            total_uses = usages.count()
            total_points_awarded = usages.aggregate(
                total=Sum('points_awarded')
            )['total'] or 0
            
            # Usage over time
            usage_timeline = []
            for usage in usages.order_by('used_at')[:50]:  # Last 50 uses
                usage_timeline.append({
                    'used_at': usage.used_at,
                    'user_id': str(usage.user.id),
                    'points_awarded': usage.points_awarded
                })
            
            # Unique users
            unique_users = usages.values('user').distinct().count()
            
            return {
                'coupon_code': coupon.code,
                'coupon_name': coupon.name,
                'total_uses': total_uses,
                'total_points_awarded': total_points_awarded,
                'unique_users': unique_users,
                'usage_timeline': usage_timeline,
                'max_possible_uses': coupon.max_uses_per_user,
                'points_per_use': coupon.points_value
            }
            
        except Coupon.DoesNotExist:
            raise ServiceException(
                detail="Coupon not found",
                code="coupon_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get coupon performance")