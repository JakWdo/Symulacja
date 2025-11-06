# Modele Danych - Sight

Wszystkie struktury danych używane w aplikacji. Obecnie są to mocki, ale struktury są przygotowane dla przyszłej integracji z backendem.

---

## Core Models

### Project
```typescript
interface Project {
  id: number;
  name: string;
  description: string;
  status: "planning" | "active" | "on-hold" | "completed";
  type: "qualitative" | "quantitative" | "mixed";
  startDate: string; // ISO date
  endDate: string; // ISO date
  budget: {
    total: number;
    allocated: number;
    spent: number;
    remaining: number;
    breakdown: {
      personnel: number;
      software: number;
      incentives: number;
      other: number;
    };
  };
  timeline: {
    milestones: Milestone[];
    currentPhase: string;
    completionPercentage: number;
  };
  team: TeamMember[];
  roi: {
    expectedValue: number;
    actualValue: number;
    timeToInsight: number; // days
    costPerInsight: number;
  };
  risks: Risk[];
  createdAt: string;
  updatedAt: string;
  createdBy: number; // user ID
}
```

### Milestone
```typescript
interface Milestone {
  id: string;
  name: string;
  description: string;
  dueDate: string;
  status: "pending" | "in-progress" | "completed" | "delayed";
  dependencies: string[]; // milestone IDs
  assignedTo: number[]; // user IDs
  completedAt?: string;
}
```

### TeamMember
```typescript
interface TeamMember {
  id: number;
  name: string;
  email: string;
  role: "lead" | "researcher" | "analyst" | "stakeholder";
  permissions: {
    canEdit: boolean;
    canDelete: boolean;
    canInvite: boolean;
    canViewBudget: boolean;
  };
  joinedAt: string;
  activityScore: number; // 0-100
}
```

### Risk
```typescript
interface Risk {
  id: string;
  title: string;
  description: string;
  probability: "low" | "medium" | "high";
  impact: "low" | "medium" | "high";
  status: "identified" | "monitoring" | "mitigated" | "realized";
  mitigation: string;
  owner: number; // user ID
  identifiedAt: string;
  lastReviewedAt: string;
}
```

---

## Persona Models

### Persona
```typescript
interface Persona {
  id: number;
  name: string;
  age: number;
  occupation: string;
  
  // Basic Info
  interests: string[];
  background: string;
  
  // Demographics
  demographics: {
    gender: string;
    location: string;
    income: string;
    education: string;
    maritalStatus?: string;
    householdSize?: number;
  };
  
  // Psychographics
  psychographics: {
    personality: string[]; // Big 5 traits
    values: string[];
    lifestyle: string;
    motivations?: string[];
  };
  
  // Behavior Profiles
  behaviorProfiles?: {
    techSavviness: number; // 0-10
    brandLoyalty: number; // 0-10
    priceSensitivity: number; // 0-10
    riskTolerance: number; // 0-10
  };
  
  // Segment Information
  segment?: SegmentData;
  
  // Jobs to be Done
  jobsToBeDone?: JobToBeDone[];
  
  // Pain Points
  painPoints?: PainPoint[];
  
  // Desired Outcomes
  desiredOutcomes?: DesiredOutcome[];
  
  // Meta
  createdAt: string;
  projectId: number;
  generationConfig?: PersonaConfig; // Config used to generate
}
```

### SegmentData
```typescript
interface SegmentData {
  name: string; // e.g., "Early Adopters"
  description: string;
  size: number; // percentage of market
  characteristics: string[];
  insights?: SegmentInsight[];
}
```

### SegmentInsight
```typescript
interface SegmentInsight {
  id: string;
  category: "behavior" | "preference" | "challenge" | "opportunity";
  insight: string;
  confidence: number; // 0-100
  supportingData?: string;
}
```

### JobToBeDone
```typescript
interface JobToBeDone {
  id: string;
  job: string; // "When [situation], I want to [motivation], so I can [outcome]"
  context: string;
  successMetrics: string[];
  currentSolution: string;
  satisfactionWithCurrent: number; // 0-100
  importance: "low" | "medium" | "high";
  userQuote: string;
}
```

### PainPoint
```typescript
interface PainPoint {
  id: string;
  title: string;
  description: string;
  severity: "low" | "medium" | "high";
  frequency: "rare" | "occasional" | "frequent" | "constant";
  category: "functional" | "emotional" | "social" | "financial";
  userQuote: string;
  relatedJobs?: string[]; // JTBD IDs
}
```

### DesiredOutcome
```typescript
interface DesiredOutcome {
  id: string;
  outcome: string;
  priority: "low" | "medium" | "high";
  currentSatisfactionLevel: number; // 0-100
  importanceScore: number; // 0-100
  opportunityScore?: number; // Importance - Satisfaction
  userQuote: string;
  relatedJobs?: string[]; // JTBD IDs
}
```

