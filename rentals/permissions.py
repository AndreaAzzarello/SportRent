"""Regole semplici per distinguere clienti, gestori, staff e superuser."""

from django.contrib.auth.decorators import user_passes_test


# Nomi dei gruppi Django usati per distinguere clienti e gestori.
NOME_GRUPPO_CLIENTI = "Clienti"
NOME_GRUPPO_GESTORI = "Gestori"


# Restituisce vero quando l'utente ha accesso all'area di gestione.
def utente_e_gestore(user):
    # Il pannello applicativo è disponibile al gruppo Gestori e, per
    # compatibilità con Django Admin, anche a staff e superuser.
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name=NOME_GRUPPO_GESTORI).exists()
        )
    )


# Decoratore pronto da usare sulle viste riservate ai gestori.
gestore_richiesto = user_passes_test(utente_e_gestore)
