"""
Logika dystrybucji demograficznej dla generatora person.

Ten moduł zawiera narzędzia do:
- Normalizacji wag i rozkładów prawdopodobieństwa
- Losowania wartości z rozkładów ważonych
- Aplikacji demographic presets (gen_z, millennials, etc.)
- Walidacji i filtrow

ania age groups
- Budowania dystrybucji lokalizacji (miasta, focus areas)

Użycie:
    builder = DistributionBuilder()

    # Normalize weights
    normalized = builder.normalize_weights({"A": 2.0, "B": 3.0})
    # → {"A": 0.4, "B": 0.6}

    # Apply preset
    distribution = builder.apply_demographic_preset(dist, "millennials")
"""

import logging
import random
import re
from typing import Any

from app.services.personas.persona_generator_langchain import DemographicDistribution
from config import demographics

logger = logging.getLogger(__name__)


# ============================================================================
# Klasa DistributionBuilder
# ============================================================================

class DistributionBuilder:
    """
    Budowanie i normalizacja rozkładów demograficznych.

    Metody służą do manipulacji rozkładami prawdopodobieństwa dla age groups,
    genders, locations, education levels, i income brackets.
    """

    @staticmethod
    def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
        """
        Normalizuj wagi do sumy 1.0 (valid probability distribution).

        Args:
            weights: Dict z wagami (mogą nie sumować się do 1.0)

        Returns:
            Znormalizowany dict (suma=1.0), tylko wartości >0

        Example:
            >>> DistributionBuilder.normalize_weights({"A": 2.0, "B": 3.0})
            {'A': 0.4, 'B': 0.6}
        """
        total = sum(value for value in weights.values() if value > 0)
        if total <= 0:
            return weights
        return {key: value / total for key, value in weights.items() if value > 0}

    @staticmethod
    def coerce_distribution(raw: dict[str, Any] | None) -> dict[str, float] | None:
        """
        Konwertuj raw dict na valid probability distribution (normalizacja + type coercion).

        Args:
            raw: Raw dict (może zawierać non-numeric values)

        Returns:
            Normalized dict[str, float] lub None jeśli invalid

        Example:
            >>> DistributionBuilder.coerce_distribution({"A": "2", "B": "3", "C": 0})
            {'A': 0.4, 'B': 0.6}
        """
        if not raw:
            return None
        cleaned: dict[str, float] = {}
        for key, value in raw.items():
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric > 0:
                cleaned[str(key)] = numeric
        return DistributionBuilder.normalize_weights(cleaned) if cleaned else None

    @staticmethod
    def select_weighted(distribution: dict[str, float]) -> str | None:
        """
        Wybierz losowy element z podanego rozkładu prawdopodobieństwa.

        Args:
            distribution: Dict z wartościami i wagami (probability weights)

        Returns:
            Losowo wybrana wartość (zgodnie z wagami) lub None

        Example:
            >>> dist = {"A": 0.7, "B": 0.3}
            >>> DistributionBuilder.select_weighted(dist)
            'A'  # With 70% probability
        """
        if not distribution:
            return None
        options = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(options, weights=weights, k=1)[0]

    @staticmethod
    def apply_demographic_preset(
        distribution: DemographicDistribution,
        preset: str | None
    ) -> DemographicDistribution:
        """
        Nadpisuje rozkłady demograficzne na podstawie demographic preset.

        Presets są mapowane na realistyczne rozkłady demograficzne dla Polski:
        - gen_z: 18-27 lat, duże miasta uniwersyteckie, niższe dochody
        - millennials: 28-43 lata, duże miasta, średnie/wysokie dochody
        - gen_x: 44-59 lat, stabilność, średnie miasta
        - boomers: 60+ lat, małe miasta, wysokie dochody
        - urban_professionals: Duże miasta, wyższe wykształcenie, wysokie dochody
        - suburban_families: Przedmieścia, średnie dochody
        - rural_communities: Małe miejscowości, niższe dochody

        Args:
            distribution: Bazowy rozkład demograficzny
            preset: Preset demograficzny (gen_z, millennials, etc.)

        Returns:
            DemographicDistribution z nadpisanymi rozkładami dla preset
        """
        if not preset:
            return distribution

        # Normalizuj preset ID (obsługa myślników i wielkości liter)
        preset = preset.replace('-', '_').lower()

        if preset == "gen_z":
            # Gen Z (18-27): Digitalni natywni, duże miasta, studia/pierwsze prace
            distribution.age_groups = {"18-24": 0.6, "25-34": 0.4}
            distribution.locations = {
                "Warszawa": 0.25,
                "Kraków": 0.15,
                "Wrocław": 0.15,
                "Gdańsk": 0.10,
                "Poznań": 0.10,
                "Łódź": 0.08,
                "Katowice": 0.07,
                "Trójmiasto": 0.05,
                "Lublin": 0.05,
            }
            distribution.education_levels = {
                "Wyższe licencjackie": 0.35,
                "W trakcie studiów": 0.25,
                "Wyższe magisterskie": 0.20,
                "Średnie": 0.20,
            }
            distribution.income_brackets = {
                "< 3 000 zł": 0.30,
                "3 000 - 5 000 zł": 0.40,
                "5 000 - 7 500 zł": 0.20,
                "7 500 - 10 000 zł": 0.08,
                "> 10 000 zł": 0.02,
            }
            logger.info("🎯 Applied preset: gen_z (18-27, duże miasta, entry-level)")

        elif preset == "millennials":
            # Millennials (28-43): Established professionals, rodziny, kariera
            distribution.age_groups = {"25-34": 0.50, "35-44": 0.50}
            distribution.locations = {
                "Warszawa": 0.30,
                "Kraków": 0.15,
                "Wrocław": 0.15,
                "Poznań": 0.10,
                "Gdańsk": 0.08,
                "Trójmiasto": 0.07,
                "Katowice": 0.07,
                "Łódź": 0.05,
                "Szczecin": 0.03,
            }
            distribution.education_levels = {
                "Wyższe magisterskie": 0.50,
                "Wyższe licencjackie": 0.30,
                "Policealne": 0.10,
                "Średnie": 0.10,
            }
            distribution.income_brackets = {
                "5 000 - 7 500 zł": 0.25,
                "7 500 - 10 000 zł": 0.30,
                "10 000 - 15 000 zł": 0.25,
                "> 15 000 zł": 0.15,
                "3 000 - 5 000 zł": 0.05,
            }
            logger.info("🎯 Applied preset: millennials (28-43, profesjonaliści)")

        elif preset == "gen_x":
            # Gen X (44-59): Doświadczeni liderzy, stabilność, średnie miasta
            distribution.age_groups = {"45-54": 0.60, "55-64": 0.40}
            distribution.locations = {
                "Warszawa": 0.20,
                "Kraków": 0.12,
                "Wrocław": 0.10,
                "Poznań": 0.10,
                "Gdańsk": 0.08,
                "Katowice": 0.08,
                "Łódź": 0.08,
                "Lublin": 0.06,
                "Szczecin": 0.06,
                "Inne miasta": 0.12,
            }
            distribution.education_levels = {
                "Wyższe magisterskie": 0.40,
                "Wyższe licencjackie": 0.25,
                "Średnie": 0.20,
                "Policealne": 0.10,
                "Podstawowe": 0.05,
            }
            distribution.income_brackets = {
                "7 500 - 10 000 zł": 0.30,
                "10 000 - 15 000 zł": 0.30,
                "> 15 000 zł": 0.25,
                "5 000 - 7 500 zł": 0.15,
            }
            logger.info("🎯 Applied preset: gen_x (44-59, doświadczeni liderzy)")

        elif preset == "boomers":
            # Baby Boomers (60+): Emeryci, tradycyjne wartości, małe miasta
            distribution.age_groups = {"55-64": 0.40, "65+": 0.60}
            distribution.locations = {
                "Warszawa": 0.15,
                "Kraków": 0.10,
                "Wrocław": 0.08,
                "Poznań": 0.08,
                "Łódź": 0.08,
                "Gdańsk": 0.08,
                "Katowice": 0.08,
                "Inne miasta": 0.20,
                "Małe miasta": 0.15,
            }
            distribution.education_levels = {
                "Średnie": 0.35,
                "Wyższe magisterskie": 0.25,
                "Wyższe licencjackie": 0.15,
                "Zawodowe": 0.15,
                "Podstawowe": 0.10,
            }
            distribution.income_brackets = {
                "3 000 - 5 000 zł": 0.35,
                "5 000 - 7 500 zł": 0.30,
                "7 500 - 10 000 zł": 0.15,
                "> 10 000 zł": 0.10,
                "< 3 000 zł": 0.10,
            }
            logger.info("🎯 Applied preset: boomers (60+, tradycyjne wartości)")

        elif preset == "urban_professionals":
            # Urban Professionals: Duże miasta, wysokie wykształcenie, wysokie dochody
            distribution.age_groups = {"25-34": 0.40, "35-44": 0.40, "45-54": 0.20}
            distribution.locations = {
                "Warszawa": 0.40,
                "Kraków": 0.18,
                "Wrocław": 0.15,
                "Poznań": 0.12,
                "Gdańsk": 0.10,
                "Trójmiasto": 0.05,
            }
            distribution.education_levels = {
                "Wyższe magisterskie": 0.60,
                "Wyższe licencjackie": 0.30,
                "MBA/Doktorat": 0.10,
            }
            distribution.income_brackets = {
                "10 000 - 15 000 zł": 0.30,
                "> 15 000 zł": 0.35,
                "7 500 - 10 000 zł": 0.25,
                "5 000 - 7 500 zł": 0.10,
            }
            logger.info("🎯 Applied preset: urban_professionals (duże miasta, wysokie dochody)")

        elif preset == "suburban_families":
            # Suburban Families: Przedmieścia, rodziny, średnie dochody
            distribution.age_groups = {"25-34": 0.30, "35-44": 0.50, "45-54": 0.20}
            distribution.locations = {
                "Warszawa - przedmieścia": 0.25,
                "Kraków - przedmieścia": 0.15,
                "Wrocław - przedmieścia": 0.12,
                "Poznań - przedmieścia": 0.10,
                "Gdańsk - przedmieścia": 0.10,
                "Trójmiasto - przedmieścia": 0.08,
                "Katowice - przedmieścia": 0.08,
                "Inne przedmieścia": 0.12,
            }
            distribution.education_levels = {
                "Wyższe licencjackie": 0.35,
                "Wyższe magisterskie": 0.30,
                "Średnie": 0.20,
                "Policealne": 0.15,
            }
            distribution.income_brackets = {
                "5 000 - 7 500 zł": 0.30,
                "7 500 - 10 000 zł": 0.35,
                "10 000 - 15 000 zł": 0.20,
                "3 000 - 5 000 zł": 0.10,
                "> 15 000 zł": 0.05,
            }
            logger.info("🎯 Applied preset: suburban_families (przedmieścia, rodziny)")

        elif preset == "rural_communities":
            # Rural Communities: Małe miejscowości, lokalne społeczności
            distribution.age_groups = {"25-34": 0.20, "35-44": 0.25, "45-54": 0.30, "55-64": 0.15, "65+": 0.10}
            distribution.locations = {
                "Małe miasta < 20k": 0.40,
                "Wsie": 0.30,
                "Miasta 20k-50k": 0.30,
            }
            distribution.education_levels = {
                "Średnie": 0.40,
                "Zawodowe": 0.25,
                "Wyższe licencjackie": 0.20,
                "Podstawowe": 0.10,
                "Wyższe magisterskie": 0.05,
            }
            distribution.income_brackets = {
                "3 000 - 5 000 zł": 0.40,
                "< 3 000 zł": 0.25,
                "5 000 - 7 500 zł": 0.25,
                "7 500 - 10 000 zł": 0.08,
                "> 10 000 zł": 0.02,
            }
            logger.info("🎯 Applied preset: rural_communities (małe miejscowości)")

        else:
            logger.warning(f"⚠️  Unknown demographic preset: {preset} - skipping override")

        return distribution

    @staticmethod
    def extract_polish_cities_from_description(description: str | None) -> list[str]:
        """
        Wyciąga polskie miasta z opisu grupy docelowej używając regex + fleksja.

        Obsługuje odmianę nazw miast w polskim języku:
        - "Gdańsk", "Gdańsku", "Gdańskiem", "z Gdańska"
        - "Warszawa", "Warszawie", "Warszawy", "z Warszawy"

        Args:
            description: Opis grupy docelowej (np. "Osoby z Gdańska zainteresowane ekologią")

        Returns:
            Lista wykrytych polskich miast (max 5)
        """
        if not description:
            return []

        from app.services.personas.demographics_formatter import DemographicsFormatter

        cities = []
        normalized_desc = DemographicsFormatter.normalize_text(description)  # Istniejąca funkcja (usuwa diakrytyki)

        # POLISH_LOCATIONS to dict z nazwami miast - używamy keys()
        for city_name in demographics.poland.locations.keys():
            # Normalizuj nazwę miasta (usuń diakrytyki dla matching)
            normalized_city = DemographicsFormatter.normalize_text(city_name)

            # Sprawdź czy miasto występuje w opisie (z obsługą fleksji)
            # Wzorce: "Gdańsk", "Gdańsku", "Gdańskiem", "z Gdańska", "Gdańska"
            # Regex: słowo + opcjonalnie 0-3 litery na końcu (fleksja)
            pattern = rf"\b{re.escape(normalized_city)}[a-z]{{0,3}}\b"
            if re.search(pattern, normalized_desc, re.IGNORECASE):
                cities.append(city_name)
                logger.debug(f"📍 Extracted city from description: {city_name}")

        # Limit do 5 miast (unikaj przepełnienia gdy opis zawiera wiele nazw)
        result = cities[:5]

        if result:
            logger.info(f"📍 Extracted {len(result)} cities from description: {result}")

        return result

    @staticmethod
    def map_focus_area_to_industries(focus_area: str | None) -> list[str] | None:
        """
        Konwertuje focus area na listę branż dla generatora person.

        Mapowanie focus areas na konkretne branże pomaga generatorowi
        tworzyć persony z odpowiednimi zawodami.

        Args:
            focus_area: Obszar zainteresowań (tech, healthcare, finance, etc.)

        Returns:
            Lista branż lub None jeśli focus area nie jest rozpoznany/nie ma mappingu
        """
        if not focus_area:
            return None

        # Normalizuj focus area (lowercase)
        focus_area = focus_area.lower()

        # Mapowanie focus areas → industries
        focus_to_industries = {
            "tech": ["technology", "software development", "IT services", "fintech", "SaaS"],
            "healthcare": ["healthcare", "pharmaceuticals", "medical devices", "biotechnology", "health services"],
            "finance": ["banking", "financial services", "fintech", "insurance", "investment management", "accounting"],
            "education": ["education", "e-learning", "training & development", "educational technology", "academic research"],
            "retail": ["retail", "e-commerce", "consumer goods", "fashion", "FMCG"],
            "manufacturing": ["manufacturing", "industrial production", "logistics", "supply chain", "automotive"],
            "services": ["consulting", "professional services", "business services", "legal services", "HR services"],
            "entertainment": ["media & entertainment", "creative industries", "arts & culture", "gaming", "streaming"],
            "lifestyle": ["health & wellness", "fitness", "beauty", "travel & leisure", "hospitality"],
            "shopping": ["retail", "e-commerce", "consumer services", "marketplaces"],
            "general": None,  # Nie filtruj branż dla general
        }

        industries = focus_to_industries.get(focus_area)

        if industries:
            logger.info(f"🏢 Mapped focus_area='{focus_area}' → industries={industries}")

        return industries

    @staticmethod
    def age_group_bounds(label: str) -> tuple[int, int | None]:
        """
        Parse age group label do (min, max) bounds.

        Args:
            label: Age group label ("18-24", "25-34", "65+", etc.)

        Returns:
            Tuple (min_age, max_age) gdzie max_age może być None dla "65+"

        Example:
            >>> DistributionBuilder.age_group_bounds("25-34")
            (25, 34)
            >>> DistributionBuilder.age_group_bounds("65+")
            (65, None)
        """
        if '-' in label:
            start, end = label.split('-', maxsplit=1)
            try:
                return int(start), int(end)
            except ValueError:
                return 0, None
        if label.endswith('+'):
            try:
                base = int(label.rstrip('+'))
                return base, None
            except ValueError:
                return 0, None
        try:
            value = int(label)
            return value, value
        except ValueError:
            return 0, None

    @staticmethod
    def age_group_overlaps(label: str, min_age: int | None, max_age: int | None) -> bool:
        """
        Sprawdź czy age group label overlaps z podanym zakresem [min_age, max_age].

        Args:
            label: Age group label ("18-24", "25-34", etc.)
            min_age: Minimum age filter (inclusive)
            max_age: Maximum age filter (inclusive)

        Returns:
            True jeśli age group overlaps z zakresem

        Example:
            >>> DistributionBuilder.age_group_overlaps("25-34", 30, 40)
            True  # Overlaps (30-34)
            >>> DistributionBuilder.age_group_overlaps("18-24", 30, 40)
            False  # No overlap
        """
        group_min, group_max = DistributionBuilder.age_group_bounds(label)
        if min_age is not None and group_max is not None and group_max < min_age:
            return False
        if max_age is not None and group_min is not None and group_min > max_age:
            return False
        return True

    @staticmethod
    def apply_age_preferences(
        age_groups: dict[str, float],
        focus: str | None,
        min_age: int | None,
        max_age: int | None,
    ) -> dict[str, float]:
        """
        Aplikuj age preferences (filtruj age groups + boost weights based on focus).

        Args:
            age_groups: Bazowe age groups distribution
            focus: Focus preference ("young_adults", "experienced_leaders", None)
            min_age: Minimum age filter
            max_age: Maximum age filter

        Returns:
            Adjusted age groups distribution (normalized)
        """
        # Filter by min/max age
        adjusted = {
            label: weight
            for label, weight in age_groups.items()
            if DistributionBuilder.age_group_overlaps(label, min_age, max_age)
        }
        if not adjusted:
            adjusted = dict(age_groups)

        # Apply focus boosts
        if focus == 'young_adults':
            for label in adjusted:
                lower, upper = DistributionBuilder.age_group_bounds(label)
                upper_value = upper if upper is not None else lower + 5
                if upper_value <= 35:
                    adjusted[label] *= 1.8
                else:
                    adjusted[label] *= 0.6
        elif focus == 'experienced_leaders':
            for label in adjusted:
                lower, _ = DistributionBuilder.age_group_bounds(label)
                if lower >= 35:
                    adjusted[label] *= 1.8
                else:
                    adjusted[label] *= 0.6

        normalized = DistributionBuilder.normalize_weights(adjusted)
        return normalized if normalized else dict(age_groups)

    @staticmethod
    def apply_gender_preferences(genders: dict[str, float], balance: str | None) -> dict[str, float]:
        """
        Aplikuj gender balance preferences.

        Args:
            genders: Bazowe genders distribution
            balance: Gender balance preference ("female_skew", "male_skew", None)

        Returns:
            Adjusted genders distribution
        """
        if balance == 'female_skew':
            return DistributionBuilder.normalize_weights({
                'female': 0.65,
                'male': 0.3,
                'non-binary': 0.05,
            })
        if balance == 'male_skew':
            return DistributionBuilder.normalize_weights({
                'male': 0.65,
                'female': 0.3,
                'non-binary': 0.05,
            })
        return genders

    @staticmethod
    def build_location_distribution(
        base_locations: dict[str, float],
        advanced_options: dict[str, Any] | None,
    ) -> dict[str, float]:
        """
        Buduje location distribution bazując na advanced options (target_cities, urbanicity, etc.).

        Args:
            base_locations: Bazowa dystrybucja lokalizacji
            advanced_options: Advanced options z target_cities, target_countries, urbanicity

        Returns:
            Adjusted location distribution
        """
        if not advanced_options:
            return base_locations

        cities = advanced_options.get('target_cities') or []
        countries = advanced_options.get('target_countries') or []

        if cities:
            city_weights = {city: 1 / len(cities) for city in cities}
            return DistributionBuilder.normalize_weights(city_weights)

        if countries:
            labels = [f"{country} - Urban hub" for country in countries]
            return DistributionBuilder.normalize_weights({label: 1 / len(labels) for label in labels})

        urbanicity = advanced_options.get('urbanicity')
        if urbanicity == 'urban':
            return base_locations
        if urbanicity == 'suburban':
            return DistributionBuilder.normalize_weights({
                'Suburban Midwest, USA': 0.25,
                'Suburban Northeast, USA': 0.25,
                'Sunbelt Suburb, USA': 0.2,
                'Other': 0.3,
            })
        if urbanicity == 'rural':
            return DistributionBuilder.normalize_weights({
                'Rural Midwest, USA': 0.35,
                'Rural South, USA': 0.25,
                'Mountain Town, USA': 0.2,
                'Other Rural Area': 0.2,
            })

        return base_locations

    @staticmethod
    def normalize_distribution(
        distribution: dict[str, float], fallback: dict[str, float]
    ) -> dict[str, float]:
        """
        Normalize distribution to sum to 1.0, or use fallback if invalid.

        Args:
            distribution: Distribution do normalizacji
            fallback: Fallback distribution (używany gdy distribution invalid)

        Returns:
            Normalized distribution lub fallback
        """
        if not distribution:
            return fallback
        total = sum(distribution.values())
        if total <= 0:
            return fallback
        return {key: value / total for key, value in distribution.items()}
