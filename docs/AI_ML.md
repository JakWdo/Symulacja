# System AI/ML w Sight

## Wprowadzenie

System AI/ML w naszej platformie zajmuje się generowaniem wiarygodnych person, prowadzeniem wirtualnych grup fokusowych i ekstrakcją wiedzy z danych społecznych. Wykorzystuje zaawansowane modele Google Gemini, techniki Retrieval Augmented Generation (RAG) oraz inteligentne strategie przetwarzania języka naturalnego.

## Architektura AI/ML

```
User Input → Orchestration → Generation → Memory → Analysis
    ↓           ↓             ↓           ↓         ↓
Demographic   Segment      Persona     Event     Insights
  Context    Definition   Generation  Sourcing   Extraction
```

## Komponenty Kluczowe

### 1. Generacja Person

#### Strategia Generacji
- Model: Gemini 2.5 Flash
- Metoda: Segment-based generacja
- Constrainty demograficzne:
  - Precyzyjne bounds (wiek, płeć, wykształcenie)
  - Walidacja statystyczna
  - Kontekst społeczny per segment

#### Przykładowy Segment
```python
segment = SegmentDefinition(
    segment_id="seg_young_precariat",
    segment_name="Młodzi Prekariusze",
    demographics=DemographicConstraints(
        age_min=18,
        age_max=24,
        gender="kobieta",
        education_levels=["wyższe"],
        income_brackets=["<3000 PLN"]
    )
)
```

### 2. Grupy Fokusowe

#### Orkiestracja
- Równoległe generowanie odpowiedzi
- Zarządzanie pamięcią kontekstu
- Asyncio dla wydajności

```python
async def run_focus_group(personas, questions):
    tasks = [
        _generate_response_for_persona(persona, question)
        for persona in personas
        for question in questions
    ]
    responses = await asyncio.gather(*tasks)
```

### 3. Hybrid Search RAG

#### Komponenty
- Wyszukiwanie wektorowe
- Wyszukiwanie słownikowe
- Reranking z cross-encoder
- Fuzja RRF (Reciprocal Rank Fusion)

#### Workflow
```
Query → Vector Search → Keyword Search → RRF Fusion → Cross-Encoder Rerank → Final Results
```

### 4. Konfiguracja LLM

#### Gemini 2.5
- **Flash:** Szybkie, krótkie operacje
  - Koszt: $0.00005/1k tokenów (input)
  - Latencja: 1-3s
  - Użycie: Generacja person, odpowiedzi

- **Pro:** Złożone analizy
  - Koszt: $0.00125/1k tokenów (input)
  - Latencja: 3-5s
  - Użycie: Podsumowania, insights

### 5. Optymalizacja

#### Strategie
- Równoległe wywołania LLM (asyncio.gather)
- Rate limiting
- Retry z exponential backoff
- Kompresja promptów
- Budżety tokenowe

## Zapewnienie Jakości

### Walidacja
- Statystyczna (test Chi-kwadrat)
- Spójność cech osobowości
- Walidacja kulturowa (wymiary Hofstede)
- Prewencja hallucynacji

### Metryki
- Scoring person (0-100)
- Kontrola długości odpowiedzi
- Sprawdzanie spójności

## Perspektywy Rozwoju

- Rozbudowa segmentów demograficznych
- Zwiększenie precyzji RAG
- Optymalizacja kosztów AI

---

## Szczegółowy Widok Persony (Persona Details)

System szczegółowego widoku persony stanowi kluczowy interfejs analityczny platformy, umożliwiający marketerom, badaczom i product managerom dogłębną analizę wygenerowanych person. Funkcjonalność została zaimplementowana w wersji MVP z wykorzystaniem service layer pattern oraz zaawansowanych technik AI/ML dla estymacji metryk biznesowych.

### Główne Zastosowania

Szczegółowy widok persony służy trzem podstawowym celom biznesowym. Pierwszy z nich to analiza KPI - system automatycznie estymuje kluczowe metryki marketingowe takie jak wielkość segmentu, conversion rate, retention rate, Net Promoter Score oraz wskaźniki LTV i CAC. Drugi cel to pełna charakterystyka persony, obejmująca demografię, psychografię (Big Five, wymiary Hofstede), wartości i zainteresowania. Trzeci obszar to śledzenie historii - każda akcja na personie jest logowana w systemie audytu, co zapewnia pełną transparentność i zgodność z wymogami regulacyjnymi.

