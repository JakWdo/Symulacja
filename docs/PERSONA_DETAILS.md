# Persona Details - Floating Modal Architecture

**Data ostatniej aktualizacji:** 2025-10-18

Dokumentacja redesignu Persona Details View z drawer na floating modal z horizontal tabs.

---

## Przegląd zmian (2025-10-18)

### Główne zmiany architektury

1. **Floating Modal zamiast Drawer**
   - Max-width: 70vw (vs. 90vw drawer)
   - Centrowany, backdrop blur
   - Height: 85vh dla lepszego UX
   - Mobile: full-screen

2. **Horizontal Tabs Navigation**
   - Desktop: horizontal tabs pod headerem
   - Mobile: Select dropdown
   - 5 sekcji: Overview, Profile, Segment, Potrzeby, Metodologia

3. **Nowe sekcje**
   - **Segment & Reasoning** - segment rules, similar personas, orchestration brief
   - **Metodologia** - data sources, generation metadata, limitations disclaimer

4. **Usunięte elementy**
   - Psychographics (Big Five, Hofstede) z Profile section
   - Akcje (Generate Messaging, Compare, Export) - read-only modal
   - Left/right navigation sidebar

5. **Nowe funkcjonalności**
   - Data freshness badge w header (<24h, 1-7d, >7d)
   - Top 3-5 insights z RAG w Overview
   - Desired Outcomes z importance/satisfaction/opportunity scores (0-10)
   - Similar personas list (ten sam segment_id)
   - Segment rules display (age_range, gender, locations, values)

---

## Backend Architecture

### 1. Schemas (`app/schemas/persona_details.py`)

#### Nowe/Zaktualizowane Schematy

**DesiredOutcome** (zaktualizowany):
```python
class DesiredOutcome(BaseModel):
    outcome_statement: str
    importance: Optional[int] = Field(ge=0, le=10)  # NEW: 0-10 scale
    satisfaction: Optional[int] = Field(ge=0, le=10)  # NEW: renamed from satisfaction_current_solutions
    opportunity_score: Optional[int] = Field(ge=0, le=10)  # NEW: importance - satisfaction
    quotes: List[str] = Field(default_factory=list)  # NEW: supporting quotes
    is_measurable: Optional[bool] = None
```

**SegmentRules** (nowy):
```python
class SegmentRules(BaseModel):
    """Reguły definiujące segment persony."""
    age_range: Optional[str]  # "30-40"
    gender_options: Optional[List[str]]  # ["Kobieta"]
    location_filters: Optional[List[str]]  # ["Warszawa", "Kraków"]
    required_values: Optional[List[str]]  # ["Niezależność", "Innowacja"]
```

**SimilarPersona** (nowy):
```python
class SimilarPersona(BaseModel):
    """Krótki opis podobnej persony (z tego samego segmentu)."""
    id: str  # UUID persony
    name: str  # "Product Manager, 32 lata"
    distinguishing_trait: str  # "Młodsza o 5 lat, z Krakowa"
```

**PersonaDetailsResponse** (rozszerzony):
```python
class PersonaDetailsResponse(BaseModel):
    # ... existing fields ...

    # NEW FIELDS (2025-10-18):
    segment_rules: Optional[SegmentRules] = None
    similar_personas: List[SimilarPersona] = Field(default_factory=list)
    data_freshness: datetime  # Timestamp dla freshness badge (bazuje na updated_at)
```

### 2. PersonaDetailsService (`app/services/personas/persona_details_service.py`)

#### Nowe metody

**_fetch_segment_rules(persona: Persona) -> Optional[Dict]**
- Parsuje segment rules z `orchestration_reasoning`
- Fallback: infer z danych persony (age → age_range, gender → gender_options)
- Zwraca: `{age_range, gender_options, location_filters, required_values}`

**_fetch_similar_personas(persona: Persona, limit=5) -> List[Dict]**
- Query: ten sam `segment_id`, exclude self
- Performance: index na (project_id, segment_id, is_active)
- Zwraca: `[{id, name, distinguishing_trait}]`

**_generate_persona_name(persona: Persona) -> str**
- Format: "Occupation, age lat" lub "Kobieta, 32 lata"
- Fallback: "Persona #<uuid[:8]>"

