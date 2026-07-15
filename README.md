# SportRent

SportRent è un'applicazione web sviluppata con Django per gestire il noleggio di attrezzature sportive.

Il progetto nasce come elaborato universitario per il corso di Tecnologie Web. L'obiettivo è simulare un piccolo sito di prenotazione in cui l'utente sceglie prima la categoria sportiva, poi il periodo di noleggio e infine visualizza solo le attrezzature realmente disponibili in quelle date.

## Funzionalità principali

- consultazione del catalogo anche senza login;
- scelta guidata: categoria, date, articolo;
- controllo della disponibilità in base al periodo richiesto;
- registrazione e login degli utenti;
- creazione di una prenotazione con una o più attrezzature della stessa categoria;
- storico dei noleggi del cliente;
- cancellazione delle prenotazioni future;
- area gestore per categorie, attrezzature e prenotazioni;
- filtro per categoria nell'area gestore;
- pannello Django Admin per la gestione tecnica;
- test automatici sui flussi principali.

Il progetto usa HTML generato da template Django e un CSS semplice. Non è presente JavaScript personalizzato.

## Tecnologie usate

- Python
- Django
- SQLite
- HTML
- CSS
- Pillow, per la gestione delle immagini

## Avvio del progetto

Clonare il repository e aprire un terminale nella cartella del progetto, dove si trova il file `manage.py`.

Creare un ambiente virtuale:

```bash
python -m venv .venv
```

Attivare l'ambiente virtuale.

Su Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Su macOS/Linux:

```bash
source .venv/bin/activate
```

Installare le dipendenze:

```bash
python -m pip install -r requirements.txt
```

Applicare le migrazioni, se necessario:

```bash
python manage.py migrate
```

Avviare il server locale:

```bash
python manage.py runserver
```

Aprire il browser su:

```text
http://127.0.0.1:8000/
```

## Database e dati demo

Nel repository è presente il file `db.sqlite3`, già popolato con dati dimostrativi. Questo permette di provare subito il sito senza dover inserire manualmente categorie, attrezzature e prenotazioni.

Se si vuole ricreare il database da zero:

```bash
python manage.py migrate
python manage.py seed_demo --with-users
```

Il comando `seed_demo` inserisce categorie, attrezzature, utenti demo e alcune prenotazioni di esempio.

## Account demo

Gli account dimostrativi sono:

```text
cliente_demo
gestore_demo
admin_demo
```

La password è uguale per tutti:

```text
Demo12345!
```

Ruoli:

- `cliente_demo`: può prenotare attrezzature e vedere i propri noleggi;
- `gestore_demo`: può accedere all'area gestione;
- `admin_demo`: può accedere anche al Django Admin.

## Struttura del progetto

```text
SportRent/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── sport_rental/          configurazione generale del progetto Django
├── rentals/               app principale del noleggio
├── templates/             template HTML delle pagine
└── media/                 immagini delle attrezzature
```

File principali dell'app `rentals`:

```text
rentals/models.py          modelli del database
rentals/forms.py           form e controlli sui dati inseriti
rentals/services.py        logica di disponibilità e creazione prenotazioni
rentals/views.py           viste e flussi delle pagine
rentals/urls.py            URL dell'applicazione
rentals/permissions.py     controllo dei permessi per l'area gestore
rentals/admin.py           configurazione del Django Admin
```

## Logica di disponibilità

La disponibilità delle attrezzature viene gestita in `rentals/services.py`.

Una prenotazione occupa un'attrezzatura solo se:

- è confermata;
- riguarda lo stesso articolo;
- il periodo si sovrappone a quello richiesto.

Le prenotazioni cancellate non occupano più disponibilità. La creazione della prenotazione avviene dentro una transazione, così si evitano salvataggi parziali.

## Test

Per eseguire i test automatici:

```bash
python manage.py test
```

Sono presenti test mirati ma completi su:

- disponibilità delle attrezzature;
- sovrapposizione delle prenotazioni;
- rifiuto dell'overbooking;
- cancellazione di una prenotazione;
- catalogo guidato;
- controllo delle date nel passato;
- registrazione e login;
- storico cliente;
- area gestore;
- Django Admin.

## Note

Il progetto è pensato per una dimostrazione universitaria e per l'esecuzione in locale. Prima di un eventuale utilizzo reale andrebbero rivisti aspetti come sicurezza, gestione delle credenziali, configurazione di produzione e database.
