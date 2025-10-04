"""
Bazowa klasa dla modeli SQLAlchemy

Ten moduł definiuje klasę bazową Base używaną przez wszystkie modele ORM.

Base - klasa bazowa SQLAlchemy
Wszystkie modele (Project, Persona, FocusGroup, etc.) dziedziczą po Base:
- Automatyczne mapowanie tabel do klas Pythona
- Zarządzanie metadanymi (nazwy tabel, kolumny, relacje)
- Integracja z sessionami i query API

Użycie w modelach:
    from app.db.base import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        id = Column(UUID, primary_key=True)
        ...

Migracje Alembic używają Base.metadata do:
- Autogenerowania migracji (alembic revision --autogenerate)
- Tworzenia/aktualizacji tabel (Base.metadata.create_all())
"""

from sqlalchemy.ext.declarative import declarative_base

# Klasa bazowa dla wszystkich modeli ORM
Base = declarative_base()
