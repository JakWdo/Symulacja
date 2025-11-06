# Sight - SaaS Market Research Platform

## Branding

### Nazwa
**sight** - zawsze małymi literami

### Kolory
- **Primary (Orange)**: `#F27405` - główny kolor akcji i brandingu
- **Secondary (Gold)**: `#F29F05` - akcent, hover states
- **White**: `#FFFFFF` - tła w light mode

### Typografia
- **Font**: Crimson Text (Google Fonts)
- **Wagi**: 400 (normal), 600 (medium), 700 (bold - rzadko używane)
- **Styl**: Serif - profesjonalny, czytelny

## Filozofia Designu

### Minimalizm
- Przejrzysty interfejs bez zbędnych elementów
- Jasna hierarchia informacji
- Duże białe przestrzenie (spacing)
- Fokus na treści, nie ozdobnikach

### Prostota
- Intuicyjna nawigacja
- Jasne labele i opisy
- Spójne wzorce interakcji
- Natychmiastowy feedback (toasty, loading states)

### Profesjonalizm
- Inspiracja narzędziami analitycznymi (analytics dashboards, research tools)
- Czytelne wykresy i wizualizacje
- Precyzyjne metryki i dane
- Business-oriented language

## Zasady Projektowe

### 1. Semantic Tokens > Direct Colors
✅ Używaj: `bg-card`, `text-foreground`, `border-border`  
❌ Unikaj: `bg-white`, `text-black`, `border-gray-300`

### 2. Defaults dla Typografii
✅ Używaj prostych tagów: `<h1>`, `<h2>`, `<p>`  
❌ NIE nadpisuj: `text-4xl`, `font-bold` (chyba że konieczne)

### 3. Consistent Spacing
- Panels: `px-8`
- Sections: `space-y-8`
- Cards: `gap-6`
- Forms: `gap-4`

### 4. Max Width dla Szerokości
- Panele: `max-w-[1920px]` (ultra-wide support)
- Dialogi: `max-w-[95vw] lg:max-w-[1000px-1200px]`
- Drawery: `sm:max-w-[500px] lg:max-w-[700px]`

### 5. Responsive Always
- Mobile-first approach
- Test na wszystkich breakpointach
- Carousel adaptuje się do screen size
- Grid col counts responywne

### 6. Dark Mode Support
- Używaj semantic tokens (auto-adapt)
- Test w obu trybach zawsze
- Charts używają CSS variables (nie hardcoded colors)

## UI Components

### Shadcn/ui Library
Używamy 42+ gotowych komponentów z `/components/ui/`

**Najczęściej używane**:
- Button (4 variants, 4 sizes)
- Card (z CardHeader, CardTitle, CardContent)
- Dialog (modals)
- Sheet (drawers/side panels)
- Tabs (multi-section interfaces)
- Select (dropdowns)
- Input, Textarea (forms)
- Badge (status, labels)
- Progress (loading bars)
- Skeleton (loading states)
- Alert (errors, warnings)

### Custom Components
- ImageWithFallback (figma integration) - CHRONIONY
- ThemeToggle (light/dark switch)
- ScoreChart (recharts wrapper)

## Wzorce Interakcji

### Akcje Użytkownika
1. **Click** → Instant visual feedback (hover state)
2. **Submit** → Toast notification (success/error)
3. **Load** → Skeleton lub Spinner
4. **Delete** → Confirmation (destructive action)

### Navigation Flow
Sidebar → Panel → Detail View → Back to List

### Modals & Drawers
- Dialog - krótkie akcje (create, edit)
- Drawer/Sheet - szczegółowe widoki (persona details, project detail)
- Wizard - multi-step processes (persona generation)

## Zasady Contentu

### Teksty
- Krótkie, konkretne
- Business English (nawet gdy UI po polsku)
- Active voice ("Create project" nie "Project creation")

### Labele
- Jasne i opisowe
- Bez żargonu (chyba że industry-standard)
- Ikony + text (nie same ikony)

### Komunikaty
- Success: "Project created!" (konkretne, pozytywne)
- Error: "Failed to save. Please try again." (co poszło źle + next step)
- Loading: "Generating personas..." (co się dzieje)

## Performance

### Optymalizacja
- useMemo dla expensive calculations
- useCallback dla event handlers
- React.memo dla pure components
- Lazy loading dla dużych komponentów (future)

### Loading States
- Skeleton dla list/grids
- Spinner dla single actions
- Progress bar dla multi-step processes

## Accessibility (A11y)

### Must-Have
- Semantic HTML (`<button>` nie `<div onClick>`)
- ARIA labels gdzie potrzebne
- Keyboard navigation (Tab, Enter, Escape)
- Focus visible states
- Color contrast WCAG AA

### Testing
- Test z klawiaturą (bez myszy)
- Test z screen reader (future)
- Test color blindness (future)

## Dokumentacja

Kompletna dokumentacja w `/docs/`:

1. **README.md** - Start tutaj, overview całości
2. **ARCHITECTURE.md** - Struktura techniczna, stack, conventions
3. **PANELS.md** - Szczegóły 6 głównych paneli i ich funkcji
4. **COMPONENTS.md** - Hierarchia komponentów, props, patterns
5. **STYLING.md** - System kolorów, typografii, spacing, responsive
6. **DATA_MODELS.md** - TypeScript interfaces, struktury danych
7. **IMPLEMENTATION.md** - Praktyczne przykłady, code snippets, patterns

## Development Workflow

### Dodawanie Nowej Funkcji
1. Sprawdź PANELS.md - czy funkcja jest unikalna dla panelu?
2. Zobacz COMPONENTS.md - czy istnieje podobny komponent?
3. Użyj wzorca z IMPLEMENTATION.md
4. Zastosuj style z STYLING.md
5. Użyj typów z DATA_MODELS.md
6. Test w light i dark mode
7. Test responsive
8. Dodaj toast notifications

### Debugging
1. Sprawdź "Common Gotchas" w IMPLEMENTATION.md
2. Verify imports (wersje!)
3. Check console errors
4. Validate semantic tokens usage

## Import Versions (WAŻNE!)

Niektóre biblioteki wymagają specific versions:

```typescript
import { toast } from 'sonner@2.0.3';
import { useForm } from 'react-hook-form@7.55.0';
```

Pozostałe - latest version (bez @version).

## Nie rób tego!

❌ Hardcoded colors (`#fff`, `bg-white`)  
❌ Override typography bez powodu (`text-4xl font-bold` na `<h1>`)  
❌ Fixed widths (`w-[500px]` zamiast `max-w-[500px]`)  
❌ Zapomnienie o responsive  
❌ Zapomnienie o dark mode  
❌ Inline styles (używaj Tailwind classes)  
❌ Tworzenie własnych wersji shadcn components  
❌ Pomijanie toast notifications dla user actions  

## Zawsze rób to!

✅ Semantic color tokens  
✅ Default typography (proste tagi)  
✅ Max-width + mx-auto (centered content)  
✅ Responsive grid/flex  
✅ Test w obu trybach (light/dark)  
✅ Tailwind utility classes  
✅ Używaj gotowych shadcn components  
✅ Toast dla każdej ważnej akcji  
✅ Loading states  
✅ Empty states  
✅ Error handling  

## Resources

- **Tailwind CSS 4.0**: https://tailwindcss.com
- **shadcn/ui**: https://ui.shadcn.com
- **Lucide Icons**: https://lucide.dev
- **Recharts**: https://recharts.org
- **Crimson Text Font**: Google Fonts

## Questions?

Wszystkie odpowiedzi w `/docs/` - zacznij od README.md!
