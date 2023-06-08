"""Apps of project."""

from django.apps import AppConfig


class BankAppConfig(AppConfig):
    """Config polls.

    Args:
        AppConfig (_type_): _description_
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_app'

    def ready(self):
        """Import signals in bank_app."""
        import bank_app.signals
