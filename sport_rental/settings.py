"""Impostazioni principali del progetto Django SportRent."""

from pathlib import Path


# Configurazione generale del progetto: app installate, database, lingua,
# percorsi media/static e comportamento di login/logout.
BASE_DIR = Path(__file__).resolve().parent.parent

# Impostazioni adatte alla dimostrazione locale. Il README descrive le
# modifiche necessarie prima di un'eventuale pubblicazione reale.
SECRET_KEY = "django-insecure-change-this-key-before-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Elenco delle applicazioni Django attive, compresa rentals.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rentals",
]

# Componenti che gestiscono sicurezza, sessione e messaggi a ogni richiesta.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Indica il file che contiene gli indirizzi principali del sito.
ROOT_URLCONF = "sport_rental.urls"

# Configura dove Django cerca i template HTML.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Riferimento usato dai server web tradizionali per avviare Django.
WSGI_APPLICATION = "sport_rental.wsgi.application"
ASGI_APPLICATION = "sport_rental.asgi.application"

# Database SQLite locale: semplice da consegnare e avviare per il progetto.
DATABASES = {
    "default": {
        # SQLite è sufficiente per la demo locale e non richiede server esterni.
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Regole Django per impedire password troppo deboli.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

# Lingua e fuso orario usati nella visualizzazione delle date.
LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

# Percorsi separati per file statici e immagini caricate dal gestore.
STATIC_URL = "static/"
MEDIA_URL = "media/"
# Le immagini caricate dal gestore vengono salvate nella cartella media.
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "equipment_list"
LOGOUT_REDIRECT_URL = "equipment_list"
