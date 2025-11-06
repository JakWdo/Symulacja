# Panele Aplikacji Sight

Każdy panel ma być **unikalny bez powtarzających się funkcji**. Poniżej szczegółowy opis wszystkich 6 głównych paneli.

---

## 1. Dashboard

**Plik**: `/components/Dashboard.tsx`

### Cel
Szybki przegląd stanu projektów i quick actions.

### Funkcje
- **Quick Actions**: Szybkie utworzenie nowego projektu, persony, ankiety, grupy fokusowej
- **Overview Stats**: Podsumowanie liczby projektów, person, ankiet
- **Recent Activity**: Lista ostatnich działań w aplikacji
- **Active Projects**: Karty z aktywnymi projektami z quick access

### Komponenty UI
- Statistics cards z ikonami i wartościami
- Quick action buttons z ikonami
- Recent activity timeline
- Project cards grid

### Kluczowe Funkcje
```tsx
// Quick action buttons
<Button onClick={() => navigate to create}>
  <Plus /> Create New Project
</Button>

// Stats overview
<Card>
  <CardContent>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-muted-foreground">Total Projects</p>
        <p className="text-2xl text-brand-orange">{count}</p>
      </div>
      <Icon className="w-8 h-8 text-brand-orange" />
    </div>
  </CardContent>
</Card>
```

---

## 2. Projects

**Plik**: `/components/Projects.tsx`, `/components/ProjectDetail.tsx`

### Cel
Kompleksowe zarządzanie projektami badawczymi z analizą ROI, timeline, budżetem.

### Funkcje UNIKALNE dla Projects
- ✅ **Budget Tracking**: Śledzenie budżetu projektu z breakdown na kategorie
- ✅ **Timeline Management**: Gantt-style timeline z kamieniami milowymi
- ✅ **Team Collaboration**: Zarządzanie zespołem i uprawnieniami
- ✅ **ROI Calculator**: Kalkulacja zwrotu z inwestycji w badania
- ✅ **Risk Assessment**: Identyfikacja i monitorowanie ryzyk projektu

### Główne Sekcje

#### Project List View
- Grid z kartami projektów
- Filtry: status, data, typ badania
- Search bar
- Create new project button

#### Project Detail View (ProjectDetail.tsx)
```tsx
// Tabs structure
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="budget">Budget</TabsTrigger>
    <TabsTrigger value="timeline">Timeline</TabsTrigger>
    <TabsTrigger value="team">Team</TabsTrigger>
    <TabsTrigger value="roi">ROI Analysis</TabsTrigger>
    <TabsTrigger value="risks">Risks</TabsTrigger>
  </TabsList>
</Tabs>
```

#### Budget Tab
- Breakdown po kategoriach (Personnel, Software, Incentives, etc.)
- Budget utilization chart
- Spending forecast
- Cost per insight metric

#### Timeline Tab
- Milestone cards z datami
- Progress tracking
- Dependencies visualization
- Delay alerts

#### Team Tab
- Team member cards z rolami
- Permissions management
- Activity log per member
- Collaboration metrics

#### ROI Analysis Tab
- Expected vs actual ROI
- Cost-benefit analysis
- Time-to-insight metrics
- Business impact calculator

#### Risks Tab
- Risk matrix (probability x impact)
- Mitigation strategies
- Risk status tracking
- Alert system

---

## 3. Personas

**Plik**: `/components/Personas.tsx`, `/components/PersonaGenerationWizard.tsx`, `/components/personas/PersonaDetailsDrawer.tsx`

### Cel
Generowanie i zarządzanie AI personas z zaawansowaną symulacją zachowań.

### Funkcje UNIKALNE dla Personas
- ✅ **AI Persona Generation Wizard**: 5-stopniowy wizard z precyzyjną kontrolą demografii
- ✅ **Behavior Simulation**: Symulacja zachowań persony w różnych scenariuszach
- ✅ **Journey Mapping**: Wizualizacja customer journey
- ✅ **Persona Comparison**: Porównanie wielu person side-by-side
- ✅ **Archetype Templates**: Predefiniowane archetypy (Gen Z, Millennials, etc.)

