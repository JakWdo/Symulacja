"""
Generator Person oparty na LangChain i Google Gemini

Ten moduł generuje realistyczne, statystycznie reprezentatywne persony
dla badań rynkowych przy użyciu Google Gemini przez framework LangChain.

Kluczowe funkcjonalności:
- Generowanie person zgodnie z zadanymi rozkładami demograficznymi
- Walidacja statystyczna przy użyciu testu chi-kwadrat
- Sampling cech osobowości (Big Five) i wymiarów kulturowych (Hofstede)
- Integracja z LangChain dla łatwej zmiany modelu LLM
"""

import re
import numpy as np
from typing import Any
from scipy import stats
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.config import get_settings
from app.core.constants import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    POLISH_LOCATIONS,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
    POLISH_MALE_NAMES,
    POLISH_FEMALE_NAMES,
    POLISH_SURNAMES,
)
from app.services.shared.clients import build_chat_model

settings = get_settings()

# Import RAG service (opcjonalny - tylko jeśli RAG włączony)
try:
    if settings.RAG_ENABLED:
        from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG
        _rag_service_available = True
    else:
        _rag_service_available = False
except ImportError:
    _rag_service_available = False


@dataclass
class DemographicDistribution:
    """
    Rozkład demograficzny populacji docelowej

    Każde pole to słownik mapujący kategorie na prawdopodobieństwa (sumujące się do 1.0)
    Przykład: {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2}
    """
    age_groups: dict[str, float]        # Grupy wiekowe
    genders: dict[str, float]           # Płeć
    education_levels: dict[str, float]  # Poziomy edukacji
    income_brackets: dict[str, float]   # Przedziały dochodowe
    locations: dict[str, float]         # Lokalizacje geograficzne


