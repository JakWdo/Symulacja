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
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG
from app.services.shared.clients import build_chat_model

settings = get_settings()
logger = logging.getLogger(__name__)


def _map_graph_node_to_insight(node: dict[str, Any]) -> "GraphInsight" | None:
    """Konwertuje graph node z polskimi property names na GraphInsight z angielskimi.

    Mapowanie:
    - streszczenie → summary
    - skala → magnitude
    - pewnosc → confidence ("wysoka"→"high", "srednia"→"medium", "niska"→"low")
    - okres_czasu → time_period
    - kluczowe_fakty → why_matters (z dodatkowym kontekstem)

    Args:
        node: Dict z grafu Neo4j (polskie property names)

    Returns:
        GraphInsight object lub None jeśli dane niepełne
    """
    if not node:
        return None

    # Graf używa polskich property names
    node_type = node.get('type', 'Unknown')
    summary = node.get('streszczenie')

    if not summary:
        logger.warning(f"Graph node bez streszczenia: {node}")
        return None

    # Mapowanie pewności PL→EN
    pewnosc_pl = node.get('pewnosc', '').lower()
    confidence_map = {'wysoka': 'high', 'srednia': 'medium', 'niska': 'low'}
    confidence = confidence_map.get(pewnosc_pl, 'medium')

    # Dane węzła (polskie property names)
    magnitude = node.get('skala')
    time_period = node.get('okres_czasu')
    source = node.get('source', node.get('document_title'))

    # why_matters - użyj kluczowych faktów lub summary jako fallback
    kluczowe_fakty = node.get('kluczowe_fakty', '')
    why_matters = f"Ten wskaźnik pokazuje: {kluczowe_fakty}" if kluczowe_fakty else summary

    try:
        return GraphInsight(
            type=node_type,
            summary=summary,
            magnitude=magnitude,
            confidence=confidence,
            time_period=time_period,
            source=source,
            why_matters=why_matters
        )
    except Exception as e:
        logger.error(f"Nie można utworzyć GraphInsight z node: {node}, error: {e}")
        return None


