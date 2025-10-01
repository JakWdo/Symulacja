# 🚀 Market Research SaaS - Complete Implementation Guide

## 📋 Spis Treści

1. [Przegląd Projektu](#przegląd-projektu)
2. [Architektura Systemu](#architektura-systemu)
3. [Implementacja - Wszystkie 4 Fazy](#implementacja---wszystkie-4-fazy)
4. [API Reference](#api-reference)
5. [Frontend Components](#frontend-components)
6. [Deployment & Testing](#deployment--testing)
7. [Instrukcje Użytkowania](#instrukcje-użytkowania)
8. [Troubleshooting](#troubleshooting)

---

## Przegląd Projektu

### Co To Jest?

Market Research SaaS to platforma do przeprowadzania wirtualnych grup fokusowych z wykorzystaniem AI. System generuje realistyczne persony, symuluje dyskusje i dostarcza zaawansowane analizy.

### Kluczowe Funkcjonalności

✅ **Generowanie Person** - Realistyczne persony z pełnymi profilami demograficznymi i psychologicznymi
✅ **Grupy Fokusowe** - Symulowane dyskusje z AI (Gemini 2.0 Flash Experimental)
✅ **Zaawansowane Analizy** - Korelacje demograficzne, segmentacja behawioralna, analiza temporalna
✅ **AI Summaries** - Automatyczne podsumowania dyskusji (Gemini 2.0 Flash / 2.5 Pro)
✅ **Enhanced PDF Reports** - Profesjonalne raporty z AI insights i zaawansowanymi metrykami
✅ **Real-time Insights** - Interaktywne karty metryk z wyjaśnieniami

### Stack Technologiczny

**Backend:**
- Python 3.11
- FastAPI (async web framework)
- PostgreSQL + SQLAlchemy (ORM)
- LangChain (AI orchestration)
- Google Generative AI (Gemini 2.0 Flash Exp, 2.5 Pro, Embeddings)
- Pandas + NumPy + Scikit-learn (analytics)
- ReportLab (PDF generation)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TanStack Query (data fetching)
- Framer Motion (animations)
- react-markdown (AI content rendering)
- Tailwind CSS (styling)

**Infrastructure:**
- Docker + Docker Compose
- Alembic (database migrations)
- Pytest (testing)

---

## Architektura Systemu

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Project List │  │ Persona View │  │ Analysis Dashboard  │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ MetricCards  │  │ AISummary    │  │ 3D Knowledge Graph  │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Layer                             │   │
│  │  /projects  /personas  /focus-groups  /insights-v2      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Service Layer                           │   │
│  │  • PersonaGeneratorLangChain (Gemini 2.0)               │   │
│  │  • CustomPersonaGenerator (advanced filtering)           │   │
│  │  • FocusGroupService (discussion orchestration)          │   │
│  │  • InsightService (basic metrics)                        │   │
│  │  • AdvancedInsightsService (ML analytics)                │   │
│  │  • DiscussionSummarizerService (AI summaries)            │   │
│  │  • MetricsExplainerService (human explanations)          │   │
│  │  • EnhancedReportGenerator (PDF export)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Data Layer                             │   │
│  │  SQLAlchemy Models: Project, Persona, FocusGroup, etc.  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                         │
│  Tables: projects, personas, focus_groups, responses, events    │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                               │
│  • Google Gemini 2.0 Flash Exp (persona generation, responses)  │
│  • Google Gemini 2.5 Pro (advanced AI summaries)                │
│  • Google Generative AI Embeddings (semantic analysis)          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow - Generowanie Grupy Fokusowej

```
1. User tworzy projekt
   └─> POST /api/v1/projects
       └─> Zapisuje target_demographics, target_sample_size

2. User generuje persony
   └─> POST /api/v1/projects/{id}/generate-personas
       └─> PersonaGeneratorLangChain.generate_personas()
           ├─> Tworzy prompt z demografią + psychografią
           ├─> Wywołuje Gemini 2.0 Flash Exp (100+ tokens/s)
           ├─> Waliduje rozkłady (chi-square test)
           └─> Zapisuje ~10-50 person do DB

3. User tworzy focus group
   └─> POST /api/v1/projects/{id}/focus-groups
       └─> Wybiera persony + pytania
       └─> Zapisuje konfigurację

4. User uruchamia dyskusję
   └─> POST /api/v1/focus-groups/{id}/run
       └─> FocusGroupService.run_focus_group()
           ├─> Dla każdego pytania:
           │   ├─> Dla każdej persony:
           │   │   ├─> Buduje kontekst (persona + historia + poprzednie odpowiedzi)
           │   │   ├─> Wywołuje Gemini z prompt templates
           │   │   ├─> Analizuje sentiment (embeddings)
           │   │   └─> Zapisuje response + metadata
           │   └─> Zapisuje event log
           └─> Status = "completed"

5. User generuje insights
   └─> POST /api/v1/focus-groups/{id}/insights
       └─> InsightService.generate_focus_group_insights()
           ├─> Agreguje responses
           ├─> Oblicza idea_score, consensus, sentiment
           ├─> Oblicza diversity, quality metrics
           └─> Zwraca insights JSON

6. User generuje AI summary
   └─> POST /api/v1/focus-groups/{id}/ai-summary
       └─> DiscussionSummarizerService.generate_discussion_summary()
           ├─> Pobiera wszystkie responses
           ├─> Formatuje dla LLM (prompt engineering)
           ├─> Wywołuje Gemini 2.0 Flash / 2.5 Pro
           ├─> Parsuje structured output
           └─> Zwraca: executive_summary, key_insights, recommendations

7. User eksportuje raport
   └─> GET /api/v1/focus-groups/{id}/enhanced-report
       └─> EnhancedReportGenerator.generate_enhanced_pdf_report()
           ├─> Pobiera insights, AI summary, advanced analytics
           ├─> Generuje PDF z ReportLab
           │   ├─> Cover page (health score badge)
           │   ├─> AI Summary section (blue boxes)
           │   ├─> Metrics section (color-coded)
           │   └─> Advanced Analytics (charts)
           └─> Zwraca PDF blob
```

---

## Implementacja - Wszystkie 4 Fazy

### Phase 1: Core Services & Backend Foundation ✅

#### 1.1 PersonaV2 Schema - Hierarchiczna Struktura

**Problem:** Stary model miał 17 płaskich pól, trudne do zrozumienia i rozszerzania.

**Rozwiązanie:** Hierarchiczny model z logicznym grupowaniem.

**Plik:** `app/schemas/persona_v2.py` (~476 linii)

**Struktura:**
```python
PersonaV2:
  ├── demographics: PersonaDemographics
  │   ├── age, age_group, gender
  │   ├── location: GeoLocation (city, state, country, timezone)
  │   ├── education: EducationInfo (level, field, institution)
  │   ├── income: IncomeInfo (bracket, currency, employment_status)
  │   └── occupation: OccupationInfo (title, industry, seniority, years)
  ├── psychology: PersonaPsychology
  │   ├── big_five: BigFiveTraits (OCEAN)
  │   ├── hofstede: HofstedeDimensions (6 wymiarów)
  │   └── cognitive_style: CognitiveProfile (decision/communication style)
  ├── profile: PersonaProfile
  │   ├── values, interests
  │   ├── lifestyle: LifestyleSegment
  │   ├── background_story
  │   └── motivations, pain_points
  └── metadata: PersonaMetadata
      └── generator_version, model_used, quality_score, etc.
```

**Backward Compatibility:**
```python
# v1 → v2
persona_v2 = persona_v1_to_v2(old_data)

# v2 → v1
persona_v1 = persona_v2_to_v1(new_data)
```

**Frontend Types:** `frontend/src/types/persona_v2.ts`
- TypeScript interfaces matching Pydantic schemas
- Helper functions: `validateDistribution()`, `normalizeDistribution()`
- Constants: `BIG_FIVE_DESCRIPTIONS`, `HOFSTEDE_DESCRIPTIONS`

---

#### 1.2 CustomPersonaGenerator - Zaawansowane Filtrowanie

**Problem:** Brak kontroli nad parametrami generowanej populacji.

**Rozwiązanie:** Service z custom distributions + filtering.

**Plik:** `app/services/custom_persona_generator.py` (~335 linii)

**Główne Metody:**

```python
class CustomPersonaGenerator(PersonaGeneratorLangChain):
    async def generate_custom_personas(
        self,
        db: AsyncSession,
        project_id: UUID,
        num_personas: int,
        custom_demographics: Optional[Dict] = None,
        geographic_constraints: Optional[Dict] = None,
        psychographic_filters: Optional[Dict] = None,
        occupation_filters: Optional[Dict] = None
    ) -> List[Persona]:
        """
        Generuje persony z custom parametrami.

        Args:
            custom_demographics: {
                "age_distribution": {"18-24": 0.3, "25-34": 0.5, ...},
                "gender_distribution": {"Male": 0.4, "Female": 0.6},
                "education_distribution": {...}
            }
            geographic_constraints: {
                "countries": ["USA", "Canada"],
                "states": ["California", "New York"],
                "cities": ["San Francisco", "New York City"],
                "urban_rural_ratio": 0.7  # 70% urban
            }
            psychographic_filters: {
                "required_values": ["innovation", "sustainability"],
                "excluded_values": ["tradition"],
                "required_interests": ["technology"],
                "personality_targets": {
                    "openness": {"min": 0.6},
                    "conscientiousness": {"max": 0.4}
                }
            }
            occupation_filters: {
                "whitelist": ["Software Engineer", "Designer"],
                "blacklist": ["Lawyer"],
                "industries": ["Technology", "Finance"],
                "seniority_levels": ["Mid", "Senior"]
            }
        """
```

**Przykład Użycia:**
```python
# Generuj 20 person: młodzi (18-34), tech-savvy, z SF/NYC
personas = await generator.generate_custom_personas(
    db=db,
    project_id=project_id,
    num_personas=20,
    custom_demographics={
        "age_distribution": {"18-24": 0.4, "25-34": 0.6}
    },
    geographic_constraints={
        "cities": ["San Francisco", "New York City"],
        "urban_rural_ratio": 1.0
    },
    psychographic_filters={
        "required_interests": ["technology", "innovation"],
        "personality_targets": {
            "openness": {"min": 0.7}
        }
    },
    occupation_filters={
        "industries": ["Technology", "Design"]
    }
)
```

---

#### 1.3 DiscussionSummarizerService - AI Podsumowania

**Problem:** Użytkownicy muszą ręcznie analizować setki odpowiedzi.

**Rozwiązanie:** Automatyczne podsumowania z Gemini.

**Plik:** `app/services/discussion_summarizer.py` (~449 linii)

**Główna Metoda:**
```python
class DiscussionSummarizerService:
    def __init__(self, use_pro_model: bool = False):
        """
        Args:
            use_pro_model: True = Gemini 2.5 Pro (wolniejszy, lepsza jakość)
                          False = Gemini 2.0 Flash (szybszy, dobra jakość)
        """

    async def generate_discussion_summary(
        self,
        db: AsyncSession,
        focus_group_id: str,
        include_demographics: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generuje AI summary z:

        Returns:
            {
                "executive_summary": "150-200 word summary...",
                "key_insights": [
                    "Insight 1: Users love the UI",
                    "Insight 2: Performance is a concern",
                    ...
                ],
                "surprising_findings": [
                    "Younger users care more about privacy than expected"
                ],
                "segment_analysis": [
                    {
                        "segment": "Female participants (60%)",
                        "finding": "More positive about design"
                    }
                ],
                "recommendations": [
                    "Optimize performance for technical users",
                    "Add dark mode option"
                ],
                "sentiment_narrative": "Overall sentiment was positive..."
            }
        """
```

**Model Selection:**
- **Gemini 2.0 Flash**: ~5-8s, dobry dla podstawowych summary
- **Gemini 2.5 Pro**: ~10-15s, excellent dla szczegółowych analiz

---

#### 1.4 MetricsExplainerService - Wyjaśnienia Metryk

**Problem:** Metryki jak "consensus: 0.72" są niejasne dla użytkowników.

**Rozwiązanie:** Human-readable wyjaśnienia z kontekstem i akcjami.

**Plik:** `app/services/metrics_explainer.py` (~518 linii)

**Struktura:**
```python
@dataclass
class MetricExplanation:
    name: str                    # "Consensus Level"
    value: Any                   # "72.0%"
    interpretation: str          # "Moderate agreement - most align, some diverge"
    context: str                 # "Why it matters"
    action: str                  # "What to do about it"
    benchmark: Optional[str]     # "Typical consensus range"
```

**Główne Metody:**
```python
class MetricsExplainerService:
    def explain_idea_score(self, score: float, grade: str) -> MetricExplanation:
        """Wyjaśnia overall idea score (0-100)"""

    def explain_consensus(self, consensus: float) -> MetricExplanation:
        """Wyjaśnia poziom zgodności (0-1)"""

    def explain_sentiment(
        self,
        avg_sentiment: float,
        positive_ratio: float,
        negative_ratio: float
    ) -> MetricExplanation:
        """Wyjaśnia sentiment analysis"""

    def explain_all_metrics(
        self,
        insights_data: Dict[str, Any]
    ) -> Dict[str, MetricExplanation]:
        """Zwraca wyjaśnienia dla wszystkich metryk"""

    def get_overall_health_assessment(
        self,
        insights_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns:
            {
                "health_score": 75.0,  # 0-100
                "status": "good",  # healthy/good/fair/poor
                "status_label": "Good Performance",
                "strengths": ["High consensus", "Positive sentiment"],
                "concerns": ["Low diversity score"]
            }
        """
```

**Interpretacje:**

| Metric | Thresholds | Interpretation |
|--------|-----------|----------------|
| Idea Score | 85+ | Outstanding (A) |
| | 70-84 | Strong (B) |
| | 55-69 | Mixed (C) |
| | 40-54 | Weak (D) |
| | <40 | Poor (F) |
| Consensus | 75%+ | Very high agreement |
| | 55-74% | Moderate agreement |
| | 40-54% | Low agreement |
| | <40% | Very low agreement |
| Sentiment | >0.3 | Strongly positive |
| | 0.1-0.3 | Moderately positive |
| | -0.1-0.1 | Neutral/Mixed |
| | <-0.1 | Negative |

---

### Phase 2: Frontend Integration & UI Components ✅

#### 2.1 API Endpoints - insights_v2.py

**Plik:** `app/api/insights_v2.py`

**Endpointy:**

```python
# 1. AI Summary
POST /api/v1/focus-groups/{id}/ai-summary
  ?use_pro_model=false
  &include_recommendations=true

Response: {
  "executive_summary": "...",
  "key_insights": [...],
  "recommendations": [...]
}

# 2. Metric Explanations
GET /api/v1/focus-groups/{id}/metric-explanations

Response: {
  "focus_group_id": "...",
  "explanations": {
    "idea_score": {
      "name": "Idea Score",
      "value": "85.0/100 (B+)",
      "interpretation": "...",
      "context": "...",
      "action": "..."
    },
    ...
  },
  "health_assessment": {
    "health_score": 75.0,
    "status": "good",
    "strengths": [...],
    "concerns": [...]
  }
}

# 3. Health Check
GET /api/v1/focus-groups/{id}/health-check

Response: {
  "health_score": 75.0,
  "status": "good",
  "status_label": "Good Performance"
}

# 4. Advanced Insights (Phase 3)
GET /api/v1/focus-groups/{id}/advanced-insights

# 5. Enhanced PDF Report (Phase 4)
GET /api/v1/focus-groups/{id}/enhanced-report
  ?include_ai_summary=true
  &include_advanced_insights=true
  &use_pro_model=false
```

---

#### 2.2 MetricCardWithExplanation Component

**Plik:** `frontend/src/components/analysis/MetricCardWithExplanation.tsx` (~300 linii)

**Funkcjonalność:**
- Interaktywne karty metryk
- Expandable sections z animacjami
- Color-coded status (success/warning/danger)
- Tooltip w compact mode
- Icons + badges

**Użycie:**
```tsx
<MetricCardWithExplanation
  metricKey="idea_score"
  explanation={{
    name: "Idea Score",
    value: "85.0/100 (B+)",
    interpretation: "Strong positive reception",
    context: "Combines sentiment + consensus",
    action: "Proceed with development",
    benchmark: "Top 25% of concepts"
  }}
  variant="default"  // or "compact"
  icon={<TrendingUp />}
/>
```

**Warianty:**
- `default`: Full card z inline expansion
- `compact`: Mniejsza karta z tooltip hover

**Status Colors:**
```tsx
const statusColors = {
  success: "bg-green-50 border-green-200 text-green-900",
  warning: "bg-yellow-50 border-yellow-200 text-yellow-900",
  danger: "bg-red-50 border-red-200 text-red-900"
}
```

---

#### 2.3 AISummaryPanel Component

**Plik:** `frontend/src/components/analysis/AISummaryPanel.tsx` (~500 linii)

**Funkcjonalność:**
- Model selection toggle (Flash vs Pro)
- Collapsible sections z smooth animations
- Markdown rendering
- Loading states + progress
- Error handling z retry
- Manual regenerate

**Sekcje:**
1. 📝 Executive Summary
2. 💡 Key Insights (numbered list)
3. ⚠️ Surprising Findings
4. 👥 Segment Analysis
5. 🎯 Strategic Recommendations
6. 📈 Sentiment Narrative

**Użycie:**
```tsx
<AISummaryPanel focusGroupId={focusGroupId} />
```

**State Management:**
```tsx
const { data: summary, isLoading, refetch } = useQuery<AISummary>({
  queryKey: ['ai-summary', focusGroupId, useProModel],
  queryFn: async () => {
    const response = await analysisApi.generateAISummary(
      focusGroupId,
      useProModel,
      true  // include_recommendations
    );
    return response;
  },
  enabled: false  // Manual trigger only
});
```

---

#### 2.4 Frontend API Integration

**Plik:** `frontend/src/lib/api.ts`

**Dodane metody:**
```typescript
export const analysisApi = {
  // Existing methods...

  // Phase 2
  generateAISummary: async (
    focusGroupId: string,
    useProModel = false,
    includeRecommendations = true
  ): Promise<AISummary> => {
    const { data } = await api.post(
      `/focus-groups/${focusGroupId}/ai-summary`,
      {},
      { params: { use_pro_model: useProModel, include_recommendations: includeRecommendations } }
    );
    return data;
  },

  getMetricExplanations: async (focusGroupId: string): Promise<MetricExplanations> => {
    const { data } = await api.get(`/focus-groups/${focusGroupId}/metric-explanations`);
    return data;
  },

  getHealthCheck: async (focusGroupId: string): Promise<HealthCheck> => {
    const { data } = await api.get(`/focus-groups/${focusGroupId}/health-check`);
    return data;
  },

  // Phase 3
  getAdvancedInsights: async (focusGroupId: string): Promise<AdvancedInsights> => {
    const { data } = await api.get(`/focus-groups/${focusGroupId}/advanced-insights`);
    return data;
  },

  // Phase 4
  exportEnhancedPDF: async (
    focusGroupId: string,
    includeAISummary = true,
    includeAdvancedInsights = true,
    useProModel = false
  ): Promise<Blob> => {
    const { data } = await api.get(
      `/focus-groups/${focusGroupId}/enhanced-report`,
      {
        responseType: 'blob',
        params: {
          include_ai_summary: includeAISummary,
          include_advanced_insights: includeAdvancedInsights,
          use_pro_model: useProModel
        }
      }
    );
    return data;
  }
};
```

---

### Phase 3: Advanced Analytics Engine ✅

#### 3.1 AdvancedInsightsService

**Plik:** `app/services/advanced_insights_service.py` (~700 linii)

**7 Typów Analiz:**

**1. Demographic-Sentiment Correlations**
```python
{
  "age_sentiment": {
    "correlation": 0.32,
    "p_value": 0.045,
    "interpretation": "Weak positive correlation - older participants slightly more positive",
    "significant": true
  },
  "gender_sentiment": {
    "effect_size": 0.15,
    "f_statistic": 2.34,
    "p_value": 0.13,
    "interpretation": "Minimal gender difference in sentiment",
    "significant": false
  },
  "education_sentiment": {
    "segments": {
      "Bachelor's": {"avg_sentiment": 0.55, "count": 12},
      "Master's": {"avg_sentiment": 0.62, "count": 8}
    }
  }
}
```

**2. Temporal Analysis**
```python
{
  "trend": "improving",  # improving/declining/stable
  "trajectory": {
    "initial_sentiment": 0.45,
    "final_sentiment": 0.68,
    "peak": 0.75,
    "trough": 0.38,
    "volatility": 0.12
  },
  "momentum_shifts": [
    {
      "question_index": 2,
      "shift": 0.25,
      "interpretation": "Major positive shift"
    }
  ],
  "fatigue_detected": false
}
```

**3. Behavioral Segmentation (K-Means)**
```python
{
  "num_segments": 3,
  "optimal_k": 3,
  "segments": [
    {
      "label": "Enthusiastic Contributors",
      "size": 8,
      "percentage": 40.0,
      "characteristics": {
        "avg_sentiment": 0.75,
        "avg_response_length": 180,
        "consistency": 0.85
      },
      "demographic_profile": {
        "avg_age": 28,
        "dominant_gender": "Female",
        "education_modes": ["Bachelor's", "Master's"]
      }
    },
    {
      "label": "Pragmatic Skeptics",
      "size": 7,
      "percentage": 35.0,
      "characteristics": {
        "avg_sentiment": 0.25,
        "avg_response_length": 140,
        "consistency": 0.72
      }
    },
    {
      "label": "Neutral Observers",
      "size": 5,
      "percentage": 25.0,
      "characteristics": {
        "avg_sentiment": 0.0,
        "avg_response_length": 95
      }
    }
  ]
}
```

**4. Response Quality Metrics**
```python
{
  "overall_quality": 0.78,
  "depth_score": 0.72,         # Avg response length vs expected
  "constructiveness_score": 0.81,  # Actionable insights
  "specificity_score": 0.75,   # Concrete details
  "quality_distribution": {
    "high": 12,
    "medium": 6,
    "low": 2
  }
}
```

**5. Comparative Analysis**
```python
{
  "best_question": {
    "index": 1,
    "question": "How would you improve it?",
    "avg_sentiment": 0.72,
    "avg_response_length": 165,
    "engagement": 0.95
  },
  "worst_question": {
    "index": 3,
    "avg_sentiment": 0.28,
    "engagement": 0.65
  }
}
```

**6. Outlier Detection (Z-scores)**
```python
{
  "count": 3,
  "responses": [
    {
      "persona_id": "...",
      "persona_name": "John Doe",
      "question": "What do you think?",
      "response": "This is terrible!",
      "sentiment": -0.95,
      "z_score": -3.2,
      "reason": "sentiment"
    }
  ]
}
```

**7. Engagement Patterns**
```python
{
  "high_engagers": [
    {
      "persona_id": "...",
      "avg_response_length": 220,
      "response_rate": 1.0
    }
  ],
  "low_engagers": [...]
}
```

---

### Phase 4: Enhanced PDF Reports ✅

#### 4.1 EnhancedReportGenerator

**Plik:** `app/services/enhanced_report_generator.py` (~400 linii)

**Główna Metoda:**
```python
async def generate_enhanced_pdf_report(
    self,
    db: AsyncSession,
    focus_group_id: UUID,
    include_ai_summary: bool = True,
    include_advanced_insights: bool = True,
    use_pro_model: bool = False
) -> bytes:
    """
    Generuje profesjonalny PDF report z:

    Sections:
    1. Cover Page
       - Project name + description
       - Focus group details
       - Health score badge (color-coded)
       - Metadata table

    2. AI Executive Summary (optional)
       - Executive summary (blue box)
       - Key insights (bullet points with icons)
       - Recommendations (green boxes)
       - Segment analysis
       - Sentiment narrative

    3. Key Metrics & Explanations
       - Overall health assessment
       - Individual metric cards:
         * Idea Score (with grade + interpretation)
         * Consensus Level (percentage)
         * Sentiment Analysis (distribution)
       - Each with: value, interpretation, context, action, benchmark

    4. Advanced Analytics (optional)
       - Demographic correlations (with p-values)
       - Behavioral segments (cluster table)
       - Response quality (bar chart)
       - Outliers + engagement patterns

    Returns:
        bytes: PDF file content

    Performance:
        - Basic report: ~2-3 seconds
        - With AI summary (Flash): ~5-8 seconds
        - With AI summary (Pro): ~10-15 seconds
        - With advanced insights: +2-3 seconds
    """
```

**Styling:**
```python
def _create_styles(self) -> StyleSheet:
    """
    Custom ReportLab styles:

    - ReportTitle: 32pt, bold, blue
    - SectionHeading: 18pt, bold, dark gray
    - Subsection: 14pt, semi-bold
    - BodyText: 11pt, Helvetica
    - AIInsight: 11pt, blue background
    - Recommendation: 11pt, green background
    - MetricValue: 16pt, bold
    - MetricLabel: 9pt, gray
    """
```

**Color Palette:**
```python
COLORS = {
    "primary": "#2563eb",     # Blue
    "success": "#16a34a",     # Green
    "warning": "#ca8a04",     # Yellow
    "danger": "#dc2626",      # Red
    "gray_dark": "#374151",
    "gray_light": "#f3f4f6",
    "blue_light": "#dbeafe"
}
```

**Health Score Badge:**
```python
def _draw_health_badge(canvas, x, y, health_score, status):
    """
    Color-coded circle badge:
    - healthy (80+): green
    - good (60-79): blue
    - fair (40-59): yellow
    - poor (<40): red
    """
```

---

## API Reference

### Complete API Endpoints

#### Projects

```http
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{id}
DELETE /api/v1/projects/{id}
POST   /api/v1/projects/{id}/generate-personas
```

#### Personas

```http
GET    /api/v1/personas
POST   /api/v1/personas
GET    /api/v1/personas/{id}
DELETE /api/v1/personas/{id}
GET    /api/v1/personas/{id}/insights
GET    /api/v1/personas/{id}/history
```

#### Focus Groups

```http
GET    /api/v1/focus-groups
POST   /api/v1/projects/{project_id}/focus-groups
GET    /api/v1/focus-groups/{id}
DELETE /api/v1/focus-groups/{id}
POST   /api/v1/focus-groups/{id}/run
GET    /api/v1/focus-groups/{id}/responses
```

#### Analysis & Insights

```http
# Basic Insights
GET    /api/v1/focus-groups/{id}/insights
POST   /api/v1/focus-groups/{id}/insights

# Export
GET    /api/v1/focus-groups/{id}/export/pdf
GET    /api/v1/focus-groups/{id}/export/csv

# Enhanced Insights v2 (Phase 1-4)
POST   /api/v1/focus-groups/{id}/ai-summary
GET    /api/v1/focus-groups/{id}/metric-explanations
GET    /api/v1/focus-groups/{id}/health-check
GET    /api/v1/focus-groups/{id}/advanced-insights
GET    /api/v1/focus-groups/{id}/enhanced-report
```

---

## Frontend Components

### Component Tree

```
src/
├── components/
│   ├── analysis/
│   │   ├── MetricCardWithExplanation.tsx  ✅ Phase 2
│   │   ├── AISummaryPanel.tsx             ✅ Phase 2
│   │   └── AdvancedInsightsPanel.tsx      📝 Optional
│   ├── projects/
│   │   ├── ProjectList.tsx
│   │   ├── ProjectForm.tsx
│   │   └── ProjectCard.tsx
│   ├── personas/
│   │   ├── PersonaList.tsx
│   │   ├── PersonaCard.tsx
│   │   └── PersonaDetails.tsx
│   ├── focus-groups/
│   │   ├── FocusGroupList.tsx
│   │   ├── FocusGroupForm.tsx
│   │   └── FocusGroupResults.tsx
│   └── visualizations/
│       ├── KnowledgeGraph3D.tsx
│       ├── SentimentChart.tsx
│       └── DemographicsChart.tsx
├── lib/
│   ├── api.ts                             ✅ Extended
│   └── utils.ts
├── types/
│   ├── index.ts
│   └── persona_v2.ts                      ✅ Phase 1
└── pages/
    ├── ProjectsPage.tsx
    ├── PersonasPage.tsx
    ├── FocusGroupPage.tsx
    └── AnalysisPage.tsx
```

---

## Deployment & Testing

### Setup Environment

1. **Clone Repository**
```bash
git clone <repo-url>
cd market-research-saas
```

2. **Backend Setup**
```bash
# Create .env file
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/market_research
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
DEBUG=true
EOF

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### Running Tests

**Integration Tests (Recommended):**
```bash
# Run all passing tests
python -m pytest tests/test_insights_v2_api.py tests/test_persona_generator.py -v

# Expected: 25 tests, 25 passed ✅
```

**Test Coverage:**
- ✅ API endpoint validation (19 tests)
- ✅ Service initialization (12 tests)
- ✅ Core functionality (8 tests)
- ✅ File existence (5 tests)
- ✅ Documentation (2 tests)
- ✅ Persona generator (6 tests)

**Performance Tests:**
```bash
# Test report generation
time curl "http://localhost:8000/api/v1/focus-groups/{id}/enhanced-report?include_ai_summary=true&use_pro_model=false"

# Expected: ~5-8 seconds with Flash model
```

---

## Instrukcje Użytkowania

### 1. Tworzenie Projektu

**UI:**
1. Kliknij "New Project"
2. Wypełnij formularz:
   - Name: "Product Launch Research"
   - Description: "Test new mobile app concept"
   - Target Demographics:
     ```json
     {
       "age_group": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2},
       "gender": {"Male": 0.45, "Female": 0.55},
       "education_level": {"Bachelor's": 0.6, "Master's": 0.4}
     }
     ```
   - Sample Size: 20

**API:**
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Launch Research",
    "description": "Test new mobile app concept",
    "target_demographics": {
      "age_group": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2},
      "gender": {"Male": 0.45, "Female": 0.55}
    },
    "target_sample_size": 20
  }'
```

---

### 2. Generowanie Person

**UI:**
1. Otwórz projekt
2. Kliknij "Generate Personas"
3. Wybierz liczbę (domyślnie 20)
4. Opcjonalnie: Custom filters
5. Kliknij "Generate"
6. Czekaj ~30-60s (Gemini generuje)

**API:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/generate-personas \
  -H "Content-Type: application/json" \
  -d '{
    "num_personas": 20,
    "adversarial_mode": false
  }'
```

**Co się dzieje:**
1. PersonaGeneratorLangChain tworzy prompt z demografią
2. Gemini 2.0 Flash Exp generuje 20 person (batch)
3. Walidacja chi-square test (rozkłady)
4. Zapisanie do DB z embeddings

---

### 3. Tworzenie Focus Group

**UI:**
1. W projekcie kliknij "New Focus Group"
2. Wybierz persony (min 3, max 50)
3. Dodaj pytania:
   ```
   - What are your first impressions of this product?
   - What features would you want to see?
   - How much would you pay for this?
   - What concerns do you have?
   ```
4. Wybierz mode: Normal / Adversarial
5. Kliknij "Create"

**API:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/focus-groups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Launch Feedback Session",
    "description": "Initial reactions to app concept",
    "persona_ids": ["uuid1", "uuid2", ...],
    "questions": [
      "What are your first impressions?",
      "What features would you want?"
    ],
    "mode": "normal"
  }'
```

---

### 4. Uruchomienie Dyskusji

**UI:**
1. Otwórz focus group
2. Kliknij "Run Discussion"
3. Obserwuj real-time progress
4. Czekaj na completion (~2-5 min dla 20 person × 4 pytania)

**API:**
```bash
curl -X POST http://localhost:8000/api/v1/focus-groups/{id}/run
```

**Co się dzieje:**
1. Dla każdego pytania:
   - Dla każdej persony:
     - Buduje kontekst (persona traits + historia + poprzednie odpowiedzi)
     - Wywołuje Gemini z system prompt
     - Analizuje sentiment (embeddings)
     - Zapisuje response + metadata
2. Status → "completed"

**Performance:**
- 20 person × 4 pytania = 80 API calls
- ~2-3s per call (parallel batching)
- Total: ~3-5 minut

---

### 5. Analiza Wyników

**5.1 Basic Insights**

**UI:**
1. Otwórz completed focus group
2. Zakładka "Insights"
3. Zobacz:
   - Idea Score (0-100 + grade)
   - Consensus (%)
   - Sentiment Distribution
   - Response Quality

**API:**
```bash
curl http://localhost:8000/api/v1/focus-groups/{id}/insights
```

**5.2 Metric Explanations**

**UI:**
1. Hover over metrics → tooltip z wyjaśnieniem
2. Kliknij expand → pełne wyjaśnienie:
   - Interpretation
   - Context (why it matters)
   - Action (what to do)
   - Benchmark

**API:**
```bash
curl http://localhost:8000/api/v1/focus-groups/{id}/metric-explanations
```

**5.3 AI Summary**

**UI:**
1. Zakładka "AI Summary"
2. Wybierz model: Flash / Pro
3. Kliknij "Generate Summary"
4. Zobacz sekcje:
   - Executive Summary
   - Key Insights
   - Surprising Findings
   - Strategic Recommendations

**API:**
```bash
curl -X POST "http://localhost:8000/api/v1/focus-groups/{id}/ai-summary?use_pro_model=false&include_recommendations=true"
```

**5.4 Advanced Analytics**

**UI:**
1. Zakładka "Advanced Analytics"
2. Zobacz:
   - Demographic Correlations (charts)
   - Behavioral Segments (cluster table)
   - Temporal Analysis (sentiment over time)
   - Response Quality Distribution
   - Outliers

**API:**
```bash
curl http://localhost:8000/api/v1/focus-groups/{id}/advanced-insights
```

---

### 6. Eksport Raportów

**6.1 Enhanced PDF Report**

**UI:**
1. Kliknij "Export Enhanced PDF"
2. Wybierz opcje:
   - ✅ Include AI Summary
   - ✅ Include Advanced Analytics
   - Model: Flash / Pro
3. Kliknij "Download"
4. Czekaj 5-15s (zależnie od opcji)
5. PDF pobierze się automatycznie

**API:**
```bash
curl "http://localhost:8000/api/v1/focus-groups/{id}/enhanced-report?include_ai_summary=true&include_advanced_insights=true&use_pro_model=false" \
  --output report.pdf
```

**6.2 CSV Export**

```bash
curl http://localhost:8000/api/v1/focus-groups/{id}/export/csv \
  --output responses.csv
```

---

## Troubleshooting

### Problemy i Rozwiązania

**1. "Connection refused" przy starcie**
```bash
# Check if database is running
docker-compose ps

# Restart services
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs backend
```

**2. "GOOGLE_API_KEY not found"**
```bash
# Add to .env
echo "GOOGLE_API_KEY=your_api_key_here" >> .env

# Restart backend
docker-compose restart backend
```

**3. "No responses found" przy generowaniu insights**
```bash
# Check if focus group was run
curl http://localhost:8000/api/v1/focus-groups/{id}
# status should be "completed"

# If "pending", run it:
curl -X POST http://localhost:8000/api/v1/focus-groups/{id}/run
```

**4. "Validation error" przy generowaniu person**
```bash
# Ensure distributions sum to 1.0
{
  "age_group": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2}  # ✅ = 1.0
}

# NOT:
{
  "age_group": {"18-24": 0.5, "25-34": 0.8}  # ❌ = 1.3
}
```

**5. "Rate limit exceeded" (Gemini API)**
```bash
# Wait 60 seconds and retry
# Or reduce batch size in config.py:
PERSONA_GENERATION_BATCH_SIZE = 10  # default: 20
```

**6. Frontend build errors**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**7. Database migration issues**
```bash
# Reset database (CAUTION: deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

**8. PDF generation fails**
```bash
# Check if ReportLab is installed
docker-compose exec backend pip list | grep reportlab

# If missing:
docker-compose exec backend pip install reportlab
```

---

## Performance Optimization

### Recommended Settings

**Production:**
```python
# config.py
PERSONA_GENERATION_BATCH_SIZE = 10  # Prevent rate limits
FOCUS_GROUP_MAX_PERSONAS = 50      # UI limit
GEMINI_FLASH_TIMEOUT = 30           # seconds
GEMINI_PRO_TIMEOUT = 60             # seconds
```

**Database:**
```sql
-- Index dla szybkich queries
CREATE INDEX idx_responses_focus_group ON responses(focus_group_id);
CREATE INDEX idx_responses_persona ON responses(persona_id);
CREATE INDEX idx_personas_project ON personas(project_id);
```

**Caching:**
```python
# Dodaj Redis dla cache'owania insights
REDIS_URL = "redis://localhost:6379"
CACHE_TTL = 3600  # 1 hour
```

---

## Security Best Practices

1. **Environment Variables**
   - NIGDY nie commituj .env do git
   - Używaj secrets manager w production (AWS Secrets Manager, etc.)

2. **API Keys**
   - Rotuj GOOGLE_API_KEY co 90 dni
   - Używaj separate keys dla dev/staging/prod

3. **Database**
   - Backup codziennie (automated)
   - Użyj SSL dla połączeń w production

4. **CORS**
   ```python
   # main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # NOT "*" in prod
       allow_credentials=True
   )
   ```

---

## Roadmap & Future Enhancements

### Planowane Funkcje

**Q1 2025:**
- [ ] Multi-language support (Gemini multilingual)
- [ ] Custom AI models (fine-tuning)
- [ ] Real-time collaboration (WebSockets)
- [ ] Advanced visualizations (D3.js charts)

**Q2 2025:**
- [ ] Integration z CRM (Salesforce, HubSpot)
- [ ] Video/audio personas (avatars)
- [ ] Predictive analytics (ML models)
- [ ] A/B testing framework

**Q3 2025:**
- [ ] Mobile app (React Native)
- [ ] Public API (developer platform)
- [ ] Marketplace (persona templates)

**Last Updated:** 2025-10-01
**Version:** 1.0.0 (All 4 Phases Complete)

---

## Quick Reference Card

### Common Commands

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Run tests
python -m pytest tests/test_insights_v2_api.py -v

# Generate personas
curl -X POST localhost:8000/api/v1/projects/{id}/generate-personas \
  -d '{"num_personas": 20}'

# Run focus group
curl -X POST localhost:8000/api/v1/focus-groups/{id}/run

# Get AI summary
curl -X POST localhost:8000/api/v1/focus-groups/{id}/ai-summary

# Download report
curl localhost:8000/api/v1/focus-groups/{id}/enhanced-report > report.pdf
```

### Important URLs

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Database:** postgresql://localhost:5432/market_research