# Persona Details - Szczegółowy Widok Persony

**Wersja:** 4.0 (Simplified Documentation)
**Data:** 2025-10-22
**Status:** ✅ Implemented (MVP)

---

## Spis Treści

1. [Cel Biznesowy](#1-cel-biznesowy)
2. [Database Schema](#2-database-schema)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [API Contracts](#5-api-contracts)
6. [Known Issues](#6-known-issues)

---

## 1. Cel Biznesowy

Szczegółowy widok persony dostarcza marketerom **skoncentrowane informacje o potrzebach i kontekście** wygenerowanych person.

### Kluczowe wartości

**1. Profil demograficzny i psychograficzny**
Pełny opis persony: wiek, płeć, zawód, wykształcenie, dochody + cechy osobowościowe (Big Five, wartości, zainteresowania).

**2. Potrzeby i bóle (Jobs-to-be-Done)**
Analiza JTBD identyfikuje kluczowe zadania, pożądane rezultaty oraz pain points. Ekstrahowane z wypowiedzi person w wirtualnych grupach fokusowych + kontekst RAG.

**3. Kontekst RAG i historia aktywności**
Szczegóły kontekstu RAG (segment, opis, kontekst społeczny) oraz dziennik audytowy (wyświetlenia, eksporty, usunięcia).

### Decyzje architektoniczne (2025-10)

**Usunięte:**
- KPI Metrics - szacunkowe metryki (conversion, retention, LTV, CAC) bez rzeczywistych danych
- Customer Journey - generyczne 4-etapowe ścieżki bez wartości dodanej

**Zachowane:**
- PersonaNeedsService - JTBD analysis z wypowiedzi person + RAG context

### Kluczowe metryki

- **Time-to-Insight**: < 50ms (cached), < 3s (fresh data)
- **Cache Strategy**: Redis 1h TTL + smart invalidation (cache key zawiera `updated_at`)

---

## 2. Database Schema

### Tabela `personas` - Rozszerzone pola

System dodaje do tabeli `personas` jedno kluczowe pole JSONB:

```python
needs_and_pains = Column(JSONB, nullable=True)
```

**Struktura:**
```json
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
      "outcome_statement": "Zaoszczędzić 50% czasu...",
      "importance": 9,
      "satisfaction_current_solutions": 4,
      "opportunity_score": 45
    }
  ],
  "pain_points": [
    {
      "pain_title": "Manualne wprowadzanie danych",
      "pain_description": "5+ godzin tygodniowo...",
      "severity": 8,
      "frequency": "daily",
      "quotes": ["Marnuję pół dnia..."]
    }
  ]
}
```

### Tabela `persona_audit_log`

```python
class PersonaAuditLog(Base):
    id: UUID
    persona_id: UUID  # FK → personas
    action: str       # 'view', 'export', 'delete', etc.
    metadata: JSONB   # Dodatkowe dane (format, reason)
    created_at: DateTime
```

---

## 3. Backend Architecture

### Service Layer

**PersonaDetailsService** - główny orchestrator:
```python
async def get_persona_details(persona_id: UUID) -> PersonaDetailsResponse:
    # 1. Fetch persona + relationships (project, focus groups)
    # 2. Generate/fetch JTBD analysis (PersonaNeedsService)
    # 3. Fetch audit log (PersonaAuditService)
    # 4. Return structured response
```

**PersonaNeedsService** - JTBD analysis:
```python
async def analyze_persona_needs(persona: Persona) -> NeedsAnalysisResult:
    # 1. Check cache (Redis, 1h TTL)
    # 2. Fetch focus group transcripts
    # 3. LLM analysis (Gemini 2.0 Flash) + structured output
    # 4. Cache result
```

**PersonaAuditService** - audit logging:
```python
async def log_action(persona_id, action, metadata=None):
    # Zapisz w persona_audit_log
```

### Caching Strategy

- **Redis TTL:** 1 hour
- **Cache Key:** `persona_details:{persona_id}:{updated_at_timestamp}`
- **Invalidation:** Automatic (nowy klucz przy update persony)

---

## 4. Frontend Architecture

### Główne komponenty

**PersonaDetailsDrawer** (Sheet 70% width):
- Lazy loading (fetch dopiero po otwarciu)
- 4 sekcje: Overview, Profile, Insights, Actions
- React Query (`usePersonaDetails` hook)

**Sekcje:**
1. **OverviewSection** - statystyki (focus groups count, needs count, audit log count)
2. **ProfileSection** - demografia + Big Five progress bars
3. **InsightsSection** - JTBD cards + RAG context + audit timeline
4. **DeletePersonaDialog** - potwierdzenie usunięcia z powodem

### State Management

```typescript
// React Query
const { data, isLoading } = usePersonaDetails(personaId)

// Mutations
const deleteMutation = useDeletePersona({
  onSuccess: () => queryClient.invalidateQueries(['personas'])
})
```

---

## 5. API Contracts

### GET /api/personas/{id}/details

**Response:**
```json
{
  "persona": {
    "id": "uuid",
    "name": "Jan Kowalski",
    "age": 34,
    "headline": "34-letni menedżer IT...",
    "demographics": {...},
    "psychographics": {...},
    "segment_name": "Tech-Savvy Professionals",
    "segment_brief": "Segmentowy brief..."
  },
  "needs_analysis": {
    "jobs_to_be_done": [...],
    "desired_outcomes": [...],
    "pain_points": [...]
  },
  "rag_context": {
    "segment_name": "Tech-Savvy Professionals",
    "segment_description": "...",
    "context_summary": "RAG context..."
  },
  "audit_log": [
    {
      "action": "view",
      "created_at": "2025-10-16T14:30:00Z",
      "metadata": null
    }
  ],
  "stats": {
    "focus_groups_count": 3,
    "needs_count": 5,
    "audit_entries_count": 12
  }
}
```

### DELETE /api/personas/{id}

**Request Body:**
```json
{
  "reason": "Duplicate entry"
}
```

**Response:** 204 No Content

---

## 6. Known Issues

### Backend

1. **Redis dependency** - Brak graceful degradation gdy Redis niedostępny
   - **Workaround:** Fallback do direct LLM call (bez cache)

2. **JTBD analysis quality** - Zależy od jakości transkryptów grup fokusowych
   - **Improvement:** Dodać confidence score do każdego JTBD

### Frontend

1. **Sheet overflow** - Długie listy JTBD powodują scroll issues
   - **Fix:** Implement virtualization dla długich list

2. **Loading states** - Brak skeleton loader dla JTBD cards
   - **Fix:** Dodać Skeleton components (shadcn/ui)

---

## Next Steps

Zobacz **PLAN.md** dla roadmap i planowanych ulepszeń.

Kluczowe obszary rozwoju:
- Confidence scores dla JTBD analysis
- Bulk export person (CSV/JSON)
- Advanced filtering w audit log
- Persona comparison view