### Główne Komponenty

#### Personas List View
- Carousel z kartami person (react-slick)
- Filtry po projekcie
- Statistics overview (Total Personas, Avg Age, Demographics)
- Generate Personas button

#### Persona Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>{persona.name}</CardTitle>
    <p>{persona.age} • {persona.occupation}</p>
    <Badge>{persona.location}</Badge>
  </CardHeader>
  <CardContent>
    {/* Background */}
    <p>{persona.background}</p>
    
    {/* Behavior Profile */}
    <div className="grid grid-cols-2 gap-2">
      <Progress label="Tech Savviness" value={9/10} />
      <Progress label="Brand Loyalty" value={6/10} />
      <Progress label="Price Sensitivity" value={5/10} />
      <Progress label="Risk Tolerance" value={7/10} />
    </div>
    
    {/* Actions */}
    <Button>View Details</Button>
    <Button>Simulate Behavior</Button>
  </CardContent>
</Card>
```

#### PersonaGenerationWizard (5 Steps)

**Step 1: Basic Setup**
- Liczba person (slider 1-100)
- Adversarial mode toggle (generuje person o przeciwnych cechach)
- Demographic presets (13 presetów: Gen Z, Millennials, Tech Pros, etc.)

**Step 2: Demographics**
- Age groups distribution (6 grup, slidery %)
- Gender distribution (Male, Female, Non-binary - slidery %)
- Education levels (5 poziomów - slidery %)
- Income brackets (6 przedziałów - slidery %)

**Step 3: Geography**
- Target cities (input z listą)
- Location distribution (weight per city)
- Urbanicity preference (Urban/Suburban/Rural - radio)

**Step 4: Psychographics**
- Required values (tags: Innovation, Environment, etc.)
- Excluded values (tags: np. Gambling)
- Required interests (tags: Technology, Travel, etc.)
- Excluded interests (tags)

**Step 5: Advanced**
- Target industries (multi-select)
- Personality skew (Big 5: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism - slidery)

Progress bar i validation errors w real-time.

#### PersonaDetailsDrawer

Drawer z prawej strony (Sheet component) zawierający:

**Sekcje:**
1. **Header**: Imię, wiek, zawód, lokalizacja
2. **Background**: Pełny opis persony (2-3 akapity)
3. **Demographics**: 
   - Gender, Location, Income, Education
   - Age group
4. **Psychographics**:
   - Personality traits (badges)
   - Values (badges)
   - Lifestyle description
5. **Behavior Profiles**:
   - Tech Savviness: 9/10
   - Brand Loyalty: 6/10
   - Price Sensitivity: 5/10
   - Risk Tolerance: 7/10
6. **Segment Information**:
   - Segment name (np. "Early Adopters")
   - Description
   - Size: X% of market
   - Key characteristics (bullet points)
7. **Pain Points**:
   - Lista pain points z:
     - Tytuł
     - Opis
     - Severity (High/Medium/Low - badge)
     - Frequency
     - User quote (italic)
8. **Jobs To Be Done**:
   - Lista JTBD z:
     - Job description
     - Context
     - Success metrics
     - Current solution
     - User quote
9. **Desired Outcomes**:
   - Lista outcomes z:
     - Outcome description
     - Priority (High/Medium/Low)
     - Current satisfaction level (%)
     - User quote

#### Behavior Simulation Dialog
- Custom question input
- AI odpowiedź symulująca myślenie persony
- Context z pełnego profilu persony

---

## 4. Surveys

**Plik**: `/components/Surveys.tsx`, `/components/SurveyBuilder.tsx`, `/components/SurveyResults.tsx`

### Cel
Tworzenie, zarządzanie i analiza ankiet z zaawansowaną logiką.

### Funkcje UNIKALNE dla Surveys
- ✅ **Skip Logic Builder**: Visual builder dla conditional questions
- ✅ **NPS Calculator**: Net Promoter Score z automatic categorization
- ✅ **Quality Control**: Attention checks, response time analysis
- ✅ **Cross-Tabulation**: Advanced cross-tab analysis
- ✅ **Question Library**: Reusable question templates

### Główne Komponenty

#### Surveys List View
- Grid z kartami ankiet
- Status badges (Draft, Active, Closed)
- Response count
- Completion rate
- Create survey button

#### SurveyBuilder
**Question Types:**
- Multiple Choice (single)
- Multiple Choice (multiple)
- Text Input (short)
- Text Input (long)
- Rating Scale (1-5, 1-10, NPS 0-10)
- Matrix/Grid
- Ranking
- Slider
- Date/Time

**Builder Features:**
- Drag & drop questions
- Question library sidebar
- Skip logic visual editor
- Attention check inserter
- Preview mode
- Response validation rules

**Skip Logic:**
```tsx
// Example structure
{
  questionId: "q1",
  logic: [
    {
      condition: "answer === 'Yes'",
      action: "jump_to",
      target: "q5"
    },
    {
      condition: "answer === 'No'",
      action: "jump_to",
      target: "q2"
    }
  ]
}
```

#### SurveyResults
**Analysis Tabs:**
1. **Summary**: Key metrics (responses, completion rate, avg time)
2. **Question Analysis**: Per-question breakdown z charts
3. **NPS**: Net Promoter Score calculation i segmentation
4. **Cross-Tabs**: Cross-tabulation matrix
5. **Quality**: Response quality metrics (speeders, straight-liners)
6. **Raw Data**: Export to CSV/Excel

**Visualizations:**
- Bar charts (recharts)
- Pie charts
- Line charts (time series)
- Heatmaps (cross-tabs)

---

## 5. Focus Groups

**Plik**: `/components/FocusGroups.tsx`, `/components/FocusGroup.tsx`, `/components/FocusGroupBuilder.tsx`, `/components/focus-groups/*`

### Cel
Symulowane grupy fokusowe z AI moderacją i analizą tematów.

### Funkcje UNIKALNE dla Focus Groups
- ✅ **Live Discussion Tools**: Real-time chat simulation
- ✅ **AI Moderation**: Automated probing questions
- ✅ **Theme Extraction**: Automatic theme identification
- ✅ **Sentiment Tracking**: Real-time sentiment analysis
- ✅ **Participant Dynamics**: Interaction patterns analysis

### Główne Komponenty

#### FocusGroups List View
- Grid z kartami grup fokusowych
- Status: Planning, In Progress, Completed
- Participant count (selected personas)
- Discussion topics
- Create new focus group button

#### FocusGroupBuilder
**Setup:**
- Select personas (multi-select z checkbox)
- Set discussion topics (list input)
- Duration (slider)
- Moderation style (Minimal, Moderate, Active)
- Auto-probing toggle

**Discussion Script:**
- Opening questions
- Main topics
- Probing questions (AI-generated)
- Closing questions

#### Focus Group Session (FocusGroup.tsx)
**Live View:**
```tsx
// Layout
<div className="grid grid-cols-[1fr,300px]">
  {/* Main Discussion Area */}
  <div>
    <ChatThread messages={messages} />
    <ModeratorControls />
  </div>
  
  {/* Sidebar */}
  <div>
    <ParticipantList />
    <SentimentMeter />
    <ThemeTracker />
  </div>
