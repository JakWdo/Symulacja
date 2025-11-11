"""
Konstrukcja segmentów demograficznych - nazwy, opisy, metadane.

Ten moduł zawiera narzędzia do:
- Tworzenia nazw segmentów (np. "Kobiety 25-34 wyższe wykształcenie Warszawa")
- Formatowania opisów segmentów
- Budowania metadanych segmentów (segment_id, segment_description, etc.)
- Slugification (URL-safe identifiers)

Użycie:
    constructor = SegmentConstructor()
    segment_name = constructor.compose_segment_name(demographics, 0)
    segment_description = constructor.compose_segment_description(demographics, segment_name)
"""

import logging
import re
import unicodedata
from typing import Any

from app.services.personas.validation.demographics_formatter import DemographicsFormatter

logger = logging.getLogger(__name__)


# ============================================================================
# STAŁE
# ============================================================================

_SEGMENT_GENDER_LABELS = {
    "kobieta": "Kobiety",
    "kobiety": "Kobiety",
    "female": "Kobiety",
    "mężczyzna": "Mężczyźni",
    "mezczyzna": "Mężczyźni",
    "mężczyzni": "Mężczyźni",
    "mężczyźni": "Mężczyźni",
    "male": "Mężczyźni",
}


# ============================================================================
# Klasa SegmentConstructor
# ============================================================================