Typowy use case obejmuje scenariusz, w którym marketer przegląda listę wygenerowanych person, wybiera interesującą personę i klika "Szczegółowy widok". System otwiera drawer (70% szerokości ekranu) z trzema zakładkami: Overview (KPI cards w układzie 2x3), Profile (demografia i Big Five), oraz Insights (kontekst RAG i audit log). Marketer może następnie eksportować personę, porównywać z innymi lub usunąć ją z systemu z podaniem powodu.

### Architektura Rozwiązania

Backend oparty jest na trzech głównych serwisach pracujących w orchestration pattern. `PersonaDetailsService` pełni rolę głównego orkiestratora, który za pomocą `asyncio.gather` równolegle pobiera dane z różnych źródeł. `PersonaKPIService` odpowiada za kalkulację metryk biznesowych wykorzystując heurystyki demograficzne oraz industry benchmarks dla branży B2B SaaS. `PersonaAuditService` zarządza audit trail, logując wszystkie akcje użytkowników na personach.

Frontend wykorzystuje React 18 z TypeScript oraz TanStack Query do zarządzania stanem serwera. Główny komponent `PersonaDetailsDrawer` (Sheet z 70% szerokością) zawiera trzy sekcje: `OverviewSection` wyświetlającą KPI cards z trend indicators, `ProfileSection` prezentującą demografię i skalę Big Five z progress bars, oraz `InsightsSection` pokazującą metadane RAG oraz timeline audit log. Komponent `DeletePersonaDialog` obsługuje usuwanie person z walidacją powodu oraz potwierdzeniem cascade effects.

Przepływ danych rozpoczyna się od kliknięcia "Szczegółowy widok" przez użytkownika. Frontend wysyła GET request na `/personas/{id}/details`, backend pobiera base persona data z PostgreSQL, a następnie równolegle fetchuje KPI snapshot (cache lub recalculation) oraz audit log (ostatnie 20 akcji). System merguje dane do PersonaDetailsResponse i zwraca do frontendu, który renderuje drawer z danymi. Dodatkowo w tle (async task) logowany jest event "view" w audit log.

### Baza Danych i Struktura

Model `Persona` został rozszerzony o trzy kluczowe JSONB fields. Pole `kpi_snapshot` przechowuje cached metryki KPI z timestampem, segment_size, conversion/retention rates, NPS score, LTV, CAC, benchmarks branżowe, źródła danych oraz confidence score. Pole `customer_journey` (Post-MVP) będzie zawierało 4 etapy customer journey (Awareness, Consideration, Decision, Post-Purchase) z touchpoints, emocjami i pain points dla każdego etapu. Pole `needs_and_pains` (Post-MVP) będzie przechowywało jobs-to-be-done framework z zadaniami funkcjonalnymi, desired outcomes oraz pain points.

Tabela `persona_audit_log` stanowi fundament systemu audytu. Każdy rekord zawiera persona_id (FK z CASCADE delete), user_id (FK z SET NULL), action (np. "view", "export", "delete"), details (JSONB z dodatkowymi informacjami), ip_address (opcjonalne, retention 90 dni dla GDPR), user_agent oraz timestamp. Tabela jest indeksowana przez composite index (persona_id, timestamp DESC) oraz (user_id, timestamp DESC) dla szybkich queries w admin dashboard.

### Integracja AI/ML

Estymacja KPI wykorzystuje trzystopniową strategię wyboru źródła danych. W pierwszej kolejności sprawdzana jest integracja CRM/CDP (Salesforce, HubSpot) dla real data. Jeśli niedostępna, system próbuje pobrać dane z integracji Analytics (Google Analytics, Mixpanel) dla behavioral metrics. W wersji MVP stosowana jest AI estimation z heurystykami demograficznymi oraz industry benchmarks.

Algorytm heurystycznej estymacji segment_size działa następująco. Bazowa populacja Polski wynosi 38 milionów. System nakłada filtry demograficzne: age filter (10-year span ≈ 15% populacji), gender filter (Kobieta: 52%, Mężczyzna: 48%, Osoba niebinarna: 2%), education filter (wyższe wykształcenie: 25% populacji), income filter (średni przedział: 20%), oraz location filter (konkretne miasto: 8%, cała Polska: 100%). Estimate jest obliczany jako iloczyn: 38M × age_filter × gender_filter × education_filter × income_filter × location_filter, z minimum threshold 1000 osób.