class GraphInsight(BaseModel):
    """Pojedynczy insight z grafu wiedzy (Wskaznik, Obserwacja, Trend).

    UWAGA: Ten schema używa ANGIELSKICH property names dla API consistency.
    Dane w grafie Neo4j używają POLSKICH nazw (streszczenie, skala, pewnosc, etc.).

    Konwersja wykonywana przez funkcję _map_graph_node_to_insight():
    - streszczenie → summary
    - skala → magnitude
    - pewnosc → confidence ("wysoka"→"high", "srednia"→"medium", "niska"→"low")
    - okres_czasu → time_period
    - kluczowe_fakty → why_matters (z dodatkowym edukacyjnym kontekstem)
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
            temperature=0.0,  # Deterministyczny output dla JSON generation (zero creativity needed)
            max_tokens=8000,  # Wystarczająco na pełny plan + briefy
            timeout=120,  # 2 minuty dla complex reasoning
        )

        # RAG service dla hybrid search kontekstu
        self.rag_service = PolishSocietyRAG()

        logger.info("PersonaOrchestrationService zainicjalizowany (Gemini 2.5 Pro)")

    async def create_persona_allocation_plan(
        self,
        target_demographics: dict[str, Any],
        num_personas: int,
        project_description: str | None = None,
        additional_context: str | None = None,
    ) -> PersonaAllocationPlan:
        """Tworzy szczegółowy plan alokacji person z długimi briefami.

        Gemini 2.5 Pro przeprowadza głęboką analizę:
        1. Pobiera Graph RAG context (hybrid search dla rozkładów demograficznych)
        2. Analizuje trendy społeczne i wskaźniki statystyczne
        3. Tworzy spójne (900-1200 znaków) edukacyjne briefe
        4. Wyjaśnia "dlaczego" dla każdej decyzji alokacyjnej

        Args:
            target_demographics: Rozkład demograficzny projektu (age_group, gender, etc.)
            num_personas: Całkowita liczba person do wygenerowania
            project_description: Opis projektu badawczego
            additional_context: Dodatkowy kontekst od użytkownika (z AI Wizard)

        Returns:
            PersonaAllocationPlan z grupami demograficznymi i szczegółowymi briefami

        Raises:
            Exception: Jeśli LLM nie może wygenerować planu lub JSON parsing fails
        """
        logger.info(f"🎯 Orchestration: Tworzenie planu alokacji dla {num_personas} person...")

        # Krok 1: Pobierz comprehensive Graph RAG context
        graph_context = await self._get_comprehensive_graph_context(target_demographics)
        logger.info(f"📊 Pobrano {len(graph_context)} fragmentów z Graph RAG")

        # Krok 2: Zbuduj prompt w stylu edukacyjnym
        prompt = self._build_orchestration_prompt(
            target_demographics=target_demographics,
            num_personas=num_personas,
            graph_context=graph_context,
            project_description=project_description,
            additional_context=additional_context,
        )

        # Krok 3: Gemini 2.5 Pro generuje plan z retry logic
        max_retries = 2
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🤖 Gemini 2.5 Pro attempt {attempt}/{max_retries} (max_tokens=8000, timeout=120s)...")
                response = await self.llm.ainvoke(prompt)

                # DEBUG: Log surowej odpowiedzi od Gemini
                response_text = response.content if hasattr(response, 'content') else str(response)
                logger.info(f"📝 Gemini response length: {len(response_text)} chars")
                logger.info(f"📝 Gemini response preview (first 500 chars): {response_text[:500]}")
                logger.info(f"📝 Gemini response preview (last 500 chars): {response_text[-500:]}")

                plan_json = self._extract_json_from_response(response_text)

                # DEBUG: Log sparsowanego JSON
                logger.info(f"✅ JSON parsed successfully: {len(plan_json)} top-level keys")
                logger.info(f"✅ JSON keys: {list(plan_json.keys())}")

                # Parse do Pydantic model (walidacja)
                plan = PersonaAllocationPlan(**plan_json)

                logger.info(f"✅ Plan alokacji utworzony: {len(plan.groups)} grup demograficznych")
                return plan

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"⚠️  Attempt {attempt}/{max_retries} - JSON syntax error: {e}")
                logger.warning(f"   Error at: line {e.lineno} col {e.colno} (pos {e.pos})")

                if attempt < max_retries:
                    logger.info("   Retrying with enhanced error feedback in prompt...")
                    # Dodaj do promptu feedback o błędzie (dla retry)
                    error_context = f"""

