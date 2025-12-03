from __future__ import annotations

from django.db import models
from api.common.models import BaseModel

class NotificationTemplate(BaseModel):
    """
    NotificationTemplate - Templates for different notification types
    """
    
    class NotificationTypeChoices(models.TextChoices):
        RENTAL = 'rental', 'Rental'
        PAYMENT = 'payment', 'Payment'
        PROMOTION = 'promotion', 'Promotion'
        SYSTEM = 'system', 'System'
        ACHIEVEMENT = 'achievement', 'Achievement'
        SECURITY = 'security', 'Security'
        POINTS = 'points', 'Points'
        UPDATE = 'update', 'Update'
        ADMIN = 'admin', 'Admin'
        OTP_SMS = 'otp_sms', 'OTP SMS'
        OTP_EMAIL = 'otp_email', 'OTP Email'
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    title_template = models.CharField(max_length=255)
    message_template = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NotificationTypeChoices.choices)
    description = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "notification_templates"
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
    
    def __str__(self):
        return self.name


class NotificationRule(BaseModel):
    """
    NotificationRule - Rules for which channels to send notifications
    """
    notification_type = models.CharField(max_length=255, unique=True)
    send_in_app = models.BooleanField(default=True)
    send_push = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    send_email = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    
    class Meta:
        db_table = "notification_rules"
        verbose_name = "Notification Rule"
        verbose_name_plural = "Notification Rules"
    
    def __str__(self):
        return f"Rule for {self.notification_type}"


class Notification(BaseModel):
    """
    Notification - Individual notifications sent to users
    """
    
    class NotificationTypeChoices(models.TextChoices):
        RENTAL = 'rental', 'Rental'
        PAYMENT = 'payment', 'Payment'
        PROMOTION = 'promotion', 'Promotion'
        SYSTEM = 'system', 'System'
        ACHIEVEMENT = 'achievement', 'Achievement'
        POINTS = 'points', 'Points'
        UPDATE = 'update', 'Update'
        ADMIN = 'admin', 'Admin'
        OTP_SMS = 'otp_sms', 'OTP SMS'
        OTP_EMAIL = 'otp_email', 'OTP Email'
    
    class ChannelChoices(models.TextChoices):
        IN_APP = 'in_app', 'In App'
        PUSH = 'push', 'Push'
        SMS = 'sms', 'SMS'
        EMAIL = 'email', 'Email'
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NotificationTypeChoices.choices)
    data = models.JSONField(default=dict)
    channel = models.CharField(max_length=50, choices=ChannelChoices.choices)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='notif_user_read_idx'),
            models.Index(fields=['user', '-created_at'], name='notif_user_created_idx'),
            models.Index(fields=['is_read', '-created_at'], name='notif_read_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class SMS_FCMLog(BaseModel):
    """
    SMS_FCMLog - Log of SMS and FCM notifications sent
    """
    
    class TypeChoices(models.TextChoices):
        FCM = 'fcm', 'FCM'
        SMS = 'sms', 'SMS'
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True, related_name='sms_fcm_logs')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TypeChoices.choices)
    recipient = models.CharField(max_length=255)  # phone number or FCM token
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    response = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "sms_fcm_logs"
        verbose_name = "SMS/FCM Log"
        verbose_name_plural = "SMS/FCM Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} to {self.recipient} - {self.status}"