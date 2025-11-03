# Persona Details - Szczegółowy Widok Persony

**Wersja:** 3.0 (Uproszczona architektura)
**Data:** 2025-10-16
**Status:** ✅ Zaimplementowane (MVP)

---

## Spis Treści

1. [Cel Biznesowy](#1-cel-biznesowy)
2. [Database Schema](#2-database-schema)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [API Contracts](#5-api-contracts)
6. [Implementation Status](#6-implementation-status)
7. [Known Issues](#7-known-issues)

---

## 1. Cel Biznesowy

Szczegółowy widok persony dostarcza marketerom i badaczom rynku **skoncentrowane informacje o potrzebach i kontekście demograficzno-społecznym** wygenerowanych person. System koncentruje się na realnych problemach i zadaniach użytkowników końcowych, unikając szacunkowych metryk biznesowych, które mogłyby sugerować wyższą pewność danych niż jest to uzasadnione.

### Kluczowe wartości

Panel szczegółów persony oferuje wgląd w trzy główne obszary, z których wszystkie są generowane przez system AI z wykorzystaniem danych z grup fokusowych oraz kontekstu z systemu RAG (GUS, CBOS, badania rynku):

**1. Profil demograficzny i psychograficzny**
Pełny opis persony obejmujący wiek, płeć, zawód, wykształcenie, dochody oraz cechy osobowościowe (Big Five, wartości, zainteresowania). Dane te pochodzą z procesu generowania person przez system orkiestracji, który łączy statystyki GUS z profilami psychograficznymi ekstrapolowanymi z badań społecznych.

**2. Potrzeby i bóle (Jobs-to-be-Done)**
Analiza Jobs-to-be-Done (JTBD) identyfikuje kluczowe zadania, które persona chce wykonać, pożądane rezultaty oraz największe punkty bólu. System ekstrahuje te informacje z odpowiedzi person w wirtualnych grupach fokusowych, używając modelu językowego Gemini 2.0 Flash z wyjściem strukturalnym (Pydantic). Analiza uwzględnia również kontekst RAG - dane o rzeczywistych wyzwaniach demograficznych i ekonomicznych segmentu, do którego należy persona.

**3. Kontekst RAG i historia aktywności**
Szczegóły kontekstu RAG wykorzystanego podczas generowania persony (nazwa segmentu, opis, kontekst społeczny z dokumentów badawczych) oraz dziennik audytowy przedstawiający historię interakcji z personą (wyświetlenia, eksporty, porównania, usunięcia).

### Decyzje architektoniczne

System został uproszczony w październiku 2025 roku poprzez usunięcie dwóch elementów, które wprowadzały niepewność w interpretacji danych:

**Usunięte funkcjonalności:**
- **KPI Metrics (PersonaKPIService)** - Szacunkowe metryki biznesowe (conversion rate, retention, NPS, LTV, CAC) sugerowały wyższy poziom pewności niż był uzasadniony. Metryki te były szacunkami opartymi wyłącznie na heurystykach i benchmarkach branżowych, bez rzeczywistych danych transakcyjnych.
- **Customer Journey (PersonaJourneyService)** - Generowane przez LLM czteroetapowe ścieżki zakupowe (Awareness → Consideration → Decision → Post-Purchase) były zbyt generyczne i nie dostarczały wartości dodanej w kontekście badań rynkowych.

**Zachowane i rozwinięte:**
- **PersonaNeedsService** - Analiza Jobs-to-be-Done i pain points pozostaje głównym elementem wartości, ponieważ bazuje na realnych wypowiedziach person w wirtualnych grupach fokusowych oraz kontekście demograficzno-społecznym z systemu RAG.

### Kluczowe metryki wydajności

- **Time-to-Insight**: < 50ms (cached data), < 3s (fresh data z LLM)
- **Action Velocity**: ≤ 3 kliknięcia dla eksportu, porównania person
- **Cache Strategy**: Redis 1h TTL ze smart invalidation (klucz cache zawiera `updated_at` persony)

---

## 2. Database Schema

### 2.1. Tabela `personas` - Rozszerzone pola

System dodaje do tabeli `personas` jedno kluczowe pole JSONB przechowujące obliczone dane potrzeb i bólów:

```python
# app/models/persona.py - COMPUTED FIELDS

needs_and_pains = Column(JSONB, nullable=True)
"""
Struktura danych Jobs-to-be-Done + Pain Points:
{
  "generated_at": "2025-10-16T14:30:00Z",
  "generated_by": "gemini-2.0-flash-exp",
  "jobs_to_be_done": [
    {
      "job_statement": "When [situation], I want [motivation], so I can [outcome]",
      "priority_score": 9,
      "frequency": "monthly",
      "difficulty": "hard",
      "quotes": ["Cytat z grupy fokusowej..."]
    }
  ],
  "desired_outcomes": [
    {
      "outcome_statement": "Zaoszczędzić 50% czasu na raportowaniu",
      "importance": 9,
      "satisfaction_current_solutions": 4,
      "opportunity_score": 45,  # importance * (importance - satisfaction)
      "is_measurable": true
    }
  ],
  "pain_points": [
    {
      "pain_title": "Manualne wprowadzanie danych",
      "pain_description": "5+ godzin tygodniowo na ręczne kopiowanie danych z wielu źródeł",
      "severity": 8,
      "frequency": "daily",
      "percent_affected": 0.75,
      "quotes": ["Marnuję pół dnia co tydzień kopiując dane."],
      "potential_solutions": ["Automatyczna synchronizacja", "Zunifikowany dashboard"]
    }
  ]
}
"""
```

**Pola segment tracking** (dodane w migracji `20251015_add_segment_tracking_to_personas`):
```python
segment_id = Column(String(100), nullable=True, index=True)
segment_name = Column(String(255), nullable=True)
```

**Pola soft delete** (dodane w migracji `20251016_add_persona_delete_metadata`):
```python
deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
deleted_by = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
```

### 2.2. Tabela `persona_audit_log`

Dziennik audytowy wszystkich akcji wykonanych na personie (GDPR compliance, accountability):

```python
# app/models/persona_audit.py

class PersonaAuditLog(Base):
    __tablename__ = "persona_audit_log"

    id = Column(UUID, primary_key=True, default=uuid4)
    persona_id = Column(UUID, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # "view", "export", "compare", "delete", "update"
    details = Column(JSON, nullable=True)  # Action-specific metadata
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 (90-day retention dla GDPR)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# Indexes dla performance
Index('idx_audit_persona_time_desc', PersonaAuditLog.persona_id, PersonaAuditLog.timestamp.desc())
Index('idx_audit_user_id', PersonaAuditLog.user_id)
Index('idx_audit_action', PersonaAuditLog.action)
```

**Polityka retencji (GDPR):**
- IP addresses i user agents są usuwane automatycznie po 90 dniach
- Wymaga schedulowanego joba czyszczącego (TODO: implementacja w Celery)

### 2.3. Historia migracji

System przeszedł następujące zmiany schematu bazy danych:

1. **`20251015_add_segment_tracking_to_personas`** - Dodanie pól `segment_id`, `segment_name` dla identyfikacji segmentów demograficznych
2. **`20251016_add_persona_details_mvp`** - Dodanie pól `kpi_snapshot`, `customer_journey`, `needs_and_pains` oraz tabeli `persona_audit_log`
3. **`20251016_add_persona_delete_metadata`** - Dodanie pól `deleted_at`, `deleted_by` dla soft delete
4. **`20251016_remove_kpi_journey_fields`** - **Usunięcie** pól `kpi_snapshot`, `customer_journey` i indeksu GIN jako część uproszczenia architektury

**Obecny stan schematu:**
- ✅ `needs_and_pains` (JSONB) - jedyne obliczane pole persony
- ✅ `segment_id`, `segment_name` - tracking segmentów
- ✅ `deleted_at`, `deleted_by` - soft delete
- ✅ `rag_context_details` (JSONB) - kontekst RAG z orkiestracji
- ✅ `persona_audit_log` (tabela) - dziennik audytowy
- ❌ `kpi_snapshot` - USUNIĘTE
- ❌ `customer_journey` - USUNIĘTE

---

## 3. Backend Architecture

### 3.1. Service Layer Overview

Backend dla szczegółowego widoku persony składa się z trzech kluczowych serwisów:

```
PersonaDetailsService (orchestrator)
    ↓
    ├─→ PersonaNeedsService (JTBD + pain points z focus groups + RAG)
    └─→ PersonaAuditService (dziennik audytowy)
```

### 3.2. PersonaDetailsService - Główny Orchestrator

Orchestrator odpowiedzialny za składanie pełnego widoku szczegółów persony z cache'owaniem i graceful degradation.

**Kluczowe cechy:**
- **Smart cache key**: Klucz Redis zawiera `persona.updated_at` timestamp, dzięki czemu cache automatycznie invaliduje się przy edycji persony
- **Długi TTL**: 1 godzina (vs. poprzednio 5 minut) - bezpieczne dzięki smart cache key
- **Parallel fetch**: `asyncio.gather()` dla równoczesnego pobierania needs i audit log
- **Graceful degradation**: Jeśli któraś operacja failuje (np. timeout LLM), zwraca partial data zamiast całkowitego błędu
- **Async audit logging**: Zapis do audit log odbywa się w tle (create_task) z własną sesją DB, nie blokuje HTTP response

**Performance:**
- Cache hit: < 50ms (Redis)
- Cache miss (z LLM call): < 3s (dzięki structured output i optymalizacjom tokenów)

**Przykład użycia:**
```python
details_service = PersonaDetailsService(db)
details = await details_service.get_persona_details(
    persona_id=uuid,
    user_id=current_user.id,
    force_refresh=False  # True bypass'uje cache
)
```

### 3.3. PersonaNeedsService - Jobs-to-be-Done Analysis

Serwis ekstrahujący Jobs-to-be-Done, desired outcomes i pain points z odpowiedzi person w wirtualnych grupach fokusowych.

**Optymalizacje wydajnościowe (październik 2025):**
- **Structured output**: Używa `.with_structured_output(NeedsAndPains)` zamiast parsowania JSON - eliminuje błędy parsowania i redukuje tokeny
- **Redukcja focus group responses**: 20 → 10 ostatnich odpowiedzi dla szybszości
- **Niższa temperatura**: 0.35 → 0.25 dla bardziej deterministycznego i szybszego inferencingu
- **Redukcja max_tokens**: 6000 → 2000 (wystarczające dla danych JTBD)
- **Integracja RAG context**: Analiza uwzględnia kontekst demograficzny i społeczny segmentu z systemu RAG

**Proces generowania:**
1. Pobiera ostatnie 10 odpowiedzi persony z grup fokusowych
2. Ekstrahuje kontekst RAG z `persona.rag_context_details` (segment_social_context, graph_context)
3. Buduje prompt zawierający profil persony, odpowiedzi oraz kontekst RAG
4. Wywołuje Gemini 2.0 Flash z wyjściem strukturalnym (Pydantic model `NeedsAndPains`)
5. Dodaje metadata (generated_at, generated_by) i zwraca dict

**Target latency**: < 2s (down z poprzednich 2-3s)

**Przykład struktury JTBD:**
```json
{
  "jobs_to_be_done": [
    {
      "job_statement": "When I'm planning quarterly budget, I want to forecast ROI accurately, so I can justify spend to CFO.",
      "priority_score": 9,
      "frequency": "monthly",
      "difficulty": "hard",
      "quotes": ["Spędzam 2 dni co kwartał budując prognozy w Excelu."]
    }
  ]
}
```

### 3.4. PersonaAuditService - Audit Trail

Serwis odpowiedzialny za rejestrowanie wszystkich akcji wykonywanych na personie (GDPR compliance, accountability).

**Wspierane akcje:**
- `view` - Wyświetlenie szczegółów persony
- `export` - Eksport persony do JSON/PDF/CSV
- `compare` - Porównanie z innymi personami
- `delete` - Usunięcie persony (soft delete)
- `update` - Modyfikacja danych persony
- `generate_messaging` - Generowanie komunikacji marketingowej

**Kluczowe cechy:**
- **Graceful degradation**: Niepowodzenie zapisu do audit log nie przerywa głównej operacji (tylko warning w logach)
- **GDPR compliance**: IP adresy i user agents muszą być usuwane po 90 dniach (wymaga schedulowanego joba)
- **Własna sesja DB**: Audit log używa `AsyncSessionLocal()` dla niezależnych transakcji

**Przykład użycia:**
```python
await audit_service.log_action(
    persona_id=uuid,
    user_id=current_user.id,
    action="export",
    details={"format": "json", "sections": ["overview", "needs"]},
    db=db
)
```

### 3.5. Usunięte serwisy

Następujące serwisy zostały usunięte w ramach uproszczenia architektury (październik 2025):

- **`PersonaKPIService`** - Szacowanie metryk biznesowych (conversion rate, retention, NPS, LTV, CAC) było oparte wyłącznie na heurystykach i nie dostarczało wartości biznesowej uzasadniającej złożoność
- **`PersonaJourneyService`** - Generowanie customer journey (4 etapy) przez LLM było zbyt generyczne i nie różniło się znacząco między personami

**Uzasadnienie:**
System koncentruje się teraz na danych, które mają solidne źródło (focus group responses + RAG context) zamiast szacunków, które mogłyby sugerować wyższą pewność niż jest uzasadniona.

---

## 4. Frontend Architecture

### 4.1. Component Tree

Szczegółowy widok persony jest zaimplementowany jako prawostronny drawer (Sheet) z nawigacją po czterech sekcjach:

```
PersonaDetailsDrawer (Sheet)
├── SheetHeader (sticky top)
│   ├── Persona name, age, occupation, location
│   └── Close button
│
├── Navigation (Left sidebar desktop / Select dropdown mobile)
│   ├── Przegląd (Overview)
│   ├── Profil (Profile)
│   ├── Potrzeby i bóle (Needs)
│   └── Insights (RAG context + audit log)
│
├── Main Content Area
│   ├── OverviewSection - podstawowe info + segment badge
│   ├── ProfileSection - demografia + psychografia (Big Five)
│   ├── NeedsSection - JTBD + pain points
│   └── InsightsSection - RAG context + audit log timeline
│
└── PersonaActionsRail (Right sidebar)
    ├── Generate Messaging (dialog)
    ├── Compare Personas (dialog)
    ├── Export (JSON)
    └── Delete (soft delete z undo - dialog)
```

### 4.2. Kluczowe komponenty

#### PersonaDetailsDrawer

Główny komponent drawera używający React Query dla data fetching i cache management.

**Features:**
- **Loading states**: Skeleton loaders dla lepszego UX
- **Error handling**: Przyjazne komunikaty błędów (404, network errors)
- **Responsive navigation**: Left sidebar na desktop, dropdown select na mobile
- **Lazy rendering**: Sekcje renderowane on-demand przy przełączaniu
- **Framer Motion animations**: Płynne transitions przy otwieraniu/zamykaniu

**React Query hook:**
```tsx
const { data: persona, isLoading, error } = usePersonaDetails(personaId);
// - Stale time: 5 minut (matches backend cache)
// - Retry: max 2 (nie retry dla 404)
// - Refetch on mount: always (background refresh)
```

#### OverviewSection - Uproszczona sekcja

Sekcja przeglądu została znacząco uproszczona po usunięciu KPI metrics. Obecnie wyświetla:

**Basic Info Card:**
- Pełne imię, wiek, lokalizacja, zawód
- Grid 2x2 (mobile) → 4 kolumny (desktop)

**Segment Info:**
- Badge z nazwą segmentu (np. "Młodzi Prekariusze")
- Badge z ID segmentu (outline style)
- Opis segmentu z `rag_context_details.orchestration_reasoning.segment_description`

**Usunięte elementy:**
- ❌ 6 KPI cards (segment size, conversion rate, retention, NPS, LTV, CAC)
- ❌ Trend indicators (↑↓→)
- ❌ Benchmark comparisons
- ❌ Top insights z RAG citations (przeniesione do InsightsSection)

#### ProfileSection

Pełny profil demograficzny i psychograficzny persony:

**Zawartość:**
- **Demographics grid**: Wiek, płeć, wykształcenie, dochody, zawód, lokalizacja
- **Big Five traits**: Progress bars dla 5 wymiarów osobowości (0-1 scale)
- **Values badges**: Lista wartości persony (tags)
- **Interests badges**: Lista zainteresowań (tags)
- **Background story**: Pełny opis historii persony (text block)

#### NeedsSection - Główna wartość

Najbardziej wartościowa sekcja dla badaczy rynku i marketerów, pokazująca analitykę Jobs-to-be-Done.

**Zawartość:**
1. **Jobs-to-be-Done cards**
   - Format: "When [situation], I want [motivation], so I can [outcome]"
   - Priority score (1-10), frequency, difficulty
   - Cytaty z grup fokusowych
   - Sortowanie według priority score

2. **Desired Outcomes**
   - Outcome statement
   - Importance (1-10) vs. Satisfaction (1-10)
   - Opportunity score = importance × (importance - satisfaction)
   - Measurability indicator

3. **Pain Points ranking**
   - Severity ranking (1-10)
   - Frequency (daily/weekly/monthly)
   - Percent affected (0-1)
   - Color coding: high (red), medium (yellow), low (green)
   - Potential solutions
   - Cytaty z badań

**Loading state:**
Jeśli `needs_and_pains` jest null lub pusty:
```tsx
<div className="text-center py-12">
  <p className="text-muted-foreground">
    Brak danych potrzeb. Persona nie brała jeszcze udziału w grupach fokusowych.
  </p>
</div>
```

#### InsightsSection

Sekcja kontekstu i historii:

**RAG Context Card:**
- Segment name, segment_id
- Segment description (z orchestration_reasoning)
- Segment social context (demografia, ekonomia, trendy)
- Graph insights (jeśli dostępne z Neo4j)
- Expandable/collapsible dla długiego kontekstu

**Audit Log Timeline:**
- Ostatnie 20 akcji
- Timeline view z icons dla każdej akcji
- Timestamp (relative: "2 godziny temu")
- User info (jeśli user_id dostępne)
- Action-specific details

#### PersonaActionsRail

Prawa szyna akcji (sticky sidebar) z następującymi przyciskami:

**Dostępne akcje:**
1. **Generate Messaging** - Otwiera `MessagingGeneratorDialog` (placeholder - TODO implementacja)
2. **Compare** - Otwiera `ComparePersonasDialog` dla porównania max 3 person
3. **Export** - Eksportuje personę do JSON (pobiera plik)
4. **Delete** - Otwiera `DeletePersonaDialog` z soft delete + 30s undo window

**Responsive behavior:**
- Desktop: Sticky right sidebar (zawsze widoczna)
- Mobile: Floating action button (FAB) z menu

### 4.3. React Query Hooks

#### usePersonaDetails

Hook fetchujący pełne szczegóły persony z backendu:

```tsx
export function usePersonaDetails(personaId: string | null) {
  return useQuery<PersonaDetailsResponse, AxiosError>({
    queryKey: ['personas', personaId, 'details'],
    queryFn: async () => {
      if (!personaId) throw new Error('Persona ID required');
      return await personasApi.getDetails(personaId);
    },
    staleTime: 5 * 60 * 1000,  // 5min (matches backend cache)
    enabled: !!personaId,
    retry: (failureCount, error) => {
      if (error.response?.status === 404) return false;
      return failureCount < 2;
    },
    refetchOnMount: 'always',
  });
}
```

#### useDeletePersona

Mutation hook dla soft delete persony z optimistic updates:

```tsx
export function useDeletePersona() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ personaId, reason, reasonDetail }) => {
      await personasApi.delete(personaId, reason, reasonDetail);
      return { personaId };
    },
    onMutate: async ({ personaId }) => {
      // Optimistic update - usuń z listy natychmiast
      await queryClient.cancelQueries({ queryKey: ['personas'] });
      const previous = queryClient.getQueryData(['personas']);
      queryClient.setQueryData(['personas'], (old: any) => {
        return old?.filter((p: any) => p.id !== personaId);
      });
      return { previous };
    },
    onSuccess: ({ personaId }) => {
      queryClient.invalidateQueries({ queryKey: ['personas'] });
      queryClient.removeQueries({ queryKey: ['personas', personaId, 'details'] });
      toast.success('Persona usunięta. Możesz cofnąć przez 30s.');
    },
    onError: (error, variables, context) => {
      // Rollback optimistic update
      if (context?.previous) {
        queryClient.setQueryData(['personas'], context.previous);
      }
      toast.error(`Usunięcie nieudane: ${error.message}`);
    },
  });
}
```

---

## 5. API Contracts

### 5.1. GET /api/v1/personas/{persona_id}/details

Główny endpoint zwracający pełne szczegóły persony.

**Response 200 OK:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "full_name": "Anna Kowalska",
  "persona_title": "Marketing Manager w Scale-upie",
  "headline": "Ambitna profesjonalistka szukająca efektywności",
  "age": 28,
  "gender": "Kobieta",
  "location": "Warszawa",
  "education_level": "Wyższe magisterskie",
  "income_bracket": "7 500 - 10 000 zł",
  "occupation": "Marketing Manager",

  "big_five": {
    "openness": 0.85,
    "conscientiousness": 0.78,
    "extraversion": 0.65,
    "agreeableness": 0.72,
    "neuroticism": 0.45
  },

  "hofstede": {
    "power_distance": 0.45,
    "individualism": 0.68,
    "masculinity": 0.52,
    "uncertainty_avoidance": 0.65,
    "long_term_orientation": 0.72,
    "indulgence": 0.58
  },

  "values": ["Sukces zawodowy", "Work-life balance", "Rozwój kompetencji"],
  "interests": ["Marketing automation", "Data analytics", "Yoga"],
  "background_story": "Anna ma 28 lat i pracuje jako Marketing Manager...",

  "needs_and_pains": {
    "generated_at": "2025-10-16T14:30:00Z",
    "generated_by": "gemini-2.0-flash-exp",
    "jobs_to_be_done": [
      {
        "job_statement": "When I'm planning quarterly budget, I want to forecast ROI, so I can justify spend to CFO.",
        "priority_score": 9,
        "frequency": "monthly",
        "difficulty": "hard",
        "quotes": ["Spędzam 2 dni co kwartał budując prognozy w Excelu."]
      }
    ],
    "desired_outcomes": [
      {
        "outcome_statement": "Zaoszczędzić 50% czasu na raportowaniu",
        "importance": 9,
        "satisfaction_current_solutions": 4,
        "opportunity_score": 45,
        "is_measurable": true
      }
    ],
    "pain_points": [
      {
        "pain_title": "Manualne wprowadzanie danych",
        "pain_description": "5+ godzin tygodniowo na ręczne kopiowanie",
        "severity": 8,
        "frequency": "daily",
        "percent_affected": 0.75,
        "quotes": ["Marnuję pół dnia co tydzień kopiując dane."],
        "potential_solutions": ["Automatyczna synchronizacja"]
      }
    ]
  },

  "segment_id": "seg_young_professionals",
  "segment_name": "Młodzi Profesjonaliści 25-34",

  "rag_context_details": {
    "orchestration_reasoning": {
      "segment_name": "Młodzi Profesjonaliści",
      "segment_id": "seg_young_professionals",
      "segment_description": "Kobiety z wyższym wykształceniem, wiek 25-34...",
      "segment_social_context": "Segment charakteryzuje się wysoką mobilnością zawodową..."
    },
    "graph_nodes": [...],
    "graph_context": "..."
  },

  "rag_context_used": true,
  "rag_citations": [...],

  "audit_log": [
    {
      "id": "uuid",
      "action": "view",
      "details": {"source": "detail_view"},
      "user_id": "uuid",
      "timestamp": "2025-10-16T14:30:00Z"
    }
  ],

  "created_at": "2025-10-15T10:00:00Z",
  "updated_at": "2025-10-16T12:00:00Z",
  "is_active": true
}
```

**Response 404 Not Found:**
```json
{
  "detail": "Persona {persona_id} not found or inactive"
}
```

**Performance:**
- Cache hit (Redis): < 50ms
- Cache miss (z LLM call): < 3s
- Rate limit: 30 req/min per user

---

### 5.2. POST /api/v1/personas/{id}/actions/compare

Porównanie max 3 person side-by-side.

**Request:**
```json
{
  "compare_with": ["persona_uuid_2", "persona_uuid_3"],
  "sections": ["demographics", "needs"],
  "highlight_differences": true
}
```

**Response 200 OK:**
```json
{
  "personas": [
    {
      "id": "uuid_1",
      "full_name": "Anna Kowalska",
      "age": 28,
      "_differences": ["age", "occupation"]
    },
    {
      "id": "uuid_2",
      "full_name": "Krzysztof Nowak",
      "age": 32,
      "_differences": ["age", "occupation", "gender"]
    }
  ],
  "summary": {
    "similarity_score": 0.82,
    "total_differences": 5,
    "key_differences": [
      {"field": "age", "values": [28, 32]},
      {"field": "occupation", "values": ["Marketing Manager", "Software Engineer"]}
    ]
  }
}
```

---

### 5.3. POST /api/v1/personas/{id}/actions/export

Eksport persony do JSON (PDF/CSV w roadmap).

**Request:**
```json
{
  "format": "json",
  "sections": ["overview", "profile", "needs"],
  "pii_mask": true
}
```

**Response 200 OK (JSON export):**
```json
{
  "export_id": "exp_uuid",
  "format": "json",
  "created_at": "2025-10-16T14:30:00Z",
  "content": {
    "persona": {...},
    "metadata": {
      "exported_by": "user_uuid",
      "exported_at": "2025-10-16T14:30:00Z",
      "sections": ["overview", "profile", "needs"],
      "pii_masked": true
    }
  }
}
```

**Response 202 Accepted (dla przyszłych async exports):**
```json
{
  "export_id": "exp_uuid",
  "status": "processing",
  "estimated_completion_seconds": 45,
  "download_url": null
}
```

---

### 5.4. DELETE /api/v1/personas/{id}

Soft delete persony z 30-sekundowym undo window.

**Request:**
```json
{
  "reason": "outdated",  // outdated/duplicate/test_data/other
  "reason_detail": "Segment demographics changed significantly"
}
```

**Response 200 OK:**
```json
{
  "persona_id": "uuid",
  "status": "deleted",
  "deleted_at": "2025-10-16T14:30:00Z",
  "deleted_by": "user_uuid",
  "undo_available_until": "2025-10-16T14:30:30Z",
  "related_data": {
    "focus_group_responses": 15,
    "persona_events": 42,
    "audit_log_entries": 8
  },
  "message": "Persona usunięta. Możesz cofnąć operację przez 30 sekund."
}
```

---

### 5.5. POST /api/v1/personas/{id}/actions/undo-delete

Przywróć usuniętą personę w ciągu 30 sekund od soft delete.

**Request:** (empty body)

**Response 200 OK:**
```json
{
  "persona_id": "uuid",
  "status": "restored",
  "restored_at": "2025-10-16T14:30:15Z",
  "message": "Persona przywrócona pomyślnie."
}
```

**Response 410 Gone:**
```json
{
  "detail": "Undo window expired (>30s since deletion)"
}
```

---

## 6. Implementation Status

### Phase 1: Database & Models ✅ DONE

**Ukończone:**
- ✅ Migracja `20251015_add_segment_tracking_to_personas` - pola segment_id, segment_name
- ✅ Migracja `20251016_add_persona_details_mvp` - pola kpi_snapshot, customer_journey, needs_and_pains + tabela audit_log
- ✅ Migracja `20251016_add_persona_delete_metadata` - pola deleted_at, deleted_by
- ✅ Migracja `20251016_remove_kpi_journey_fields` - usunięcie kpi_snapshot, customer_journey
- ✅ Model `PersonaAuditLog` z relacjami i indexami
- ✅ Indexy GIN dla JSONB fields, B-tree dla common queries

**Obecny stan schematu:**
- needs_and_pains (JSONB) - jedyne computed field
- segment_id, segment_name - tracking segmentów
- deleted_at, deleted_by - soft delete
- rag_context_details (JSONB) - kontekst RAG
- persona_audit_log (tabela) - audit trail

---

### Phase 2: Backend Services ✅ DONE

**Ukończone:**
- ✅ `PersonaNeedsService` - JTBD extraction z focus groups + RAG context
  - Structured output (Pydantic)
  - Token reduction (6000 → 2000)
  - Temperature reduction (0.35 → 0.25)
  - Focus group limit (20 → 10)
  - Target latency: <2s

- ✅ `PersonaDetailsService` - Main orchestrator
  - Smart cache key (z updated_at)
  - Long TTL (1h z auto-invalidation)
  - Parallel fetch (asyncio.gather)
  - Graceful degradation
  - Background audit logging

- ✅ `PersonaAuditService` - Audit trail
  - Graceful degradation
  - Własna DB session
  - GDPR-ready (wymaga cleanup job)

- ✅ `PersonaComparisonService` - Compare personas
  - Side-by-side comparison
  - Similarity scoring

**Usunięte serwisy:**
- ❌ `PersonaKPIService` - Mock KPI metrics (hardcoded benchmarks)
- ❌ `PersonaJourneyService` - Generic customer journey (LLM-generated)

---

### Phase 3: API Endpoints ✅ DONE

**Ukończone:**
- ✅ `GET /personas/{id}/details` - pełny detail view
  - RBAC enforcement
  - Rate limiting (30/min)
  - OpenAPI docs

- ✅ `DELETE /personas/{id}` - soft delete z audit log
  - Related data count
  - 30s undo window (state w Redis)

- ✅ `POST /personas/{id}/actions/undo-delete` - przywróć usuniętą personę

- ✅ `POST /personas/{id}/actions/compare` - porównanie person
  - Max 3 personas validation

- ✅ `POST /personas/{id}/actions/export` - eksport do JSON
  - PII masking (domyślnie ON)

**Nie zaimplementowane:**
- ⏸️ `POST /personas/{id}/actions/messaging` - AI-powered copywriting (TODO)
- ⏸️ PDF/CSV export (obecnie tylko JSON)

---

### Phase 4: Frontend Components ✅ DONE

**Ukończone:**
- ✅ `PersonaDetailsDrawer` - główny drawer z 4 sekcjami
  - Responsive navigation (sidebar + dropdown)
  - Loading/error states
  - Framer Motion animations

- ✅ `OverviewSection` - uproszczona (basic info + segment)
  - Usunięte KPI cards
  - Segment badges z RAG context

- ✅ `ProfileSection` - demografia + psychografia
  - Big Five progress bars
  - Values/Interests badges
  - Background story

- ✅ `NeedsSection` - JTBD + pain points
  - Jobs cards z priority sorting
  - Desired outcomes
  - Pain ranking

- ✅ `InsightsSection` - RAG context + audit log
  - Expandable RAG context card
  - Timeline audit log (last 20)

- ✅ `PersonaActionsRail` - prawa szyna akcji
  - Compare, Export, Delete (z undo)

- ✅ `ComparePersonasDialog` - porównanie max 3 person
- ✅ `DeletePersonaDialog` - soft delete z reason dropdown

**Nie zaimplementowane:**
- ⏸️ `MessagingGeneratorDialog` - placeholder (wymaga backend endpoint)
- ⏸️ `JourneySection` - usunięta (brak customer_journey w backend)

---

### Phase 5: Hooks & API ✅ DONE

**Ukończone:**
- ✅ `usePersonaDetails` - React Query hook z 5min staleTime
- ✅ `useDeletePersona` - mutation z optimistic updates
- ✅ `useUndoDeletePersona` - mutation dla undo
- ✅ `useComparePersonas` - query dla comparison
- ✅ `personasApi.getDetails()` - typed API client
- ✅ `personasApi.delete()` - soft delete
- ✅ `personasApi.undoDelete()` - undo endpoint
- ✅ `personasApi.compare()` - comparison endpoint
- ✅ `personasApi.export()` - JSON export
- ✅ `PersonaDetailsResponse` TypeScript interface

**Nie zaimplementowane:**
- ⏸️ `useGenerateMessaging` - wymaga backend endpoint

---

### Phase 6-8: Testing, Security, Docs

**Status:**
- ⚠️ Testing: Brak comprehensive test suite dla persona details
  - Unit tests dla services: TODO
  - Integration tests dla API: TODO
  - Frontend component tests: TODO

- ⚠️ Security & GDPR:
  - ✅ Rate limiting na endpoints
  - ✅ RBAC enforcement
  - ⚠️ IP cleanup job (90-day retention): TODO

- ⚠️ Documentation:
  - ✅ Ten dokument (PERSONA_DETAILS.md)
  - ⚠️ Postman collection: TODO
  - ⚠️ OpenAPI spec update: TODO

---

## 7. Known Issues

### 7.1. Otwarte zagadnienia wymagające uwagi

**1. Needs muszą być generowane on-demand**
Pole `needs_and_pains` jest cache'owane w bazie danych, ale wymaga regeneracji gdy persona uczestniczy w nowych grupach fokusowych. System nie ma automatycznego triggera do odświeżania needs po nowych odpowiedziach.

**Potencjalne rozwiązanie:**
- Event listener na dodanie `PersonaResponse` → invalidate `needs_and_pains`
- Lub: Pokazuj "Needs outdated" badge jeśli `needs_and_pains.generated_at` < ostatnia odpowiedź

**2. Segment info może być missing dla starych person**
Persony wygenerowane przed migracją `20251015_add_segment_tracking_to_personas` nie mają wypełnionych pól `segment_id`, `segment_name`. Frontend musi to obsłużyć gracefully (ukryć segment section).

**Potencjalne rozwiązanie:**
- Backfill job ekstrahujący segment info z `rag_context_details` dla starych person
- Lub: Re-run orchestracji dla starych person z nowym kodem

**3. Brak GDPR cleanup job dla IP addresses**
`PersonaAuditLog` przechowuje IP adresy i user agents, które muszą być usuwane po 90 dniach zgodnie z GDPR. Obecnie brak automatycznego cleanup.

**Wymagana implementacja:**
```python
# app/tasks/gdpr_cleanup.py
@celery.task
async def cleanup_old_audit_log_pii():
    """Remove IP addresses and user agents older than 90 days"""
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    await db.execute(
        update(PersonaAuditLog)
        .where(PersonaAuditLog.timestamp < cutoff_date)
        .values(ip_address=None, user_agent=None)
    )
```

**4. Export PDF/CSV nie zaimplementowany**
Endpoint `/actions/export` zwraca tylko JSON. PDF i CSV są w roadmap ale nie zaimplementowane.

**Wymagana implementacja:**
- PDF: Użyć `ReportLab` lub `WeasyPrint` dla formatowania
- CSV: Flattened struktura z selected sections
- PII masking: Automatyczne maskowanie pól sensitive (imię → "A.K.", email → "a***@example.com")

**5. Messaging generator nie zaimplementowany**
Dialog `MessagingGeneratorDialog` jest placeholder. Backend endpoint `/actions/messaging` nie istnieje.

**Roadmap item:**
- Implementacja `PersonaMessagingService` dla AI copywriting
- Gemini 2.0 Flash z promptem tone + type + persona context
- 3 warianty messaging (headline, body, CTA)
- Rate limiting (10 req/hour - LLM expensive)

**6. Brak distributed locking dla needs generation**
Jeśli dwóch użytkowników jednocześnie otworzy detail view tej samej persony (cache miss), oba requesty wywołają LLM dla generowania needs. To powoduje:
- Podwójne koszty LLM calls
- Potencjalny race condition przy zapisie do DB

**Potencjalne rozwiązanie:**
```python
# app/services/persona_needs_service.py
async def generate_needs_analysis(self, persona: Persona) -> Dict[str, Any]:
    lock_key = f"needs_generation:{persona.id}"
    async with redis_lock(lock_key, timeout=30):  # Distributed lock
        # Check cache again (może inny request już wygenerował)
        if persona.needs_and_pains:
            return persona.needs_and_pains
        # Generate...
```

---

### 7.2. Rozwiązane zagadnienia

- ✅ Audit logging używa własnej sesji DB (`AsyncSessionLocal()`) - nie blokuje głównej transakcji
- ✅ Smart cache key z `updated_at` - automatyczna invalidacja przy edycji persony
- ✅ Redis cache (1h TTL) dla szczegółów persony - znacząco skraca latency
- ✅ RBAC: `get_persona_for_user` chroni endpointy przed dostępem do cudzych danych
- ✅ Graceful degradation - jeśli LLM failuje, zwraca cached needs zamiast błędu 500

---

## 8. Roadmap & Next Steps

### Krótkoterminowe (Q4 2025)

**1. Implementacja GDPR cleanup job (Priorytet: HIGH)**
- Celery scheduled task dla usuwania IP addresses >90 dni
- Monitoring compliance via admin dashboard
- Szacowany wysiłek: 1 dzień

**2. Distributed lock dla needs generation (Priorytet: MEDIUM)**
- Redis lock dla równoczesnych requestów
- Retry logic dla timeout scenarios
- Szacowany wysiłek: 4 godziny

**3. Backfill segment info dla starych person (Priorytet: LOW)**
- Skrypt ekstrahujący segment z `rag_context_details`
- Lub: Re-run orchestracji dla person bez segment_id
- Szacowany wysiłek: 1 dzień

### Średnioterminowe (Q1 2026)

**4. PDF/CSV export (Priorytet: MEDIUM)**
- PDF z watermarkiem i formatowaniem
- CSV z flattened structure
- PII masking enforcement
- Szacowany wysiłek: 2-3 dni

**5. Messaging Generator (Priorytet: LOW)**
- `PersonaMessagingService` implementation
- Gemini prompt engineering (tone + type)
- Rate limiting (10 req/hour)
- Szacowany wysiłek: 2 dni

**6. Comprehensive test suite (Priorytet: HIGH)**
- Unit tests dla PersonaNeedsService, PersonaDetailsService
- Integration tests dla API endpoints
- Frontend component tests (React Testing Library)
- Target coverage: 80%+ backend, 70%+ frontend
- Szacowany wysiłek: 2-3 dni

### Długoterminowe (Q2 2026+)

**7. Real-time needs updates**
- Event listener na `PersonaResponse` → trigger needs regeneration
- WebSocket push notifications dla outdated needs
- Background job queue dla async processing

**8. Advanced analytics**
- Aggregate JTBD insights across all personas
- Pain point clustering (identify common themes)
- Opportunity score heatmap per segment

**9. Collaborative features**
- Comments & mentions (już częściowo zaimplementowane w modelu)
- Persona versioning (snapshots w czasie)
- Team permissions (read/write/admin per persona)

---

**Wersja:** 3.0
**Status:** MVP zaimplementowane, uproszczona architektura (bez KPI/Journey)
**Focus:** Needs & Pain Points z RAG integration
**Data ostatniej aktualizacji:** 2025-10-16
