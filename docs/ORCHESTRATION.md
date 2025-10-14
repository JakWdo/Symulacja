# System Generowania Person z Graph RAG Orchestration

## Przegląd

System wykorzystuje **dwupoziomową architekturę AI** do generowania fascynujących, realistycznych person syntetycznych:

1. **Orchestration Agent (Gemini 2.5 Pro)** - Complex reasoning, długie analizy (2000-3000 znaków)
2. **Individual Generators (Gemini 2.5 Flash)** - Szybkie generowanie konkretnych person

## Architektura

```
User: "Wygeneruj 20 person"
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ KROK 1: ORCHESTRATION (Gemini 2.5 Pro)                         │
├─────────────────────────────────────────────────────────────────┤
│ • Pobiera Graph RAG context (Hybrid Search)                      │
│   - Vector search (semantic similarity)                          │
│   - Keyword search (lexical matching)                            │
│   - RRF Fusion (Reciprocal Rank Fusion)                          │
│                                                                   │
│ • Analizuje rozkłady demograficzne + trendy społeczne           │
│ • Tworzy szczegółowe briefe (2000-3000 znaków) dla grup          │
│                                                                   │
│ Output: PersonaAllocationPlan                                    │
│   - Overall context (500-800 znaków)                             │
│   - Groups[] z briefami i graph insights                         │
│   - Allocation reasoning dla każdej grupy                        │
│                                                                   │
│ Performance: ~30-60s                                             │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ KROK 2: GENEROWANIE PERSON (Gemini 2.5 Flash, równolegle)       │
├─────────────────────────────────────────────────────────────────┤
│ Dla każdej persony:                                              │
│   • Dostaje swój DŁUGI brief jako kontekst                       │
│   • Brief używany jako TŁO (nie cytowany bezpośrednio)          │
│   • Generuje fascynującą postać odzwierciedlającą realia        │
│                                                                   │
│ Output dla każdej persony:                                       │
│   - Natural description (karty) - BEZ statystyk                  │
│   - Orchestration reasoning (View Details) - edukacyjne          │
│                                                                   │
│ Performance: ~1.5-3s per persona (parallel)                      │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ KROK 3: ZAPISYWANIE REASONING                                    │
├─────────────────────────────────────────────────────────────────┤
│ rag_context_details.orchestration_reasoning:                     │
│   - brief (2000-3000 znaków)                                     │
│   - graph_insights (lista z "why_matters")                       │
│   - allocation_reasoning                                         │
│   - demographics                                                 │
│   - overall_context                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Output Style - Edukacyjny

**Zasady:**
- ✅ Konwersacyjny ton (jak kolega z zespołu)
- ✅ Wyjaśnia "dlaczego", nie tylko "co"
- ✅ Production-ready content (może iść bezpośrednio do użytkownika)
- ✅ Polski w komunikacji, angielski w kodzie

**Przykład ZŁY (raportowy):**
```
Anna Kowalska, 29 lat. Należy do 17.3% populacji miejskiej.
Stopa zatrudnienia: 78.4%. Mobilność zawodowa: 63%.
```

**Przykład DOBRY (edukacyjny):**
```
Anna ma 29 lat i pracuje jako project manager w warszawskim startupie
fintech. Jak wielu jej rówieśników z wyższym wykształceniem, zmaga się
z wysokimi cenami mieszkań - wynajmuje z koleżanką na Mokotowie,
oszczędzając 2000 zł miesięcznie na własne mieszkanie.

Weekendy spędza na jodze (jej ulubione studio to Fabryka Trzciny)
i planowaniu kolejnej podróży - ostatnio wróciła z Lizbony, teraz
myśli o Gruzji. Słucha podcastów o finansach osobistych podczas
commute (Jak Oszczędzać Pieniądze, Świat na Kredycie).
```

## Dwupoziomowy Opis Person

### Poziom 1: Karty (Natural Description)
- **Gdzie:** Lista person, preview cards
- **Styl:** Narracyjny, BEZ statystyk, FASCYNUJĄCA POSTAĆ
- **Pola:** full_name, persona_title, headline, background_story
- **Przykład:** "Anna ma 29 lat i pracuje jako project manager..."

### Poziom 2: View Details (Reasoning)
- **Gdzie:** Dialog → Zakładka "Uzasadnienie"
- **Styl:** Edukacyjny, ze statystykami, wyjaśnia "dlaczego"
- **Zawartość:**
  - Orchestration brief (2000-3000 znaków)
  - Graph insights z wyjaśnieniami
  - Allocation reasoning
  - Overall context Polski

## Frontend - Zakładki w Persona Dialog

Po kliknięciu "Zobacz szczegóły" na personie:

```tsx
<Tabs defaultValue="profile">
  <TabsList>
    <TabsTrigger value="profile">
      <User /> Profil
    </TabsTrigger>
    <TabsTrigger value="reasoning">
      <Brain /> Uzasadnienie
    </TabsTrigger>
    <TabsTrigger value="rag">
      <Database /> Kontekst RAG
    </TabsTrigger>
  </TabsList>

  <TabsContent value="profile">
    {/* Basic info, demographics, psychographics */}
  </TabsContent>

  <TabsContent value="reasoning">
    <PersonaReasoningPanel persona={apiPersona} />
  </TabsContent>

  <TabsContent value="rag">
    {/* RAG citations */}
  </TabsContent>
