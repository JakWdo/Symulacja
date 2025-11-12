"""
Serwis Podsumowań Dyskusji oparty na AI

Generuje automatyczne podsumowania grup fokusowych przy użyciu Google Gemini.
Analizuje wszystkie odpowiedzi i tworzy executive summary, key insights,
rekomendacje biznesowe oraz segmentację demograficzną.

Obsługuje dwa modele:
- Gemini 2.5 Flash: szybsze podsumowania (domyślne)
- Gemini 2.5 Pro: bardziej szczegółowa analiza
"""

import logging
import re
from datetime import datetime
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FocusGroup, PersonaResponse, Persona, Project
from app.services.shared.clients import build_chat_model
from app.services.dashboard.usage import log_usage_from_metadata, UsageLogContext
from app.services.dashboard.cache_invalidation import invalidate_dashboard_cache

# Import modularized utilities
from ..discussion.data_preparation import prepare_discussion_data, prepare_prompt_variables
from .insight_persistence import store_insights_from_summary

logger = logging.getLogger(__name__)

# Regex patterns for parsing
_BULLET_PREFIX_RE = re.compile(r"^[-*•\d\.\)\s]+")
_SEGMENT_LINE_RE = re.compile(r"\*\*(.+?)\*\*\s*[:\-–]\s*(.+)")


