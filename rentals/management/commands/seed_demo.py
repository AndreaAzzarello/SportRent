"""Comando personalizzato che popola il database con dati demo e account di prova."""

from datetime import timedelta

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from rentals.models import (
    Equipment,
    EquipmentCategory,
    Reservation,
    ReservationItem,
)
from rentals.permissions import NOME_GRUPPO_CLIENTI, NOME_GRUPPO_GESTORI


DEMO_PASSWORD = "Demo12345!"


# Comando usato per preparare il progetto alla dimostrazione d'esame.
# Crea dati, utenti e prenotazioni demo in modo ripetibile.
class Command(BaseCommand):
    help = "Inserisce tipologie, attrezzature e account dimostrativi."

    # Aggiunge l'opzione per creare anche gli account dimostrativi.
    def add_arguments(self, parser):
        parser.add_argument(
            "--with-users",
            action="store_true",
            help="Crea anche cliente_demo e gestore_demo.",
        )

    # Inserisce o aggiorna categorie e attrezzature senza duplicare i dati.
    def handle(self, *args, **options):
        # update_or_create rende il comando ripetibile senza duplicare i dati.
        manager_group, _ = Group.objects.get_or_create(
            name=NOME_GRUPPO_GESTORI
        )
        client_group, _ = Group.objects.get_or_create(
            name=NOME_GRUPPO_CLIENTI
        )

        categorie = {}
        category_data = [
            ("Sci", "Attrezzatura per sci alpino e sci di fondo."),
            ("Ciclismo", "Biciclette e accessori per il ciclismo."),
            ("Sport acquatici", "Attrezzatura per attività in acqua."),
            ("Fitness", "Attrezzatura per allenamento e benessere."),
            ("Tennis", "Racchette e accessori per il tennis."),
            ("Calcio", "Palloni e materiali per allenamenti di squadra."),
            ("Arrampicata", "Attrezzatura per arrampicata sportiva indoor e outdoor."),
        ]
        for name, description in category_data:
            category, _ = EquipmentCategory.objects.update_or_create(
                name=name,
                defaults={"description": description},
            )
            categorie[name] = category

        equipment_data = [
            {
                "name": "Set sci alpino",
                "category": "Sci",
                "description": (
                    "Sci, attacchi e bastoncini. Disponibile in varie misure."
                ),
                "total_quantity": 12,
                "daily_price": "24.90",
                "image": "equipment/set-sci-alpino.png",
            },
            {
                "name": "Scarponi da sci",
                "category": "Sci",
                "description": (
                    "Scarponi regolabili, igienizzati dopo ogni utilizzo."
                ),
                "total_quantity": 18,
                "daily_price": "9.50",
                "image": "equipment/scarponi-sci.png",
            },
            {
                "name": "Mountain bike",
                "category": "Ciclismo",
                "description": (
                    "Mountain bike front suspended con casco incluso."
                ),
                "total_quantity": 8,
                "daily_price": "32.00",
                "image": "equipment/mountain-bike.png",
            },
            {
                "name": "Bicicletta da trekking",
                "category": "Ciclismo",
                "description": (
                    "Bicicletta confortevole con portapacchi, luci e parafanghi."
                ),
                "total_quantity": 5,
                "daily_price": "27.00",
                "image": "equipment/bicicletta-trekking.png",
            },
            {
                "name": "Casco da ciclismo",
                "category": "Ciclismo",
                "description": (
                    "Casco ventilato e regolabile, disponibile in più misure."
                ),
                "total_quantity": 16,
                "daily_price": "4.50",
                "image": "equipment/casco-ciclismo.png",
            },
            {
                "name": "Kayak singolo",
                "category": "Sport acquatici",
                "description": (
                    "Kayak per una persona con pagaia e giubbotto salvagente."
                ),
                "total_quantity": 6,
                "daily_price": "28.00",
                "image": "equipment/kayak-singolo.png",
            },
            {
                "name": "Muta in neoprene",
                "category": "Sport acquatici",
                "description": (
                    "Muta intera in neoprene per attività in acqua, varie taglie."
                ),
                "total_quantity": 14,
                "daily_price": "8.00",
                "image": "equipment/muta-neoprene.png",
            },
            {
                "name": "Stand up paddle",
                "category": "Sport acquatici",
                "description": (
                    "Tavola SUP gonfiabile completa di pagaia e pompa."
                ),
                "total_quantity": 10,
                "daily_price": "20.00",
                "image": "equipment/stand-up-paddle.png",
            },
            {
                "name": "Kit pesi regolabili",
                "category": "Fitness",
                "description": (
                    "Coppia di manubri regolabili fino a 20 kg complessivi."
                ),
                "total_quantity": 7,
                "daily_price": "12.00",
                "image": "equipment/kit-pesi-regolabili.png",
            },
            {
                "name": "Palla medica",
                "category": "Fitness",
                "description": (
                    "Palla medica per allenamento funzionale, core training "
                    "e preparazione atletica."
                ),
                "total_quantity": 2,
                "daily_price": "5.00",
                "image": "equipment/palla-medica.png",
            },
            {
                "name": "Panca fitness regolabile",
                "category": "Fitness",
                "description": (
                    "Panca inclinabile per allenamento con pesi e corpo libero."
                ),
                "total_quantity": 3,
                "daily_price": "15.00",
                "image": "equipment/panca-fitness.png",
                "is_active": False,
            },
            {
                "name": "Tavola da snowboard",
                "category": "Sci",
                "description": (
                    "Snowboard all-mountain con attacchi regolabili inclusi."
                ),
                "total_quantity": 9,
                "daily_price": "22.00",
                "image": "equipment/tavola-snowboard.png",
            },
            {
                "name": "Racchette da neve",
                "category": "Sci",
                "description": (
                    "Coppia di ciaspole regolabili con bastoncini telescopici."
                ),
                "total_quantity": 11,
                "daily_price": "11.00",
                "image": "equipment/racchette-neve.png",
            },
            {
                "name": "Racchetta da tennis",
                "category": "Tennis",
                "description": (
                    "Racchetta leggera per partite amatoriali e allenamenti."
                ),
                "total_quantity": 10,
                "daily_price": "7.00",
                "image": "equipment/racchetta-tennis.png",
            },
            {
                "name": "Set palline da tennis",
                "category": "Tennis",
                "description": (
                    "Tubo da tre palline adatte a campi in cemento e terra."
                ),
                "total_quantity": 20,
                "daily_price": "3.00",
                "image": "equipment/set-palline-tennis.png",
            },
            {
                "name": "Borsa porta racchette",
                "category": "Tennis",
                "description": (
                    "Borsa sportiva con scomparto per racchette e accessori."
                ),
                "total_quantity": 6,
                "daily_price": "5.00",
                "image": "equipment/borsa-racchette-tennis.png",
            },
            {
                "name": "Pallone da calcio",
                "category": "Calcio",
                "description": (
                    "Pallone regolamentare per partite e allenamenti."
                ),
                "total_quantity": 15,
                "daily_price": "4.00",
                "image": "equipment/pallone-calcio.png",
            },
            {
                "name": "Kit coni allenamento",
                "category": "Calcio",
                "description": (
                    "Coni colorati per esercizi tecnici e percorsi atletici."
                ),
                "total_quantity": 12,
                "daily_price": "6.00",
                "image": "equipment/kit-coni-allenamento.png",
            },
            {
                "name": "Pettorine squadra",
                "category": "Calcio",
                "description": (
                    "Set di pettorine per dividere le squadre durante gli allenamenti."
                ),
                "total_quantity": 10,
                "daily_price": "5.50",
                "image": "equipment/pettorine-squadra.png",
            },
            {
                "name": "Imbrago arrampicata",
                "category": "Arrampicata",
                "description": (
                    "Imbrago regolabile per palestra e vie sportive attrezzate."
                ),
                "total_quantity": 8,
                "daily_price": "11.00",
                "image": "equipment/imbrago-arrampicata.png",
            },
            {
                "name": "Casco arrampicata",
                "category": "Arrampicata",
                "description": (
                    "Casco leggero per protezione durante arrampicata e ferrate."
                ),
                "total_quantity": 9,
                "daily_price": "6.00",
                "image": "equipment/casco-arrampicata.png",
            },
            {
                "name": "Scarpette arrampicata",
                "category": "Arrampicata",
                "description": (
                    "Scarpette tecniche disponibili in diverse taglie."
                ),
                "total_quantity": 10,
                "daily_price": "8.50",
                "image": "equipment/scarpette-arrampicata.png",
            },
        ]

        for item in equipment_data:
            defaults = {
                "description": item["description"],
                "total_quantity": item["total_quantity"],
                "daily_price": item["daily_price"],
                "is_active": item.get("is_active", True),
            }
            if "image" in item:
                defaults["image"] = item["image"]
            Equipment.objects.update_or_create(
                name=item["name"],
                category=categorie[item["category"]],
                defaults=defaults,
            )

        if options["with_users"]:
            # Gli account coprono i tre punti di vista da mostrare all'esame:
            # cliente, gestore operativo e amministratore completo.
            client, _ = User.objects.get_or_create(username="cliente_demo")
            client.first_name = "Cliente"
            client.last_name = "Demo"
            client.email = "cliente@example.com"
            client.set_password(DEMO_PASSWORD)
            client.save()
            client.groups.add(client_group)

            manager, _ = User.objects.get_or_create(username="gestore_demo")
            manager.first_name = "Gestore"
            manager.last_name = "Demo"
            manager.email = "gestore@example.com"
            manager.is_staff = True
            manager.set_password(DEMO_PASSWORD)
            manager.save()
            manager.groups.add(manager_group)

            rental_permissions = Permission.objects.filter(
                content_type__app_label="rentals"
            )
            manager_group.permissions.add(*rental_permissions)

            admin, _ = User.objects.get_or_create(username="admin_demo")
            admin.first_name = "Amministratore"
            admin.last_name = "Demo"
            admin.email = "admin@example.com"
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password(DEMO_PASSWORD)
            admin.save()

            today = timezone.localdate()
            # Gli esempi sono relativi alla data di esecuzione, quindi restano
            # utili anche eseguendo il comando in un momento successivo.
            confirmed = client.reservations.filter(
                status=Reservation.Status.CONFIRMED
            )
            if not confirmed.filter(start_date__gt=today).exists():
                self._ensure_reservation(
                    client,
                    today + timedelta(days=7),
                    today + timedelta(days=9),
                    [
                        ("Mountain bike", 1),
                        ("Scarponi da sci", 2),
                    ],
                )
            if not confirmed.filter(
                start_date__lte=today,
                end_date__gte=today,
            ).exists():
                self._ensure_reservation(
                    client,
                    today - timedelta(days=1),
                    today + timedelta(days=1),
                    [("Kayak singolo", 1)],
                )
            if not confirmed.filter(end_date__lt=today).exists():
                self._ensure_reservation(
                    client,
                    today - timedelta(days=12),
                    today - timedelta(days=10),
                    [
                        ("Set sci alpino", 1),
                        ("Scarponi da sci", 1),
                    ],
                )
            if not client.reservations.filter(
                status=Reservation.Status.CANCELLED
            ).exists():
                self._ensure_reservation(
                    client,
                    today + timedelta(days=15),
                    today + timedelta(days=16),
                    [("Bicicletta da trekking", 1)],
                    status=Reservation.Status.CANCELLED,
                )

            self.stdout.write(
                self.style.WARNING(
                    "Account cliente, gestore, admin e prenotazioni demo creati. "
                    "Cambiare le password fuori dalla demo."
                )
            )

        self.stdout.write(
            self.style.SUCCESS("Dati dimostrativi inseriti correttamente.")
        )

    # Crea una prenotazione demo soltanto quando non esiste già.
    def _ensure_reservation(
        self,
        user,
        start_date,
        end_date,
        righe_attrezzature,
        status=Reservation.Status.CONFIRMED,
    ):
        # La coppia utente-periodo identifica lo scenario demo ed evita che
        # esecuzioni successive del comando lo ricreino.
        reservation, created = Reservation.objects.get_or_create(
            user=user,
            start_date=start_date,
            end_date=end_date,
            defaults={
                "status": status,
                "cancelled_at": (
                    timezone.now()
                    if status == Reservation.Status.CANCELLED
                    else None
                ),
            },
        )
        if not created:
            return reservation

        ReservationItem.objects.bulk_create(
            [
                ReservationItem(
                    reservation=reservation,
                    equipment=equipment,
                    quantity=quantity,
                    daily_price=equipment.daily_price,
                )
                for equipment_name, quantity in righe_attrezzature
                for equipment in [
                    Equipment.objects.get(name=equipment_name)
                ]
            ]
        )
        return reservation
