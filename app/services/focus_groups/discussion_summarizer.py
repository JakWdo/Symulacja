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
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import FocusGroup, PersonaResponse, Persona, Project
from app.services.shared.clients import build_chat_model
from app.services.dashboard.insight_traceability_service import InsightTraceabilityService
from app.services.dashboard.usage_logging import log_usage_from_metadata, UsageLogContext
from app.services.dashboard.cache_invalidation import invalidate_dashboard_cache

settings = get_settings()
logger = logging.getLogger(__name__)

# Słowa kluczowe do analizy sentymentu
_POSITIVE_WORDS = {
    "good", "great", "excellent", "love", "like", "enjoy", "positive",
    "amazing", "wonderful", "fantastic", "best", "happy", "yes", "agree",
    "excited", "helpful", "valuable", "useful"
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "hate", "dislike", "awful", "worst", "negative",
    "horrible", "poor", "no", "disagree", "concern", "worried", "against",
    "confusing", "hard", "difficult"
}

_BULLET_PREFIX_RE = re.compile(r"^[-*•\d\.\)\s]+")
_SEGMENT_LINE_RE = re.compile(r"\*\*(.+?)\*\*\s*[:\-–]\s*(.+)")

# Polish NLP Support - Stopwords
# ==============================
# Try to load NLTK stopwords, fallback to hardcoded list if not available
try:
    import nltk
    from nltk.corpus import stopwords
    _NLTK_AVAILABLE = True
    try:
        _POLISH_STOPWORDS_NLTK = set(stopwords.words('polish'))
        _ENGLISH_STOPWORDS_NLTK = set(stopwords.words('english'))
    except LookupError:
        # NLTK data not downloaded - NLTK dependency removed
        logger.warning("NLTK stopwords data not found (NLTK dependency removed)")
        _NLTK_AVAILABLE = False
        _POLISH_STOPWORDS_NLTK = set()
        _ENGLISH_STOPWORDS_NLTK = set()
except ImportError:
    _NLTK_AVAILABLE = False
    _POLISH_STOPWORDS_NLTK = set()
    _ENGLISH_STOPWORDS_NLTK = set()

# Comprehensive Polish stopwords (custom + NLTK)
_POLISH_STOPWORDS_CUSTOM = {
    # Pronouns
    "ja", "ty", "on", "ona", "ono", "my", "wy", "oni", "one",
    "mnie", "cię", "go", "ją", "nas", "was", "ich", "sobie", "się",
    "moja", "mój", "moje", "twoja", "twój", "twoje", "jego", "jej",
    # Prepositions
    "w", "z", "do", "od", "na", "po", "o", "u", "przy", "przez",
    "za", "dla", "nad", "pod", "przed", "między", "bez",
    # Conjunctions
    "i", "a", "ale", "oraz", "czy", "że", "jeśli", "gdyby", "bo",
    "więc", "zatem", "jednak", "ponieważ", "dlatego",
    # Verbs (common forms)
    "jest", "są", "był", "była", "było", "byli", "były", "być",
    "mieć", "ma", "mają", "miał", "miała", "miało", "mieli", "miały",
    "może", "mogą", "mógł", "mogła", "mogło", "mogli", "mogły",
    "chce", "chcą", "chciał", "chciała", "chciało", "chcieli", "chciały",
    "wie", "wiedzą", "wiedział", "wiedziała", "wiedziało", "wiedzieli", "wiedziały",
    # Articles & particles
    "ten", "ta", "to", "te", "ci", "tego", "tej", "tych",
    "jeden", "jedna", "jedno", "jedni", "jedne",
    "żaden", "żadna", "żadne", "żadni", "żadne",
    "każdy", "każda", "każde", "wszyscy", "wszystkie",
    "który", "która", "które", "którzy", "których",
    "jaki", "jaka", "jakie", "jacy", "jakich",
    "taki", "taka", "takie", "tacy", "takich",
    "ile", "ilu", "gdzie", "kiedy", "jak", "dlaczego", "czemu",
    # Adverbs
    "tu", "tutaj", "tam", "tu", "teraz", "wtedy", "zawsze", "nigdy",
    "często", "rzadko", "czasami", "bardzo", "mało", "dużo", "zbyt",
    "bardziej", "mniej", "najbardziej", "najmniej", "też", "także", "również",
    # Common verbs (infinitive)
    "robić", "zrobić", "mówić", "powiedzieć", "iść", "pójść",
    # Numbers
    "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć", "dziesięć",
    # Common words that appear in concepts but are not meaningful
    "brak", "czas", "czasu", "czasów", "razy", "rok", "roku", "lat",
    "sposób", "sposób", "sposobu", "sposobów", "rzecz", "rzeczy",
    "część", "części", "miejsce", "miejsca", "dane", "danych",
    "np", "itp", "itd", "tzn", "tj", "tzw",
}