⚠️  **PREVIOUS ATTEMPT FAILED - FIX THIS ERROR:**
- JSON syntax error at line {e.lineno}, column {e.colno}
- Error: {str(e)}
- CRITICAL: Check for trailing commas, unclosed brackets, or invalid escapes
- Return ONLY valid JSON, no preamble, no explanations!
"""
                    prompt = prompt + error_context
                else:
                    logger.error(f"❌ All {max_retries} attempts failed with JSON syntax errors")
                    logger.error(f"❌ Last error: {e}")
                    raise

            except Exception as e:
                last_error = e
                logger.error(f"❌ Attempt {attempt}/{max_retries} - Unexpected error: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                logger.error(f"❌ Exception details: {str(e)[:1000]}")

                if attempt < max_retries:
                    logger.info("   Retrying...")
                else:
                    logger.error(f"❌ All {max_retries} attempts failed")
                    raise

        # Jeśli tu dojdziemy, znaczy że wszystkie retries failed
        if last_error:
            raise last_error
        else:
            raise Exception("Failed to create persona allocation plan after all retries")

    async def _get_comprehensive_graph_context(
        self,
        target_demographics: dict[str, Any]
    ) -> str:
        """Pobiera comprehensive Graph RAG context dla rozkładów demograficznych.

        Hybrid search (vector + keyword + RRF) dla każdej grupy demograficznej:
        - Age groups (18-24, 25-34, etc.)
        - Gender
        - Education levels
        - Locations

        Args:
            target_demographics: Rozkład demograficzny (age_group, gender, etc.)

        Returns:
            Sformatowany string z Graph RAG context (Wskazniki, Obserwacje, Trendy)
        """
        # Przygotuj queries dla hybrid search
        queries = []

        # Age groups
        if "age_group" in target_demographics:
            for age_group in target_demographics["age_group"].keys():
                queries.append(f"demographics statistics age {age_group} Poland")

        # Gender
        if "gender" in target_demographics:
            for gender in target_demographics["gender"].keys():
                queries.append(f"gender {gender} demographics Poland workforce")

        # Education
        if "education_level" in target_demographics:
            for education in target_demographics["education_level"].keys():
                queries.append(f"education level {education} Poland employment")

        # Ogólne trendy społeczne
        queries.extend([
            "Polish society trends 2023 2024 demographics",
            "workforce statistics Poland employment rates",
            "income housing costs Poland urban areas",
            "work-life balance trends Poland young professionals",
        ])

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
            logger.warning("⚠️ Graph RAG queries przekroczyły timeout (30s) - zwracam pusty kontekst")
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

    def _format_graph_context(self, documents: list[Any]) -> str:
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
        target_demographics: dict[str, Any],
        num_personas: int,
        graph_context: str,
        project_description: str | None,
        additional_context: str | None,
    ) -> str:
        """Buduje prompt w stylu edukacyjnym dla Gemini 2.5 Pro.

        Prompt instruuje LLM aby:
        1. Przeanalizować Graph RAG context (Wskazniki, Obserwacje)
        2. Wyjaśnić "dlaczego" dla każdej decyzji (edukacyjny styl)
        3. Utworzyć spójne (900-1200 znaków) briefe dla każdej grupy
        4. Użyć konwersacyjnego tonu (jak kolega z zespołu)

        Args:
            target_demographics: Rozkład demograficzny
            num_personas: Liczba person
            graph_context: Kontekst z Graph RAG
            project_description: Opis projektu
            additional_context: Dodatkowy kontekst od użytkownika

        Returns:
            Długi prompt string (production-ready instrukcje)
        """
        prompt = f"""
Jesteś ekspertem od socjologii i badań społecznych w Polsce. Twoim zadaniem jest
przeanalizowanie danych demograficznych i Graph RAG context, a następnie stworzenie
szczegółowego, EDUKACYJNEGO planu alokacji {num_personas} syntetycznych person.

=== STYL KOMUNIKACJI (KRYTYCZNY!) ===

WAŻNE: Twoim outputem będzie używany bezpośrednio przez innych agentów AI oraz
pokazywany użytkownikom w interfejsie. Dlatego MUSISZ:

✅ **Konwersacyjny ton** - Mówisz jak kolega z zespołu, nie jak suchy raport
✅ **Wyjaśniaj "dlaczego"** - Nie podawaj tylko faktów, ale ich znaczenie i kontekst
✅ **Używaj przykładów z życia** - "Wyobraź sobie Annę z Warszawy, która..."
✅ **Production-ready** - Treść może iść bezpośrednio do użytkownika bez edycji
✅ **Edukacyjny** - User ma się UCZYĆ o polskim społeczeństwie, nie tylko dostać dane
✅ **PO POLSKU** - Naturalnie, bez anglicyzmów gdzie niepotrzebne

    DŁUGOŚĆ BRIEFÓW: Każdy brief dla grupy demograficznej ma mieć 900-1200 znaków.
    To ma być edukacyjny mini-esej, który wyjaśnia kontekst społeczny bez lania wody.

