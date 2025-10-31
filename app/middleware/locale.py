"""
Middleware dla zarządzania locale użytkownika.

Odczytuje język z Accept-Language header i zapisuje do request.state.locale.
Fallback: preferred_language z profilu użytkownika (jeśli zalogowany).

Priority:
1. Accept-Language header (wysyłany przez frontend)
2. current_user.preferred_language (jeśli zalogowany)
3. Default: 'pl' (polski)

Usage:
    from app.middleware.locale import get_locale

    @router.post("/some-endpoint")
    async def some_endpoint(
        locale: str = Depends(get_locale),
        current_user: User = Depends(get_current_user)
    ):
        # Use locale in business logic
        result = await some_service.do_something(locale=locale)
        return result
"""
import logging
from fastapi import Request
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_language(lang_code: str) -> str:
    """
    Normalizuje kod języka do 'pl' lub 'en'.

    Obsługuje różne formaty locale:
    - 'pl-PL' → 'pl'
    - 'en-US' → 'en'
    - 'pl' → 'pl'
    - 'en' → 'en'
    - 'fr' → 'pl' (fallback dla niewspieranych języków)

    Args:
        lang_code: Kod języka (np. 'pl-PL', 'en-US', 'pl', 'en')

    Returns:
        'pl' lub 'en'

    Examples:
        >>> normalize_language('pl-PL')
        'pl'
        >>> normalize_language('en-US')
        'en'
        >>> normalize_language('pl')
        'pl'
        >>> normalize_language('fr')
        'pl'
    """
    if not lang_code:
        return 'pl'  # Default to Polish

    # Wyciągnij język z locale (pl-PL -> pl, en-US -> en)
    # Obsługuj separatory: '-' (BCP 47) i '_' (POSIX)
    lang = lang_code.split('-')[0].split('_')[0].lower()

    # Wspierane języki: pl, en
    if lang in ['pl', 'en']:
        return lang

    # Default fallback dla niewspieranych języków
    logger.debug(f"Unsupported language code '{lang_code}', falling back to 'pl'")
    return 'pl'


async def get_locale(request: Request) -> str:
    """
    Dependency dla odczytywania locale z requestu.

    Priority:
    1. Accept-Language header (wysyłany przez frontend w każdym requeście)
    2. current_user.preferred_language (jeśli zalogowany)
    3. Default: 'pl'

    Zapisuje wynik do request.state.locale dla późniejszego użycia.

    Args:
        request: FastAPI request object

    Returns:
        Kod języka: 'pl' lub 'en'

    Examples:
        >>> # Request z headerem Accept-Language: en-US
        >>> locale = await get_locale(request)
        >>> print(locale)
        'en'

        >>> # Request bez headera, użytkownik zalogowany z preferred_language='en'
        >>> locale = await get_locale(request)
        >>> print(locale)
        'en'

        >>> # Request bez headera, użytkownik niezalogowany
        >>> locale = await get_locale(request)
        >>> print(locale)
        'pl'
    """
    # 1. Sprawdź Accept-Language header (highest priority)
    # Frontend wysyła ten header w każdym requeście z wyborem języka
    accept_language = request.headers.get('accept-language', '')
    if accept_language:
        # Accept-Language może zawierać quality values (pl-PL,pl;q=0.9,en;q=0.8)
        # Bierzemy tylko pierwszy język (przed przecinkiem lub średnikiem)
        primary_lang = accept_language.split(',')[0].split(';')[0].strip()
        locale = normalize_language(primary_lang)
        request.state.locale = locale
        logger.debug(f"Locale from Accept-Language header: {locale}")
        return locale

    # 2. Sprawdź current_user.preferred_language (jeśli jest zalogowany)
    # current_user jest ustawiany przez get_current_user dependency
    if hasattr(request.state, 'current_user') and request.state.current_user:
        user_lang = getattr(request.state.current_user, 'preferred_language', None)
        if user_lang:
            locale = normalize_language(user_lang)
            request.state.locale = locale
            logger.debug(f"Locale from user profile: {locale}")
            return locale

    # 3. Default fallback (polski - domyślny język produktu)
    request.state.locale = 'pl'
    logger.debug("Locale defaulted to 'pl'")
    return 'pl'
