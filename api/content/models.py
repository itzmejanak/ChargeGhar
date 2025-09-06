from __future__ import annotations

from django.db import models
from api.common.models import BaseModel


class ContentPage(BaseModel):
    """
    ContentPage - Static content pages like Terms, Privacy Policy, etc.
    """
    
    class PageTypeChoices(models.TextChoices):
        TERMS_OF_SERVICE = 'terms-of-service', 'Terms of Service'
        PRIVACY_POLICY = 'privacy-policy', 'Privacy Policy'
        ABOUT = 'about', 'About Us'
        CONTACT = 'contact', 'Contact Us'
        FAQ = 'faq', 'FAQ'
    
    page_type = models.CharField(max_length=255, choices=PageTypeChoices.choices, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "content_pages"
        verbose_name = "Content Page"
        verbose_name_plural = "Content Pages"
    
    def __str__(self):
        return self.title


class FAQ(BaseModel):
    """
    FAQ - Frequently Asked Questions
    """
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_faqs')
    updated_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='updated_faqs')
    
    class Meta:
        db_table = "faqs"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['category', 'sort_order']
    
    def __str__(self):
        return self.question[:100]


class ContactInfo(BaseModel):
    """
    ContactInfo - Contact information like phone, email, address
    """
    
    class InfoTypeChoices(models.TextChoices):
        PHONE = 'phone', 'Phone'
        EMAIL = 'email', 'Email'
        ADDRESS = 'address', 'Address'
        SUPPORT_HOURS = 'support_hours', 'Support Hours'
    
    info_type = models.CharField(max_length=255, choices=InfoTypeChoices.choices, unique=True)
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='updated_contact_info')
    
    class Meta:
        db_table = "contact_info"
        verbose_name = "Contact Info"
        verbose_name_plural = "Contact Info"
    
    def __str__(self):
        return f"{self.get_info_type_display()}: {self.value}"
        
    
class Banner(BaseModel):
    """
    Banner - Promotional banners for the app
    """
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField()
    redirect_url = models.URLField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    class Meta:
        db_table = "banners"
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.title