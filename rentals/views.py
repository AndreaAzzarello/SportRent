"""Viste Django che ricevono le richieste, usano form/service e scelgono i template da mostrare."""

from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    ModuloCategoriaAttrezzatura,
    ModuloAttrezzatura,
    ModuloRicercaAttrezzature,
    ModuloRegistrazione,
    ModuloPrenotazione,
)
from .models import Equipment, EquipmentCategory, Reservation
from .permissions import utente_e_gestore, gestore_richiesto
from .services import crea_prenotazione

# Le costanti definiscono la dimensione delle pagine per la paginazione.
CATALOG_PAGE_SIZE = 6
MANAGER_EQUIPMENT_PAGE_SIZE = 10


# Le viste collegano richieste HTTP, form, template e funzioni di servizio.
# La logica critica di disponibilità resta nei service.

# Mostra il catalogo guidando prima alla scelta della categoria e poi del periodo.
def catalogo_attrezzature(request):
    # Il flusso pubblico è guidato: categoria, periodo, risultati disponibili.
    modulo_ricerca = ModuloRicercaAttrezzature(request.GET or None)
    categoria_scelta = None
    periodo_scelto = None
    equipment = []

    if modulo_ricerca.is_bound:
        categoria_scelta = _categoria_da_richiesta(request)

    if modulo_ricerca.is_valid():
        categoria_scelta = modulo_ricerca.cleaned_data.get("category")
        start_date = modulo_ricerca.cleaned_data.get("start_date")
        end_date = modulo_ricerca.cleaned_data.get("end_date")

        if categoria_scelta and start_date and end_date:
            periodo_scelto = {
                "start_date": start_date,
                "end_date": end_date,
            }
            query_attrezzature = Equipment.objects.filter(
                is_active=True,
                category=categoria_scelta,
            ).select_related("category")
            # Gli articoli sono già limitati alla categoria scelta; l'ordinamento segue il nome.
            query_attrezzature = query_attrezzature.order_by("name")

            # La disponibilità dipende dal periodo e non è un campo permanente:
            # viene calcolata per ogni risultato della categoria scelta.
            for item in query_attrezzature:
                item.disponibili_periodo = item.quantita_disponibile(
                    start_date,
                    end_date,
                )
                
                if item.disponibili_periodo > 0:
                    equipment.append(item)

    pagina = _impagina(request, equipment, CATALOG_PAGE_SIZE)
    query_paginazione = _query_paginazione(request)

    return render(
        request,
        "rentals/equipment_list.html",
        {
            "equipment_list": pagina.object_list,
            "categorie": EquipmentCategory.objects.all(),
            "modulo_ricerca": modulo_ricerca,
            "categoria_scelta": categoria_scelta,
            "periodo_scelto": periodo_scelto,
            "pagina": pagina,
            "query_paginazione": query_paginazione,
        },
    )


# Mostra la scheda di un articolo e la sua disponibilità nel periodo scelto.
def dettaglio_attrezzatura(request, pk):
    equipment = get_object_or_404(
        Equipment.objects.select_related("category"),
        pk=pk,
        is_active=True,
    )
    today = timezone.localdate()
    periodo_scelto = None
    disponibili_periodo = None
    start_date = _leggi_data(request.GET.get("start_date"))
    end_date = _leggi_data(request.GET.get("end_date"))

    if (
        start_date
        and end_date
        and start_date >= today
        and end_date >= start_date
    ):
        periodo_scelto = {
            "start_date": start_date,
            "end_date": end_date,
        }
        disponibili_periodo = equipment.quantita_disponibile(
            start_date,
            end_date,
        )

    return render(
        request,
        "rentals/equipment_detail.html",
        {
            "equipment": equipment,
            "available_today": equipment.quantita_disponibile(today, today),
            "periodo_scelto": periodo_scelto,
            "disponibili_periodo": disponibili_periodo,
        },
    )


