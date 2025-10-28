# Focus Group Analysis View - Implementation Guide

## Przegląd

Kompletna implementacja widoku "Wyniki i Analiza" dla focus group, zgodnie ze specyfikacją UI/UX i architekturą techniczną.

## Zaimplementowane Komponenty

### 1. **Core Components** (`src/components/focus-group/analysis/`)

#### Main Containers:
- **`FocusGroupAnalysisView.tsx`** - Główny kontener z nawigacją sub-tabs
  - Sub-tab 1: "Podsumowanie AI" (ResultsAnalysisTab)
  - Sub-tab 2: "Surowe Odpowiedzi" (RawResponsesTab)
  - Lazy loading dla optymalnej wydajności

- **`ResultsAnalysisTab.tsx`** - Kontener dla AI-powered analysis
  - Zarządza stanem loading/error/success
  - Integracja z AI Summary API
  - Button "Wygeneruj ponownie"

- **`RawResponsesTab.tsx`** - Kontener dla surowych odpowiedzi
  - Filtrowanie (search, persona, question)
  - Lista odpowiedzi z paginacją

#### AI Summary Components:
- **`ExecutiveSummaryCard.tsx`** - Podsumowanie zarządcze z Sight logo i metadanymi
- **`KeyInsightsGrid.tsx`** - Grid 2x2 z numbered badges (4 kluczowe wnioski)
- **`SurprisingFindingsCard.tsx`** - Lista zaskakujących odkryć z bullet points
- **`SegmentAnalysisSection.tsx`** - 3 karty analizy segmentów
- **`StrategicRecommendationsCard.tsx`** - Rekomendacje strategiczne z priority badges

#### Raw Responses Components:
- **`ResponseCard.tsx`** - Pojedyncza odpowiedź z avatarem persony (memoized)
- **`ResponseFilters.tsx`** - Search input + 2 dropdowns (persona, question)
- **`ResponsesList.tsx`** - Lista z inteligentnym filtrowaniem

#### Custom Components:
- **`NumberedBadge.tsx`** - Okrągły badge z numerem (1-4)
- **`SegmentCard.tsx`** - Karta segmentu z nazwą, analizą i procentem
- **`RecommendationItem.tsx`** - Rekomendacja z priority badge (high/medium/low)

#### Skeletons:
- **`AISummarySkeleton.tsx`** - Loading skeleton dla AI Summary
- **`ResponsesSkeleton.tsx`** - Loading skeleton dla Raw Responses

### 2. **Hooks** (`src/hooks/focus-group/`)

- **`useFocusGroupAnalysis.ts`** - Pobieranie AI summary (staleTime: 10 min)
- **`useFocusGroupResponses.ts`** - Pobieranie surowych odpowiedzi (staleTime: 3s)
- **`useRegenerateAnalysis.ts`** - Mutation do regeneracji AI summary

### 3. **Integracja z FocusGroupView**

- Zmiana nazw tabów na polskie:
  - "Configuration" → "Konfiguracja"
  - "Discussion" → "Dyskusja"
  - "Results & Analysis" → "Wyniki i Analiza"

- Zastąpienie zawartości "Results" tab nowym komponentem `FocusGroupAnalysisView`
- Lazy loading z Suspense dla optymalnej wydajności

## API Endpoints (już gotowe w backend)

```typescript
// GET /api/v1/focus-groups/{id}/ai-summary
interface AISummary {
  executive_summary: string;
  key_insights: string[];
  surprising_findings: string[];
  segment_analysis: Record<string, string>;
  recommendations: string[];
  sentiment_narrative: string;
  metadata: {
    focus_group_id: string;
    generated_at: string;
    model_used: string;
    total_responses: number;
    total_participants: number;
    questions_asked?: number;
  };
}

// GET /api/v1/focus-groups/{id}/responses
interface FocusGroupResponses {
  focus_group_id: string;
  total_responses: number;
  questions: Array<{
    question: string;
    responses: Array<{
      persona_id: string;
      response: string;
      created_at: string;
    }>;
  }>;
}

// POST /api/v1/focus-groups/{id}/ai-summary
// Regeneruje AI summary (params: use_pro_model, include_recommendations)
```

