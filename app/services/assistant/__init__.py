"""
Product Assistant Service Module

Lightweight AI helper do wspierania użytkowników platformy Sight.
Stateless - nie zapisuje historii w bazie danych.
"""

from app.services.assistant.assistant_service import AssistantService

__all__ = ["AssistantService"]
