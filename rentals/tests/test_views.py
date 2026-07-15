"""Test dei flussi principali visti dall'utente, dal gestore e dall'admin."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rentals.models import Equipment, EquipmentCategory, Reservation
from rentals.permissions import NOME_GRUPPO_CLIENTI, NOME_GRUPPO_GESTORI
from rentals.services import AttrezzaturaRichiesta, crea_prenotazione


# Test delle viste: pochi casi completi che coprono i flussi principali.
class RentalViewTests(TestCase):
    # Prepara i dati minimi con cui simulare le azioni dei diversi utenti.
    def setUp(self):
        self.user = User.objects.create_user("cliente", password="Pass12345!")
        self.other_user = User.objects.create_user(
            "altro",
            password="Pass12345!",
        )
        self.category = EquipmentCategory.objects.create(name="Sci")
        self.other_category = EquipmentCategory.objects.create(name="Ciclismo")
        self.equipment = Equipment.objects.create(
            name="Set sci",
            category=self.category,
            description="Set completo",
            total_quantity=4,
            daily_price=Decimal("25.00"),
        )
        self.start_date = timezone.localdate() + timedelta(days=7)
        self.end_date = self.start_date + timedelta(days=1)

    def test_catalog_guided_search_availability_and_past_date(self):
        # Catalogo: prima categoria, poi date, poi risultati disponibili.
        response = self.client.get(reverse("equipment_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scegli la categoria")
        self.assertNotContains(response, "Apri scheda e prenota")

        category_response = self.client.get(
            reverse("equipment_list"),
            {"category": self.category.pk},
        )
        self.assertContains(category_response, "Categoria scelta:")
        self.assertContains(category_response, "Sci")
        self.assertContains(category_response, "Indica le date")
        self.assertNotContains(category_response, "Set sci")

        available_response = self.client.get(
            reverse("equipment_list"),
            {
                "category": self.category.pk,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )
        self.assertContains(available_response, "Set sci")
        self.assertContains(available_response, "Apri scheda e prenota")

        past_date = timezone.localdate() - timedelta(days=1)
        past_response = self.client.get(
            reverse("equipment_list"),
            {
                "category": self.category.pk,
                "start_date": past_date.isoformat(),
                "end_date": past_date.isoformat(),
            },
        )
        self.assertContains(past_response, "Periodo non valido")
        self.assertNotContains(past_response, "Apri scheda e prenota")

        crea_prenotazione(
            self.other_user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.equipment.pk, 4)],
        )
        filtered_response = self.client.get(
            reverse("equipment_list"),
            {
                "category": self.category.pk,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )

        self.assertEqual(filtered_response.status_code, 200)
        self.assertNotContains(filtered_response, "Set sci")
        self.assertContains(filtered_response, "Nessun'attrezzatura disponibile")

    # Verifica ruolo cliente e ritorno alla scheda aperta prima della registrazione.
    def test_registration_assigns_client_group_and_returns_to_product(self):
        # Registrazione: crea un cliente e rispetta il parametro next.
        detail_url = reverse("equipment_detail", args=[self.equipment.pk])
        response = self.client.post(
            reverse("register"),
            {
                "username": "nuovo_cliente",
                "first_name": "Nuovo",
                "last_name": "Cliente",
                "email": "nuovo@example.com",
                "password1": "PasswordSicura123!",
                "password2": "PasswordSicura123!",
                "next": detail_url,
            },
        )

        self.assertRedirects(response, detail_url)
        new_user = User.objects.get(username="nuovo_cliente")
        self.assertTrue(
            new_user.groups.filter(name=NOME_GRUPPO_CLIENTI).exists()
        )

    def test_reservation_requires_login_uses_period_and_same_category(self):
        # Prenotazione: usa date già scelte e mostra solo la categoria richiesta.
        login_required = self.client.get(reverse("reservation_create"))
        self.assertRedirects(
            login_required,
            f"{reverse('login')}?next={reverse('reservation_create')}",
        )

        helmet = Equipment.objects.create(
            name="Casco",
            category=self.category,
            description="Casco regolabile",
            total_quantity=2,
            daily_price=Decimal("5.00"),
        )
        Equipment.objects.create(
            name="Mountain bike",
            category=self.other_category,
            description="Bici fuori strada",
            total_quantity=2,
            daily_price=Decimal("30.00"),
        )
        crea_prenotazione(
            self.other_user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.equipment.pk, 4)],
        )
        self.client.login(username="cliente", password="Pass12345!")

        form_response = self.client.get(
            reverse("reservation_create"),
            {
                "equipment": helmet.pk,
                "category": self.category.pk,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )

        nome_campo = f"quantity_{helmet.pk}"
        self.assertEqual(form_response.context["form"][nome_campo].value(), 1)
        self.assertContains(form_response, "Periodo scelto")
        self.assertNotContains(form_response, 'type="date"')
        self.assertContains(form_response, "Casco")
        self.assertNotContains(form_response, "Set sci")
        self.assertNotContains(form_response, "Mountain bike")

        post_response = self.client.post(
            reverse("reservation_create"),
            {
                "category": self.category.pk,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "attrezzatura_scelta": helmet.pk,
                nome_campo: 1,
            },
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(self.user.reservations.count(), 1)

    # Verifica storico, annullamento e protezione dei dati di altri clienti.
    def test_customer_history_detail_cancel_and_isolation(self):
        # Area cliente: filtri storico, dettaglio, cancellazione e isolamento dati.
        upcoming = crea_prenotazione(
            self.user,
            self.start_date,
            self.end_date,
            [AttrezzaturaRichiesta(self.equipment.pk, 1)],
        )
        completed = Reservation.objects.create(
            user=self.user,
            start_date=timezone.localdate() - timedelta(days=5),
            end_date=timezone.localdate() - timedelta(days=3),
        )
        cancelled = Reservation.objects.create(
            user=self.user,
            start_date=self.start_date + timedelta(days=10),
            end_date=self.start_date + timedelta(days=11),
            status=Reservation.Status.CANCELLED,
        )
        other_reservation = crea_prenotazione(
            self.other_user,
            self.start_date + timedelta(days=20),
            self.end_date + timedelta(days=20),
            [AttrezzaturaRichiesta(self.equipment.pk, 1)],
        )
        self.client.login(username="cliente", password="Pass12345!")

        active_response = self.client.get(reverse("reservation_history"))
        completed_response = self.client.get(
            reverse("reservation_history"),
            {"filter": "completed"},
        )
        cancelled_response = self.client.get(
            reverse("reservation_history"),
            {"filter": "cancelled"},
        )
        detail_response = self.client.get(
            reverse("reservation_detail", args=[upcoming.pk])
        )
        forbidden_response = self.client.get(
            reverse("reservation_detail", args=[other_reservation.pk])
        )
        cancel_response = self.client.post(
            reverse("reservation_cancel", args=[upcoming.pk])
        )

        upcoming.refresh_from_db()
        self.assertContains(active_response, f"#{upcoming.pk}")
        self.assertContains(completed_response, f"#{completed.pk}")
        self.assertContains(cancelled_response, f"#{cancelled.pk}")
        self.assertContains(detail_response, "Riepilogo noleggio")
        self.assertEqual(forbidden_response.status_code, 404)
        self.assertRedirects(
            cancel_response,
            reverse("reservation_detail", args=[upcoming.pk]),
        )
        self.assertEqual(upcoming.status, Reservation.Status.CANCELLED)

    # Verifica accesso del gestore, filtri e paginazione del catalogo.
    def test_manager_area_admin_and_equipment_pagination_are_protected(self):
        # Ruoli: il cliente non entra in gestione, il gestore sì, admin funziona.
        self.client.login(username="cliente", password="Pass12345!")
        denied_response = self.client.get(reverse("manager_dashboard"))
        self.assertEqual(denied_response.status_code, 302)
        self.client.logout()

        manager = User.objects.create_user(
            "gestore",
            password="Pass12345!",
            is_staff=True,
        )
        group = Group.objects.create(name=NOME_GRUPPO_GESTORI)
        manager.groups.add(group)
        Equipment.objects.create(
            name="Casco bici",
            category=self.other_category,
            description="Casco per test filtro categoria",
            total_quantity=2,
            daily_price=Decimal("5.00"),
        )
        for index in range(10):
            Equipment.objects.create(
                name=f"Attrezzatura extra {index}",
                category=self.category,
                description="Articolo per test paginazione",
                total_quantity=1,
                daily_price=Decimal("3.00"),
            )

        self.client.login(username="gestore", password="Pass12345!")
        for url_name, expected_text in [
            ("manager_dashboard", "Riepilogo operativo"),
            ("manager_equipment_list", "Catalogo attrezzature"),
            ("manager_reservation_list", "Prenotazioni clienti"),
        ]:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_text)
        equipment_response = self.client.get(reverse("manager_equipment_list"))
        self.assertContains(equipment_response, "Pagina 1 di 2")

        filtered_equipment_response = self.client.get(
            reverse("manager_equipment_list"),
            {"category": self.other_category.pk},
        )
        self.assertContains(filtered_equipment_response, "Filtro attivo: ")
        self.assertContains(filtered_equipment_response, "Ciclismo")
        self.assertContains(filtered_equipment_response, "Casco bici")
        self.assertNotContains(filtered_equipment_response, "Set sci")
        self.client.logout()

        staff = User.objects.create_superuser(
            "staff",
            email="staff@example.com",
            password="Pass12345!",
        )
        self.client.login(username=staff.username, password="Pass12345!")
        admin_response = self.client.get(reverse("admin:index"))
        equipment_admin_response = self.client.get(
            reverse("admin:rentals_equipment_changelist")
        )

        self.assertContains(admin_response, "Amministrazione SportRent")
        self.assertContains(equipment_admin_response, "Scegli attrezzatura")
