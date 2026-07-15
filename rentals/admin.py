"""Configurazione del Django Admin tecnico per categorie, attrezzature e prenotazioni."""

from django.contrib import admin

from .models import (
    Equipment,
    EquipmentCategory,
    Reservation,
    ReservationItem,
)


# Configurazione del Django Admin tecnico.
# Il pannello gestori dell'app resta separato ed è più adatto all'uso operativo.
@admin.register(EquipmentCategory)
# Personalizza l'elenco delle categorie nel pannello Django Admin.
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "conteggio_attrezzature", "description"]

    #aggiunge un barra di ricerca nell'Admin. permette di cercare le categorie per nome o descrizione.
    search_fields = ["name", "description"]

    @admin.display(description="Attrezzature")
    def conteggio_attrezzature(self, obj):
        return obj.equipment.count()


@admin.register(Equipment)
# Personalizza ricerca, filtri e campi mostrati per le attrezzature.
class EquipmentAdmin(admin.ModelAdmin):
    # Colonne e filtri per controllare rapidamente il catalogo.
    list_display = [
        "name",
        "category",
        "total_quantity",
        "daily_price",
        "is_active",
    ]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description"]
    list_editable = ["total_quantity", "daily_price", "is_active"]
    readonly_fields = ["created_at", "updated_at"]

    # Organizza i campi in sezioni per una visualizzazione più chiara.
    fieldsets = [
        (
            "Scheda prodotto",
            {"fields": ["name", "category", "description", "image"]},
        ),
        (
            "Noleggio e pubblicazione",
            {"fields": ["total_quantity", "daily_price", "is_active"]},
        ),
        (
            "Informazioni di sistema",
            {"fields": ["created_at", "updated_at"]},
        ),
    ]


# Visualizza le righe della prenotazione direttamente nella relativa scheda.
class ReservationItemInline(admin.TabularInline):
    # Mostra gli articoli collegati a una prenotazione dentro la stessa pagina.
    model = ReservationItem
    extra = 0
    readonly_fields = ["equipment", "quantity", "daily_price"]

    # Le righe nascono dalla procedura di prenotazione, non dal pannello admin.
    def has_add_permission(self, request, obj=None):
        # Le righe devono nascere dal flusso transazionale di prenotazione,
        # non essere aggiunte manualmente dall'amministratore.
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Reservation)
# Permette di consultare le prenotazioni evitando modifiche non controllate.
class ReservationAdmin(admin.ModelAdmin):
    # Le prenotazioni sono consultabili in admin ma nascono dal flusso utente.
    list_display = [
        "id",
        "user",
        "start_date",
        "end_date",
        "status",
        "fase_noleggio",
        "created_at",
    ]
    list_filter = ["status", "start_date", "end_date"]
    search_fields = ["user__username", "user__email"]
    date_hierarchy = "created_at"
    list_select_related = ["user"]
    readonly_fields = [
        "user",
        "start_date",
        "end_date",
        "status",
        "created_at",
        "cancelled_at",
    ]
    #mostra le righe in formato tabella
    inlines = [ReservationItemInline]

    #impedisce di creare e eliminare prenotazioni direttamente dal django admin, perché rimangono nello storico
    def has_add_permission(self, request):
        # Anche la testata viene creata esclusivamente dal service applicativo.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    #crea colonna situazione che mostra lo stato della prenotazione in modo leggibile
    @admin.display(description="Situazione")
    def fase_noleggio(self, obj):
        return obj.etichetta_fase_noleggio


admin.site.site_header = "Amministrazione SportRent"
admin.site.site_title = "SportRent"
admin.site.index_title = "Gestione del servizio"
