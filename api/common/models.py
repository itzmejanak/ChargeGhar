from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Base model with common fields for all models
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Country(BaseModel):
    """
    Country - Countries with dialing codes
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ISO country code
    dial_code = models.CharField(max_length=10)
    flag_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "countries"
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return self.name


class MediaUpload(BaseModel):
    """
    MediaUpload - Uploaded media files
    """
    MEDIA_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
    ]

    file_url = models.URLField()
    file_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES)
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "media_uploads"
        verbose_name = "Media Upload"
        verbose_name_plural = "Media Uploads"

    def __str__(self):
        return self.original_name