**_get_distinguishing_trait(base_persona, other_persona) -> str**
- Porównuje: age diff, location, occupation, income
- Zwraca: "Młodsza o 5 lat, z Krakowa" (max 2 traits)
- Fallback: "podobny profil"

**_extract_income_value(income_bracket: str) -> Optional[int]**
- Helper: parsuje "7500-10000 PLN" → średnia wartość
- Używane do porównania dochodów

#### Aktualizacja get_persona_details()

```python
# Parallel fetch (asyncio.gather):
needs_and_pains, audit_log, narratives_data, similar_personas_data = await asyncio.gather(
    self._fetch_needs_and_pains(persona, force_refresh=force_refresh),
    self._fetch_audit_log(persona_id),
    self._fetch_narratives(persona_id, force_refresh=force_refresh),
    self._fetch_similar_personas(persona, limit=5),  # NEW
    return_exceptions=True,
)

# Sync fetch (quick, no DB):
segment_rules_data = self._fetch_segment_rules(persona)  # NEW

# Response:
response = PersonaDetailsResponse(
    # ... existing fields ...
    segment_rules=segment_rules,  # NEW
    similar_personas=similar_personas,  # NEW
    data_freshness=persona.updated_at,  # NEW
)
```

### 3. PersonaNeedsService (`app/services/personas/persona_needs_service.py`)

#### Aktualizacja promptu

Nowy prompt dla Desired Outcomes:
```
2. Desired outcomes (based on persona's actual life situation - NOT generic):
   - outcome_statement: Clear statement of desired outcome
   - importance: How important is this outcome (0-10 scale, 10 = critical)
   - satisfaction: Current satisfaction level with available solutions (0-10 scale)
   - opportunity_score: Calculate as (importance - satisfaction), or estimate separately (0-10)
   - quotes: 1-2 supporting quotes from focus group responses
```

---

## Frontend Architecture

### 1. PersonaDetailsDrawer (`frontend/src/components/personas/PersonaDetailsDrawer.tsx`)

#### Redesign (2025-10-18)

**Struktura:**
```tsx
<Dialog open={isOpen} onOpenChange={onClose}>
  <DialogContent className="max-w-[70vw] sm:max-w-full sm:h-full h-[85vh]">
    {/* Sticky Header */}
    <DialogHeader className="sticky top-0 bg-background z-10">
      <DialogTitle>
        {occupation}, {age} lat - {location}
      </DialogTitle>
      <DataFreshnessBadge timestamp={data_freshness || updated_at} />
    </DialogHeader>

    {/* Horizontal Tabs */}
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      {/* Mobile: Select dropdown */}
      <div className="sm:hidden">
        <Select value={activeTab} onValueChange={setActiveTab}>
          <SelectItem value="overview">Overview</SelectItem>
          {/* ... */}
        </Select>
      </div>

      {/* Desktop: Horizontal tabs */}
      <TabsList className="hidden sm:flex border-b">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="profile">Profile</TabsTrigger>
        <TabsTrigger value="segment">Segment</TabsTrigger>
        <TabsTrigger value="needs">Potrzeby</TabsTrigger>
        <TabsTrigger value="methodology">Metodologia</TabsTrigger>
      </TabsList>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        <TabsContent value="overview"><OverviewSection /></TabsContent>
        <TabsContent value="profile"><ProfileSection /></TabsContent>
        <TabsContent value="segment"><SegmentSection /></TabsContent>
        <TabsContent value="needs"><NeedsSection /></TabsContent>
        <TabsContent value="methodology"><MethodologySection /></TabsContent>
      </div>
    </Tabs>
  </DialogContent>
</Dialog>
```

**Kluczowe zmiany:**
- Left sidebar navigation → Horizontal tabs (Radix Tabs)
- Mobile select navigation → Select dropdown
- Max-width: 90vw → 70vw
- Usunięto PersonaActionsPanel (read-only modal)
- Dodano DataFreshnessBadge w header

### 2. DataFreshnessBadge (`frontend/src/components/personas/DataFreshnessBadge.tsx`)

**Funkcjonalność:**
- Oblicza dni od `updated_at`
- Kolory:
  - <24h: green (default variant)
  - 1-7 dni: gray (secondary variant)
  - >7 dni: red (destructive variant)
- Format: "Dzisiaj", "Wczoraj", "3 dni temu", "2 tyg. temu"

**Usage:**
```tsx
<DataFreshnessBadge timestamp={persona.data_freshness || persona.updated_at} />
```

