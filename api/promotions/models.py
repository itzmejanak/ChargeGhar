from __future__ import annotations

from django.db import models
from api.common.models import BaseModel


class Coupon(BaseModel):
    """
    Coupon - Promotional coupons for points
    """
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        EXPIRED = 'expired', 'Expired'
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    points_value = models.IntegerField()
    max_uses_per_user = models.IntegerField(default=1)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    
    
    class Meta:
        db_table = "coupons"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CouponUsage(BaseModel):
    """
    CouponUsage - Track coupon usage by users
    """
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='coupon_usages')
    points_awarded = models.IntegerField()
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "coupon_usages"
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        unique_together = ['coupon', 'user']
    
    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"