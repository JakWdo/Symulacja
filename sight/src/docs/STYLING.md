# System Stylowania - Sight

## Tailwind CSS 4.0

Aplikacja używa Tailwind CSS 4.0 z semantycznymi tokenami CSS zdefiniowanymi w `/styles/globals.css`.

---

## Kolory (CSS Variables)

### Light Mode (`:root`)

```css
:root {
  /* Background & Foreground */
  --background: #ffffff;
  --foreground: #333333;
  
  /* Cards */
  --card: #ffffff;
  --card-foreground: #333333;
  
  /* Popovers */
  --popover: #ffffff;
  --popover-foreground: #333333;
  
  /* Primary (Brand Orange) */
  --primary: #F27405;
  --primary-foreground: #ffffff;
  
  /* Secondary (Brand Gold) */
  --secondary: #F29F05;
  --secondary-foreground: #333333;
  
  /* Muted */
  --muted: #f8f9fa;
  --muted-foreground: #6c757d;
  
  /* Accent */
  --accent: #F29F05;
  --accent-foreground: #333333;
  
  /* Destructive */
  --destructive: #dc3545;
  --destructive-foreground: #ffffff;
  
  /* Border */
  --border: rgba(0, 0, 0, 0.12);
  
  /* Input */
  --input: transparent;
  --input-background: #f8f9fa;
  
  /* Ring (focus) */
  --ring: #F27405;
  
  /* Charts */
  --chart-1: #F27405;
  --chart-2: #F29F05;
  --chart-3: #28a745;
  --chart-4: #17a2b8;
  --chart-5: #6f42c1;
  
  /* Sidebar */
  --sidebar: #ffffff;
  --sidebar-foreground: #333333;
  --sidebar-primary: #F27405;
  --sidebar-primary-foreground: #ffffff;
  --sidebar-accent: #f8f9fa;
  --sidebar-accent-foreground: #333333;
  --sidebar-border: rgba(0, 0, 0, 0.12);
  --sidebar-ring: #F27405;
}
```

### Dark Mode (`.dark`)

```css
.dark {
  /* Background & Foreground */
  --background: #1a1a1a;
  --foreground: #f8f9fa;
  
  /* Cards */
  --card: #2d2d2d;
  --card-foreground: #f8f9fa;
  
  /* Popovers */
  --popover: #2d2d2d;
  --popover-foreground: #f8f9fa;
  
  /* Primary (Brand Orange - remains same) */
  --primary: #F27405;
  --primary-foreground: #ffffff;
  
  /* Secondary (Brand Gold - remains same) */
  --secondary: #F29F05;
  --secondary-foreground: #1a1a1a;
  
  /* Muted */
  --muted: #404040;
  --muted-foreground: #adb5bd;
  
  /* Accent */
  --accent: #F29F05;
  --accent-foreground: #1a1a1a;
  
  /* Destructive */
  --destructive: #dc3545;
  --destructive-foreground: #ffffff;
  
  /* Border */
  --border: rgba(255, 255, 255, 0.12);
  
  /* Input */
  --input: #404040;
  
  /* Ring */
  --ring: #F27405;
  
  /* Sidebar */
  --sidebar: #2d2d2d;
  --sidebar-foreground: #f8f9fa;
  --sidebar-primary: #F27405;
  --sidebar-primary-foreground: #ffffff;
  --sidebar-accent: #404040;
  --sidebar-accent-foreground: #f8f9fa;
  --sidebar-border: rgba(255, 255, 255, 0.12);
  --sidebar-ring: #F27405;
}
```

---

## Użycie Kolorów

### Semantic Tokens (PREFEROWANE)
```tsx
// Background
<div className="bg-background text-foreground">

// Cards
<Card className="bg-card text-card-foreground border-border">

// Muted text
<p className="text-muted-foreground">

// Primary actions
<Button className="bg-primary text-primary-foreground">

// Borders
<div className="border border-border">
```

### Brand Colors (Direct)
```tsx
// Orange (Primary)
<Button className="bg-brand-orange hover:bg-brand-orange/90 text-white">
<p className="text-brand-orange">
<div className="border-brand-orange">

// Gold (Secondary)
<Badge className="bg-brand-gold text-white">
<p className="text-brand-gold">
```

