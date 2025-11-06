# Szczegóły Implementacji - Sight

Praktyczny przewodnik po implementacji kluczowych funkcji aplikacji.

---

## Setup & Installation

### Zależności
```json
{
  "dependencies": {
    "react": "^18.x",
    "lucide-react": "latest",
    "recharts": "latest",
    "react-slick": "latest",
    "slick-carousel": "latest",
    "sonner": "^2.0.3",
    "react-hook-form": "7.55.0"
  }
}
```

### Import Patterns
```typescript
// Standard
import { useState, useEffect, useMemo, useCallback } from 'react';

// UI Components
import { Button } from './components/ui/button';
import { Card } from './components/ui/card';
import { Dialog } from './components/ui/dialog';

// Icons
import { Plus, Edit, Trash } from 'lucide-react';

// Toast (WAŻNE: wersja 2.0.3)
import { toast } from 'sonner@2.0.3';

// React Hook Form (WAŻNE: wersja 7.55.0)
import { useForm } from 'react-hook-form@7.55.0';
```

---

## State Management Patterns

### Panel-Level State
```typescript
export default function Personas() {
  // Filter state
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  
  // Modal/Dialog state
  const [showWizard, setShowWizard] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  
  // Selected item state
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  
  // Data state
  const [personas, setPersonas] = useState<Persona[]>(mockPersonas);
  
  // Derived state (use useMemo for performance)
  const filteredPersonas = useMemo(() => {
    if (!selectedProject) return personas;
    return personas.filter(p => p.projectId === selectedProject);
  }, [personas, selectedProject]);
  
  return (
    // JSX
  );
}
```

### Form State (React Hook Form)
```typescript
import { useForm } from 'react-hook-form@7.55.0';

interface FormData {
  title: string;
  description: string;
  budget: number;
}

function CreateProjectDialog() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();
  
  const onSubmit = (data: FormData) => {
    console.log(data);
    toast.success("Project created!");
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input {...register("title", { required: "Title is required" })} />
      {errors.title && <span className="text-destructive">{errors.title.message}</span>}
      
      <Textarea {...register("description")} />
      
      <Input 
        type="number" 
        {...register("budget", { 
          required: "Budget is required",
          min: { value: 0, message: "Budget must be positive" }
        })} 
      />
      
      <Button type="submit">Create</Button>
    </form>
  );
}
```

---

## Toast Notifications

```typescript
import { toast } from 'sonner@2.0.3';

// Success
toast.success("Persona created successfully!");

// Error
toast.error("Failed to create persona");

// Info
toast.info("Processing your request...");

// Warning
toast.warning("This action cannot be undone");

// Custom with duration
toast.success("Saved!", { duration: 3000 });

// With action
toast.success("Persona deleted", {
  action: {
    label: "Undo",
    onClick: () => handleUndo()
  }
});

// Loading state
const toastId = toast.loading("Generating personas...");
// Later...
toast.success("Personas generated!", { id: toastId });
```

---

## Dialog/Modal Patterns

