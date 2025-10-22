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

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.config import get_settings
from app.core.constants import (
    POLISH_LOCATIONS,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
    POLISH_MALE_NAMES,
    POLISH_FEMALE_NAMES,
    POLISH_SURNAMES,
)
from app.services.shared.clients import build_chat_model

settings = get_settings()


# ============================================================================
# PROMPT BUILDERS - Funkcje pomocnicze dla generacji promptów
# ============================================================================

def create_persona_prompt(
    demographic: Dict[str, Any],
    psychological: Dict[str, Any],
    persona_seed: int,
    suggested_first_name: str,
    suggested_surname: str,
    rag_context: Optional[str] = None,
    target_audience_description: Optional[str] = None,
    orchestration_brief: Optional[str] = None
) -> str:
    """
    Tworzy szczegółowy prompt dla LLM do generowania persony - WERSJA POLSKA

    Args:
        demographic: Profil demograficzny (wiek, płeć, edukacja, etc.)
        psychological: Profil psychologiczny (Big Five + Hofstede)
        persona_seed: Unikalny seed dla różnicowania (1000-9999)
        suggested_first_name: Sugerowane polskie imię
        suggested_surname: Sugerowane polskie nazwisko
        rag_context: Opcjonalny kontekst z RAG (fragmenty z dokumentów)
        target_audience_description: Opcjonalny dodatkowy opis grupy docelowej
        orchestration_brief: Opcjonalny DŁUGI brief od orchestration agent (Gemini 2.5 Pro)

    Returns:
        Pełny tekst prompta gotowy do wysłania do LLM (po polsku)
    """

    # Determine headline age rule based on available data
    if demographic.get('age'):
        headline_age_rule = f"• HEADLINE: Musi zawierać liczbę {demographic['age']} lat i realną motywację tej osoby.\n"
    elif demographic.get('age_group'):
        headline_age_rule = (
            f"• HEADLINE: Podaj konkretną liczbę lat zgodną z przedziałem {demographic['age_group']} "
            "i pokaż realną motywację tej osoby.\n"
        )
    else:
        headline_age_rule = "• HEADLINE: Podaj konkretny wiek w latach i realną motywację tej osoby.\n"

    # Get Big Five values
    openness_val = psychological.get('openness', 0.5)
    conscientiousness_val = psychological.get('conscientiousness', 0.5)
    extraversion_val = psychological.get('extraversion', 0.5)
    agreeableness_val = psychological.get('agreeableness', 0.5)
    neuroticism_val = psychological.get('neuroticism', 0.5)

    # Unified context section (merge RAG + Target Audience + Orchestration Brief)
    unified_context = ""
    if rag_context or target_audience_description or orchestration_brief:
        context_parts = []

        if rag_context:
            context_parts.append(f"📊 KONTEKST RAG:\n{rag_context}")
        if orchestration_brief and orchestration_brief.strip():
            context_parts.append(f"📋 ORCHESTRATION BRIEF:\n{orchestration_brief.strip()}")
        if target_audience_description and target_audience_description.strip():
            context_parts.append(f"🎯 GRUPA DOCELOWA:\n{target_audience_description.strip()}")

        unified_context = f"""
═══════════════════════════════════════════
KONTEKST (RAG + Brief + Audience):
═══════════════════════════════════════════

{chr(10).join(context_parts)}

⚠️ KLUCZOWE ZASADY:
• Użyj kontekstu jako TŁA życia persony (nie cytuj statystyk!)
• Stwórz FASCYNUJĄCĄ historię - kontekst to fundament, nie lista faktów
• Wskaźniki → konkretne detale życia (housing crisis → wynajmuje, oszczędza)
• Trendy → doświadczenia życiowe (mobilność → zmiana 3 prac w 5 lat)
• Naturalność: "Jak wielu rówieśników..." zamiast "67% absolwentów..."

═══════════════════════════════════════════

"""

    return f"""Expert: Syntetyczne persony dla polskiego rynku - UNIKALNE, REALISTYCZNE, SPÓJNE.

{unified_context}PERSONA #{persona_seed}: {suggested_first_name} {suggested_surname}

PROFIL:
• Wiek: {demographic.get('age_group')} | Płeć: {demographic.get('gender')} | Lokalizacja: {demographic.get('location')}
• Wykształcenie: {demographic.get('education_level')} | Dochód: {demographic.get('income_bracket')}

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
• Detale: dzielnice, marki, konkretne hobby
• UNIKALNOŚĆ: Każda persona MUSI mieć RÓŻNĄ historię życiową - nie kopiuj opisów!
• Background_story NIE może kopiować briefu segmentu ani powtarzać całych akapitów z kontekstu
{headline_age_rule}• Pokaż codzienne wybory i motywacje tej osoby - zero ogólników

⚠️ CATCHY SEGMENT NAME (2-4 słowa):
Wygeneruj krótką, chwytliwą nazwę marketingową dla segmentu tej persony.
• Powinna odzwierciedlać wiek, wartości, styl życia, status ekonomiczny
• Przykłady: "Pasywni Liberałowie", "Młodzi Prekariusze", "Aktywni Seniorzy", "Cyfrowi Nomadzi", "Stabilni Tradycjonaliści"
• UNIKAJ długich opisów technicznych jak "Kobiety 35-44 wyższe wykształcenie"
• Polski język, kulturowo relevantne, konkretne

PRZYKŁAD:
{{"full_name": "Marek Kowalczyk", "catchy_segment_name": "Stabilni Tradycjonaliści", "persona_title": "Główny Księgowy", "headline": "Poznański księgowy (56) planujący emeryturę", "background_story": "28 lat w firmie, żonaty, dwoje dorosłych dzieci, kupił działkę pod Poznaniem, skarbnik parafii", "values": ["Stabilność", "Lojalność", "Rodzina", "Odpowiedzialność"], "interests": ["Wędkarstwo", "Majsterkowanie", "Grillowanie"], "communication_style": "formalny, face-to-face", "decision_making_style": "metodyczny, unika ryzyka", "typical_concerns": ["Emerytura", "Sukcesja", "Zdrowie"]}}

⚠️ KRYTYCZNE: Generuj KOMPLETNIE INNĄ personę z UNIKALNĄ historią życiową!
• NIE kopiuj ogólnych opisów segmentu do background_story
• Fokus na TEJ KONKRETNEJ OSOBY, jej specyficznych doświadczeniach
• Użyj persona_seed #{persona_seed} jako źródło różnorodności

WYŁĄCZNIE JSON (bez markdown):
{{
  "full_name": "<polskie imię+nazwisko>",
  "catchy_segment_name": "<2-4 słowa, krótka marketingowa nazwa segmentu>",
  "persona_title": "<zawód/etap życia>",
  "headline": "<1 zdanie: wiek, zawód, UNIKALNE motywacje>",
  "background_story": "<2-3 zdania: KONKRETNA historia TEJ OSOBY - jej życie, kariera, sytuacja>",
  "values": ["<5-7 wartości>"],
  "interests": ["<5-7 hobby/aktywności>"],
  "communication_style": "<jak się komunikuje>",
  "decision_making_style": "<jak podejmuje decyzje>",
  "typical_concerns": ["<3-5 SPECYFICZNYCH zmartwień/priorytetów>"]
}}"""