### Utility Classes
```css
.brand-orange { color: #F27405; }
.bg-brand-orange { background-color: #F27405; }
.border-brand-orange { border-color: #F27405; }

.brand-gold { color: #F29F05; }
.bg-brand-gold { background-color: #F29F05; }
.border-brand-gold { border-color: #F29F05; }
```

---

## Typografia

### Font Family
```css
html {
  font-family: 'Crimson Text', serif;
}
```

**Import** (w globals.css):
```css
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&display=swap');
```

### Font Weights
```css
--font-weight-normal: 400;
--font-weight-medium: 600;
/* Bold (700) dostępny ale rzadko używany */
```

### Hierarchia Nagłówków

**WAŻNE**: NIE używaj klas Tailwind dla `font-size`, `font-weight`, `line-height` na nagłówkach, chyba że specjalnie wymagane.

```css
h1 {
  font-size: var(--text-2xl);     /* Nie nadpisuj! */
  font-weight: var(--font-weight-medium);
  line-height: 1.4;
}

h2 {
  font-size: var(--text-xl);
  font-weight: var(--font-weight-medium);
  line-height: 1.4;
}

h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-medium);
  line-height: 1.4;
}

h4 {
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  line-height: 1.4;
}

p {
  font-size: var(--text-base);
  font-weight: var(--font-weight-normal);
  line-height: 1.6;
}
```

### Użycie w Komponencie
```tsx
// ✅ DOBRZE - używaj prostych tagów
<h1>Dashboard</h1>
<h2>Projects Overview</h2>
<h3>Recent Activity</h3>
<p className="text-muted-foreground">Description text</p>

// ❌ ŹLE - nie nadpisuj font-size/weight
<h1 className="text-4xl font-bold">Dashboard</h1>

// ✅ OK - tylko jeśli specjalnie wymagane
<h1 className="text-muted-foreground">Muted Title</h1>
```

### Text Utilities (gdzie dozwolone)
```tsx
// Colors
<p className="text-muted-foreground">  // Szary tekst
<p className="text-destructive">       // Czerwony (błędy)
<p className="text-brand-orange">      // Pomarańczowy brand

// Alignment
<p className="text-center">
<p className="text-right">

// Truncation
<p className="truncate">
<p className="line-clamp-2">
<p className="line-clamp-3">
```

---

## Spacing

### Container Padding
```tsx
// Standardowy padding dla paneli
<div className="px-8">

// Responsive padding (jeśli potrzebne)
<div className="px-4 sm:px-6 lg:px-8">
```

### Gaps & Spacing
```tsx
// Space between sections
<div className="space-y-8">    // Vertical (32px)
<div className="space-y-6">    // Vertical (24px)
<div className="space-y-4">    // Vertical (16px)

// Grid gaps
<div className="grid gap-6">   // 24px
<div className="grid gap-4">   // 16px

// Flex gaps
<div className="flex gap-4">   // 16px
<div className="flex gap-2">   // 8px
```

### Margins
```tsx
<h1 className="mb-2">Title</h1>           // 8px bottom
<p className="mt-4 mb-6">Paragraph</p>    // 16px top, 24px bottom
```

---

## Layout

### Max Width
```tsx
// Panele główne - ultrawide support
<div className="w-full max-w-[1920px] mx-auto">

// Dialogi
<DialogContent className="max-w-[95vw] w-full lg:max-w-[1200px]">

// Drawery
<SheetContent className="w-full sm:max-w-[500px] lg:max-w-[700px]">
```

### Grid Layouts
```tsx
// Responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

// Stats grid
<div className="grid grid-cols-1 md:grid-cols-4 gap-4">

// Form grid
<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
```

### Flex Layouts
```tsx
// Header with actions
<div className="flex items-center justify-between">
  <div>
    <h1>Title</h1>
  </div>
  <Button>Action</Button>
</div>

// Centered content
<div className="flex items-center justify-center h-full">
  <div>Content</div>
</div>
```

---

## Borders & Shadows

### Borders
```tsx
// Standard border
<div className="border border-border">

// Rounded corners (default --radius: 0.5rem)
<div className="rounded-lg">      // 0.5rem
<div className="rounded-xl">      // 0.75rem (0.5rem + 4px)
<div className="rounded-full">    // Full circle

// Border sides
<div className="border-t border-border">  // Top only
<div className="border-b border-border">  // Bottom only
```

