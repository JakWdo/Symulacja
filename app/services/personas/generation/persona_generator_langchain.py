"""
Generator Person oparty na LangChain i Google Gemini

Ten moduł generuje realistyczne, statystycznie reprezentatywne persony
dla badań rynkowych przy użyciu Google Gemini przez framework LangChain.

Kluczowe funkcjonalności:
- Generowanie person zgodnie z zadanymi rozkładami demograficznymi
- Walidacja statystyczna przy użyciu testu chi-kwadrat
- Sampling cech osobowości (Big Five) i wymiarów kulturowych (Hofstede)
- Integracja z LangChain dla łatwej zmiany modelu LLM

UWAGA: Od refactoringu (2025-11) większość logiki pomocniczej przeniesiono do modułów:
- demographic_sampling.py - próbkowanie demografii
- psychological_profiles.py - Big Five + Hofstede
- prompt_templates.py - prompty dla LLM
- statistical_validation.py - testy chi-kwadrat
- rag_integration.py - RAG context fetching
"""

import logging
import re
import numpy as np
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config import models, features, demographics
from app.services.shared.clients import build_chat_model
from app.services.dashboard.usage_logging import (
    UsageLogContext,
    context_with_model,
    schedule_usage_logging,
)

# Import z nowych modułów pomocniczych
from .demographic_sampling import (
    DemographicDistribution,
    sample_demographic_profile,
)
from .psychological_profiles import (
    sample_big_five_traits,
    sample_cultural_dimensions,
)
from .prompt_templates import (
    create_persona_prompt,
    create_segment_persona_prompt,
)
from ..validation.statistical_validation import validate_distribution
from .rag_integration import get_rag_context_for_persona


# Import RAG service singleton
try:
    from app.services.shared import get_polish_society_rag
    _rag_service_available = True
except ImportError:
    _rag_service_available = False


logger = logging.getLogger(__name__)