### Basic Dialog
```typescript
function MyDialog() {
  const [open, setOpen] = useState(false);
  
  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Dialog</Button>
      
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-[95vw] lg:max-w-[800px]">
          <DialogHeader>
            <DialogTitle>Dialog Title</DialogTitle>
            <DialogDescription>Description text</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Content */}
          </div>
          
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              Submit
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

### Sheet/Drawer Pattern
```typescript
function PersonaDrawer({ persona, open, onClose }: Props) {
  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent 
        side="right" 
        className="w-full sm:max-w-[500px] lg:max-w-[700px]"
      >
        <SheetHeader>
          <SheetTitle>{persona.name}</SheetTitle>
        </SheetHeader>
        
        <ScrollArea className="h-full mt-6">
          <div className="space-y-6 pr-6">
            {/* Content */}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
```

---

## Carousel Implementation (react-slick)

### Setup
```typescript
import Slider from 'react-slick';
import 'slick-carousel/slick/slick.css';
import 'slick-carousel/slick/slick-theme.css';

function PersonasCarousel({ personas }: Props) {
  const settings = {
    dots: true,
    infinite: false,
    speed: 500,
    slidesToShow: Math.min(4, personas.length),
    slidesToScroll: 1,
    arrows: true,
    nextArrow: <ChevronRight />,
    prevArrow: <ChevronLeft />,
    responsive: [
      {
        breakpoint: 1920,
        settings: {
          slidesToShow: Math.min(4, personas.length),
          slidesToScroll: 1
        }
      },
      {
        breakpoint: 1536,
        settings: {
          slidesToShow: Math.min(3, personas.length),
          slidesToScroll: 1
        }
      },
      {
        breakpoint: 1280,
        settings: {
          slidesToShow: Math.min(2, personas.length),
          slidesToScroll: 1
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1
        }
      }
    ]
  };
  
  return (
    <div className="persona-carousel">
      <Slider {...settings}>
        {personas.map(persona => (
          <div key={persona.id} className="px-3">
            <PersonaCard persona={persona} />
          </div>
        ))}
      </Slider>
    </div>
  );
}
```

### Custom Arrow Components
```typescript
const NextArrow = ({ onClick }: any) => (
  <button
    onClick={onClick}
    className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-card border border-border hover:bg-muted flex items-center justify-center"
  >
    <ChevronRight className="w-5 h-5" />
  </button>
);

const PrevArrow = ({ onClick }: any) => (
  <button
    onClick={onClick}
    className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-card border border-border hover:bg-muted flex items-center justify-center"
  >
    <ChevronLeft className="w-5 h-5" />
  </button>
);

// Use in settings
const settings = {
  // ...
  nextArrow: <NextArrow />,
  prevArrow: <PrevArrow />
};
```

---

## Charts (recharts)

### Bar Chart
```typescript
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Jan', value: 400 },
  { name: 'Feb', value: 300 },
  { name: 'Mar', value: 600 }
];

function MyBarChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
        <YAxis stroke="hsl(var(--muted-foreground))" />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px'
          }}
        />
        <Bar dataKey="value" fill="#F27405" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