class DiscussionSummarizerService:
    """
    Generuje AI-powered podsumowania dyskusji grup fokusowych

    Wykorzystuje Google Gemini do analizy wszystkich odpowiedzi
    i tworzenia strukturalnych insightów biznesowych.
    """

    def __init__(self, use_pro_model: bool = False):
        """
        Inicjalizuj summarizer z wyborem modelu

        Args:
            use_pro_model: True = gemini-2.5-pro (wolniejszy, lepsza jakość)
                          False = gemini-2.5-flash (szybszy, zbalansowana jakość)
        """
        # Dobieramy model do jakości i czasu wykonania
        from config import models

        # Model config z centralnego registry
        model_config = models.get("focus_groups", "summarization")
        self.llm = build_chat_model(**model_config.params)

        self.str_parser = StrOutputParser()

    async def generate_discussion_summary(
        self,
        db: AsyncSession,
        focus_group_id: str,
        include_demographics: bool = True,
        include_recommendations: bool = True,
        preferred_language: str | None = None,
    ) -> dict[str, Any]:
        """
        Generuje kompleksowe AI-powered podsumowanie dyskusji grupy fokusowej

        Args:
            db: Sesja bazy danych
            focus_group_id: ID grupy fokusowej
            include_demographics: Czy uwzględnić dane demograficzne
            include_recommendations: Czy zawrzeć rekomendacje strategiczne
            preferred_language: Docelowy język treści ("pl" lub "en"); jeśli None, wykryj automatycznie

        Returns:
            {
                "executive_summary": str,
                "key_insights": List[str],
                "surprising_findings": List[str],
                "segment_analysis": Dict[str, Any],
                "recommendations": List[str],
                "sentiment_narrative": str,
                "metadata": Dict[str, Any]
            }
        """
        # Pobieramy grupę fokusową wraz z projektem (dla user_id)
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group:
            raise ValueError("Focus group not found")

        if focus_group.status != "completed":
            raise ValueError("Focus group must be completed to generate summary")

        # Fetch project to get owner_id (for token usage logging)
        project_result = await db.execute(
            select(Project).where(Project.id == focus_group.project_id)
        )
        project = project_result.scalar_one_or_none()
        user_id = project.owner_id if project else None

        # Pobieramy wszystkie odpowiedzi
        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
            .order_by(PersonaResponse.created_at)
        )
        responses = result.scalars().all()

        if not responses:
            raise ValueError("No responses found for this focus group")

        # Pobieramy persony, aby mieć kontekst demograficzny
        persona_ids = list(set(str(r.persona_id) for r in responses))
        result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = {str(p.id): p for p in result.scalars().all()}

        # Przygotowujemy dane dyskusji w ustrukturyzowanej formie
        discussion_data = prepare_discussion_data(
            focus_group, responses, personas, include_demographics
        )

        # Wykryj język z treści dyskusji (questions + first responses)
        # Bierzemy pierwsze 1500 znaków dla language detection (optymalizacja)
        all_text = ""

        # Dodaj pytania (z focus_group.questions)
        for question in focus_group.questions:
            all_text += question + " "

        # Dodaj pierwsze odpowiedzi (z responses)
        for response in responses[:10]:  # Pierwsze 10 odpowiedzi
            all_text += response.response_text + " "

        # Weź pierwsze 1500 znaków dla language detection
        sample_text = all_text[:1500]
        # TODO: Implement language detection - temporarily using Polish default
        # Previously used: detect_input_language(sample_text) from nlp module
        detected_language = "pl"

        target_language = detected_language
        if preferred_language and preferred_language in {"pl", "en"}:
            target_language = preferred_language

        logger.info(
            "Language selection for focus group %s: detected='%s', preferred='%s', target='%s' (sample_length=%s chars)",
            focus_group_id,
            detected_language,
            preferred_language,
            target_language,
            len(sample_text),
        )

        # Budujemy zmienne do promptu (z YAML)
        prompt_variables = prepare_prompt_variables(
            discussion_data,
            include_recommendations,
            language=target_language,
        )

        # Renderujemy prompt z config/prompts/focus_groups/discussion_summary.yaml
        from config import prompts
        summary_prompt_template = prompts.get("focus_groups.discussion_summary")
        rendered_messages = summary_prompt_template.render(**prompt_variables)

        # Call LLM (returns AIMessage with metadata)
        ai_message = await self.llm.ainvoke(rendered_messages)

        # Extract string content from AIMessage
        ai_response = self.str_parser.invoke(ai_message)

        # Log token usage for monitoring and budget tracking
        if user_id:
            try:
                # Extract usage metadata from AIMessage response_metadata
                usage_metadata = getattr(ai_message, 'response_metadata', {}).get('usage_metadata')
                if not usage_metadata:
                    # Fallback: check if metadata is at top level
                    usage_metadata = getattr(ai_message, 'response_metadata', {})

                await log_usage_from_metadata(
                    UsageLogContext(
                        user_id=user_id,
                        project_id=focus_group.project_id,
                        operation_type="focus_group_summary",
                        operation_id=focus_group.id,
                        model_name=self.llm.model,
                    ),
                    usage_metadata,
                )
            except Exception as e:
                # Don't fail summary generation if usage logging fails
                logger.warning(f"Failed to log token usage: {e}")

        # Przetwarzamy odpowiedź modelu do struktury słownika
        parsed_summary = self._parse_ai_response(ai_response)

        # Dodajemy metadane techniczne
        parsed_summary["metadata"] = {
            "focus_group_id": focus_group_id,
            "focus_group_name": focus_group.name,
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": self.llm.model,
            "total_responses": len(responses),
            "total_participants": len(persona_ids),
            "questions_asked": len(focus_group.questions),
            "language": target_language,
        }

        # Przypisujemy podsumowanie do obiektu grupy (commit wykona wywołujący)
        focus_group.ai_summary = parsed_summary

        # Persist insights to InsightEvidence table
        # Zbuduj prompt_text dla celów auditowych (serializacja zmiennych promptu)
        prompt_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in rendered_messages
        ])
        created_insights = await store_insights_from_summary(
            db=db,
            focus_group=focus_group,
            parsed_summary=parsed_summary,
            prompt_text=prompt_text,
            model_name=self.llm.model,
        )

        # Invalidate dashboard cache if insights were created
        if created_insights and user_id:
            try:
                await invalidate_dashboard_cache(user_id)
                logger.debug(f"Dashboard cache invalidated after creating {len(created_insights)} insights")
            except Exception as e:
                logger.warning(f"Failed to invalidate dashboard cache: {e}")

        return parsed_summary

    def _parse_ai_response(self, ai_response: str) -> dict[str, Any]:
        """
        Przetwarza odpowiedź AI na ustrukturyzowaną postać
        Obsługuje sekcje w formacie Markdown i wydobywa kluczowe elementy
        """
        sections = {
            "executive_summary": "",
            "key_insights": [],
            "surprising_findings": [],
            "segment_analysis": {},
            "recommendations": [],
            "sentiment_narrative": "",
            "full_analysis": ai_response,  # Zachowujemy pełny tekst dla wglądu
        }

        current_section = None
        current_content = []

        lines = ai_response.split("\n")

        for line in lines:
            line_lower = line.lower().strip()

            # Wykrywamy nagłówki sekcji
            if "executive summary" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "executive_summary"
                current_content = []
            elif "key insights" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "key_insights"
                current_content = []
            elif "surprising findings" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "surprising_findings"
                current_content = []
            elif "segment analysis" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "segment_analysis"
                current_content = []
            elif "recommendation" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "recommendations"
                current_content = []
            elif "sentiment narrative" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "sentiment_narrative"
                current_content = []
            else:
                if current_section and line.strip():
                    current_content.append(line)

        # Zapisujemy ostatnią sekcję
        if current_section:
            self._finalize_section(sections, current_section, current_content)

        return sections

    def _finalize_section(
        self, sections: dict[str, Any], section_name: str, content: list[str]
    ):
        """Finalize a parsed section"""
        content_text = "\n".join(content).strip()

        if section_name in ["executive_summary", "sentiment_narrative"]:
            sections[section_name] = content_text
        elif section_name in ["key_insights", "surprising_findings", "recommendations"]:
            # Wyodrębniamy wypunktowania
            bullets = []
            for line in content:
                stripped = line.strip()
                if stripped.startswith(("-", "*", "•")) or (stripped and stripped[0].isdigit()):
                    bullet_text = _BULLET_PREFIX_RE.sub("", stripped)
                    if bullet_text:
                        bullets.append(bullet_text)
            sections[section_name] = bullets
        elif section_name == "segment_analysis":
            # Parsujemy analizę segmentów (pary klucz-wartość)
            segments = {}
            current_segment = None
            for line in content:
                stripped = line.strip()
                match = _SEGMENT_LINE_RE.search(stripped)
                if match:
                    current_segment = match.group(1).strip()
                    segments[current_segment] = match.group(2).strip()
                elif current_segment and stripped:
                    segments[current_segment] += " " + stripped
            sections[section_name] = segments