### 3. OverviewSection (zaktualizowany)

**Nowe elementy:**
- **Top RAG Insights** - top 3-5 insights z `orchestration_reasoning.graph_insights`
  - Wyświetla: summary, why_matters, confidence badge, type, source, time_period
  - Limit: 5 insights
  - Conditional: tylko jeśli `graph_insights` dostępne

**Istniejące elementy (bez zmian):**
- Basic Info Card (wiek, płeć, lokalizacja, zawód, segment)
- Segment Context Card (segment name, description, social context, characteristics)

### 4. ProfileSection (bez zmian - już bez psychografii)

**Wyświetla:**
- **Demografia**: wiek, płeć, lokalizacja, wykształcenie, dochód, zawód
- **Values**: badges z wartościami
- **Interests**: badges z zainteresowaniami
- **Background Story**: narrative tekst

**Usunięte (przed redesignem):**
- Big Five scores
- Hofstede dimensions
- Psychographic analysis

### 5. SegmentSection (nowy komponent)

**Struktura:**
```tsx
<div className="space-y-6">
  {/* Segment Overview Card */}
  <Card>
    <CardHeader>
      <CardTitle>{segment_name}</CardTitle>
      <CardDescription>{segment_description}</CardDescription>
    </CardHeader>
    <CardContent>
      <h4>Kontekst Społeczny</h4>
      <p>{segment_social_context}</p>
    </CardContent>
  </Card>

  {/* Segment Rules Card */}
  <Card>
    <CardTitle>Reguły Segmentu</CardTitle>
    <dl>
      <dt>Wiek:</dt> <dd>{age_range}</dd>
      <dt>Płeć:</dt> <dd>{gender_options.join(", ")}</dd>
      <dt>Lokalizacje:</dt> <dd>{location_filters.map(Badge)}</dd>
      <dt>Wartości:</dt> <dd>{required_values.map(Badge)}</dd>
    </dl>
  </Card>

  {/* Why This Persona Card */}
  <Card>
    <CardTitle>Dlaczego ta persona?</CardTitle>
    <p>{orchestration_reasoning.brief}</p>
  </Card>

  {/* Similar Personas Card */}
  <Card>
    <CardTitle>Podobne Persony</CardTitle>
    <ul>
      {similar_personas.map(p => (
        <li>
          <Link to={`/personas/${p.id}`}>{p.name}</Link>
          <span>{p.distinguishing_trait}</span>
        </li>
      ))}
    </ul>
  </Card>
</div>
```

**Empty State:**
- Wyświetla placeholder jeśli brak segment rules, similar personas, i brief

### 6. NeedsSection (zaktualizowany)

**Desired Outcomes - nowe wyświetlanie:**
```tsx
<OutcomeCard outcome={outcome}>
  <p>{outcome_statement}</p>

  {/* NEW: Importance/Satisfaction/Opportunity scores */}
  <div className="flex flex-wrap gap-2">
    <Badge variant="outline">Ważność: {importance}/10</Badge>
    <Badge variant="secondary">Satysfakcja: {satisfaction}/10</Badge>
  </div>

  {/* Progress bar dla opportunity score */}
  <Progress value={opportunity_score * 10} />
  <span>{opportunityLevel}</span>  {/* "Bardzo wysoka", "Wysoka", etc. */}

  {/* Quotes (jeśli dostępne) */}
  {outcome.quotes?.map(q => <Quote>{q}</Quote>)}
</OutcomeCard>
```

**Zmiany:**
- Zmiana pola: `satisfaction_current_solutions` → `satisfaction`
- Dodano wyświetlanie: `importance`, `satisfaction`, `opportunity_score`
- Opportunity level: Bardzo wysoka (>75), Wysoka (>50), Średnia (>25), Niska (<25)
- Kolory: green (>75), blue (>50), yellow (>25), red (<25)

**Bez zmian:**
- JTBD display (job_statement, priority_score, quotes)
- Pain Points display (severity, frequency, percent_affected, quotes)

### 7. MethodologySection (nowy komponent)