Industry benchmarks dla branży B2B SaaS wykorzystują następujące wartości standardowe: conversion_rate = 12%, retention_rate = 85%, NPS score = 45 (good), LTV = avg_income × 0.3 × 3 years, CAC = LTV × 0.15 (15% of LTV), confidence_score = 0.70 (niższe dla AI estimation vs real data). System porównuje również estymat z industry averages (conversion: 10%, retention: 80%, NPS: 40) aby pokazać performance vs benchmark.

W przyszłości planowane jest LLM-powered customer journey generation przy użyciu Gemini 2.5 Pro. System będzie generował 4 etapy journey z typical_questions, buying_signals, recommended_touchpoints (z priorytetem, expected_impact, effort), avg_time_in_stage_days oraz drop_off_rate. Druga planowana funkcja to Jobs-to-be-done extraction z RAG, gdzie LLM ekstrahuje functional/emotional jobs, desired outcomes oraz pain points z dokumentów RAG oraz historii focus groups.

### Workflow Użytkownika

Typowy scenariusz rozpoczyna się w liście person. Użytkownik klika dropdown menu (three dots) przy personie i wybiera "Szczegółowy widok". System otwiera drawer (Sheet 70% width) z prawej strony ekranu. Podczas ładowania wyświetlany jest skeleton loader, a następnie renderowane są trzy zakładki.

W zakładce Overview użytkownik widzi grid 2x3 z KPI cards: Segment Size (liczba osób w segmencie + trend), Conversion Rate (% z trend indicator), Retention Rate (% z trend indicator), NPS Score (0-100 z trend indicator), LTV (Lifetime Value w PLN z trend indicator), CAC (Customer Acquisition Cost w PLN z trend indicator). Każda karta pokazuje również delta vs poprzedni okres oraz trend direction (up/down/stable) z kolorowymi strzałkami.

W zakładce Profile prezentowana jest demografia (wiek, płeć, wykształcenie, dochód, lokalizacja, zawód) oraz psychografia. Skala Big Five wyświetlana jest jako 5 progress bars (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism), a wymiary kulturowe Hofstede (Power Distance, Individualism, Masculinity, Uncertainty Avoidance, Long-term Orientation, Indulgence) również jako progress bars. Dodatkowo pokazywane są values i interests jako badge components oraz background story jako tekst narracyjny.

Zakładka Insights zawiera metadane RAG (search_type: hybrid/graph, num_results, graph_nodes_count, orchestration_reasoning) oraz graph nodes visualization (lista węzłów z relationships). Timeline audit log pokazuje ostatnie 20 akcji z typami (view, export, compare, delete, update), timestampem, użytkownikiem oraz details (filtered - bez IP/user agent).

Użytkownik może również usunąć personę poprzez Delete button (dostępny dla Admin role). System otwiera AlertDialog z potwierdzeniem, dropdown z powodem (duplicate, outdated, test_data, other), textarea dla "other reason detail" oraz warning o cascade effects (responses, events, analytics). Po potwierdzeniu następuje soft delete (is_active=False), logowanie w audit trail oraz pokazanie toast notification z potwierdzeniem.

### Wydajność Systemu

Strategia cache'owania działa na dwóch poziomach. KPI snapshot jest cache'owany w JSONB field `persona.kpi_snapshot` z timestampem. Jeśli snapshot jest świeży (< 5min old), używany jest cached value. Po upływie 5 minut następuje recalculation w tle z update JSONB field. Full detail response (Post-MVP) będzie cache'owany w Redis z TTL 5min, co da cache hit < 50ms vs cache miss < 500ms.

Parallel fetching wykorzystuje `asyncio.gather` dla równoległego pobierania KPI snapshot, customer journey (Post-MVP), needs & pains (Post-MVP) oraz audit log. Wykorzystywany jest flag `return_exceptions=True` dla graceful degradation - jeśli KPI calculation failuje, system zwraca partial response bez KPI ale z pozostałymi danymi.

Audit logging jest async i non-blocking. View event jest logowany przez `asyncio.create_task` w tle, co nie blokuje HTTP response. W przypadku failowania audit log, system loguje warning ale nie propaguje exception (graceful degradation).

Target performance metrics wynoszą: GET `/personas/{id}/details` cache miss < 500ms P95 (parallel fetch + 1 DB query), audit log query < 50ms P95 (index na persona_id + timestamp DESC, limit 20), KPI calculation < 300ms P95 (heurystyki + arithmetic, brak LLM calls). Drawer render time to < 2s TTI (Time to Interactive) z lazy loading dla tabs.

### Znane Ograniczenia MVP

