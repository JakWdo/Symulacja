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

import asyncio
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from scipy import stats
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.config import get_settings
# NOTE: Imports z constants.py usunięte - demographics teraz z orchestration, nie z sampling
from app.models import Persona
from app.services.core.clients import build_chat_model
from app.core.prompts import (
    COMPREHENSIVE_PERSONA_GENERATION_PROMPT,
    COMPREHENSIVE_PERSONA_GENERATION_SCHEMA,
    COMPREHENSIVE_PERSONA_MODEL_PARAMS,
)

settings = get_settings()

try:  # Opcjonalny import wyjątku z pakietu Google API (może nie być dostępny w testach)
    from google.api_core.exceptions import ServiceUnavailable  # type: ignore
except Exception:  # pragma: no cover - brak zależności w środowisku testowym
    ServiceUnavailable = None  # type: ignore

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
    age_groups: Dict[str, float]        # Grupy wiekowe
    genders: Dict[str, float]           # Płeć
    education_levels: Dict[str, float]  # Poziomy edukacji
    income_brackets: Dict[str, float]   # Przedziały dochodowe
    locations: Dict[str, float]         # Lokalizacje geograficzne


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

    # NOTE: sample_demographic_profile(), _weighted_sample(), _prepare_distribution()
    # zostały USUNIĘTE - demographics teraz pochodzą z orchestration, nie z sampling

    def sample_big_five_traits(self, personality_skew: Dict[str, float] = None) -> Dict[str, float]:
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

    def sample_cultural_dimensions(self) -> Dict[str, float]:
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
        self, demographic: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
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
        demographic_profile: Dict[str, Any],
        psychological_profile: Dict[str, Any],
        use_rag: bool = True,  # NOWY PARAMETR - domyślnie włączony
        advanced_options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
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
        graph_insights = None
        allocation_reasoning = None

        if advanced_options:
            target_audience_desc = advanced_options.get('target_audience_description')
            orchestration_brief = advanced_options.get('orchestration_brief')
            graph_insights = advanced_options.get('graph_insights')
            allocation_reasoning = advanced_options.get('allocation_reasoning')

            if target_audience_desc:
                logger.info(f"Using target audience description: {target_audience_desc[:100]}...")
            if orchestration_brief:
                logger.info(f"Using orchestration brief: {orchestration_brief[:150]}... ({len(orchestration_brief)} chars)")

        # Generuj prompt (z RAG, target audience, i orchestration brief jeśli dostępne)
        prompt_text = self._create_persona_prompt(
            demographic_profile,
            psychological_profile,
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
        demographic: Dict[str, Any],
        psychological: Dict[str, Any],
        rag_context: Optional[str] = None,
        target_audience_description: Optional[str] = None,
        orchestration_brief: Optional[str] = None  # NOWY PARAMETR - długi brief od Gemini 2.5 Pro
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

{unified_context}PERSONA #{persona_seed}

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

ZASADY IMION I NAZWISK:
• Używaj TYPOWYCH POLSKICH imion pasujących do wieku i płci persony
• Przykłady imion: dla 25-34 lat (Julia, Kacper), dla 45-54 lat (Małgorzata, Krzysztof), dla 55+ (Grażyna, Stanisław)
• Nazwiska neutralne, popularne (np. Kowalski, Nowak, Wiśniewski, Kowalczyk)
• Imiona muszą być realistyczne dla Polski 2025 i pasować do pokolenia
• NIE wymyślaj egzotycznych lub nieprawdopodobnych kombinacji

ZASADY ZAWODÓW:
• Zawód = wykształcenie + dochód + brief
• Używaj TYLKO konkretnych, istniejących zawodów w Polsce (nie abstrakcyjnych tytułów)
• Osobowość → historia (O→podróże, S→planowanie)
• Detale: dzielnice, marki, konkretne hobby

PRZYKŁAD:
{{"full_name": "Marek Kowalczyk", "persona_title": "Główny Księgowy", "headline": "Poznański księgowy (56) planujący emeryturę", "background_story": "28 lat w firmie, żonaty, dwoje dorosłych dzieci, kupił działkę pod Poznaniem, skarbnik parafii", "values": ["Stabilność", "Lojalność", "Rodzina", "Odpowiedzialność"], "interests": ["Wędkarstwo", "Majsterkowanie", "Grillowanie"], "communication_style": "formalny, face-to-face", "decision_making_style": "metodyczny, unika ryzyka", "typical_concerns": ["Emerytura", "Sukcesja", "Zdrowie"]}}

Generuj KOMPLETNIE INNĄ personę. WYŁĄCZNIE JSON (bez markdown):
{{
  "full_name": "<polskie imię+nazwisko - typowe dla tego wieku>",
  "persona_title": "<konkretny zawód istniejący w Polsce>",
  "headline": "<1 zdanie: wiek, zawód, motywacje>",
  "background_story": "<2-3 zdania: życie, kariera, kontekst>",
  "values": ["<5-7 wartości - konkretne, życiowe>"],
  "interests": ["<5-7 hobby/aktywności - realistyczne>"],
  "communication_style": "<jak się komunikuje>",
  "decision_making_style": "<jak podejmuje decyzje>",
  "typical_concerns": ["<3-5 zmartwień/priorytetów>"]
}}"""

    def validate_distribution(
        self,
        generated_personas: List[Dict[str, Any]],
        target_distribution: DemographicDistribution,
    ) -> Dict[str, Any]:
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
        self, personas: List[Dict[str, Any]], field: str, expected_dist: Dict[str, float]
    ) -> Dict[str, float]:
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
        demographics_constraints: Dict[str, Any],  # Will be DemographicConstraints from SegmentDefinition
        graph_insights: List[Any] = None,
        rag_citations: List[Any] = None,
        personality_skew: Optional[Dict[str, float]] = None
    ) -> Tuple[str, Dict[str, Any]]:
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

    async def generate_comprehensive_persona(
        self,
        orchestration_brief: str,
        segment_characteristics: List[str],
        demographic_guidance: Dict[str, Any],
        rag_context: Optional[str] = None,
        psychological_profile: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generuj KOMPLETNĄ personę używając comprehensive prompt (LLM generuje ALL DATA).

        Ta metoda różni się od generate_persona_personality():
        - LLM generuje WSZYSTKIE dane razem (demographics + background_story + values + interests)
        - Brak post-processing polonizacji - LLM generuje od razu po polsku
        - demographic_guidance jest tylko sugestią dla LLM, nie requirement
        - Używa structured output dla reliability

        Args:
            orchestration_brief: Brief segmentu z orchestration service (kontekst społeczny)
            segment_characteristics: Lista 4-6 charakterystyk segmentu
            demographic_guidance: Orientacyjne demographics (guidance, nie requirement)
            rag_context: Opcjonalny kontekst z RAG
            psychological_profile: Opcjonalny Big Five + Hofstede (jeśli None → samplingujemy)

        Returns:
            Dict z ALL DATA:
            - Demographics: age, gender, location, education_level, income_bracket, occupation
            - Content: full_name, background_story, values, interests
            - Psychographics: openness, conscientiousness, ... (z psychological_profile)

        Raises:
            ValueError: Jeśli generowanie się nie powiedzie
        """
        import logging
        logger = logging.getLogger(__name__)

        # Sample psychographics jeśli nie podane
        if not psychological_profile:
            psychological_profile = {
                **self.sample_big_five_traits(),
                **self.sample_cultural_dimensions()
            }

        # Format segment characteristics
        segment_chars_text = "\n".join(f"- {char}" for char in segment_characteristics) if segment_characteristics else "Brak dodatkowych charakterystyk"

        # Format demographic guidance
        demographic_guidance_text = (
            f"• Wiek: {demographic_guidance.get('age', 'elastyczny')}\n"
            f"• Płeć: {demographic_guidance.get('gender', 'elastyczna')}\n"
            f"• Lokalizacja: {demographic_guidance.get('location', 'elastyczna')}\n"
            f"• Wykształcenie: {demographic_guidance.get('education_level', 'elastyczne')}\n"
            f"• Dochód: {demographic_guidance.get('income_bracket', 'elastyczny')}"
        )

        # Build prompt
        prompt_text = COMPREHENSIVE_PERSONA_GENERATION_PROMPT.format(
            orchestration_brief=orchestration_brief or "Brak briefu",
            segment_characteristics=segment_chars_text,
            rag_context=rag_context or "Brak kontekstu RAG",
            demographic_guidance=demographic_guidance_text
        )

        try:
            # Build model with structured output
            comprehensive_model = build_chat_model(
                model=settings.PERSONA_GENERATION_MODEL,
                temperature=COMPREHENSIVE_PERSONA_MODEL_PARAMS["temperature"],
                max_tokens=COMPREHENSIVE_PERSONA_MODEL_PARAMS["max_tokens"],
                top_p=COMPREHENSIVE_PERSONA_MODEL_PARAMS["top_p"],
                top_k=COMPREHENSIVE_PERSONA_MODEL_PARAMS["top_k"],
            )

            # Use with_structured_output dla JSON reliability
            structured_model = comprehensive_model.with_structured_output(
                COMPREHENSIVE_PERSONA_GENERATION_SCHEMA
            )

            # Invoke LLM with simple retry logic for transient Gemini failures
            max_attempts = 3
            response: Optional[Dict[str, Any]] = None
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(
                        "Generating comprehensive persona with LLM (attempt %s/%s)...",
                        attempt,
                        max_attempts,
                    )
                    result = await structured_model.ainvoke([
                        {"role": "system", "content": "Jesteś ekspertem od badań rynkowych tworzącym realistyczne syntetyczne persony dla polskiego rynku."},
                        {"role": "user", "content": prompt_text}
                    ])
                except Exception as invoke_exc:  # pragma: no cover - zależne od klienta Gemini
                    if attempt < max_attempts and self._is_retryable_gemini_error(invoke_exc):
                        logger.warning(
                            "Gemini API call failed (attempt %s/%s): %s. Retrying...",
                            attempt,
                            max_attempts,
                            invoke_exc,
                        )
                        last_exception = invoke_exc
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    raise

                if isinstance(result, dict):
                    response = result
                    break

                if result is None and attempt < max_attempts:
                    logger.warning(
                        "Structured output zwrócił None (attempt %s/%s). Retrying...",
                        attempt,
                        max_attempts,
                    )
                    await asyncio.sleep(0.5 * attempt)
                    continue

                raise ValueError(f"Expected dict from structured output, got {type(result)}")

            if response is None:
                if last_exception:
                    raise ValueError(f"Failed to generate comprehensive persona after retries: {last_exception}") from last_exception
                raise ValueError("Expected dict from structured output, got <class 'NoneType'>")

            # Normalizuj gender do standardowego formatu (case-insensitive, obsługa wariantów)
            if 'gender' in response:
                gender_raw = str(response['gender']).strip().lower()
                if gender_raw in ['kobieta', 'woman', 'female', 'f']:
                    response['gender'] = 'Kobieta'
                elif gender_raw in ['mężczyzna', 'mezczyzna', 'man', 'male', 'm']:
                    response['gender'] = 'Mężczyzna'
                else:
                    # Fallback do capitalize jeśli nieznany format
                    response['gender'] = response['gender'].capitalize()

            # Dodaj psychographics do response
            response.update(psychological_profile)

            # Dodaj persona_title jako alias dla occupation (backward compatibility)
            if 'occupation' in response and 'persona_title' not in response:
                response['persona_title'] = response['occupation']

            # Dodaj headline jeśli brakuje (fallback)
            if 'headline' not in response or not response.get('headline'):
                response['headline'] = f"{response.get('full_name', 'Persona')}, {response.get('age', '?')} lat - {response.get('occupation', 'Zawód')}"

            logger.info(
                f"✅ Comprehensive persona generated: {response.get('full_name')} "
                f"({response.get('age')} lat, {response.get('gender')}, {response.get('location')})"
            )

            return response

        except Exception as e:
            logger.error(f"❌ Failed to generate comprehensive persona: {e}", exc_info=True)
            raise ValueError(f"Failed to generate comprehensive persona: {e}")

    @staticmethod
    def _is_retryable_gemini_error(exc: Exception) -> bool:
        """Heurystycznie określ, czy błąd Gemini warto spróbować ponowić."""
        if ServiceUnavailable is not None and isinstance(exc, ServiceUnavailable):
            return True

        message = str(exc).lower()
        retry_markers = (
            "503",
            "service unavailable",
            "temporarily overloaded",
            "retry later",
        )
        return any(marker in message for marker in retry_markers)

    def _create_segment_persona_prompt(
        self,
        demographic: Dict[str, Any],
        psychological: Dict[str, Any],
        segment_name: str,
        segment_context: str,
        graph_insights: List[Any],
        rag_citations: List[Any]
    ) -> str:
        """Create prompt for segment-based persona generation."""

        age = demographic.get('age', 30)
        gender = demographic.get('gender', 'kobieta')

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
• Płeć: {gender}
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

ZASADY IMION:
• Używaj TYPOWYCH POLSKICH imion pasujących do wieku {age} lat i płci {gender}
• Przykłady: dla 25-34 lat (Julia, Kacper), dla 45-54 lat (Małgorzata, Krzysztof)
• Nazwiska popularne (Kowalski, Nowak, Wiśniewski)

ZASADY:
• Persona MUSI pasować do constraints
• Zawód = wykształcenie + dochód + kontekst segmentu
• Używaj kontekstu jako tła (nie cytuj statystyk!)

ZWRÓĆ JSON:
{{
  "full_name": "<typowe polskie imię+nazwisko dla tego wieku i płci>",
  "persona_title": "<konkretny zawód>",
  "headline": "<{age} lat, zawód, motywacje>",
  "background_story": "<2-3 zdania>",
  "values": ["<5-7 wartości>"],
  "interests": ["<5-7 hobby>"],
  "communication_style": "<styl>",
  "decision_making_style": "<styl>",
  "typical_concerns": ["<3-5 zmartwień>"]
}}"""
