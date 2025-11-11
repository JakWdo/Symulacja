"""
Insight Traceability Service - Evidence trail & provenance tracking

Serwis do zarządzania insight evidence:
- Zapisywanie insightów z provenance (model, prompt, sources)
- Tracking adoption (viewed, shared, exported, adopted)
- Pobieranie evidence trail dla transparency
"""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InsightEvidence


class InsightTraceabilityService:
    """Serwis do śledzenia pochodzenia i adopcji insightów"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_insight_evidence(
        self,
        project_id: UUID,
        insight_text: str,
        insight_type: str,
        confidence_score: float,
        impact_score: int,
        evidence: list[dict[str, Any]],
        concepts: list[str],
        sentiment: str,
        model_version: str,
        prompt: str,
        sources: list[dict[str, Any]],
        focus_group_id: UUID | None = None,
    ) -> InsightEvidence:
        """
        Zapisz insight z pełnym evidence trail

        Args:
            project_id: UUID projektu
            insight_text: Treść insightu
            insight_type: Typ ('opportunity', 'risk', 'trend', 'pattern')
            confidence_score: Confidence (0-1)
            impact_score: Impact (1-10)
            evidence: Lista evidence (quotes, snippets)
            concepts: Kluczowe koncepty
            sentiment: Sentiment ('positive', 'negative', 'neutral', 'mixed')
            model_version: Nazwa modelu ('gemini-2.5-flash')
            prompt: Prompt użyty do generacji
            sources: Source references
            focus_group_id: UUID focus group (optional)

        Returns:
            InsightEvidence: Zapisany insight
        """
        # Calculate prompt hash for reproducibility
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        insight = InsightEvidence(
            project_id=project_id,
            focus_group_id=focus_group_id,
            insight_type=insight_type,
            insight_text=insight_text,
            confidence_score=confidence_score,
            impact_score=impact_score,
            evidence=evidence,
            concepts=concepts,
            sentiment=sentiment,
            model_version=model_version,
            prompt_hash=prompt_hash,
            sources=sources,
        )

        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        return insight

    async def get_insight_provenance(
        self, insight_id: UUID
    ) -> dict[str, Any] | None:
        """
        Pobierz provenance insightu (model, sources, timestamp)

        Args:
            insight_id: UUID insightu

        Returns:
            Provenance data lub None
        """
        stmt = select(InsightEvidence).where(InsightEvidence.id == insight_id)
        result = await self.db.execute(stmt)
        insight = result.scalar_one_or_none()

        if not insight:
            return None

        return {
            "model_version": insight.model_version,
            "prompt_hash": insight.prompt_hash,
            "sources": insight.sources,
            "created_at": insight.created_at,
        }

    async def track_insight_adoption(
        self,
        insight_id: UUID,
        action: str,  # 'viewed', 'shared', 'exported', 'adopted'
    ) -> InsightEvidence:
        """
        Track adoption action na insighcie

        Args:
            insight_id: UUID insightu
            action: Typ akcji ('viewed', 'shared', 'exported', 'adopted')

        Returns:
            InsightEvidence: Zaktualizowany insight
        """
        stmt = select(InsightEvidence).where(InsightEvidence.id == insight_id)
        result = await self.db.execute(stmt)
        insight = result.scalar_one()

        now = datetime.utcnow()

        if action == "viewed" and not insight.viewed_at:
            insight.viewed_at = now
        elif action == "shared" and not insight.shared_at:
            insight.shared_at = now
        elif action == "exported" and not insight.exported_at:
            insight.exported_at = now
        elif action == "adopted" and not insight.adopted_at:
            insight.adopted_at = now

        await self.db.commit()
        await self.db.refresh(insight)

        return insight

    async def get_project_insights(
        self,
        project_id: UUID,
        insight_type: str | None = None,
        min_confidence: float | None = None,
        limit: int = 50,
    ) -> list[InsightEvidence]:
        """
        Pobierz insighty dla projektu

        Args:
            project_id: UUID projektu
            insight_type: Filtruj po typie (optional)
            min_confidence: Minimalna confidence (optional)
            limit: Maksymalna liczba wyników

        Returns:
            Lista InsightEvidence
        """
        stmt = select(InsightEvidence).where(
            InsightEvidence.project_id == project_id
        )

        if insight_type:
            stmt = stmt.where(InsightEvidence.insight_type == insight_type)

        if min_confidence is not None:
            stmt = stmt.where(InsightEvidence.confidence_score >= min_confidence)

        stmt = stmt.order_by(InsightEvidence.created_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