</Tabs>
```

## Przykładowy Orchestration Brief

```markdown
# Grupa: Kobiety 25-34, wyższe wykształcenie, Warszawa (6 person)

## Dlaczego ta grupa?

W polskim społeczeństwie kobiety 25-34 z wyższym wykształceniem stanowią
około 17.3% populacji miejskiej według danych GUS z 2022 roku. To fascynująca
grupa społeczna która znajduje się w momencie życia pełnym zmian - balansują
między budowaniem kariery a decyzjami o rodzinie, między niezależnością
finansową a realiami rynku nieruchomości.

Dla tego badania ta grupa jest kluczowa bo to oni są early adopters nowych
produktów i usług. Wskaźniki pokazują że 78.4% tej grupy jest zatrudnionych
(najwyższa stopa w Polsce!), co oznacza że mają purchasing power...

## Kontekst zawodowy

Warszawa koncentruje 35% polskiego rynku tech, fintech i consulting. Dla młodych
kobiet z wyższym wykształceniem to oznacza szeroki wybór możliwości kariery...

[... dalszy tekst 1500+ znaków ...]
```

## Graph Insights - Przykład

```json
{
  "type": "Indicator",
  "summary": "Stopa zatrudnienia kobiet 25-34 z wyższym wykształceniem",
  "magnitude": "78.4%",
  "confidence": "high",
  "time_period": "2022",
  "source": "GUS",
  "why_matters": "Wysoka stopa zatrudnienia oznacza że ta grupa ma regularny dochód i potrzebę narzędzi financial management. To core target dla produktów fintech."
}
```

## API Endpoints

### Generate Personas (z orchestration)
```bash
POST /api/v1/projects/{project_id}/personas/generate
{
  "num_personas": 20,
  "use_rag": true,
  "adversarial_mode": false,
  "advanced_options": {
    "target_audience_description": "Osoby zainteresowane ekologią"
  }
}
```

### Get Persona Reasoning
```bash
GET /api/v1/personas/{persona_id}/reasoning

Response:
{
  "orchestration_brief": "DŁUGI (2000-3000 znaków) brief...",
  "graph_insights": [
    {
      "type": "Indicator",
      "summary": "...",
      "magnitude": "78.4%",
      "confidence": "high",
      "why_matters": "Dlaczego to ważne..."
    }
  ],
  "allocation_reasoning": "Dlaczego 6 z 20...",
  "demographics": {...},
  "overall_context": "Kontekst społeczny Polski..."
}
```

## Performance

- **Orchestration Step:** ~30-60s (Gemini 2.5 Pro)
- **Individual Personas:** ~1.5-3s każda (Gemini 2.5 Flash, parallel)
- **Total dla 20 person:** ~2-4 min (orchestration + generation)

## Konfiguracja

### Backend (app/core/config.py)
```python
# Orchestration używa Gemini 2.5 Pro
PERSONA_ORCHESTRATION_MODEL = "gemini-2.5-pro"

# Individual generation używa Gemini 2.5 Flash
PERSONA_GENERATION_MODEL = "gemini-2.5-flash"

# RAG Hybrid Search
RAG_USE_HYBRID_SEARCH = True
RAG_VECTOR_WEIGHT = 0.7  # 70% vector, 30% keyword
RAG_RRF_K = 60  # Reciprocal Rank Fusion parameter
```

## Pliki

**Backend:**
- `app/services/persona_orchestration.py` - Orchestration agent (462 linii)
- `app/services/persona_generator_langchain.py` - Generator person (MODIFIED)
- `app/api/personas.py` - API endpoints (MODIFIED)
- `app/schemas/persona.py` - Pydantic schemas (MODIFIED)

**Frontend:**
- `frontend/src/components/personas/PersonaReasoningPanel.tsx` - UI component (207 linii)
- `frontend/src/components/layout/Personas.tsx` - Główny component (MODIFIED - tabs)
- `frontend/src/types/index.ts` - TypeScript types (MODIFIED)
- `frontend/src/lib/api.ts` - API client (MODIFIED)

## Testowanie

1. **Uruchom backend:**
   ```bash
   docker-compose up -d
   ```

2. **Wygeneruj persony z orchestration:**
   - Otwórz projekt
   - Kliknij "Generuj persony"
   - Poczekaj ~2-4 min dla 20 person

3. **Zobacz reasoning:**
   - Kliknij "..." na personie → "Zobacz szczegóły"
   - Przełącz na zakładkę "Uzasadnienie"
   - Powinieneś zobaczyć długi brief od Gemini 2.5 Pro

## Troubleshooting

**Problem: Brak reasoning data**
- Persona wygenerowana przed włączeniem orchestration
- Rozwiązanie: Wygeneruj nowe persony

**Problem: Orchestration failuje**
- System ma fallback - persony zostaną wygenerowane bez briefów
- Sprawdź logi: `docker-compose logs api | grep orchestration`

**Problem: Frontend nie pokazuje zakładki**
- Sprawdź czy persona ma `rag_context_details.orchestration_reasoning`
- Sprawdź console browsera na błędy

## Future Enhancements

- [ ] Markdown rendering dla briefów (react-markdown)
- [ ] Cache orchestration plans (tego samego projektu)
- [ ] User feedback na quality briefów
- [ ] A/B testing: orchestration vs. no orchestration
- [ ] Export reasoning do PDF/DOCX
