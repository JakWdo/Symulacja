"""Sample data fixtures shared across tests."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.fixture
def sample_persona_dict():
    """Provide a minimal persona payload for schema/unit tests."""
    return {
        "id": uuid4(),
        "project_id": uuid4(),
        "age": 30,
        "gender": "female",
        "location": "Warsaw",
        "education_level": "Master",
        "income_bracket": "50k-70k",
        "occupation": "Software Engineer",
        "full_name": "Anna Kowalska",
        "background_story": "A creative professional who loves technology.",
        "values": ["Innovation", "Quality"],
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.6,
        "agreeableness": 0.7,
        "neuroticism": 0.3,
    }


@pytest.fixture
def sample_project_dict():
    """Provide a minimal project payload for schema/unit tests."""
    return {
        "id": uuid4(),
        "owner_id": uuid4(),
        "name": "Test Research Project",
        "description": "Testing market research features",
        "target_audience": "Young professionals",
        "research_objectives": "Test research features",
        "target_sample_size": 20,
    }

