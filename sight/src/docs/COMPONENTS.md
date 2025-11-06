# Struktura Komponentów

## Hierarchia Katalogów

```
/components
├── Główne Panele (Top-level)
│   ├── Dashboard.tsx
│   ├── Projects.tsx
│   ├── ProjectDetail.tsx
│   ├── Personas.tsx
│   ├── Surveys.tsx
│   ├── FocusGroups.tsx
│   └── Workflow.tsx
│
├── Buildersy i Wizardy
│   ├── PersonaGenerationWizard.tsx
│   ├── SurveyBuilder.tsx
│   ├── SurveyResults.tsx
│   ├── FocusGroupBuilder.tsx
│   └── FocusGroup.tsx
│
├── Shared Components
│   ├── AppSidebar.tsx
│   ├── ScoreChart.tsx
│   └── Settings.tsx
│
├── Sub-komponenty Paneli
│   ├── /personas
│   │   ├── PersonaDetailsDrawer.tsx
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   └── /focus-groups
│       ├── ResultsAnalysis.tsx
│       ├── AISummarySection.tsx
│       ├── RawResponsesSection.tsx
│       ├── ResultsEmpty.tsx
│       ├── ResultsLoading.tsx
│       ├── ResultsError.tsx
│       └── index.ts
│
├── UI Components (shadcn/ui)
│   └── /ui
│       ├── accordion.tsx
│       ├── alert.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── drawer.tsx
│       ├── input.tsx
│       ├── select.tsx
│       ├── tabs.tsx
│       ├── progress.tsx
│       ├── slider.tsx
│       ├── badge.tsx
│       ├── scroll-area.tsx
│       ├── separator.tsx
│       ├── switch.tsx
│       ├── theme-toggle.tsx
│       └── ... (pozostałe shadcn components)
│
└── Figma Integration
    └── /figma
        └── ImageWithFallback.tsx
```

---

## Główne Panele

### Dashboard.tsx
**Odpowiedzialność**: Landing page z overview i quick actions

**Props**: Brak (zarządza własnym stanem)

**Key State**:
```tsx
const [projects, setProjects] = useState<Project[]>(mockProjects);
const [recentActivity, setRecentActivity] = useState<Activity[]>([]);
```

**Struktura**:
```tsx
<div className="w-full max-w-[1920px] mx-auto space-y-8 px-8">
  {/* Header */}
  <h1>Dashboard</h1>
  
  {/* Stats Grid */}
  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
    <StatCard />
  </div>
  
  {/* Quick Actions */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <QuickActionButton />
  </div>
  
  {/* Active Projects */}
  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
    <ProjectCard />
  </div>
</div>
```

---

### Projects.tsx
**Odpowiedzialność**: Lista projektów z filtrowaniem

**Props**: Brak

**Key Features**:
- Project grid
- Filtry (status, search)
- Create project dialog
- Navigation do ProjectDetail

**Key Functions**:
```tsx
const handleCreateProject = () => {
  setShowCreateDialog(true);
};

const handleViewProject = (projectId: number) => {
  setSelectedProject(projectId);
  setShowProjectDetail(true);
};
```

---

### ProjectDetail.tsx
**Odpowiedzialność**: Szczegóły pojedynczego projektu z tabami

**Props**:
```tsx
interface ProjectDetailProps {
  project: Project;
  onClose: () => void;
}
```

**Tabs**:
1. Overview
2. Budget
3. Timeline
4. Team
5. ROI Analysis
6. Risks

**Structure**:
```tsx
<Sheet>
  <SheetContent className="w-full sm:max-w-[600px] lg:max-w-[900px]">
    <Tabs defaultValue="overview">
      <TabsList>...</TabsList>
      
      <TabsContent value="overview">
        {/* Project info, description, key metrics */}
      </TabsContent>
      
      <TabsContent value="budget">
        {/* Budget breakdown, charts */}
      </TabsContent>
      
      {/* ... other tabs */}
    </Tabs>
  </SheetContent>
</Sheet>
```

---

### Personas.tsx
**Odpowiedzialność**: Galeria person z carousel i filtrowaniem

**Props**: Brak

