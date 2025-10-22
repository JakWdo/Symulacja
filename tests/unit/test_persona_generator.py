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
from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain as PersonaGenerator


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


# NOTE: Tests for demographic sampling and chi-square validation removed
# after refactoring to segment-based allocation (2025-10-22).
# System now uses PersonaOrchestrationService for allocation planning.


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


# NOTE: Chi-square validation tests removed (2025-10-22)
# System no longer uses statistical validation of demographics after
# refactoring to segment-based allocation with PersonaOrchestrationService


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