=== DANE WEJŚCIOWE ===

**Projekt badawczy:**
{project_description or "Badanie person syntetycznych"}

**Dodatkowy kontekst od użytkownika:**
{additional_context or "Brak dodatkowego kontekstu"}

**Rozkład demograficzny docelowy:**
```json
{json.dumps(target_demographics, indent=2, ensure_ascii=False)}
```

**Liczba person do wygenerowania:** {num_personas}

{graph_context}

=== TWOJE ZADANIE ===

Przeprowadź głęboką socjologiczną analizę i stwórz plan alokacji person który zawiera:

### 1. OGÓLNY KONTEKST SPOŁECZNY (500-800 znaków)

Zrób overview polskiego społeczeństwa bazując na Graph RAG context:
- Jakie są kluczowe trendy demograficzne w Polsce?
- Co pokazują wskaźniki ekonomiczne (zatrudnienie, dochody, housing)?
- Jakie wartości i wyzwania ma polskie społeczeństwo 2025?
- Dlaczego to ma znaczenie dla generowania person?
- Dla kazdej osoby twórz opis dlaczego akurat do niej się to tyczy.

### 2. GRUPY DEMOGRAFICZNE Z DŁUGIMI BRIEFAMI

Dla każdej znaczącej grupy demograficznej (na podstawie rozkładu docelowego), stwórz:

**Każdy brief MUSI zawierać (900-1200 znaków):**

a) **Dlaczego ta grupa?** (180-220 znaków)
   - Jaki % populacji stanowi ta grupa (z Graph RAG)
   - Dlaczego są ważni dla badania
   - Jak rozkład pasuje do realiów polskiego społeczeństwa
   - Statystyki z Graph RAG (magnitude, confidence)

b) **Kontekst zawodowy i życiowy** (260-320 znaków)
   - Typowe zawody dla tej grupy
   - Zarobki (realne liczby w PLN z Graph RAG jeśli dostępne)
   - Housing situation (własne/wynajem, ceny mieszkań)
   - Wyzwania ekonomiczne (kredyty, oszczędności, koszty życia)
   - Dlaczego tak jest? (społeczno-ekonomiczny kontekst)

c) **Wartości i aspiracje** (260-320 znaków)
   - Jakie wartości są ważne dla tej grupy (z badań społecznych)
   - Aspiracje i life goals
   - Dlaczego te wartości? (kontekst pokoleniowy, historyczny)
   - Jak zmienia się to w czasie (trendy)

d) **Typowe wyzwania i zainteresowania** (180-240 znaków)
   - Realne problemy życiowe tej grupy
   - Typowe hobby i sposób spędzania wolnego czasu
   - Dlaczego te zainteresowania pasują do profilu

e) **Segment Characteristics** (4-6 kluczowych cech tego segmentu)
   - Krótkie, mówiące cechy charakterystyczne dla tej grupy
   - Format: Lista stringów (np. ["Profesjonaliści z wielkich miast", "Wysoko wykształceni", "Stabilna kariera"])
   - Cechy powinny być KONKRETNE dla tej grupy (nie ogólne!)
   - Bazowane na demographics + insights z grafu

f) **Graph Insights** (structured data)
   - Lista 3-5 kluczowych wskaźników z Graph RAG
   - Każdy z wyjaśnieniem "why_matters"

g) **Allocation Reasoning**
   - Dlaczego tyle person w tej grupie (X z {num_personas})?
   - Jak to odnosi się do % populacji vs. relevance dla badania?

### 3. PRZYKŁAD DOBREGO BRIEFU