# Registra un cliente e lo riporta alla pagina richiesta in precedenza.
def registrazione(request):
    if request.user.is_authenticated:
        return redirect("equipment_list")
    
    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST":
        form = ModuloRegistrazione(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registrazione completata.")
            # Accetta il parametro next solo se rimane sullo stesso host,
            # evitando redirect verso siti esterni.
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)
            return redirect("equipment_list")
    else:
        form = ModuloRegistrazione()
    return render(
        request,
        "registration/register.html",
        {"form": form, "next": next_url},
    )


# Le pagine seguenti richiedono un utente autenticato.
@login_required
# Trasforma la scelta del cliente in una nuova prenotazione.
def nuova_prenotazione(request):
    id_attrezzatura_scelta = _intero_positivo(
        request.POST.get("attrezzatura_scelta") or request.GET.get("equipment")
    )
    id_categoria_scelta = _intero_positivo(
        request.POST.get("category") or request.GET.get("category")
    )

    if id_attrezzatura_scelta and not id_categoria_scelta:
        attrezzatura_scelta = Equipment.objects.filter(
            pk=id_attrezzatura_scelta,
            is_active=True,
        ).first()
        if attrezzatura_scelta:
            id_categoria_scelta = attrezzatura_scelta.category_id
    # Il form di prenotazione richiede la categoria per mostrare le attrezzature disponibili.
    if request.method == "POST":
        form = ModuloPrenotazione(
            request.POST,
            id_attrezzatura_scelta=id_attrezzatura_scelta,
            id_categoria_scelta=id_categoria_scelta,
        )
        if form.is_valid():
            try:
                # La vista coordina HTTP e messaggi; disponibilità e salvataggio
                # atomico sono delegati al service applicativo.
                reservation = crea_prenotazione(
                    utente=request.user,
                    data_inizio=form.cleaned_data["start_date"],
                    data_fine=form.cleaned_data["end_date"],
                    attrezzature_richieste=form.ottieni_attrezzature_richieste(),
                )
            except ValidationError as exc:
                for error in exc.messages:
                    form.add_error(None, error)
            else:
                return redirect("reservation_detail", pk=reservation.pk)
    # altrimenti, se la richiesta è GET, il form viene precompilato con i valori passati nella query string.
    else:
        initial = {}
        if id_categoria_scelta:
            initial["category"] = id_categoria_scelta
        if id_attrezzatura_scelta:
            initial[f"quantity_{id_attrezzatura_scelta}"] = 1
        start_date = _leggi_data(request.GET.get("start_date"))
        end_date = _leggi_data(request.GET.get("end_date"))
        if start_date:
            initial["start_date"] = start_date
        if end_date:
            initial["end_date"] = end_date
        form = ModuloPrenotazione(
            initial=initial,
            id_attrezzatura_scelta=id_attrezzatura_scelta,
            id_categoria_scelta=id_categoria_scelta,
        )
    return render(
        request,
        "rentals/reservation_form.html",
        {"form": form},
    )


@login_required
# Mostra soltanto lo storico appartenente al cliente collegato.
def storico_prenotazioni(request):
    # Si parte sempre dalla relazione dell'utente autenticato: un cliente non
    # può ottenere prenotazioni appartenenti ad altri utenti.
    reservations = (
        request.user.reservations.prefetch_related("items__equipment")
        .all()
    )
    filtro_scelto = request.GET.get("filter", "active")
    today = timezone.localdate()
    filtri = _filtri_fase_prenotazioni(today)
    if filtro_scelto not in filtri:
        filtro_scelto = "active"
    reservations = reservations.filter(filtri[filtro_scelto])

    tutte_prenotazioni = request.user.reservations.all()
    conteggi = {
        key: tutte_prenotazioni.filter(query).count()
        for key, query in filtri.items()
    }
    return render(
        request,
        "rentals/reservation_history.html",
        {
            "reservations": reservations,
            "filtro_scelto": filtro_scelto,
            "conteggi": conteggi,
        },
    )


