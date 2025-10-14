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

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from scipy import stats
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.config import get_settings
from app.core.constants import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    DEFAULT_EDUCATION_LEVELS,
    DEFAULT_INCOME_BRACKETS,
    DEFAULT_LOCATIONS,
    POLISH_LOCATIONS,
    POLISH_VALUES,
    POLISH_INTERESTS,
    POLISH_COMMUNICATION_STYLES,
    POLISH_DECISION_STYLES,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
    POLISH_MALE_NAMES,
    POLISH_FEMALE_NAMES,
    POLISH_SURNAMES,
)
from app.models import Persona

settings = get_settings()

# Import RAG service (opcjonalny - tylko jeśli RAG włączony)
try:
    if settings.RAG_ENABLED:
        from app.services.rag_service import PolishSocietyRAG
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

        self.llm = ChatGoogleGenerativeAI(
            model=persona_model,
            google_api_key=settings.GOOGLE_API_KEY,
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

    def sample_demographic_profile(
        self, distribution: DemographicDistribution, n_samples: int = 1
    ) -> List[Dict[str, Any]]:
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
            # Normalizuj każdy rozkład lub użyj wartości domyślnych
            age_groups = self._prepare_distribution(
                distribution.age_groups, DEFAULT_AGE_GROUPS
            )
            genders = self._prepare_distribution(distribution.genders, DEFAULT_GENDERS)
            education_levels = self._prepare_distribution(
                distribution.education_levels, DEFAULT_EDUCATION_LEVELS
            )
            income_brackets = self._prepare_distribution(
                distribution.income_brackets, DEFAULT_INCOME_BRACKETS
            )
            locations = self._prepare_distribution(
                distribution.locations, DEFAULT_LOCATIONS
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

    def _weighted_sample(self, distribution: Dict[str, float]) -> str:
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

    def _prepare_distribution(
        self, distribution: Dict[str, float], fallback: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Przygotuj i znormalizuj rozkład prawdopodobieństw

        Sprawdza czy rozkład jest poprawny, normalizuje go do sumy 1.0,
        lub zwraca fallback jeśli rozkład jest niepoprawny.

        Dodatkowo: jeśli fallback to DEFAULT_LOCATIONS, DEFAULT_INCOME_BRACKETS
        lub DEFAULT_EDUCATION_LEVELS, zamienia na polskie odpowiedniki.

        Args:
            distribution: Rozkład do znormalizowania
            fallback: Rozkład domyślny używany gdy distribution jest pusty/błędny

        Returns:
            Znormalizowany rozkład (suma = 1.0) lub fallback
        """
        if not distribution:
            # Użyj polskich wartości domyślnych jeśli fallback jest anglojęzyczny
            if fallback is DEFAULT_LOCATIONS:
                fallback = POLISH_LOCATIONS
            elif fallback is DEFAULT_INCOME_BRACKETS:
                fallback = POLISH_INCOME_BRACKETS
            elif fallback is DEFAULT_EDUCATION_LEVELS:
                fallback = POLISH_EDUCATION_LEVELS
            return fallback
        total = sum(distribution.values())
        if total <= 0:
            # Użyj polskich wartości domyślnych jeśli fallback jest anglojęzyczny
            if fallback is DEFAULT_LOCATIONS:
                fallback = POLISH_LOCATIONS
            elif fallback is DEFAULT_INCOME_BRACKETS:
                fallback = POLISH_INCOME_BRACKETS
            elif fallback is DEFAULT_EDUCATION_LEVELS:
                fallback = POLISH_EDUCATION_LEVELS
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
                    "graph_nodes_count": len(rag_data.get('graph_nodes', [])),
                    "graph_nodes": rag_data.get('graph_nodes', []),
                    "graph_context": rag_data.get('graph_context', ''),
                    "enriched_chunks": sum(
                        1 for c in rag_data.get('citations', [])
                        if c.get('enriched', False)
                    )
                }

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
        - Opcjonalny orchestration brief (2000-3000 znaków) od Gemini 2.5 Pro
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

        # Wskazówki do interpretacji cech osobowości (PO POLSKU)
        openness_val = psychological.get('openness', 0.5)
        conscientiousness_val = psychological.get('conscientiousness', 0.5)
        extraversion_val = psychological.get('extraversion', 0.5)
        agreeableness_val = psychological.get('agreeableness', 0.5)
        neuroticism_val = psychological.get('neuroticism', 0.5)

        openness_hint = "kreatywna, ciekawa świata, otwarta na nowe doświadczenia" if openness_val > 0.6 else "praktyczna, tradycyjna, preferuje rutynę" if openness_val < 0.4 else "umiarkowanie otwarta"
        conscientiousness_hint = "zorganizowana, zdyscyplinowana, skrupulatna" if conscientiousness_val > 0.6 else "spontaniczna, elastyczna, mniej uporządkowana" if conscientiousness_val < 0.4 else "zbalansowana w planowaniu"
        extraversion_hint = "towarzyska, energiczna, lubi ludzi" if extraversion_val > 0.6 else "powściągliwa, introwertyczna, preferuje samotność" if extraversion_val < 0.4 else "ambiwertysta"
        agreeableness_hint = "współpracująca, empatyczna, życzliwa" if agreeableness_val > 0.6 else "konkurencyjna, bezpośrednia, sceptyczna" if agreeableness_val < 0.4 else "zbalansowane podejście społeczne"
        neuroticism_hint = "nerwowa, wrażliwa, podatna na stres" if neuroticism_val > 0.6 else "spokojna, odporna, stabilna emocjonalnie" if neuroticism_val < 0.4 else "umiarkowanie emocjonalna"

        # Sekcja RAG context (jeśli dostępna)
        rag_section = ""
        if rag_context:
            rag_section = f"""
═══════════════════════════════════════════════════════════════════════════════
KONTEKST Z BAZY WIEDZY O POLSKIM SPOŁECZEŃSTWIE:
═══════════════════════════════════════════════════════════════════════════════

{rag_context}

⚠️ KRYTYCZNE INSTRUKCJE WYKORZYSTANIA KONTEKSTU:

1. **NATURALNOŚĆ**: NIE cytuj statystyk bezpośrednio w opisach
   - ❌ ZŁE: "Należy do 67% absolwentów..."
   - ✅ DOBRE: "Jak wielu jej rówieśników z wyższym wykształceniem, zmaga się z..."
   - Użyj wskaźników jako TŁEM dla życia persony, nie jako faktów do cytowania

2. **CIEKAWOŚĆ**: Twórz FASCYNUJĄCE historie życia
   - Wykorzystaj obserwacje demograficzne jako INSPIRACJĘ do szczegółów
   - Przykład: Jeśli kontekst mówi o "wysokiej mobilności zawodowej"
     → Persona może mieć historię zmiany 3 prac w ciągu 5 lat z konkretnymi powodami

3. **KONTEKST CZASOWY**: Osadź personę w trendach bez nazywania ich
   - ❌ ZŁE: "Obserwuje trend wzrostu cen mieszkań w latach 2018-2023"
   - ✅ DOBRE: "Odkąd 5 lat temu przeprowadziła się do Warszawy, ceny mieszkań podwoiły się"

4. **AUTENTYCZNOŚĆ**: Persona ma WŁASNE doświadczenia odzwierciedlające dane
   - Jeśli wskaźniki pokazują problem (np. trudności finansowe młodych)
   - Persona ma KONKRETNE przykłady tego w życiu (mieszka z rodzicami, spłaca kredyt)

5. **SPÓJNOŚĆ Z DANYMI**: Wszystkie szczegóły PASUJĄ do kontekstu
   - Dochody, wartości, zainteresowania, concerns MUSZĄ być zgodne z danymi demograficznymi
   - Ale przedstawione jako CZĘŚĆ ŻYCIA persony, nie jako cytaty ze statystyk

💡 PAMIĘTAJ: Czytelnicy chcą poznać PRAWDZIWĄ OSOBĘ, nie raport statystyczny.
Użyj danych jako fundamentu, ale zbuduj na nich ŻYWĄ, INTERESUJĄCĄ postać.

═══════════════════════════════════════════════════════════════════════════════

"""

        # Sekcja dodatkowego opisu grupy docelowej (jeśli dostępny)
        target_audience_section = ""
        if target_audience_description and target_audience_description.strip():
            target_audience_section = f"""
═══════════════════════════════════════════════════════════════════════════════
DODATKOWY OPIS GRUPY DOCELOWEJ:
═══════════════════════════════════════════════════════════════════════════════

{target_audience_description.strip()}

⚠️ WAŻNE: Ta persona MUSI odpowiadać powyższemu opisowi grupy docelowej.
Upewnij się, że cechy, zainteresowania, wartości i styl życia persony są
zgodne z tym opisem.

═══════════════════════════════════════════════════════════════════════════════

"""

        # Sekcja orchestration brief (jeśli dostępny) - DŁUGI edukacyjny brief od Gemini 2.5 Pro
        orchestration_section = ""
        if orchestration_brief and orchestration_brief.strip():
            orchestration_section = f"""
═══════════════════════════════════════════════════════════════════════════════
📋 ORCHESTRATION BRIEF (od Gemini 2.5 Pro - Szczegółowy Kontekst Społeczny)
═══════════════════════════════════════════════════════════════════════════════

{orchestration_brief.strip()}

⚠️ KRYTYCZNE INSTRUKCJE WYKORZYSTANIA BRIEFU:

1. **TO JEST TWÓJ FUNDAMENT**: Ten brief zawiera głęboką socjologiczną analizę
   grupy demograficznej do której należy ta persona. Przeczytaj go UWAŻNIE.

2. **NATURALNOŚĆ W OPISIE**: NIE cytuj briefu dosłownie w background_story!
   - ❌ ZŁE: "Według briefu, ta grupa stanowi 17.3% populacji..."
   - ✅ DOBRE: "Jak wielu jej rówieśników w Warszawie, zmaga się z wysokimi cenami mieszkań..."

3. **UŻYJ JAKO TŁA**: Brief wyjaśnia DLACZEGO ta persona jest taka jaka jest.
   - Wskaźniki z briefu (78.4% zatrudnienia, 63% mobilność) = kontekst życia persony
   - Wartości opisane w briefie (work-life balance, rozwój) = wartości persony
   - Wyzwania z briefu (housing crisis, burnout) = konkretne problemy w życiu persony

4. **CIEKAWA HISTORIA ŻYCIA**: Użyj insights z briefu aby stworzyć FASCYNUJĄCĄ personę
   - Brief mówi o "mobilności zawodowej" → Persona może mieć historię zmiany 3 prac
   - Brief mówi o "cenach mieszkań" → Persona wynajmuje, oszczędza, ma konkretne plany
   - Brief mówi o "work-life balance" → Persona ma hobby, boundaries, mindfulness

5. **SPÓJNOŚĆ Z BRIEFEM**: Każdy szczegół życia persony MUSI pasować do briefu
   - Dochody, zawód, lokalizacja, wartości, zainteresowania = zgodne z kontekstem
   - Ale przedstawione jako ŻYCIE PERSONY, nie jako statystyki

💡 PAMIĘTAJ: Brief to mapa społeczna. Ty tworzysz KONKRETNĄ OSOBĘ która żyje w tym społeczeństwie.
Czytelnicy chcą poznać FASCYNUJĄCĄ POSTAĆ, która jest autentyczna bo odzwierciedla realne
trendy społeczne.

═══════════════════════════════════════════════════════════════════════════════

"""

        return f"""Jesteś ekspertem od badań rynkowych tworzącym syntetyczne persony dla polskiego rynku. Twoje persony muszą być UNIKALNE, REALISTYCZNE i WEWNĘTRZNIE SPÓJNE, odzwierciedlające POLSKIE SPOŁECZEŃSTWO.

{orchestration_section}{rag_section}{target_audience_section}
PERSONA #{persona_seed}
SUGEROWANE IMIĘ I NAZWISKO: {suggested_first_name} {suggested_surname} (możesz użyć lub wybrać inne polskie)

PROFIL DEMOGRAFICZNY:
- Grupa wiekowa: {demographic.get('age_group')}
- Płeć: {demographic.get('gender')}
- Wykształcenie: {demographic.get('education_level')}
- Przedział dochodowy: {demographic.get('income_bracket')}
- Lokalizacja: {demographic.get('location')}

CECHY OSOBOWOŚCI (Big Five):
- Otwartość: {openness_val:.2f} → {openness_hint}
- Sumienność: {conscientiousness_val:.2f} → {conscientiousness_hint}
- Ekstrawersja: {extraversion_val:.2f} → {extraversion_hint}
- Ugodowość: {agreeableness_val:.2f} → {agreeableness_hint}
- Neurotyzm: {neuroticism_val:.2f} → {neuroticism_hint}

WYMIARY KULTUROWE (Hofstede):
- Dystans władzy: {psychological.get('power_distance', 0.5):.2f}
- Indywidualizm: {psychological.get('individualism', 0.5):.2f}
- Unikanie niepewności: {psychological.get('uncertainty_avoidance', 0.5):.2f}

KRYTYCZNE INSTRUKCJE DLA POLSKIEJ PERSONY:
1. Persona MUSI być UNIKALNA - unikaj ogólnych opisów
2. Imię i nazwisko MUSI być POLSKIE (Jan Kowalski, Anna Nowak, Piotr Zieliński, Maria Wiśniewska)
3. Lokalizacja MUSI być polska (Warszawa, Kraków, Wrocław, Gdańsk, inne polskie miasta)
4. Wiek ma znaczenie: 25-latek i 65-latek mają BARDZO różne konteksty życiowe
5. Zawód zgodny z wykształceniem i poziomem dochodów (typowe polskie zawody)
6. Historia życiowa zgodna z cechami osobowości:
   - Wysoka Otwartość → podróże, kreatywne hobby, różnorodne doświadczenia
   - Wysoka Sumienność → uporządkowana ścieżka kariery, planowanie
   - Wysoka Ekstrawersja → aktywności społeczne, networking
   - Niska Ugodowość → zawody konkurencyjne, niezależna praca
   - Wysoki Indywidualizm → przedsiębiorczość, samodzielność
7. Bądź KONKRETNY: nazwij dzielnice miast, konkretne polskie marki, prawdziwe hobby

PRZYKŁADY FEW-SHOT (POLSKIE PERSONY):

Przykład 1 (Wysoka otwartość, kreatywny zawód w średniej karierze):
{{
  "full_name": "Katarzyna Lewandowska",
  "persona_title": "Freelance UX Designer",
  "headline": "Krakowska designerka eksperymentująca z dostępnością cyfrową i zero waste.",
  "background_story": "Kasia ma 32 lata i mieszka w Krakowie na Kazimierzu. Po ASP i 5 latach w agencji przeszła na freelancing 3 lata temu. Obecnie projektuje interfejsy dla polskich startupów i zagranicznych klientów, uczy się Swift, a weekendy spędza na wspinaczce w Tatrach. Singielka ciesząca się wolnością wyboru projektów od sustainable fashion po edtech.",
  "values": ["Kreatywność", "Niezależność", "Ciągły rozwój", "Autentyczność", "Ekologia", "Równowaga praca-życie"],
  "interests": ["Wspinaczka górska", "Design dostępny (a11y)", "Festiwale muzyczne (Opener, OFF)", "Kawiarnie specialty coffee", "Zero waste", "Sketching w plenerze"],
  "communication_style": "entuzjastyczna i wizualna, używa metafor i przykładów z różnych dziedzin, preferuje Slack i Figma",
  "decision_making_style": "intuicyjna z research; testuje pomysły szybko przez prototypy i MVP",
  "typical_concerns": ["Utrzymanie wolności twórczej przy stabilności finansowej", "Znalezienie sensownych projektów", "Balansowanie samotnej pracy z potrzebą kontaktu społecznego", "Brak pewności socjalnej (ZUS, urlop)"]
}}

Przykład 2 (Niska otwartość, wysoka sumienność, zbliżający się do emerytury):
{{
  "full_name": "Marek Kowalczyk",
  "persona_title": "Doświadczony Główny Księgowy",
  "headline": "Poznański księgowy skrupulatnie planujący emeryturę i mentorujący młodsze pokolenie.",
  "background_story": "Marek ma 56 lat i pracuje w tej samej firmie produkcyjnej od 28 lat. Żonaty, dwoje dorosłych dzieci (syn lekarz, córka nauczycielka). Kupił niedawno działkę pod Poznaniem i planuje emeryturę za 6 lat. Jest skarbnikiem parafii, dumny ze swojej przewidywalnej rutyny i relacji z klientami budowanych przez dekady.",
  "values": ["Stabilność", "Lojalność", "Rodzina", "Odpowiedzialność", "Tradycja", "Uczciwość"],
  "interests": ["Wędkarstwo nad Wartą", "Majsterkowanie i renowacja domu", "Podcasty o finansach osobistych", "Grillowanie", "Działalność parafialna", "Chór kościelny"],
  "communication_style": "formalny i profesjonalny, preferuje spotkania twarzą w twarz, używa sprawdzonych schematów",
  "decision_making_style": "metodyczny i unikający ryzyka, opiera się na sprawdzonych metodach i dokładnym planowaniu",
  "typical_concerns": ["Zapewnienie wystarczającej emerytury", "Utrzymanie relacji z klientami przez sukcesję", "Zdrowie i opieka medyczna na emeryturze", "Planowanie spadku dla dzieci"]
}}

Przykład 3 (Wysoka ekstrawersja, wysoki neurotyzm, świeży absolwent):
{{
  "full_name": "Julia Nowicka",
  "persona_title": "Social Media Manager & Content Creator",
  "headline": "Warszawska marketerka Z-ki walcząca z niepewnością kariery w creator economy.",
  "background_story": "Julia ma 25 lat i niedawno skończyła marketing na SGH. Mieszka z trzema współlokatorkami na Mokotowie, pracuje jako social media manager w agencji beauty. Balansuje między lękiem o stabilność pracy a ekscytacją gospodarką twórców. Stale networkuje na eventach branżowych budując markę osobistą jako Gen-Z marketing consultant. Rodzice z Radomia nie do końca rozumieją jej wybór kariery.",
  "values": ["Relacje", "Rozpoznawalność", "Autentyczność", "Innowacja", "Rodzina", "Sukces zawodowy"],
  "interests": ["Tworzenie contentu TikTok/Instagram", "Eventy networkingowe", "Kultura brunchowa", "Secondhandy (Vinted, lumpeksy)", "Słuchanie podcastów", "Mental health awareness", "K-pop"],
  "communication_style": "energiczna i świadoma trendów, używa slangu social media, bardzo ekspresywna z emoji",
  "decision_making_style": "impulsywna ale kolaboratywna, szuka walidacji od rówieśników przed zobowiązaniem",
  "typical_concerns": ["Pewność pracy w niestabilnej branży", "Kredyt studencki do spłaty", "Lęk porównawczy z social media", "Udowodnienie wyboru kariery rodzicom", "Budowanie zrównoważonego dochodu", "Wysokie ceny wynajmu w Warszawie"]
}}

Teraz wygeneruj KOMPLETNIE INNĄ personę zachowując ten sam poziom szczegółowości i spójności z podanym profilem demograficznym i psychologicznym.

Generuj WYŁĄCZNIE JSON (bez markdown, bez dodatkowego tekstu):
{{
  "full_name": "<realistyczne polskie imię i nazwisko pasujące do lokalizacji>",
  "persona_title": "<zwięzły tytuł zawodowy lub etapu życia>",
  "headline": "<jedno zdanie podsumowujące spójne z wiekiem, zawodem i motywacjami>",
  "background_story": "<2-3 konkretne zdania o ich obecnym życiu, ścieżce kariery i unikalnym kontekście>",
  "values": ["<5-7 konkretnych wartości które kierują ich decyzjami>"],
  "interests": ["<5-7 konkretnych hobby/aktywności które faktycznie uprawiają>"],
  "communication_style": "<jak się wyrażają i komunikują>",
  "decision_making_style": "<jak podchodzą do ważnych wyborów>",
  "typical_concerns": ["<3-5 konkretnych zmartwień lub priorytetów na obecnym etapie życia>"]
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