**Struktura:**
```tsx
<div className="space-y-6">
  {/* Data Sources Card */}
  <Card>
    <CardTitle>Źródła Danych</CardTitle>
    <dl>
      <dt>RAG Documents:</dt> <dd>{rag_citations.length}</dd>
      <dt>Graph RAG Nodes:</dt> <dd>{graph_nodes_count}</dd>
      <dt>Typ Wyszukiwania:</dt> <dd>{search_type}</dd>
    </dl>
    {!rag_context_used && <Alert>Brak RAG context</Alert>}
  </Card>

  {/* Generation Metadata Card */}
  <Card>
    <CardTitle>Metadane Generacji</CardTitle>
    <dl>
      <dt>Data utworzenia:</dt> <dd>{formatDate(created_at)}</dd>
      <dt>Ostatnia aktualizacja:</dt> <dd>{formatDate(updated_at)}</dd>
      <dt>Model LLM:</dt> <dd>Google Gemini 2.5 (Flash + Pro)</dd>
      <dt>Status Narracji:</dt> <dd>{narratives_status}</dd>
    </dl>
  </Card>

  {/* Limitations Disclaimer Card */}
  <Card className="border-amber-200 bg-amber-50">
    <CardTitle>Ograniczenia Interpretacji</CardTitle>
    <p>
      Persona została wygenerowana na podstawie danych agregowanych...
      Model LLM może wprowadzać własne założenia i uprzedzenia.
      Rekomendujemy krytyczną ocenę i weryfikację z rzeczywistymi użytkownikami.
    </p>
  </Card>
</div>
```

**Funkcjonalność:**
- Data sources: count RAG documents, Graph nodes, search type
- Generation metadata: timestamps, model, narratives status
- Limitations: static disclaimer text (amber warning card)

---

## TypeScript Types

### Aktualizowane typy (`frontend/src/types/index.ts`)

```typescript
export interface DesiredOutcome {
  outcome_statement: string;
  importance?: number;  // 0-10 scale (NEW)
  satisfaction?: number;  // 0-10 scale (renamed from satisfaction_current_solutions)
  opportunity_score?: number;  // 0-10 scale
  quotes?: string[];  // Supporting quotes (NEW)
  is_measurable?: boolean;
}

export interface SegmentRules {
  age_range?: string;  // "30-40"
  gender_options?: string[];  // ["Kobieta"]
  location_filters?: string[];  // ["Warszawa", "Kraków"]
  required_values?: string[];  // ["Niezależność", "Innowacja"]
}

export interface SimilarPersona {
  id: string;  // UUID
  name: string;  // "Product Manager, 32 lata"
  distinguishing_trait: string;  // "Młodsza o 5 lat, z Krakowa"
}

export interface PersonaDetailsResponse extends Persona {
  // ... existing fields ...

  // NEW FIELDS:
  segment_rules?: SegmentRules | null;
  similar_personas?: SimilarPersona[];
  data_freshness?: string;  // ISO datetime
  updated_at?: string;
}
```

---

## Performance & Optimizations

### Backend Performance

**Parallel Fetch (asyncio.gather):**
- needs_and_pains: <2s (LLM structured output)
- audit_log: <50ms (indexed query, limit 20)
- narratives: <20s (5 parallel LLM calls, cached)
- similar_personas: <100ms (indexed query, limit 5)

**Sync Operations:**
- segment_rules: <5ms (parse + infer, no DB)

**Cache Strategy:**
- Redis TTL: 1h (3600s)
- Cache key: `persona_details:{persona_id}:{updated_at_timestamp}`
- Auto-invalidation: gdy `updated_at` się zmieni
- Cache hit: <50ms (Redis)
- Cache miss: <3s total (parallel fetch)

### Frontend Performance

**Loading States:**
- Skeleton loaders dla każdej sekcji
- Separate skeletons: header, tabs, content
- Graceful degradation dla missing data

**Data Fetching:**
- React Query cache: 5min
- Retry: 2 attempts
- Auto-refetch: on window focus (disabled dla details view)

**Animation:**
- Framer Motion: duration 0.2s (vs. 0.5s poprzednio)
- Stagger children: 0.1s
- AnimatePresence dla modal open/close

---

## Testing Scenarios

### Happy Path
1. User clicks "View Details" na persona
2. Modal opens z loading skeletons
3. Data fetches (cache hit <50ms lub cache miss <3s)
4. All 5 tabs render z complete data:
   - Overview: basic info + top insights + segment context
   - Profile: demographics + values + interests + background
   - Segment: rules + similar personas + reasoning
   - Needs: JTBD + outcomes (z scores) + pains
   - Methodology: data sources + metadata + disclaimer
