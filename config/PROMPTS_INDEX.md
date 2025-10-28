# Indeks Promptów - Kompletny Katalog

Katalog wszystkich 25 promptów w systemie konfiguracji Sight. Każdy prompt zawiera ID, wersję, parametry i przykład użycia.

**Ostatnia aktualizacja:** 2025-10-27
**Łączna liczba promptów:** 25 (23 bazowe + 2 warianty)

---

## 📑 Spis Treści

- [Grupy Fokusowe (2)](#grupy-fokusowe)
- [Persony (7)](#persony)
- [RAG - Retrieval Augmented Generation (2)](#rag)
- [Ankiety (4)](#ankiety)
- [Prompty Systemowe (10)](#prompty-systemowe)

---

## Grupy Fokusowe

### `focus_groups.discussion_summary`

**Plik:** `config/prompts/focus_groups/discussion_summary.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje kompleksowe strategiczne podsumowanie dyskusji w grupie fokusowej

**Parametry:**
- `topic` - temat dyskusji w grupie fokusowej
- `description` - opis projektu badawczego
- `demo_context` - kontekst demograficzny uczestników (opcjonalny)
- `discussion_text` - pełny transkrypt dyskusji
- `recommendations_section` - sekcja z rekomendacjami (opcjonalna)

**Używany w:**
- `DiscussionSummarizer` (app/services/focus_groups/discussion_summarizer.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("focus_groups.discussion_summary")
rendered = template.render(
    topic="AI w służbie zdrowia",
    description="Badanie percepcji AI w służbie zdrowia",
    demo_context="8 uczestników (4K/4M), 25-45 lat",
    discussion_text="[transkrypt]",
    recommendations_section="## 5. REKOMENDACJE STRATEGICZNE\n..."
)
```

**Output:** Podsumowanie w formacie Markdown z 6 sekcjami (Executive Summary, Kluczowe Wnioski, Zaskakujące Odkrycia, Analiza Segmentów, Rekomendacje, Narracja Sentymentu)

---

### `focus_groups.persona_response`

**Plik:** `config/prompts/focus_groups/persona_response.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje odpowiedź persony w dyskusji grupowej (2-4 zdania, naturalna, konwersacyjna)

**Parametry:**
- `full_name` - pełne imię i nazwisko persony
- `age` - wiek
- `gender` - płeć
- `occupation` - zawód
- `education_level` - poziom wykształcenia
- `location` - lokalizacja geograficzna
- `values` - wartości persony
- `interests` - zainteresowania
- `background_story` - historia życia persony
- `context_text` - dodatkowy kontekst z RAG (opcjonalny)
- `question` - pytanie moderatora

**Używany w:**
- `FocusGroupServiceLangChain` (app/services/focus_groups/focus_group_service_langchain.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("focus_groups.persona_response")
rendered = template.render(
    full_name="Anna Kowalska",
    age=32,
    gender="kobieta",
    occupation="Marketing Manager",
    education_level="wyższe",
    location="Warszawa",
    values="rozwój osobisty, work-life balance",
    interests="joga, podcasty biznesowe",
    background_story="[historia]",
    context_text="",
    question="Co myślisz o produktach ekologicznych?"
)
```

**Output:** 2-4 zdania naturalnej odpowiedzi persony

---

## Persony

### `personas.jtbd`

**Plik:** `config/prompts/personas/jtbd.yaml`
**Wersja:** 1.0.0
**Opis:** Analiza Jobs-to-be-Done dla person z wykorzystaniem metodologii JTBD

**Parametry:**
- `age` - wiek persony
- `occupation` - zawód
- `values` - wartości
- `interests` - zainteresowania
- `background` - tło życiowe
- `segment_name` - nazwa segmentu
- `rag_section` - kontekst z RAG (opcjonalny)
- `formatted_responses` - ostatnie 10 odpowiedzi z grup fokusowych

**Używany w:**
- `PersonaNeedsService` (app/services/personas/persona_needs_service.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("personas.jtbd")
rendered = template.render(
    age=28,
    occupation="Grafik freelancer",
    values="niezależność, kreatywność",
    interests="design, fotografia",
    background="[historia]",
    segment_name="Młodzi Profesjonaliści",
    rag_section="",
    formatted_responses="[ostatnie odpowiedzi]"
)
```

**Output:** JSON z Jobs-to-be-Done, pożądanymi rezultatami, bolączkami (z severity, cytatami, rozwiązaniami)

---

### `personas.orchestration`

**Plik:** `config/prompts/personas/orchestration.yaml`
**Wersja:** 1.0.0
**Opis:** Orkiestracja alokacji person - głęboka analiza socjologiczna z edukacyjnymi briefami

**Parametry:**
- `num_personas` - liczba person do wygenerowania
- `project_description` - opis projektu badawczego
- `additional_context` - dodatkowy kontekst od użytkownika
- `target_demographics` - docelowy rozkład demograficzny (JSON)
- `graph_context` - kontekst z Graph RAG (opcjonalny)

**Używany w:**
- `PersonaOrchestrationService` (app/services/personas/persona_orchestration.py)

**Przykład użycia:**
```python
from config import prompts, models
from app.services.shared.clients import build_chat_model

# Konfiguracja modelu (gemini-2.5-pro, temp=0.3)
model_config = models.get("personas", "orchestration")
llm = build_chat_model(**model_config.params)

template = prompts.get("personas.orchestration")
rendered = template.render(
    num_personas=20,
    project_description="Badanie aplikacji fitness",
    additional_context="Fokus na młodych użytkowników",
    target_demographics='{"age_groups": {"18-24": 0.3, "25-34": 0.5}}',
    graph_context="[insights z Neo4j]"
)
```

**Output:** JSON z `total_personas`, `overall_context`, `groups[]` (każda z długim briefem 900-1200 znaków, cechami segmentu, insightami z grafu, uzasadnieniem alokacji)

---

### `personas.persona_generation_system`

**Plik:** `config/prompts/personas/persona_generation_system.yaml`
**Wersja:** 1.0.0
**Opis:** Systemowy prompt dla generatora person - tworzy realistyczne syntetyczne persony dla polskiego rynku

**Parametry:** brak (prompt systemowy)

**Używany w:**
- `PersonaGeneratorLangChain` (app/services/personas/persona_generator_langchain.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("personas.persona_generation_system")
system_message = template.messages[0]["content"]

# Używane jako system prompt w LangChain
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("user", "Wygeneruj personę: {demographics}")
])
```

**Output:** Używany jako prompt systemowy (brak bezpośredniego outputu)

---

### `personas.persona_uniqueness`

**Plik:** `config/prompts/personas/persona_uniqueness.yaml`
**Wersja:** 1.0.0
**Opis:** Opisuje co czyni tę personę wyjątkową w ramach jej segmentu (250-400 słów)

**Parametry:**
- `persona_name` - pełne imię i nazwisko
- `age` - wiek
- `occupation` - zawód
- `background_story` - historia życia
- `values` - wartości
- `interests` - zainteresowania
- `segment_name` - nazwa segmentu
- `segment_brief_summary` - brief segmentu (typowy przedstawiciel)

**Używany w:**
- `PersonaDetailsService` (app/services/personas/persona_details_service.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("personas.persona_uniqueness")
rendered = template.render(
    persona_name="Anna Kowalska",
    age=32,
    occupation="Marketing Manager",
    background_story="[historia]",
    values="rozwój osobisty",
    interests="joga, podcasty",
    segment_name="Aspirujące Profesjonalistki 25-34",
    segment_brief_summary="[brief segmentu]"
)
```

**Output:** 3-4 akapity (250-400 słów) opisujące unikalność persony względem segmentu

---

### `personas.segment_brief`

**Plik:** `config/prompts/personas/segment_brief.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje długi, angażujący, osobisty opis segmentu (400-800 słów)

**Parametry:**
- `segment_name` - nazwa segmentu
- `age_range` - zakres wiekowy
- `gender` - płeć
- `education` - wykształcenie
- `location` - lokalizacja
- `income` - przedział dochodowy
- `rag_context` - kontekst z RAG (dane społeczne z Polski)
- `example_personas` - przykładowe persony z segmentu (opcjonalne)

**Używany w:**
- `SegmentBriefService` (app/services/personas/segment_brief_service.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("personas.segment_brief")
rendered = template.render(
    segment_name="Młodzi Profesjonaliści",
    age_range="25-34",
    gender="różnorodny",
    education="wyższe",
    location="duże miasta",
    income="8-12k PLN netto",
    rag_context="[dane społeczne z RAG]",
    example_personas="Anna (32, Marketing), Tomasz (29, IT)"
)
```

**Output:** 400-800 słów opisu storytellingowego w 4 sekcjach (Kim są? / Kontekst zawodowy / Wartości / Wyzwania)

---

### `personas.segment_context`

**Plik:** `config/prompts/personas/segment_context.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje kontekst społeczny dla segmentu (500-800 znaków)

**Parametry:**
- `segment_name` - nazwa segmentu
- `age_range` - zakres wiekowy
- `gender` - płeć
- `education` - wykształcenie
- `income` - przedział dochodowy
- `insights_text` - insights z grafu wiedzy
- `citations_text` - cytaty z RAG
- `project_goal` - cel projektu badawczego

**Używany w:**
- `PersonaOrchestrationService` (wewnętrznie dla kontekstowych briefów)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("personas.segment_context")
rendered = template.render(
    segment_name="Młodzi Prekariusze",
    age_range="18-24",
    gender="różnorodny",
    education="średnie / licencjat w trakcie",
    income="3-5k PLN netto",
    insights_text="[insights z Neo4j]",
    citations_text="[cytaty z dokumentów RAG]",
    project_goal="Badanie aplikacji finansowych"
)
```

**Output:** 500-800 znaków kontekstu społecznego dla segmentu

---

### `personas.segment_name`

**Plik:** `config/prompts/personas/segment_name.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje znaczące, evokacyjne nazwy segmentów (2-4 słowa)

**Parametry:**
- `age_range` - zakres wiekowy
- `gender` - płeć
- `education` - wykształcenie
- `income` - przedział dochodowy
- `insights_text` - insights z grafu wiedzy
- `citations_text` - cytaty z RAG

**Używany w:**
- `PersonaOrchestrationService` (generowanie nazw segmentów)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("personas.segment_name")
rendered = template.render(
    age_range="25-34",
    gender="kobieta",
    education="wyższe",
    income="8-12k PLN netto",
    insights_text="Wysoka stopa zatrudnienia, stabilna kariera",
    citations_text="78.4% zatrudnienia w grupie 25-34"
)
```

**Output:** 2-4 słowa nazwy segmentu (np. "Aspirujące Profesjonalistki 25-34", "Młodzi Prekariusze")

---

## RAG

### `rag.cypher_generation`

**Plik:** `config/prompts/rag/cypher_generation.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje zapytanie Cypher z pytania w języku naturalnym (analityk społeczeństwa polskiego)

**Parametry:**
- `graph_schema` - schemat grafu Neo4j
- `question` - pytanie w języku naturalnym

**Używany w:**
- `GraphRAGService` (app/services/rag/rag_graph_service.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("rag.cypher_generation")
rendered = template.render(
    graph_schema="Etykiety węzłów: Obserwacja, Wskaznik, Demografia...",
    question="Jakie są największe wskaźniki zatrudnienia w Polsce?"
)
```

**Output:** Zapytanie Cypher (string) do wykonania na grafie Neo4j

**Węzły:** Obserwacja, Wskaznik, Demografia, Trend, Lokalizacja
**Relacje:** OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W, POWIAZANY_Z

---

### `rag.graph_rag_answer`

**Plik:** `config/prompts/rag/graph_rag_answer.yaml`
**Wersja:** 1.0.0
**Opis:** Odpowiada na pytanie wykorzystując kontekst z grafu i dokumentów RAG (polski ekspert społeczny)

**Parametry:**
- `question` - pytanie użytkownika
- `context` - kontekst z grafu i dokumentów RAG

**Używany w:**
- `GraphRAGService.answer_question()` (app/services/rag/rag_graph_service.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("rag.graph_rag_answer")
rendered = template.render(
    question="Jakie są typowe zarobki młodych profesjonalistów?",
    context="[kontekst z Neo4j + vector search]"
)
```

**Output:** Odpowiedź po polsku z precyzyjnymi danymi z kontekstu

---

## Ankiety

### `surveys.multiple_choice`

**Plik:** `config/prompts/surveys/multiple_choice.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje odpowiedź wielokrotnego wyboru w ankiecie jako konkretna persona

**Parametry:**
- `persona_context` - pełny kontekst persony (demografia, wartości, tło)
- `question` - pytanie ankietowe
- `description` - dodatkowy opis pytania (opcjonalny)
- `options` - lista opcji odpowiedzi

**Używany w:**
- `SurveyResponseGenerator` (app/services/surveys/survey_response_generator.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("surveys.multiple_choice")
rendered = template.render(
    persona_context="Anna, 32 lata, Marketing Manager...",
    question="Które aplikacje fitness używasz?",
    description="Możesz wybrać wiele opcji",
    options="Nike Training Club\nStrava\nFitbit\nInne"
)
```

**Output:** Lista wybranych opcji rozdzielona przecinkami (np. "Nike Training Club, Strava")

---

### `surveys.open_text`

**Plik:** `config/prompts/surveys/open_text.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje odpowiedź tekstową w ankiecie jako konkretna persona

**Parametry:**
- `persona_context` - pełny kontekst persony
- `question` - pytanie ankietowe
- `description` - dodatkowy opis pytania (opcjonalny)

**Używany w:**
- `SurveyResponseGenerator` (app/services/surveys/survey_response_generator.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("surveys.open_text")
rendered = template.render(
    persona_context="Anna, 32 lata, Marketing Manager...",
    question="Co myślisz o produktach ekologicznych?",
    description=""
)
```

**Output:** 2-4 zdania naturalnej odpowiedzi persony

---

### `surveys.rating_scale`

**Plik:** `config/prompts/surveys/rating_scale.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje odpowiedź na skali ocen w ankiecie jako konkretna persona

**Parametry:**
- `persona_context` - pełny kontekst persony
- `question` - pytanie ankietowe
- `description` - dodatkowy opis pytania (opcjonalny)
- `scale_min` - minimalna wartość skali (np. 1)
- `scale_max` - maksymalna wartość skali (np. 10)

**Używany w:**
- `SurveyResponseGenerator` (app/services/surveys/survey_response_generator.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("surveys.rating_scale")
rendered = template.render(
    persona_context="Anna, 32 lata, Marketing Manager...",
    question="Jak oceniasz jakość usług w restauracji?",
    description="1 = bardzo słabo, 10 = doskonale",
    scale_min=1,
    scale_max=10
)
```

**Output:** Pojedyncza liczba (np. "8")

---

### `surveys.single_choice`

**Plik:** `config/prompts/surveys/single_choice.yaml`
**Wersja:** 1.0.0
**Opis:** Generuje odpowiedź jednokrotnego wyboru w ankiecie jako konkretna persona

**Parametry:**
- `persona_context` - pełny kontekst persony
- `question` - pytanie ankietowe
- `description` - dodatkowy opis pytania (opcjonalny)
- `options` - lista opcji odpowiedzi

**Używany w:**
- `SurveyResponseGenerator` (app/services/surveys/survey_response_generator.py)

**Przykład użycia:**
```python
from config import prompts

template = prompts.get("surveys.single_choice")
rendered = template.render(
    persona_context="Anna, 32 lata, Marketing Manager...",
    question="Jak często korzystasz z social media?",
    description="",
    options="Codziennie\nKilka razy w tygodniu\nRzadko\nWcale"
)
```

**Output:** Wybrana opcja (np. "Codziennie")

---

## Prompty Systemowe

### `system.conversational_tone`

**Plik:** `config/prompts/system/conversational_tone.yaml`
**Wersja:** 1.0.0
**Opis:** Styl konwersacyjny - jak rozmowa z kolegą z zespołu, nie czytanie raportu

**Parametry:** brak (prompt modyfikujący)

**Używany w:** Może być kombinowany z innymi promptami dla stylu konwersacyjnego

**Przykład użycia:**
```python
from config import prompts

# Pobierz oba prompty
conversational = prompts.get("system.conversational_tone")
main_prompt = prompts.get("personas.segment_brief")

# Połącz komunikaty systemowe
system_message = conversational.messages[0]["content"] + "\n\n" + main_prompt.messages[0]["content"]
```

**Efekt:** Naturalny, konwersacyjny ton (jak kolega z zespołu, nie raport)

---

### `system.educational`

**Plik:** `config/prompts/system/educational.yaml`
**Wersja:** 1.0.0
**Opis:** Podejście edukacyjne - ucz użytkownika, nie tylko dostarczaj informacji

**Parametry:** brak (prompt modyfikujący)

**Używany w:** Kombinowany z promptami wymagającymi edukacyjnego podejścia (np. orchestration)

**Przykład użycia:**
```python
from config import prompts

educational = prompts.get("system.educational")
# Używane jako część system message
```

**Efekt:** Wyjaśnia "dlaczego", używa analogii, buduje wiedzę stopniowo

---

### `system.formatting_markdown`

**Plik:** `config/prompts/system/formatting_markdown.yaml`
**Wersja:** 1.0.0
**Opis:** Instrukcje formatowania Markdown dla lepszej czytelności (angielski)

**Parametry:** brak (prompt modyfikujący)

**Używany w:** Prompty generujące długi tekst w języku angielskim

**Przykład użycia:**
```python
from config import prompts

formatting = prompts.get("system.formatting_markdown")
# Dodaj do system message dla lepszego formatowania
```

**Efekt:** Output formatowany w Markdown (## headings, **bold**, bullets)

---

### `system.formatting_polish_markdown`

**Plik:** `config/prompts/system/formatting_polish_markdown.yaml`
**Wersja:** 1.0.0
**Opis:** Instrukcje formatowania Markdown dla lepszej czytelności (polski)

**Parametry:** brak (prompt modyfikujący)

**Używany w:** Prompty generujące długi tekst po polsku

**Przykład użycia:**
```python
from config import prompts

formatting = prompts.get("system.formatting_polish_markdown")
# Dodaj do system message dla lepszego formatowania
```

**Efekt:** Output formatowany w Markdown (## nagłówki, **pogrubienie**, wypunktowania)

---

### `system.json_output`

**Plik:** `config/prompts/system/json_output.yaml`
**Wersja:** 1.0.0
**Opis:** Instrukcje outputu JSON - ścisłe formatowanie dla parsowalnych odpowiedzi

**Parametry:** brak (prompt modyfikujący)

**Używany w:** Wszystkie prompty wymagające outputu JSON (orchestration, jtbd, itp.)

**Przykład użycia:**
```python
from config import prompts

json_instructions = prompts.get("system.json_output")
# Kombinuj z głównym promptem dla ścisłego JSON
```

**Efekt:** Wymusza poprawny JSON bez markdown code blocks, text wrappers, trailing commas

---

### `system.market_research_expert`

**Plik:** `config/prompts/system/market_research_expert.yaml`
**Wersja:** 1.0.0
**Opis:** Ekspert systemowy prompt dla analizy badań rynkowych - strategiczne wnioski dla zespołów produktowych

**Parametry:** brak (prompt systemowy)

**Używany w:**
- `DiscussionSummarizer` (podsumowania grup fokusowych)
- Inne serwisy wymagające ekspertyzy market research

**Przykład użycia:**
```python
from config import prompts

expert = prompts.get("system.market_research_expert")
system_message = expert.messages[0]["content"]
```

**Efekt:** Analiza z perspektywy eksperta market research (actionable insights, wzorce, rekomendacje strategiczne)

---

### `system.market_research_expert` (wariant B)

**Plik:** `config/prompts/system/market_research_expert_variant_b.yaml`
**Wersja:** 1.1.0
**Opis:** Ekspert systemowy prompt dla market research - WARIANT B (bardziej zwięzły)
**Wariant:** b

**Parametry:** brak (prompt systemowy)

**Używany w:** Testy A/B promptów (bardziej zwięzła wersja eksperta)

**Przykład użycia:**
```python
from config import prompts

# Losowy ważony wybór
expert = prompts.get("system.market_research_expert")

# Lub konkretny wariant
expert_b = prompts.get("system.market_research_expert", variant="b")
```

**Efekt:** Bardziej zwięzła wersja eksperta (fokus na actionable insights, bez zbędnych słów)

---

### `system.polish_society_expert`

**Plik:** `config/prompts/system/polish_society_expert.yaml`
**Wersja:** 1.0.0
**Opis:** Ekspert w dziedzinie socjologii i badań społecznych w Polsce - oparty na rzeczywistych danych

**Parametry:** brak (prompt systemowy)

**Używany w:**
- `PersonaOrchestrationService` (orchestration)
- `SegmentBriefService` (briefe segmentów)
- Wszystkie serwisy wymagające wiedzy o polskim społeczeństwie

**Przykład użycia:**
```python
from config import prompts

expert = prompts.get("system.polish_society_expert")
system_message = expert.messages[0]["content"]
```

**Efekt:** Analiza z perspektywy eksperta socjologii polskiej (konkretne liczby, źródła GUS/CBOS, kontekst społeczno-ekonomiczny)

---

### `system.quality_control`

**Plik:** `config/prompts/system/quality_control.yaml`
**Wersja:** 1.0.0
**Opis:** Specjalista kontroli jakości dla weryfikacji treści generowanych przez AI

**Parametry:** brak (prompt systemowy)

**Używany w:** Potencjalnie do walidacji wygenerowanych person / treści (obecnie nie używany w produkcji)

**Przykład użycia:**
```python
from config import prompts

qc = prompts.get("system.quality_control")
# Używane do weryfikacji wygenerowanych person
```

**Efekt:** Weryfikuje spójność, realizm, język polski, brak stereotypów

---

### `system.storytelling`

**Plik:** `config/prompts/system/storytelling.yaml`
**Wersja:** 1.0.0
**Opis:** Utalentowany storyteller tworzący angażujące narracje z danych

**Parametry:** brak (prompt modyfikujący)

**Używany w:** Kombinowany z briefami segmentów dla podejścia storytellingowego

**Przykład użycia:**
```python
from config import prompts

storytelling = prompts.get("system.storytelling")
# Używane jako część system message dla briefów
```

**Efekt:** Hook na początku, emotional connection, konkretne przykłady, actionable insights na końcu

---

## 🔍 Szybkie Wyszukiwanie

### Po Kategorii
- **Grupy Fokusowe** - discussion_summary, persona_response
- **Persony** - jtbd, orchestration, persona_generation_system, persona_uniqueness, segment_brief, segment_context, segment_name
- **RAG** - cypher_generation, graph_rag_answer
- **Ankiety** - multiple_choice, open_text, rating_scale, single_choice
- **Systemowe** - conversational_tone, educational, formatting_markdown, formatting_polish_markdown, json_output, market_research_expert, polish_society_expert, quality_control, storytelling

### Po Serwisie

**PersonaGeneratorLangChain:**
- personas.persona_generation_system

**PersonaOrchestrationService:**
- personas.orchestration
- personas.segment_name
- personas.segment_context
- system.polish_society_expert

**SegmentBriefService:**
- personas.segment_brief
- system.polish_society_expert
- system.storytelling

**PersonaNeedsService:**
- personas.jtbd

**PersonaDetailsService:**
- personas.persona_uniqueness

**FocusGroupServiceLangChain:**
- focus_groups.persona_response

**DiscussionSummarizer:**
- focus_groups.discussion_summary
- system.market_research_expert

**GraphRAGService:**
- rag.cypher_generation
- rag.graph_rag_answer
- system.polish_society_expert

**SurveyResponseGenerator:**
- surveys.single_choice
- surveys.multiple_choice
- surveys.rating_scale
- surveys.open_text

---

## 📚 Dodatkowe Zasoby

**Główna dokumentacja:**
- `config/README.md` - Kompletny przewodnik po systemie konfiguracji
- `config/models.yaml` - Rejestr modeli (fallback chain)
- `config/pricing.yaml` - Ceny modeli dla śledzenia kosztów

**Walidacja:**
```bash
# Waliduj wszystkie prompty
python scripts/config_validate.py

# Sprawdź placeholdery
python scripts/config_validate.py --check-placeholders

# Auto-bump wersji
python scripts/config_validate.py --auto-bump
```

**Testy:**
```bash
# Test rejestru promptów
pytest tests/config/test_prompt_registry.py -v

# Test rejestru modeli
pytest tests/config/test_model_registry.py -v
```

---

**Ostatnia aktualizacja:** 2025-10-27