### Pie Chart
```typescript
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = ['#F27405', '#F29F05', '#28a745', '#17a2b8'];

function MyPieChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

### Line Chart
```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function SentimentOverTime() {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
        <YAxis stroke="hsl(var(--muted-foreground))" />
        <Tooltip />
        <Line 
          type="monotone" 
          dataKey="sentiment" 
          stroke="#F27405" 
          strokeWidth={2}
          dot={{ fill: '#F27405', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

---

## Tabs Pattern

```typescript
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';

function ProjectDetail() {
  return (
    <Tabs defaultValue="overview">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="budget">Budget</TabsTrigger>
        <TabsTrigger value="timeline">Timeline</TabsTrigger>
        <TabsTrigger value="team">Team</TabsTrigger>
      </TabsList>
      
      <TabsContent value="overview" className="space-y-4">
        {/* Overview content */}
      </TabsContent>
      
      <TabsContent value="budget" className="space-y-4">
        {/* Budget content */}
      </TabsContent>
      
      {/* More tabs */}
    </Tabs>
  );
}
```

---

## Multi-Step Wizard Pattern

```typescript
function PersonaGenerationWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<PersonaConfig>(defaultConfig);
  const [errors, setErrors] = useState<string[]>([]);
  
  const totalSteps = 5;
  
  const validateStep = (step: number): string[] => {
    const errors: string[] = [];
    
    switch (step) {
      case 1:
        if (config.personaCount < 1) {
          errors.push("At least 1 persona required");
        }
        break;
      case 2:
        const ageTotal = Object.values(config.ageGroups)
          .reduce((sum, [val]) => sum + val, 0);
        if (ageTotal !== 100) {
          errors.push("Age distribution must sum to 100%");
        }
        break;
      // More cases...
    }
    
    return errors;
  };
  
  const handleNext = () => {
    const stepErrors = validateStep(currentStep);
    if (stepErrors.length > 0) {
      setErrors(stepErrors);
      return;
    }
    
    setErrors([]);
    setCurrentStep(prev => Math.min(prev + 1, totalSteps));
  };
  
  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };
  
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <Step1 config={config} setConfig={setConfig} />;
      case 2:
        return <Step2 config={config} setConfig={setConfig} />;
      // More cases...
      default:
        return null;
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] lg:max-w-[1200px] h-[90vh]">
        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-6">
          {[1, 2, 3, 4, 5].map(step => (
            <div 
              key={step}
              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                currentStep >= step 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {step}
            </div>
          ))}
        </div>
        
        {/* Validation Errors */}
        {errors.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside">
                {errors.map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}
        
        {/* Step Content */}
        <div className="flex-1 overflow-y-auto">
          {renderStepContent()}
        </div>
        
        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          
          {currentStep < totalSteps ? (
            <Button onClick={handleNext}>
              Next
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleGenerate}>
              Generate
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Progress Simulation

```typescript
function SimulateGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const handleGenerate = () => {
    setIsGenerating(true);
    setProgress(0);
    
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          toast.success("Generation complete!");
          return 100;
        }
        return prev + 8; // Increment by 8% every tick
      });
    }, 200); // Update every 200ms
  };
  
  return (
    <>
      <Button onClick={handleGenerate} disabled={isGenerating}>
        {isGenerating ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Generating...
          </>
        ) : (
          "Generate"
        )}
      </Button>
      
      {isGenerating && (
        <div className="mt-4">
          <Progress value={progress} className="w-full" />
          <p className="text-sm text-muted-foreground mt-2">
            {progress}% complete
          </p>
        </div>
      )}
    </>
  );
}
```

---

## Filtering Pattern

```typescript
function FilterableList() {
  const [items, setItems] = useState<Item[]>(mockItems);
  const [filters, setFilters] = useState({
    search: "",
    status: "all",
    category: "all"
  });
  
  // Memoize filtered results
  const filteredItems = useMemo(() => {
    return items.filter(item => {
      // Search filter
      if (filters.search && !item.name.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }
      
      // Status filter
      if (filters.status !== "all" && item.status !== filters.status) {
        return false;
      }
      
      // Category filter
      if (filters.category !== "all" && item.category !== filters.category) {
        return false;
      }
      
      return true;
    });
  }, [items, filters]);
  
  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex gap-4">
        <Input
          placeholder="Search..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        
        <Select
          value={filters.status}
          onValueChange={(value) => setFilters({ ...filters, status: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Results */}
      <div className="grid grid-cols-3 gap-6">
        {filteredItems.map(item => (
          <ItemCard key={item.id} item={item} />
        ))}
      </div>
      
      {/* Empty state */}
      {filteredItems.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No items found</p>
        </div>
      )}
    </div>
  );
}
```

---

## CRUD Operations Pattern

```typescript
function ItemManager() {
  const [items, setItems] = useState<Item[]>(mockItems);
  const [editingItem, setEditingItem] = useState<Item | null>(null);
  
  // Create
  const handleCreate = (newItem: Omit<Item, 'id'>) => {
    const item: Item = {
      ...newItem,
      id: Date.now(),
      createdAt: new Date().toISOString()
    };
    
    setItems(prev => [...prev, item]);
    toast.success("Item created!");
  };
  
  // Update
  const handleUpdate = (id: number, updates: Partial<Item>) => {
    setItems(prev => prev.map(item => 
      item.id === id 
        ? { ...item, ...updates, updatedAt: new Date().toISOString() }
        : item
    ));
    toast.success("Item updated!");
  };
  
  // Delete
  const handleDelete = (id: number) => {
    setItems(prev => prev.filter(item => item.id !== id));
    toast.success("Item deleted!");
  };
  
  // Duplicate
  const handleDuplicate = (id: number) => {
    const original = items.find(item => item.id === id);
    if (!original) return;
    
    const duplicate: Item = {
      ...original,
      id: Date.now(),
      name: `${original.name} (Copy)`,
      createdAt: new Date().toISOString()
    };
    
    setItems(prev => [...prev, duplicate]);
    toast.success("Item duplicated!");
  };
  
  return (
    // JSX
  );
}
```

---

## Loading States

### Skeleton Loading
```typescript
import { Skeleton } from './components/ui/skeleton';

function ItemList({ isLoading, items }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2 mt-2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-3 gap-6">
      {items.map(item => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  );
}
```

### Spinner Loading
```typescript
import { Loader2 } from 'lucide-react';

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
    </div>
  );
}
```

---

## Error Handling

```typescript
function DataFetcher() {
  const [data, setData] = useState(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    fetchData()
      .then(setData)
      .catch(err => {
        setError(err.message);
        toast.error("Failed to load data");
      })
      .finally(() => setIsLoading(false));
  }, []);
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  
  return <DataDisplay data={data} />;
}
```

---

## Local Storage Persistence

```typescript
// Save to localStorage
const saveToLocalStorage = (key: string, value: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
};

