from django.apps import AppConfig


class marketplaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "marketplace"

    # If you need to import signals or models, do it INSIDE the ready() method:
    # def ready(self):
    #     import marketplace.signals
