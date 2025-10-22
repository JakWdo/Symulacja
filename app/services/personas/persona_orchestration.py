"""Serwis orkiestracji generowania person używający Gemini 2.5 Pro.

Ten moduł zawiera `PersonaOrchestrationService`, który wykorzystuje Gemini 2.5 Pro
do przeprowadzenia głębokiej analizy Graph RAG i tworzenia szczegółowych briefów
(900-1200 znaków) dla każdej grupy demograficznej person.

Filozofia:
- Orchestration Agent (Gemini 2.5 Pro) = complex reasoning, długie analizy
- Individual Generators (Gemini 2.5 Flash) = szybkie generowanie konkretnych person
- Output style: Edukacyjny - wyjaśnia "dlaczego", konwersacyjny ton
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG
from app.services.shared.clients import build_chat_model
from app.core.prompts.persona_prompts import (
    ORCHESTRATION_PROMPT_TEMPLATE,
    SEGMENT_NAME_PROMPT_TEMPLATE,
    SEGMENT_CONTEXT_PROMPT_TEMPLATE,
)

settings = get_settings()
logger = logging.getLogger(__name__)


class GraphInsight(BaseModel):
    """Pojedynczy insight z grafu wiedzy (Wskaznik, Obserwacja, Trend).

    UWAGA: Ten schema używa ANGIELSKICH property names dla API consistency.
    Dane w grafie Neo4j używają POLSKICH nazw (streszczenie, skala, pewnosc, etc.).

    Konwersja wykonywana przez funkcję _map_graph_node_to_insight():
    - streszczenie -> summary
    - skala -> magnitude
    - pewnosc -> confidence ("wysoka"->"high", "srednia"->"medium", "niska"->"low")
    - okres_czasu -> time_period
    - kluczowe_fakty -> why_matters (z dodatkowym edukacyjnym kontekstem)
    """

    type: str = Field(description="Typ węzła (Wskaznik, Obserwacja, Trend, etc.)")
    summary: str = Field(description="Jednozdaniowe podsumowanie")
    magnitude: str | None = Field(default=None, description="Wartość liczbowa jeśli istnieje (np. '78.4%')")
    confidence: str = Field(default="medium", description="Poziom pewności: high, medium, low")
    time_period: str | None = Field(default=None, description="Okres czasu (np. '2022')")
    source: str | None = Field(default=None, description="Źródło danych (np. 'GUS', 'CBOS')")
    why_matters: str = Field(description="Edukacyjne wyjaśnienie dlaczego to ważne dla person")


class DemographicGroup(BaseModel):
    """Grupa demograficzna z briefem i insightami."""

    count: int = Field(description="Liczba person do wygenerowania w tej grupie")
    demographics: dict[str, Any] = Field(description="Cechy demograficzne (age, gender, education, etc.)")
    brief: str = Field(description="Długi (900-1200 znaków) edukacyjny brief dla generatorów")
    graph_insights: list[GraphInsight] = Field(default_factory=list, description="Insighty z Graph RAG")
    allocation_reasoning: str = Field(description="Dlaczego tyle person w tej grupie")
    segment_characteristics: list[str] = Field(default_factory=list, description="4-6 kluczowych cech tego segmentu (np. 'Profesjonaliści z wielkich miast')")


class PersonaAllocationPlan(BaseModel):
    """Plan alokacji person z szczegółowymi briefami dla każdej grupy."""

    total_personas: int = Field(description="Całkowita liczba person do wygenerowania")
    groups: list[DemographicGroup] = Field(description="Grupy demograficzne z briefami")
    overall_context: str = Field(description="Ogólny kontekst społeczny Polski z Graph RAG")


class PersonaOrchestrationService:
    """Serwis orkiestracji używający Gemini 2.5 Pro do tworzenia briefów.

    Ten serwis:
    1. Pobiera comprehensive Graph RAG context (Wskazniki, Grupy_Demograficzne, Trendy)
    2. Przeprowadza głęboką socjologiczną analizę używając Gemini 2.5 Pro
    3. Tworzy szczegółowe briefe (900-1200 znaków) dla każdej grupy person
    4. Wyjaśnia "dlaczego" (edukacyjny output style) dla wszystkich decyzji

    Output style: Konwersacyjny, edukacyjny, wyjaśniający, production-ready.
    """

    def __init__(self) -> None:
        """Inicjalizuje orchestration agent (Gemini 2.5 Pro) i RAG service."""

        # Gemini 2.5 Pro dla complex reasoning i długich analiz
        self.llm = build_chat_model(
            model="gemini-2.5-pro",
            temperature=0.3,  # Niższa dla analytical tasks
            max_tokens=8000,  # Wystarczająco na pełny plan + briefy
            timeout=120,  # 2 minuty dla complex reasoning
        )

        # RAG service dla hybrid search kontekstu
        self.rag_service = PolishSocietyRAG()

        logger.info("PersonaOrchestrationService zainicjalizowany (Gemini 2.5 Pro)")

    async def create_persona_allocation_plan(
        self,
        num_personas: int,
        project_description: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> PersonaAllocationPlan:
        """Tworzy szczegółowy plan alokacji person z długimi briefami.

        Gemini 2.5 Pro przeprowadza głęboką analizę:
        1. Pobiera Graph RAG context (ogólne trendy społeczne Polski)
        2. Analizuje trendy społeczne i wskaźniki statystyczne
        3. Tworzy spójne (900-1200 znaków) edukacyjne briefe
        4. Wyjaśnia "dlaczego" dla każdej decyzji alokacyjnej
        5. Generuje segmenty bazując WYŁĄCZNIE na project_description + RAG + LLM reasoning

        Args:
            num_personas: Całkowita liczba person do wygenerowania
            project_description: Opis projektu badawczego
            additional_context: Dodatkowy kontekst od użytkownika (z AI Wizard)

        Returns:
            PersonaAllocationPlan z grupami demograficznymi i szczegółowymi briefami

        Raises:
            Exception: Jeśli LLM nie może wygenerować planu lub JSON parsing fails
        """
        logger.info(f"[TARGET] Orchestration: Tworzenie planu alokacji dla {num_personas} person...")

        # Krok 1: Pobierz comprehensive Graph RAG context (ogólne trendy Polski)
        graph_context = await self._get_comprehensive_graph_context()
        logger.info(f"[CHART] Pobrano {len(graph_context)} fragmentów z Graph RAG")

        # Krok 2: Zbuduj prompt w stylu edukacyjnym
        prompt = self._build_orchestration_prompt(
            num_personas=num_personas,
            graph_context=graph_context,
            project_description=project_description,
            additional_context=additional_context,
        )

        # Krok 3: Gemini 2.5 Pro generuje plan (długa analiza)
        try:
            logger.info(f"🤖 Wywołuję Gemini 2.5 Pro dla orchestration (max_tokens=8000, timeout=120s)...")
            response = await self.llm.ainvoke(prompt)

            # DEBUG: Log surowej odpowiedzi od Gemini
            response_text = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[NOTE] Gemini response length: {len(response_text)} chars")
            logger.info(f"[NOTE] Gemini response preview (first 500 chars): {response_text[:500]}")
            logger.info(f"[NOTE] Gemini response preview (last 500 chars): {response_text[-500:]}")

            plan_json = self._extract_json_from_response(response_text)

            # DEBUG: Log sparsowanego JSON
            logger.info(f"[OK] JSON parsed successfully: {len(plan_json)} top-level keys")
            logger.info(f"[OK] JSON keys: {list(plan_json.keys())}")

            # Parse do Pydantic model (walidacja)
            plan = PersonaAllocationPlan(**plan_json)

            logger.info(f"[OK] Plan alokacji utworzony: {len(plan.groups)} grup demograficznych")
            return plan

        except Exception as e:
            logger.error(f"[X] Błąd podczas tworzenia planu alokacji: {e}")
            logger.error(f"[X] Exception type: {type(e).__name__}")
            logger.error(f"[X] Exception details: {str(e)[:1000]}")
            raise

    async def _get_comprehensive_graph_context(self) -> str:
        """Pobiera comprehensive Graph RAG context o polskim społeczeństwie.

        Hybrid search (vector + keyword + RRF) dla ogólnych trendów społecznych Polski:
        - Demografia i statystyki GUS
        - Zatrudnienie i płace
        - Koszty życia i mieszkań
        - Work-life balance i wartości

        Returns:
            Sformatowany string z Graph RAG context (Wskazniki, Obserwacje, Trendy)
        """
        # Ogólne queries o polskim społeczeństwie (bez specyfikacji demograficznych)
        # LLM sam zdecyduje jakie segmenty wygenerować based on project_description + ten kontekst
        queries = [
            "Polish society trends 2023 2024 demographics",
            "workforce statistics Poland employment rates",
            "income housing costs Poland urban areas",
            "work-life balance trends Poland young professionals",
            "education levels Poland university graduates statistics",
            "age demographics Poland population structure",
            "gender equality Poland workplace statistics",
            "urban rural Poland differences demographics",
        ]

        # Wykonaj parallel hybrid searches z timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[
                    self.rag_service.hybrid_search(query=q, top_k=3)
                    for q in queries[:8]  # Limit do 8 queries (24 results max)
                ]),
                timeout=30.0  # 30 sekund dla wszystkich queries
            )
        except asyncio.TimeoutError:
            logger.warning("[!] Graph RAG queries przekroczyły timeout (30s) - zwracam pusty kontekst")
            return "Brak dostępnego kontekstu z Graph RAG (timeout)."

        # Deduplikuj i formatuj
        all_docs = []
        seen_texts = set()
        for docs_list in results:
            for doc in docs_list:
                if doc.page_content not in seen_texts:
                    all_docs.append(doc)
                    seen_texts.add(doc.page_content)

        # Formatuj jako czytelny context
        formatted_context = self._format_graph_context(all_docs[:15])  # Top 15 unique
        return formatted_context

    def _format_graph_context(self, documents: List[Any]) -> str:
        """Formatuje Graph RAG documents jako czytelny context dla LLM.

        Args:
            documents: Lista Document objects z Graph RAG

        Returns:
            Sformatowany string z numbered entries
        """
        if not documents:
            return "Brak dostępnego kontekstu z Graph RAG."

        formatted = "=== KONTEKST Z GRAPH RAG (Raporty o polskim społeczeństwie) ===\n\n"

        for idx, doc in enumerate(documents, 1):
            formatted += f"[{idx}] {doc.page_content}\n"

            # Dodaj metadata jeśli istnieje
            if hasattr(doc, 'metadata') and doc.metadata:
                meta = doc.metadata
                if 'source' in meta:
                    formatted += f"    Źródło: {meta['source']}\n"
                if 'document_title' in meta:
                    formatted += f"    Tytuł: {meta['document_title']}\n"

            formatted += "\n"

        return formatted

    def _build_orchestration_prompt(
        self,
        num_personas: int,
        graph_context: str,
        project_description: str | None,
        additional_context: str | None,
    ) -> str:
        """Buduje prompt w stylu edukacyjnym dla Gemini 2.5 Pro.

        Używa ORCHESTRATION_PROMPT_TEMPLATE z app.core.prompts.persona_prompts.

        Args:
            num_personas: Liczba person
            graph_context: Kontekst z Graph RAG
            project_description: Opis projektu
            additional_context: Dodatkowy kontekst od użytkownika

        Returns:
            Sformatowany prompt string z template
        """
        return ORCHESTRATION_PROMPT_TEMPLATE.format(
            num_personas=num_personas,
            project_description=project_description or "Badanie person syntetycznych",
            additional_context=additional_context or "Brak dodatkowego kontekstu",
            graph_context=graph_context,
        )

    def _extract_json_from_response(self, response_text: str) -> dict[str, Any]:
        """Ekstraktuje JSON z odpowiedzi LLM (może być otoczony markdown lub preambułą).

        Args:
            response_text: Surowa odpowiedź od LLM

        Returns:
            Parsed JSON jako dict

        Raises:
            ValueError: Jeśli nie można sparsować JSON
        """
        text = response_text.strip()

        # Strategia 1: Znajdź blok ```json ... ``` (może być w środku tekstu)
        import re
        json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_block_match:
            json_text = json_block_match.group(1).strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"[X] Nie można sparsować JSON z bloku markdown: {e}")
                logger.error(f"JSON block text: {json_text[:500]}...")
                # Kontynuuj do następnej strategii

        # Strategia 2: Znajdź blok ``` ... ``` (bez json)
        code_block_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if code_block_match:
            json_text = code_block_match.group(1).strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"[X] Nie można sparsować JSON z bloku kodu: {e}")
                # Kontynuuj do następnej strategii

        # Strategia 3: Znajdź pierwszy { ... } (może być po preambule)
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            json_text = brace_match.group(0).strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"[X] Nie można sparsować JSON z braces: {e}")
                logger.error(f"Braces text: {json_text[:500]}...")

        # Strategia 4: Spróbuj sparsować cały tekst (fallback)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"[X] Nie można sparsować JSON (all strategies failed): {e}")
            logger.error(f"[X] Response text length: {len(text)} chars")
            logger.error(f"[X] Response text (first 1000 chars): {text[:1000]}")
            logger.error(f"[X] Response text (last 1000 chars): {text[-1000:]}")
            raise ValueError(f"LLM nie zwrócił poprawnego JSON: {e}")

    # === NEW METHODS FOR SEGMENT-BASED ARCHITECTURE ===

    async def _generate_segment_name(
        self,
        demographics: dict[str, Any],
        graph_insights: list[GraphInsight],
        rag_citations: list[Any]
    ) -> str:
        """Generuje mówiącą nazwę segmentu używając Gemini 2.5 Flash.

        Nazwa powinna być krótka (2-4 słowa), mówiąca i odzwierciedlać
        kluczowe cechy grupy demograficznej bazując na insightach.

        Args:
            demographics: Cechy demograficzne (age, gender, education, income)
            graph_insights: Graph insights dla tej grupy
            rag_citations: RAG citations dla kontekstu

        Returns:
            Nazwa segmentu (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")

        Raises:
            ValueError: Jeśli LLM nie zwróci poprawnej nazwy
        """
        # Extract key demographics
        age_range = demographics.get('age', demographics.get('age_group', 'nieznany'))
        gender = demographics.get('gender', 'nieznana')
        education = demographics.get('education', demographics.get('education_level', 'nieznane'))
        income = demographics.get('income', demographics.get('income_bracket', 'nieznany'))

        # Format insights
        insights_text = "\n".join(
            [f"- {ins.summary} ({ins.confidence})" for ins in graph_insights[:3]]
        ) if graph_insights else "Brak insights"

        # Format citations (first 2 max)
        citations_text = "\n".join(
            [f"- {cit.page_content[:100]}..." for cit in (rag_citations or [])[:2]]
        ) if hasattr((rag_citations or [None])[0], 'page_content') else "Brak cytatów"

        prompt = SEGMENT_NAME_PROMPT_TEMPLATE.format(
            age_range=age_range,
            gender=gender,
            education=education,
            income=income,
            insights_text=insights_text,
            citations_text=citations_text,
        )

        try:
            # Use Gemini Flash for quick naming (cheap, fast)
            llm_flash = build_chat_model(
                model="gemini-2.0-flash-exp",
                temperature=0.7,
                max_tokens=50,
                timeout=10,
            )

            response = await llm_flash.ainvoke(prompt)
            segment_name = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # Clean up (remove quotes if present)
            segment_name = segment_name.strip('"\'')

            # Validation: nazwa powinna mieć 5-60 znaków
            if len(segment_name) < 5 or len(segment_name) > 60:
                logger.warning(f"Generated segment name too short/long: '{segment_name}', using fallback")
                # Fallback: template name
                segment_name = f"Segment {age_range}, {gender}"

            logger.info(f"[OK] Generated segment name: '{segment_name}'")
            return segment_name

        except Exception as e:
            logger.error(f"[X] Failed to generate segment name: {e}")
            # Fallback: template name
            fallback_name = f"Segment {age_range}, {gender}"
            logger.warning(f"Using fallback segment name: '{fallback_name}'")
            return fallback_name

    async def _generate_segment_context(
        self,
        segment_name: str,
        demographics: dict[str, Any],
        graph_insights: list[GraphInsight],
        rag_citations: list[Any],
        project_goal: str | None = None
    ) -> str:
        """Generuje kontekst społeczny dla segmentu używając Gemini 2.5 Pro.

        Kontekst powinien być 500-800 znaków, edukacyjny i specyficzny dla TEJ grupy.

        Args:
            segment_name: Nazwa segmentu
            demographics: Cechy demograficzne
            graph_insights: Graph insights dla tej grupy
            rag_citations: RAG citations dla kontekstu
            project_goal: Cel projektu (opcjonalny)

        Returns:
            Kontekst społeczny (500-800 znaków)

        Raises:
            ValueError: Jeśli LLM nie zwróci poprawnego kontekstu
        """
        # Extract key demographics
        age_range = demographics.get('age', demographics.get('age_group', 'nieznany'))
        gender = demographics.get('gender', 'nieznana')
        education = demographics.get('education', demographics.get('education_level', 'nieznane'))
        income = demographics.get('income', demographics.get('income_bracket', 'nieznany'))

        # Format insights (concise for template)
        insights_text = "\n".join(
            [f"- {ins.summary} (mag: {ins.magnitude or 'N/A'}, conf: {ins.confidence})" for ins in graph_insights[:5]]
        ) if graph_insights else "Brak insights"

        # Format citations (first 3 max)
        citations_text = "\n".join(
            [f"[{idx+1}] {cit.page_content[:200]}..." for idx, cit in enumerate((rag_citations or [])[:3])]
        ) if hasattr((rag_citations or [None])[0], 'page_content') else "Brak cytatów"

        prompt = SEGMENT_CONTEXT_PROMPT_TEMPLATE.format(
            segment_name=segment_name,
            age_range=age_range,
            gender=gender,
            education=education,
            income=income,
            insights_text=insights_text,
            citations_text=citations_text,
            project_goal=project_goal or "Badanie syntetycznych person",
        )

        try:
            response = await self.llm.ainvoke(prompt)  # Use Gemini 2.5 Pro
            segment_context = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # Validation: kontekst powinien mieć 400-1200 znaków
            if len(segment_context) < 400 or len(segment_context) > 1200:
                logger.warning(
                    f"Generated segment context length ({len(segment_context)}) outside range 400-1200, "
                    "but accepting anyway"
                )

            logger.info(f"[OK] Generated segment context: {len(segment_context)} chars")
            return segment_context

        except Exception as e:
            logger.error(f"[X] Failed to generate segment context: {e}")
            # Fallback: minimal context
            fallback_context = (
                f"Segment '{segment_name}' obejmuje osoby w wieku {age_range}, {gender}, "
                f"z wykształceniem {education} i dochodami {income}. "
                f"Ta grupa stanowi istotną część polskiego społeczeństwa i wymaga szczególnej uwagi "
                f"w kontekście badań rynkowych."
            )
            logger.warning(f"Using fallback segment context: {len(fallback_context)} chars")
            return fallback_context

    def _filter_graph_insights_for_segment(
        self,
        insights: list[GraphInsight],
        demographics: dict[str, Any]
    ) -> list[GraphInsight]:
        """Filtruje graph insights dla konkretnego segmentu demograficznego.

        Zwraca tylko insights relevantne dla tego segmentu (np. insights o młodych
        dla segmentu 18-24).

        Args:
            insights: Wszystkie graph insights
            demographics: Demografia segmentu

        Returns:
            Filtrowana lista insights (max 10)
        """
        if not insights:
            return []

        # Extract age range for filtering
        age_str = demographics.get('age', demographics.get('age_group', ''))

        filtered = []
        for insight in insights:
            # Filter by age relevance (check if age range mentioned in summary)
            age_relevant = True
            if age_str:
                # Simple heuristic: if insight mentions age, check if it's relevant
                summary_lower = insight.summary.lower()
                if any(age_term in summary_lower for age_term in ['wiek', 'lat', 'young', 'old', 'młod', 'star']):
                    # Check if age range overlaps (simplified)
                    age_relevant = age_str.lower() in summary_lower or not any(
                        other_age in summary_lower
                        for other_age in ['18-24', '25-34', '35-44', '45-54', '55+']
                        if other_age != age_str
                    )

            if age_relevant:
                filtered.append(insight)

        # Sort by confidence (high first) and return top 10
        confidence_order = {'high': 3, 'medium': 2, 'low': 1}
        filtered.sort(key=lambda x: confidence_order.get(x.confidence, 0), reverse=True)

        return filtered[:10]

    def _filter_rag_citations(
        self,
        citations: list[Any],
        min_confidence: float = 0.7
    ) -> list[Any]:
        """Filtruje RAG citations - tylko high-quality (confidence > threshold).

        Args:
            citations: Lista RAG citations (Document objects)
            min_confidence: Minimalny confidence score (default 0.7)

        Returns:
            Filtrowana lista citations (max 10)
        """
        if not citations:
            return []

        filtered = []
        for cit in citations:
            # Check if citation has confidence score in metadata
            confidence = 1.0  # Default if not available
            if hasattr(cit, 'metadata') and cit.metadata:
                confidence = cit.metadata.get('confidence', cit.metadata.get('score', 1.0))

            # Filter by confidence
            if confidence >= min_confidence:
                filtered.append(cit)

        # Return top 10
        return filtered[:10]