### PersonaConfig
```typescript
interface PersonaConfig {
  // Basic Setup
  personaCount: number;
  adversarialMode: boolean;
  demographicPreset: string;
  
  // Demographics
  ageGroups: Record<string, [number]>; // e.g., { "18-24": [20], "25-34": [30] }
  genderDistribution: Record<string, [number]>;
  educationLevels: Record<string, [number]>;
  incomeBrackets: Record<string, [number]>;
  
  // Geography
  locationDistribution: { city: string; weight: number }[];
  targetCities: string;
  urbanicity: "urban" | "suburban" | "rural" | "mixed";
  
  // Psychographics
  requiredValues: string[];
  excludedValues: string[];
  requiredInterests: string[];
  excludedInterests: string[];
  
  // Advanced
  targetIndustries: string[];
  personalitySkew: Record<string, [number]>; // Big 5
}
```

---

## Survey Models

### Survey
```typescript
interface Survey {
  id: number;
  title: string;
  description: string;
  projectId: number;
  
  // Configuration
  questions: Question[];
  logic: SkipLogic[];
  settings: SurveySettings;
  
  // Status
  status: "draft" | "active" | "paused" | "closed";
  
  // Metrics
  responseCount: number;
  completionRate: number; // percentage
  averageTimeToComplete: number; // seconds
  
  // Dates
  createdAt: string;
  publishedAt?: string;
  closedAt?: string;
}
```

### Question
```typescript
interface Question {
  id: string;
  type: QuestionType;
  text: string;
  description?: string;
  required: boolean;
  
  // Type-specific options
  options?: string[]; // For multiple choice
  min?: number; // For rating, slider
  max?: number;
  step?: number; // For slider
  rows?: string[]; // For matrix
  columns?: string[]; // For matrix
  
  // Validation
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string; // regex
    customError?: string;
  };
  
  // Attention check
  isAttentionCheck?: boolean;
  correctAnswer?: string | string[];
}

type QuestionType = 
  | "multiple-choice-single"
  | "multiple-choice-multiple"
  | "text-short"
  | "text-long"
  | "rating-scale"
  | "nps"
  | "matrix"
  | "ranking"
  | "slider"
  | "date"
  | "time";
```

### SkipLogic
```typescript
interface SkipLogic {
  id: string;
  questionId: string;
  conditions: LogicCondition[];
  action: LogicAction;
}

interface LogicCondition {
  field: string; // question ID
  operator: "equals" | "not-equals" | "contains" | "greater-than" | "less-than";
  value: any;
  connector?: "AND" | "OR"; // For multiple conditions
}

interface LogicAction {
  type: "jump" | "show" | "hide" | "end";
  target?: string; // question ID or page ID
}
```

### SurveySettings
```typescript
interface SurveySettings {
  allowAnonymous: boolean;
  oneResponsePerUser: boolean;
  shuffleQuestions: boolean;
  showProgressBar: boolean;
  thankYouMessage: string;
  redirectUrl?: string;
  
  // Quality Control
  speedThreshold: number; // minimum seconds per question
  flagStraightLiners: boolean;
  requireAttentionChecks: boolean;
}
```

### SurveyResponse
```typescript
interface SurveyResponse {
  id: number;
  surveyId: number;
  respondentId?: number; // If not anonymous
  
  answers: Answer[];
  
  // Metadata
  startedAt: string;
  completedAt?: string;
  timeToComplete?: number; // seconds
  
  // Quality Flags
  qualityFlags: {
    isSpeeder: boolean; // Completed too fast
    isStraightLiner: boolean; // Same answer repeated
    failedAttentionCheck: boolean;
  };
  
  // Device Info
  device: {
    type: "desktop" | "tablet" | "mobile";
    os: string;
    browser: string;
  };
}
```

### Answer
```typescript
interface Answer {
  questionId: string;
  value: any; // string, number, string[], etc.
  timeSpent: number; // seconds on this question
}
```

### SurveyResults
```typescript
interface SurveyResults {
  surveyId: number;
  
  // Summary
  summary: {
    totalResponses: number;
    completedResponses: number;
    completionRate: number;
    averageTime: number;
    medianTime: number;
  };
  
  // Per Question
  questionResults: QuestionResult[];
  
  // NPS (if applicable)
  nps?: {
    score: number; // -100 to 100
    promoters: number;
    passives: number;
    detractors: number;
    breakdown: { score: number; count: number }[]; // 0-10
  };
  
  // Cross-tabs
  crossTabs?: CrossTabulation[];
  
  // Quality
  quality: {
    speeders: number;
    straightLiners: number;
    attentionCheckFails: number;
    validResponses: number;
  };
}
```

