"""
Product Assistant Service - Lightweight AI Helper

Odpowiada na pytania użytkowników o platformę Sight, pomaga w nawigacji,
wyjaśnia funkcje. NIE WYKONUJE żadnych akcji.

Stateless - historia konwersacji przechowywana tylko w frontend (in-memory).
Używa Gemini Flash dla szybkich odpowiedzi.

Sugestie follow-up pytań są generowane przez LLM (kontekstowe, inteligentne).
"""

import logging
import json
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import models, prompts
from app.services.shared.clients import build_chat_model
from app.models.project import Project
from app.models.persona import Persona
from app.models.focus_group import FocusGroup
from app.models.survey import Survey

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Service dla Product Assistant AI.

    Responsibilities:
    - Odpowiadanie na pytania o platformę Sight
    - Pobieranie kontekstu użytkownika (projekty, persony, focus groups)
    - Budowanie promptu z wiedzą o produkcie
    - Generowanie inteligentnych sugestii follow-up pytań przez LLM
    - NIE zapisuje historii (stateless poza single session w frontend)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # Load LLM model (Gemini Flash)
        model_config = models.get("assistant", "chat")
        self.llm = build_chat_model(**model_config.params)

        # Load system prompt
        self.system_prompt_template = prompts.get("assistant.system")

    async def chat(
        self,
        user_id: UUID,
        message: str,
        conversation_history: List[Dict[str, str]],
        include_user_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Przetwarza pytanie użytkownika i zwraca odpowiedź asystenta.

        Args:
            user_id: UUID użytkownika
            message: Pytanie użytkownika
            conversation_history: Historia konwersacji (in-memory z frontendu)
            include_user_context: Czy dołączyć dane użytkownika

        Returns:
            Dict z odpowiedzią asystenta i sugestiami:
            {
                "message": "Odpowiedź asystenta...",
                "suggestions": ["Pytanie 1?", "Pytanie 2?", "Pytanie 3?"]
            }
        """
        logger.info(f"Assistant chat request from user {user_id}")

        # 1. Zbierz kontekst użytkownika (jeśli requested)
        user_context = ""
        if include_user_context:
            user_context = await self._gather_user_context(user_id)

        # 2. Zbuduj system prompt z wiedzą o produkcie
        system_prompt = self.system_prompt_template.render(
            user_context=user_context,
        )

        # 3. Zbuduj messages dla LLM
        messages = [SystemMessage(content=system_prompt)]

        # Dodaj historię konwersacji (max 10 ostatnich wymian)
        for msg in conversation_history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Dodaj aktualne pytanie z instrukcją do generowania sugestii
        user_prompt = f"""{message}

WAŻNE: Po odpowiedzi na pytanie, wygeneruj 2-3 sugestie follow-up pytań, które użytkownik może zadać. Sugestie powinny być:
- Kontekstowe (związane z tematem rozmowy)
- Praktyczne (pomagające użytkownikowi osiągnąć cel)
- Krótkie (max 10 słów każda)

Zwróć odpowiedź w formacie JSON:
{{
  "answer": "Twoja odpowiedź na pytanie...",
  "suggestions": ["Pytanie 1?", "Pytanie 2?", "Pytanie 3?"]
}}"""

        messages.append(HumanMessage(content=user_prompt))

        # 4. Wywołaj LLM
        try:
            response = await self.llm.ainvoke(messages)
            response_content = response.content

            # Spróbuj sparsować JSON z sugestiami
            try:
                # Jeśli response to JSON, parsuj
                parsed = json.loads(response_content)
                answer = parsed.get("answer", response_content)
                suggestions = parsed.get("suggestions", [])
            except json.JSONDecodeError:
                # Jeśli nie JSON, użyj całej odpowiedzi jako answer
                # i spróbuj wyekstrahować sugestie z tekstu
                answer = response_content
                suggestions = self._extract_suggestions_from_text(response_content)

        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            # Fallback response
            answer = "Przepraszam, wystąpił problem z przetwarzaniem Twojego pytania. Spróbuj ponownie za chwilę."
            suggestions = [
                "Jak utworzyć nowy projekt?",
                "Jak wygenerować persony?",
                "Co to są grupy fokusowe?"
            ]

        # 5. Zwróć odpowiedź
        return {
            "message": answer,
            "suggestions": suggestions[:3],  # Max 3 sugestie
        }

    async def _gather_user_context(self, user_id: UUID) -> str:
        """
        Zbiera kontekst użytkownika: projekty, persony, focus groups, surveys.

        Returns:
            String z podsumowaniem danych użytkownika
        """
        context_parts = []

        # Projekty
        projects_stmt = select(Project).where(
            Project.user_id == user_id,
            Project.deleted_at.is_(None),
        )
        projects_result = await self.db.execute(projects_stmt)
        projects = projects_result.scalars().all()

        if projects:
            project_names = [p.name for p in projects[:5]]  # Max 5
            context_parts.append(
                f"Użytkownik ma {len(projects)} projekt(ów): {', '.join(project_names)}"
            )
        else:
            context_parts.append("Użytkownik nie ma jeszcze projektów")

        # Persony (dla aktywnych projektów)
        if projects:
            project_ids = [p.id for p in projects]
            personas_stmt = select(Persona).where(Persona.project_id.in_(project_ids))
            personas_result = await self.db.execute(personas_stmt)
            personas = personas_result.scalars().all()

            if personas:
                context_parts.append(f"Użytkownik wygenerował łącznie {len(personas)} person")

        # Focus Groups
        focus_groups_stmt = select(FocusGroup).where(
            FocusGroup.user_id == user_id,
            FocusGroup.deleted_at.is_(None),
        )
        fg_result = await self.db.execute(focus_groups_stmt)
        focus_groups = fg_result.scalars().all()

        if focus_groups:
            context_parts.append(f"Użytkownik utworzył {len(focus_groups)} grup(y) fokusowych")

        # Surveys
        surveys_stmt = select(Survey).where(
            Survey.user_id == user_id,
            Survey.deleted_at.is_(None),
        )
        surveys_result = await self.db.execute(surveys_stmt)
        surveys = surveys_result.scalars().all()

        if surveys:
            context_parts.append(f"Użytkownik utworzył {len(surveys)} ankiet(y)")

        return "\n".join(context_parts) if context_parts else "Użytkownik dopiero zaczyna korzystać z platformy"

    def _extract_suggestions_from_text(self, text: str) -> List[str]:
        """
        Ekstrahuje sugestie z tekstu jeśli LLM nie zwrócił JSON.

        Szuka linii zaczynających się od "- " lub numerów, które wyglądają jak pytania.

        Args:
            text: Tekst odpowiedzi LLM

        Returns:
            Lista sugestii (może być pusta)
        """
        suggestions = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # Szukaj linii zaczynających się od "- " lub "1. " itp.
            if line.startswith("- ") or (len(line) > 2 and line[0].isdigit() and line[1] in ['.', ')']):
                # Usuń prefix
                if line.startswith("- "):
                    suggestion = line[2:].strip()
                else:
                    # Usuń numer (np. "1. ")
                    suggestion = line.split(None, 1)[-1].strip()

                # Sprawdź czy wygląda jak pytanie (kończy się "?")
                if suggestion.endswith("?"):
                    suggestions.append(suggestion)

                if len(suggestions) >= 3:
                    break

        # Fallback jeśli nie znaleziono sugestii w tekście
        if not suggestions:
            suggestions = [
                "Jakie są główne funkcje platformy?",
                "Jak rozpocząć swoje pierwsze badanie?",
                "Gdzie mogę znaleźć pomoc?"
            ]

        return suggestions