## Testing Guide

### Quick Start

```bash
# 1. Uruchom backend
cd /Users/jakubwdowicz/market-research-saas
docker-compose up -d

# 2. Uruchom frontend (dev mode)
cd frontend
npm run dev

# 3. Otwórz http://localhost:5173
```

### Test Scenarios

#### Scenario 1: Completed Focus Group z AI Summary
1. Zaloguj się do aplikacji
2. Wybierz projekt z completed focus group
3. Kliknij na focus group ze statusem "Completed"
4. Przejdź do zakładki "Wyniki i Analiza"
5. **Powinno się wyświetlić:**
   - Sub-tab "Podsumowanie AI" (domyślny)
   - Executive Summary Card z logo Sight i metadanymi
   - Key Insights Grid (2x2 z numbered badges)
   - Surprising Findings Card (bullet points z żółtym accentem)
   - Segment Analysis Section (3 karty segmentów)
   - Strategic Recommendations Card (z priority badges)
   - Button "Wygeneruj ponownie" w prawym górnym rogu

6. Kliknij na sub-tab "Surowe Odpowiedzi"
7. **Powinno się wyświetlić:**
   - Search input + 2 dropdowns (Wszyscy uczestnicy, Wszystkie pytania)
   - Lista pytań z odpowiedziami
   - Każda odpowiedź z avatarem persony

#### Scenario 2: Completed Focus Group BEZ AI Summary
1. Znajdź completed focus group bez wygenerowanej analizy AI
2. Przejdź do "Wyniki i Analiza" → "Podsumowanie AI"
3. **Powinno się wyświetlić:**
   - Komunikat "Analiza AI nie została jeszcze wygenerowana"
   - Button "Wygeneruj analizę AI"
4. Kliknij button
5. **Powinno się pokazać:**
   - Spinner z tekstem "Generowanie analizy..."
   - Po ~30-60s pojawi się pełna analiza AI

#### Scenario 3: Running Focus Group
1. Znajdź focus group ze statusem "Running"
2. Przejdź do "Wyniki i Analiza"
3. **Powinno się wyświetlić:**
   - Spinner z tekstem "Dyskusja w toku"
   - Progress bar z procentem ukończenia
   - Liczba odpowiedzi: X/Y odpowiedzi

#### Scenario 4: Pending Focus Group
1. Znajdź focus group ze statusem "Pending"
2. Przejdź do "Wyniki i Analiza"
3. **Powinno się wyświetlić:**
   - Ikona BarChart3
   - Komunikat "Brak wyników"
   - "Uruchom najpierw dyskusję..."

#### Scenario 5: Filtrowanie Raw Responses
1. Otwórz completed focus group
2. Przejdź do "Surowe Odpowiedzi"
3. **Testuj filtry:**
   - Wpisz tekst w search → odpowiedzi filtrują się w czasie rzeczywistym
   - Wybierz konkretną personę z dropdown → pokazują się tylko jej odpowiedzi
   - Wybierz konkretne pytanie → pokazują się tylko odpowiedzi na to pytanie
   - Kombinacja filtrów działa poprawnie

4. **Test edge cases:**
   - Szukaj tekstu, którego nie ma → "Brak odpowiedzi spełniających kryteria"
   - Wybierz personę bez odpowiedzi → pusty widok z komunikatem

#### Scenario 6: Responsywność
1. Otwórz DevTools (F12)
2. Testuj różne breakpointy:
   - **Mobile (375px):** Filtry stackują się pionowo, karty full-width
   - **Tablet (768px):** Grid 2x2 dla Key Insights, segment cards 2 kolumny
   - **Desktop (1280px+):** Pełny grid layout, 3 kolumny dla segmentów

