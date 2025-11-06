# Architektura Aplikacji Sight

## Przegląd

Sight to aplikacja SaaS do badań rynku z minimalistycznym interfejsem inspirowanym profesjonalnymi narzędziami analitycznymi. Aplikacja umożliwia tworzenie projektów badawczych, generowanie person AI, symulowane grupy fokusowe i analizę wyników.

## Stack Technologiczny

- **Framework**: React + TypeScript
- **Styling**: Tailwind CSS 4.0 z semantycznymi tokenami CSS
- **Komponenty UI**: shadcn/ui
- **Ikony**: lucide-react
- **Font**: Crimson Text (Google Fonts)
- **Wykresy**: recharts
- **Karuzele**: react-slick
- **Toasty**: sonner

## Branding

### Kolory
- **Podstawowy (Primary)**: `#F27405` (pomarańczowy)
- **Biały**: `#FFFFFF`
- **Złoty/Żółty (Secondary)**: `#F29F05`

### Typografia
- **Font**: Crimson Text (serif)
- **Wagi**: 400 (normal), 600 (medium), 700 (bold)

## Struktura Layoutu

### Główny Layout (App.tsx)
```
┌─────────────────────────────────────────┐
│ [Sidebar - 280px]  [Main Content Area]  │
│                                          │
│ - Logo (sight)                           │
│ - Navigation Menu                        │
│ - Theme Toggle                           │
│                                          │
│ 6 głównych sekcji:                       │
│ • Dashboard                              │
│ • Projects                               │
│ • Personas                               │
│ • Surveys                                │
│ • Focus Groups                           │
│ • Workflow                               │
└─────────────────────────────────────────┘
```

### Maksymalne Szerokości
- **Panels**: `max-w-[1920px]` (zoptymalizowane dla ultraszerokich ekranów)
- **Padding**: `px-8` (standardowy dla wszystkich paneli)
- **Dialogi**: `max-w-[95vw] lg:max-w-[1000px-1200px]` (responsywne)

## Motywy (Theme)

### Light Mode (Domyślny)
- Background: `#ffffff`
- Foreground: `#333333`
- Card: `#ffffff`
- Muted: `#f8f9fa`
- Border: `rgba(0, 0, 0, 0.12)`

### Dark Mode
- Background: `#1a1a1a`
- Foreground: `#f8f9fa`
- Card: `#2d2d2d`
- Muted: `#404040`
- Border: `rgba(255, 255, 255, 0.12)`

## Nawigacja

### Sidebar (AppSidebar.tsx)
- Stała lewa nawigacja (280px szerokości)
- Logo "sight" na górze
- 6 głównych elementów menu z ikonami
- Theme toggle (light/dark) na dole
- Aktywny element podświetlony kolorem primary

### Menu Items
1. **Dashboard** - LayoutDashboard icon
2. **Projects** - Briefcase icon
3. **Personas** - Users icon
4. **Surveys** - FileText icon
5. **Focus Groups** - MessageSquare icon
6. **Workflow** - GitBranch icon

## Responsive Design

### Breakpointy
- **Mobile**: < 768px
- **Tablet**: 768px - 1280px
- **Desktop**: 1280px - 1536px
- **Wide Desktop**: 1536px - 1920px
- **Ultra-wide**: > 1920px

### Strategie
- Grid layouts adaptują się do rozmiaru ekranu
- Karuzele pokazują różną liczbę slajdów
- Dialogi i drawery zajmują 95vw na mobile, fixed width na desktop
- Sidebar collapsible na małych ekranach

## Wzorce Komponentów

### Panele Główne
Każdy panel działa według wzorca:
```tsx
<div className="w-full max-w-[1920px] mx-auto space-y-8 px-8">
  {/* Header */}
  <div>
    <h1 className="mb-2">Panel Name</h1>
    <p className="text-muted-foreground">Description</p>
  </div>
  
  {/* Content */}
  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
    {/* Cards/Components */}
  </div>
</div>
```

### Dialogi i Modals
```tsx
<Dialog>
  <DialogContent className="max-w-[95vw] w-full lg:max-w-[1200px]">
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    {/* Content */}
  </DialogContent>
</Dialog>
```

### Karty (Cards)
```tsx
<Card className="bg-card border border-border hover:shadow-xl transition-all">
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

## Konwencje Nazewnictwa

### Komponenty
- **PascalCase**: `PersonaDetailsDrawer`, `SurveyBuilder`
- **Sufiksy**: `Builder`, `Wizard`, `Dialog`, `Drawer`, `Section`

### Pliki
- Komponenty główne: `/components/[Name].tsx`
- Sub-komponenty: `/components/[panel-name]/[Component].tsx`
- UI komponenty: `/components/ui/[component].tsx`

### Classes CSS
- Tailwind utility classes
- Semantic tokens: `text-foreground`, `bg-card`, `border-border`
- Brand colors: `bg-brand-orange`, `text-brand-orange`, `border-brand-orange`

## State Management

### Local State (useState)
- Używany dla UI state w pojedynczych komponentach
- Przykłady: modals open/close, form inputs, selected items

### Mock Data
- Wszystkie dane są mockami w komponentach
- Struktury danych przygotowane dla przyszłej integracji z backend

## Optymalizacja Performance

### Code Splitting
- Lazy loading dla większych komponentów (future)
- Dynamic imports dla dialogów i drawerów (future)

### Memoization
- React.memo dla expensive components (gdzie potrzebne)
- useMemo/useCallback dla ciężkich obliczeń

## Dostępność (A11y)

- Semantyczne HTML (h1, h2, h3, p, button)
- ARIA labels w shadcn components
- Keyboard navigation
- Focus states
- Color contrast (WCAG AA)

## Bezpieczeństwo

- Brak przechowywania PII
- Client-side only (na razie)
- Input sanitization (gdzie potrzebne)
- XSS prevention poprzez React

## Future Considerations

### Backend Integration
- REST API lub GraphQL
- Supabase jako backend (opcjonalnie)
- Authentication & Authorization
- Real-time updates (WebSockets/Supabase Realtime)

### Data Persistence
- Database schema dla personas, projects, surveys
- File storage dla media
- Caching strategy

### Analytics
- User behavior tracking
- Performance monitoring
- Error tracking (Sentry)

## Maintenance

### Aktualizacje
- Regular dependency updates
- Security patches
- Tailwind 4.0 updates

### Testing
- Unit tests (future)
- Integration tests (future)
- E2E tests (future)

## Deployment

### Build
```bash
npm run build
```

### Environment Variables
- Theme preference
- API keys (future)
- Feature flags (future)
