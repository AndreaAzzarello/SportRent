"""Collegamenti URL dell'app rentals verso catalogo, prenotazioni e area gestore."""

from django.urls import path

from . import views


# Rotte dell'app: catalogo pubblico, prenotazioni cliente e area gestore.
# Indirizzi pubblici del catalogo e della registrazione delle prenotazioni.
urlpatterns = [
    path("", views.catalogo_attrezzature, name="equipment_list"),
    path(
        "attrezzature/<int:pk>/",
        views.dettaglio_attrezzatura,
        name="equipment_detail",
    ),
    path(
        "prenotazioni/nuova/",
        views.nuova_prenotazione,
        name="reservation_create",
    ),
    path(
        "prenotazioni/",
        views.storico_prenotazioni,
        name="reservation_history",
    ),
    path(
        "prenotazioni/<int:pk>/",
        views.dettaglio_prenotazione,
        name="reservation_detail",
    ),
    path(
        "prenotazioni/<int:pk>/cancella/",
        views.cancella_prenotazione,
        name="reservation_cancel",
    ),
    path(
        "gestione/",
        views.pannello_gestore,
        name="manager_dashboard",
    ),
    path(
        "gestione/attrezzature/",
        views.elenco_attrezzature_gestore,
        name="manager_equipment_list",
    ),
    path(
        "gestione/attrezzature/nuova/",
        views.crea_attrezzatura_gestore,
        name="manager_equipment_create",
    ),
    path(
        "gestione/attrezzature/<int:pk>/modifica/",
        views.modifica_attrezzatura_gestore,
        name="manager_equipment_update",
    ),
    path(
        "gestione/tipologie/",
        views.elenco_categorie_gestore,
        name="manager_category_list",
    ),
    path(
        "gestione/tipologie/nuova/",
        views.crea_categoria_gestore,
        name="manager_category_create",
    ),
    path(
        "gestione/tipologie/<int:pk>/modifica/",
        views.modifica_categoria_gestore,
        name="manager_category_update",
    ),
    path(
        "gestione/prenotazioni/",
        views.elenco_prenotazioni_gestore,
        name="manager_reservation_list",
    ),
]
