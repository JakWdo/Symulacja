"""
Moduł do walidacji statystycznej rozkładów demograficznych person

Zawiera logikę do:
- Testowania zgodności rozkładów z testem chi-kwadrat
- Walidacji czy wygenerowane persony pasują do oczekiwanych rozkładów
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Any
from config import features

from .demographic_sampling import DemographicDistribution


def validate_distribution(
    generated_personas: list[dict[str, Any]],
    target_distribution: DemographicDistribution,
) -> dict[str, Any]:
    """
    Waliduj czy wygenerowane persony pasują do docelowego rozkładu (test chi-kwadrat)

    Sprawdza statystycznie czy rzeczywisty rozkład cech demograficznych w wygenerowanych
    personach odpowiada zadanemu rozkładowi docelowemu. Używa testu chi-kwadrat dla
    każdej kategorii (wiek, płeć, edukacja, dochód, lokalizacja).

    Args:
        generated_personas: Lista wygenerowanych person (jako słowniki)
        target_distribution: Oczekiwany rozkład demograficzny

    Returns:
        Słownik z wynikami testów dla każdej kategorii oraz ogólną oceną:
        {
            "age": {"p_value": float, "chi_square_statistic": float, ...},
            "gender": {...},
            "overall_valid": bool  # Wartość True oznacza, że wszystkie p > 0.05
        }
    """
    results = {}

    # Testuj rozkład wieku (tylko jeśli podany)
    if target_distribution.age_groups:
        results["age"] = _chi_square_test(
            generated_personas, "age_group", target_distribution.age_groups
        )

    # Testuj rozkład płci (tylko jeśli podany)
    if target_distribution.genders:
        results["gender"] = _chi_square_test(
            generated_personas, "gender", target_distribution.genders
        )

    # Testuj rozkład edukacji (tylko jeśli podany)
    if target_distribution.education_levels:
        results["education"] = _chi_square_test(
            generated_personas, "education_level", target_distribution.education_levels
        )

    # Testuj rozkład dochodów (tylko jeśli podany)
    if target_distribution.income_brackets:
        results["income"] = _chi_square_test(
            generated_personas, "income_bracket", target_distribution.income_brackets
        )

    # Testuj rozkład lokalizacji (tylko jeśli podany)
    if target_distribution.locations:
        results["location"] = _chi_square_test(
            generated_personas, "location", target_distribution.locations
        )

    # Ogólna walidacja - wszystkie p-wartości powinny być > 0.05
    all_p_values = [r["p_value"] for r in results.values() if "p_value" in r]
    results["overall_valid"] = all(
        p > features.performance.statistical_significance_threshold for p in all_p_values
    ) if all_p_values else True

    return results


def _chi_square_test(
    personas: list[dict[str, Any]], field: str, expected_dist: dict[str, float]
) -> dict[str, float]:
    """
    Wykonaj test chi-kwadrat dla konkretnego pola demograficznego

    Test chi-kwadrat sprawdza czy obserwowany rozkład kategorii (np. grup wiekowych)
    statystycznie różni się od rozkładu oczekiwanego. Im wyższe p-value, tym lepiej
    (p > 0.05 oznacza że rozkłady są zgodne).

    Args:
        personas: Lista person do sprawdzenia
        field: Nazwa pola do przetestowania (np. "age_group", "gender")
        expected_dist: Oczekiwany rozkład prawdopodobieństw

    Returns:
        Słownik z wynikami testu:
        - chi_square_statistic: wartość statystyki chi-kwadrat
        - p_value: p-wartość (>0.05 = dobre dopasowanie)
        - degrees_of_freedom: liczba stopni swobody
        - observed: obserwowane liczności
        - expected: oczekiwane liczności
    """
    # Filtruj kategorie z niepoprawnymi prawdopodobieństwami
    valid_categories = [
        (category, probability)
        for category, probability in expected_dist.items()
        if probability and probability > 0
    ]

    if not valid_categories:
        return {
            "chi_square_statistic": 0.0,
            "p_value": 1.0,
            "degrees_of_freedom": 0,
            "observed": {},
            "expected": {},
        }

    # Normalizuj prawdopodobieństwa do sumy = 1.0
    total_prob = sum(probability for _, probability in valid_categories)
    normalized_probs = {
        category: probability / total_prob for category, probability in valid_categories
    }

    # Policz obserwowane wystąpienia każdej kategorii
    observed_counts = {category: 0 for category in normalized_probs}
    valid_samples = 0
    for persona in personas:
        value = persona.get(field)
        if value in observed_counts:
            observed_counts[value] += 1
            valid_samples += 1

    if valid_samples == 0:
        return {
            "chi_square_statistic": 0.0,
            "p_value": 1.0,
            "degrees_of_freedom": len(observed_counts) - 1,
            "observed": observed_counts,
            "expected": {category: 0.0 for category in observed_counts},
        }

    # Oblicz oczekiwane liczności (probability * total_count)
    expected_counts = {
        category: normalized_probs[category] * valid_samples
        for category in normalized_probs
    }

    # Przygotuj listy do testu chi-kwadrat (scipy wymaga list w tej samej kolejności)
    observed = [observed_counts[category] for category in normalized_probs]
    expected = [expected_counts[category] for category in normalized_probs]

    # Wykonaj test chi-kwadrat
    chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)

    return {
        "chi_square_statistic": float(chi2_stat),
        "p_value": float(p_value),
        "degrees_of_freedom": len(normalized_probs) - 1,
        "observed": observed_counts,
        "expected": expected_counts,
        "sample_size": valid_samples,
    }