class PersonaGeneratorLangChain:
    """
    Generator statystycznie reprezentatywnych person przy użyciu LangChain + Gemini

    Używa Google Gemini do generowania realistycznych profili person na podstawie
    zadanych rozkładów demograficznych i psychologicznych.
    """

    def __init__(self):
        """Inicjalizuj generator z konfiguracją LangChain i Gemini"""
        import logging
        logger = logging.getLogger(__name__)

        self.settings = settings
        self._rng = np.random.default_rng(self.settings.RANDOM_SEED)

        # Inicjalizujemy model Gemini z wyższą temperaturą dla większej różnorodności
        persona_model = getattr(settings, "PERSONA_GENERATION_MODEL", settings.DEFAULT_MODEL)

        self.llm = build_chat_model(
            model=persona_model,
            temperature=0.7,  # Balansuje kreatywność z deterministycznym enforcement demographics
            max_tokens=settings.MAX_TOKENS,
            top_p=0.95,
            top_k=40,
        )

        # Konfigurujemy parser JSON, aby wymusić strukturalną odpowiedź
        self.json_parser = JsonOutputParser()

        # Budujemy szablon promptu do generowania person
        self.persona_prompt = ChatPromptTemplate.from_messages([
            ("system", "Jesteś ekspertem od badań rynkowych tworzącym realistyczne syntetyczne persony dla polskiego rynku. Zawsze odpowiadaj poprawnym JSONem."),
            ("user", "{prompt}")
        ])

        # Składamy łańcuch LangChain (prompt -> LLM -> parser)
        self.persona_chain = (
            self.persona_prompt
            | self.llm
            | self.json_parser
        )

        # Inicjalizuj RAG service (opcjonalnie - tylko jeśli włączony)
        self.rag_service = None
        if _rag_service_available and settings.RAG_ENABLED:
            try:
                self.rag_service = PolishSocietyRAG()
                logger.info("RAG service initialized successfully in PersonaGenerator")
            except Exception as e:
                logger.warning(f"RAG service unavailable: {e}")

    def sample_demographic_profile(
        self, distribution: DemographicDistribution, n_samples: int = 1
    ) -> list[dict[str, Any]]:
        """
        Próbkuj profile demograficzne zgodnie z zadanym rozkładem

        Metoda ta tworzy losowe profile demograficzne na podstawie prawdopodobieństw
        w obiekcie DemographicDistribution. Jeśli jakiś rozkład jest pusty lub niepoprawny,
        używa domyślnych wartości z constants.py.

        Args:
            distribution: Obiekt zawierający rozkłady prawdopodobieństw dla każdej kategorii
            n_samples: Liczba profili do wygenerowania (domyślnie 1)

        Returns:
            Lista słowników, każdy zawiera klucze: age_group, gender, education_level,
            income_bracket, location
        """
        profiles = []

        for _ in range(n_samples):
            # Normalizuj każdy rozkład lub użyj wartości domyślnych (polskich)
            age_groups = self._prepare_distribution(
                distribution.age_groups, DEFAULT_AGE_GROUPS
            )
            genders = self._prepare_distribution(distribution.genders, DEFAULT_GENDERS)
            education_levels = self._prepare_distribution(
                distribution.education_levels, POLISH_EDUCATION_LEVELS
            )
            income_brackets = self._prepare_distribution(
                distribution.income_brackets, POLISH_INCOME_BRACKETS
            )
            locations = self._prepare_distribution(
                distribution.locations, POLISH_LOCATIONS
            )

            # Losuj wartość z każdej kategorii zgodnie z wagami
            profile = {
                "age_group": self._weighted_sample(age_groups),
                "gender": self._weighted_sample(genders),
                "education_level": self._weighted_sample(education_levels),
                "income_bracket": self._weighted_sample(income_brackets),
                "location": self._weighted_sample(locations),
            }
            profiles.append(profile)

        return profiles

    def _weighted_sample(self, distribution: dict[str, float]) -> str:
        """
        Losuj element z rozkładu ważonego (weighted sampling)

        Args:
            distribution: Słownik kategoria -> prawdopodobieństwo (suma = 1.0)

        Returns:
            Wylosowana kategoria jako string

        Raises:
            ValueError: Jeśli rozkład jest pusty
        """
        if not distribution:
            raise ValueError("Distribution cannot be empty")
        categories = list(distribution.keys())
        weights = list(distribution.values())
        return self._rng.choice(categories, p=weights)

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

    def _prepare_distribution(
        self, distribution: dict[str, float], fallback: dict[str, float]
    ) -> dict[str, float]:
        """
        Przygotuj i znormalizuj rozkład prawdopodobieństw

        Sprawdza czy rozkład jest poprawny, normalizuje go do sumy 1.0,
        lub zwraca fallback jeśli rozkład jest niepoprawny.

        Args:
            distribution: Rozkład do znormalizowania
            fallback: Rozkład domyślny używany gdy distribution jest pusty/błędny

        Returns:
            Znormalizowany rozkład (suma = 1.0) lub fallback
        """
        if not distribution:
            return fallback
        total = sum(distribution.values())
        if total <= 0:
            return fallback
        # Pierwsza normalizacja - dziel przez sumę
        normalized = {key: value / total for key, value in distribution.items()}
        normalized_total = sum(normalized.values())
        # Druga normalizacja jeśli są błędy zaokrągleń numerycznych
        if not np.isclose(normalized_total, 1.0):
            normalized = {
                key: value / normalized_total for key, value in normalized.items()
            }
        return normalized

    def sample_big_five_traits(self, personality_skew: dict[str, float] = None) -> dict[str, float]:
        """
        Próbkuj cechy osobowości Big Five z rozkładów normalnych

        Model Big Five (OCEAN) mierzy pięć głównych wymiarów osobowości:
        - Openness (otwartość): ciekawość, kreatywność
        - Conscientiousness (sumienność): organizacja, dyscyplina
        - Extraversion (ekstrawersja): towarzyskość, energia
        - Agreeableness (ugodowość): empatia, współpraca
        - Neuroticism (neurotyzm): emocjonalność, podatność na stres

        Args:
            personality_skew: Opcjonalny słownik do przesunięcia rozkładów.
                              Klucze: 'openness', 'conscientiousness', etc.
                              Wartości: 0.0-1.0 (0=niskie, 0.5=zbalansowane, 1.0=wysokie)

        Returns:
            Słownik z wartościami cech w przedziale [0, 1]
        """
        skew = personality_skew or {}

        traits = {}
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            # Domyślnie: średnia = 0.5, odchylenie standardowe = 0.15
            mean = skew.get(trait, 0.5)
            # Upewnij się że średnia jest w przedziale [0, 1]
            mean = np.clip(mean, 0.0, 1.0)

            # Losuj z rozkładu normalnego i przytnij do [0, 1]
            value = np.clip(self._rng.normal(mean, 0.15), 0, 1)
            traits[trait] = value

        return traits

    def sample_cultural_dimensions(self) -> dict[str, float]:
        """
        Próbkuj wymiary kulturowe Hofstede

        Model Hofstede opisuje różnice kulturowe w 6 wymiarach:
        - power_distance: akceptacja nierówności władzy
        - individualism: indywidualizm vs kolektywizm
        - masculinity: asertywność vs troska o innych
        - uncertainty_avoidance: unikanie niepewności
        - long_term_orientation: orientacja długo- vs krótkoterminowa
        - indulgence: pobłażliwość vs powściągliwość

        Returns:
            Słownik z wartościami wymiarów w przedziale [0, 1]
        """
        return {
            "power_distance": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "individualism": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "masculinity": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "uncertainty_avoidance": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "long_term_orientation": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "indulgence": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
        }

    async def _get_rag_context_for_persona(
        self, demographic: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Pobierz kontekst z RAG dla danego profilu demograficznego

        Args:
            demographic: Profil demograficzny persony

        Returns:
            Dict z kluczami: context (str), citations (list), query (str),
            graph_context (str), graph_nodes (list), search_type (str)
            lub None jeśli RAG niedostępny
        """
        if not self.rag_service:
            return None

        import logging
        logger = logging.getLogger(__name__)

        try:
            context_data = await self.rag_service.get_demographic_insights(
                age_group=demographic.get('age_group', '25-34'),
                education=demographic.get('education_level', 'wyższe'),
                location=demographic.get('location', 'Warszawa'),
                gender=demographic.get('gender', 'mężczyzna')
            )

            # Loguj szczegóły RAG context
            context_len = len(context_data.get('context', ''))
            graph_nodes_count = len(context_data.get('graph_nodes', []))
            search_type = context_data.get('search_type', 'unknown')
            citations_count = len(context_data.get('citations', []))

            logger.info(
                f"RAG context retrieved: {context_len} chars, "
                f"{graph_nodes_count} graph nodes, "
                f"{citations_count} citations, "
                f"search_type={search_type}"
            )

            # Jeśli mamy graph nodes, loguj ich typy
            if graph_nodes_count > 0:
                node_types = [node.get('type', 'Unknown') for node in context_data.get('graph_nodes', [])]
                logger.info(f"Graph node types: {', '.join(node_types)}")

            return context_data
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {e}", exc_info=True)
            return None

    async def generate_persona_personality(
        self,
        demographic_profile: dict[str, Any],
        psychological_profile: dict[str, Any],
        use_rag: bool = True,  # NOWY PARAMETR - domyślnie włączony
        advanced_options: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Generuj osobowość persony przy użyciu LangChain + Gemini

        Tworzy szczegółowy prompt oparty na profilach demograficznym i psychologicznym,
        opcjonalnie wzbogacony o kontekst RAG z bazy wiedzy o polskim społeczeństwie.

        Args:
            demographic_profile: Słownik z danymi demograficznymi (wiek, płeć, lokalizacja, etc.)
            psychological_profile: Słownik z cechami Big Five i wymiarami Hofstede
            use_rag: Czy użyć kontekstu z bazy wiedzy RAG (default: True)
            advanced_options: Opcjonalne zaawansowane opcje generowania (nieużywane obecnie)

        Returns:
            Krotka (prompt_text, response_dict) gdzie:
            - prompt_text: Pełny tekst wysłany do LLM (do logowania/debugowania)
            - response_dict: Sparsowana odpowiedź JSON z polami persony
                            + pole '_rag_citations' jeśli użyto RAG

        Raises:
            ValueError: Jeśli generowanie się nie powiedzie lub odpowiedź jest niepoprawna
        """

        import logging
        logger = logging.getLogger(__name__)

        # Pobierz kontekst RAG jeśli włączony
        rag_context = None
        rag_citations = None
        rag_context_details = None
        if use_rag and self.rag_service:
            rag_data = await self._get_rag_context_for_persona(demographic_profile)
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

        # Pobierz target_audience_description, orchestration brief, focus_area z advanced_options
        target_audience_desc = None
        orchestration_brief = None
        focus_area = None
        demographic_preset = None
        if advanced_options:
            target_audience_desc = advanced_options.get('target_audience_description')
            orchestration_brief = advanced_options.get('orchestration_brief')
            focus_area = advanced_options.get('focus_area')
            demographic_preset = advanced_options.get('demographic_preset')

            if target_audience_desc:
                logger.info(f"Using target audience description: {target_audience_desc[:100]}...")
            if orchestration_brief:
                logger.info(f"Using orchestration brief: {orchestration_brief[:150]}... ({len(orchestration_brief)} chars)")
            if focus_area:
                logger.info(f"Using focus area: {focus_area}")
            if demographic_preset:
                logger.info(f"Using demographic preset: {demographic_preset}")

        # Generuj prompt (z RAG, target audience, orchestration brief, focus_area)
        prompt_text = self._create_persona_prompt(
            demographic_profile,
            psychological_profile,
            rag_context=rag_context,
            target_audience_description=target_audience_desc,
            orchestration_brief=orchestration_brief,
            focus_area=focus_area,
            demographic_preset=demographic_preset
        )

        try:
            logger.info(
                f"Generating persona with demographics: {demographic_profile.get('age_group')}, "
                f"{demographic_profile.get('gender')}, {demographic_profile.get('location')}"
                f" | RAG: {'YES' if rag_context else 'NO'}"
            )
            # Wywołaj łańcuch LangChain (prompt -> LLM -> parser JSON)
            response = await self.persona_chain.ainvoke({"prompt": prompt_text})

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

    def _get_focus_area_enforcement(self, focus_area: str | None) -> str:
        """Zwraca enforcement rules dla focus_area (używane w ZASADY prompt section)."""
        if not focus_area:
            return ""

        enforcements = {
            "technology": "\n• 🎯 FOCUS AREA: TECHNOLOGIA - Interests MUSZĄ zawierać tech keywords (AI, programming, gadgets, software, gaming, etc.)!",
            "lifestyle": "\n• 🎯 FOCUS AREA: LIFESTYLE - Interests MUSZĄ zawierać lifestyle keywords (fitness, yoga, wellness, healthy eating, meditation, etc.)!",
            "finance": "\n• 🎯 FOCUS AREA: FINANSE - Interests MUSZĄ zawierać finance keywords (investing, stocks, budgeting, financial planning, crypto, etc.)!",
            "shopping": "\n• 🎯 FOCUS AREA: ZAKUPY - Interests MUSZĄ zawierać shopping keywords (fashion, online shopping, deals, brands, e-commerce, etc.)!",
            "entertainment": "\n• 🎯 FOCUS AREA: ROZRYWKA - Interests MUSZĄ zawierać entertainment keywords (films, music, concerts, gaming, social events, etc.)!",
            "general": "\n• 🎯 FOCUS AREA: OGÓLNE - Interests powinny być różnorodne, nie ograniczone do jednej dziedziny"
        }

        return enforcements.get(focus_area.lower(), "")

    def _create_persona_prompt(
        self,
        demographic: dict[str, Any],
        psychological: dict[str, Any],
        rag_context: str | None = None,
        target_audience_description: str | None = None,
        orchestration_brief: str | None = None,  # Długi brief od Gemini 2.5 Pro
        focus_area: str | None = None,  # UI dropdown: Obszar Zainteresowań (PRIORYTET!)
        demographic_preset: str | None = None  # UI dropdown: Grupa Demograficzna (kontekst)
    ) -> str:
        """
        Utwórz prompt dla LLM do generowania persony - WERSJA POLSKA

        Tworzy szczegółowy prompt zawierający:
        - Dane demograficzne i psychologiczne
        - Interpretację cech Big Five i Hofstede PO POLSKU
        - 3 przykłady few-shot z polskimi personami
        - Opcjonalny kontekst RAG z bazy wiedzy o polskim społeczeństwie
        - Opcjonalny dodatkowy opis grupy docelowej od użytkownika
        - Opcjonalny orchestration brief (900-1200 znaków) od Gemini 2.5 Pro
        - Instrukcje jak stworzyć unikalną polską personę

        Args:
            demographic: Profil demograficzny (wiek, płeć, edukacja, etc.)
            psychological: Profil psychologiczny (Big Five + Hofstede)
            rag_context: Opcjonalny kontekst z RAG (fragmenty z dokumentów)
            target_audience_description: Opcjonalny dodatkowy opis grupy docelowej
            orchestration_brief: Opcjonalny DŁUGI brief od orchestration agent (Gemini 2.5 Pro)

        Returns:
            Pełny tekst prompta gotowy do wysłania do LLM (po polsku)
        """

        # Generuj unikalny seed dla tej persony (do różnicowania)
        persona_seed = self._rng.integers(1000, 9999)

        # Losuj polskie imię i nazwisko dla większej różnorodności
        gender_lower = demographic.get('gender', 'male').lower()
        if 'female' in gender_lower or 'kobieta' in gender_lower:
            suggested_first_name = self._rng.choice(POLISH_FEMALE_NAMES)
        else:
            suggested_first_name = self._rng.choice(POLISH_MALE_NAMES)
        suggested_surname = self._rng.choice(POLISH_SURNAMES)

        if demographic.get('age'):
            headline_age_rule = f"• HEADLINE: Musi zawierać liczbę {demographic['age']} lat i realną motywację tej osoby.\n"
        elif demographic.get('age_group'):
            headline_age_rule = (
                f"• HEADLINE: Podaj konkretną liczbę lat zgodną z przedziałem {demographic['age_group']} "
                "i pokaż realną motywację tej osoby.\n"
            )
        else:
            headline_age_rule = "• HEADLINE: Podaj konkretny wiek w latach i realną motywację tej osoby.\n"

        # Pobierz wartości Big Five (interpretację robi LLM)
        openness_val = psychological.get('openness', 0.5)
        conscientiousness_val = psychological.get('conscientiousness', 0.5)
        extraversion_val = psychological.get('extraversion', 0.5)
        agreeableness_val = psychological.get('agreeableness', 0.5)
        neuroticism_val = psychological.get('neuroticism', 0.5)

        # Unified context section (merge focus_area + target_audience + brief + RAG)
        # NOWA KOLEJNOŚĆ: focus_area (PRIORYTET!) → target_audience → brief → RAG
        unified_context = ""
        if rag_context or target_audience_description or orchestration_brief or focus_area:
            context_parts = []

            # 1. FOCUS AREA - NAJWYŻSZY PRIORYTET (UI dropdown)
            if focus_area and focus_area.strip():
                focus_area_descriptions = {
                    "technology": "🎯 OBSZAR ZAINTERESOWAŃ (PRIORYTET #1!):\nPersona MUSI być zainteresowana TECHNOLOGIĄ - produkty tech, oprogramowanie, gadżety, innowacje cyfrowe. Interests powinny zawierać tech-related keywords (programowanie, AI, gaming, tech gadgets, etc.)",
                    "lifestyle": "🎯 OBSZAR ZAINTERESOWAŃ (PRIORYTET #1!):\nPersona MUSI być zainteresowana STYLEM ŻYCIA - zdrowie, fitness, wellness, hobby, rozwój osobisty. Interests powinny zawierać lifestyle keywords (yoga, medytacja, zdrowa żywność, sport, self-improvement, etc.)",
                    "finance": "🎯 OBSZAR ZAINTERESOWAŃ (PRIORYTET #1!):\nPersona MUSI być zainteresowana FINANSAMI - bankowość, inwestycje, oszczędzanie, planowanie finansowe. Interests powinny zawierać finance keywords (investing, stocks, budgeting, financial planning, etc.)",
                    "shopping": "🎯 OBSZAR ZAINTERESOWAŃ (PRIORYTET #1!):\nPersona MUSI być zainteresowana ZAKUPAMI - retail, e-commerce, konsumpcja, trendy zakupowe. Interests powinny zawierać shopping keywords (fashion, online shopping, deals, brands, etc.)",
                    "entertainment": "🎯 OBSZAR ZAINTERESOWAŃ (PRIORYTET #1!):\nPersona MUSI być zainteresowana ROZRYWKĄ - media, kultura, czas wolny, entertainment. Interests powinny zawierać entertainment keywords (films, music, concerts, gaming, social events, etc.)",
                    "general": "🎯 OBSZAR ZAINTERESOWAŃ (PRIORYTET #1!):\nPersona ma SZEROKĄ PERSPEKTYWĘ SPOŁECZNĄ - różnorodne zainteresowania, nie ograniczone do jednej dziedziny."
                }
                focus_desc = focus_area_descriptions.get(focus_area.lower(), f"🎯 OBSZAR ZAINTERESOWAŃ: {focus_area}")
                context_parts.append(focus_desc)

            # 2. TARGET AUDIENCE DESCRIPTION - WYSOKI PRIORYTET (UI textarea)
            if target_audience_description and target_audience_description.strip():
                context_parts.append(f"🎯 DODATKOWY OPIS GRUPY DOCELOWEJ (PRIORYTET #2!):\n{target_audience_description.strip()}")

            # 3. ORCHESTRATION BRIEF - średni priorytet (Gemini 2.5 Pro analysis)
            if orchestration_brief and orchestration_brief.strip():
                context_parts.append(f"📋 ORCHESTRATION BRIEF:\n{orchestration_brief.strip()}")

            # 4. RAG CONTEXT - najniższy priorytet (background knowledge)
            if rag_context:
                context_parts.append(f"📊 KONTEKST RAG (tło):\n{rag_context}")

            unified_context = f"""
═══════════════════════════════════════════
KONTEKST (Focus Area + Target Audience + Brief + RAG):
═══════════════════════════════════════════

{chr(10).join(context_parts)}

⚠️ KLUCZOWE ZASADY:
• PRIORYTET: Focus Area i Target Audience MUSZĄ mieć wpływ na interests i values!
• Użyj kontekstu jako TŁA życia persony (nie cytuj statystyk!)
• Stwórz FASCYNUJĄCĄ historię - kontekst to fundament, nie lista faktów
• Wskaźniki → konkretne detale życia (housing crisis → wynajmuje, oszczędza)
• Trendy → doświadczenia życiowe (mobilność → zmiana 3 prac w 5 lat)
• Naturalność: "Jak wielu rówieśników..." zamiast "67% absolwentów..."

═══════════════════════════════════════════

"""

        return f"""Expert: Syntetyczne persony dla polskiego rynku - UNIKALNE, REALISTYCZNE, SPÓJNE.

{unified_context}PERSONA #{persona_seed}: {suggested_first_name} {suggested_surname}

⚠️  DEMOGRAPHICS - MUSISZ DOKŁADNIE PRZESTRZEGAĆ (KRYTYCZNE!):
• WIEK: {demographic.get('age_group')} lat - generuj osobę DOKŁADNIE z tego przedziału!
• PŁEĆ: {demographic.get('gender')} - generuj TYLKO tę płeć, NIE odwrotną!
• LOKALIZACJA: {demographic.get('location')} - osoba MIESZKA TAM, nie gdzie indziej!
• WYKSZTAŁCENIE: {demographic.get('education_level')}
• DOCHÓD: {demographic.get('income_bracket')}

OSOBOWOŚĆ (Big Five - wartości 0-1):
• Otwartość (Openness): {openness_val:.2f}
• Sumienność (Conscientiousness): {conscientiousness_val:.2f}
• Ekstrawersja (Extraversion): {extraversion_val:.2f}
• Ugodowość (Agreeableness): {agreeableness_val:.2f}
• Neurotyzm (Neuroticism): {neuroticism_val:.2f}

Interpretacja Big Five: <0.4 = niskie, 0.4-0.6 = średnie, >0.6 = wysokie.
Wykorzystaj te wartości do stworzenia spójnej osobowości i historii życiowej.

HOFSTEDE (wartości 0-1): PD={psychological.get('power_distance', 0.5):.2f} | IND={psychological.get('individualism', 0.5):.2f} | UA={psychological.get('uncertainty_avoidance', 0.5):.2f}

ZASADY:
• Zawód = wykształcenie + dochód
• Osobowość → historia (O→podróże, S→planowanie)
• Detale: dzielnice, marki, konkretne hobby{self._get_focus_area_enforcement(focus_area)}
• UNIKALNOŚĆ: Każda persona MUSI mieć RÓŻNĄ historię życiową - nie kopiuj opisów!
• Background_story NIE może kopiować briefu segmentu ani powtarzać całych akapitów z kontekstu
{headline_age_rule}• Pokaż codzienne wybory i motywacje tej osoby - zero ogólników

⚠️ CATCHY SEGMENT NAME (2-4 słowa):
Wygeneruj krótką, chwytliwą nazwę marketingową dla segmentu tej persony.
• Powinna odzwierciedlać wiek, wartości, styl życia, status ekonomiczny
• Przykłady: "Pasywni Liberałowie", "Młodzi Prekariusze", "Aktywni Seniorzy", "Cyfrowi Nomadzi", "Stabilni Tradycjonaliści"
• UNIKAJ długich opisów technicznych jak "Kobiety 35-44 wyższe wykształcenie"
• Polski język, kulturowo relevantne, konkretne

⚠️ KRYTYCZNE: Generuj KOMPLETNIE UNIKALNĄ personę z FASCYNUJĄCĄ historią życiową!
• NIE kopiuj ogólnych opisów segmentu do background_story
• Fokus na TEJ KONKRETNEJ OSOBY, jej specyficznych doświadczeniach
• Użyj persona_seed #{persona_seed} jako źródło różnorodności

WYŁĄCZNIE JSON (bez markdown):
{{
  "full_name": "<polskie imię+nazwisko>",
  "catchy_segment_name": "<2-4 słowa, krótka marketingowa nazwa segmentu>",
  "persona_title": "<zawód/etap życia>",
  "headline": "<1 zdanie: wiek, zawód, UNIKALNE motywacje>",
  "background_story": "<3-5 akapitów (400-600 słów): SZCZEGÓŁOWA historia TEJ OSOBY - jej życie, kariera, wyzwania, aspiracje, konkretne wydarzenia. Pokaż jej drogę życiową, kluczowe decyzje, obecną sytuację i marzenia. Każdy akapit powinien pokazywać inny aspekt jej życia (przeszłość, praca, relacje, wyzwania, cele). Pisz jak storyteller - używaj konkretnych detali, emocji, wewnętrznych dylemotów.>",
  "values": ["<5-7 wartości>"],
  "interests": ["<5-7 hobby/aktywności>"],
  "communication_style": "<jak się komunikuje>",
  "decision_making_style": "<jak podejmuje decyzje>",
  "typical_concerns": ["<3-5 SPECYFICZNYCH zmartwień/priorytetów>"]
}}"""

    def validate_distribution(
        self,
        generated_personas: list[dict[str, Any]],
        target_distribution: DemographicDistribution,
    ) -> dict[str, Any]:
        """
        Waliduj czy wygenerowane persony pasują do docelowego rozkładu (test chi-kwadrat)

        Sprawdza statystycznie czy rzeczywisty rozkład cech demograficznych w wygenerowanych
        personach odpowiada zadanemu rozkładowi docelowemu. Używa testu chi-kwadrat dla
        każdej kategorii (wiek, płeć, edukacja, dochód, lokalizacja).

        Args:
            generated_personas: Lista wygenerowanych person (jako słowniki)
            target_distribution: Oczekiwany rozkład demograficzny

        Returns:
            Słownik z wynikami testów dla każdej kategorii oraz ogólną oceną:
            {
                "age": {"p_value": float, "chi_square_statistic": float, ...},
                "gender": {...},
                "overall_valid": bool  # Wartość True oznacza, że wszystkie p > 0.05
            }
        """
        results = {}

        # Testuj rozkład wieku (tylko jeśli podany)
        if target_distribution.age_groups:
            results["age"] = self._chi_square_test(
                generated_personas, "age_group", target_distribution.age_groups
            )

        # Testuj rozkład płci (tylko jeśli podany)
        if target_distribution.genders:
            results["gender"] = self._chi_square_test(
                generated_personas, "gender", target_distribution.genders
            )

        # Testuj rozkład edukacji (tylko jeśli podany)
        if target_distribution.education_levels:
            results["education"] = self._chi_square_test(
                generated_personas, "education_level", target_distribution.education_levels
            )

        # Testuj rozkład dochodów (tylko jeśli podany)
        if target_distribution.income_brackets:
            results["income"] = self._chi_square_test(
                generated_personas, "income_bracket", target_distribution.income_brackets
            )

        # Testuj rozkład lokalizacji (tylko jeśli podany)
        if target_distribution.locations:
            results["location"] = self._chi_square_test(
                generated_personas, "location", target_distribution.locations
            )

        # Ogólna walidacja - wszystkie p-wartości powinny być > 0.05
        all_p_values = [r["p_value"] for r in results.values() if "p_value" in r]
        results["overall_valid"] = all(
            p > settings.STATISTICAL_SIGNIFICANCE_THRESHOLD for p in all_p_values
        ) if all_p_values else True

        return results

    def _chi_square_test(
        self, personas: list[dict[str, Any]], field: str, expected_dist: dict[str, float]
    ) -> dict[str, float]:
        """
        Wykonaj test chi-kwadrat dla konkretnego pola demograficznego

        Test chi-kwadrat sprawdza czy obserwowany rozkład kategorii (np. grup wiekowych)
        statystycznie różni się od rozkładu oczekiwanego. Im wyższe p-value, tym lepiej
        (p > 0.05 oznacza że rozkłady są zgodne).

        Args:
            personas: Lista person do sprawdzenia
            field: Nazwa pola do przetestowania (np. "age_group", "gender")
            expected_dist: Oczekiwany rozkład prawdopodobieństw

        Returns:
            Słownik z wynikami testu:
            - chi_square_statistic: wartość statystyki chi-kwadrat
            - p_value: p-wartość (>0.05 = dobre dopasowanie)
            - degrees_of_freedom: liczba stopni swobody
            - observed: obserwowane liczności
            - expected: oczekiwane liczności
        """
        # Filtruj kategorie z niepoprawnymi prawdopodobieństwami
        valid_categories = [
            (category, probability)
            for category, probability in expected_dist.items()
            if probability and probability > 0
        ]

        if not valid_categories:
            return {
                "chi_square_statistic": 0.0,
                "p_value": 1.0,
                "degrees_of_freedom": 0,
                "observed": {},
                "expected": {},
            }

        # Normalizuj prawdopodobieństwa do sumy = 1.0
        total_prob = sum(probability for _, probability in valid_categories)
        normalized_probs = {
            category: probability / total_prob for category, probability in valid_categories
        }

        # Policz obserwowane wystąpienia każdej kategorii
        observed_counts = {category: 0 for category in normalized_probs}
        valid_samples = 0
        for persona in personas:
            value = persona.get(field)
            if value in observed_counts:
                observed_counts[value] += 1
                valid_samples += 1

        if valid_samples == 0:
            return {
                "chi_square_statistic": 0.0,
                "p_value": 1.0,
                "degrees_of_freedom": len(observed_counts) - 1,
                "observed": observed_counts,
                "expected": {category: 0.0 for category in observed_counts},
            }

        # Oblicz oczekiwane liczności (probability * total_count)
        expected_counts = {
            category: normalized_probs[category] * valid_samples
            for category in normalized_probs
        }

        # Przygotuj listy do testu chi-kwadrat (scipy wymaga list w tej samej kolejności)
        observed = [observed_counts[category] for category in normalized_probs]
        expected = [expected_counts[category] for category in normalized_probs]

        # Wykonaj test chi-kwadrat
        chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)

        return {
            "chi_square_statistic": float(chi2_stat),
            "p_value": float(p_value),
            "degrees_of_freedom": len(normalized_probs) - 1,
            "observed": observed_counts,
            "expected": expected_counts,
            "sample_size": valid_samples,
        }

    # === SEGMENT-BASED ARCHITECTURE: ENFORCE DEMOGRAPHICS ===

    async def generate_persona_from_segment(
        self,
        segment_id: str,
        segment_name: str,
        segment_context: str,
        demographics_constraints: dict[str, Any],  # Will be DemographicConstraints from SegmentDefinition
        graph_insights: list[Any] = None,
        rag_citations: list[Any] = None,
        personality_skew: dict[str, float] | None = None
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

        Returns:
            Tuple (prompt_text, response_dict)
        """
        import logging
        logger = logging.getLogger(__name__)

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

        # Create prompt with segment context
        prompt_text = self._create_segment_persona_prompt(
            demographic_profile,
            psychological_profile,
            segment_name,
            segment_context,
            graph_insights,
            rag_citations
        )

        try:
            response = await self.persona_chain.ainvoke({"prompt": prompt_text})

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

    def _create_segment_persona_prompt(
        self,
        demographic: dict[str, Any],
        psychological: dict[str, Any],
        segment_name: str,
        segment_context: str,
        graph_insights: list[Any],
        rag_citations: list[Any]
    ) -> str:
        """Create prompt for segment-based persona generation."""

        # Suggest Polish name
        gender_lower = demographic.get('gender', 'kobieta').lower()
        if 'female' in gender_lower or 'kobieta' in gender_lower:
            suggested_first_name = self._rng.choice(POLISH_FEMALE_NAMES)
        else:
            suggested_first_name = self._rng.choice(POLISH_MALE_NAMES)
        suggested_surname = self._rng.choice(POLISH_SURNAMES)

        age = demographic.get('age', 30)

        # Generate unique persona seed for diversity
        persona_seed = self._rng.integers(1000, 9999)

        # Format insights
        insights_text = ""
        if graph_insights:
            insights_text = "\n".join([
                f"- {ins.get('summary', ins.get('streszczenie', 'N/A'))}"
                for ins in graph_insights[:5]
            ])

        return f"""Wygeneruj realistyczną personę dla segmentu "{segment_name}".

CONSTRAINTS (MUSISZ PRZESTRZEGAĆ!):
• Wiek: {age} lat
• Płeć: {demographic.get('gender')}
• Wykształcenie: {demographic.get('education_level')}
• Dochód: {demographic.get('income_bracket')}
• Lokalizacja: {demographic.get('location')}

KONTEKST SEGMENTU:
{segment_context}

INSIGHTS:
{insights_text or "Brak insights"}

OSOBOWOŚĆ (Big Five):
• Otwartość: {psychological.get('openness', 0.5):.2f}
• Sumienność: {psychological.get('conscientiousness', 0.5):.2f}
• Ekstrawersja: {psychological.get('extraversion', 0.5):.2f}

ZASADY:
• Persona MUSI pasować do constraints
• Zawód = wykształcenie + dochód
• Używaj kontekstu jako tła (nie cytuj statystyk!)
• UNIKALNOŚĆ: Każda persona w segmencie MUSI mieć RÓŻNĄ historię życiową!
• HEADLINE: Musi zawierać liczbę {age} lat i realną motywację tej osoby
• Background_story NIE może kopiować briefu segmentu ani powtarzać całych akapitów z kontekstu
• Pokaż codzienne wybory i motywacje tej osoby - zero ogólników

⚠️ CATCHY SEGMENT NAME (2-4 słowa):
Wygeneruj krótką, chwytliwą nazwę marketingową dla tego segmentu.
• Powinna odzwierciedlać wiek, wartości, styl życia, status ekonomiczny
• Przykłady: "Pasywni Liberałowie", "Młodzi Prekariusze", "Aktywni Seniorzy", "Cyfrowi Nomadzi"
• UNIKAJ długich opisów technicznych jak "Kobiety 35-44 wyższe wykształcenie"
• Polski język, kulturowo relevantne

⚠️ KRYTYCZNE: Generuj UNIKALNĄ personę (Persona #{persona_seed})!
• NIE kopiuj ogólnych opisów segmentu do background_story
• Fokus na TEJ KONKRETNEJ OSOBY, jej specyficznych doświadczeniach
• Każda persona w segmencie ma INNĄ historię życiową, inne detale, różne zainteresowania

ZWRÓĆ JSON:
{{
  "full_name": "{suggested_first_name} {suggested_surname}",
  "catchy_segment_name": "<2-4 słowa, krótka marketingowa nazwa segmentu>",
  "persona_title": "<zawód>",
  "headline": "<{age} lat, zawód, UNIKALNE motywacje>",
  "background_story": "<2-3 zdania: KONKRETNA historia TEJ OSOBY - nie ogólny opis segmentu!>",
  "values": ["<5-7 wartości>"],
  "interests": ["<5-7 hobby>"],
  "communication_style": "<styl>",
  "decision_making_style": "<styl>",
  "typical_concerns": ["<3-5 SPECYFICZNYCH zmartwień>"]
}}"""