### QuestionResult
```typescript
interface QuestionResult {
  questionId: string;
  questionText: string;
  questionType: QuestionType;
  
  // Statistics
  responseCount: number;
  skipCount: number;
  
  // Type-specific results
  frequencies?: { value: string; count: number; percentage: number }[];
  mean?: number;
  median?: number;
  mode?: string | number;
  standardDeviation?: number;
  
  // Text responses
  textResponses?: string[];
  
  // Sentiment (for text questions)
  sentiment?: {
    positive: number;
    neutral: number;
    negative: number;
  };
}
```

### CrossTabulation
```typescript
interface CrossTabulation {
  id: string;
  question1Id: string;
  question2Id: string;
  data: {
    row: string;
    column: string;
    count: number;
    percentage: number;
  }[];
}
```

---

## Focus Group Models

### FocusGroup
```typescript
interface FocusGroup {
  id: number;
  title: string;
  description: string;
  projectId: number;
  
  // Configuration
  participantIds: number[]; // Persona IDs
  topics: string[];
  duration: number; // minutes
  moderationStyle: "minimal" | "moderate" | "active";
  autoProbing: boolean;
  
  // Session
  status: "planning" | "in-progress" | "completed";
  startedAt?: string;
  completedAt?: string;
  messages: Message[];
  
  // Results
  results?: FocusGroupResults;
  
  createdAt: string;
}
```

### Message
```typescript
interface Message {
  id: string;
  focusGroupId: number;
  
  // Sender
  personaId?: number; // null if moderator
  personaName?: string;
  isModerator: boolean;
  
  // Content
  text: string;
  timestamp: string;
  
  // Analysis
  sentiment: "positive" | "neutral" | "negative";
  emotionalTone?: string; // excited, frustrated, curious, etc.
  
  // Metadata
  isProbe?: boolean; // AI-generated probing question
  replyTo?: string; // message ID
}
```

### FocusGroupResults
```typescript
interface FocusGroupResults {
  focusGroupId: number;
  
  // AI Summary
  summary: {
    overview: string;
    keyInsights: string[];
    recommendations: string[];
    unexpectedFindings: string[];
  };
  
  // Themes
  themes: Theme[];
  
  // Notable Quotes
  quotes: Quote[];
  
  // Sentiment Analysis
  sentimentOverTime: {
    timestamp: string;
    overall: number; // -1 to 1
    byParticipant: { personaId: number; sentiment: number }[];
  }[];
  
  // Participation
  participation: {
    personaId: number;
    personaName: string;
    messageCount: number;
    wordCount: number;
    engagementScore: number; // 0-100
  }[];
  
  // Interaction Patterns
  interactions: {
    agreements: number;
    disagreements: number;
    buildingOnIdeas: number;
    askingQuestions: number;
  };
}
```

### Theme
```typescript
interface Theme {
  id: string;
  name: string;
  description: string;
  mentions: number;
  sentiment: "positive" | "neutral" | "negative" | "mixed";
  
  // Supporting Data
  keyQuotes: string[];
  participants: number[]; // persona IDs
  relatedTopics: string[];
  
  // Analysis
  importance: "low" | "medium" | "high";
  consensus: number; // 0-100, how much agreement
}
```

### Quote
```typescript
interface Quote {
  id: string;
  messageId: string;
  personaId: number;
  personaName: string;
  text: string;
  context: string; // What was being discussed
  significance: string; // Why this quote matters
  relatedThemes: string[]; // theme IDs
}
```

---

## Workflow Models

### Workflow
```typescript
interface Workflow {
  id: number;
  name: string;
  description: string;
  projectId?: number;
  
  // Graph
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  
  // Template
  isTemplate: boolean;
  templateCategory?: string;
  
  // Execution
  status: "draft" | "validated" | "running" | "completed" | "failed";
  currentNodeId?: string;
  
  // Results
  executionHistory: WorkflowExecution[];
  
  createdAt: string;
  updatedAt: string;
}
```

### WorkflowNode
```typescript
interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  position: { x: number; y: number };
  
  // Configuration
  label: string;
  config: NodeConfig;
  
  // Execution
  status?: "pending" | "running" | "completed" | "failed" | "skipped";
  result?: any;
  error?: string;
}

type WorkflowNodeType = 
  | "start"
  | "end"
  | "create-project"
  | "generate-personas"
  | "create-survey"
  | "run-focus-group"
  | "analyze-results"
  | "decision"
  | "delay"
  | "notification";
```

