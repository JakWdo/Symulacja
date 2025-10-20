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


def test_weighted_sampling(generator, sample_distribution):
    """
    Test losowania z wagami (weighted sampling)

    Sprawdza czy metoda _weighted_sample respektuje zadane rozkłady prawdopodobieństw:
    1. Generuje 1000 próbek z rozkładu grup wiekowych
    2. Weryfikuje że wszystkie kategorie są reprezentowane
    3. Sprawdza czy obserwowane proporcje są bliskie oczekiwanym (tolerancja ±5%)

    Np. jeśli grupa "25-34" ma wagę 0.25, to ~250/1000 próbek powinno należeć do tej grupy
    """
    samples = []
    for _ in range(1000):
        sample = generator._weighted_sample(sample_distribution.age_groups)
        samples.append(sample)

    # Check that all categories are represented
    unique_values = set(samples)
    assert unique_values == set(sample_distribution.age_groups.keys())

    # Check proportions (with some tolerance)
    for category, expected_prob in sample_distribution.age_groups.items():
        observed_prob = samples.count(category) / len(samples)
        assert abs(observed_prob - expected_prob) < 0.05  # 5% tolerance


def test_sample_demographic_profile(generator, sample_distribution):
    """
    Test generowania profili demograficznych

    Sprawdza czy metoda sample_demographic_profile generuje kompletne profile osoby:
    1. Generuje 10 profili demograficznych
    2. Weryfikuje że każdy profil zawiera wszystkie wymagane pola:
       - age_group (grupa wiekowa)
       - gender (płeć)
       - education_level (poziom wykształcenia)
       - income_bracket (przedział dochodowy)
       - location (lokalizacja)
    3. Sprawdza czy wartości należą do zdefiniowanych kategorii w rozkładzie
    """
    profiles = generator.sample_demographic_profile(sample_distribution, n_samples=10)

    assert len(profiles) == 10

    for profile in profiles:
        assert "age_group" in profile
        assert "gender" in profile
        assert "education_level" in profile
        assert "income_bracket" in profile
        assert "location" in profile

        assert profile["age_group"] in sample_distribution.age_groups
        assert profile["gender"] in sample_distribution.genders
        assert profile["education_level"] in sample_distribution.education_levels
        assert profile["income_bracket"] in sample_distribution.income_brackets
        assert profile["location"] in sample_distribution.locations


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


def test_chi_square_validation(generator, sample_distribution):
    """
    Test walidacji statystycznej chi-kwadrat

    Test chi-kwadrat (χ²) sprawdza czy obserwowany rozkład pasuje do oczekiwanego.
    Jest to kluczowa walidacja dla generatora person - musi tworzyć populacje zgodne
    z założonymi rozkładami demograficznymi.

    Proces testu:
    1. Generuje 200 person z zadanym rozkładem demograficznym
    2. Przeprowadza testy χ² dla każdej kategorii (wiek, płeć, wykształcenie, dochód, lokalizacja)
    3. Sprawdza strukturę wyniku - każdy test zwraca:
       - p_value - prawdopodobieństwo (p > 0.05 oznacza zgodność)
       - chi_square_statistic - wartość statystyki χ²
       - degrees_of_freedom - stopnie swobody
    4. Weryfikuje overall_valid=True (wszystkie rozkłady są poprawne)

    Z 200 próbkami rozkład powinien być statystycznie zgodny z oczekiwanym
    """
    # Generate personas that match distribution
    personas = []
    for _ in range(200):
        profile = generator.sample_demographic_profile(sample_distribution)[0]
        personas.append(profile)

    # Validate distribution
    validation = generator.validate_distribution(personas, sample_distribution)

    # Check structure
    assert "age" in validation
    assert "gender" in validation
    assert "education" in validation
    assert "income" in validation
    assert "location" in validation
    assert "overall_valid" in validation

    # Each test should have p_value
    for key in ["age", "gender", "education", "income", "location"]:
        assert "p_value" in validation[key]
        assert "chi_square_statistic" in validation[key]
        assert "degrees_of_freedom" in validation[key]

    # With 200 samples, distribution should be valid (p > 0.05)
    assert validation["overall_valid"] is True


def test_chi_square_validation_small_sample(generator, sample_distribution):
    """
    Test walidacji chi-kwadrat z małą próbką

    Sprawdza zachowanie testu χ² przy niewystarczającej liczbie próbek.

    Z zaledwie 20 personami:
    - Test może wykazać rozbieżność od oczekiwanego rozkładu (to normalne)
    - Struktura wyników powinna być prawidłowa (zawierać overall_valid)
    - Test powinien zakończyć się bez błędów (nawet jeśli validacja = False)

    Ten test pokazuje że generator działa poprawnie nawet z małymi próbkami,
    ale ostrzega że walidacja statystyczna wymaga większej liczby person.
    """
    # Generate only 20 personas (too small for good statistical validation)
    personas = []
    for _ in range(20):
        profile = generator.sample_demographic_profile(sample_distribution)[0]
        personas.append(profile)

    validation = generator.validate_distribution(personas, sample_distribution)

    # Structure should still be correct
    assert "overall_valid" in validation

    # With small sample, might fail validation (that's expected)
    # Just verify the test completes without error


