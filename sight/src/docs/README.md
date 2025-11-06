# Dokumentacja Sight - SaaS Market Research Platform

Kompletna dokumentacja aplikacji Sight - narzędzia do badań rynku z AI-powered personas, ankietami, grupami fokusowymi i workflow automation.

---

## 📚 Spis Dokumentów

### 1. [ARCHITECTURE.md](./ARCHITECTURE.md)
**Architektura aplikacji i overview techniczny**

- Stack technologiczny (React, TypeScript, Tailwind 4.0)
- Branding i kolory (#F27405, #F29F05)
- Struktura layoutu (sidebar + content area, max-width 1920px)
- Motywy (light/dark mode)
- Nawigacja (6 głównych paneli)
- Responsive design (breakpointy, strategie)
- Wzorce komponentów
- Konwencje nazewnictwa
- State management approach
- Optymalizacja performance
- Dostępność (a11y)
- Future considerations (backend, deployment)

**Kiedy czytać**: Na początku, aby zrozumieć ogólną strukturę i filozofię aplikacji.

---

### 2. [PANELS.md](./PANELS.md)
**Szczegółowy opis wszystkich 6 paneli głównych**

#### Dashboard
- Quick actions
- Overview stats
- Recent activity
- Active projects

#### Projects
- ✅ Budget tracking z breakdown
- ✅ Timeline management (Gantt-style)
- ✅ Team collaboration
- ✅ ROI calculator
- ✅ Risk assessment

#### Personas
- ✅ AI Persona Generation Wizard (5 kroków)
- ✅ Behavior simulation
- ✅ Journey mapping
- ✅ Persona comparison
- ✅ 13 archetype templates (Gen Z, Millennials, etc.)
- PersonaDetailsDrawer z pełnymi danymi (demographics, psychographics, pain points, JTBD, desired outcomes)

#### Surveys
- ✅ Skip logic builder
- ✅ NPS calculator
- ✅ Quality control (attention checks, speeders)
- ✅ Cross-tabulation analysis
- ✅ Question library
- SurveyBuilder z 10+ typami pytań
- SurveyResults z zaawansowaną analizą

#### Focus Groups
- ✅ Live discussion tools (symulowany chat)
- ✅ AI moderation (auto-probing)
- ✅ Theme extraction
- ✅ Sentiment tracking
- ✅ Participant dynamics analysis

#### Workflow
- ✅ Process validation (pre-flight checks)
- ✅ Automated execution
- ✅ Auto-layout algorytmy
- ✅ Template library
- ✅ Integration points między panelami
- ReactFlow-based visual editor

**Kiedy czytać**: Gdy implementujesz lub modyfikujesz konkretny panel.

---

### 3. [COMPONENTS.md](./COMPONENTS.md)
**Struktura komponentów i wzorce implementacji**

- Hierarchia katalogów (`/components/...`)
- Opis każdego głównego komponentu
- Props interfaces
- Key state management
- Sub-komponenty (personas, focus-groups)
- UI components (shadcn/ui)
- Import patterns
- Component patterns (loading, empty, error states)
- Performance optimizations (memo, useMemo, useCallback)
- Testing considerations

**Kiedy czytać**: Gdy tworzysz nowe komponenty lub modyfikujesz istniejące.

---

### 4. [STYLING.md](./STYLING.md)
**Kompletny system stylowania z Tailwind CSS 4.0**

#### CSS Variables
- Light mode colors
- Dark mode colors
- Semantic tokens

#### Kolory
- Używanie semantic tokens (`bg-card`, `text-foreground`)
- Brand colors (`bg-brand-orange`, `text-brand-gold`)
- Utility classes

#### Typografia
- Font: Crimson Text (serif)
- Hierarchia nagłówków (h1-h4, p)
- **WAŻNE**: NIE nadpisuj font-size/weight na nagłówkach

#### Spacing
- Container padding (`px-8`)
- Gaps (`space-y-8`, `gap-6`)
- Margins

#### Layout
- Max widths (1920px dla paneli)
- Grid layouts (responsive)
- Flex layouts

#### Borders & Shadows
- Border utilities
- Custom shadows (`shadow-elevated`, `shadow-floating`)

#### Transitions & Animations
- Hover states
- Focus states
- Transitions

#### Komponenty UI
- Button variants i sizes
- Card styling
- Badge variants

#### Responsive Design
- Breakpointy
- Mobile-first approach

#### Dark Mode
- Toggle implementation
- Theme-aware styling

#### Accessibility
- Focus visible
- Screen reader only
- Color contrast (WCAG AA)

#### Custom Utilities
- Gradients
- Color utilities
- React Slick carousel styles

**Kiedy czytać**: Gdy dodajesz style lub debugujesz problemy z wyglądem.

---

### 5. [DATA_MODELS.md](./DATA_MODELS.md)
**Wszystkie struktury danych TypeScript**

#### Core Models
- Project (z budget, timeline, team, ROI, risks)
- Milestone
- TeamMember
- Risk

#### Persona Models
- Persona (complete z demographics, psychographics, behaviors)
- SegmentData
- SegmentInsight
- JobToBeDone
- PainPoint
- DesiredOutcome
- PersonaConfig (wizard configuration)

#### Survey Models
- Survey
- Question (10+ typów)
- SkipLogic
- SurveySettings
- SurveyResponse
- Answer
- SurveyResults
- QuestionResult
- CrossTabulation
- NPS calculation

#### Focus Group Models
- FocusGroup
- Message (z sentiment analysis)
- FocusGroupResults
- Theme (extracted themes)
- Quote (notable quotes)

#### Workflow Models
- Workflow
- WorkflowNode (8 typów)
- NodeConfig (per-type)
- WorkflowEdge
- WorkflowExecution

#### Activity & Analytics
- Activity (audit log)
- Analytics (metrics)

#### User Models (Future)
- User
- Organization

#### Mock Data Patterns
- Creating mock data
- Data generation helpers
- API response formats (future)

**Kiedy czytać**: Gdy pracujesz z danymi, tworzysz nowe typy lub integrujesz z backendem.

---

### 6. [IMPLEMENTATION.md](./IMPLEMENTATION.md)
**Praktyczne przewodniki implementacji**

#### Setup & Installation
- Zależności (z wersjami!)
- Import patterns

#### State Management Patterns
- Panel-level state
- Form state (React Hook Form 7.55.0)

#### Toast Notifications
- Używanie sonner@2.0.3
- Success, error, info, warning
- Loading states

#### Dialog/Modal Patterns
- Basic Dialog
- Sheet/Drawer
- Scrollable content

#### Carousel Implementation
- react-slick setup
- Responsive settings
- Custom arrows

#### Charts (recharts)
- Bar chart
- Pie chart
- Line chart
- Styling dla dark mode

#### Tabs Pattern
- Multi-tab interfaces
- Tab content organization

#### Multi-Step Wizard Pattern
- Progress indicator
- Validation per step
- Navigation controls

#### Progress Simulation
- Loading animations
- Progress bars

#### Filtering Pattern
- Search + filters
- useMemo optimization

#### CRUD Operations Pattern
- Create, Read, Update, Delete
- Duplicate functionality

#### Loading States
- Skeleton loading
- Spinner loading

#### Error Handling
- Try-catch patterns
- Error displays

#### Local Storage Persistence
- Save/load data
- useState initialization

#### Debouncing
- Search input debouncing
- Custom useDebounce hook

#### Theme Toggle Implementation
- useTheme hook
- Component implementation

#### Performance Tips
- useMemo
- useCallback
- React.memo

#### Accessibility Best Practices
- Semantic HTML
- ARIA labels
- Focus management
- Keyboard navigation

#### Testing Patterns (Future)
- Unit test examples

#### Deployment Checklist
- Pre-deployment checks

#### Common Gotchas & Solutions
- Import versioning
- Typography classes
- Color tokens
- Max widths

**Kiedy czytać**: Gdy implementujesz konkretną funkcjonalność lub debugujesz problem.

---

## 🚀 Quick Start

1. **Rozpocznij od** [ARCHITECTURE.md](./ARCHITECTURE.md) - zrozum ogólną strukturę
2. **Przeczytaj** [PANELS.md](./PANELS.md) - poznaj funkcje każdego panelu
3. **Sprawdź** [COMPONENTS.md](./COMPONENTS.md) - zobacz jak komponenty są zorganizowane
4. **Zapoznaj się z** [STYLING.md](./STYLING.md) - naucz się systemu stylowania
5. **Przejrzyj** [DATA_MODELS.md](./DATA_MODELS.md) - poznaj struktury danych
6. **Użyj** [IMPLEMENTATION.md](./IMPLEMENTATION.md) - jako odniesienia podczas kodowania

---

## 📋 Szybkie Odniesienia

### Kolory Brandingu
- **Primary Orange**: `#F27405` (bg-brand-orange)
- **Secondary Gold**: `#F29F05` (bg-brand-gold)
- **White**: `#FFFFFF`

### Typografia
- **Font**: Crimson Text (400, 600, 700)
- **Reguła**: NIE używaj `text-*` lub `font-*` classes na nagłówkach (chyba że konieczne)

### Layout
- **Max Width**: `max-w-[1920px]` dla paneli
- **Padding**: `px-8` standardowy
- **Dialogi**: `max-w-[95vw] lg:max-w-[1000px-1200px]`

### Imports (WAŻNE WERSJE!)
```typescript
import { toast } from 'sonner@2.0.3';
import { useForm } from 'react-hook-form@7.55.0';
```

### 6 Głównych Paneli
1. **Dashboard** - Quick actions, overview
2. **Projects** - Budget, timeline, team, ROI, risks
3. **Personas** - AI generation, behavior simulation, JTBD
4. **Surveys** - Skip logic, NPS, quality control, cross-tabs
5. **Focus Groups** - Live tools, AI moderation, theme extraction
6. **Workflow** - Validation, execution, auto-layout

### Shadcn Components Dostępne
42+ komponenty UI w `/components/ui/` gotowe do użycia:
- button, card, dialog, sheet, tabs
- input, select, slider, switch
- alert, badge, progress, skeleton
- table, tooltip, popover, dropdown-menu
- i wiele więcej...

---

## 🎯 Najbardziej Użyteczne Sekcje

### Dla Nowych Developerów
1. ARCHITECTURE.md → "Stack Technologiczny"
2. PANELS.md → "Panel Relationship Matrix"
3. STYLING.md → "Best Practices"
4. IMPLEMENTATION.md → "Common Gotchas & Solutions"

### Dla Implementacji Funkcji
1. PANELS.md → Szczegóły konkretnego panelu
2. COMPONENTS.md → Wzorce komponentów
3. DATA_MODELS.md → Typy danych
4. IMPLEMENTATION.md → Przykłady kodu

### Dla Stylowania
1. STYLING.md → "CSS Variables"
2. STYLING.md → "Użycie Kolorów"
3. STYLING.md → "Typografia"
4. STYLING.md → "Przykładowe Komponenty"

### Dla Integracji Backend
1. DATA_MODELS.md → Wszystkie interfaces
2. DATA_MODELS.md → "API Response Formats"
3. ARCHITECTURE.md → "Future Considerations"

---

## 🔍 Szukanie Informacji

### "Jak zrobić carousel?"
→ IMPLEMENTATION.md → "Carousel Implementation"

### "Jak stylować w dark mode?"
→ STYLING.md → "Dark Mode"

### "Jak stworzyć wizard?"
→ IMPLEMENTATION.md → "Multi-Step Wizard Pattern"

### "Jak zorganizować dane persony?"
→ DATA_MODELS.md → "Persona Models"

### "Jak dodać nowy panel?"
→ ARCHITECTURE.md → "Wzorce Komponentów"
→ COMPONENTS.md → "Główne Panele"
→ PANELS.md → "Wspólne Wzorce"

### "Jak używać toastów?"
→ IMPLEMENTATION.md → "Toast Notifications"

### "Jakie są dostępne komponenty UI?"
→ COMPONENTS.md → "UI Components"

---

## 📝 Konwencje Dokumentacji

### Code Blocks
- ✅ Zawierają pełny kontekst (imports, interfaces)
- ✅ Pokazują best practices
- ✅ Komentarze wyjaśniają kluczowe koncepcje

### Przykłady
- Praktyczne, działające przykłady
- Pokrywają common use cases
- Zawierają warianty (success, error, loading)

### Organizacja
- Od ogółu do szczegółu
- Logiczne grupowanie
- Cross-references między dokumentami

---

## 🛠 Maintenance

### Aktualizacja Dokumentacji
Gdy dodajesz nową funkcję:
1. Zaktualizuj odpowiedni plik (PANELS.md, COMPONENTS.md, etc.)
2. Dodaj nowe typy do DATA_MODELS.md
3. Dodaj przykład implementacji do IMPLEMENTATION.md
4. Zaktualizuj ARCHITECTURE.md jeśli zmienia się struktura

### Wersjonowanie
- Dokumentacja odzwierciedla current state aplikacji
- Major changes = update all relevant docs
- Minor changes = update specific sections

---

## 💡 Tips

1. **Ctrl+F jest twoim przyjacielem** - wyszukuj konkretne terms
2. **Czytaj przykłady kodu** - często szybsze niż opis tekstowy
3. **Sprawdź "Common Gotchas"** - zaoszczędź czas na debugowaniu
4. **Używaj typów** - wszystkie w DATA_MODELS.md
5. **Kopiuj pattern'y** - z IMPLEMENTATION.md

---

## 📧 Kontakt & Feedback

Jeśli znajdziesz błędy w dokumentacji lub masz sugestie:
- Dodaj komentarz w kodzie
- Zaktualizuj README z pytaniami
- Stwórz issue (future)

---

## 🎓 Learning Path

### Dzień 1: Overview
- [ ] Przeczytaj ARCHITECTURE.md
- [ ] Przejrzyj PANELS.md (10 min każdy panel)
- [ ] Zobacz strukturę w COMPONENTS.md

### Dzień 2: Styling & Data
- [ ] Przestudiuj STYLING.md
- [ ] Poznaj typy z DATA_MODELS.md
- [ ] Zrób test: zstyluj prosty komponent

### Dzień 3: Implementation
- [ ] Przeczytaj IMPLEMENTATION.md
- [ ] Zaimplementuj prosty dialog
- [ ] Dodaj toast notification

### Dzień 4: Advanced
- [ ] Zbuduj wizard (np. simplified persona wizard)
- [ ] Dodaj carousel
- [ ] Stworz chart

### Dzień 5: Integration
- [ ] Połącz komponenty w panel
- [ ] Dodaj CRUD operations
- [ ] Zaimplementuj filtering

---

## ✅ Checklist: "Czy rozumiem Sight?"

- [ ] Znam 6 głównych paneli i ich UNIKALNE funkcje
- [ ] Potrafię używać semantic color tokens
- [ ] Wiem jak importować toast i react-hook-form (z wersjami!)
- [ ] Rozumiem hierarchię komponentów
- [ ] Znam struktury danych (Persona, Survey, etc.)
- [ ] Potrafię stworzyć dialog i drawer
- [ ] Wiem jak dodać carousel
- [ ] Umiem używać recharts
- [ ] Rozumiem wzorzec wizard'a
- [ ] Znam best practices dla stylowania

Jeśli zaznaczyłeś wszystko - jesteś gotowy do pracy z Sight! 🎉

---

## 🚀 Start Coding!

**Przypomnienie**: To jest aplikacja mock/prototype. Wszystkie dane są frontend-only. 

Gdy będziesz gotowy na backend integration:
- Zobacz DATA_MODELS.md → "API Response Formats"
- Zobacz ARCHITECTURE.md → "Future Considerations"

**Happy Coding!** ✨