# English stopwords (basic set + common words)
_ENGLISH_STOPWORDS_CUSTOM = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "could", "may", "might", "can", "this", "that", "these", "those",
    "it", "its", "he", "she", "they", "them", "their", "his", "her",
    "from", "as", "not", "all", "any", "some", "such", "no", "yes",
    "more", "most", "less", "very", "so", "just", "than", "too",
    "there", "here", "when", "where", "why", "how", "what", "which",
}

# Combine all stopwords
_ALL_STOPWORDS = (
    _POLISH_STOPWORDS_CUSTOM
    | _ENGLISH_STOPWORDS_CUSTOM
    | _POLISH_STOPWORDS_NLTK
    | _ENGLISH_STOPWORDS_NLTK
)

# Polish suffix patterns for pseudo-lemmatization
_POLISH_SUFFIXES = [
    # Genitive plural
    "ów", "ami", "ach",
    # Adjective endings
    "ego", "ymi", "ymi", "owej", "owych",
    # Common verb endings
    "ać", "ić", "yć", "eć",
    # Common noun endings
    "ami", "ach", "iej",
]


def detect_input_language(text: str) -> str:
    """
    Wykrywa język z tekstu input (prosty heurystyczny detektor).

    Algorytm:
    1. Zlicza wystąpienia polskich stopwords (jak, co, jest, się, czy, ...)
    2. Zlicza wystąpienia angielskich stopwords (what, how, is, are, ...)
    3. Porównuje liczności i wybiera język z większą liczbą trafień
    4. Fallback: polski (domyślny język produktu)

    Args:
        text: Tekst do analizy (questions/messages z focus group)

    Returns:
        'pl' lub 'en'

    Note:
        To jest prosty heurystyczny detektor. W przyszłości można użyć biblioteki
        jak langdetect, ale dla dwóch języków (pl/en) ta metoda jest wystarczająca.

    Examples:
        >>> detect_input_language("Jak oceniasz ten produkt?")
        'pl'
        >>> detect_input_language("What do you think about this product?")
        'en'
        >>> detect_input_language("xyz123")  # unclear text
        'pl'
    """
    # Polski stopwords (niektóre z listy POLISH_STOPWORDS)
    polish_indicators = [
        'jak', 'co', 'jest', 'się', 'czy', 'nie', 'ale', 'to', 'że', 'do',
        'z', 'na', 'i', 'w', 'o', 'dla', 'po', 'przez', 'od', 'kiedy',
        'dlaczego', 'gdzie', 'który', 'jakie', 'jaką', 'jaką', 'które',
        'czym', 'czemu', 'kto', 'kim', 'kogo', 'was', 'nas', 'mnie', 'cię',
        'możesz', 'możemy', 'powinien', 'powinna', 'powinno', 'chcesz',
        'chcemy', 'myślisz', 'uważasz', 'uważam', 'myślę', 'sądzisz',
    ]

    # Anglojęzyczne stopwords
    english_indicators = [
        'what', 'how', 'why', 'where', 'when', 'who', 'which', 'is', 'are',
        'the', 'and', 'but', 'that', 'this', 'with', 'for', 'from', 'about',
        'would', 'should', 'could', 'have', 'has', 'do', 'does', 'did',
        'your', 'you', 'we', 'they', 'them', 'think', 'believe', 'feel',
        'can', 'will', 'must', 'may', 'might',
    ]

    text_lower = text.lower()
    # Usuń znaki interpunkcyjne i podziel na słowa
    import re
    words = re.findall(r'\b[a-ząćęłńóśźż]+\b', text_lower, flags=re.UNICODE)

    # Zlicz dokładne dopasowania słów kluczowych (nie substrings!)
    polish_count = sum(1 for word in words if word in polish_indicators)
    english_count = sum(1 for word in words if word in english_indicators)

    logger.debug(f"Language detection: PL={polish_count}, EN={english_count} (sample: {text[:100]}...)")

    # Jeśli więcej polskich słów → polski
    if polish_count > english_count:
        return 'pl'
    # Jeśli więcej angielskich słów → angielski
    elif english_count > polish_count:
        return 'en'

    # Default: polski (dla polskiego produktu)
    return 'pl'


