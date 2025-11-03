"""
Moduł Core - Konfiguracja Aplikacji

⚠️ DEPRECATION NOTICE ⚠️

The get_settings() adapter has been REMOVED (PR4).

OLD (deprecated):
    from app.core import get_settings
    settings = get_settings()
    api_key = settings.GOOGLE_API_KEY

NEW (current):
    from config import app, features, models
    api_key = os.getenv("GOOGLE_API_KEY")
    db_url = app.database.url
    rag_enabled = features.rag.enabled

See config/README.md for complete migration guide.

Zawiera:
- Settings: DEPRECATED adapter class (kept for internal use by config/app_loader.py)
- constants.py: Stałe używane w całej aplikacji (demografia, lokalizacje, rozkłady)
"""

from .config import Settings

__all__ = ["Settings"]