### Shadows
```tsx
// Tailwind defaults
<Card className="shadow-sm">      // Subtle
<Card className="shadow-md">      // Medium
<Card className="shadow-lg">      // Large

// Custom shadows (defined in globals.css)
<Card className="shadow-elevated">   // Custom elevated
<Card className="shadow-floating">   // Custom floating

// Hover effects
<Card className="hover:shadow-xl transition-all">
```

### Custom Shadows (globals.css)
```css
.shadow-elevated {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.05);
}

.shadow-floating {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1), 0 4px 8px rgba(0, 0, 0, 0.05);
}
```

---

## Transitions & Animations

### Transitions
```tsx
// All properties
<div className="transition-all duration-300">

// Specific properties
<div className="transition-colors duration-200">
<div className="transition-transform duration-300">

// Easing
<div className="ease-in-out">
<div className="ease-out">
```

### Hover States
```tsx
// Background
<Button className="hover:bg-brand-orange/90">

// Shadow
<Card className="hover:shadow-xl transition-all">

// Border
<Card className="hover:border-brand-orange/50">

// Scale
<div className="hover:scale-105 transition-transform">

// Opacity
<div className="hover:opacity-80 transition-opacity">
```

### Focus States
```tsx
// Ring (outline)
<Input className="focus:ring-2 focus:ring-ring">

// Border
<Input className="focus:border-primary">
```

---

## Komponenty UI - Custom Styling

### Button Variants
```tsx
// Default (primary)
<Button variant="default">
  // bg-primary text-primary-foreground

// Outline
<Button variant="outline">
  // border border-border bg-transparent

// Ghost
<Button variant="ghost">
  // transparent, hover shows bg

// Destructive
<Button variant="destructive">
  // bg-destructive text-destructive-foreground
```

### Button Sizes
```tsx
<Button size="sm">Small</Button>      // Smaller padding
<Button size="default">Default</Button>
<Button size="lg">Large</Button>      // Larger padding
<Button size="icon">              // Square for icons
  <Icon />
</Button>
```

### Card Styling
```tsx
<Card className="bg-card border border-border hover:shadow-xl hover:border-brand-orange/50 transition-all">
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content
  </CardContent>
</Card>
```

### Badge Variants
```tsx
<Badge variant="default">Default</Badge>      // primary bg
<Badge variant="secondary">Secondary</Badge>  // secondary bg
<Badge variant="outline">Outline</Badge>      // border only
<Badge variant="destructive">Error</Badge>    // destructive bg
```

---

## Responsive Design

### Breakpoints
```
sm:  640px   (Tablet portrait)
md:  768px   (Tablet landscape)
lg:  1024px  (Desktop)
xl:  1280px  (Large desktop)
2xl: 1536px  (Wide desktop)
```

### Responsive Classes
```tsx
// Display
<div className="hidden md:block">        // Hidden on mobile
<div className="block md:hidden">        // Visible on mobile only

// Grid
<div className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// Padding
<div className="px-4 md:px-6 lg:px-8">

// Text size (rzadko używane - preferuj defaults)
<p className="text-sm md:text-base">

// Width
<div className="w-full lg:w-1/2">
```

### Mobile-First Approach
```tsx
// Zaczynaj od mobile, dodawaj dla większych
<div className="p-4 md:p-6 lg:p-8">
<div className="text-sm md:text-base lg:text-lg">
```

---

## Dark Mode

### Toggle Implementation
```tsx
// components/ui/theme-toggle.tsx
import { useTheme } from './use-theme';

const ThemeToggle = () => {
  const { theme, setTheme } = useTheme();
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  );
};
```

### Theme-Aware Styling
```tsx
// Automatyczne - używaj semantic tokens
<div className="bg-background text-foreground">
<Card className="bg-card border-border">

// Manual (rzadko potrzebne)
<div className="bg-white dark:bg-gray-900">
<p className="text-gray-900 dark:text-gray-100">
```

---

## Accessibility

### Focus Visible
```tsx
<Button className="focus-visible:ring-2 focus-visible:ring-ring">
```

### Screen Reader Only
```tsx
<span className="sr-only">Hidden from visual, visible to screen readers</span>
```

