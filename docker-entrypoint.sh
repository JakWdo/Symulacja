#!/bin/sh
set -e

echo "--- Docker Entrypoint: Czekam na gotowość bazy danych ---"
sleep 5

echo "--- Docker Entrypoint: Inicjalizuję bazę danych (tworzę tabele)... ---"
# POPRAWKA: Używamy flagi -m, aby uruchomić skrypt jako moduł
python -m scripts.init_db

echo "--- Docker Entrypoint: Uruchamiam serwer Uvicorn... ---"
exec "$@"