</div>
```

**Chat Messages:**
- Persona avatar + name
- Message text
- Timestamp
- Sentiment indicator (🟢🟡🔴)

**AI Moderator:**
- Probing questions based on responses
- Follow-up prompts
- Encouragement for quieter participants
- Theme summary prompts

#### Results Analysis (focus-groups/ResultsAnalysis.tsx)
**Tabs:**
1. **AI Summary**: Automatic summary z key insights
2. **Themes**: Extracted themes z frequency i sentiment
3. **Quotes**: Notable quotes z context
4. **Sentiment**: Sentiment over time chart
5. **Participation**: Participation balance chart
6. **Raw Transcript**: Full conversation export

**Theme Extraction:**
```tsx
{
  theme: "Price Sensitivity",
  mentions: 12,
  sentiment: "negative",
  keyQuotes: ["...", "..."],
  participants: ["Sarah", "Marcus"]
}
```

---

## 6. Workflow

**Plik**: `/components/Workflow.tsx`

### Cel
Zarządzanie procesem badawczym jako workflow z automatyzacją.

### Funkcje UNIKALNE dla Workflow
- ✅ **Process Validation**: Pre-flight checks przed uruchomieniem
- ✅ **Automated Execution**: Sequential task execution
- ✅ **Auto-Layout**: Automatic workflow graph layout
- ✅ **Template Library**: Pre-built research workflow templates
- ✅ **Integration Points**: Connections between projects, personas, surveys, focus groups

### Główne Komponenty

#### Workflow Canvas
**Based on ReactFlow:**
- Visual node-based workflow editor
- Drag & drop nodes
- Connection lines (edges)
- Zoom & pan controls

**Node Types:**
1. **Start**: Entry point
2. **Create Project**: Setup research project
3. **Generate Personas**: Create AI personas
4. **Create Survey**: Design survey
5. **Run Focus Group**: Conduct focus group
6. **Analyze Results**: Data analysis
7. **Decision**: Conditional branching
8. **End**: Completion

**Node Structure:**
```tsx
<div className="workflow-node">
  <div className="node-header">
    <Icon />
    <span>{nodeType}</span>
  </div>
  <div className="node-body">
    {/* Configuration */}
  </div>
  <Handle type="source" position="bottom" />
  <Handle type="target" position="top" />