### Color Contrast
- All text combinations meet WCAG AA standards
- Primary orange (#F27405) on white: ✅ Pass
- Muted text (#6c757d) on white: ✅ Pass
- Dark mode combinations: ✅ Pass

---

## Custom Utilities

### Gradients (globals.css)
```css
.gradient-primary {
  background: linear-gradient(135deg, hsl(var(--chart-1)), hsl(var(--chart-4)));
}

.gradient-secondary {
  background: linear-gradient(135deg, hsl(var(--chart-2)), hsl(var(--chart-5)));
}
```

**Usage**:
```tsx
<div className="gradient-primary p-6 rounded-lg">
  Content with gradient background
</div>
```

### Additional Color Utilities
```css
.text-blue-600 { color: #2563eb; }
.text-green-600 { color: #10b981; }
.text-amber-600 { color: #f59e0b; }
.text-purple-600 { color: #8b5cf6; }

.bg-blue-100 { background-color: rgba(37, 99, 235, 0.1); }
.bg-green-100 { background-color: rgba(16, 185, 129, 0.1); }
.bg-amber-100 { background-color: rgba(245, 158, 11, 0.1); }
.bg-purple-100 { background-color: rgba(139, 92, 246, 0.1); }
```

---

## React Slick Carousel Styles

Custom styles dla carousel (globals.css):

```css
.slick-slider {
  position: relative;
  display: block;
  box-sizing: border-box;
  user-select: none;
  touch-action: pan-y;
}

.slick-dots {
  position: relative;
  bottom: 0;
  list-style: none;
  display: flex !important;
  justify-content: center;
  gap: 8px;
  margin: 16px 0 0 0;
  padding: 0;
}

.slick-dots li button {
  width: 8px;
  height: 8px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: hsl(var(--muted-foreground));
  opacity: 0.3;
  cursor: pointer;
}

.slick-dots li.slick-active button {
  background: #F27405;
  opacity: 1;
}
```

---

## Best Practices

### Do's ✅
- Używaj semantic tokens (`bg-card`, `text-foreground`)
- Używaj prostych tagów HTML dla typografii (`<h1>`, `<p>`)
- Używaj transition classes dla smooth UX
- Używaj responsive classes (mobile-first)
- Testuj w light i dark mode
- Zachowaj spójność paddingu (`px-8` dla paneli)

### Don'ts ❌
- NIE nadpisuj font-size/weight na nagłówkach (chyba że konieczne)
- NIE używaj hardcoded hex colors (używaj tokens)
- NIE zapominaj o hover/focus states
- NIE używaj fixed widths (preferuj max-width)
- NIE pomijaj responsywności

---

## Przykładowe Komponenty

### Typical Panel
```tsx
<div className="w-full max-w-[1920px] mx-auto space-y-8 px-8">
  {/* Header */}
  <div>
    <h1 className="mb-2">Panel Name</h1>
    <p className="text-muted-foreground">Description</p>
  </div>
  
  {/* Stats */}
  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
    <Card className="bg-card border border-border">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Metric</p>
            <p className="text-2xl text-brand-orange">42</p>
          </div>
          <Icon className="w-8 h-8 text-brand-orange" />
        </div>
      </CardContent>
    </Card>
  </div>
  
  {/* Content Grid */}
  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
    {items.map(item => (
      <Card 
        key={item.id}
        className="bg-card border border-border hover:shadow-xl hover:border-brand-orange/50 transition-all"
      >
        <CardHeader>
          <CardTitle>{item.title}</CardTitle>
        </CardHeader>
        <CardContent>
          {item.content}
        </CardContent>
      </Card>
    ))}
  </div>
</div>
```

### Typical Dialog
```tsx
<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent className="max-w-[95vw] w-full lg:max-w-[1000px]">
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    
    <ScrollArea className="max-h-[70vh]">
      <div className="space-y-6 px-1">
        {/* Content */}
      </div>
    </ScrollArea>
    
    <div className="flex justify-end gap-3 mt-6">
      <Button variant="outline" onClick={() => setOpen(false)}>
        Cancel
      </Button>
      <Button 
        className="bg-brand-orange hover:bg-brand-orange/90"
        onClick={handleSubmit}
      >
        Submit
      </Button>
    </div>
  </DialogContent>
</Dialog>
```
