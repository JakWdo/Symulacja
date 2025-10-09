"""Testy funkcji pomocniczych DiscussionSummarizerService."""

from types import SimpleNamespace

import numpy as np

from app.services.discussion_summarizer import (
    DiscussionSummarizerService,
    _simple_sentiment_score,
)


class DummyFocusGroup:
    """Prosty obiekt udający model SQLAlchemy."""

    def __init__(self):
        self.name = "Nowy produkt"
        self.description = "Dyskusja o nowym produkcie"
        self.questions = ["Co sądzisz o produkcie?"]


class DummyPersona:
    """Imituje personę z wymaganymi polami."""

    def __init__(self, age, gender, education, occupation):
        self.age = age
        self.gender = gender
        self.education_level = education
        self.occupation = occupation


def test_simple_sentiment_score_balanced():
    """Analiza sentymentu powinna rozpoznawać pozytywne i negatywne słowa."""
    text = "I love the idea but I hate the execution"
    score = _simple_sentiment_score(text)
    assert np.isclose(score, 0.0)


def test_prepare_discussion_data_builds_structure():
    """Metoda powinna grupować odpowiedzi oraz liczyć sentyment."""
    service = DiscussionSummarizerService.__new__(DiscussionSummarizerService)

    focus_group = DummyFocusGroup()
    responses = [
        SimpleNamespace(
            question="Co sądzisz o produkcie?",
            response="I love the sleek design",
            persona_id="1",
        ),
        SimpleNamespace(
            question="Co sądzisz o produkcie?",
            response="I dislike the price point",
            persona_id="2",
        ),
    ]
    personas = {
        "1": DummyPersona(25, "female", "Master", "Designer"),
        "2": DummyPersona(45, "male", "Bachelor", "Manager"),
    }

    data = service._prepare_discussion_data(focus_group, responses, personas, True)

    assert data["topic"] == focus_group.name
    assert data["total_responses"] == 2
    assert len(data["responses_by_question"]["Co sądzisz o produkcie?"]) == 2
    sentiments = [item["sentiment"] for item in data["responses_by_question"]["Co sądzisz o produkcie?"]]
    assert all(-1.0 <= s <= 1.0 for s in sentiments)


def test_create_summary_prompt_contains_sections():
    """Prompt powinien zawierać kluczowe nagłówki do analizy."""
    service = DiscussionSummarizerService.__new__(DiscussionSummarizerService)
    discussion = {
        "topic": "Produkt",
        "description": "Opis",
        "responses_by_question": {
            "Co?": [
                {"response": "I love it", "sentiment": 0.5, "demographics": {"gender": "female", "age": 25, "occupation": "UX"}},
            ]
        },
        "demographic_summary": {
            "sample_size": 2,
            "age_range": "20-40",
            "gender_distribution": {"female": 1, "male": 1},
            "education_levels": ["Master"],
        },
    }

    prompt = service._create_summary_prompt(discussion, include_recommendations=True)

    assert "EXECUTIVE SUMMARY" in prompt
    assert "STRATEGIC RECOMMENDATIONS" in prompt
    assert "SENTIMENT NARRATIVE" in prompt


def test_parse_ai_response_splits_sections():
    """Parser powinien poprawnie rozdzielać sekcje Markdown."""
    service = DiscussionSummarizerService.__new__(DiscussionSummarizerService)
    ai_text = """## Executive Summary
Kluczowe wnioski.

## Key Insights
- **Insight**: przykład

## Surprising Findings
- **Finding**: coś

## Segment Analysis
**Młodzi**: lubią produkt

## Strategic Recommendations
- **Action**: zrób coś

## Sentiment Narrative
Neutralny ton.
"""

    sections = service._parse_ai_response(ai_text)

    assert sections["executive_summary"].startswith("Kluczowe")
    assert sections["key_insights"][0].endswith("przykład")
    assert sections["surprising_findings"][0].endswith("coś")
    assert sections["segment_analysis"] == {"Młodzi": "lubią produkt"}
    assert sections["recommendations"][0].endswith("zrób coś")
    assert sections["sentiment_narrative"].startswith("Neutralny")
