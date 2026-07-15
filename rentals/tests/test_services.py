"""Test delle funzioni di disponibilità e creazione prenotazioni."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from rentals.models import Equipment, EquipmentCategory, Reservation
from rentals.services import (
    AttrezzaturaRichiesta,
    crea_prenotazione,
    calcola_quantita_disponibile,
)


# Test del livello service: controllano disponibilità, totali e overbooking.
class ReservationServiceTests(TestCase):
    # Prepara utenti, articoli e date comuni a tutti i test del servizio.
    def setUp(self):
        self.user = User.objects.create_user("mario", password="Testpass123!")
        self.other_user = User.objects.create_user(
            "anna",
            password="Testpass123!",
        )
        self.category = EquipmentCategory.objects.create(name="Ciclismo")
        self.bike = Equipment.objects.create(
            name="Mountain bike",
            category=self.category,
            description="Bicicletta da montagna",
            total_quantity=3,
            daily_price=Decimal("20.00"),
        )
        self.helmet = Equipment.objects.create(
            name="Casco",
            category=self.category,
            description="Casco regolabile",
            total_quantity=5,
            daily_price=Decimal("5.00"),
        )
        self.start_date = timezone.localdate() + timedelta(days=5)
        self.end_date = self.start_date + timedelta(days=2)

    # Verifica che una prenotazione possa contenere più articoli e calcoli il totale.
    def test_create_reservation_with_multiple_equipment(self):
        reservation = crea_prenotazione(
            self.user,
            self.start_date,
            self.end_date,
            [
                AttrezzaturaRichiesta(self.bike.pk, 2),
                AttrezzaturaRichiesta(self.helmet.pk, 1),
            ],
        )

        self.assertEqual(reservation.items.count(), 2)
        self.assertEqual(reservation.giorni_noleggio, 3)
        self.assertEqual(reservation.prezzo_totale, Decimal("135.00"))

    # Verifica che due periodi sovrapposti riducano la disponibilità.
    def test_overlapping_reservation_reduces_availability(self):
        crea_prenotazione(
            self.user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.bike.pk, 2)],
        )

        available = calcola_quantita_disponibile(
            self.bike,
            self.start_date + timedelta(days=1),
            self.end_date + timedelta(days=1),
        )

        self.assertEqual(available, 1)

    # Verifica che un periodo separato non consumi disponibilità.
    def test_non_overlapping_reservation_does_not_reduce_availability(self):
        crea_prenotazione(
            self.user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.bike.pk, 3)],
        )

        available = calcola_quantita_disponibile(
            self.bike,
            self.end_date + timedelta(days=1),
            self.end_date + timedelta(days=3),
        )

        self.assertEqual(available, 3)

    def test_overbooking_is_rejected(self):
        # Caso black-box principale: la seconda richiesta supera la quantità
        # residua e non deve lasciare dati parziali nel database.
        crea_prenotazione(
            self.user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.bike.pk, 2)],
        )

        with self.assertRaises(ValidationError):
            crea_prenotazione(
                self.other_user,
                self.start_date,
                self.end_date,
                [AttrezzaturaRichiesta(self.bike.pk, 2)],
            )

        self.assertEqual(Reservation.objects.count(), 1)

    # Verifica che annullare un noleggio liberi di nuovo gli articoli.
    def test_cancellation_releases_equipment(self):
        reservation = crea_prenotazione(
            self.user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.bike.pk, 3)],
        )
        reservation.cancella()

        available = calcola_quantita_disponibile(
            self.bike,
            self.start_date,
            self.end_date,
        )

        self.assertEqual(available, 3)
