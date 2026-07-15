"""Configurazione dell'app rentals usata da Django."""

from django.apps import AppConfig


# Identifica l'applicazione rentals nella configurazione generale di Django.
class RentalsConfig(AppConfig):
    # Configurazione dell'app mostrata anche nel Django Admin.
    default_auto_field = "django.db.models.BigAutoField"
    name = "rentals"
    verbose_name = "Noleggio attrezzature"
