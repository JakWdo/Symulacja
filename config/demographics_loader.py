"""
Demographics Loader - Centralized demographic configuration management.

Ten moduł dostarcza:
- PolandDemographics: Dane demograficzne dla rynku polskiego
- InternationalDemographics: Dane demograficzne dla rynków międzynarodowych
- CommonDemographics: Wspólne dane demograficzne (age_groups, genders)
- DemographicsConfig: Singleton łączący wszystkie źródła

Użycie:
    from config import demographics

    # Poland
    locations = demographics.poland.locations
    occupations = demographics.poland.occupations

    # International
    values = demographics.international.values
    interests = demographics.international.interests

    # Common
    age_groups = demographics.common.age_groups
    genders = demographics.common.genders
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from config.loader import ConfigLoader, CONFIG_ROOT

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASSES - POLAND DEMOGRAPHICS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class PolandDemographics:
    """
    Dane demograficzne dla rynku polskiego.

    Oparte na danych GUS (Główny Urząd Statystyczny) 2022-2024.
    Zawiera specyficzne dla Polski lokalizacje, zawody, wartości, zainteresowania.

    Attributes:
        locations: Słownik {miasto: prawdopodobieństwo}
        values: Lista polskich wartości kulturowych
        interests: Lista popularnych zainteresowań w Polsce
        occupations: Słownik {zawód: prawdopodobieństwo}
        male_names: Lista popularnych męskich imion
        female_names: Lista popularnych żeńskich imion
        surnames: Lista popularnych nazwisk
        income_brackets: Słownik {przedział_dochodu: prawdopodobieństwo}
        education_levels: Słownik {poziom_wykształcenia: prawdopodobieństwo}
        communication_styles: Lista stylów komunikacji
        decision_styles: Lista stylów podejmowania decyzji
    """
    locations: dict[str, float] = field(default_factory=dict)
    values: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    occupations: dict[str, float] = field(default_factory=dict)
    male_names: list[str] = field(default_factory=list)
    female_names: list[str] = field(default_factory=list)
    surnames: list[str] = field(default_factory=list)
    income_brackets: dict[str, float] = field(default_factory=dict)
    education_levels: dict[str, float] = field(default_factory=dict)
    communication_styles: list[str] = field(default_factory=list)
    decision_styles: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASSES - INTERNATIONAL DEMOGRAPHICS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class InternationalDemographics:
    """
    Dane demograficzne dla rynków międzynarodowych (USA, EU, UK).

    Domyślne wartości dla rynków zachodnich.

    Attributes:
        age_groups: Słownik {grupa_wiekowa: prawdopodobieństwo}
        genders: Słownik {płeć: prawdopodobieństwo}
        locations: Słownik {miasto: prawdopodobieństwo}
        education_levels: Słownik {poziom_wykształcenia: prawdopodobieństwo}
        income_brackets: Słownik {przedział_dochodu: prawdopodobieństwo}
        occupations: Lista zawodów (bez prawdopodobieństw - równomierny rozkład)
        values: Lista wartości (Western values)
        interests: Lista zainteresowań
        communication_styles: Lista stylów komunikacji
        decision_styles: Lista stylów podejmowania decyzji
        life_situations: Lista sytuacji życiowych
    """
    age_groups: dict[str, float] = field(default_factory=dict)
    genders: dict[str, float] = field(default_factory=dict)
    locations: dict[str, float] = field(default_factory=dict)
    education_levels: dict[str, float] = field(default_factory=dict)
    income_brackets: dict[str, float] = field(default_factory=dict)
    occupations: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    communication_styles: list[str] = field(default_factory=list)
    decision_styles: list[str] = field(default_factory=list)
    life_situations: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASSES - COMMON DEMOGRAPHICS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class CommonDemographics:
    """
    Wspólne dane demograficzne używane przez wszystkie rynki.

    Attributes:
        age_groups: Słownik {grupa_wiekowa: prawdopodobieństwo}
        genders: Słownik {płeć: prawdopodobieństwo}
        family_situations: Lista sytuacji rodzinnych
        personality_traits: Lista uniwersalnych cech osobowości (Big Five)
    """
    age_groups: dict[str, float] = field(default_factory=dict)
    genders: dict[str, float] = field(default_factory=dict)
    family_situations: list[str] = field(default_factory=list)
    personality_traits: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# DEMOGRAPHICS CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class DemographicsConfig:
    """
    Centralny konfigurator danych demograficznych.

    Ładuje trzy źródła:
    1. config/demographics/poland.yaml
    2. config/demographics/international.yaml
    3. config/demographics/common.yaml

    Features:
    - Lazy loading z ConfigLoader
    - Walidacja struktur danych
    - Error handling z fallback do pustych wartości
    """

    def __init__(self):
        self.loader = ConfigLoader()
        self.demographics_dir = CONFIG_ROOT / "demographics"

        # Lazy load demographics
        self.poland = self._load_poland()
        self.international = self._load_international()
        self.common = self._load_common()

    def _load_poland(self) -> PolandDemographics:
        """
        Ładuje config/demographics/poland.yaml.

        Returns:
            PolandDemographics object

        Raises:
            FileNotFoundError: Jeśli plik nie istnieje
        """
        try:
            config = self.loader.load_yaml(self.demographics_dir / "poland.yaml")

            return PolandDemographics(
                locations=config.get("locations", {}),
                values=config.get("values", []),
                interests=config.get("interests", []),
                occupations=config.get("occupations", {}),
                male_names=config.get("male_names", []),
                female_names=config.get("female_names", []),
                surnames=config.get("surnames", []),
                income_brackets=config.get("income_brackets", {}),
                education_levels=config.get("education_levels", {}),
                communication_styles=config.get("communication_styles", []),
                decision_styles=config.get("decision_styles", []),
            )
        except FileNotFoundError:
            logger.error("Poland demographics not found, using empty defaults")
            return PolandDemographics()

    def _load_international(self) -> InternationalDemographics:
        """
        Ładuje config/demographics/international.yaml.

        Returns:
            InternationalDemographics object

        Raises:
            FileNotFoundError: Jeśli plik nie istnieje
        """
        try:
            config = self.loader.load_yaml(self.demographics_dir / "international.yaml")

            return InternationalDemographics(
                age_groups=config.get("age_groups", {}),
                genders=config.get("genders", {}),
                locations=config.get("locations", {}),
                education_levels=config.get("education_levels", {}),
                income_brackets=config.get("income_brackets", {}),
                occupations=config.get("occupations", []),
                values=config.get("values", []),
                interests=config.get("interests", []),
                communication_styles=config.get("communication_styles", []),
                decision_styles=config.get("decision_styles", []),
                life_situations=config.get("life_situations", []),
            )
        except FileNotFoundError:
            logger.error("International demographics not found, using empty defaults")
            return InternationalDemographics()

    def _load_common(self) -> CommonDemographics:
        """
        Ładuje config/demographics/common.yaml.

        Returns:
            CommonDemographics object

        Raises:
            FileNotFoundError: Jeśli plik nie istnieje
        """
        try:
            config = self.loader.load_yaml(self.demographics_dir / "common.yaml")

            return CommonDemographics(
                age_groups=config.get("age_groups", {}),
                genders=config.get("genders", {}),
                family_situations=config.get("family_situations", []),
                personality_traits=config.get("personality_traits", []),
            )
        except FileNotFoundError:
            logger.error("Common demographics not found, using empty defaults")
            return CommonDemographics()


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

# Global demographics singleton (lazy-initialized on first access)
_demographics: DemographicsConfig | None = None


def get_demographics_config() -> DemographicsConfig:
    """
    Get global DemographicsConfig singleton.

    Returns:
        DemographicsConfig instance
    """
    global _demographics
    if _demographics is None:
        _demographics = DemographicsConfig()
        logger.debug("Initialized DemographicsConfig singleton")
    return _demographics


# Convenience export
demographics = get_demographics_config()