#### Scenario 7: Regeneracja AI Summary
1. Otwórz completed focus group z AI summary
2. Kliknij "Wygeneruj ponownie"
3. **Powinno się wydarzyć:**
   - Button zmienia się na "Generowanie..." z spinnerem
   - Po ~30-60s pokazuje się nowa analiza
   - Toast notification: "Analiza AI została wygenerowana"
   - Cache zostaje zinwalidowany

### Performance Testing

```bash
# Build production
npm run build

# Preview production build
npm run preview
```

**Sprawdź:**
- Lazy loading działa (ResultsAnalysisTab ładuje się tylko po kliknięciu)
- Code splitting: `FocusGroupAnalysisView-*.js` i `ResultsAnalysisTab-*.js` osobne chunki
- Time to Interactive < 3s
- React Query cache działa (drugi fetch z cache)

### Error Handling Testing

#### Test 1: Network Error
```bash
# Wyłącz backend
docker-compose down api
```
- Przejdź do "Wyniki i Analiza"
- **Powinno się wyświetlić:** Error state z komunikatem błędu

#### Test 2: 404 Not Found (brak AI summary)
- Focus group completed, ale bez AI summary
- **Powinno się wyświetlić:** "Analiza AI nie została jeszcze wygenerowana" + button

#### Test 3: Empty Responses
- Focus group completed, ale bez odpowiedzi (edge case)
- **Powinno się wyświetlić:** "Brak odpowiedzi" komunikat

## Checklist Pre-Launch

### Funkcjonalność
- [ ] Wszystkie 4 statusy focus group wyświetlają się poprawnie (pending/running/completed/failed)
- [ ] AI Summary ładuje się z cache po pierwszym fetch
- [ ] Raw Responses filtrują się poprawnie (search + 2 dropdowns)
- [ ] Regeneracja AI summary działa
- [ ] Toast notifications pokazują się po akcjach
- [ ] Lazy loading działa (sprawdź Network tab w DevTools)

### UI/UX
- [ ] Wszystkie texty PO POLSKU
- [ ] Crimson Text font używany dla headings
- [ ] Figma colors używane (figma-primary, figma-secondary, etc.)
- [ ] Border radius zgodny z designem (figma-card, figma-inner, figma-button)
- [ ] Numbered badges (1-4) w Key Insights
- [ ] Priority badges (high/medium/low) w Recommendations
- [ ] Sight logo w Executive Summary Card
- [ ] Avatary person z gradientem (figma-primary → figma-secondary)

### Responsywność
- [ ] Mobile (375px): Wszystko stackuje się pionowo
- [ ] Tablet (768px): Grid 2x2 dla Key Insights
- [ ] Desktop (1280px+): Pełny layout 3 kolumny dla segmentów

### Performance
- [ ] Build size < 1.5MB (gzip)
- [ ] Lazy loading chunks < 10KB każdy
- [ ] React Query staleTime ustawiony (10 min dla AI summary, 3s dla responses)
- [ ] Memoization w ResponseCard (React.memo)

### Error Handling
- [ ] Network errors wyświetlają się czytelnie
- [ ] 404 (brak AI summary) obsłużony
- [ ] Empty states dla wszystkich scenariuszy
- [ ] Loading skeletons podczas fetch

### Accessibility
- [ ] Tab navigation działa
- [ ] ARIA labels na interaktywnych elementach
- [ ] Screen reader support (testuj z VoiceOver/NVDA)
- [ ] Focus indicators widoczne

## Known Issues / Limitations

### Current Limitations:
1. **Brak virtualizacji:** ResponsesList nie używa react-window (implementacja przy >50 responses)
2. **Brak export:** Brak przycisku "Export to PDF" (można dodać w przyszłości)
3. **Priority badges auto-assigned:** Priority dla recommendations przypisywane automatycznie based na pozycji
4. **Percentage dla segmentów:** Równomiernie rozdzielony, zamiast rzeczywistego z danych