@login_required
# Mostra il dettaglio solo al proprietario della prenotazione o a un gestore.
def dettaglio_prenotazione(request, pk):
    reservations = Reservation.objects.prefetch_related(
        "items__equipment__category"
    )
    if not utente_e_gestore(request.user):
        # Per i clienti il vincolo sul proprietario produce un 404 anche
        # conoscendo manualmente l'identificativo di un'altra prenotazione.
        reservations = reservations.filter(user=request.user)
    reservation = get_object_or_404(reservations, pk=pk)
    return render(
        request,
        "rentals/reservation_detail.html",
        {"reservation": reservation},
    )


@login_required
# Riceve il comando di annullamento e conserva la prenotazione nello storico.
def cancella_prenotazione(request, pk):
    # Una modifica di stato è accettata solo via POST e protetta dal token CSRF
    # presente nel template.
    if request.method != "POST":
        return redirect("reservation_detail", pk=pk)

    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user,
    )
    try:
        reservation.cancella()
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Prenotazione cancellata.")
    return redirect("reservation_detail", pk=pk)


# Le pagine seguenti sono riservate ai gestori e agli amministratori.
@gestore_richiesto
# Raccoglie i dati principali per il riepilogo operativo del gestore.
def pannello_gestore(request):
    prenotazioni_confermate = Reservation.objects.filter(
        status=Reservation.Status.CONFIRMED
    ).prefetch_related("items")
    prenotazioni_future = prenotazioni_confermate.filter(
        start_date__gt=timezone.localdate()
    )
    prenotazioni_in_corso = prenotazioni_confermate.filter(
        start_date__lte=timezone.localdate(),
        end_date__gte=timezone.localdate(),
    )
    return render(
        request,
        "rentals/manager/dashboard.html",
        {
            "conteggio_attrezzature": Equipment.objects.count(),
            "conteggio_attrezzature_attive": Equipment.objects.filter(
                is_active=True
            ).count(),
            "prenotazioni_confermate": prenotazioni_confermate.count(),
            "prenotazioni_future": prenotazioni_future.count(),
            "prenotazioni_in_corso": prenotazioni_in_corso.count(),
            "conteggio_clienti": Reservation.objects.values("user").distinct().count(),
            "prenotazioni_recenti": (
                Reservation.objects.select_related("user")
                .prefetch_related("items")
                .all()[:10]
            ),
        },
    )


@gestore_richiesto
# Elenca il catalogo con filtro per categoria e paginazione.
def elenco_attrezzature_gestore(request):
    categoria_scelta = _categoria_da_richiesta(request)
    equipment = Equipment.objects.select_related("category")
    if categoria_scelta:
        equipment = equipment.filter(category=categoria_scelta)
    pagina = _impagina(request, equipment, MANAGER_EQUIPMENT_PAGE_SIZE)
    query_paginazione = _query_paginazione(request)
    return render(
        request,
        "rentals/manager/equipment_list.html",
        {
            "equipment_list": pagina.object_list,
            "categorie": EquipmentCategory.objects.all(),
            "categoria_scelta": categoria_scelta,
            "pagina": pagina,
            "query_paginazione": query_paginazione,
        },
    )


