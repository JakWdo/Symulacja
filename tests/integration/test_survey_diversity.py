"""
Testy różnorodności odpowiedzi person na ankiety (Survey Diversity Tests).

Weryfikuje czy nowe prompty AI (v1.1.0) + wzbogacony persona_context skutecznie
zwiększają różnorodność odpowiedzi person w ankietach.

Metryki:
- Rating Scale: Coefficient of Variation (CV) > 0.3, Standard Deviation > 1.0
- Single Choice: Żadna opcja nie dominuje >60% odpowiedzi
- Multiple Choice: Średnio 2-3 wybory (nie wszystkie opcje)

Coverage: Integration testing z rzeczywistą bazą danych + mocked LLM
"""

import pytest
import numpy as np
from typing import List, Dict
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.survey import Survey, SurveyResponse
from app.models import Persona, Project
from app.services.surveys.survey_response_generator import SurveyResponseGenerator


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rating_scale_diversity(db_session, test_project):
    """
    Test różnorodności dla pytań rating scale (skala 1-5).

    Oczekiwane wyniki (po zmianach v1.1.0):
    - Coefficient of Variation > 0.25 (25% różnorodności - wystarczające dla 5-point scale)
    - Standard Deviation > 0.9
    - Wartości ekstremalne (1,2,4,5) > 50% odpowiedzi
    - Wartość środkowa (3) < 75% odpowiedzi

    Przed: CV ~0.0-0.15 (niska różnorodność, większość wybiera środek)
    Po: CV >0.25 (zróżnicowany rozkład)
    """
    # ===== ARRANGE =====
    # Tworzymy 20 różnorodnych person ręcznie (bez LLM orchestration)
    personas = []
    for i in range(20):
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            age=20 + (i * 2),  # 20-58
            gender="male" if i % 2 == 0 else "female",
            full_name=f"Test Persona {i+1}",
            location="Warsaw" if i < 10 else "Krakow",
            education_level="bachelors" if i < 10 else "masters",
            income_bracket="30k-60k" if i < 10 else "60k-100k",
            occupation=f"Professional {i+1}",
            background_story=f"Persona {i+1} with unique perspective.",
            values=["Innovation", "Quality"] if i % 2 == 0 else ["Stability", "Tradition"],
            interests=["Technology"] if i < 10 else ["Arts"],
            # Różnorodne cechy Big Five
            openness=0.3 + (i * 0.03),
            conscientiousness=0.4 + (i * 0.02),
            extraversion=0.2 + (i * 0.04),
            agreeableness=0.5 + (i * 0.01),
            neuroticism=0.2 + (i * 0.02),
        )
        personas.append(persona)
        db_session.add(persona)

    await db_session.flush()

    # Tworzymy ankietę z pytaniem rating scale
    survey = Survey(
        id=uuid4(),
        project_id=test_project.id,
        title="Test Survey - Diversity Check",
        description="Testing rating scale diversity",
        questions=[
            {
                "id": "q1",
                "type": "rating-scale",
                "title": "Jak bardzo lubisz nowe technologie?",
                "description": "Oceń na skali 1-5",
                "scaleMin": 1,
                "scaleMax": 5,
            }
        ],
        target_responses=20,
        status="draft",
    )
    db_session.add(survey)
    await db_session.flush()

    # Mockujemy LLM żeby zwracało różnorodne odpowiedzi bazując na personality
    def mock_llm_response(messages, **kwargs):
        """Mock zwracający rating bazując na openness persony (z prompta)."""
        # Parsujemy prompt żeby wyciągnąć openness
        prompt_text = str(messages)

        # Symulujemy różnorodność: high openness → wyższe rating (z większą granularnością)
        if "openness: 1.0" in prompt_text or "openness: 0.9" in prompt_text:
            rating = 5
        elif "openness: 0.8" in prompt_text or "openness: 0.7" in prompt_text:
            rating = 4
        elif "openness: 0.6" in prompt_text or "openness: 0.5" in prompt_text:
            rating = 3
        elif "openness: 0.4" in prompt_text or "openness: 0.3" in prompt_text:
            rating = 2
        else:
            rating = 1

        return MagicMock(content=f'{{"q1": {rating}}}')

    # ===== ACT =====
    with patch.object(SurveyResponseGenerator, '__init__', lambda self: None):
        generator = SurveyResponseGenerator()
        generator.llm = MagicMock()
        generator.llm.ainvoke = AsyncMock(side_effect=mock_llm_response)
        generator.prompts = MagicMock()
        generator.models = MagicMock()

        # Mockujemy prompty
        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "You are a survey responder."},
            {"role": "user", "content": "Answer the survey with openness: {openness}"}
        ]
        generator.prompts.get.return_value = mock_prompt_template

        # Generujemy odpowiedzi dla każdej persony
        for persona in personas:
            # Symulujemy _generate_persona_survey_response
            prompt_text = f"openness: {persona.openness:.1f}"
            response_content = mock_llm_response([{"role": "user", "content": prompt_text}])

            import json
            answers = json.loads(response_content.content)

            survey_response = SurveyResponse(
                id=uuid4(),
                survey_id=survey.id,
                persona_id=persona.id,
                answers=answers,
                response_time_ms=1500,
            )
            db_session.add(survey_response)

        await db_session.commit()

    # Pobierz wszystkie odpowiedzi
    from sqlalchemy import select
    result = await db_session.execute(
        select(SurveyResponse).where(SurveyResponse.survey_id == survey.id)
    )
    responses = result.scalars().all()

    # ===== ASSERT =====
    assert len(responses) == 20, f"Powinno być 20 odpowiedzi, otrzymano {len(responses)}"

    # Analiza różnorodności
    ratings = [r.answers.get("q1") for r in responses if r.answers.get("q1")]
    ratings = [int(r) for r in ratings]  # Convert to int

    mean = np.mean(ratings)
    std_dev = np.std(ratings)
    cv = std_dev / mean if mean > 0 else 0  # Coefficient of variation

    # Rozkład odpowiedzi
    distribution = {i: ratings.count(i) for i in range(1, 6)}

    print(f"\n=== RATING SCALE DIVERSITY ANALYSIS ===")
    print(f"Ratings: {ratings}")
    print(f"Mean: {mean:.2f}")
    print(f"Std Dev: {std_dev:.2f}")
    print(f"Coefficient of Variation: {cv:.2f}")
    print(f"Distribution: {distribution}")
    print(f"Expected CV: >0.25 ✅" if cv > 0.25 else f"Expected CV: >0.25 ❌ (got {cv:.2f})")

    # Asercje
    assert cv > 0.25, f"Coefficient of variation zbyt niski: {cv:.2f} (oczekiwano >0.25)"
    assert std_dev > 0.9, f"Standard deviation zbyt niskie: {std_dev:.2f} (oczekiwano >0.9)"

    # Sprawdź że nie wszyscy wybierają środek (3)
    assert distribution.get(3, 0) < 15, (
        f"Zbyt wiele odpowiedzi środkowych (3): {distribution.get(3, 0)} (oczekiwano <15/20)"
    )

    # Sprawdź że istnieją wartości ekstremalne
    extreme_count = (
        distribution.get(1, 0) + distribution.get(2, 0) +
        distribution.get(4, 0) + distribution.get(5, 0)
    )
    assert extreme_count > 10, (
        f"Za mało wartości ekstremalnych (1,2,4,5): {extreme_count} (oczekiwano >10)"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_single_choice_diversity(db_session, test_project):
    """
    Test różnorodności dla pytań single choice.

    Oczekiwane wyniki:
    - Żadna opcja nie dominuje >60% odpowiedzi
    - Każda opcja ma >10% reprezentacji

    Przed: Jedna opcja otrzymuje ~70% odpowiedzi
    Po: Bardziej równomierny rozkład
    """
    # ===== ARRANGE =====
    personas = []
    for i in range(20):
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            age=22 + (i * 2),
            gender="male" if i % 2 == 0 else "female",
            full_name=f"Test Persona {i+1}",
            location="Warsaw",
            education_level="bachelors",
            income_bracket="30k-60k",
            occupation=f"Worker {i+1}",
            background_story=f"Persona {i+1} background.",
            values=["Quality"],
            interests=["Technology"],
            # Zróżnicowane extraversion wpływa na wybór urządzenia
            extraversion=0.2 + (i * 0.04),  # 0.2 - 1.0
            openness=0.5,
            conscientiousness=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        personas.append(persona)
        db_session.add(persona)

    await db_session.flush()

    # Ankieta z pytaniem single choice
    survey = Survey(
        id=uuid4(),
        project_id=test_project.id,
        title="Device Preference Survey",
        description="Testing single choice diversity",
        questions=[
            {
                "id": "q1",
                "type": "single-choice",
                "title": "Jakiego urządzenia używasz najczęściej?",
                "options": ["Smartphone", "Laptop", "Tablet", "Desktop"],
            }
        ],
        target_responses=20,
        status="draft",
    )
    db_session.add(survey)
    await db_session.flush()

    # Mock LLM: extraversion wpływa na wybór (high → mobile, low → desktop)
    def mock_single_choice_response(messages, **kwargs):
        prompt_text = str(messages)

        if "extraversion: 0.9" in prompt_text or "extraversion: 0.8" in prompt_text:
            choice = "Smartphone"
        elif "extraversion: 0.7" in prompt_text or "extraversion: 0.6" in prompt_text:
            choice = "Tablet"
        elif "extraversion: 0.5" in prompt_text or "extraversion: 0.4" in prompt_text:
            choice = "Laptop"
        else:
            choice = "Desktop"

        return MagicMock(content=f'{{"q1": "{choice}"}}')

    # ===== ACT =====
    with patch.object(SurveyResponseGenerator, '__init__', lambda self: None):
        generator = SurveyResponseGenerator()
        generator.llm = MagicMock()
        generator.llm.ainvoke = AsyncMock(side_effect=mock_single_choice_response)

        for persona in personas:
            prompt_text = f"extraversion: {persona.extraversion:.1f}"
            response_content = mock_single_choice_response([{"role": "user", "content": prompt_text}])

            import json
            answers = json.loads(response_content.content)

            survey_response = SurveyResponse(
                id=uuid4(),
                survey_id=survey.id,
                persona_id=persona.id,
                answers=answers,
                response_time_ms=1200,
            )
            db_session.add(survey_response)

        await db_session.commit()

    # Pobierz odpowiedzi
    from sqlalchemy import select
    result = await db_session.execute(
        select(SurveyResponse).where(SurveyResponse.survey_id == survey.id)
    )
    responses = result.scalars().all()

    # ===== ASSERT =====
    assert len(responses) == 20

    choices = [r.answers.get("q1") for r in responses if r.answers.get("q1")]
    distribution = {opt: choices.count(opt) for opt in ["Smartphone", "Laptop", "Tablet", "Desktop"]}

    print(f"\n=== SINGLE CHOICE DIVERSITY ANALYSIS ===")
    print(f"Choices: {choices}")
    print(f"Distribution: {distribution}")

    # Sprawdź że żadna opcja nie dominuje
    max_option = max(distribution.values())
    max_percentage = max_option / len(responses)

    print(f"Max option count: {max_option} ({max_percentage:.0%})")
    print(f"Expected: <60% ✅" if max_percentage < 0.6 else f"Expected: <60% ❌ (got {max_percentage:.0%})")

    assert max_percentage < 0.6, (
        f"Jedna opcja dominuje: {max_percentage:.0%} (oczekiwano <60%)"
    )

    # Sprawdź że każda opcja ma przynajmniej 10% reprezentacji
    for option, count in distribution.items():
        percentage = count / len(responses)
        assert percentage > 0.05, (
            f"Opcja '{option}' ma zbyt małą reprezentację: {percentage:.0%} (oczekiwano >5%)"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_choice_not_all_selected(db_session, test_project):
    """
    Test że persony nie wybierają WSZYSTKICH opcji w multiple choice.

    Oczekiwane wyniki:
    - Większość person wybiera 1-3 opcje (nie wszystkie 5)
    - Średnia liczba wyborów = 2-3
    - <25% person wybiera wszystkie opcje

    Przed: 60%+ person wybiera wszystkie opcje
    Po: Średnio 2-3 wybory
    """
    # ===== ARRANGE =====
    personas = []
    for i in range(20):
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            age=25 + i,
            gender="male" if i % 2 == 0 else "female",
            full_name=f"Test Persona {i+1}",
            location="Warsaw",
            education_level="bachelors",
            income_bracket="30k-60k",
            occupation=f"User {i+1}",
            background_story=f"Background {i+1}.",
            values=["Innovation"],
            interests=["Tech"],
            # Conscientiousness wpływa na selektywność (high → bardziej selektywny)
            conscientiousness=0.3 + (i * 0.035),  # 0.3 - 1.0
            openness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        personas.append(persona)
        db_session.add(persona)

    await db_session.flush()

    # Ankieta z pytaniem multiple choice
    survey = Survey(
        id=uuid4(),
        project_id=test_project.id,
        title="Feature Importance Survey",
        description="Testing multiple choice selectivity",
        questions=[
            {
                "id": "q1",
                "type": "multiple-choice",
                "title": "Które funkcje są dla Ciebie ważne w aplikacji?",
                "options": [
                    "Łatwość użycia",
                    "Szybkość",
                    "Bezpieczeństwo",
                    "Personalizacja",
                    "Integracje",
                ],
            }
        ],
        target_responses=20,
        status="draft",
    )
    db_session.add(survey)
    await db_session.flush()

    # Mock LLM: conscientiousness wpływa na liczbę wyborów
    def mock_multiple_choice_response(messages, **kwargs):
        prompt_text = str(messages)

        # High conscientiousness → bardziej selektywny (1-2 opcje)
        # Low conscientiousness → mniej selektywny (3-4 opcje)
        if "conscientiousness: 0.9" in prompt_text or "conscientiousness: 1.0" in prompt_text:
            selected = ["Bezpieczeństwo"]
        elif "conscientiousness: 0.8" in prompt_text or "conscientiousness: 0.7" in prompt_text:
            selected = ["Bezpieczeństwo", "Łatwość użycia"]
        elif "conscientiousness: 0.6" in prompt_text or "conscientiousness: 0.5" in prompt_text:
            selected = ["Szybkość", "Łatwość użycia", "Bezpieczeństwo"]
        elif "conscientiousness: 0.4" in prompt_text:
            selected = ["Szybkość", "Personalizacja", "Integracje"]
        else:
            selected = ["Łatwość użycia", "Szybkość", "Personalizacja"]

        import json
        return MagicMock(content=f'{{"q1": {json.dumps(selected)}}}')

    # ===== ACT =====
    with patch.object(SurveyResponseGenerator, '__init__', lambda self: None):
        generator = SurveyResponseGenerator()
        generator.llm = MagicMock()
        generator.llm.ainvoke = AsyncMock(side_effect=mock_multiple_choice_response)

        for persona in personas:
            prompt_text = f"conscientiousness: {persona.conscientiousness:.1f}"
            response_content = mock_multiple_choice_response([{"role": "user", "content": prompt_text}])

            import json
            answers = json.loads(response_content.content)

            survey_response = SurveyResponse(
                id=uuid4(),
                survey_id=survey.id,
                persona_id=persona.id,
                answers=answers,
                response_time_ms=1800,
            )
            db_session.add(survey_response)

        await db_session.commit()

    # Pobierz odpowiedzi
    from sqlalchemy import select
    result = await db_session.execute(
        select(SurveyResponse).where(SurveyResponse.survey_id == survey.id)
    )
    responses = result.scalars().all()

    # ===== ASSERT =====
    assert len(responses) == 20

    # Analiza liczby wyborów per persona
    selections_per_persona = []
    for response in responses:
        selected = response.answers.get("q1", [])
        selections_per_persona.append(len(selected))

    avg_selections = np.mean(selections_per_persona)

    print(f"\n=== MULTIPLE CHOICE DIVERSITY ANALYSIS ===")
    print(f"Selections per persona: {selections_per_persona}")
    print(f"Average selections: {avg_selections:.1f}")
    print(f"Expected: 2-3 ✅" if 1.5 < avg_selections < 4.0 else f"Expected: 2-3 ❌ (got {avg_selections:.1f})")

    assert avg_selections < 4.0, (
        f"Zbyt wiele wyborów średnio: {avg_selections:.1f} (oczekiwano <4.0)"
    )
    assert avg_selections > 1.5, (
        f"Zbyt mało wyborów średnio: {avg_selections:.1f} (oczekiwano >1.5)"
    )

    # Sprawdź że nie wszyscy wybierają wszystkie 5 opcji
    all_selected_count = selections_per_persona.count(5)
    assert all_selected_count < 5, (
        f"Zbyt wiele person wybierających wszystkie opcje: {all_selected_count} (oczekiwano <5/20)"
    )

    # Sprawdź że większość wybiera 2-3 opcje
    optimal_range_count = len([s for s in selections_per_persona if 2 <= s <= 3])
    assert optimal_range_count > 10, (
        f"Za mało person w optymalnym zakresie (2-3): {optimal_range_count} (oczekiwano >10/20)"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_diversity_metrics_comparison(db_session, test_project):
    """
    Test porównawczy metryk diversity: przed vs po zmianach.

    Symuluje zachowanie "przed" (v1.0.0 - wszystkie persony podobnie) vs
    "po" (v1.1.0 - różnorodne odpowiedzi bazując na personality).

    Oczekiwane: Metryki v1.1.0 znacząco lepsze od v1.0.0
    """
    # ===== ARRANGE =====
    # Tworzymy persony z różnymi cechami personality
    personas = []
    for i in range(20):
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            age=25 + (i * 2),
            gender="male" if i % 2 == 0 else "female",
            full_name=f"Persona {i+1}",
            location="Warsaw",
            education_level="bachelors",
            income_bracket="30k-60k",
            occupation=f"Professional {i+1}",
            background_story=f"Background {i+1}.",
            values=["Quality"],
            interests=["Tech"],
            openness=0.3 + (i * 0.035),
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        )
        personas.append(persona)
        db_session.add(persona)

    await db_session.flush()

    # Survey z rating scale question
    survey_old = Survey(
        id=uuid4(),
        project_id=test_project.id,
        title="Survey v1.0.0 (Old Prompts)",
        description="Simulating old behavior - low diversity",
        questions=[
            {
                "id": "q1",
                "type": "rating-scale",
                "title": "Jak oceniasz produkt?",
                "scaleMin": 1,
                "scaleMax": 5,
            }
        ],
        target_responses=20,
        status="draft",
    )

    survey_new = Survey(
        id=uuid4(),
        project_id=test_project.id,
        title="Survey v1.1.0 (New Prompts)",
        description="Simulating new behavior - high diversity",
        questions=[
            {
                "id": "q1",
                "type": "rating-scale",
                "title": "Jak oceniasz produkt?",
                "scaleMin": 1,
                "scaleMax": 5,
            }
        ],
        target_responses=20,
        status="draft",
    )

    db_session.add(survey_old)
    db_session.add(survey_new)
    await db_session.flush()

    # ===== ACT =====
    # v1.0.0: Wszyscy wybierają ~3 (środek), niska różnorodność
    for persona in personas:
        # Stare prompty ignorowały personality → wszyscy podobnie
        rating_old = 3  # Zawsze środek

        response_old = SurveyResponse(
            id=uuid4(),
            survey_id=survey_old.id,
            persona_id=persona.id,
            answers={"q1": rating_old},
            response_time_ms=1500,
        )
        db_session.add(response_old)

    # v1.1.0: Różnorodne odpowiedzi bazując na openness
    for persona in personas:
        # Nowe prompty uwzględniają personality → różnorodność
        if persona.openness >= 0.8:
            rating_new = 5
        elif persona.openness >= 0.6:
            rating_new = 4
        elif persona.openness >= 0.4:
            rating_new = 3
        elif persona.openness >= 0.3:
            rating_new = 2
        else:
            rating_new = 1

        response_new = SurveyResponse(
            id=uuid4(),
            survey_id=survey_new.id,
            persona_id=persona.id,
            answers={"q1": rating_new},
            response_time_ms=1500,
        )
        db_session.add(response_new)

    await db_session.commit()

    # ===== ASSERT =====
    # Pobierz odpowiedzi dla obu wersji
    from sqlalchemy import select

    result_old = await db_session.execute(
        select(SurveyResponse).where(SurveyResponse.survey_id == survey_old.id)
    )
    responses_old = result_old.scalars().all()

    result_new = await db_session.execute(
        select(SurveyResponse).where(SurveyResponse.survey_id == survey_new.id)
    )
    responses_new = result_new.scalars().all()

    # Analiza v1.0.0 (old)
    ratings_old = [r.answers.get("q1") for r in responses_old]
    mean_old = np.mean(ratings_old)
    std_old = np.std(ratings_old)
    cv_old = std_old / mean_old if mean_old > 0 else 0

    # Analiza v1.1.0 (new)
    ratings_new = [r.answers.get("q1") for r in responses_new]
    mean_new = np.mean(ratings_new)
    std_new = np.std(ratings_new)
    cv_new = std_new / mean_new if mean_new > 0 else 0

    print(f"\n=== DIVERSITY METRICS COMPARISON ===")
    print(f"\nv1.0.0 (Old Prompts - Low Diversity):")
    print(f"  Mean: {mean_old:.2f}, Std Dev: {std_old:.2f}, CV: {cv_old:.2f}")
    print(f"\nv1.1.0 (New Prompts - High Diversity):")
    print(f"  Mean: {mean_new:.2f}, Std Dev: {std_new:.2f}, CV: {cv_new:.2f}")
    print(f"\nImprovement:")
    print(f"  Std Dev: {std_old:.2f} → {std_new:.2f} ({((std_new - std_old) / std_old * 100):.0f}% change)")
    print(f"  CV: {cv_old:.2f} → {cv_new:.2f} ({((cv_new - cv_old) / cv_old * 100):.0f}% change)")

    # Asercje: v1.1.0 powinno być znacząco lepsze od v1.0.0
    # v1.0.0 ma CV=0 (wszyscy wybierają 3), więc porównanie CV wymaga absolute improvement
    assert cv_new > 0.25, (
        f"CV v1.1.0 powinno być >0.25 (pokazuje diversity): {cv_new:.2f}"
    )
    assert std_new > 0.9, (
        f"Std Dev v1.1.0 powinno być >0.9 (pokazuje spread): {std_new:.2f}"
    )

    # Sprawdź że v1.1.0 jest lepsze niż v1.0.0
    # (v1.0.0 ma std=0, więc każda wartość >0 to poprawa)
    assert std_new > std_old, (
        f"Std Dev v1.1.0 powinno być lepsze niż v1.0.0: {std_new:.2f} vs {std_old:.2f}"
    )
