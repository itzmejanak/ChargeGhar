from django.apps import AppConfig


class SystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.system'
    verbose_name = 'System Configuration'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        pass
