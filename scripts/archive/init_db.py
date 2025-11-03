#!/usr/bin/env python3
"""
Skrypt inicjalizacji bazy danych

Ten skrypt konfiguruje bazę danych PostgreSQL dla aplikacji:
1. Włącza rozszerzenie pgvector (wektory do embeddings AI)
2. Tworzy wszystkie tabele z modeli SQLAlchemy

Użycie:
    python scripts/archive/init_db.py
    python -m scripts.archive.init_db

Uwaga: Wymaga działającej bazy PostgreSQL i poprawnych danych w .env
"""
import asyncio
import sys
from pathlib import Path

# Umożliwia uruchamianie jako "python scripts/archive/init_db.py"
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from app.db import engine, Base
from app.models import Project, Persona, PersonaEvent, PersonaResponse, FocusGroup


async def init_db():
    """
    Inicjalizuje bazę danych

    Proces:
    1. Tworzy connection do PostgreSQL (używając engine z app.db)
    2. Włącza rozszerzenie pgvector (jeśli nie istnieje)
       - pgvector umożliwia przechowywanie wektorów embeddings dla AI
    3. Tworzy tabele zdefiniowane w Base.metadata (wszystkie modele SQLAlchemy)
       - Project - projekty badawcze
       - Persona - wygenerowane persony
       - PersonaEvent - historia działań person
       - PersonaResponse - odpowiedzi person w dyskusjach
       - FocusGroup - grupy fokusowe

    Bezpiecznie: CREATE IF NOT EXISTS - nie nadpisuje istniejących danych
    """
    print("Creating database tables...")

    async with engine.begin() as conn:
        # Włącz rozszerzenie pgvector (potrzebne do przechowywania wektorów embeddings)
        print("Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Utwórz wszystkie tabele z modeli (Project, Persona, PersonaEvent, etc.)
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database initialization complete!")


if __name__ == "__main__":
    # Uruchom funkcję asynchroniczną init_db()
    asyncio.run(init_db())