class PersonaGeneratorLangChain:
    """
    Generator statystycznie reprezentatywnych person przy użyciu LangChain + Gemini

    Używa Google Gemini do generowania realistycznych profili person na podstawie
    zadanych rozkładów demograficznych i psychologicznych.
    """

    def __init__(self):
        """Inicjalizuj generator z konfiguracją LangChain i Gemini"""
        # RNG dla próbkowania
        self._rng = np.random.default_rng(features.performance.random_seed)

        # Model config z centralnego registry
        model_config = models.get("personas", "generation")
        self.llm = build_chat_model(**model_config.params)

        # Konfigurujemy parser JSON, aby wymusić strukturalną odpowiedź
        self.json_parser = JsonOutputParser()

        # System prompt z centralnego registry
        from config import prompts
        system_prompt_template = prompts.get("personas.persona_generation_system")
        system_message = system_prompt_template.messages[0]["content"]

        # Budujemy szablon promptu do generowania person
        self.persona_prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", "{prompt}")
        ])

        # Składamy łańcuch LangChain (prompt -> LLM -> parser)
        self.persona_chain = (
            self.persona_prompt
            | self.llm
            | self.json_parser
        )

        # Inicjalizuj RAG service (singleton - opcjonalnie, tylko jeśli włączony)
        self.rag_service = None
        if _rag_service_available and features.rag.enabled:
            try:
                self.rag_service = get_polish_society_rag()
                logger.info("RAG service initialized successfully in PersonaGenerator (singleton)")
            except Exception as e:
                logger.warning(f"RAG service unavailable: {e}")

        # In-memory cache dla RAG queries (eliminuje wielokrotne identyczne zapytania)
        # Key: (age_group, education, location, gender) tuple
        # Value: dict z RAG context
        self._rag_cache: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def sample_demographic_profile(
        self, distribution: DemographicDistribution, n_samples: int = 1
    ) -> list[dict[str, Any]]:
        """
        Próbkuj profile demograficzne zgodnie z zadanym rozkładem

        Deleguje do demographic_sampling.sample_demographic_profile()

        Args:
            distribution: Obiekt zawierający rozkłady prawdopodobieństw dla każdej kategorii
            n_samples: Liczba profili do wygenerowania (domyślnie 1)

        Returns:
            Lista słowników, każdy zawiera klucze: age_group, gender, education_level,
            income_bracket, location
        """
        return sample_demographic_profile(distribution, demographics, self._rng, n_samples)

    def sample_big_five_traits(self, personality_skew: dict[str, float] = None) -> dict[str, float]:
        """
        Próbkuj cechy osobowości Big Five z rozkładów normalnych

        Deleguje do psychological_profiles.sample_big_five_traits()

        Args:
            personality_skew: Opcjonalny słownik do przesunięcia rozkładów

        Returns:
            Słownik z wartościami cech w przedziale [0, 1]
        """
        return sample_big_five_traits(self._rng, personality_skew)

    def sample_cultural_dimensions(self) -> dict[str, float]:
        """
        Próbkuj wymiary kulturowe Hofstede

        Deleguje do psychological_profiles.sample_cultural_dimensions()

        Returns:
            Słownik z wartościami wymiarów w przedziale [0, 1]
        """
        return sample_cultural_dimensions(self._rng)

    def validate_distribution(
        self,
        generated_personas: list[dict[str, Any]],
        target_distribution: DemographicDistribution,
    ) -> dict[str, Any]:
        """
        Waliduj czy wygenerowane persony pasują do docelowego rozkładu (test chi-kwadrat)

        Deleguje do statistical_validation.validate_distribution()

        Args:
            generated_personas: Lista wygenerowanych person (jako słowniki)
            target_distribution: Oczekiwany rozkład demograficzny

        Returns:
            Słownik z wynikami testów dla każdej kategorii oraz ogólną oceną
        """
        return validate_distribution(generated_personas, target_distribution)

    def _weighted_sample(self, distribution: dict[str, float]) -> str:
        """
        Losuj element z rozkładu ważonego (weighted sampling)

        Deleguje do demographic_sampling._weighted_sample()
        Wrapper dla backward compatibility z testami.

        Args:
            distribution: Słownik kategoria -> prawdopodobieństwo (suma = 1.0)

        Returns:
            Wylosowana kategoria jako string
        """
        from .demographic_sampling import _weighted_sample
        return _weighted_sample(distribution, self._rng)

    def _sanitize_text(self, text: str, preserve_paragraphs: bool = False) -> str:
        """
        Sanityzuj tekst wygenerowany przez LLM, usuwając nadmierne białe znaki

        Metoda ta usuwa:
        - Nadmiarowe znaki nowej linii (\\n\\n -> pojedyncza spacja lub akapit)
        - Nadmiarowe spacje (wiele spacji -> jedna spacja)
        - Leading/trailing whitespace

        Args:
            text: Tekst do sanityzacji
            preserve_paragraphs: Czy zachować podział na akapity (dla background_story)
                                Jeśli True, zachowuje podział na paragrafy (\\n\\n)
                                Jeśli False, zamienia wszystkie \\n na spacje

        Returns:
            Zsanityzowany tekst bez nadmiarowych białych znaków

        Przykłady:
            >>> _sanitize_text("Zawód\\n\\nJuż")
            "Zawód Już"
            >>> _sanitize_text("Tekst  z   wieloma    spacjami")
            "Tekst z wieloma spacjami"
            >>> _sanitize_text("Para 1\\n\\nPara 2", preserve_paragraphs=True)
            "Para 1\\n\\nPara 2"
        """
        if not text:
            return text

        if preserve_paragraphs:
            # Dla background_story - zachowaj podział na akapity ale znormalizuj każdy akapit
            paragraphs = text.split('\n')
            paragraphs = [re.sub(r'\s+', ' ', p).strip() for p in paragraphs if p.strip()]
            return '\n\n'.join(paragraphs)
        else:
            # Dla pól jednoliniowych - usuń wszystkie \\n i znormalizuj spacje
            return re.sub(r'\s+', ' ', text).strip()

    async def _invoke_persona_llm(
        self,
        prompt_text: str,
        usage_context: UsageLogContext | None = None,
    ) -> str:
        """Invoke the chat model and optionally log token usage."""
        messages = self.persona_prompt.format_messages(prompt=prompt_text)

        result = await self.llm.ainvoke(messages)

        if usage_context:
            usage_meta = None
            if hasattr(result, "response_metadata"):
                meta = result.response_metadata or {}
                if isinstance(meta, dict):
                    usage_meta = meta.get("usage_metadata") or meta.get("token_usage") or meta
            if usage_meta is None and hasattr(result, "additional_kwargs"):
                extras = result.additional_kwargs or {}
                if isinstance(extras, dict):
                    usage_meta = extras.get("usage_metadata") or extras.get("token_usage")

            schedule_usage_logging(
                context_with_model(usage_context, getattr(self.llm, "model", None)),
                usage_meta,
            )

        return self._extract_text_from_result(result)

    def _extract_text_from_result(self, result: Any) -> str:
        """Normalise LangChain AIMessage/content into a plain string."""
        content = getattr(result, "content", result)
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            content = " ".join(part for part in parts if part)
        if not isinstance(content, str):
            content = str(content)
        return content.strip()

    def _parse_persona_response(self, raw_response: str) -> dict[str, Any]:
        """Parse persona JSON output, preserving existing parser behaviour."""
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return self.json_parser.parse(cleaned)

    async def generate_persona_personality(
        self,
        demographic_profile: dict[str, Any],
        psychological_profile: dict[str, Any],
        use_rag: bool = True,
        advanced_options: dict[str, Any] | None = None,
        usage_context: UsageLogContext | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generuj osobowość persony przy użyciu LangChain + Gemini

        Tworzy szczegółowy prompt oparty na profilach demograficznym i psychologicznym,
        opcjonalnie wzbogacony o kontekst RAG z bazy wiedzy o polskim społeczeństwie.

        Args:
            demographic_profile: Słownik z danymi demograficznymi (wiek, płeć, lokalizacja, etc.)
            psychological_profile: Słownik z cechami Big Five i wymiarami Hofstede
            use_rag: Czy użyć kontekstu z bazy wiedzy RAG (default: True)
            advanced_options: Opcjonalne zaawansowane opcje generowania
            usage_context: Kontekst dla logowania użycia

        Returns:
            Krotka (prompt_text, response_dict) gdzie:
            - prompt_text: Pełny tekst wysłany do LLM (do logowania/debugowania)
            - response_dict: Sparsowana odpowiedź JSON z polami persony
                            + pole '_rag_citations' jeśli użyto RAG

        Raises:
            ValueError: Jeśli generowanie się nie powiedzie lub odpowiedź jest niepoprawna
        """

        # Pobierz kontekst RAG jeśli włączony
        rag_context = None
        rag_citations = None
        rag_context_details = None
        if use_rag and self.rag_service:
            rag_data = await get_rag_context_for_persona(
                demographic_profile,
                self.rag_service,
                self._rag_cache
            )
            if rag_data:
                rag_context = rag_data.get('context')
                rag_citations = rag_data.get('citations')

                # Przygotuj rag_context_details dla View Details
                rag_context_details = {
                    "search_type": rag_data.get('search_type', 'unknown'),
                    "num_results": rag_data.get('num_results', 0),
                    "graph_nodes_count": rag_data.get('graph_nodes_count', len(rag_data.get('graph_nodes', []))),
                    "graph_nodes": rag_data.get('graph_nodes', []),
                    "graph_context": rag_data.get('graph_context', ''),
                    "enriched_chunks": rag_data.get('enriched_chunks_count', 0),
                }

                if rag_data.get('query'):
                    rag_context_details["query"] = rag_data.get('query')
                if rag_context:
                    rag_context_details["context_preview"] = rag_context[:1500]
                    rag_context_details["context_length"] = len(rag_context)
                if rag_citations is not None:
                    rag_context_details["citations_count"] = len(rag_citations or [])

                logger.info(
                    f"Using RAG context: {len(rag_context or '')} chars, "
                    f"{len(rag_citations or [])} citations, "
                    f"search_type={rag_context_details['search_type']}"
                )

        # Pobierz target_audience_description i orchestration brief z advanced_options
        target_audience_desc = None
        orchestration_brief = None
        if advanced_options:
            target_audience_desc = advanced_options.get('target_audience_description')
            orchestration_brief = advanced_options.get('orchestration_brief')
            if target_audience_desc:
                logger.info(f"Using target audience description: {target_audience_desc[:100]}...")
            if orchestration_brief:
                logger.info(f"Using orchestration brief: {orchestration_brief[:150]}... ({len(orchestration_brief)} chars)")

        # Generuj prompt (deleguj do prompt_templates)
        prompt_text = create_persona_prompt(
            demographic_profile,
            psychological_profile,
            demographics,
            self._rng,
            rag_context=rag_context,
            target_audience_description=target_audience_desc,
            orchestration_brief=orchestration_brief
        )

        try:
            logger.info(
                f"Generating persona with demographics: {demographic_profile.get('age_group')}, "
                f"{demographic_profile.get('gender')}, {demographic_profile.get('location')}"
                f" | RAG: {'YES' if rag_context else 'NO'}"
            )
            # Wywołaj łańcuch LangChain (prompt -> LLM -> parser JSON)
            raw_response = await self._invoke_persona_llm(prompt_text, usage_context)
            response = self._parse_persona_response(raw_response)

            # Loguj odpowiedź do debugowania
            logger.info(f"LLM response type: {type(response)}, keys: {response.keys() if isinstance(response, dict) else 'N/A'}")

            # Waliduj wymagane pola
            required_fields = ["full_name", "persona_title", "headline", "background_story", "values", "interests"]
            missing_fields = [field for field in required_fields if not response.get(field)]
            if missing_fields:
                logger.error(
                    f"LLM response missing required fields: {missing_fields}. "
                    f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'NOT A DICT'}"
                )

            # Sanityzuj wszystkie pola tekstowe (usuń nadmiarowe \n\n i whitespace)
            # KLUCZOWE: Zapobiega wyświetlaniu "Zawód\n\nJuż" w UI
            text_fields_single = [
                'occupation', 'full_name', 'location', 'headline',
                'persona_title', 'communication_style', 'decision_making_style'
            ]
            for field in text_fields_single:
                if field in response and isinstance(response[field], str):
                    response[field] = self._sanitize_text(response[field], preserve_paragraphs=False)

            # Sanityzuj background_story zachowując podział na akapity
            if 'background_story' in response and isinstance(response['background_story'], str):
                response['background_story'] = self._sanitize_text(response['background_story'], preserve_paragraphs=True)

            # Dodaj RAG citations i details do response (jeśli były używane)
            if rag_citations:
                response['_rag_citations'] = rag_citations
            if rag_context_details:
                response['_rag_context_details'] = rag_context_details

            return prompt_text, response
        except Exception as e:
            logger.error(f"Failed to generate persona: {str(e)[:500]}", exc_info=True)
            # Fallback dla błędów parsowania
            raise ValueError(f"Failed to generate persona: {str(e)}")

    async def generate_persona_from_segment(
        self,
        segment_id: str,
        segment_name: str,
        segment_context: str,
        demographics_constraints: dict[str, Any],
        graph_insights: list[Any] = None,
        rag_citations: list[Any] = None,
        personality_skew: dict[str, float] | None = None,
        usage_context: UsageLogContext | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generuj personę Z WYMUSZENIEM demographics z segmentu.

        KLUCZOWA RÓŻNICA vs generate_persona_personality():
        - Demographics są ENFORCE (nie losowane poza bounds!)
        - Age = random.randint(age_min, age_max)
        - Gender = demographics_constraints.gender (NO randomization!)
        - Education/Income = random.choice z allowed lists

        Args:
            segment_id: ID segmentu
            segment_name: Nazwa segmentu (np. "Młodzi Prekariusze")
            segment_context: Kontekst społeczny segmentu
            demographics_constraints: Dict z keys: age_min, age_max, gender, education_levels, income_brackets, locations
            graph_insights: Insights filtrowane dla segmentu
            rag_citations: High-quality RAG citations
            personality_skew: Opcjonalne przesunięcie Big Five
            usage_context: Kontekst dla logowania użycia

        Returns:
            Tuple (prompt_text, response_dict)
        """

        # ENFORCE DEMOGRAPHICS
        age_min = demographics_constraints.get('age_min', 25)
        age_max = demographics_constraints.get('age_max', 34)
        age = self._rng.integers(age_min, age_max + 1)

        gender = demographics_constraints.get('gender', 'kobieta')
        education_levels = demographics_constraints.get('education_levels', ['wyższe'])
        income_brackets = demographics_constraints.get('income_brackets', ['3000-5000 PLN'])
        locations = demographics_constraints.get('locations') or ['Warszawa']

        education = self._rng.choice(education_levels)
        income = self._rng.choice(income_brackets)
        location = self._rng.choice(locations)

        demographic_profile = {
            "age": age,
            "age_group": f"{age_min}-{age_max}",
            "gender": gender,
            "education_level": education,
            "income_bracket": income,
            "location": location
        }

        logger.info(
            f"🔒 ENFORCED demographics: age={age}, gender={gender}, "
            f"education={education}, income={income}, segment='{segment_name}'"
        )

        # Sample psychological profile
        psychological_profile = {
            **self.sample_big_five_traits(personality_skew),
            **self.sample_cultural_dimensions()
        }

        # Create prompt with segment context (deleguj do prompt_templates)
        prompt_text = create_segment_persona_prompt(
            demographic_profile,
            psychological_profile,
            segment_name,
            segment_context,
            demographics,
            self._rng,
            graph_insights,
            rag_citations
        )

        try:
            raw_response = await self._invoke_persona_llm(prompt_text, usage_context)
            response = self._parse_persona_response(raw_response)

            # ENFORCE demographic fields (override LLM if needed)
            response['age'] = age
            response['gender'] = gender
            response['education_level'] = education
            response['income_bracket'] = income
            response['location'] = location

            # Sanityzuj wszystkie pola tekstowe (usuń nadmiarowe \n\n i whitespace)
            text_fields_single = [
                'occupation', 'full_name', 'location', 'headline',
                'persona_title', 'communication_style', 'decision_making_style'
            ]
            for field in text_fields_single:
                if field in response and isinstance(response[field], str):
                    response[field] = self._sanitize_text(response[field], preserve_paragraphs=False)

            # Sanityzuj background_story zachowując podział na akapity
            if 'background_story' in response and isinstance(response['background_story'], str):
                response['background_story'] = self._sanitize_text(response['background_story'], preserve_paragraphs=True)

            # Add segment tracking
            response['_segment_id'] = segment_id
            response['_segment_name'] = segment_name

            if rag_citations:
                response['_rag_citations'] = rag_citations

            logger.info(f"✅ Persona generated: {response.get('full_name')} (segment='{segment_name}')")
            return prompt_text, response

        except Exception as e:
            logger.error(f"❌ Failed to generate persona from segment: {e}", exc_info=True)
            raise ValueError(f"Failed to generate persona from segment '{segment_name}': {e}")