**Key State**:
```tsx
const [selectedProject, setSelectedProject] = useState<number | null>(null);
const [filteredPersonas, setFilteredPersonas] = useState<Persona[]>([]);
const [showPersonaWizard, setShowPersonaWizard] = useState(false);
const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
const [showBehaviorSimulation, setShowBehaviorSimulation] = useState(false);
```

**Carousel Settings (react-slick)**:
```tsx
const sliderSettings = {
  dots: true,
  infinite: false,
  speed: 500,
  slidesToShow: Math.min(4, filteredPersonas.length),
  slidesToScroll: 1,
  arrows: true,
  responsive: [
    {
      breakpoint: 1920,
      settings: { slidesToShow: Math.min(4, filteredPersonas.length) }
    },
    {
      breakpoint: 1536,
      settings: { slidesToShow: Math.min(3, filteredPersonas.length) }
    },
    {
      breakpoint: 1280,
      settings: { slidesToShow: Math.min(2, filteredPersonas.length) }
    },
    {
      breakpoint: 768,
      settings: { slidesToShow: 1 }
    }
  ]
};
```

**Components Used**:
- PersonaGenerationWizard (dialog)
- PersonaDetailsDrawer (sheet)
- Behavior Simulation Dialog

---

### PersonaGenerationWizard.tsx
**Odpowiedzialność**: 5-stopniowy wizard do generowania person

**Props**:
```tsx
interface PersonaGenerationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerate: (config: PersonaConfig) => void;
}
```

**Key State**:
```tsx
const [currentStep, setCurrentStep] = useState(1); // 1-5
const [isGenerating, setIsGenerating] = useState(false);
const [generationProgress, setGenerationProgress] = useState(0);
const [config, setConfig] = useState<PersonaConfig>({...});
const [validationErrors, setValidationErrors] = useState<string[]>([]);
```

**Steps**:
1. Basic Setup (personaCount, adversarialMode, demographicPreset)
2. Demographics (age, gender, education, income)
3. Geography (cities, urbanicity)
4. Psychographics (values, interests)
5. Advanced (industries, personality)

**Validation**:
```tsx
const validateStep = (step: number): string[] => {
  const errors: string[] = [];
  
  if (step === 1) {
    if (config.personaCount < 1) errors.push("At least 1 persona required");
  }
  
  if (step === 2) {
    const ageTotal = Object.values(config.ageGroups)
      .reduce((sum, [val]) => sum + val, 0);
    if (ageTotal !== 100) errors.push("Age distribution must sum to 100%");
  }
  
  // ... more validation
  
  return errors;
};
```

**Navigation**:
```tsx
const handleNext = () => {
  const errors = validateStep(currentStep);
  if (errors.length > 0) {
    setValidationErrors(errors);
    return;
  }
  setCurrentStep(prev => Math.min(prev + 1, 5));
};

const handlePrevious = () => {
  setCurrentStep(prev => Math.max(prev - 1, 1));
};
```

**Generation**:
```tsx
const handleGenerate = async () => {
  setIsGenerating(true);
  setGenerationProgress(0);
  
  // Simulate generation
  const interval = setInterval(() => {
    setGenerationProgress(prev => {
      if (prev >= 100) {
        clearInterval(interval);
        onGenerate(config);
        onOpenChange(false);
        return 100;
      }
      return prev + 8;
    });
  }, 200);
};
```

---

### Surveys.tsx
**Odpowiedzialność**: Lista ankiet

**Key Features**:
- Survey cards grid
- Status filters
- Create survey button
- Navigation do SurveyBuilder/SurveyResults

---

### SurveyBuilder.tsx
**Odpowiedzialność**: Visual builder dla ankiet

**Key State**:
```tsx
const [surveyTitle, setSurveyTitle] = useState("");
const [questions, setQuestions] = useState<Question[]>([]);
const [selectedQuestion, setSelectedQuestion] = useState<number | null>(null);
const [showPreview, setShowPreview] = useState(false);
```

**Question Types**:
```tsx
type QuestionType = 
  | "multiple-choice"
  | "text-short"
  | "text-long"
  | "rating"
  | "nps"
  | "matrix"
  | "ranking"
  | "slider";
```

