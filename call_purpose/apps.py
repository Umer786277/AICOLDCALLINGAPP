from django.apps import AppConfig


class CallPurposeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'call_purpose'

    def ready(self):
        import call_purpose.signals

