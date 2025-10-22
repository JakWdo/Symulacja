"""Helper functions for constructing rich API payloads in tests."""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4


def project_payload(**overrides: Any) -> Dict[str, Any]:
    """Return a default project payload that satisfies validation rules.

    Note: target_demographics is now optional. Projects use segment-based
    allocation via PersonaOrchestrationService instead of demographics.
    """
    payload: Dict[str, Any] = {
        "name": "Test Research Project",
        "description": "Integration test project",
        "target_audience": "Young professionals aged 25-35",
        "research_objectives": "Validate feature set",
        "target_sample_size": 10,
    }
    payload.update(overrides)
    return payload


def focus_group_payload(persona_ids: List[str], **overrides: Any) -> Dict[str, Any]:
    """Return a default focus-group payload with provided persona IDs."""
    payload: Dict[str, Any] = {
        "name": "Test Focus Group",
        "description": "Focus group integration scenario",
        "persona_ids": persona_ids,
        "questions": [
            "What do you think about this product?",
            "Would you recommend it?",
        ],
        "mode": "normal",
    }
    payload.update(overrides)
    return payload


def persona_generation_request(num_personas: int = 5, **overrides: Any) -> Dict[str, Any]:
    """Return a payload for persona generation API calls."""
    payload: Dict[str, Any] = {
        "num_personas": num_personas,
        "adversarial_mode": False,
    }
    payload.update(overrides)
    return payload


def unique_email(prefix: str = "user") -> str:
    """Generate a unique email address for authentication tests."""
    return f"{prefix}_{uuid4().hex[:8]}@example.com"

