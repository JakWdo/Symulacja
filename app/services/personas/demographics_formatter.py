"""
Formatowanie i normalizacja danych demograficznych dla polskich person.

Ten moduł zawiera narzędzia do:
- Konwersji danych demograficznych (EN → PL)
- Normalizacji lokalizacji (zapewnienie polskich miast)
- Ekstrakcji informacji z background stories
- Wnioskowania zawodów bazując na kontekście
- Formatowania nazw i tytułów

Użycie:
    formatter = DemographicsFormatter()
    gender_pl = formatter.polishify_gender("female")  # "Kobieta"
    location = formatter.ensure_polish_location("Warsaw", story)  # "Warszawa"
"""

import logging
import random
import re
import unicodedata
from typing import Any

from config import demographics

logger = logging.getLogger(__name__)


# ============================================================================
# STAŁE - Słowniki Konwersji i Wzorce
# ============================================================================

_POLISH_CHARACTERS = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"

_POLISH_CITY_LOOKUP = {
    "warszawa": "Warszawa",
    "krakow": "Kraków",
    "wroclaw": "Wrocław",
    "poznan": "Poznań",
    "gdansk": "Gdańsk",
    "szczecin": "Szczecin",
    "bydgoszcz": "Bydgoszcz",
    "lublin": "Lublin",
    "katowice": "Katowice",
    "bialystok": "Białystok",
    "gdynia": "Gdynia",
    "czestochowa": "Częstochowa",
    "radom": "Radom",
    "sosnowiec": "Sosnowiec",
    "torun": "Toruń",
    "kielce": "Kielce",
    "gliwice": "Gliwice",
    "zabrze": "Zabrze",
    "bytom": "Bytom",
    "olsztyn": "Olsztyn",
    "rzeszow": "Rzeszów",
    "ruda slaska": "Ruda Śląska",
    "rybnik": "Rybnik",
    "tychy": "Tychy",
    "dabrowa gornicza": "Dąbrowa Górnicza",
    "lodz": "Łódź",
    "opole": "Opole",
    "trojmiasto": "Trójmiasto",
}

_EN_TO_PL_GENDER = {
    "female": "Kobieta",
    "male": "Mężczyzna",
    "non-binary": "Osoba niebinarna",
    "nonbinary": "Osoba niebinarna",
    "other": "Inna",
    "kobieta": "Kobieta",
    "mezczyzna": "Mężczyzna",
    "mężczyzna": "Mężczyzna",
}

_EN_TO_PL_EDUCATION = {
    "high school": "Średnie ogólnokształcące",
    "high school or equivalent": "Średnie ogólnokształcące",
    "some college": "W trakcie studiów",
    "bachelor's degree": "Wyższe licencjackie",
    "bachelor": "Wyższe licencjackie",
    "master's degree": "Wyższe magisterskie",
    "master": "Wyższe magisterskie",
    "master's degree or above": "Wyższe magisterskie",
    "phd": "Doktorat",
    "doctorate": "Doktorat",
    "podstawowe": "Podstawowe",
    "zawodowe": "Zawodowe",
    "srednie": "Średnie ogólnokształcące",
    "średnie": "Średnie ogólnokształcące",
    "wyzsze": "Wyższe licencjackie",
    "wyższe": "Wyższe licencjackie",
}

_EN_TO_PL_INCOME = {
    "< $25k": "< 3 000 zł",
    "$25k-$50k": "3 000 - 5 000 zł",
    "$50k-$75k": "5 000 - 7 500 zł",
    "$75k-$100k": "7 500 - 10 000 zł",
    "$100k-$150k": "10 000 - 15 000 zł",
    "> $150k": "> 15 000 zł",
    "$150k+": "> 15 000 zł",
}

_ADDITIONAL_CITY_ALIASES = {
    "warsaw": "Warszawa",
    "krakow": "Kraków",
    "wroclaw": "Wrocław",
    "poznan": "Poznań",
    "lodz": "Łódź",
    "gdansk": "Gdańsk",
    "gdynia": "Gdynia",
    "szczecin": "Szczecin",
    "lublin": "Lublin",
    "bialystok": "Białystok",
    "bydgoszcz": "Bydgoszcz",
    "katowice": "Katowice",
    "czestochowa": "Częstochowa",
    "torun": "Toruń",
    "radom": "Radom",
}

# Regex patterns dla ekstrakcji z background stories
_NAME_FROM_STORY_PATTERN = re.compile(r"^(?P<name>[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)+)")
_AGE_IN_STORY_PATTERN = re.compile(r"(?P<age>\d{1,2})-year-old", re.IGNORECASE)
_POLISH_AGE_PATTERNS = [
    re.compile(r"(?:ma|mam|wieku)\s+(?P<age>\d{1,2})\s+lat", re.IGNORECASE),
    re.compile(r"(?P<age>\d{1,2})-letni[a]?", re.IGNORECASE),
    re.compile(r"lat\s+(?P<age>\d{1,2})", re.IGNORECASE),
]