**Drag & Drop** (future - można użyć react-dnd):
```tsx
const handleDragEnd = (result: DropResult) => {
  if (!result.destination) return;
  
  const items = Array.from(questions);
  const [reordered] = items.splice(result.source.index, 1);
  items.splice(result.destination.index, 0, reordered);
  
  setQuestions(items);
};
```

---

### SurveyResults.tsx
**Odpowiedzialność**: Analiza wyników ankiety

**Tabs**:
1. Summary
2. Question Analysis
3. NPS
4. Cross-Tabs
5. Quality
6. Raw Data

**NPS Calculation**:
```tsx
const calculateNPS = (responses: number[]): number => {
  const promoters = responses.filter(r => r >= 9).length;
  const detractors = responses.filter(r => r <= 6).length;
  const total = responses.length;
  
  return Math.round(((promoters - detractors) / total) * 100);
};

// Categorize
const npsCategory = nps >= 50 ? "Excellent" : 
                   nps >= 0 ? "Good" : "Needs Improvement";
```

**Charts** (recharts):
```tsx
import { BarChart, Bar, PieChart, Pie, LineChart, Line } from "recharts";

<BarChart data={chartData}>
  <Bar dataKey="count" fill="#F27405" />
</BarChart>
```

---

### FocusGroups.tsx
**Odpowiedzialność**: Lista grup fokusowych

**Features**:
- Focus group cards
- Status indicators
- Create button
- Navigation do FocusGroupBuilder/FocusGroup

---

### FocusGroupBuilder.tsx
**Odpowiedzialność**: Setup grupy fokusowej

**Key State**:
```tsx
const [selectedPersonas, setSelectedPersonas] = useState<number[]>([]);
const [discussionTopics, setDiscussionTopics] = useState<string[]>([]);
const [duration, setDuration] = useState(60); // minutes
const [moderationStyle, setModerationStyle] = useState("moderate");
```

**Persona Selection**:
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {personas.map(persona => (
    <Card 
      className={selectedPersonas.includes(persona.id) ? "border-primary" : ""}
      onClick={() => togglePersona(persona.id)}
    >
      <Checkbox checked={selectedPersonas.includes(persona.id)} />
      {/* Persona info */}
    </Card>
  ))}
</div>
```

---

### FocusGroup.tsx
**Odpowiedzialność**: Live focus group session

**Key State**:
```tsx
const [messages, setMessages] = useState<Message[]>([]);
const [isRunning, setIsRunning] = useState(false);
const [currentTopic, setCurrentTopic] = useState(0);
const [sentiment, setSentiment] = useState<SentimentData>({});
```

**Message Structure**:
```tsx
interface Message {
  id: string;
  personaId: number;
  personaName: string;
  text: string;
  timestamp: Date;
  sentiment: "positive" | "neutral" | "negative";
  isModeratorPrompt?: boolean;
}
```

**AI Simulation**:
```tsx
const simulateResponse = (persona: Persona, topic: string): Message => {
  // Generate AI response based on persona profile
  return {
    id: generateId(),
    personaId: persona.id,
    personaName: persona.name,
    text: generatePersonaResponse(persona, topic),
    timestamp: new Date(),
    sentiment: calculateSentiment(text)
  };
};
```

---

### Workflow.tsx
**Odpowiedzialność**: Visual workflow builder

**Dependencies**: react-flow-renderer (lub podobna biblioteka)

**Key State**:
```tsx
const [nodes, setNodes] = useState<Node[]>([]);
const [edges, setEdges] = useState<Edge[]>([]);
const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
const [isExecuting, setIsExecuting] = useState(false);
```

**Node Types**:
```tsx
const nodeTypes = {
  start: StartNode,
  project: ProjectNode,
  persona: PersonaNode,
  survey: SurveyNode,
  focusGroup: FocusGroupNode,
  analysis: AnalysisNode,
  decision: DecisionNode,
  end: EndNode
};
```

**Custom Node Component**:
```tsx
const CustomNode = ({ data }: NodeProps) => {
  return (
    <div className="workflow-node">
      <Handle type="target" position="top" />
      <div className="node-content">
        {data.icon}
        <span>{data.label}</span>
      </div>
      <Handle type="source" position="bottom" />
    </div>
  );
};
```

---

## Sub-komponenty

### personas/PersonaDetailsDrawer.tsx

**Props**:
```tsx
interface PersonaDetailsDrawerProps {
  persona: Persona | null;
  open: boolean;
  onClose: () => void;
}
```

**Structure**:
```tsx
<Sheet open={open} onOpenChange={onClose}>
  <SheetContent className="w-full sm:max-w-[500px] lg:max-w-[700px]">
    <ScrollArea className="h-full">
      {/* Header */}
      <div className="space-y-4">
        <h2>{persona.name}</h2>
        <div className="flex items-center gap-4">
          <Badge>{persona.age} years old</Badge>
          <Badge>{persona.occupation}</Badge>
        </div>
      </div>
      
      {/* Background */}
      <Card>
        <h3>Background</h3>
        <p>{persona.background}</p>
      </Card>
      
      {/* Demographics */}
      <Card>
        <h3>Demographics</h3>
        <dl>
          <dt>Gender</dt>
          <dd>{persona.demographics.gender}</dd>
          {/* ... */}
        </dl>
      </Card>
      
      {/* Psychographics */}
      {/* Behavior Profiles */}
      {/* Segment Information */}
      {/* Pain Points */}
      {/* Jobs To Be Done */}
      {/* Desired Outcomes */}
    </ScrollArea>
  </SheetContent>