Wersja MVP posiada kilka świadomych ograniczeń. Brak Redis caching oznacza, że każdy request robi DB queries zamiast cache hit < 50ms. Brak RBAC enforcement powoduje, że endpoint `/personas/{id}/details` nie sprawdza user role (production wymaga Viewer+). Simplified KPI estimation wykorzystuje hardcoded benchmarks zamiast real CRM integration czy LLM extraction z RAG. Brak Undo delete oznacza, że soft delete jest nieodwracalne (SHOULD HAVE feature).

Code review zidentyfikował również trzy critical issues wymagające naprawy. Race condition w KPI calculation - concurrent calculations dla tej samej persony mogą nadpisać swoje wyniki (wymaga distributed locking via Redis). DB session leak w background tasks - `asyncio.create_task` dla audit logging używa `self.db` która może być już closed (wymaga nowej AsyncSession w task). Missing `cac_ltv_ratio` field - frontend używa tego pola ale backend schema go nie zwraca (wymaga dodania do KPISnapshot + calculation w service).

### Roadmap Post-MVP

Planowane rozszerzenia obejmują pełne Customer Journey generation z wykorzystaniem Gemini 2.5 Pro, gdzie LLM generuje 4 etapy journey z touchpoints, emocjami, buying signals oraz recommended actions. Kolejna funkcja to Export functionality umożliwiająca export do PDF/CSV/JSON z PII masking (Admin może unmask), watermarks oraz selective sections (overview/profile/behaviors).

Compare personas feature pozwoli porównać do 3 person side-by-side, z highlight differences, similarity score (cosine similarity na embeddings) oraz shareable comparison URL (30-day expiry). Real-time collaboration wprowadzi WebSocket comments, @mentions z email notifications, tasks assigned do person oraz status workflow (draft/active/archived/needs_review).

Advanced KPI features będą obejmować CRM integration (Salesforce, HubSpot API) dla real conversion/retention data, Analytics integration (Google Analytics, Mixpanel) dla behavioral metrics, LLM-powered customer journey z RAG context oraz scheduled background job dla periodic KPI recalculation (co 5min).

### Quick Start dla Deweloperów

Aby uruchomić funkcjonalność lokalnie, należy wykonać migrację bazy danych: `docker-compose exec api alembic upgrade head`, zrestartować API: `docker-compose restart api`, oraz przetestować endpoint: `curl http://localhost:8000/api/v1/personas/{id}/details -H "Authorization: Bearer {token}"`.

Dla nowych deweloperów polecane jest przeczytanie dokumentacji w następującej kolejności: najpierw `docs/PERSONA_DETAILS_BUSINESS_ANALYSIS.md` (42 user stories, priorytetyzacja MoSCoW), następnie `docs/PERSONA_DETAILS_ARCHITECTURE.md` (database schema, service layer, caching strategy), potem `docs/PERSONA_DETAILS_API_CONTRACTS.md` (API endpoints, request/response schemas, error handling), oraz na końcu `docs/CODE_REVIEW_PERSONA_DETAILS_MVP.md` (critical issues, quality score 7.5/10, approval z fixami).

Kluczowe pliki kodu backendu to: `app/services/persona_details_service.py` (orchestrator, 280 linii), `app/services/persona_kpi_service.py` (KPI calculation, 226 linii), `app/services/persona_audit_service.py` (audit logging), `app/models/persona_audit.py` (audit log model), `app/schemas/persona_details.py` (Pydantic schemas), `app/api/personas.py` (GET /details endpoint lines 1515-1575), oraz `alembic/versions/20251016_add_persona_details_mvp.py` (migration).

Kluczowe pliki kodu frontendu to: `frontend/src/components/personas/PersonaDetailsDrawer.tsx` (main component, Sheet 70%), `frontend/src/components/personas/OverviewSection.tsx` (KPI cards grid 2x3), `frontend/src/components/personas/ProfileSection.tsx` (demografia + Big Five progress bars), `frontend/src/components/personas/InsightsSection.tsx` (RAG metadata + audit timeline), `frontend/src/components/personas/DeletePersonaDialog.tsx` (delete confirmation z powodem), `frontend/src/hooks/usePersonaDetails.ts` (React Query hook, staleTime 5min), `frontend/src/hooks/useDeletePersona.ts` (mutation hook z cache invalidation), oraz `frontend/src/types/index.ts` (TypeScript interfaces).

---

**Wersja:** 1.3
**Ostatnia aktualizacja:** 2025-10-16
**Jakość AI:** 8.2/10