def create_segment_persona_prompt(
    demographic: Dict[str, Any],
    psychological: Dict[str, Any],
    segment_name: str,
    segment_context: str,
    graph_insights: List[Any],
    rag_citations: List[Any],
    persona_seed: int,
    suggested_first_name: str,
    suggested_surname: str
) -> str:
    """
    Tworzy prompt dla generacji persony z WYMUSZENIEM demographics z segmentu.

    Args:
        demographic: Enforced demographic profile (age, gender, education, income, location)
        psychological: Psychological profile (Big Five + Hofstede)
        segment_name: Nazwa segmentu (np. "Młodzi Prekariusze")
        segment_context: Kontekst społeczny segmentu (500-800 znaków)
        graph_insights: Insights filtrowane dla segmentu
        rag_citations: High-quality RAG citations
        persona_seed: Unique persona seed for diversity
        suggested_first_name: Suggested Polish first name
        suggested_surname: Suggested Polish surname

    Returns:
        Full prompt text for segment-based persona generation
    """
    age = demographic.get('age', 30)

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


# Import RAG service (opcjonalny - tylko jeśli RAG włączony)
try:
    if settings.RAG_ENABLED:
        from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG
        _rag_service_available = True
    else:
        _rag_service_available = False
except ImportError:
    _rag_service_available = False


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
            temperature=0.9,  # Podniesiona wartość dla bardziej kreatywnych, zróżnicowanych person
            max_tokens=settings.MAX_TOKENS,
            top_p=0.95,
            top_k=40,
        )

        # Konfigurujemy parser JSON, aby wymusić strukturalną odpowiedź
        self.json_parser = JsonOutputParser()

        # Budujemy szablon promptu do generowania person (z importu)
        self.persona_prompt = PERSONA_GENERATION_CHAT_PROMPT

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

        # In-memory cache dla RAG queries (eliminuje wielokrotne identyczne zapytania)
        # Key: (age_group, education, location, gender) tuple
        # Value: dict z RAG context
        self._rag_cache: dict[tuple[str, str, str, str], dict[str, Any]] = {}

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
        Pobierz kontekst z RAG dla danego profilu demograficznego (z cache)

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

        # Przygotuj cache key (normalizuj wartości)
        age_group = demographic.get('age_group', '25-34')
        education = demographic.get('education_level', 'wyższe')
        location = demographic.get('location', 'Warszawa')
        gender = demographic.get('gender', 'mężczyzna')

        cache_key = (age_group, education, location, gender)

        # Sprawdź cache przed wywołaniem RAG
        if cache_key in self._rag_cache:
            logger.debug(
                f"RAG cache HIT dla profilu: wiek={age_group}, edukacja={education}, "
                f"lokalizacja={location}, płeć={gender}"
            )
            return self._rag_cache[cache_key]

        logger.debug(
            f"RAG cache MISS dla profilu: wiek={age_group}, edukacja={education}, "
            f"lokalizacja={location}, płeć={gender}"
        )

        try:
            context_data = await self.rag_service.get_demographic_insights(
                age_group=age_group,
                education=education,
                location=location,
                gender=gender
            )

            # Zapisz w cache dla przyszłych wywołań
            self._rag_cache[cache_key] = context_data

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

        # Generuj unikalny seed dla tej persony (do różnicowania)
        persona_seed = self._rng.integers(1000, 9999)

        # Losuj polskie imię i nazwisko dla większej różnorodności
        gender_lower = demographic_profile.get('gender', 'male').lower()
        if 'female' in gender_lower or 'kobieta' in gender_lower:
            suggested_first_name = self._rng.choice(POLISH_FEMALE_NAMES)
        else:
            suggested_first_name = self._rng.choice(POLISH_MALE_NAMES)
        suggested_surname = self._rng.choice(POLISH_SURNAMES)

        # Generuj prompt używając funkcji modułowej
        prompt_text = create_persona_prompt(
            demographic_profile,
            psychological_profile,
            persona_seed=persona_seed,
            suggested_first_name=suggested_first_name,
            suggested_surname=suggested_surname,
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

    def _create_persona_prompt(
        self,
        demographic: dict[str, Any],
        psychological: dict[str, Any],
        rag_context: str | None = None,
        target_audience_description: str | None = None,
        orchestration_brief: str | None = None  # NOWY PARAMETR - długi brief od Gemini 2.5 Pro
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

        # Unified context section (merge RAG + Target Audience + Orchestration Brief)
        unified_context = ""
        if rag_context or target_audience_description or orchestration_brief:
            context_parts = []

            if rag_context:
                context_parts.append(f"📊 KONTEKST RAG:\n{rag_context}")
            if orchestration_brief and orchestration_brief.strip():
                context_parts.append(f"📋 ORCHESTRATION BRIEF:\n{orchestration_brief.strip()}")
            if target_audience_description and target_audience_description.strip():
                context_parts.append(f"🎯 GRUPA DOCELOWA:\n{target_audience_description.strip()}")

            unified_context = f"""
═══════════════════════════════════════════
KONTEKST (RAG + Brief + Audience):
═══════════════════════════════════════════

{chr(10).join(context_parts)}

⚠️ KLUCZOWE ZASADY:
• Użyj kontekstu jako TŁA życia persony (nie cytuj statystyk!)
• Stwórz FASCYNUJĄCĄ historię - kontekst to fundament, nie lista faktów
• Wskaźniki → konkretne detale życia (housing crisis → wynajmuje, oszczędza)
• Trendy → doświadczenia życiowe (mobilność → zmiana 3 prac w 5 lat)
• Naturalność: "Jak wielu rówieśników..." zamiast "67% absolwentów..."

═══════════════════════════════════════════

"""

        return f"""Expert: Syntetyczne persony dla polskiego rynku - UNIKALNE, REALISTYCZNE, SPÓJNE.

{unified_context}PERSONA #{persona_seed}: {suggested_first_name} {suggested_surname}

PROFIL:
• Wiek: {demographic.get('age_group')} | Płeć: {demographic.get('gender')} | Lokalizacja: {demographic.get('location')}
• Wykształcenie: {demographic.get('education_level')} | Dochód: {demographic.get('income_bracket')}

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
• Detale: dzielnice, marki, konkretne hobby
• UNIKALNOŚĆ: Każda persona MUSI mieć RÓŻNĄ historię życiową - nie kopiuj opisów!
• Background_story NIE może kopiować briefu segmentu ani powtarzać całych akapitów z kontekstu
{headline_age_rule}• Pokaż codzienne wybory i motywacje tej osoby - zero ogólników

⚠️ CATCHY SEGMENT NAME (2-4 słowa):
Wygeneruj krótką, chwytliwą nazwę marketingową dla segmentu tej persony.
• Powinna odzwierciedlać wiek, wartości, styl życia, status ekonomiczny
• Przykłady: "Pasywni Liberałowie", "Młodzi Prekariusze", "Aktywni Seniorzy", "Cyfrowi Nomadzi", "Stabilni Tradycjonaliści"
• UNIKAJ długich opisów technicznych jak "Kobiety 35-44 wyższe wykształcenie"
• Polski język, kulturowo relevantne, konkretne

PRZYKŁAD (z rozbudowanym background_story):
{{"full_name": "Marek Kowalczyk", "catchy_segment_name": "Stabilni Tradycjonaliści", "persona_title": "Główny Księgowy", "headline": "Poznański księgowy (56) planujący emeryturę", "background_story": "Marek zaczął swoją karierę w latach 90., kiedy polska gospodarka przechodziła transformację. Po ukończeniu ekonomii na UAM w Poznaniu, dostał pracę w lokalnej firmie produkcyjnej jako młodszy księgowy. Przez 28 lat z zaangażowaniem budował struktury finansowe firmy, przechodząc od ręcznych ksiąg rachunkowych do nowoczesnych systemów ERP. Pamięta czasy hiperinflacji, kiedy ceny zmieniały się z dnia na dzień - to ukształtowało jego konserwatywne podejście do finansów.\\n\\nW życiu prywatnym stabilność była dla niego priorytetem. Ożenił się z Anną, koleżanką ze studiów, i razem wychowali dwoje dzieci - córkę Kasię (dziś prawniczkę w Warszawie) i syna Tomka (inżyniera w Wrocławiu). Trzy lata temu, po latach oszczędzania, spełnił marzenie i kupił działkę pod Poznaniem. Każdy weekend spędza tam, budując dom na emeryturę - to jego sposób na relaks i ucieczkę od codziennych obowiązków.\\n\\nMarek jest również skarbnikiem parafii w swojej dzielnicy. Pilnuje każdego grosza w budżecie kościoła, co czasami prowadzi do konfliktów z proboszczem, który ma bardziej 'wizjonerskie' podejście do wydatków. Ale Marek nie ustępuje - wie, że jego konserwatywne podejście chroni wspólnotę przed nieprzemyślanymi decyzjami.\\n\\nTeraz, na rok przed emeryturą, Marek czuje mieszankę ulgi i niepokoju. Z jednej strony cieszy się na czas dla siebie, wędkowanie i dokończenie domu. Z drugiej martwi się, czy jego emerytura (około 3500 zł netto) wystarczy na godne życie, zwłaszcza przy rosnącej inflacji. Obserwuje też z niepokojem, jak zmienia się świat - digitalizacja, którą wspierał w firmie, teraz wydaje mu się obca. Często zastanawia się, czy jego dzieci poradzą sobie w tym szybko zmieniającym się świecie.", "values": ["Stabilność", "Lojalność", "Rodzina", "Odpowiedzialność", "Oszczędność"], "interests": ["Wędkarstwo", "Majsterkowanie", "Grillowanie", "Historia Polski", "Budowa domu"], "communication_style": "formalny, face-to-face, ceni bezpośrednie rozmowy", "decision_making_style": "metodyczny, analityczny, unika ryzyka, bazuje na doświadczeniu", "typical_concerns": ["Wysokość emerytury i inflacja", "Zdrowie i dostęp do opieki medycznej", "Przyszłość dzieci", "Zakończenie budowy domu", "Cyfryzacja i nowe technologie"]}}

⚠️ KRYTYCZNE: Generuj KOMPLETNIE INNĄ personę z UNIKALNĄ historią życiową!
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

    # === SEGMENT-BASED ARCHITECTURE ===

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

        # Generate unique persona seed for diversity
        persona_seed = self._rng.integers(1000, 9999)

        # Suggest Polish name
        gender_lower = demographic_profile.get('gender', 'kobieta').lower()
        if 'female' in gender_lower or 'kobieta' in gender_lower:
            suggested_first_name = self._rng.choice(POLISH_FEMALE_NAMES)
        else:
            suggested_first_name = self._rng.choice(POLISH_MALE_NAMES)
        suggested_surname = self._rng.choice(POLISH_SURNAMES)

        # Create prompt with segment context (używając funkcji modułowej)
        prompt_text = create_segment_persona_prompt(
            demographic_profile,
            psychological_profile,
            segment_name,
            segment_context,
            graph_insights,
            rag_citations,
            persona_seed,
            suggested_first_name,
            suggested_surname
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