</Sheet>
```

### personas/types.ts

**Type Definitions**:
```tsx
export interface Persona {
  id: number;
  name: string;
  age: number;
  occupation: string;
  interests: string[];
  background: string;
  demographics: {
    gender: string;
    location: string;
    income: string;
    education: string;
  };
  psychographics: {
    personality: string[];
    values: string[];
    lifestyle: string;
  };
  behaviorProfiles?: {
    techSavviness: number;
    brandLoyalty: number;
    priceSensitivity: number;
    riskTolerance: number;
  };
  createdAt: string;
  projectId: number;
}

export interface PainPoint {
  id: string;
  title: string;
  description: string;
  severity: "high" | "medium" | "low";
  frequency: string;
  userQuote: string;
}

export interface JobToBeDone {
  id: string;
  job: string;
  context: string;
  successMetrics: string[];
  currentSolution: string;
  userQuote: string;
}

export interface DesiredOutcome {
  id: string;
  outcome: string;
  priority: "high" | "medium" | "low";
  satisfactionLevel: number; // 0-100
  userQuote: string;
}

export interface SegmentData {
  name: string;
  description: string;
  size: number; // percentage
  characteristics: string[];
}
```

---

### focus-groups/ResultsAnalysis.tsx

**Props**:
```tsx
interface ResultsAnalysisProps {
  focusGroupId: number;
  messages: Message[];
}
```

**Tabs**:
```tsx
<Tabs defaultValue="summary">
  <TabsList>
    <TabsTrigger value="summary">AI Summary</TabsTrigger>
    <TabsTrigger value="themes">Themes</TabsTrigger>
    <TabsTrigger value="quotes">Quotes</TabsTrigger>
    <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
    <TabsTrigger value="participation">Participation</TabsTrigger>
    <TabsTrigger value="transcript">Transcript</TabsTrigger>
  </TabsList>
  
  {/* Tab contents */}
</Tabs>
```

**Theme Extraction**:
```tsx
interface Theme {
  id: string;
  name: string;
  mentions: number;
  sentiment: "positive" | "neutral" | "negative";
  keyQuotes: string[];
  participants: string[];
}