```
# Grupa: Kobiety 25-34, wyższe wykształcenie, Warszawa (6 person)

## Dlaczego ta grupa?

W polskim społeczeństwie kobiety 25-34 z wyższym wykształceniem stanowią
około 17.3% populacji miejskiej według danych GUS z 2022 roku. To fascynująca
grupa społeczna która znajduje się w momencie życia pełnym zmian - balansują
między budowaniem kariery a decyzjami o rodzinie, między niezależnością finansową
a realiami rynku nieruchomości.

Dla tego badania ta grupa jest kluczowa bo to oni są early adopters nowych
produktów i usług. Wskaźniki pokazują że 78.4% tej grupy jest zatrudnionych
(najwyższa stopa w Polsce!), co oznacza że mają purchasing power. Jednocześnie
63% wykazuje wysoką mobilność zawodową - często zmieniają pracę, co czyni ich
otwartymi na nowe rozwiązania.

## Kontekst zawodowy i życiowy

Warszawa koncentruje 35% polskiego rynku tech, fintech i consulting. Dla młodych
kobiet z wyższym wykształceniem to oznacza szeroki wybór możliwości kariery - od
project managerów przez UX designerów po analityków danych. Typowe zarobki w tej
grupie to 7000-12000 zł netto, co brzmi nieźle, ale...

...ale tu zaczyna się problem. Cena m2 w Warszawie to ~15000 zł. Dla osoby
zarabiającej 9000 zł netto (mediana), zakup 50m2 mieszkania wymaga odłożenia
~750000 zł, co przy oszczędzaniu 2000 zł miesięcznie daje... 31 lat. Nie dziwi
więc że 45% tej grupy wynajmuje mieszkania. To nie wybór stylu życia - to
konieczność ekonomiczna.

[... dalszy tekst 1000+ znaków ...]
```

=== CRITICAL: JSON OUTPUT REQUIREMENTS ===

⚠️  **BARDZO WAŻNE - PRZECZYTAJ UWAŻNIE:**

Your output will be parsed by `json.loads()`. MUSISZ przestrzegać tych zasad:

1. **TYLKO JSON** - Zwróć WYŁĄCZNIE obiekt JSON, bez ŻADNEGO dodatkowego tekstu:
   - ❌ NIE: "Jasne, rozumiem zadanie. Zaczynajmy!\\n```json\\n{{...}}"
   - ✅ TAK: "{{...}}" (tylko czysty JSON)
   - ❌ NIE: Dodawanie preambuły, wyjaśnień przed JSON
   - ✅ TAK: Start response bezpośrednio z `{{`

2. **Poprawna składnia JSON:**
   - ❌ NIE: trailing commas: `"key": "value",]` lub `{{"x": 1,}}`
   - ✅ TAK: brak trailing comma: `"key": "value"]` i `{{"x": 1}}`
   - ❌ NIE: single quotes: `{{'key': 'value'}}`
   - ✅ TAK: double quotes: `{{"key": "value"}}`
   - ❌ NIE: comments: `// this is comment`
   - ✅ TAK: tylko valid JSON (brak komentarzy)

3. **Zamknięte nawiasy** - każdy `{{` ma swoje `}}`, każdy `[` ma swoje `]`
   - Sprawdź szczególnie długie listy (graph_insights!)

4. **Escaped characters** - użyj `\\n` dla newlines w długich tekstach
   - Brief może mieć 1200 znaków → użyj `\\n` dla nowych linii

5. **Valid Unicode** - polskie znaki (ą, ę, ś, etc.) są OK w UTF-8

**BAD Example (WILL CRASH):**
```
Cześć! Przeanalizowałem dane. Oto plan:
```json
{{
  "groups": [
    {{"count": 2, "demographics": {{...}},}}  // trailing comma!
  ]
}}
```
```

**GOOD Example (VALID):**
```json
{{
  "total_personas": 4,
  "overall_context": "Tekst...",
  "groups": [
    {{"count": 2, "demographics": {{"age": "25-34"}}}}
  ]
}}
```

Jeśli masz wątpliwości, mentalnie zwaliduj output przez https://jsonlint.com/

=== OUTPUT FORMAT ===

Generuj JSON zgodny z tym schematem:

```json
{{
  "total_personas": {num_personas},
  "overall_context": "DŁUGI (500-800 znaków) overview polskiego społeczeństwa...",
  "groups": [
    {{
      "count": 6,
      "demographics": {{
        "age": "25-34",
        "gender": "kobieta",
        "education": "wyższe",
        "location": "Warszawa"
      }},
      "brief": "Edukacyjny brief (900-1200 znaków) jak w przykładzie...",
      "segment_characteristics": [
        "Profesjonaliści z wielkich miast",
        "Wysoko wykształceni",
        "Stabilna kariera",
        "Wysokie zaangażowanie społeczne"
      ],
      "graph_insights": [
        {{
          "type": "Wskaznik",
          "summary": "Stopa zatrudnienia kobiet 25-34 z wyższym",
          "magnitude": "78.4%",
          "confidence": "high",
          "time_period": "2022",
          "source": "GUS",
          "why_matters": "Wysoka stopa zatrudnienia oznacza że ta grupa ma..."
        }}
      ],
      "allocation_reasoning": "Dlaczego 6 z {num_personas}? Bo ta grupa stanowi..."
    }}
  ]
}}
```

KLUCZOWE ZASADY:

1. **Briefe mają być KONKRETNE** (900-1200 znaków każdy) - mini-eseje, nie listy
2. **Wyjaśniaj "dlaczego"** dla WSZYSTKIEGO - user ma się uczyć
3. **Konwersacyjny ton** - jak kolega tłumaczy przy kawie, nie jak raport naukowy
4. **Używaj danych z Graph RAG** - magnitude, confidence, time_period, sources
5. **Production-ready** - ten output idzie bezpośrednio do użytkowników
6. **Realne liczby** - PLN, %, lata, konkretne wskaźniki (nie "wysoki" ale "78.4%")
7. **Kontekst społeczny** - wyjaśniaj TŁO (historia, ekonomia, trendy)

