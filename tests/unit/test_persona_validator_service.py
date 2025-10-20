"""Testy jednostkowe serwisu PersonaValidator."""

from typing import Dict, Any, List, Optional

from app.services.personas.persona_validator import PersonaValidator


def _make_persona(
    background: str,
    age: int = 30,
    gender: str = "female",
    location: str = "Warsaw",
    education: str = "Master",
    income: str = "50k-70k",
    values: Optional[List[str]] = None,
    traits: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Pomocnicza funkcja budująca słownik persony."""
    traits = traits or {
        "openness": 0.6,
        "conscientiousness": 0.5,
        "extraversion": 0.4,
        "agreeableness": 0.6,
        "neuroticism": 0.3,
    }
    base = {
        "background_story": background,
        "age": age,
        "gender": gender,
        "location": location,
        "education_level": education,
        "income_bracket": income,
        "values": values or ["Innovation", "Family"],
    }
    base.update(traits)
    return base


def test_calculate_text_similarity_handles_empty():
    """Puste teksty powinny zwracać 0 podobieństwa."""
    validator = PersonaValidator()
    assert validator.calculate_text_similarity("", "") == 0.0
    assert validator.calculate_text_similarity("Tekst", "") == 0.0


def test_check_background_uniqueness_detects_duplicates():
    """Walidator powinien wykrywać podobne historie."""
    validator = PersonaValidator(similarity_threshold=0.5)
    personas = [
        _make_persona("Anna uwielbia podróże i gotowanie, pracuje w marketingu."),
        _make_persona("Anna uwielbia podróże i gotowanie, pracuje w marketingu."),
        _make_persona("Kasia to inżynierka z zamiłowaniem do robotyki."),
    ]

    result = validator.check_background_uniqueness(personas)

    assert result["is_unique"] is False
    assert result["total_comparisons"] == 3
    assert result["duplicate_pairs"], "Powinna istnieć co najmniej jedna para duplikatów"


def test_check_diversity_score_balanced_group():
    """Zróżnicowana grupa powinna uzyskać wysoki wynik różnorodności."""
    validator = PersonaValidator()
    personas = [
        _make_persona(
            "Maria prowadzi startup edukacyjny.",
            age=28,
            gender="female",
            location="Warsaw",
            education="Master",
            income="30k-40k",
            values=["Innovation", "Adventure"],
            traits={
                "openness": 0.9,
                "conscientiousness": 0.4,
                "extraversion": 0.7,
                "agreeableness": 0.5,
                "neuroticism": 0.2,
            },
        ),
        _make_persona(
            "Piotr jest konserwatywnym finansistą.",
            age=52,
            gender="male",
            location="Krakow",
            education="Bachelor",
            income="70k-90k",
            values=["Stability", "Family"],
            traits={
                "openness": 0.3,
                "conscientiousness": 0.8,
                "extraversion": 0.2,
                "agreeableness": 0.4,
                "neuroticism": 0.5,
            },
        ),
    ]

    diversity = validator.check_diversity_score(personas)

    assert diversity["diversity_score"] >= 0.5
    assert diversity["demographic_diversity"] > 0
    assert diversity["personality_diversity"] > 0


def test_validate_personas_generates_recommendations():
    """Mało zróżnicowane persony powinny generować rekomendacje."""
    validator = PersonaValidator(similarity_threshold=0.9)
    personas = [
        _make_persona("Ala kocha sport.", age=30, gender="female", values=["Health"]),
        _make_persona("Ola kocha sport.", age=30, gender="female", values=["Health"]),
    ]

    results = validator.validate_personas(personas)

    assert results["is_valid"] is False
    assert results["recommendations"], "Powinny zostać wygenerowane rekomendacje"
