from django.apps import AppConfig


class UserProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user_profile'
    def ready(self):
        # Import your signals here to ensure they are registered when the app loads
        import apps.user_profile.signals