Generuj plan alokacji:
"""
        return prompt

    def _extract_json_from_response(self, response_text: str) -> dict[str, Any]:
        """Ekstraktuje JSON z odpowiedzi LLM (może być otoczony markdown lub preambułą).

        Próbuje 4 strategii parsowania w kolejności:
        1. ```json ... ``` blok markdown
        2. ``` ... ``` blok kodu bez typu
        3. Pierwszy { ... } (może być po preambule)
        4. Cały tekst (fallback)

        Args:
            response_text: Surowa odpowiedź od LLM

        Returns:
            Parsed JSON jako dict

        Raises:
            ValueError: Jeśli żadna strategia nie zadziała
        """
        text = response_text.strip()
        import re

        # Strategia 1: Znajdź blok ```json ... ``` (may be embedded in text)
        logger.debug("Trying strategy 1: ```json ... ``` block")
        json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_block_match:
            json_text = json_block_match.group(1).strip()
            logger.debug(f"Found ```json block, length: {len(json_text)} chars")
            logger.debug(f"JSON preview: {json_text[:200]}...")

            try:
                parsed = json.loads(json_text)
                logger.info("✅ JSON parsed successfully via strategy 1 (```json block)")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Strategy 1 failed: {e}")
                logger.warning(f"   At position: line {e.lineno}, col {e.colno}")
                if e.pos < len(json_text):
                    error_snippet = json_text[max(0, e.pos-50):min(len(json_text), e.pos+50)]
                    logger.warning(f"   Error context: ...{error_snippet}...")
                # Kontynuuj do następnej strategii

        # Strategia 2: Znajdź blok ``` ... ``` (without json marker)
        logger.debug("Trying strategy 2: ``` ... ``` code block")
        code_block_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if code_block_match:
            json_text = code_block_match.group(1).strip()
            logger.debug(f"Found code block, length: {len(json_text)} chars")

            try:
                parsed = json.loads(json_text)
                logger.info("✅ JSON parsed successfully via strategy 2 (code block)")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Strategy 2 failed: {e}")
                logger.warning(f"   At position: line {e.lineno}, col {e.colno}")
                # Kontynuuj do następnej strategii

        # Strategia 3: Znajdź pierwszy { ... } (after potential preamble)
        logger.debug("Trying strategy 3: First { ... } braces")
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            json_text = brace_match.group(0).strip()
            logger.debug(f"Found braces block, length: {len(json_text)} chars")
            logger.debug(f"JSON preview: {json_text[:200]}...")

            try:
                parsed = json.loads(json_text)
                logger.info("✅ JSON parsed successfully via strategy 3 (braces)")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Strategy 3 failed: {e}")
                logger.warning(f"   At position: line {e.lineno}, col {e.colno}")
                if e.pos < len(json_text):
                    error_snippet = json_text[max(0, e.pos-50):min(len(json_text), e.pos+50)]
                    logger.warning(f"   Error context: ...{error_snippet}...")
                # Kontynuuj do następnej strategii

        # Strategia 4: Spróbuj sparsować cały tekst (fallback)
        logger.debug("Trying strategy 4: Full text parsing")
        try:
            parsed = json.loads(text)
            logger.info("✅ JSON parsed successfully via strategy 4 (full text)")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"❌ ALL 4 STRATEGIES FAILED")
            logger.error(f"❌ Final error: {e}")
            logger.error(f"❌ At position: line {e.lineno}, col {e.colno}")
            logger.error(f"❌ Response text length: {len(text)} chars")
            logger.error(f"❌ Response text (first 1000 chars): {text[:1000]}")
            logger.error(f"❌ Response text (last 1000 chars): {text[-1000:]}")
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
        insights_text = "\n".join([
            f"- {ins.summary} ({ins.confidence})"
            for ins in graph_insights[:3]  # Top 3
        ]) if graph_insights else "Brak insights"

        # Format citations (first 2 max)
        citations_text = "\n".join([
            f"- {cit.page_content[:100]}..."
            for cit in rag_citations[:2]
        ]) if hasattr(rag_citations[0] if rag_citations else None, 'page_content') else "Brak cytatów"

        prompt = f"""Stwórz trafną, MÓWIĄCĄ nazwę dla poniższego segmentu demograficznego.

DANE SEGMENTU:
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

INSIGHTS Z GRAFU:
{insights_text}

CYTATY Z RAG:
{citations_text}

