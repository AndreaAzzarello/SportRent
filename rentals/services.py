"""Funzioni di servizio con la logica principale di disponibilita e creazione prenotazioni."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Equipment, Reservation, ReservationItem


# Oggetto semplice usato per passare al service gli articoli richiesti.
@dataclass(frozen=True)
class AttrezzaturaRichiesta:
    id_attrezzatura: int
    quantita: int


# Somma gli articoli gia impegnati da noleggi confermati nello stesso periodo.
def calcola_quantita_prenotata(
    attrezzatura,
    data_inizio,
    data_fine,
    prenotazione_esclusa=None,
):
    # Due intervalli si sovrappongono quando l'inizio di uno non supera la
    # fine dell'altro e viceversa. Le prenotazioni cancellate non occupano disponibilita.
    righe_sovrapposte = ReservationItem.objects.filter(
        equipment=attrezzatura,
        reservation__status=Reservation.Status.CONFIRMED,
        reservation__start_date__lte=data_fine,
        reservation__end_date__gte=data_inizio,
    )
    if prenotazione_esclusa is not None:
        righe_sovrapposte = righe_sovrapposte.exclude(
            reservation=prenotazione_esclusa
        )

    risultato = righe_sovrapposte.aggregate(totale=Sum("quantity"))
    return risultato["totale"] or 0


# Sottrae gli articoli prenotati dalla quantita totale disponibile.
def calcola_quantita_disponibile(
    attrezzatura,
    data_inizio,
    data_fine,
    prenotazione_esclusa=None,
):
    quantita_prenotata = calcola_quantita_prenotata(
        attrezzatura,
        data_inizio,
        data_fine,
        prenotazione_esclusa=prenotazione_esclusa,
    )
    return max(attrezzatura.total_quantity - quantita_prenotata, 0)


# Racchiude la creazione in una sola operazione del database.
@transaction.atomic
# Controlla la richiesta e crea prenotazione e righe solo se tutto e valido.
def crea_prenotazione(utente, data_inizio, data_fine, attrezzature_richieste):
    # Le stesse regole principali vengono ricontrollate qui anche se il form le
    # valida gia: il service puo essere richiamato da viste, test o codice futuro.
    if data_inizio < timezone.localdate():
        raise ValidationError("La data di inizio non puo essere nel passato.")
    if data_fine < data_inizio:
        raise ValidationError(
            "La data di fine deve seguire quella di inizio."
        )

    attrezzature_richieste = [
        riga for riga in attrezzature_richieste if riga.quantita > 0
    ]
    if not attrezzature_richieste:
        raise ValidationError("Seleziona almeno un'attrezzatura.")

    id_attrezzature = [riga.id_attrezzatura for riga in attrezzature_richieste]
    # Il lock mantiene coerente la disponibilita se due richieste tentano di
    # prenotare contemporaneamente gli stessi articoli.
    attrezzature_per_id = {
        attrezzatura.pk: attrezzatura
        for attrezzatura in Equipment.objects.select_for_update().filter(
            pk__in=id_attrezzature,
            is_active=True,
        )
    }

    if len(attrezzature_per_id) != len(set(id_attrezzature)):
        raise ValidationError(
            "Una delle attrezzature selezionate non e disponibile."
        )

    errori = []
    for riga in attrezzature_richieste:
        attrezzatura = attrezzature_per_id[riga.id_attrezzatura]
        disponibili = calcola_quantita_disponibile(
            attrezzatura,
            data_inizio,
            data_fine,
        )
        if riga.quantita > disponibili:
            errori.append(
                f"{attrezzatura.name}: richieste {riga.quantita} unita, "
                f"disponibili {disponibili}."
            )

    if errori:
        # transaction.atomic impedisce salvataggi parziali: o passa tutto,
        # oppure non viene creata alcuna prenotazione.
        raise ValidationError(errori)

    prenotazione = Reservation.objects.create(
        user=utente,
        start_date=data_inizio,
        end_date=data_fine,
    )
    ReservationItem.objects.bulk_create(
        # Il prezzo corrente viene copiato nella riga per mantenere corretto
        # lo storico anche se il gestore cambiera il listino in futuro.
        [
            ReservationItem(
                reservation=prenotazione,
                equipment=attrezzature_per_id[riga.id_attrezzatura],
                quantity=riga.quantita,
                daily_price=attrezzature_per_id[riga.id_attrezzatura].daily_price,
            )
            for riga in attrezzature_richieste
        ]
    )
    return prenotazione
