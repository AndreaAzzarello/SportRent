"""Form usati per registrazione, ricerca catalogo, prenotazioni e gestione attrezzature."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Equipment, EquipmentCategory
from .permissions import NOME_GRUPPO_CLIENTI
from .services import AttrezzaturaRichiesta


# Form di registrazione: estende quello Django e assegna il gruppo Clienti.
class ModuloRegistrazione(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="Nome", max_length=150, required=True)
    last_name = forms.CharField(label="Cognome", max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    # Salva l'utente e lo collega al gruppo Clienti.
    def save(self, commit=True):
        user = super().save(commit=commit)
        #controlla che l'utente viene davvero salvato nel databese 
        if commit:
            # Ogni registrazione pubblica nasce con il ruolo cliente.
            client_group, _ = Group.objects.get_or_create(
                name=NOME_GRUPPO_CLIENTI
            )
            user.groups.add(client_group)
        return user


class ModuloRicercaAttrezzature(forms.Form):
    # Form della home: prima si sceglie la categoria, poi il periodo.
    category = forms.ModelChoiceField(
        label="Categoria sportiva",
        queryset=EquipmentCategory.objects.none(),
        required=True,
        empty_label="Scegli una categoria",
        error_messages={"required": "Scegli prima una categoria sportiva."},
    )
    start_date = forms.DateField(
        label="Data di ritiro",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="Data di riconsegna",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    # Carica le categorie dal database quando il form viene visualizzato.
    # Costruisce i campi quantità solo per gli articoli della categoria scelta.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = EquipmentCategory.objects.all()

    # Controlla che le date scelte siano coerenti.
    def clean(self):
        # Le validazioni incrociate richiedono più campi e quindi appartengono
        # al clean del form anziché a un singolo campo.
        dati_puliti = super().clean()
        start_date = dati_puliti.get("start_date")
        end_date = dati_puliti.get("end_date")
        if bool(start_date) != bool(end_date):
            raise forms.ValidationError(
                "Per verificare la disponibilità indica entrambe le date."
            )
        # Controlla che la data iniziale non sia nel passato e che la data finale sia coerente.
        if start_date and start_date < timezone.localdate():
            self.add_error(
                "start_date",
                "La data iniziale non può essere nel passato.",
            )
        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "La data finale deve seguire quella iniziale.",
            )
        return dati_puliti


# Questo form riceve il periodo già scelto e fa scegliere le quantità.
class ModuloPrenotazione(forms.Form):
    # Form dinamico: crea le quantità solo per la categoria e il periodo scelti.
    category = forms.ModelChoiceField(
        queryset=EquipmentCategory.objects.none(),
        required=True,
        widget=forms.HiddenInput,
        error_messages={"required": "Categoria non riconosciuta."},
    )
    start_date = forms.DateField(
        label="Data di inizio",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="Data di fine",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(
        self,
        *args,
        id_attrezzatura_scelta=None, #attrezzatura selezionata per aprire la scheda dell'articolo
        id_categoria_scelta=None, # categoria selezionata nel catalogo
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = EquipmentCategory.objects.all()
        self.id_attrezzatura_scelta = id_attrezzatura_scelta
        self.nomi_campi_attrezzature = []
        self.inizio_periodo = self._data_da_valore_form("start_date")
        self.fine_periodo = self._data_da_valore_form("end_date")
        self.id_categoria_scelta = (
            self._id_categoria_da_valore_form() or id_categoria_scelta
        )
        self.categoria_scelta = None

        if self.id_categoria_scelta:
            self.categoria_scelta = EquipmentCategory.objects.filter(
                pk=self.id_categoria_scelta
            ).first()
            self.initial.setdefault("category", self.id_categoria_scelta)

        today = timezone.localdate()

        self.periodo_valido = (
            self.inizio_periodo
            and self.fine_periodo
            and self.inizio_periodo >= today
            and self.fine_periodo >= self.inizio_periodo
        )

        # Se il periodo è valido, carica gli articoli disponibili per la categoria scelta.
        equipment = Equipment.objects.none()
        if self.categoria_scelta and self.periodo_valido:
            equipment = Equipment.objects.filter(
                category=self.categoria_scelta,
                is_active=True,
            ).select_related("category")

        # Calcola la disponibilità per ciascun articolo e filtra quelli non disponibili.
        attrezzature_disponibili = []
        for item in equipment:
            item.disponibili_periodo = item.quantita_disponibile(
                self.inizio_periodo,
                self.fine_periodo,
            )
            if item.disponibili_periodo > 0:
                attrezzature_disponibili.append(item)
        self.equipment = attrezzature_disponibili

        # Un campo quantità viene generato solo per articoli davvero prenotabili.
        for equipment in self.equipment:
            nome_campo = f"quantity_{equipment.pk}"
            self.nomi_campi_attrezzature.append(nome_campo)
            available = equipment.disponibili_periodo
            self.fields[nome_campo] = forms.IntegerField(
                label=equipment.name,
                min_value=0,
                max_value=available,
                initial=0,
                required=False,
            )

    @property
    # Restituisce i campi dinamici nell'ordine in cui saranno mostrati.
    def campi_attrezzature(self):
        return [self[name] for name in self.nomi_campi_attrezzature]

    @property
    # Prepara dati pronti per le righe della tabella nel template.
    def righe_attrezzature(self):
        righe = []
        for equipment in self.equipment:
            nome_campo = f"quantity_{equipment.pk}"
            righe.append(
                {
                    "field": self[nome_campo],
                    "equipment": equipment,
                    "available": equipment.disponibili_periodo,
                    "is_selected": (
                        nome_campo == self.nome_campo_attrezzatura_scelta
                    ),
                }
            )
        return righe

    @property
    # Individua il campo dell'articolo aperto dalla sua scheda.
    def nome_campo_attrezzatura_scelta(self):
        if not self.id_attrezzatura_scelta:
            return ""
        return f"quantity_{self.id_attrezzatura_scelta}"

    # Convalida le date e la quantità di articoli selezionati.
    def clean(self):
        dati_puliti = super().clean()
        start_date = dati_puliti.get("start_date")
        end_date = dati_puliti.get("end_date")

        if start_date and start_date < timezone.localdate():
            self.add_error(
                "start_date",
                "La data di inizio non può essere nel passato.",
            )
        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "La data di fine deve seguire quella di inizio.",
            )

        # Se le date non sono valide non ha senso pretendere quantità.
        if self.errors:
            return dati_puliti

        quantita_scelta = sum(
            dati_puliti.get(nome_campo) or 0
            for nome_campo in self.nomi_campi_attrezzature
        )
        if quantita_scelta == 0:
            raise forms.ValidationError(
                "Seleziona almeno un'attrezzatura disponibile."
            )
        return dati_puliti

    # Trasforma le quantità valide in oggetti usati dal servizio di prenotazione.
    def ottieni_attrezzature_richieste(self):
        # Il form traduce i campi dinamici in oggetti semplici usati dal service.
        return [
            AttrezzaturaRichiesta(
                id_attrezzatura=equipment.pk,
                quantita=self.cleaned_data.get(f"quantity_{equipment.pk}") or 0,
            )
            for equipment in self.equipment
            if (self.cleaned_data.get(f"quantity_{equipment.pk}") or 0) > 0
        ]

    # Legge una data sia dal form inviato sia dai parametri iniziali della pagina.
    def _data_da_valore_form(self, nome_campo):
        value = self.data.get(nome_campo) if self.is_bound else None
        if not value:
            value = self.initial.get(nome_campo)
        if hasattr(value, "isoformat"):
            return value
        if not value:
            return None
        return parse_date(value)

    # Legge in modo sicuro l'identificativo della categoria scelta.
    def _id_categoria_da_valore_form(self):
        value = self.data.get("category") if self.is_bound else None
        if not value:
            value = self.initial.get("category")
        if isinstance(value, EquipmentCategory):
            return value.pk
        if not value:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


# Form del gestore per creare o aggiornare un articolo di catalogo.
class ModuloAttrezzatura(forms.ModelForm):
    # Form usato dal gestore per creare o aggiornare un'attrezzatura.
    class Meta:
        model = Equipment
        fields = [
            "name",
            "category",
            "description",
            "total_quantity",
            "daily_price",
            "image",
            "is_active",
        ]


# Form del gestore per creare o aggiornare una categoria sportiva.
class ModuloCategoriaAttrezzatura(forms.ModelForm):
    # Form usato dal gestore per creare o aggiornare una categoria sportiva.
    class Meta:
        model = EquipmentCategory
        fields = ["name", "description"]
