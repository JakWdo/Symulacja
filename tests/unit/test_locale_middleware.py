"""
Unit tests dla locale middleware.

Testuje:
- normalize_language() - normalizację kodów językowych
- get_locale() - dependency dla odczytu locale z requestu

Pokrycie:
- Różne formaty locale (pl-PL, en-US, pl, en)
- Fallback do domyślnego języka (pl)
- Priority: Accept-Language > user.preferred_language > default
- Edge cases (empty headers, niepoprawne kody)
"""
import pytest
from unittest.mock import MagicMock
from fastapi import Request

from app.middleware.locale import normalize_language, get_locale


class TestNormalizeLanguage:
    """Testy dla funkcji normalize_language"""

    def test_normalize_polish_locale(self):
        """Test normalizacji polskiego locale (pl-PL → pl)"""
        assert normalize_language('pl-PL') == 'pl'

    def test_normalize_english_locale(self):
        """Test normalizacji angielskiego locale (en-US → en)"""
        assert normalize_language('en-US') == 'en'

    def test_normalize_polish_short(self):
        """Test krótkiego kodu polskiego (pl → pl)"""
        assert normalize_language('pl') == 'pl'

    def test_normalize_english_short(self):
        """Test krótkiego kodu angielskiego (en → en)"""
        assert normalize_language('en') == 'en'

    def test_normalize_with_underscore_separator(self):
        """Test locale z separatorem underscore (POSIX style: pl_PL → pl)"""
        assert normalize_language('pl_PL') == 'pl'
        assert normalize_language('en_US') == 'en'

    def test_normalize_unsupported_language(self):
        """Test niewspieranego języka (fallback do 'pl')"""
        assert normalize_language('fr') == 'pl'
        assert normalize_language('de-DE') == 'pl'
        assert normalize_language('es-ES') == 'pl'

    def test_normalize_empty_string(self):
        """Test pustego stringu (fallback do 'pl')"""
        assert normalize_language('') == 'pl'

    def test_normalize_none(self):
        """Test None (fallback do 'pl')"""
        assert normalize_language(None) == 'pl'

    def test_normalize_case_insensitive(self):
        """Test case-insensitive normalizacji"""
        assert normalize_language('PL-PL') == 'pl'
        assert normalize_language('EN-US') == 'en'  # EN (uppercase) jest rozpoznawane (lower() w funkcji)
        assert normalize_language('Pl') == 'pl'
        assert normalize_language('En') == 'en'  # Podobnie


@pytest.mark.asyncio
class TestGetLocale:
    """Testy dla dependency get_locale"""

    async def test_locale_from_accept_language_header_polish(self):
        """Test odczytu locale z Accept-Language header (polski)"""
        # Mock request z headerem Accept-Language: pl-PL
        request = MagicMock(spec=Request)
        request.headers = {'accept-language': 'pl-PL'}
        request.state = MagicMock()

        locale = await get_locale(request)

        assert locale == 'pl'
        assert request.state.locale == 'pl'

    async def test_locale_from_accept_language_header_english(self):
        """Test odczytu locale z Accept-Language header (angielski)"""
        request = MagicMock(spec=Request)
        request.headers = {'accept-language': 'en-US'}
        request.state = MagicMock()

        locale = await get_locale(request)

        assert locale == 'en'
        assert request.state.locale == 'en'

    async def test_locale_from_accept_language_with_quality_values(self):
        """Test Accept-Language z quality values (pl-PL,pl;q=0.9,en;q=0.8)"""
        # Browser często wysyła quality values - bierzemy pierwszy język
        request = MagicMock(spec=Request)
        request.headers = {'accept-language': 'pl-PL,pl;q=0.9,en;q=0.8'}
        request.state = MagicMock()

        locale = await get_locale(request)

        assert locale == 'pl'
        assert request.state.locale == 'pl'

    async def test_locale_from_accept_language_english_quality_values(self):
        """Test Accept-Language z angielskim jako pierwszym"""
        request = MagicMock(spec=Request)
        request.headers = {'accept-language': 'en-US,en;q=0.9,pl;q=0.8'}
        request.state = MagicMock()

        locale = await get_locale(request)

        assert locale == 'en'
        assert request.state.locale == 'en'

    async def test_locale_from_user_profile_when_no_header(self):
        """Test fallback do user.preferred_language gdy brak headera"""
        # Mock user z preferred_language='en'
        mock_user = MagicMock()
        mock_user.preferred_language = 'en'

        request = MagicMock(spec=Request)
        request.headers = {}  # Brak Accept-Language
        request.state = MagicMock()
        request.state.current_user = mock_user

        locale = await get_locale(request)

        assert locale == 'en'
        assert request.state.locale == 'en'

    async def test_locale_from_user_profile_polish(self):
        """Test fallback do user.preferred_language='pl'"""
        mock_user = MagicMock()
        mock_user.preferred_language = 'pl-PL'

        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        request.state.current_user = mock_user

        locale = await get_locale(request)

        assert locale == 'pl'
        assert request.state.locale == 'pl'

    async def test_locale_default_when_no_header_no_user(self):
        """Test default fallback (pl) gdy brak headera i użytkownika"""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        # Brak current_user (niezalogowany)
        delattr(request.state, 'current_user')

        locale = await get_locale(request)

        assert locale == 'pl'
        assert request.state.locale == 'pl'

    async def test_locale_default_when_user_has_no_preferred_language(self):
        """Test default gdy user nie ma preferred_language"""
        mock_user = MagicMock()
        # User nie ma atrybutu preferred_language
        if hasattr(mock_user, 'preferred_language'):
            delattr(mock_user, 'preferred_language')

        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        request.state.current_user = mock_user

        locale = await get_locale(request)

        assert locale == 'pl'
        assert request.state.locale == 'pl'

    async def test_locale_priority_header_over_user(self):
        """Test priorytetu: Accept-Language ma wyższy priorytet niż user.preferred_language"""
        # Header: en-US, User: pl
        mock_user = MagicMock()
        mock_user.preferred_language = 'pl'

        request = MagicMock(spec=Request)
        request.headers = {'accept-language': 'en-US'}
        request.state = MagicMock()
        request.state.current_user = mock_user

        locale = await get_locale(request)

        # Header powinien wygrać
        assert locale == 'en'
        assert request.state.locale == 'en'

    async def test_locale_empty_accept_language_falls_back_to_user(self):
        """Test pustego Accept-Language headera (fallback do user)"""
        mock_user = MagicMock()
        mock_user.preferred_language = 'en'

        request = MagicMock(spec=Request)
        request.headers = {'accept-language': ''}  # Pusty string
        request.state = MagicMock()
        request.state.current_user = mock_user

        locale = await get_locale(request)

        # Pusty header jest ignorowany, więc fallback do user
        assert locale == 'en'
        assert request.state.locale == 'en'

    async def test_locale_unsupported_language_in_header(self):
        """Test niewspieranego języka w headerze (fallback do 'pl')"""
        request = MagicMock(spec=Request)
        request.headers = {'accept-language': 'fr-FR'}  # Francuski nie jest wspierany
        request.state = MagicMock()

        locale = await get_locale(request)

        # Niewspierany język → fallback do 'pl'
        assert locale == 'pl'
        assert request.state.locale == 'pl'