@gestore_richiesto
# Salva una nuova attrezzatura inserita dal gestore.
def crea_attrezzatura_gestore(request):
    if request.method == "POST":
        form = ModuloAttrezzatura(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save()
            messages.success(request, "Attrezzatura inserita.")
            return redirect("manager_equipment_update", pk=equipment.pk)
    else:
        form = ModuloAttrezzatura()
    return render(
        request,
        "rentals/manager/equipment_form.html",
        {"form": form, "page_title": "Nuova attrezzatura"},
    )


@gestore_richiesto
# Aggiorna i dati di un'attrezzatura già presente.
def modifica_attrezzatura_gestore(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        form = ModuloAttrezzatura(
            request.POST,
            request.FILES,
            instance=equipment,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Attrezzatura aggiornata.")
            return redirect("manager_equipment_update", pk=equipment.pk)
    else:
        form = ModuloAttrezzatura(instance=equipment)
    return render(
        request,
        "rentals/manager/equipment_form.html",
        {"form": form, "page_title": "Modifica attrezzatura"},
    )


@gestore_richiesto
# Mostra le categorie che organizzano il catalogo.
def elenco_categorie_gestore(request):
    return render(
        request,
        "rentals/manager/category_list.html",
        {"categorie": EquipmentCategory.objects.all()},
    )


@gestore_richiesto
# Crea una nuova categoria sportiva.
def crea_categoria_gestore(request):
    if request.method == "POST":
        form = ModuloCategoriaAttrezzatura(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Tipologia inserita.")
            return redirect("manager_category_update", pk=category.pk)
    else:
        form = ModuloCategoriaAttrezzatura()
    return render(
        request,
        "rentals/manager/category_form.html",
        {"form": form, "page_title": "Nuova tipologia"},
    )


@gestore_richiesto
# Modifica nome e descrizione di una categoria esistente.
def modifica_categoria_gestore(request, pk):
    category = get_object_or_404(EquipmentCategory, pk=pk)
    if request.method == "POST":
        form = ModuloCategoriaAttrezzatura(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipologia aggiornata.")
            return redirect("manager_category_update", pk=category.pk)
    else:
        form = ModuloCategoriaAttrezzatura(instance=category)
    return render(
        request,
        "rentals/manager/category_form.html",
        {"form": form, "page_title": "Modifica tipologia"},
    )


@gestore_richiesto
# Elenca le prenotazioni con un filtro per fase del noleggio.
def elenco_prenotazioni_gestore(request):
    reservations = Reservation.objects.select_related("user").prefetch_related(
        "items__equipment"
    )
    filtro_scelto = request.GET.get("filter", "active")
    filtri = _filtri_fase_prenotazioni(timezone.localdate())
    if filtro_scelto not in filtri:
        filtro_scelto = "active"
    reservations = reservations.filter(filtri[filtro_scelto])
    return render(
        request,
        "rentals/manager/reservation_list.html",
        {
            "reservations": reservations,
            "filtro_scelto": filtro_scelto,
        },
    )


# Legge la categoria dalla URL senza generare errori per valori non validi.
def _categoria_da_richiesta(request):
    category_id = _intero_positivo(request.GET.get("category"))
    if not category_id:
        return None
    return EquipmentCategory.objects.filter(pk=category_id).first()


# Divide un elenco lungo in pagine di dimensione controllata.
def _impagina(request, items, per_page):
    paginator = Paginator(items, per_page)
    return paginator.get_page(request.GET.get("page"))


# Conserva i parametri scelti quando l'utente passa alla pagina successiva.
def _query_paginazione(request):
    parametri_query = request.GET.copy()
    parametri_query.pop("page", None)
    return parametri_query.urlencode()


# Accetta soltanto numeri interi maggiori di zero per ID e parametri numerici.
def _intero_positivo(value):
    if value in (None, ""):
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


# Converte una data ricevuta dalla URL oppure restituisce nessun valorè valido.
def _leggi_data(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# Definisce una sola volta i filtri usati per fasi e storico delle prenotazioni.
def _filtri_fase_prenotazioni(today):
    # I filtri riutilizzano la stessa definizione temporale nelle pagine del
    # cliente e del gestore.
    return {
        "active": Q(
            status=Reservation.Status.CONFIRMED,
            end_date__gte=today,
        ),
        "upcoming": Q(
            status=Reservation.Status.CONFIRMED,
            start_date__gt=today,
        ),
        "in_progress": Q(
            status=Reservation.Status.CONFIRMED,
            start_date__lte=today,
            end_date__gte=today,
        ),
        "completed": Q(
            status=Reservation.Status.CONFIRMED,
            end_date__lt=today,
        ),
        "cancelled": Q(status=Reservation.Status.CANCELLED),
        "all": Q(),
    }
