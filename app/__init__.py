"""
Sight - Backend API

Platforma do przeprowadzania badań rynkowych z wykorzystaniem AI (Google Gemini).

Główne moduły:
- api: Endpointy REST API (projekty, persony, grupy fokusowe, ankiety, analizy)
- models: Modele bazy danych SQLAlchemy (Project, Persona, FocusGroup, Survey, etc.)
- services: Logika biznesowa (generatory person, orkiestracja dyskusji, podsumowania AI)
- schemas: Schematy Pydantic do walidacji danych wejściowych/wyjściowych
- core: Konfiguracja aplikacji (settings, stałe)
- db: Warstwa bazodanowa (sesje, engine, Base)

Architektura:
FastAPI + PostgreSQL + Neo4j + Redis + Google Gemini (LangChain)

Wersja: 1.0.0
"""

__version__ = "1.0.0"