// Load from localStorage
const loadFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Failed to load from localStorage:', error);
    return defaultValue;
  }
};

// Usage in component
function PersistentComponent() {
  const [data, setData] = useState(() => 
    loadFromLocalStorage('myData', defaultData)
  );
  
  useEffect(() => {
    saveToLocalStorage('myData', data);
  }, [data]);
  
  return // JSX
}
```

---

## Debouncing (for search)

```typescript
import { useState, useEffect } from 'react';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
}

// Usage
function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  
  useEffect(() => {
    if (debouncedSearchTerm) {
      // Perform search
      console.log("Searching for:", debouncedSearchTerm);
    }
  }, [debouncedSearchTerm]);
  
  return (
    <Input
      placeholder="Search..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
    />
  );
}
```

---

## Theme Toggle Implementation

```typescript
// hooks/useTheme.ts
import { useEffect, useState } from 'react';

export function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') as 'light' | 'dark' || 'light';
    }
    return 'light';
  });
  
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);
  
  return { theme, setTheme };
}

// ThemeToggle component
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      {theme === 'dark' ? (
        <Sun className="h-5 w-5" />
      ) : (
        <Moon className="h-5 w-5" />
      )}
    </Button>
  );
}
```

---

## Performance Tips

### useMemo for Expensive Calculations
```typescript
const expensiveResult = useMemo(() => {
  return items
    .filter(item => item.active)
    .map(item => calculateComplexMetric(item))
    .reduce((sum, val) => sum + val, 0);
}, [items]);
```

### useCallback for Event Handlers
```typescript
const handleClick = useCallback((id: number) => {
  setItems(prev => prev.map(item => 
    item.id === id ? { ...item, clicked: true } : item
  ));
}, []); // Empty deps if no external dependencies

// Pass to child components
<ChildComponent onClick={handleClick} />
```

### React.memo for Pure Components
```typescript
const ItemCard = React.memo(({ item, onClick }: Props) => {
  return (
    <Card onClick={() => onClick(item.id)}>
      {/* Content */}
    </Card>
  );
});
```

---

## Accessibility Best Practices

```typescript
// Semantic HTML
<button onClick={handleClick}>Click me</button> // ✅
<div onClick={handleClick}>Click me</div>       // ❌

// ARIA labels
<Button aria-label="Close dialog">
  <X className="w-4 h-4" />
</Button>

// Focus management
const inputRef = useRef<HTMLInputElement>(null);

useEffect(() => {
  if (open) {
    inputRef.current?.focus();
  }
}, [open]);

<Input ref={inputRef} />

// Keyboard navigation
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Custom clickable
</div>
```

---

## Testing Patterns (Future)

### Unit Test Example
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });
});
```

---

## Deployment Checklist

- [ ] All dependencies installed
- [ ] Environment variables set
- [ ] Build completes without errors
- [ ] No console errors in production
- [ ] Theme toggle works in both modes
- [ ] All panels load correctly
- [ ] Responsive on mobile/tablet/desktop
- [ ] Accessibility check (keyboard navigation, screen reader)
- [ ] Performance check (Lighthouse score)
- [ ] Browser compatibility (Chrome, Firefox, Safari, Edge)

---

## Common Gotchas & Solutions

### 1. Toast import version
```typescript
// ✅ Correct
import { toast } from 'sonner@2.0.3';

// ❌ Wrong
import { toast } from 'sonner';
```

### 2. React Hook Form version
```typescript
// ✅ Correct
import { useForm } from 'react-hook-form@7.55.0';

// ❌ Wrong
import { useForm } from 'react-hook-form';
```

### 3. Don't override typography classes
```typescript
// ✅ Correct
<h1>Title</h1>

// ❌ Wrong (unless specifically needed)
<h1 className="text-4xl font-bold">Title</h1>
```

### 4. Use semantic color tokens
```typescript
// ✅ Correct
<div className="bg-card text-foreground border-border">

// ❌ Wrong
<div className="bg-white text-black border-gray-300">
```

### 5. Max width for panels
```typescript
// ✅ Correct
<div className="w-full max-w-[1920px] mx-auto px-8">

// ❌ Wrong
<div className="container px-4">
```