def test_sanitize_text_single_line(generator):
    """
    Test sanityzacji tekstu jednoliniowego (usuwa wszystkie \\n)

    Bug fix test: LLM generowało pola tekstowe z nadmiarowymi \\n\\n,
    powodując wyświetlanie "Zawód\\n\\nJuż" zamiast "Zawód Już" w UI.

    Test sprawdza czy _sanitize_text():
    1. Usuwa wszystkie znaki nowej linii (\\n)
    2. Normalizuje nadmiarowe spacje (wiele spacji -> jedna spacja)
    3. Usuwa leading/trailing whitespace
    """
    # Test 1: Usuwa \n\n (używamy raw string lub literalnych znaków nowej linii)
    assert generator._sanitize_text("Zawód\n\nJuż", preserve_paragraphs=False) == "Zawód Już"

    # Test 2: Usuwa pojedyncze \n
    assert generator._sanitize_text("First line\nSecond line", preserve_paragraphs=False) == "First line Second line"

    # Test 3: Normalizuje nadmiarowe spacje
    assert generator._sanitize_text("Tekst  z   wieloma    spacjami", preserve_paragraphs=False) == "Tekst z wieloma spacjami"

    # Test 4: Usuwa leading/trailing whitespace
    assert generator._sanitize_text("  Tekst z padding  ", preserve_paragraphs=False) == "Tekst z padding"

    # Test 5: Łączy wszystkie problemy
    assert generator._sanitize_text("  Line 1\n\n  Line 2  \n  Line 3  ", preserve_paragraphs=False) == "Line 1 Line 2 Line 3"

    # Test 6: Pusta wartość zwraca pustą wartość
    assert generator._sanitize_text("", preserve_paragraphs=False) == ""
    assert generator._sanitize_text(None, preserve_paragraphs=False) is None


def test_sanitize_text_preserve_paragraphs(generator):
    """
    Test sanityzacji background_story (zachowuje podział na akapity)

    background_story może zawierać podział na akapity (\n\n) który chcemy zachować.
    Ale wciąż chcemy znormalizować nadmiarowe spacje w każdym akapicie.

    Test sprawdza czy _sanitize_text(preserve_paragraphs=True):
    1. Zachowuje podział na akapity (\n\n)
    2. Normalizuje spacje w każdym akapicie
    3. Usuwa puste linie
    """
    # Test 1: Zachowuje podział na akapity
    input_text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    expected = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    assert generator._sanitize_text(input_text, preserve_paragraphs=True) == expected

    # Test 2: Normalizuje spacje w każdym akapicie
    input_text = "Paragraph  with  spaces\n\nAnother  paragraph  here"
    expected = "Paragraph with spaces\n\nAnother paragraph here"
    assert generator._sanitize_text(input_text, preserve_paragraphs=True) == expected

    # Test 3: Usuwa puste linie
    input_text = "Para 1\n\n\n\nPara 2\n\nPara 3"
    expected = "Para 1\n\nPara 2\n\nPara 3"
    assert generator._sanitize_text(input_text, preserve_paragraphs=True) == expected

    # Test 4: Usuwa leading/trailing whitespace z każdego akapitu
    input_text = "  Para 1  \n\n  Para 2  \n\n  Para 3  "
    expected = "Para 1\n\nPara 2\n\nPara 3"
    assert generator._sanitize_text(input_text, preserve_paragraphs=True) == expected


def test_sanitize_text_edge_cases(generator):
    """
    Test edge cases dla sanityzacji tekstu

    Sprawdza zachowanie dla nietypowych inputów:
    - Tylko whitespace
    - Tylko \n
    - Mixed whitespace (spacje, tabulatory, \n)
    """
    # Test 1: Tylko whitespace -> pusty string
    assert generator._sanitize_text("   ", preserve_paragraphs=False) == ""
    assert generator._sanitize_text("   ", preserve_paragraphs=True) == ""

    # Test 2: Tylko \n -> pusty string
    assert generator._sanitize_text("\n\n\n", preserve_paragraphs=False) == ""
    assert generator._sanitize_text("\n\n\n", preserve_paragraphs=True) == ""

    # Test 3: Mixed whitespace (spacje + tabulatory + \n)
    assert generator._sanitize_text("Text\twith\ttabs\nand\nnewlines", preserve_paragraphs=False) == "Text with tabs and newlines"

    # Test 4: Unicode whitespace (non-breaking space, etc.) - should be normalized
    # Note: re.sub(r'\s+', ' ', ...) catches all unicode whitespace
    assert generator._sanitize_text("Text\u00A0with\u00A0NBSP", preserve_paragraphs=False) == "Text with NBSP"