ZASADY:
1. Nazwa powinna być 2-4 słowa (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")
2. Oddaje kluczową charakterystykę grupy (wiek + status społeczno-ekonomiczny)
3. Używa polskiego języka, brzmi naturalnie
4. Bazuje na insightach (np. jeśli grupa ma niskie dochody + młody wiek → "Młodzi Prekariusze")
5. Unikaj ogólników ("Grupa A", "Segment 1")
6. Jeśli wiek jest istotny, włącz go (np. "35-44")

PRZYKŁADY DOBRYCH NAZW:
- "Młodzi Prekariusze" (18-24, niskie dochody)
- "Aspirujące Profesjonalistki 35-44" (kobiety, wyższe wykształcenie, średnie dochody)
- "Dojrzali Eksperci" (45-54, wysokie dochody, stabilna kariera)
- "Początkujący Profesjonaliści" (25-34, pierwsze kroki w karierze)

ZWRÓĆ TYLKO NAZWĘ (bez cudzysłowów, bez dodatkowych wyjaśnień):"""

        try:
            # Use Gemini Flash for quick naming (cheap, fast)
            llm_flash = build_chat_model(
                model=settings.DEFAULT_MODEL,
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

            logger.info(f"✅ Generated segment name: '{segment_name}'")
            return segment_name

        except Exception as e:
            logger.error(f"❌ Failed to generate segment name: {e}")
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

        # Format insights with details
        insights_text = "\n".join([
            f"- **{ins.summary}**\n  Magnitude: {ins.magnitude or 'N/A'}, Confidence: {ins.confidence}, "
            f"Source: {ins.source or 'N/A'}, Year: {ins.time_period or 'N/A'}\n  "
            f"Why it matters: {ins.why_matters[:150]}..."
            for ins in graph_insights[:5]  # Top 5
        ]) if graph_insights else "Brak insights"

        # Format citations (first 3 max)
        citations_text = "\n".join([
            f"[{idx+1}] {cit.page_content[:200]}..."
            for idx, cit in enumerate(rag_citations[:3])
        ]) if hasattr(rag_citations[0] if rag_citations else None, 'page_content') else "Brak cytatów"

        prompt = f"""Stwórz kontekst społeczny dla segmentu "{segment_name}".

DEMOGRAFIA SEGMENTU:
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

INSIGHTS Z GRAFU WIEDZY:
{insights_text}

CYTATY Z RAG:
{citations_text}

CEL PROJEKTU:
{project_goal or "Badanie syntetycznych person"}

WYTYCZNE:
1. Długość: 500-800 znaków (WAŻNE!)
2. Kontekst SPECYFICZNY dla KONKRETNEJ GRUPY (nie ogólny opis Polski!)
3. Zacznij od opisu charakterystyki grupy (jak w przykładzie)
4. Struktura:
   a) Pierwsza część (2-3 zdania): KIM są te osoby, co ich charakteryzuje
   b) Druga część (2-3 zdania): Ich WARTOŚCI i ASPIRACJE
   c) Trzecia część (2-3 zdania): WYZWANIA i kontekst ekonomiczny z konkretnymi liczbami
5. Ton: konkretny, praktyczny, opisujący TYCH ludzi (nie teoretyczny!)
6. Używaj konkretnych liczb z insights tam gdzie dostępne
7. Unikaj: ogólników ("polska społeczeństwo"), teoretyzowania

PRZYKŁAD DOBREGO KONTEKSTU (na wzór Figmy):
"Tech-Savvy Profesjonaliści to osoby w wieku 28 lat, pracujące jako Marketing Manager w dużych miastach jak Warszawa czy Kraków. Charakteryzują się wysokim wykształceniem (licencjat lub wyżej), stabilną karierą w branży technologicznej i dochodami 8k-12k PLN netto. Są early adopters nowych technologii i cenią sobie work-life balance. Ich główne wartości to innovation, ciągły rozwój i sustainability. Aspirują do awansu na wyższe stanowiska (senior manager, director), własnego mieszkania w atrakcyjnej lokalizacji (co przy cenach 15-20k PLN/m2 wymaga oszczędzania przez 10+ lat) i rozwoju kompetencji w digital marketing oraz AI tools. Wyzwania: rosnąca konkurencja na rynku pracy (według GUS 78% osób z tej grupy ma wyższe wykształcenie), wysokie koszty życia w dużych miastach (średni czynsz ~3500 PLN), presja na ciągły rozwój i keeping up with tech trends."

WAŻNE: Pisz o KONKRETNEJ grupie ludzi, używaj przykładów zawodów, konkretnych liczb, opisuj ICH życie.

ZWRÓĆ TYLKO KONTEKST (bez nagłówków, bez komentarzy, 500-800 znaków):"""

        try:
            response = await self.llm.ainvoke(prompt)  # Use Gemini 2.5 Pro
            segment_context = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # Validation: kontekst powinien mieć 400-1200 znaków
            if len(segment_context) < 400 or len(segment_context) > 1200:
                logger.warning(
                    f"Generated segment context length ({len(segment_context)}) outside range 400-1200, "
                    "but accepting anyway"
                )

            logger.info(f"✅ Generated segment context: {len(segment_context)} chars")
            return segment_context

        except Exception as e:
            logger.error(f"❌ Failed to generate segment context: {e}")
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
