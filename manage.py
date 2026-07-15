#!/usr/bin/env python
"""Punto di ingresso dei comandi Django.

Da qui partono comandi come migrate, runserver, test e seed_demo.
"""
import os
import sys 


def main():
    # Indica a Django quale file settings usare per questo progetto.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sport_rental.settings")
    #setdefault() importa il valore slo se non esiste già, quindi non sovrascrive
    #eventuali confifuaiozni già presenti

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
    
        raise ImportError(
            "Django non è installato. Esegui: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

#imposta il file delle configurazioni del progetto
