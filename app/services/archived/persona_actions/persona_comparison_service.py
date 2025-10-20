"""
PersonaComparisonService - compare personas and highlight differences.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona
from app.utils.math_utils import cosine_similarity


class PersonaComparisonService:
    """Compare personas side-by-side and compute similarity scores."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def compare_personas(
        self,
        primary_persona: Persona,
        other_persona_ids: List[str],
        *,
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare primary persona with up to two others.

        Args:
            primary_persona: Persona selected in UI (fully loaded)
            other_persona_ids: list of persona IDs (max 2)
            sections: optional list of sections to compare
        """
        persona_ids = [primary_persona.id] + [pid for pid in other_persona_ids if pid != str(primary_persona.id)]
        persona_ids = persona_ids[:3]

        result = await self.db.execute(select(Persona).where(Persona.id.in_(persona_ids)))
        personas = result.scalars().all()
        persona_map = {str(p.id): p for p in personas}

        ordered = [primary_persona] + [persona_map[pid] for pid in other_persona_ids if pid in persona_map]

        comparisons = [self._serialize_persona(p) for p in ordered]
        differences = self._collect_differences(ordered, sections)
        similarity_matrix = self._compute_similarity_matrix(ordered)

        return {
            "personas": comparisons,
            "differences": differences,
            "similarity": similarity_matrix,
        }

    def _serialize_persona(self, persona: Persona) -> Dict[str, Any]:
        return {
            "id": str(persona.id),
            "full_name": persona.full_name,
            "age": persona.age,
            "gender": persona.gender,
            "location": persona.location,
            "occupation": persona.occupation,
            "education_level": persona.education_level,
            "segment_id": persona.segment_id,
            "segment_name": persona.segment_name,
            "values": persona.values or [],
            "interests": persona.interests or [],
            # kpi_snapshot removed - use PersonaKPIService for real-time metrics
            "big_five": {
                "openness": persona.openness,
                "conscientiousness": persona.conscientiousness,
                "extraversion": persona.extraversion,
                "agreeableness": persona.agreeableness,
                "neuroticism": persona.neuroticism,
            },
        }

    def _collect_differences(
        self,
        personas: List[Persona],
        sections: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        # KPI section removed - use PersonaKPIService for real-time metrics comparison
        tracked_sections = set(sections or ["demographics", "psychographics"])
        differences: List[Dict[str, Any]] = []

        if "demographics" in tracked_sections:
            differences.extend(self._diff_field(personas, "location"))
            differences.extend(self._diff_field(personas, "occupation"))
            differences.extend(self._diff_field(personas, "education_level"))
            differences.extend(self._diff_field(personas, "income_bracket"))

        if "psychographics" in tracked_sections:
            for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
                differences.extend(self._diff_field(personas, trait))

            differences.extend(self._diff_list_field(personas, "values"))
            differences.extend(self._diff_list_field(personas, "interests"))

        # Note: KPI comparison removed - deprecated field
        # For KPI comparison, use PersonaKPIService directly in frontend

        return differences

    def _diff_field(self, personas: List[Persona], attr: str) -> List[Dict[str, Any]]:
        values = [getattr(p, attr, None) for p in personas]
        if len(set(values)) <= 1:
            return []
        return [
            {
                "field": attr,
                "values": [
                    {"persona_id": str(personas[i].id), "value": values[i]}
                    for i in range(len(personas))
                ],
            }
        ]

    def _diff_list_field(self, personas: List[Persona], attr: str) -> List[Dict[str, Any]]:
        values = [tuple(getattr(p, attr) or []) for p in personas]
        if len(set(values)) <= 1:
            return []
        diff_entry = {
            "field": attr,
            "values": [
                {"persona_id": str(persona.id), "value": list(entry)}
                for persona, entry in zip(personas, values, strict=False)
            ],
        }
        return [diff_entry]

    # _diff_kpi method removed - KPI comparison deprecated
    # Use PersonaKPIService for real-time metrics calculation instead

    def _compute_similarity_matrix(self, personas: List[Persona]) -> Dict[str, Any]:
        matrix = {}
        for i, persona_a in enumerate(personas):
            row = {}
            vector_a = self._personality_vector(persona_a)
            for j, persona_b in enumerate(personas):
                if i == j:
                    row[str(persona_b.id)] = 1.0
                else:
                    vector_b = self._personality_vector(persona_b)
                    row[str(persona_b.id)] = cosine_similarity(vector_a, vector_b)
            matrix[str(persona_a.id)] = row
        return matrix

    def _personality_vector(self, persona: Persona) -> List[float]:
        return [
            float(persona.openness or 0.5),
            float(persona.conscientiousness or 0.5),
            float(persona.extraversion or 0.5),
            float(persona.agreeableness or 0.5),
            float(persona.neuroticism or 0.5),
        ]
