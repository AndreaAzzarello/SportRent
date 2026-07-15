"""Configurazione ASGI generata da Django per server asincroni."""

import os

from django.core.asgi import get_asgi_application


# Configurazione ASGI standard generata da Django.
# Nella demo locale il progetto viene avviato con runserver.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sport_rental.settings")
# Oggetto ASGI esposto a un server che gestisce richieste asincrone.
application = get_asgi_application()
