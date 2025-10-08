"""
Moduł Core - Konfiguracja Aplikacji

Zawiera:
- Settings: Klasa z konfiguracją aplikacji (zmienne środowiskowe, API keys, parametry LLM)
- get_settings(): Singleton dostarczający instancję Settings z cache'owaniem
- constants.py: Stałe używane w całej aplikacji (demografia, lokalizacje, rozkłady)

Użycie:
    from app.core import get_settings
    settings = get_settings()
    api_key = settings.GOOGLE_API_KEY
"""

from .config import get_settings, Settings

__all__ = ["get_settings", "Settings"]