class SegmentConstructor:
    """
    Konstrukcja nazw, opisów i metadanych segmentów demograficznych.

    Segmenty są grupami person o podobnych cechach demograficznych
    (np. "Kobiety 25-34 wyższe wykształcenie Warszawa").
    """

    def __init__(self):
        self.formatter = DemographicsFormatter()

    @staticmethod
    def segment_gender_label(raw_gender: str | None) -> str:
        """
        Przekonwertuj płeć na label segmentu (liczba mnoga).

        Args:
            raw_gender: Płeć (Kobieta, Mężczyzna, female, male, etc.)

        Returns:
            Label w liczbie mnogiej (Kobiety, Mężczyźni, Osoby)

        Example:
            >>> SegmentConstructor.segment_gender_label("kobieta")
            'Kobiety'
        """
        normalized = DemographicsFormatter.normalize_text(raw_gender)
        return _SEGMENT_GENDER_LABELS.get(normalized, "Osoby")

    @staticmethod
    def format_age_segment(raw_age: str | None) -> str | None:
        """
        Formatuj age segment label (dodaj "lat" jeśli brakuje).

        Args:
            raw_age: Age value ("25-34", "18-24", "65+", etc.)

        Returns:
            Formatted age label ("25-34 lat", "65+ lat") lub None

        Example:
            >>> SegmentConstructor.format_age_segment("25-34")
            '25-34 lat'
        """
        if raw_age is None:
            return None
        age_str = str(raw_age).strip()
        if not age_str:
            return None
        if age_str.replace("+", "").isdigit() or "-" in age_str:
            if age_str.endswith("lat"):
                return age_str
            return f"{age_str} lat"
        return age_str

    @staticmethod
    def format_education_phrase(raw_education: str | None) -> str | None:
        """
        Formatuj education jako frazę opisową ("z wyższym wykształceniem").

        Args:
            raw_education: Wykształcenie ("Wyższe magisterskie", "Średnie", etc.)

        Returns:
            Fraza opisowa lub None

        Example:
            >>> SegmentConstructor.format_education_phrase("Wyższe magisterskie")
            'z wyższym wykształceniem'
        """
        if not raw_education:
            return None
        value = str(raw_education).strip()
        lower = value.lower()
        if "wyższ" in lower:
            return "z wyższym wykształceniem"
        if "średn" in lower:
            return "ze średnim wykształceniem"
        if "zawod" in lower:
            return "z wykształceniem zawodowym"
        if "podstaw" in lower:
            return "z wykształceniem podstawowym"
        if value:
            return f"z wykształceniem {value}"
        return None

    @staticmethod
    def format_income_phrase(raw_income: str | None) -> str | None:
        """
        Formatuj income jako frazę opisową ("osiągające dochody około 5000-7500 zł").

        Args:
            raw_income: Dochód ("5 000 - 7 500 zł", "< 3 000 zł", etc.)

        Returns:
            Fraza opisowa lub None

        Example:
            >>> SegmentConstructor.format_income_phrase("5 000 - 7 500 zł")
            'osiągające dochody około 5 000 - 7 500 zł'
        """
        if not raw_income:
            return None
        value = str(raw_income).strip()
        if not value:
            return None
        if any(char.isdigit() for char in value):
            return f"osiągające dochody około {value}"
        return f"o dochodach {value}"

    @staticmethod
    def format_location_phrase(raw_location: str | None) -> str | None:
        """
        Formatuj location jako frazę opisową ("mieszkające w Warszawie").

        Args:
            raw_location: Lokalizacja ("Warszawa", "Kraków", "cała Polska", etc.)

        Returns:
            Fraza opisowa lub None

        Example:
            >>> SegmentConstructor.format_location_phrase("Warszawa")
            'mieszkające w Warszawa'
        """
        if not raw_location:
            return None
        value = str(raw_location).strip()
        if not value:
            return None
        normalized = DemographicsFormatter.normalize_text(value)
        if normalized in {"polska", "kraj", "calapolska", "całapolska", "cała polska"}:
            return "rozproszone w całej Polsce"
        return f"mieszkające w {value}"

    @staticmethod
    def slugify_segment(name: str) -> str:
        """
        Przekonwertuj segment name na URL-safe slug.

        Args:
            name: Segment name ("Młodzi Prekariusze 25-34")

        Returns:
            URL-safe slug ("mlodzi-prekariusze-25-34")

        Example:
            >>> SegmentConstructor.slugify_segment("Młodzi Prekariusze 25-34")
            'mlodzi-prekariusze-25-34'
        """
        normalized = unicodedata.normalize("NFKD", name)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
        return ascii_text

    @staticmethod
    def sanitize_brief_text(text: str | None, max_length: int = 900) -> str | None:
        """
        Oczyść brief text (usuń markdown, truncate do max_length).

        Args:
            text: Brief text (może zawierać markdown)
            max_length: Max length (default 900 chars)

        Returns:
            Sanitized text lub None

        Example:
            >>> SegmentConstructor.sanitize_brief_text("**Bold** text", 50)
            'Bold text'
        """
        if not text:
            return None
        cleaned = re.sub(r"[`*_#>\[\]]+", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return None
        if max_length and len(cleaned) > max_length:
            truncated = cleaned[:max_length].rsplit(" ", 1)[0]
            return f"{truncated}..."
        return cleaned

    @staticmethod
    def segment_subject_descriptor(gender_label: str, age_phrase: str | None) -> str:
        """
        Buduje subject descriptor dla segment description ("kobiety w wieku 25-34 lat").

        Args:
            gender_label: Gender label (Kobiety, Mężczyźni, Osoby)
            age_phrase: Age phrase ("25-34 lat")

        Returns:
            Subject descriptor

        Example:
            >>> SegmentConstructor.segment_subject_descriptor("Kobiety", "25-34 lat")
            'kobiety w wieku 25-34 lat'
        """
        base = gender_label.lower() if gender_label and gender_label != "Osoby" else "osoby"
        if age_phrase:
            return f"{base} w wieku {age_phrase}"
        return base

    def compose_segment_description(
        self,
        demographics: dict[str, Any],
        segment_name: str,
    ) -> str:
        """
        Komponuje pełny segment description (multi-sentence).

        Args:
            demographics: Demografia segmentu
            segment_name: Nazwa segmentu

        Returns:
            Segment description (2-3 zdania)

        Example:
            >>> demographics = {"gender": "Kobieta", "age_group": "25-34", "education": "Wyższe"}
            >>> constructor.compose_segment_description(demographics, "Kobiety 25-34")
            'Kobiety 25-34 obejmuje kobiety w wieku 25-34 lat. W tej grupie dominują osoby z wyższym wykształceniem.'
        """
        gender_label = self.segment_gender_label(demographics.get("gender"))
        age_phrase = self.format_age_segment(
            demographics.get("age") or demographics.get("age_group")
        )
        education_phrase = self.format_education_phrase(
            demographics.get("education") or demographics.get("education_level")
        )
        income_phrase = self.format_income_phrase(
            demographics.get("income") or demographics.get("income_bracket")
        )
        location_phrase = self.format_location_phrase(demographics.get("location"))

        subject = self.segment_subject_descriptor(gender_label, age_phrase)
        segment_label = segment_name or "Ten segment"

        sentences = [f"{segment_label} obejmuje {subject}."]
        details = [phrase for phrase in [education_phrase, income_phrase, location_phrase] if phrase]
        if details:
            detail_sentence = ", ".join(details)
            sentences.append(f"W tej grupie dominują osoby {detail_sentence}.")

        return " ".join(sentences)

    def compose_segment_name(
        self,
        demographics: dict[str, Any],
        group_index: int,
    ) -> str:
        """
        Komponuje segment name z demographics (używane jako fallback gdy brak catchy name).

        Args:
            demographics: Demografia segmentu
            group_index: Index grupy (używany do fallback name "Segment 1")

        Returns:
            Segment name (max 60 chars)

        Example:
            >>> demographics = {"gender": "Kobieta", "age_group": "25-34", "education": "Wyższe", "location": "Warszawa"}
            >>> constructor.compose_segment_name(demographics, 0)
            'Kobiety 25-34 wyższe wykształcenie Warszawa'
        """
        gender_label = self.segment_gender_label(demographics.get("gender"))
        age_value = demographics.get("age") or demographics.get("age_group")
        location = demographics.get("location")
        education_raw = demographics.get("education") or demographics.get("education_level")

        age_component = None
        if age_value:
            age_component = str(age_value).replace("lat", "").strip()

        education_component = None
        if education_raw:
            value = str(education_raw).strip()
            lower = value.lower()
            if "wyższ" in lower:
                education_component = "wyższe wykształcenie"
            elif "średn" in lower:
                education_component = "średnie wykształcenie"
            elif "zawod" in lower:
                education_component = "zawodowe wykształcenie"

        location_component = None
        if location:
            normalized_loc = self.formatter.normalize_text(location)
            if normalized_loc not in {"polska", "kraj", "calapolska", "całapolska"}:
                location_component = str(location).strip()

        parts = []
        if gender_label and gender_label != "Osoby":
            parts.append(gender_label)
        else:
            parts.append("Osoby")
        if age_component:
            parts.append(age_component)
        if education_component:
            parts.append(education_component)
        if location_component:
            parts.append(location_component)

        name = " ".join(parts).strip()
        if not name:
            name = f"Segment {group_index + 1}"
        if len(name) > 60:
            name = name[:57].rstrip() + "..."
        return name

    def build_segment_metadata(
        self,
        demographics: dict[str, Any],
        brief: str | None,
        allocation_reasoning: str | None,
        group_index: int,
        segment_characteristics: list[str] | None = None,
    ) -> dict[str, str | None]:
        """
        Buduje metadata segmentu z chwytliwą nazwą (jeśli dostępna).

        Priorytet nazw:
        1. segment_characteristics[0] - chwytliwa nazwa z orchestration (np. "Młodzi Prekariusze")
        2. _compose_segment_name() - generyczna nazwa (fallback)

        Args:
            demographics: Cechy demograficzne
            brief: Brief segmentu
            allocation_reasoning: Reasoning alokacji
            group_index: Indeks grupy
            segment_characteristics: Kluczowe cechy segmentu z orchestration (opcjonalne)

        Returns:
            Dict z segment_name, segment_id, segment_description, segment_social_context
        """
        # PRIORYTET 1: Użyj pierwszej charakterystyki jako chwytliwej nazwy (jeśli istnieje i wygląda jak nazwa)
        catchy_segment_name = None
        if segment_characteristics and len(segment_characteristics) > 0:
            first_char = segment_characteristics[0].strip()
            # Validate: krótka nazwa (2-6 słów, <60 znaków), nie pełne zdanie
            word_count = len(first_char.split())
            if 2 <= word_count <= 6 and len(first_char) < 60 and not first_char.endswith('.'):
                catchy_segment_name = first_char
                logger.info(f"✨ Using catchy segment name from orchestration: '{catchy_segment_name}'")

        # FALLBACK: Generyczna nazwa
        segment_name = catchy_segment_name or self.compose_segment_name(demographics, group_index)

        slug = self.slugify_segment(segment_name)
        if not slug:
            slug = f"segment-{group_index + 1}"

        description = self.compose_segment_description(demographics, segment_name)
        social_context = self.sanitize_brief_text(brief)
        if not social_context:
            social_context = self.sanitize_brief_text(allocation_reasoning)
        if not social_context:
            social_context = description

        return {
            "segment_name": segment_name,
            "segment_id": slug,
            "segment_description": description,
            "segment_social_context": social_context,
        }