5. User navigates between tabs (smooth transitions)
6. Data freshness badge shows appropriate color (<24h, 1-7d, >7d)

### Partial Data
1. **Brak RAG context:**
   - Overview: basic info only, hide top insights
   - Segment: show placeholder "Brak danych segmentowych"
   - Methodology: alert "Persona wygenerowana bez RAG"

2. **Brak needs_and_pains:**
   - Needs tab: placeholder "Brak danych JTBD"
   - (możliwość triggeru regeneracji - future feature)

3. **Brak similar personas:**
   - Segment: empty state dla similar personas list
   - (jeśli brak segment_id)

4. **Brak narratives:**
   - Narratives status: "degraded" | "offline" | "pending"
   - Methodology: wyświetla status z ikoną

### Error States
1. **LLM timeout:**
   - Graceful degradation: partial response
   - Error message: "Część danych może być niekompletna"
   - Retry: dostępne przez force_refresh

2. **Network error:**
   - React Query error boundary
   - Error message z retry button
   - Close modal option

3. **Stale data (>7 dni):**
   - Data freshness badge: red/destructive
   - Warning w Methodology: "Dane mogą być nieaktualne"

### Edge Cases
1. **Mobile view:**
   - Full-screen modal
   - Select dropdown navigation (zamiast tabs)
   - Scrollable content
   - Responsive cards (grid-cols-1)

2. **Empty persona (minimal data):**
   - Only demographics
   - Placeholders dla missing sections
   - No crash, graceful degradation

3. **Very long content:**
   - Scrollable modal body (max-h-[85vh])
   - Sticky header (z-index 10)
   - Smooth scroll behavior

---

## Migration Checklist

### Backend
- [x] Update schemas (DesiredOutcome, SegmentRules, SimilarPersona)
- [x] Implement PersonaDetailsService methods
- [x] Update PersonaNeedsService prompt
- [ ] Write unit tests (PersonaDetailsService)
- [ ] Write integration tests (GET /personas/{id}/details)

### Frontend
- [x] Update TypeScript types
- [x] Create PersonaDetailsModal (Tabs)
- [x] Create DataFreshnessBadge
- [x] Refactor OverviewSection (top insights)
- [x] Refactor ProfileSection (remove psychographics)
- [x] Create SegmentSection
- [x] Update NeedsSection (scores display)
- [x] Create MethodologySection
- [x] Mobile responsive design

### Documentation
- [x] Update PERSONA_DETAILS.md

### QA
- [ ] Test happy path (all tabs, complete data)
- [ ] Test partial data scenarios
- [ ] Test error states
- [ ] Test mobile responsive
- [ ] Test data freshness badge variants

---

## Future Enhancements

### Backend
1. **KPI Snapshot** (currently omitted):
   - Add `kpi_snapshot` field with real metrics
   - Calculate segment_size, conversion_rate, retention, NPS, LTV, CAC
   - Source: PostgreSQL aggregates lub Graph RAG queries

2. **Confidence Score**:
   - Add `confidence_score` to orchestration_reasoning
   - Display w Methodology section

3. **Segment rules auto-extraction**:
   - LLM-based extraction z orchestration text
   - Structured output dla segment_rules

### Frontend
1. **Regenerate actions**:
   - "Regenerate needs" button gdy brak needs_and_pains
   - "Refresh narratives" button gdy status = "degraded"

2. **Share/Export**:
   - Share link (read-only view)
   - Export to PDF (formatted report)
   - Copy persona summary to clipboard

3. **Interactive insights**:
   - Click insight → show full RAG citation
   - Click similar persona → open their details (nested modal)

4. **Accessibility**:
   - Keyboard navigation między tabs (Arrow keys)
   - Focus trap improvements
   - Screen reader announcements

5. **Performance**:
   - Preload narratives w background (on hover)
   - Virtual scrolling dla long lists (similar personas, insights)

---

## References

- **Backend service:** `app/services/personas/persona_details_service.py`
- **Frontend modal:** `frontend/src/components/personas/PersonaDetailsDrawer.tsx`
- **Schemas:** `app/schemas/persona_details.py`
- **Types:** `frontend/src/types/index.ts`
- **RAG docs:** `docs/RAG.md`
- **AI/ML docs:** `docs/AI_ML.md`
