"""
Distribution Calculator - Logika obliczeń rozkładów demograficznych

Funkcje do:
- Normalizacji wag i rozkładów prawdopodobieństwa
- Losowania wartości z rozkładów ważonych
- Aplikacji demographic presets (gen_z, millennials, etc.)
- Budowania dystrybucji lokalizacji i aplikowania preferencji
"""

import logging
import random
from typing import Any

from app.services.personas.generation.persona_generator_langchain import DemographicDistribution
from app.services.personas.validation.distribution_validators import age_group_bounds, age_group_overlaps

logger = logging.getLogger(__name__)


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
            >>> normalize_weights({"A": 2.0, "B": 3.0})
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
    @staticmethod
    @staticmethod
    @staticmethod
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
            if age_group_overlaps(label, min_age, max_age)
        }
        if not adjusted:
            adjusted = dict(age_groups)

        # Apply focus boosts
        if focus == 'young_adults':
            for label in adjusted:
                lower, upper = age_group_bounds(label)
                upper_value = upper if upper is not None else lower + 5
                if upper_value <= 35:
                    adjusted[label] *= 1.8
                else:
                    adjusted[label] *= 0.6
        elif focus == 'experienced_leaders':
            for label in adjusted:
                lower, _ = age_group_bounds(label)
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

