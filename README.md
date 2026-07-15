# SportRent

SportRent è un progetto Django per il noleggio di attrezzature sportive.
L'utente sceglie prima la categoria sportiva, poi il periodo di noleggio e infine vede solo gli articoli disponibili in quelle date.

Il sito usa template HTML generati da Django e un file CSS semplice per rendere le pagine pi? ordinate. Non sono presenti file JavaScript personalizzati.

## Cosa si può fare

- consultare le categorie anche senza login;
- scegliere una categoria e poi indicare le date del noleggio;
- vedere solo le attrezzature disponibili della categoria scelta;
- registrarsi e accedere come cliente;
- creare una prenotazione con una o più attrezzature della stessa categoria;
- vedere i propri noleggi attivi, futuri, conclusi e cancellati;
- cancellare una prenotazione futura;
- usare un pannello gestore per attrezzature, categorie e prenotazioni;
- filtrare le attrezzature per categoria nell'area gestore;
- usare il Django Admin per la gestione tecnica.

## Come avviare il progetto

Estrarre lo ZIP e aprire un terminale nella cartella dove si trova il file `manage.py`.

Creare l'ambiente virtuale:

```powershell
python -m venv .venv
```

Attivare l'ambiente virtuale:

```powershell
.\.venv\Scripts\Activate.ps1
```

Installare le librerie richieste:

```powershell
python -m pip install -r requirements.txt
```

Il database `db.sqlite3` è già presente e contiene dati demo. Per avviare il sito:

```powershell
python manage.py runserver
```

Aprire il browser su:

```text
http://127.0.0.1:8000/
```

## Se PowerShell blocca l'attivazione

Su alcuni PC PowerShell può bloccare il file `Activate.ps1`. In quel caso si può usare direttamente il Python dell'ambiente virtuale:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py runserver
```

## Ricreare il database da zero

Se si vuole ripartire da un database pulito:

```powershell
del db.sqlite3
python manage.py migrate
python manage.py seed_demo --with-users
```

Poi avviare nuovamente il server:

```powershell
python manage.py runserver
```

## Account demo

Il comando `seed_demo --with-users` crea questi account:

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

- `cliente_demo`: può prenotare e vedere i propri noleggi;
- `gestore_demo`: può entrare nell'area gestione;
- `admin_demo`: può entrare anche nel Django Admin.

## Dati demo

Il catalogo contiene 22 attrezzature divise in 7 categorie:

- Sci;
- Ciclismo;
- Sport acquatici;
- Fitness;
- Tennis;
- Calcio;
- Arrampicata.

Sono presenti immagini per diversi articoli. Una panca fitness è disattivata, così si vede la differenza tra catalogo pubblico e gestione interna.

Nel database sono presenti alcune prenotazioni demo:

- una conclusa;
- una in corso;
- una futura;
- una cancellata.

Questi dati servono per mostrare subito storico, filtri e stati dei noleggi.

## File principali

```text
sport_rental/        configurazione generale del progetto
rentals/models.py    tabelle principali del database
rentals/forms.py     form e controlli sugli input
rentals/views.py     pagine e flussi del sito
rentals/services.py  regole su disponibilità e prenotazioni
rentals/admin.py     configurazione del Django Admin
templates/           pagine HTML
```

La parte più importante è in `rentals/services.py`, dove viene controllata la disponibilità degli articoli. Due prenotazioni si sovrappongono quando hanno almeno un giorno in comune. Le prenotazioni cancellate non occupano più attrezzature.

## Test

Per eseguire i test:

```powershell
python manage.py test
```

Sono presenti 10 test automatici, pochi ma completi. Coprono disponibilità, sovrapposizioni, cancellazione, catalogo guidato, data nel passato, prenotazione, storico cliente, area gestore e Django Admin.