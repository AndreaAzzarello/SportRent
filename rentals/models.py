"""Modelli del database: categorie, attrezzature, prenotazioni e righe di prenotazione."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


# Modelli principali del database: categorie, attrezzature, prenotazioni e righe.
class EquipmentCategory(models.Model):
    name = models.CharField("nome", max_length=100, unique=True)
    description = models.TextField("descrizione", blank=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorie"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Equipment(models.Model):
    # Articolo noleggiabile: categoria, descrizione, quantità, prezzo e immagine.
    name = models.CharField("nome", max_length=150)
    category = models.ForeignKey(
        EquipmentCategory,
        on_delete=models.PROTECT,
        related_name="equipment",
        verbose_name="tipologia",
    )
    description = models.TextField("descrizione")
    total_quantity = models.PositiveIntegerField(
        "quantità totale",
        validators=[MinValueValidator(1)],
    )
    daily_price = models.DecimalField(
        "prezzo giornaliero",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    image = models.ImageField(
        "immagine",
        upload_to="equipment/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField("disponibile nel catalogo", default=True)
    created_at = models.DateTimeField("creata il", auto_now_add=True)
    updated_at = models.DateTimeField("modificata il", auto_now=True)

    class Meta:
        verbose_name = "attrezzatura"
        verbose_name_plural = "attrezzature"
        ordering = ["category__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                name="unique_equipment_name_per_category",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"

    # Calcola la quantità disponibile per un certo periodo, escludendo eventualmente una prenotazione.
    def quantita_disponibile(self, data_inizio, data_fine, prenotazione_esclusa=None):
        # Il modello espone un'API comoda, mentre il calcolo resta nel
        # service layer per evitare di concentrare troppa logica nei modelli.
        from .services import calcola_quantita_disponibile

        return calcola_quantita_disponibile(
            self,
            data_inizio,
            data_fine,
            prenotazione_esclusa=prenotazione_esclusa,
        )


class Reservation(models.Model):
    # Prenotazione del cliente: salva periodo, stato e collegamento all'utente.
    # Lo stato memorizzato è volutamente essenziale. Le fasi "in programma",
    # "in corso" e "conclusa" sono ricavate dalle date e non duplicate nel DB.
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confermata"
        CANCELLED = "cancelled", "Cancellata"
    # 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="cliente",
    )
    start_date = models.DateField("data di inizio")
    end_date = models.DateField("data di fine")
    status = models.CharField(
        "stato",
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField("creata il", auto_now_add=True)
    cancelled_at = models.DateTimeField(
        "cancellata il",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "prenotazione"
        verbose_name_plural = "prenotazioni"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prenotazione #{self.pk} - {self.user}"

    # Evita di salvare una prenotazione con fine precedente all'inizio.
    def clean(self):
        super().clean()
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(
                    {"end_date": "La data di fine deve seguire quella di inizio."}
                )

    @property
    def giorni_noleggio(self):
        if not self.start_date or not self.end_date:
            return 0
        # Ritiro e riconsegna sono entrambi giorni di noleggio.
        return (self.end_date - self.start_date).days + 1

    @property
    def prezzo_totale(self):
        # Il totale deriva dalle righe: prezzo storico x quantità x giorni.
        return sum(
            (item.subtotale for item in self.items.all()),
            Decimal("0.00"),
        )

    @property
    # Una prenotazione risulta annullabile soltanto prima del giorno di ritiro.
    def puo_essere_cancellata(self):
        return (
            self.status == self.Status.CONFIRMED
            and self.start_date > timezone.localdate()
        )

    @property
    # Trasforma date e stato in una fase facile da mostrare nelle pagine.
    def fase_noleggio(self):
        if self.status == self.Status.CANCELLED:
            return "cancelled"

        today = timezone.localdate()
        if self.start_date > today:
            return "upcoming"
        if self.end_date < today:
            return "completed"
        return "in_progress"

    @property
    # Converte il valore tecnico della fase in una scritta per l'utente.
    def etichetta_fase_noleggio(self):
        labels = {
            "upcoming": "In programma",
            "in_progress": "In corso",
            "completed": "Concluso",
            "cancelled": "Cancellato",
        }
        return labels[self.fase_noleggio]

    def cancella(self):
        # La cancellazione logica conserva lo storico e rende nuovamente
        # disponibili le quantità, perché i calcoli ignorano lo stato CANCELLED.
        if not self.puo_essere_cancellata:
            raise ValidationError(
                "La prenotazione non può più essere cancellata."
            )
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at"])


class ReservationItem(models.Model):
    # Riga di dettaglio: collega una prenotazione a un'attrezzatura specifica.
    # Questa entità realizza la relazione molti-a-molti tra prenotazioni e
    # attrezzature e aggiunge quantità e prezzo applicato.
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="prenotazione",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="reservation_items",
        verbose_name="attrezzatura",
    )
    quantity = models.PositiveIntegerField(
        "quantità",
        validators=[MinValueValidator(1)],
    )
    daily_price = models.DecimalField(
        "prezzo giornaliero applicato",
        max_digits=8,
        decimal_places=2,
    )

    class Meta:
        verbose_name = "riga prenotazione"
        verbose_name_plural = "righe prenotazione"
        constraints = [
            models.UniqueConstraint(
                fields=["reservation", "equipment"],
                name="unique_equipment_per_reservation",
            )
        ]

    def __str__(self):
        return f"{self.quantity} x {self.equipment.name}"

    @property
    # Calcola il costo di questa singola riga del noleggio.
    def subtotale(self):
        return self.daily_price * self.quantity * self.reservation.giorni_noleggio