_BACKGROUND_JOB_PATTERNS = [
    re.compile(r"pracuje jako (?P<job>[^\.,]+)", re.IGNORECASE),
    re.compile(r"jest (?P<job>[^\.,]+) w", re.IGNORECASE),
    re.compile(r"na stanowisku (?P<job>[^\.,]+)", re.IGNORECASE),
    re.compile(r"pełni funkcję (?P<job>[^\.,]+)", re.IGNORECASE),
]


# ============================================================================
# Klasa DemographicsFormatter
# ============================================================================

class DemographicsFormatter:
    """
    Formatowanie i normalizacja danych demograficznych dla polskich person.

    Metody służą do konwersji danych z różnych formatów (angielski, polski, mieszany)
    na jednolity polski format zgodny z demografią Polski.
    """

    @staticmethod
    def normalize_text(value: str | None) -> str:
        """
        Usuń diakrytyki i sprowadź tekst do małych liter – pomocne przy dopasowaniach.

        Args:
            value: Tekst do normalizacji

        Returns:
            Znormalizowany tekst (lowercase, bez diakrytyków)

        Example:
            >>> DemographicsFormatter.normalize_text("Kraków")
            'krakow'
        """
        if not value:
            return ""
        normalized = unicodedata.normalize("NFD", value)
        stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return stripped.lower().strip()

    @staticmethod
    def polishify_gender(raw_gender: str | None) -> str:
        """
        Przekonwertuj nazwy płci na polskie odpowiedniki.

        Args:
            raw_gender: Płeć w formacie EN lub PL (female, male, kobieta, etc.)

        Returns:
            Płeć w formacie polskim (Kobieta, Mężczyzna, Osoba niebinarna)

        Example:
            >>> DemographicsFormatter.polishify_gender("female")
            'Kobieta'
        """
        normalized = DemographicsFormatter.normalize_text(raw_gender)
        return _EN_TO_PL_GENDER.get(normalized, raw_gender.title() if raw_gender else "Kobieta")

    @staticmethod
    def polishify_education(raw_education: str | None) -> str:
        """
        Przekonwertuj poziom wykształcenia na polską etykietę.

        Args:
            raw_education: Wykształcenie w formacie EN lub PL

        Returns:
            Wykształcenie w formacie polskim (Wyższe magisterskie, Średnie, etc.)

        Example:
            >>> DemographicsFormatter.polishify_education("bachelor's degree")
            'Wyższe licencjackie'
        """
        normalized = DemographicsFormatter.normalize_text(raw_education)
        if normalized in _EN_TO_PL_EDUCATION:
            return _EN_TO_PL_EDUCATION[normalized]
        if raw_education:
            return raw_education
        # Fallback - losuj z rozkładu Polski
        from app.services.personas.distribution_builder import DistributionBuilder
        return DistributionBuilder.select_weighted(demographics.poland.education_levels) or "Średnie ogólnokształcące"

    @staticmethod
    def polishify_income(raw_income: str | None) -> str:
        """
        Przekonwertuj przedział dochodowy na złotówki.

        Args:
            raw_income: Dochód w formacie dolarowym ($25k-$50k) lub złotówkach

        Returns:
            Dochód w złotówkach (3 000 - 5 000 zł, etc.)

        Example:
            >>> DemographicsFormatter.polishify_income("$50k-$75k")
            '5 000 - 7 500 zł'
        """
        normalized = raw_income.strip() if isinstance(raw_income, str) else None
        if normalized:
            normalized_key = normalized.replace(" ", "")
            if normalized in _EN_TO_PL_INCOME:
                return _EN_TO_PL_INCOME[normalized]
            if normalized_key in _EN_TO_PL_INCOME:
                return _EN_TO_PL_INCOME[normalized_key]
        if raw_income:
            return raw_income
        # Fallback - losuj z rozkładu Polski
        from app.services.personas.distribution_builder import DistributionBuilder
        return DistributionBuilder.select_weighted(demographics.poland.income_brackets) or "5 000 - 7 500 zł"

    @staticmethod
    def extract_polish_location_from_story(story: str | None) -> str | None:
        """
        Spróbuj znaleźć polską lokalizację wewnątrz historii tła persony.

        Obsługuje fleksję (Warszawie, Gdańsku, z Krakowa).

        Args:
            story: Background story persony

        Returns:
            Nazwa polskiego miasta lub None

        Example:
            >>> story = "Mieszka w Gdańsku od 5 lat."
            >>> DemographicsFormatter.extract_polish_location_from_story(story)
            'Gdańsk'
        """
        if not story:
            return None
        normalized_story = DemographicsFormatter.normalize_text(story)
        for normalized_city, original_city in _POLISH_CITY_LOOKUP.items():
            if normalized_city and normalized_city in normalized_story:
                return original_city
            # Obsługa odmian fleksyjnych (np. Wrocławiu, Gdańsku)
            if normalized_city.endswith("a") and normalized_city + "ch" in normalized_story:
                return original_city
            if normalized_city + "iu" in normalized_story or normalized_city + "u" in normalized_story:
                return original_city
            if normalized_city + "ie" in normalized_story:
                return original_city
        return None

    @staticmethod
    def ensure_polish_location(location: str | None, story: str | None) -> str:
        """
        Zadbaj aby lokalizacja była polska – użyj historii lub losowania z listy.

        Args:
            location: Raw location (może być angielska nazwa, np. "Warsaw")
            story: Background story persony (do ekstrakcji lokalizacji)

        Returns:
            Polska nazwa miasta (Warszawa, Kraków, etc.)

        Example:
            >>> DemographicsFormatter.ensure_polish_location("Warsaw", None)
            'Warszawa'
        """
        normalized = DemographicsFormatter.normalize_text(location)
        if normalized:
            if normalized in _POLISH_CITY_LOOKUP:
                return _POLISH_CITY_LOOKUP[normalized]
            if normalized in _ADDITIONAL_CITY_ALIASES:
                return _ADDITIONAL_CITY_ALIASES[normalized]
            # Usuń przyrostki typu ", ca" itp.
            stripped_parts = re.split(r"[,/\\]", normalized)
            for part in stripped_parts:
                part = part.strip()
                if part in _POLISH_CITY_LOOKUP:
                    return _POLISH_CITY_LOOKUP[part]
                if part in _ADDITIONAL_CITY_ALIASES:
                    return _ADDITIONAL_CITY_ALIASES[part]
        story_city = DemographicsFormatter.extract_polish_location_from_story(story)
        if story_city:
            return story_city
        # Fallback - losuj z rozkładu Polski
        from app.services.personas.distribution_builder import DistributionBuilder
        fallback = DistributionBuilder.select_weighted(demographics.poland.locations) or "Warszawa"
        return fallback

    @staticmethod
    def looks_polish_phrase(text: str | None) -> bool:
        """
        Sprawdź heurystycznie czy tekst wygląda na polski (znaki diakrytyczne, słowa kluczowe).

        Args:
            text: Tekst do sprawdzenia

        Returns:
            True jeśli tekst wygląda na polski
        """
        if not text:
            return False
        lowered = text.strip().lower()
        if any(char in text for char in _POLISH_CHARACTERS):
            return True
        keywords = ["specjalista", "menedżer", "koordynator", "student", "uczeń", "właściciel", "kierownik", "logistyk"]
        return any(keyword in lowered for keyword in keywords)

    @staticmethod
    def format_job_title(job: str) -> str:
        """
        Ujednolicenie formatowania tytułu zawodowego (capitalize first letter).

        Args:
            job: Tytuł zawodowy

        Returns:
            Sformatowany tytuł (pierwsza litera wielka)
        """
        job = job.strip()
        if not job:
            return job
        return job[0].upper() + job[1:]

    @staticmethod
    def infer_polish_occupation(
        education_level: str | None,
        income_bracket: str | None,
        age: int,
        personality: dict[str, Any],
        background_story: str | None,
    ) -> str:
        """
        Ustal możliwie polski tytuł zawodowy bazując na dostępnych danych.

        Priorytet:
        1. personality["persona_title"] lub personality["occupation"] (jeśli polski)
        2. Ekstrakcja z background_story (regex patterns)
        3. Losowanie z demographics.poland.occupations
        4. Fallback: demographics.international.occupations lub "Specjalista"

        Args:
            education_level: Poziom wykształcenia
            income_bracket: Przedział dochodowy
            age: Wiek
            personality: Dict z danymi personality (może zawierać persona_title, occupation)
            background_story: Historia życiowa persony

        Returns:
            Polski tytuł zawodowy
        """
        candidate = personality.get("persona_title") or personality.get("occupation")
        if candidate and DemographicsFormatter.looks_polish_phrase(candidate):
            return DemographicsFormatter.format_job_title(candidate)

        if background_story:
            for pattern in _BACKGROUND_JOB_PATTERNS:
                match = pattern.search(background_story)
                if match:
                    job = match.group("job").strip()
                    if job:
                        return DemographicsFormatter.format_job_title(job)

        # Jeżeli AI nie zwróciło spójnego polskiego zawodu – losuj realistyczny zawód z rozkładu
        from app.services.personas.distribution_builder import DistributionBuilder
        occupation = DistributionBuilder.select_weighted(demographics.poland.occupations)
        if occupation:
            return occupation

        # Fallback na wylosowaną angielską listę (ostatnia linia obrony)
        return random.choice(demographics.international.occupations) if demographics.international.occupations else "Specjalista"

    @staticmethod
    def fallback_polish_list(source: list[str] | None, fallback_pool: list[str]) -> list[str]:
        """
        Zapewnij, że listy wartości i zainteresowań mają polskie elementy.

        Args:
            source: Lista źródłowa (może być None lub pusta)
            fallback_pool: Pool do losowania (fallback)

        Returns:
            Lista polskich wartości (max 5 elementów)
        """
        if source:
            return [item for item in source if isinstance(item, str) and item.strip()]
        if not fallback_pool:
            return []
        sample_size = min(5, len(fallback_pool))
        return random.sample(fallback_pool, k=sample_size)

    @staticmethod
    def infer_full_name(background_story: str | None) -> str | None:
        """
        Ekstraktuj pełne imię i nazwisko z background_story (regex pattern).

        Args:
            background_story: Historia życiowa persony

        Returns:
            Pełne imię lub None

        Example:
            >>> story = "Jan Kowalski mieszka w Warszawie..."
            >>> DemographicsFormatter.infer_full_name(story)
            'Jan Kowalski'
        """
        if not background_story:
            return None
        match = _NAME_FROM_STORY_PATTERN.match(background_story.strip())
        if match:
            return match.group('name')
        return None

    @staticmethod
    def extract_age_from_story(background_story: str | None) -> int | None:
        """
        Ekstraktuj wiek z background_story (wspiera polski i angielski tekst).

        Patterns:
        - Angielski: "32-year-old"
        - Polski: "ma 32 lata", "32-letni", "lat 32"

        Args:
            background_story: Historia życiowa persony

        Returns:
            Wyekstraktowany wiek (10-100) lub None jeśli nie znaleziono
        """
        if not background_story:
            return None

        # Spróbuj angielski wzorzec "32-year-old"
        match = _AGE_IN_STORY_PATTERN.search(background_story)
        if match:
            try:
                return int(match.group('age'))
            except (ValueError, AttributeError):
                pass

        # Spróbuj polskie wzorce
        for pattern in _POLISH_AGE_PATTERNS:
            match = pattern.search(background_story)
            if match:
                try:
                    age = int(match.group('age'))
                    if 10 <= age <= 100:  # Sanity check
                        return age
                except (ValueError, AttributeError):
                    continue

        return None

    @staticmethod
    def fallback_full_name(gender: str | None, age: int) -> str:
        """
        Generuj fallback full name gdy nie można wyekstrahować z historii.

        Args:
            gender: Płeć (Kobieta, Mężczyzna, etc.)
            age: Wiek

        Returns:
            Fallback name (np. "Kobieta 28", "Mężczyzna 35")
        """
        gender_label = (gender or "Persona").split()[0].capitalize()
        return f"{gender_label} {age}"

    @staticmethod
    def get_consistent_occupation(
        education_level: str | None,
        income_bracket: str | None,
        age: int,
        personality: dict[str, Any],
        background_story: str | None,
    ) -> str:
        """
        Zapewnij polski, spójny zawód bazując na danych kontekstowych.

        Wrapper nad infer_polish_occupation dla zgodności API.
        """
        return DemographicsFormatter.infer_polish_occupation(education_level, income_bracket, age, personality, background_story)

    @staticmethod
    def ensure_story_alignment(
        story: str | None,
        age: int,
        occupation: str | None,
    ) -> str | None:
        """
        Zadbaj o spójność story z actual age (zamień niepasujący wiek w tekście).

        Args:
            story: Background story
            age: Actual age persony
            occupation: Zawód (obecnie nie używany)

        Returns:
            Story ze skorygowanym wiekiem
        """
        if not story:
            return story
        text = story.strip()
        match = _AGE_IN_STORY_PATTERN.search(text)
        if match and match.group('age') != str(age):
            text = _AGE_IN_STORY_PATTERN.sub(f"{age}-year-old", text, count=1)
        return text

    @staticmethod
    def compose_headline(
        full_name: str,
        persona_title: str | None,
        occupation: str | None,
        location: str | None,
    ) -> str:
        """
        Skomponuj nagłówek persony (headline for profile).

        Args:
            full_name: Pełne imię i nazwisko
            persona_title: Tytuł persony (opcjonalny)
            occupation: Zawód (opcjonalny)
            location: Lokalizacja (opcjonalna)

        Returns:
            Headline (np. "Software Engineer based in Warszawa")
        """
        primary_role = persona_title or occupation
        name_root = full_name.split()[0]
        if primary_role and location:
            return f"{primary_role} based in {location}"
        if primary_role:
            return primary_role
        if location:
            return f"{name_root} from {location}"
        return f"{name_root}'s persona profile"
