from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache

from api.common.tasks.base import BaseTask
from api.promotions.models import Coupon, CouponUsage


@shared_task(base=BaseTask, bind=True)
def expire_old_coupons(self):
    """Mark expired coupons as expired"""
    try:
        now = timezone.now()
        
        # Find coupons that have passed their expiry date
        expired_coupons = Coupon.objects.filter(
            status=Coupon.StatusChoices.ACTIVE,
            valid_until__lt=now
        )
        
        updated_count = expired_coupons.update(status=Coupon.StatusChoices.EXPIRED)
        
        # Clear active coupons cache
        cache.delete("active_coupons")
        
        self.logger.info(f"Marked {updated_count} coupons as expired")
        return {'expired_count': updated_count}
        
    except Exception as e:
        self.logger.error(f"Failed to expire old coupons: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def cleanup_old_coupon_data(self):
    """Clean up old coupon usage data"""
    try:
        # Clean up usage records for expired coupons older than 1 year
        one_year_ago = timezone.now() - timezone.timedelta(days=365)
        
        old_usages = CouponUsage.objects.filter(
            coupon__status=Coupon.StatusChoices.EXPIRED,
            used_at__lt=one_year_ago
        )
        
        deleted_count = old_usages.delete()[0]
        
        self.logger.info(f"Cleaned up {deleted_count} old coupon usage records")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup old coupon data: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_promotion_analytics_report(self):
    """Generate promotion analytics report"""
    try:
        from api.promotions.services import PromotionAnalyticsService
        
        service = PromotionAnalyticsService()
        analytics = service.get_coupon_analytics()
        
        # Cache the analytics report
        cache.set('promotion_analytics', analytics, timeout=3600)  # 1 hour
        
        self.logger.info("Promotion analytics report generated")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate promotion analytics: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def send_coupon_expiry_reminders(self):
    """Send reminders for coupons expiring soon"""
    try:
        # Find coupons expiring in 3 days
        three_days_from_now = timezone.now() + timezone.timedelta(days=3)
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        
        expiring_coupons = Coupon.objects.filter(
            status=Coupon.StatusChoices.ACTIVE,
            valid_until__gte=tomorrow,
            valid_until__lte=three_days_from_now
        )
        
        from api.notifications.services import NotificationService
        notification_service = NotificationService()
        
        # Get users who haven't used these coupons
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        notifications_sent = 0
        
        for coupon in expiring_coupons:
            # Get users who haven't used this coupon
            users_who_used = CouponUsage.objects.filter(
                coupon=coupon
            ).values_list('user_id', flat=True)
            
            eligible_users = User.objects.filter(
                is_active=True,
                status='ACTIVE'
            ).exclude(id__in=users_who_used)[:100]  # Limit to 100 users per coupon
            
            for user in eligible_users:
                try:
                    notification_service.create_notification(
                        user=user,
                        title="⏰ Coupon Expiring Soon!",
                        message=f"Don't miss out! Coupon '{coupon.code}' expires in {(coupon.valid_until - timezone.now()).days} days. Use it now to get {coupon.points_value} points!",
                        notification_type='promotion',
                        data={
                            'coupon_code': coupon.code,
                            'coupon_name': coupon.name,
                            'points_value': coupon.points_value,
                            'expires_at': coupon.valid_until.isoformat(),
                            'action': 'apply_coupon'
                        }
                    )
                    notifications_sent += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to send coupon reminder to user {user.id}: {str(e)}")
        
        self.logger.info(f"Sent {notifications_sent} coupon expiry reminders")
        return {
            'expiring_coupons': expiring_coupons.count(),
            'notifications_sent': notifications_sent
        }
        
    except Exception as e:
        self.logger.error(f"Failed to send coupon expiry reminders: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def create_seasonal_coupons(self):
    """Create seasonal promotional coupons"""
    try:
        from api.promotions.services import CouponService
        
        # This would create special coupons for holidays, events, etc.
        # For now, create a monthly special coupon
        
        current_month = timezone.now().strftime('%B')
        coupon_code = f"{current_month.upper()[:3]}{timezone.now().year % 100}"
        
        # Check if monthly coupon already exists
        if Coupon.objects.filter(code=coupon_code).exists():
            return {'coupon_created': False, 'reason': 'Already exists'}
        
        service = CouponService()
        
        # Create monthly special coupon
        coupon = Coupon.objects.create(
            code=coupon_code,
            name=f"{current_month} Special",
            points_value=200,
            max_uses_per_user=1,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=30),
            status=Coupon.StatusChoices.ACTIVE
        )
        
        # Clear cache
        cache.delete("active_coupons")
        
        self.logger.info(f"Created seasonal coupon: {coupon_code}")
        return {
            'coupon_created': True,
            'coupon_code': coupon_code,
            'coupon_name': coupon.name
        }
        
    except Exception as e:
        self.logger.error(f"Failed to create seasonal coupons: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def analyze_coupon_performance(self):
    """Analyze coupon performance and send insights to admin"""
    try:
        from api.promotions.services import PromotionAnalyticsService
        
        service = PromotionAnalyticsService()
        analytics = service.get_coupon_analytics()
        
        # Identify underperforming coupons
        underperforming_coupons = []
        
        active_coupons = Coupon.objects.filter(status=Coupon.StatusChoices.ACTIVE)
        
        for coupon in active_coupons:
            usage_count = CouponUsage.objects.filter(coupon=coupon).count()
            days_active = (timezone.now() - coupon.valid_from).days + 1
            
            # Consider coupon underperforming if less than 1 use per day on average
            if days_active > 3 and usage_count / days_active < 1:
                underperforming_coupons.append({
                    'code': coupon.code,
                    'name': coupon.name,
                    'usage_count': usage_count,
                    'days_active': days_active,
                    'usage_rate': round(usage_count / days_active, 2)
                })
        
        # Send insights to admin if there are underperforming coupons
        if underperforming_coupons:
            from api.notifications.services import NotificationService
            notification_service = NotificationService()
            
            # Get admin users
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            
            for admin in admin_users:
                notification_service.create_notification(
                    user=admin,
                    title="📊 Coupon Performance Insights",
                    message=f"{len(underperforming_coupons)} coupons are underperforming. Consider reviewing their terms or promotion strategy.",
                    notification_type='system',
                    data={
                        'underperforming_coupons': underperforming_coupons,
                        'total_analytics': analytics,
                        'action': 'review_coupons'
                    }
                )
        
        self.logger.info(f"Analyzed coupon performance. {len(underperforming_coupons)} underperforming coupons found")
        return {
            'total_coupons_analyzed': active_coupons.count(),
            'underperforming_count': len(underperforming_coupons),
            'underperforming_coupons': underperforming_coupons
        }
        
    except Exception as e:
        self.logger.error(f"Failed to analyze coupon performance: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def refresh_promotion_cache(self):
    """Refresh promotion-related caches"""
    try:
        # Clear existing caches
        cache_keys = [
            "active_coupons",
            "promotion_analytics"
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        # Warm up active coupons cache
        from api.promotions.services import CouponService
        service = CouponService()
        service.get_active_coupons()
        
        # Warm up analytics cache
        from api.promotions.services import PromotionAnalyticsService
        analytics_service = PromotionAnalyticsService()
        analytics_service.get_coupon_analytics()
        
        self.logger.info("Promotion caches refreshed successfully")
        return {'status': 'success', 'caches_refreshed': len(cache_keys)}
        
    except Exception as e:
        self.logger.error(f"Failed to refresh promotion cache: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def send_new_coupon_notifications(self, coupon_id: str):
    """Send notifications about new coupons to eligible users"""
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        
        from api.notifications.services import NotificationService
        notification_service = NotificationService()
        
        # Get active users (limit to prevent spam)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        eligible_users = User.objects.filter(
            is_active=True,
            status='ACTIVE'
        )[:500]  # Limit to 500 users
        
        notifications_sent = 0
        
        for user in eligible_users:
            try:
                notification_service.create_notification(
                    user=user,
                    title="🎁 New Coupon Available!",
                    message=f"Use coupon '{coupon.code}' to get {coupon.points_value} points! Valid until {coupon.valid_until.strftime('%B %d, %Y')}.",
                    notification_type='promotion',
                    data={
                        'coupon_code': coupon.code,
                        'coupon_name': coupon.name,
                        'points_value': coupon.points_value,
                        'expires_at': coupon.valid_until.isoformat(),
                        'action': 'apply_coupon'
                    }
                )
                notifications_sent += 1
                
            except Exception as e:
                self.logger.error(f"Failed to send new coupon notification to user {user.id}: {str(e)}")
        
        self.logger.info(f"Sent new coupon notifications to {notifications_sent} users")
        return {
            'coupon_code': coupon.code,
            'notifications_sent': notifications_sent
        }
        
    except Coupon.DoesNotExist:
        self.logger.error(f"Coupon not found: {coupon_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send new coupon notifications: {str(e)}")
        raise