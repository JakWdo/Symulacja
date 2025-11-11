"""
Moduł do próbkowania profili demograficznych dla person

Zawiera logikę do:
- Tworzenia rozkładów demograficznych (DemographicDistribution)
- Próbkowania profili zgodnie z zadanymi prawdopodobieństwami
- Normalizacji rozkładów i fallbacków do wartości domyślnych
"""

import numpy as np
from dataclasses import dataclass
from typing import Any


@dataclass
class DemographicDistribution:
    """
    Rozkład demograficzny populacji docelowej

    Każde pole to słownik mapujący kategorie na prawdopodobieństwa (sumujące się do 1.0)
    Przykład: {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2}
    """
    age_groups: dict[str, float]        # Grupy wiekowe
    genders: dict[str, float]           # Płeć
    education_levels: dict[str, float]  # Poziomy edukacji
    income_brackets: dict[str, float]   # Przedziały dochodowe
    locations: dict[str, float]         # Lokalizacje geograficzne


def sample_demographic_profile(
    distribution: DemographicDistribution,
    demographics_config,
    rng: np.random.Generator,
    n_samples: int = 1
) -> list[dict[str, Any]]:
    """
    Próbkuj profile demograficzne zgodnie z zadanym rozkładem

    Metoda ta tworzy losowe profile demograficzne na podstawie prawdopodobieństw
    w obiekcie DemographicDistribution. Jeśli jakiś rozkład jest pusty lub niepoprawny,
    używa domyślnych wartości z constants.py.

    Args:
        distribution: Obiekt zawierający rozkłady prawdopodobieństw dla każdej kategorii
        demographics_config: Obiekt demographics z config (dla wartości domyślnych)
        rng: NumPy random generator
        n_samples: Liczba profili do wygenerowania (domyślnie 1)

    Returns:
        Lista słowników, każdy zawiera klucze: age_group, gender, education_level,
        income_bracket, location
    """
    profiles = []

    for _ in range(n_samples):
        # Normalizuj każdy rozkład lub użyj wartości domyślnych (polskich)
        age_groups = _prepare_distribution(
            distribution.age_groups,
            demographics_config.common.age_groups,
            rng
        )
        genders = _prepare_distribution(
            distribution.genders,
            demographics_config.common.genders,
            rng
        )
        education_levels = _prepare_distribution(
            distribution.education_levels,
            demographics_config.poland.education_levels,
            rng
        )
        income_brackets = _prepare_distribution(
            distribution.income_brackets,
            demographics_config.poland.income_brackets,
            rng
        )
        locations = _prepare_distribution(
            distribution.locations,
            demographics_config.poland.locations,
            rng
        )

        # Losuj wartość z każdej kategorii zgodnie z wagami
        profile = {
            "age_group": _weighted_sample(age_groups, rng),
            "gender": _weighted_sample(genders, rng),
            "education_level": _weighted_sample(education_levels, rng),
            "income_bracket": _weighted_sample(income_brackets, rng),
            "location": _weighted_sample(locations, rng),
        }
        profiles.append(profile)

    return profiles


def _weighted_sample(distribution: dict[str, float], rng: np.random.Generator) -> str:
    """
    Losuj element z rozkładu ważonego (weighted sampling)

    Args:
        distribution: Słownik kategoria -> prawdopodobieństwo (suma = 1.0)
        rng: NumPy random generator

    Returns:
        Wylosowana kategoria jako string

    Raises:
        ValueError: Jeśli rozkład jest pusty
    """
    if not distribution:
        raise ValueError("Distribution cannot be empty")
    categories = list(distribution.keys())
    weights = list(distribution.values())
    return rng.choice(categories, p=weights)


def _prepare_distribution(
    distribution: dict[str, float],
    fallback: dict[str, float],
    rng: np.random.Generator
) -> dict[str, float]:
    """
    Przygotuj i znormalizuj rozkład prawdopodobieństw

    Sprawdza czy rozkład jest poprawny, normalizuje go do sumy 1.0,
    lub zwraca fallback jeśli rozkład jest niepoprawny.

    Args:
        distribution: Rozkład do znormalizowania
        fallback: Rozkład domyślny używany gdy distribution jest pusty/błędny
        rng: NumPy random generator (unused, ale zachowujemy dla kompatybilności)

    Returns:
        Znormalizowany rozkład (suma = 1.0) lub fallback
    """
    if not distribution:
        return fallback
    total = sum(distribution.values())
    if total <= 0:
        return fallback
    # Pierwsza normalizacja - dziel przez sumę
    normalized = {key: value / total for key, value in distribution.items()}
    normalized_total = sum(normalized.values())
    # Druga normalizacja jeśli są błędy zaokrągleń numerycznych
    if not np.isclose(normalized_total, 1.0):
        normalized = {
            key: value / normalized_total for key, value in normalized.items()
        }
    return normalized