const extractThemes = (messages: Message[]): Theme[] => {
  // AI-based theme extraction logic
  // Could use keyword clustering, topic modeling, etc.
  return themes;
};
```

---

## Shared Components

### AppSidebar.tsx

**Odpowiedzialność**: Główna nawigacja aplikacji

**Props**: Brak (używa context dla aktywnej strony)

**Structure**:
```tsx
<Sidebar className="w-[280px]">
  <SidebarHeader>
    <h1 className="brand-orange">sight</h1>
  </SidebarHeader>
  
  <SidebarContent>
    <SidebarMenu>
      {menuItems.map(item => (
        <SidebarMenuItem key={item.id}>
          <SidebarMenuButton
            onClick={() => setActivePage(item.id)}
            isActive={activePage === item.id}
          >
            <item.icon />
            <span>{item.label}</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  </SidebarContent>
  
  <SidebarFooter>
    <ThemeToggle />
  </SidebarFooter>
</Sidebar>
```

### ScoreChart.tsx

**Props**:
```tsx
interface ScoreChartProps {
  data: { label: string; value: number }[];
  height?: number;
}
```

**Usage**:
```tsx
<ScoreChart 
  data={[
    { label: "Q1", value: 85 },
    { label: "Q2", value: 78 },
    { label: "Q3", value: 92 }
  ]}
  height={300}
/>
```

---

## UI Components (shadcn/ui)

Wszystkie UI components z shadcn/ui są pre-styled i gotowe do użycia:

### Button
```tsx
import { Button } from "./components/ui/button";

<Button variant="default">Click me</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

### Card
```tsx
import { Card, CardHeader, CardTitle, CardContent } from "./components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

### Dialog
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./components/ui/dialog";

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
    </DialogHeader>
    {/* Content */}
  </DialogContent>
</Dialog>
```

### Sheet (Drawer)
```tsx
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "./components/ui/sheet";

<Sheet open={open} onOpenChange={setOpen}>
  <SheetContent side="right">
    <SheetHeader>
      <SheetTitle>Title</SheetTitle>
    </SheetHeader>
    {/* Content */}
  </SheetContent>
</Sheet>
```

Pełna lista dostępnych komponentów w `/components/ui/` - wszystkie są gotowe do użycia.

---

## Import Patterns

### Standardowe Importy
```tsx
// React
import { useState, useEffect } from 'react';

// UI Components
import { Button } from './components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';

// Icons
import { Plus, Edit, Trash, ChevronRight } from 'lucide-react';

// Sub-components
import { PersonaDetailsDrawer } from './components/personas/PersonaDetailsDrawer';

// Types
import type { Persona } from './components/personas/types';

// Toast
import { toast } from 'sonner@2.0.3';
```

---

## Component Patterns

### Loading State
```tsx
{isLoading ? (
  <div className="grid grid-cols-3 gap-6">
    {[1,2,3].map(i => (
      <Skeleton key={i} className="h-32" />
    ))}
  </div>
) : (
  <div className="grid grid-cols-3 gap-6">
    {items.map(item => <Card key={item.id}>...</Card>)}
  </div>
)}
```

### Empty State
```tsx
{items.length === 0 ? (
  <div className="text-center py-12">
    <Icon className="w-16 h-16 mx-auto text-muted-foreground" />
    <h3 className="mt-4">No items yet</h3>
    <p className="text-muted-foreground mt-2">Get started by creating one</p>
    <Button onClick={handleCreate} className="mt-4">
      <Plus className="w-4 h-4 mr-2" />
      Create
    </Button>
  </div>
) : (
  {/* Items */}
)}
```

### Error State
```tsx
{error ? (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertDescription>{error}</AlertDescription>
  </Alert>
) : (
  {/* Content */}
)}
```

---

## Performance Optimizations

### Memoization
```tsx
const expensiveCalculation = useMemo(() => {
  return calculateComplexMetric(data);
}, [data]);

const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### Lazy Loading (Future)
```tsx
const PersonaDetailsDrawer = lazy(() => 
  import('./components/personas/PersonaDetailsDrawer')
);
```

---

## Testing Considerations (Future)

### Unit Tests
```tsx
// PersonaCard.test.tsx
describe('PersonaCard', () => {
  it('renders persona name', () => {
    render(<PersonaCard persona={mockPersona} />);
    expect(screen.getByText('Sarah Johnson')).toBeInTheDocument();
  });
});
```

### Integration Tests
```tsx
// Personas.test.tsx
describe('Personas Flow', () => {
  it('opens wizard on generate button click', async () => {
    render(<Personas />);
    const button = screen.getByText('Generate Personas');
    fireEvent.click(button);
    expect(screen.getByText('AI Persona Generation Wizard')).toBeInTheDocument();
  });
});
```