def _normalize_polish_word(word: str) -> str:
    """
    Pseudo-lematyzacja dla polskich słów.

    Usuwa najczęstsze końcówki fleksyjne, aby zredukować warianty tego samego słowa.
    UWAGA: To bardzo prosta heurystyka, nie zastępuje prawdziwej lematyzacji.

    Args:
        word: Słowo do normalizacji

    Returns:
        Znormalizowane słowo
    """
    word = word.lower()

    # Skip very short words
    if len(word) <= 3:
        return word

    # Try removing common suffixes
    for suffix in _POLISH_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            # Keep at least 3 characters after removing suffix
            normalized = word[:-len(suffix)]
            if len(normalized) >= 3:
                return normalized

    return word


def _simple_sentiment_score(text: str) -> float:
    """
    Prosta analiza sentymentu na podstawie słów kluczowych

    Algorytm:
    1. Liczy wystąpienia słów pozytywnych (POSITIVE_WORDS)
    2. Liczy wystąpienia słów negatywnych (NEGATIVE_WORDS)
    3. Oblicza score = (pozytywne - negatywne) / wszystkie

    Args:
        text: Tekst do analizy

    Returns:
        Wartość od -1.0 (czysto negatywny) do 1.0 (czysto pozytywny)
        0.0 = neutralny lub brak słów kluczowych
    """
    lowered = text.lower()
    pos = sum(1 for token in _POSITIVE_WORDS if token in lowered)
    neg = sum(1 for token in _NEGATIVE_WORDS if token in lowered)
    total = pos + neg
    if total == 0:
        return 0.0
    return float((pos - neg) / total)


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
        self.settings = settings

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
        discussion_data = self._prepare_discussion_data(
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
        detected_language = detect_input_language(sample_text)

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
        prompt_variables = self._prepare_prompt_variables(
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
                print(f"Warning: Failed to log token usage: {e}")

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
        created_insights = await self._store_insights_from_summary(
            db=db,
            focus_group=focus_group,
            parsed_summary=parsed_summary,
            prompt_text=prompt_text,
        )

        # Invalidate dashboard cache if insights were created
        if created_insights and user_id:
            try:
                await invalidate_dashboard_cache(user_id)
                logger.debug(f"Dashboard cache invalidated after creating {len(created_insights)} insights")
            except Exception as e:
                logger.warning(f"Failed to invalidate dashboard cache: {e}")

        return parsed_summary

    def _prepare_discussion_data(
        self,
        focus_group: FocusGroup,
        responses: list[PersonaResponse],
        personas: dict[str, Persona],
        include_demographics: bool,
    ) -> dict[str, Any]:
        """
        Przygotowuje ustrukturyzowane dane dyskusji do analizy AI

        Proces:
        1. Grupuje odpowiedzi po pytaniach (każde pytanie ma listę odpowiedzi)
        2. Dla każdej odpowiedzi oblicza sentiment score
        3. Dodaje dane demograficzne persony (jeśli include_demographics=True)
        4. Agreguje statystyki demograficzne całej grupy

        Args:
            focus_group: Obiekt grupy fokusowej
            responses: Lista wszystkich odpowiedzi person
            personas: Słownik {persona_id: Persona}
            include_demographics: Czy dodać dane demograficzne

        Returns:
            Słownik z danymi:
            {
                "topic": str,
                "description": str,
                "responses_by_question": {
                    "Question 1?": [
                        {"response": str, "sentiment": float, "demographics": {...}},
                        ...
                    ]
                },
                "demographic_summary": {
                    "age_range": "25-65",
                    "gender_distribution": {"male": 5, "female": 5},
                    "education_levels": ["Bachelor's", "Master's"],
                    "sample_size": 10
                },
                "total_responses": int
            }
        """

        # Grupuj odpowiedzi po pytaniach
        responses_by_question = {}
        for response in responses:
            if response.question_text not in responses_by_question:
                responses_by_question[response.question_text] = []

            persona = personas.get(str(response.persona_id))
            response_data = {
                "response": response.response_text,
                "sentiment": _simple_sentiment_score(response.response_text),  # -1.0 do 1.0
            }

            # Dodaj demografię jeśli włączona
            if include_demographics and persona:
                response_data["demographics"] = {
                    "age": persona.age,
                    "gender": persona.gender,
                    "education": persona.education_level,
                    "occupation": persona.occupation,
                }

            responses_by_question[response.question_text].append(response_data)

        # Agreguj statystyki demograficzne całej grupy
        demographic_summary = None
        if include_demographics:
            ages = [p.age for p in personas.values()]
            genders = [p.gender for p in personas.values()]
            educations = [p.education_level for p in personas.values() if p.education_level]

            demographic_summary = {
                "age_range": f"{min(ages)}-{max(ages)}" if ages else "N/A",
                "gender_distribution": dict(zip(*np.unique(genders, return_counts=True))) if genders else {},
                "education_levels": list(set(educations)),
                "sample_size": len(personas),
            }

        return {
            "topic": focus_group.name,
            "description": focus_group.description,
            "responses_by_question": responses_by_question,
            "demographic_summary": demographic_summary,
            "total_responses": len(responses),
        }

    def _prepare_prompt_variables(
        self,
        discussion_data: dict[str, Any],
        include_recommendations: bool,
        language: str = 'pl',
    ) -> dict[str, str]:
        """
        Przygotowuje zmienne do renderowania promptu z YAML.

        Formatuje pytania, odpowiedzi, sentiment i demografię.
        Parametryzuje język dla treści AI output (nagłówki sekcji pozostają po angielsku).

        Args:
            discussion_data: Dane dyskusji z responses, questions, demographics
            include_recommendations: Czy zawrzeć sekcję Strategic Recommendations
            language: Język dla treści podsumowania ('pl' lub 'en')

        Returns:
            Słownik zmiennych do podstawienia w prompt template
        """

        topic = discussion_data["topic"]
        description = discussion_data["description"] or "No description provided"
        responses_by_question = discussion_data["responses_by_question"]
        demo_summary = discussion_data.get("demographic_summary")

        # Formatujemy pytania wraz z odpowiedziami
        formatted_discussion = []
        for idx, (question, responses) in enumerate(responses_by_question.items(), 1):
            formatted_discussion.append(f"\n**Question {idx}:** {question}")
            formatted_discussion.append(f"*({len(responses)} responses)*\n")

            for ridx, resp in enumerate(responses[:15], 1):  # Ograniczamy liczbę odpowiedzi, aby nie przekroczyć limitu tokenów
                text = resp["response"][:300]  # Skracamy bardzo długie wypowiedzi
                sentiment = resp["sentiment"]
                sentiment_label = "positive" if sentiment > 0.15 else "negative" if sentiment < -0.15 else "neutral"

                demo_str = ""
                if "demographics" in resp:
                    demo = resp["demographics"]
                    demo_str = f" ({demo['gender']}, {demo['age']}, {demo['occupation']})"

                formatted_discussion.append(
                    f"{ridx}. [{sentiment_label.upper()}]{demo_str} \"{text}\""
                )

        discussion_text = "\n".join(formatted_discussion)

        # Kontekst demograficzny
        demo_context = ""
        if demo_summary:
            demo_context = f"""
**PARTICIPANT DEMOGRAPHICS:**
- Sample size: {demo_summary['sample_size']}
- Age range: {demo_summary['age_range']}
- Gender distribution: {demo_summary['gender_distribution']}
- Education levels: {', '.join(demo_summary['education_levels'][:5])}
"""

        recommendations_section = ""
        if include_recommendations:
            recommendations_section = """
## 5. STRATEGIC RECOMMENDATIONS (2-3 bullet points, ≤25 words each)
Give the most valuable next steps for the product/marketing team.
Format every bullet as: **Actionable theme**: succinct action with expected impact.
Use proper markdown bold syntax: **text** (two asterisks on both sides).
Tie each recommendation to evidence from the discussion.
"""

        # Instrukcja językowa (nagłówki po angielsku, treść w wybranym języku)
        language_instruction_map = {
            'pl': (
                "\n\n**CRITICAL LANGUAGE INSTRUCTION:**\n"
                "- Keep ALL section headings in ENGLISH (e.g., ## 1. EXECUTIVE SUMMARY, ## 2. KEY INSIGHTS)\n"
                "- Write ALL content (paragraphs, bullet points, analysis, quotes) in POLISH\n"
                "- Use Polish grammar, vocabulary, and phrasing throughout the content\n"
                "- Example: '## 2. KEY INSIGHTS' followed by '**Główny problem**: Użytkownicy oczekują...'\n"
            ),
            'en': (
                "\n\n**CRITICAL LANGUAGE INSTRUCTION:**\n"
                "- Keep ALL section headings in ENGLISH (e.g., ## 1. EXECUTIVE SUMMARY, ## 2. KEY INSIGHTS)\n"
                "- Write ALL content (paragraphs, bullet points, analysis, quotes) in ENGLISH\n"
                "- Use English grammar, vocabulary, and phrasing throughout the content\n"
                "- Example: '## 2. KEY INSIGHTS' followed by '**Main concern**: Users expect...'\n"
            ),
        }

        language_instruction = language_instruction_map.get(
            language,
            language_instruction_map['pl']
        )

        return {
            "topic": topic,
            "description": description,
            "demo_context": demo_context,
            "discussion_text": discussion_text,
            "recommendations_section": recommendations_section,
            "language_instruction": language_instruction,
        }

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

    async def _store_insights_from_summary(
        self,
        db: AsyncSession,
        focus_group: FocusGroup,
        parsed_summary: dict[str, Any],
        prompt_text: str,
    ) -> list:
        """
        Extract and persist InsightEvidence records from AI summary

        Converts 3-7 key insights from the summary into InsightEvidence records
        with provenance tracking (model, prompt, sources).

        Args:
            db: Database session
            focus_group: FocusGroup instance
            parsed_summary: Parsed AI summary dict
            prompt_text: Original prompt used for generation

        Returns:
            List of created InsightEvidence instances
        """
        traceability_service = InsightTraceabilityService(db)

        key_insights = parsed_summary.get("key_insights", [])
        if not key_insights:
            return []

        created_insights = []

        # Extract concepts from executive summary and sentiment narrative
        concepts = self._extract_concepts(
            parsed_summary.get("executive_summary", "")
            + " "
            + parsed_summary.get("sentiment_narrative", "")
        )

        # Determine overall sentiment
        overall_sentiment = self._determine_sentiment(
            parsed_summary.get("sentiment_narrative", "")
        )

        for idx, insight_text in enumerate(key_insights[:7]):  # Max 7 insights
            # Determine insight type from text
            insight_type = self._classify_insight_type(insight_text)

            # Calculate confidence and impact scores (heuristic)
            confidence_score = self._calculate_confidence(insight_text)
            impact_score = self._calculate_impact(insight_text, idx)

            # Extract evidence (use surprising findings or recommendations as supporting evidence)
            evidence = self._build_evidence(parsed_summary, insight_text)

            # Build sources reference
            sources = [
                {
                    "type": "focus_group_discussion",
                    "focus_group_id": str(focus_group.id),
                    "focus_group_name": focus_group.name,
                }
            ]

            # Store insight
            try:
                insight_record = await traceability_service.store_insight_evidence(
                    project_id=focus_group.project_id,
                    insight_text=insight_text,
                    insight_type=insight_type,
                    confidence_score=confidence_score,
                    impact_score=impact_score,
                    evidence=evidence,
                    concepts=concepts[:10],  # Max 10 concepts
                    sentiment=overall_sentiment,
                    model_version=self.llm.model,
                    prompt=prompt_text,
                    sources=sources,
                    focus_group_id=focus_group.id,
                )
                created_insights.append(insight_record)
            except Exception as e:
                # Log error but don't fail the entire summary generation
                print(f"Warning: Failed to store insight {idx}: {e}")
                continue

        return created_insights

    def _extract_concepts(self, text: str) -> list[str]:
        """
        Ekstrakcja kluczowych koncepcji z tekstu z wsparciem dla języka polskiego.

        Wykorzystuje:
        - Polskie i angielskie stopwords (NLTK + custom)
        - Regex z polskimi znakami (ą, ć, ę, ł, ń, ó, ś, ź, ż)
        - Pseudo-lematyzację (usuwanie końcówek fleksyjnych)
        - N-gramy (bigramy i trigramy) z sklearn CountVectorizer
        - Preferencję dla fraz wielowyrazowych nad pojedynczymi słowami

        Args:
            text: Tekst do analizy

        Returns:
            Lista top 15 koncepcji, posortowanych według częstości
        """
        if not text or len(text.strip()) < 10:
            return []

        text_lower = text.lower()

        # Step 1: Extract unigrams with Polish character support
        # Regex: 3+ characters, Polish diacritics, hyphens for compound words
        unigram_pattern = r'\b[a-ząćęłńóśźż-]{3,}\b'
        words = re.findall(unigram_pattern, text_lower, flags=re.UNICODE)

        # Filter stopwords and normalize
        normalized_words = []
        for word in words:
            # Skip stopwords
            if word in _ALL_STOPWORDS:
                continue
            # Skip pure numbers or very short words
            if word.isdigit() or len(word) < 3:
                continue
            # Normalize (pseudo-lemmatization)
            normalized = _normalize_polish_word(word)
            if normalized not in _ALL_STOPWORDS:
                normalized_words.append(normalized)

        # Count unigrams
        unigram_counts = Counter(normalized_words)

        # Step 2: Extract n-grams (bigrams and trigrams) using sklearn
        # This catches multi-word concepts like "customer experience", "product quality"
        ngram_concepts = []
        try:
            # Create vectorizer with n-gram support
            vectorizer = CountVectorizer(
                ngram_range=(2, 3),  # Bigrams and trigrams
                min_df=1,  # Minimum document frequency
                max_df=0.9,  # Maximum document frequency (filter very common)
                stop_words=list(_ALL_STOPWORDS),
                token_pattern=r'\b[a-ząćęłńóśźż-]{3,}\b',  # Polish characters
                lowercase=True,
            )

            # Fit and transform text (treat as single document)
            X = vectorizer.fit_transform([text_lower])

            # Get n-grams with their counts
            feature_names = vectorizer.get_feature_names_out()
            counts = X.toarray()[0]

            # Filter n-grams: only those with ≥2 occurrences
            for ngram, count in zip(feature_names, counts):
                if count >= 2:
                    ngram_concepts.append((ngram, count))

            # Sort by frequency
            ngram_concepts.sort(key=lambda x: x[1], reverse=True)

        except Exception as e:
            # If sklearn extraction fails, continue with unigrams only
            logger.warning(f"N-gram extraction failed: {e}")
            ngram_concepts = []

        # Step 3: Combine and prioritize n-grams
        # Strategy: Prefer n-grams (multi-word concepts) over single words
        final_concepts = []

        # Add top n-grams first (up to 10)
        for ngram, count in ngram_concepts[:10]:
            final_concepts.append(ngram)

        # Add top unigrams to fill remaining slots
        # Skip unigrams that are already part of extracted n-grams
        ngram_words = set()
        for ngram, _ in ngram_concepts:
            ngram_words.update(ngram.split())

        for word, count in unigram_counts.most_common(30):
            # Skip if already in final concepts
            if word in final_concepts:
                continue
            # Skip if word is part of an n-gram we already included
            if word in ngram_words:
                continue
            # Add if we have slots remaining
            if len(final_concepts) < 15:
                final_concepts.append(word)
            else:
                break

        # If we don't have enough concepts, add more unigrams
        if len(final_concepts) < 10:
            for word, count in unigram_counts.most_common(15):
                if word not in final_concepts and len(final_concepts) < 15:
                    final_concepts.append(word)

        return final_concepts[:15]  # Return top 15

    def _determine_sentiment(self, sentiment_narrative: str) -> str:
        """Determine overall sentiment from narrative"""
        if not sentiment_narrative:
            return "neutral"

        score = _simple_sentiment_score(sentiment_narrative)
        if score > 0.2:
            return "positive"
        elif score < -0.2:
            return "negative"
        elif "mixed" in sentiment_narrative.lower() or "polarizing" in sentiment_narrative.lower():
            return "mixed"
        else:
            return "neutral"

    def _classify_insight_type(self, insight_text: str) -> str:
        """
        Klasyfikacja typu spostrzeżenia (insight) na podstawie słów kluczowych.

        Obsługiwane typy:
        - opportunity: szanse, potencjał wzrostu, przewagi
        - risk: ryzyka, zagrożenia, problemy
        - trend: trendy, zmiany w czasie, przesunięcia
        - pattern: wzorce, powtarzające się zachowania

        Wspiera język polski i angielski.

        Args:
            insight_text: Tekst spostrzeżenia do klasyfikacji

        Returns:
            Typ spostrzeżenia: "opportunity", "risk", "trend", lub "pattern"
        """
        insight_lower = insight_text.lower()

        # Keyword patterns for classification (PL + EN)
        # Priority order: opportunity > risk > trend > pattern
        # This ensures specific types are detected before generic "pattern"

        # 1. OPPORTUNITY - szanse, potencjał, wzrost, przewagi
        opportunity_keywords = [
            # Polish
            "szansa", "szanse", "potencjał", "wzrost", "przewaga", "okazja",
            "możliwość", "korzyść", "zaleta", "zysk", "rozwój", "ekspansja",
            "innowacja", "ulepszenie",
            # English
            "opportunity", "potential", "growth", "advantage", "benefit",
            "gain", "upside", "improvement", "innovation",
        ]

        # 2. RISK - ryzyko, zagrożenia, problemy, wyzwania
        risk_keywords = [
            # Polish
            "ryzyko", "zagrożenie", "obawa", "problem", "wyzwanie",
            "bariera", "trudność", "niebezpieczeństwo", "słabość", "ograniczenie",
            "kryzys", "utrata", "odpływ", "negatywny wpływ",
            # English
            "risk", "threat", "concern", "problem", "issue", "challenge",
            "barrier", "difficulty", "danger", "weakness", "limitation",
            "crisis", "loss", "churn", "negative impact",
        ]

        # 3. TREND - trendy, zmiany w czasie, przesunięcia
        trend_keywords = [
            # Polish
            "trend", "tendencja", "zmiana", "przesunięcie", "ewolucja",
            "wzrostowy", "spadkowy", "rosnący", "malejący", "coraz więcej",
            "coraz mniej", "stopniowo", "dynamika",
            # English
            "trend", "tendency", "shift", "change", "evolution",
            "increasing", "decreasing", "growing", "declining", "more and more",
            "less and less", "gradually", "dynamics",
        ]

        # 4. PATTERN - wzorce, powtarzalność, konsekwencja
        pattern_keywords = [
            # Polish
            "wzorzec", "schemat", "powtarzalny", "konsekwentny", "regularny",
            "częsty", "powszechny", "typowy", "stały", "większość", "wszyscy",
            "systematyczny",
            # English
            "pattern", "consistent", "regular", "frequent", "common",
            "typical", "recurring", "systematic", "across", "all", "majority",
        ]

        # Check for opportunities (highest priority for positive insights)
        if any(keyword in insight_lower for keyword in opportunity_keywords):
            return "opportunity"

        # Check for risks (high priority for negative insights)
        if any(keyword in insight_lower for keyword in risk_keywords):
            return "risk"

        # Check for trends (changes over time)
        if any(keyword in insight_lower for keyword in trend_keywords):
            return "trend"

        # Check for patterns (recurring behaviors)
        if any(keyword in insight_lower for keyword in pattern_keywords):
            return "pattern"

        # Default fallback logic: infer from context if no keywords matched
        # If text mentions change/time, likely a trend
        # If text mentions positive outcome, likely opportunity
        # Otherwise default to "opportunity" (more actionable than "pattern")

        time_indicators = ["czas", "ostatnio", "wcześniej", "teraz", "obecnie", "recently", "now", "before", "time"]
        positive_indicators = ["dobrze", "lepiej", "pozytywnie", "sukces", "well", "better", "positive", "success"]

        if any(indicator in insight_lower for indicator in time_indicators):
            return "trend"
        elif any(indicator in insight_lower for indicator in positive_indicators):
            return "opportunity"
        else:
            # Final fallback: opportunity (more actionable than pattern)
            return "opportunity"

    def _calculate_confidence(self, insight_text: str) -> float:
        """Calculate confidence score based on language strength (0-1)"""
        insight_lower = insight_text.lower()

        # Strong confidence indicators
        strong_words = ["all", "every", "consistently", "clearly", "definitely", "strongly"]
        # Weak confidence indicators
        weak_words = ["some", "may", "might", "possibly", "potentially", "could"]

        strong_count = sum(1 for word in strong_words if word in insight_lower)
        weak_count = sum(1 for word in weak_words if word in insight_lower)

        # Base confidence: 0.7
        base_confidence = 0.7
        confidence = base_confidence + (strong_count * 0.1) - (weak_count * 0.1)

        return max(0.5, min(1.0, confidence))  # Clamp between 0.5 and 1.0

    def _calculate_impact(self, insight_text: str, position: int) -> int:
        """Calculate impact score based on insight importance (1-10)"""
        # First insights are typically more important
        position_score = max(10 - position * 2, 3)  # 10, 8, 6, 4, 3...

        # High-impact keywords
        high_impact_words = ["critical", "major", "significant", "key", "essential", "crucial"]
        impact_multiplier = 1.0

        insight_lower = insight_text.lower()
        if any(word in insight_lower for word in high_impact_words):
            impact_multiplier = 1.2

        impact = int(position_score * impact_multiplier)
        return max(1, min(10, impact))  # Clamp between 1 and 10

    def _build_evidence(self, parsed_summary: dict[str, Any], insight_text: str) -> list[dict]:
        """Build evidence list from summary components"""
        evidence = []

        # Add executive summary as context
        if parsed_summary.get("executive_summary"):
            evidence.append({
                "type": "summary",
                "text": parsed_summary["executive_summary"][:300],  # Truncate
                "source": "executive_summary",
            })

        # Add surprising findings as supporting evidence
        for finding in parsed_summary.get("surprising_findings", [])[:2]:
            evidence.append({
                "type": "supporting_finding",
                "text": finding,
                "source": "surprising_findings",
            })

        # Add segment analysis if relevant
        segment_analysis = parsed_summary.get("segment_analysis", {})
        if segment_analysis:
            # Take first 2 segments
            for segment_name, analysis in list(segment_analysis.items())[:2]:
                evidence.append({
                    "type": "segment_insight",
                    "text": f"{segment_name}: {analysis}",
                    "source": "segment_analysis",
                })

        return evidence[:5]  # Max 5 evidence items
