"""Configurazione WSGI generata da Django per l'avvio su server web tradizionali."""

import os

from django.core.wsgi import get_wsgi_application


# Configurazione WSGI standard generata da Django per server compatibili.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sport_rental.settings")
# Oggetto WSGI esposto a un server web tradizionale.
application = get_wsgi_application()