### Edge Cases:
- Focus group bez segment_analysis → sekcja nie wyświetla się
- Focus group bez recommendations → karta nie wyświetla się
- Bardzo długie odpowiedzi (>1000 chars) → mogą overflow na mobile

## Next Steps / Future Enhancements

1. **Export to PDF:** Button do eksportu AI Summary jako PDF
2. **Sentiment Analysis Visualization:** Wykresy dla sentiment_narrative
3. **Comparison View:** Porównanie wyników z innych focus groups
4. **Real-time Updates:** WebSocket dla live responses podczas running
5. **Advanced Filters:** Filter po sentiment, response length, timestamp range
6. **Annotations:** Możliwość dodawania notatek do odpowiedzi
7. **Highlights:** Podświetlanie kluczowych fraz w odpowiedziach

## Troubleshooting

### Problem: Build fails with TypeScript errors
**Rozwiązanie:**
```bash
cd frontend
npm run build
# Sprawdź błędy, popraw typy
```

### Problem: API 404 dla /ai-summary
**Rozwiązanie:**
- Sprawdź czy backend jest up: `docker-compose ps`
- Sprawdź czy focus group jest completed: `status === 'completed'`
- Wygeneruj AI summary: Kliknij "Wygeneruj analizę AI"

### Problem: React Query cache nie działa
**Rozwiązanie:**
- Sprawdź `staleTime` w hooks:
  - `useFocusGroupAnalysis`: 10 * 60 * 1000 (10 min)
  - `useFocusGroupResponses`: 3000 (3s)
- Sprawdź DevTools → React Query → Cache

### Problem: Lazy loading nie działa
**Rozwiązanie:**
- Sprawdź Network tab w DevTools
- Powinny być osobne chunki: `FocusGroupAnalysisView-*.js`, `ResultsAnalysisTab-*.js`
- Jeśli nie ma chunków → sprawdź vite.config.ts

### Problem: Filters nie działają
**Rozwiązanie:**
- Sprawdź czy `personas` są przekazane do `RawResponsesTab`
- Sprawdź console.log w `ResponsesList.tsx` → `filteredResponses`
- Sprawdź czy search query działa: `response.toLowerCase().includes(query)`

## Files Changed

### New Files:
```
frontend/src/
├── components/focus-group/analysis/
│   ├── FocusGroupAnalysisView.tsx
│   ├── ResultsAnalysisTab.tsx
│   ├── RawResponsesTab.tsx
│   ├── ExecutiveSummaryCard.tsx
│   ├── KeyInsightsGrid.tsx
│   ├── SurprisingFindingsCard.tsx
│   ├── SegmentAnalysisSection.tsx
│   ├── StrategicRecommendationsCard.tsx
│   ├── ResponseCard.tsx
│   ├── ResponseFilters.tsx
│   ├── ResponsesList.tsx
│   ├── NumberedBadge.tsx
│   ├── SegmentCard.tsx
│   ├── RecommendationItem.tsx
│   ├── AISummarySkeleton.tsx
│   ├── ResponsesSkeleton.tsx
│   └── index.ts
├── hooks/focus-group/
│   ├── useFocusGroupAnalysis.ts
│   ├── useFocusGroupResponses.ts
│   ├── useRegenerateAnalysis.ts
│   └── index.ts
```

### Modified Files:
```
frontend/src/
├── components/layout/FocusGroupView.tsx
│   - Dodano lazy import FocusGroupAnalysisView
│   - Zmiana nazw tabów na polskie
│   - Zastąpiono zawartość Results tab nowym komponentem
```

## Credits

- **Design:** Figma specs (89:2113 Discussion, 89:1758 Results & Analysis)
- **Architecture:** software-architect + backend-developer specs
- **Implementation:** frontend-developer (Claude Code)
- **Date:** 2025-10-28
