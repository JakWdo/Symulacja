"""
Testy jednostkowe dla generatora person (PersonaGenerator)

Ten moduł testuje kluczowe funkcjonalności generatora person:
- Losowanie z wagami (weighted sampling) - czy rozkłady demograficzne są respektowane
- Generowanie profili demograficznych - wiek, płeć, wykształcenie, dochód, lokalizacja
- Losowanie cech osobowości Big Five (OCEAN) - openness, conscientiousness, extraversion, etc.
- Losowanie wymiarów kulturowych Hofstede - power distance, individualism, etc.
- Walidacja statystyczna chi-kwadrat - czy wygenerowane persony odpowiadają założonym rozkładom
"""

import pytest
import numpy as np
from app.core.config import get_settings
from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain as PersonaGenerator, DemographicDistribution


@pytest.fixture
def sample_distribution():
    """
    Fixture - przykładowy rozkład demograficzny dla testów

    Zwraca obiekt DemographicDistribution z rozkładami prawdopodobieństw dla:
    - Grup wiekowych (age_groups): 18-24, 25-34, 35-44, 45-54, 55+
    - Płci (genders): male, female
    - Poziomów wykształcenia (education_levels): high_school, bachelors, masters, phd
    - Przedziałów dochodowych (income_brackets): <30k, 30k-60k, 60k-100k, 100k+
    - Lokalizacji (locations): urban, suburban, rural

    Wszystkie rozkłady sumują się do 1.0 (100%)
    """
    return DemographicDistribution(
        age_groups={"18-24": 0.15, "25-34": 0.25, "35-44": 0.25, "45-54": 0.20, "55+": 0.15},
        genders={"male": 0.49, "female": 0.51},
        education_levels={
            "high_school": 0.30,
            "bachelors": 0.40,
            "masters": 0.20,
            "phd": 0.10,
        },
        income_brackets={
            "<30k": 0.20,
            "30k-60k": 0.30,
            "60k-100k": 0.30,
            "100k+": 0.20,
        },
        locations={"urban": 0.60, "suburban": 0.30, "rural": 0.10},
    )


@pytest.fixture
def generator():
    """
    Fixture - instancja generatora person bez wywoływania zewnętrznych usług.

    Tworzy obiekt przy użyciu __new__ i ręcznie ustawia wymagane atrybuty,
    aby uniknąć inicjalizacji modeli LLM podczas testów.
    """

    gen = PersonaGenerator.__new__(PersonaGenerator)
    gen.settings = get_settings()
    gen._rng = np.random.default_rng(gen.settings.RANDOM_SEED)
    return gen


@pytest.mark.skip(reason="DEPRECATED: _weighted_sample() removed in comprehensive generation refactor. Demographics now from orchestration, not sampling.")
def test_weighted_sampling(generator, sample_distribution):
    """
    Test losowania z wagami (weighted sampling)

    DEPRECATED: Ta metoda została usunięta w refactorze comprehensive generation.
    Demographics są teraz generowane przez orchestration service (Gemini 2.5 Pro),
    nie przez statistical sampling.

    Zachowane dla historii - testy dla nowego flow w test_comprehensive_generation().
    """
    pass


@pytest.mark.skip(reason="DEPRECATED: sample_demographic_profile() removed in comprehensive generation refactor. Demographics now from orchestration.")
def test_sample_demographic_profile(generator, sample_distribution):
    """
    Test generowania profili demograficznych

    DEPRECATED: Ta metoda została usunięta w refactorze comprehensive generation.
    Demographics są teraz generowane przez orchestration service, nie sampling.

    Zachowane dla historii - testy dla nowego flow w test_comprehensive_generation().
    """
    pass


def test_big_five_traits_sampling(generator):
    """
    Test losowania cech osobowości Big Five (OCEAN)

    Model Big Five to pięć głównych wymiarów osobowości:
    - Openness (otwartość na doświadczenia) - kreatywność, ciekawość
    - Conscientiousness (sumienność) - organizacja, odpowiedzialność
    - Extraversion (ekstrawersja) - towarzyskość, energia
    - Agreeableness (ugodowość) - empatia, współpraca
    - Neuroticism (neurotyczność) - stabilność emocjonalna

    Test sprawdza czy:
    1. Wszystkie 5 cech są generowane
    2. Wartości są w zakresie 0-1 (0=niska cecha, 1=wysoka cecha)
    """
    traits = generator.sample_big_five_traits()

    assert "openness" in traits
    assert "conscientiousness" in traits
    assert "extraversion" in traits
    assert "agreeableness" in traits
    assert "neuroticism" in traits

    # All traits should be between 0 and 1
    for trait_value in traits.values():
        assert 0 <= trait_value <= 1


def test_cultural_dimensions_sampling(generator):
    """
    Test losowania wymiarów kulturowych Hofstede

    Model Hofstede opisuje różnice kulturowe między społeczeństwami:
    - Power Distance (dystans władzy) - akceptacja nierówności w hierarchii
    - Individualism (indywidualizm) - niezależność vs. kolektywizm
    - Masculinity (męskość) - asertywność vs. troska o innych
    - Uncertainty Avoidance (unikanie niepewności) - tolerancja na nieznane
    - Long-term Orientation (orientacja długoterminowa) - pragmatyzm vs. tradycja
    - Indulgence (pobłażliwość) - gratyfikacja vs. powściągliwość

    Test sprawdza czy:
    1. Wszystkie 6 wymiarów są generowane
    2. Wartości są w zakresie 0-1
    """
    dimensions = generator.sample_cultural_dimensions()

    expected_dimensions = [
        "power_distance",
        "individualism",
        "masculinity",
        "uncertainty_avoidance",
        "long_term_orientation",
        "indulgence",
    ]

    for dim in expected_dimensions:
        assert dim in dimensions
        assert 0 <= dimensions[dim] <= 1


@pytest.mark.skip(reason="DEPRECATED: Statistical validation removed - demographics from orchestration, not sampling.")
def test_chi_square_validation(generator, sample_distribution):
    """
    Test walidacji statystycznej chi-kwadrat

    DEPRECATED: Statistical validation został usunięty w comprehensive generation refactor.
    Demographics są teraz generowane przez orchestration service (Gemini 2.5 Pro) z intelligent
    allocation, nie przez statistical sampling. Orchestration zapewnia odpowiednią dystrybucję
    demograficzną bez potrzeby chi-square validation.

    Zachowane dla historii - nowy system waliduje spójność z orchestration briefs.
    """
    pass


@pytest.mark.skip(reason="DEPRECATED: Statistical validation removed - demographics from orchestration, not sampling.")
def test_chi_square_validation_small_sample(generator, sample_distribution):
    """
    Test walidacji chi-kwadrat z małą próbką

    DEPRECATED: Statistical validation został usunięty w comprehensive generation refactor.
    Demographics są teraz generowane przez orchestration service, nie sampling.

    Zachowane dla historii.
    """
    pass