### NodeConfig
```typescript
type NodeConfig = 
  | CreateProjectConfig
  | GeneratePersonasConfig
  | CreateSurveyConfig
  | RunFocusGroupConfig
  | DecisionConfig
  | DelayConfig;

interface CreateProjectConfig {
  name: string;
  type: string;
  budget?: number;
}

interface GeneratePersonasConfig {
  count: number;
  config: PersonaConfig;
}

interface CreateSurveyConfig {
  title: string;
  templateId?: string;
}

interface RunFocusGroupConfig {
  duration: number;
  topics: string[];
  personaCount: number;
}

interface DecisionConfig {
  condition: string; // JavaScript expression
  trueTarget: string; // node ID
  falseTarget: string; // node ID
}

interface DelayConfig {
  duration: number; // minutes
  unit: "minutes" | "hours" | "days";
}
```

### WorkflowEdge
```typescript
interface WorkflowEdge {
  id: string;
  source: string; // node ID
  target: string; // node ID
  type?: "default" | "conditional";
  label?: string;
  
  // For conditional edges
  condition?: string;
}
```

### WorkflowExecution
```typescript
interface WorkflowExecution {
  id: number;
  workflowId: number;
  
  startedAt: string;
  completedAt?: string;
  status: "running" | "completed" | "failed";
  
  // Node executions
  nodeExecutions: {
    nodeId: string;
    startedAt: string;
    completedAt?: string;
    status: "pending" | "running" | "completed" | "failed";
    duration?: number; // seconds
    result?: any;
    error?: string;
  }[];
  
  // Overall stats
  totalDuration?: number; // seconds
  failureReason?: string;
}
```

---

## Activity & Analytics

### Activity
```typescript
interface Activity {
  id: number;
  type: "create" | "update" | "delete" | "complete" | "comment";
  entityType: "project" | "persona" | "survey" | "focus-group" | "workflow";
  entityId: number;
  entityName: string;
  
  description: string; // "Created project 'Mobile App Research'"
  
  userId: number;
  userName: string;
  
  timestamp: string;
  
  metadata?: {
    changes?: any;
    previousValue?: any;
    newValue?: any;
  };
}
```

### Analytics
```typescript
interface Analytics {
  // Overview
  totalProjects: number;
  activeProjects: number;
  totalPersonas: number;
  totalSurveys: number;
  totalFocusGroups: number;
  
  // Trends
  projectsOverTime: { date: string; count: number }[];
  personasOverTime: { date: string; count: number }[];
  
  // Performance
  averageProjectDuration: number; // days
  averageSurveyResponseRate: number; // percentage
  averageFocusGroupParticipation: number; // percentage
  
  // ROI
  totalBudgetAllocated: number;
  totalBudgetSpent: number;
  averageROI: number;
  
  // User Engagement
  activeUsers: number;
  totalActivities: number;
  activitiesPerDay: number;
}
```

---

## User Models (Future)

### User
```typescript
interface User {
  id: number;
  email: string;
  name: string;
  avatar?: string;
  
  // Organization
  organizationId: number;
  role: "admin" | "manager" | "researcher" | "viewer";
  
  // Preferences
  preferences: {
    theme: "light" | "dark" | "system";
    notifications: {
      email: boolean;
      inApp: boolean;
    };
    defaultView: string;
  };
  
  // Meta
  createdAt: string;
  lastLoginAt: string;
  isActive: boolean;
}
```

### Organization
```typescript
interface Organization {
  id: number;
  name: string;
  plan: "free" | "pro" | "enterprise";
  
  // Limits (based on plan)
  limits: {
    maxProjects: number;
    maxPersonas: number;
    maxSurveys: number;
    maxFocusGroups: number;
  };
  
  // Usage
  usage: {
    projects: number;
    personas: number;
    surveys: number;
    focusGroups: number;
  };
  
  createdAt: string;
}
```

---

## Mock Data Patterns

### Creating Mock Data
```typescript
// Example: Mock Projects
const mockProjects: Project[] = [
  {
    id: 1,
    name: "Mobile App Launch Research",
    description: "Research for new mobile application targeting millennials",
    status: "active",
    type: "mixed",
    startDate: "2024-01-01",
    endDate: "2024-06-30",
    budget: {
      total: 50000,
      allocated: 50000,
      spent: 23500,
      remaining: 26500,
      breakdown: {
        personnel: 25000,
        software: 10000,
        incentives: 12000,
        other: 3000
      }
    },
    // ... rest of fields
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-15T10:30:00Z",
    createdBy: 1
  },
  // ... more projects
];
```

### Data Generation Helpers
```typescript
// Generate ID
const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// Generate date
const generateDate = (daysAgo: number = 0): string => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString();
};

// Generate random in range
const randomInRange = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};
```

---

## API Response Formats (Future)

### Success Response
```typescript
interface APIResponse<T> {
  success: true;
  data: T;
  meta?: {
    page?: number;
    totalPages?: number;
    totalCount?: number;
  };
}
```

### Error Response
```typescript
interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
```

### Pagination
```typescript
interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    totalCount: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}
```