</div>
```

#### Workflow Templates
- **Basic Research**: Project → Personas → Survey → Analysis
- **Deep Dive**: Project → Personas → Survey → Focus Group → Analysis
- **Iterative**: Loop z decision points
- **Custom**: Build from scratch

#### Validation Panel
**Pre-flight Checks:**
- [ ] Project configured
- [ ] Personas generated (min 5)
- [ ] Survey questions added (min 3)
- [ ] Logic validated
- [ ] No disconnected nodes

#### Execution Panel
**Progress Tracking:**
```tsx
<div className="execution-timeline">
  {steps.map(step => (
    <div className={step.status}>
      <Check /> {step.name}
      <span>{step.duration}</span>
    </div>
  ))}
</div>
```

**Status Indicators:**
- ⏳ Pending
- ▶️ Running
- ✅ Completed
- ❌ Failed

#### Auto-Layout
Automatic node positioning algorithms:
- **Hierarchical**: Top-to-bottom flow
- **Force-directed**: Physics-based spacing
- **Grid**: Aligned grid layout

---

## Panel Relationship Matrix

| Panel | Projects | Personas | Surveys | Focus Groups | Workflow |
|-------|----------|----------|---------|--------------|----------|
| **Dashboard** | Quick create | Quick create | Quick create | Quick create | View templates |
| **Projects** | - | Select for project | Link to project | Link to project | Create workflow |
| **Personas** | Filter by project | - | Use in survey | Use in focus group | Generate step |
| **Surveys** | Filter by project | Test with personas | - | - | Survey step |
| **Focus Groups** | Filter by project | Select participants | - | - | Focus group step |
| **Workflow** | Create project node | Generate personas node | Create survey node | Run FG node | - |

---

## Wspólne Wzorce

Wszystkie panele dzielą:
- Maksymalna szerokość: `max-w-[1920px]`
- Padding: `px-8`
- Header z h1 + description
- Responsywny grid layout
- Consistent card styling
- Toast notifications dla akcji
- Loading states (Skeleton)
- Empty states z ilustracjami
- Error handling

---

## Navigation Flow

```
Dashboard → Quick Action
  ├─ Create Project → Projects → ProjectDetail
  ├─ Create Persona → Personas → PersonaGenerationWizard
  ├─ Create Survey → Surveys → SurveyBuilder
  └─ Create Focus Group → FocusGroups → FocusGroupBuilder

Projects → ProjectDetail
  └─ Related Personas/Surveys/Focus Groups

Personas → PersonaDetailsDrawer
  └─ Behavior Simulation Dialog

Surveys → SurveyBuilder → SurveyResults

Focus Groups → FocusGroupBuilder → FocusGroup (Session) → ResultsAnalysis

Workflow → Template Selection → Canvas → Execution
```
