// API Types
export interface Project {
  id: string;
  name: string;
  description: string | null;
  target_audience: string | null;
  research_objectives: string | null;
  additional_notes: string | null;
  target_demographics: Record<string, Record<string, number>>;
  target_sample_size: number;
  chi_square_statistic: Record<string, number> | null;
  p_values: Record<string, number> | null;
  is_statistically_valid: boolean;
  validation_date: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface Persona {
  id: string;
  project_id: string;
  age: number;
  gender: string;
  location: string | null;
  education_level: string | null;
  income_bracket: string | null;
  occupation: string | null;
  full_name: string | null;
  persona_title: string | null;
  headline: string | null;
  openness: number | null;
  conscientiousness: number | null;
  extraversion: number | null;
  agreeableness: number | null;
  neuroticism: number | null;
  power_distance: number | null;
  individualism: number | null;
  masculinity: number | null;
  uncertainty_avoidance: number | null;
  long_term_orientation: number | null;
  indulgence: number | null;
  values: string[] | null;
  interests: string[] | null;
  background_story: string | null;
  created_at: string;
  is_active: boolean;
  rag_context_used: boolean;
  rag_citations: RAGCitation[] | null;
  rag_context_details?: RagContextDetails | null;
}

export interface FocusGroup {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  project_context: string | null;
  persona_ids: string[];
  questions: string[];
  mode: 'normal' | 'adversarial';
  status: 'pending' | 'running' | 'completed' | 'failed';
  target_participants: number | null;
  total_execution_time_ms: number | null;
  avg_response_time_ms: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface PersonaResponse {
  persona_id: string;
  response: string;
  created_at: string;
}

export interface FocusGroupResponses {
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

export interface InsightSignalItem {
  title: string;
  summary: string;
  evidence?: string;
}

export interface InsightSignalBreakdown {
  strengths: InsightSignalItem[];
  risks: InsightSignalItem[];
  opportunities: InsightSignalItem[];
}

export type PersonaClassification = 'champion' | 'detractor' | 'low_engagement' | 'neutral';

export interface PersonaPattern {
  persona_id: string;
  classification: PersonaClassification;
  avg_sentiment: number;
  contribution_count: number;
  last_activity: string | null;
  summary: string;
}

export interface EvidenceHighlight {
  persona_id: string | null;
  question: string | null;
  response: string;
  sentiment: number;
  consistency_score: number | null;
  created_at: string | null;
}

export interface EvidenceFeed {
  positives: EvidenceHighlight[];
  negatives: EvidenceHighlight[];
}

export interface FocusGroupInsights {
  focus_group_id: string;
  idea_score: number;
  idea_grade: string;
  metrics: {
    consensus: number;
    average_sentiment: number;
    sentiment_summary: {
      positive_ratio: number;
      negative_ratio: number;
      neutral_ratio: number;
    };
    engagement: {
      average_response_time_ms: number | null;
      completion_rate: number;
      consistency_score: number | null;
    };
  };
  signal_breakdown?: InsightSignalBreakdown;
  persona_patterns?: PersonaPattern[];
  evidence_feed?: EvidenceFeed;
  llm_confidence?: number;
  llm_rationale?: string;
}

export interface PersonaInsight {
  persona: {
    id: string;
    age: number;
    gender: string;
    location: string | null;
    education_level: string | null;
    income_bracket: string | null;
    occupation: string | null;
    values: string[];
    interests: string[];
    background_story: string | null;
  };
  trait_scores: Record<string, number>;
  expectations: string[];
}

export interface AISummaryMetadata {
  focus_group_id: string;
  focus_group_name: string;
  generated_at: string;
  model_used: string;
  total_responses: number;
  total_participants: number;
  questions_asked?: number;
}

export interface AISummary {
  executive_summary: string;
  key_insights: string[];
  surprising_findings: string[];
  segment_analysis: Record<string, string>;
  recommendations: string[];
  sentiment_narrative: string;
  full_analysis: string;
  metadata: AISummaryMetadata;
}

export interface MetricExplanation {
  name: string;
  value: string;
  interpretation: string;
  context: string;
  action: string;
  benchmark?: string | null;
}

export type MetricExplanationMap = Record<string, MetricExplanation>;

export type HealthStatus = 'healthy' | 'good' | 'fair' | 'poor';

export interface HealthAssessment {
  health_score: number;
  status: HealthStatus;
  status_label: string;
  color: string;
  message: string;
  concerns: string[];
  strengths: string[];
}

export interface MetricExplanationsResponse {
  focus_group_id: string;
  explanations: MetricExplanationMap;
  health_assessment: HealthAssessment;
}

export interface HealthCheck extends HealthAssessment {
  focus_group_id: string;
}

export interface TemporalTrend {
  slope: number;
  direction: 'improving' | 'declining' | 'stable';
  r_squared: number;
  p_value: number;
  significant: boolean;
}

export interface SentimentTrajectory {
  initial_sentiment: number;
  final_sentiment: number;
  peak_sentiment: number;
  trough_sentiment: number;
  volatility: number;
}

export interface MomentumShift {
  index: number;
  sentiment_change: number;
  question: string;
}

export interface FatigueAnalysis {
  fatigue_detected: boolean;
  response_length_trend: number;
  interpretation: string;
}

export interface TemporalAnalysis {
  overall_trend?: TemporalTrend;
  sentiment_trajectory?: SentimentTrajectory;
  momentum_shifts?: MomentumShift[];
  fatigue_analysis?: FatigueAnalysis;
}

export interface DemographicCorrelations {
  age_sentiment?: {
    correlation: number;
    p_value: number;
    significant: boolean;
    interpretation: string;
  };
  gender_sentiment?: {
    mean_by_gender: Record<string, number>;
    f_statistic: number;
    p_value: number;
    significant: boolean;
    interpretation: string;
  };
  education_sentiment?: {
    mean_by_education: Record<string, number>;
    top_segment?: string | null;
    bottom_segment?: string | null;
  };
  personality_sentiment?: Record<
    string,
    {
      correlation: number;
      p_value: number;
      significant: boolean;
    }
  >;
  [key: string]: unknown;
}

export interface BehavioralSegment {
  segment_id: number;
  size: number;
  percentage: number;
  characteristics: {
    avg_sentiment: number;
    sentiment_volatility: number;
    avg_response_length: number;
    avg_consistency: number;
  };
  demographics: {
    avg_age: number;
    gender_distribution: Record<string, number>;
    top_education: string;
  };
  label: string;
}

export interface BehavioralSegmentation {
  num_segments?: number;
  segments?: BehavioralSegment[];
  segmentation_quality?: number;
}

export interface QualityMetrics {
  depth_score?: number;
  constructiveness_score?: number;
  specificity_score?: number;
  overall_quality?: number;
  quality_distribution?: {
    high_quality_responses?: number;
    medium_quality_responses?: number;
    low_quality_responses?: number;
  };
}

export interface ComparativeQuestionMetrics {
  question: string;
  avg_sentiment: number;
  avg_length: number;
  sentiment_std?: number;
}

export interface ComparativeAnalysis {
  best_questions?: ComparativeQuestionMetrics[];
  worst_questions?: ComparativeQuestionMetrics[];
  most_polarizing?: ComparativeQuestionMetrics[];
}

export interface OutlierDetection {
  sentiment_outliers?: number;
  length_outliers?: number;
  outlier_personas?: string[];
}

export interface EngagementPatterns {
  high_engagers?: number;
  low_engagers?: number;
  avg_response_time?: number;
  avg_words_per_response?: number;
}

export interface AdvancedInsights {
  focus_group_id: string;
  demographic_correlations: DemographicCorrelations;
  temporal_analysis: TemporalAnalysis;
  behavioral_segments: BehavioralSegmentation;
  quality_metrics: QualityMetrics;
  comparative_analysis: ComparativeAnalysis;
  outlier_detection: OutlierDetection;
  engagement_patterns: EngagementPatterns;
}

// Graph Types
export interface GraphNode {
  id: string;
  name?: string;
  label?: string;
  type: 'persona' | 'concept' | 'emotion' | 'cluster' | 'topic' | 'project';
  group?: number;
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  vz?: number;
  data?: Persona | ClusterDetail | any;
  metadata?: Record<string, any>;
  color?: string;
  size?: number;
  sentiment?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  value?: number;
  type: 'mentions' | 'feels' | 'agrees' | 'disagrees' | 'similarity' | 'cluster' | 'response';
  strength?: number;
  sentiment?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// Advanced Graph Insights
export interface ControversialConcept {
  concept: string;
  avg_sentiment: number;
  polarization: number;
  supporters: string[];
  critics: string[];
  total_mentions: number;
}

export interface TraitCorrelation {
  concept: string;
  young_sentiment: number | null;
  mid_sentiment: number | null;
  senior_sentiment: number | null;
  age_gap: number;
  mentions: number;
}

export interface EmotionData {
  emotion: string;
  personas_count: number;
  avg_intensity: number;
  percentage: number;
}

export interface InfluentialPersona {
  id: string;
  name: string;
  influence: number;
  connections: number;
  sentiment: number;
}

export interface KeyConcept {
  name: string;
  frequency: number;
  sentiment: number;
  personas: string[];
}

export interface GraphQueryInsight {
  title: string;
  detail: string;
  metadata?: Record<string, any>;
}

export interface GraphQueryResponse {
  answer: string;
  insights: GraphQueryInsight[];
  suggested_questions: string[];
}

// UI State Types
export interface FloatingPanelState {
  isOpen: boolean;
  position: { x: number; y: number };
  size: { width: number; height: number };
}

export interface ViewState {
  selectedProject: Project | null;
  selectedPersona: Persona | null;
  selectedFocusGroup: FocusGroup | null;
  graphData: GraphData | null;
  filterMode: 'all' | 'selected' | 'cluster';
}

// AI Business Insights Types
export interface MarketFitAssessment {
  score: number; // 0-100
  confidence: 'low' | 'medium' | 'high';
  rationale: string;
  supporting_evidence: string;
  key_insights: string[];
}

export interface ReadinessLevel {
  level: 'not_ready' | 'needs_work' | 'ready' | 'high_confidence';
  score: number; // 0-100
  gaps: string[];
  strengths: string[];
  recommendation: string;
  timeline_estimate?: string | null;
}

export interface RiskItem {
  category: 'adoption_barrier' | 'pricing_concern' | 'competition_threat' | 'ux_issue' | 'market_timing' | 'other';
  severity: 'low' | 'medium' | 'high';
  description: string;
  evidence: string;
  affected_personas_pct: number;
  mitigation_suggestion?: string | null;
}

export interface RiskProfile {
  overall_risk_level: 'low' | 'medium' | 'high';
  risks: RiskItem[];
  risk_summary: string;
}

export interface OpportunityItem {
  description: string;
  impact_score: number; // 0-100
  category: 'new_use_case' | 'unexpected_segment' | 'adjacent_market' | 'feature_request' | 'positioning_insight' | 'other';
  evidence: string;
  personas_mentioning: number;
}

export interface OpportunityAnalysis {
  opportunities: OpportunityItem[];
  opportunity_summary: string;
  strategic_recommendation: string;
}

export interface QualityAssessment {
  authenticity_score: number; // 0-100
  detail_level: 'superficial' | 'adequate' | 'detailed' | 'exceptional';
  engagement_quality: 'low' | 'moderate' | 'high';
  constructive_feedback_ratio: number; // 0-1
  interpretation: string;
  notable_patterns: string[];
}

export interface BusinessInsights {
  focus_group_id: string;
  market_fit: MarketFitAssessment;
  readiness: ReadinessLevel;
  risk_profile: RiskProfile;
  opportunities: OpportunityAnalysis;
  quality: QualityAssessment;
  generated_at: string;
  model_used: string;
}

// Survey Types
export interface Question {
  id: string;
  type: 'single-choice' | 'multiple-choice' | 'rating-scale' | 'open-text';
  title: string;
  description?: string;
  options?: string[];
  required: boolean;
  scaleMin?: number;
  scaleMax?: number;
}

export interface Survey {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  questions: Question[];
  status: 'draft' | 'running' | 'completed' | 'failed';
  target_responses: number;
  actual_responses: number;
  total_execution_time_ms?: number;
  avg_response_time_ms?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  is_active: boolean;
}

export interface QuestionAnalytics {
  question_id: string;
  question_type: string;
  question_title: string;
  responses_count: number;
  statistics: Record<string, any>;
}

export interface SurveyResults {
  // Base Survey fields
  id: string;
  project_id: string;
  title: string;
  description?: string;
  questions: Question[];
  status: string;
  target_responses: number;
  actual_responses: number;
  total_execution_time_ms?: number;
  avg_response_time_ms?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;

  // Analytics fields
  question_analytics: QuestionAnalytics[];
  demographic_breakdown: Record<string, Record<string, any>>;
  completion_rate: number;
  average_response_time_ms?: number;
}

// RAG Types
export interface RAGDocument {
  id: string;
  title: string;
  filename: string;
  file_path: string;
  file_type: 'pdf' | 'docx';
  country: string;
  num_chunks: number;
  status: 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
  is_active: boolean;
}

export interface RAGCitation {
  document_title: string;
  chunk_text: string;
  relevance_score: number;
}

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
}

export interface RAGQueryResponse {
  query: string;
  context: string;
  citations: RAGCitation[];
  num_results: number;
}

export interface RagContextOrchestrationReasoning {
  brief?: string;
  graph_insights?: GraphInsight[];
  allocation_reasoning?: string;
  demographics?: Record<string, any>;
  overall_context?: string;
  segment_name?: string;
  segment_description?: string;
  segment_social_context?: string;
  segment_id?: string;
}

export interface RAGGraphNode {
  type?: string;
  summary?: string;
  streszczenie?: string;
  magnitude?: string;
  skala?: string;
  confidence?: string;
  pewnosc?: string;
  time_period?: string;
  okres_czasu?: string;
  source?: string;
  document_title?: string;
  why_matters?: string;
  kluczowe_fakty?: string;
  [key: string]: unknown;
}

export interface RagContextDetails {
  search_type?: string;
  num_results?: number;
  graph_nodes_count?: number;
  graph_nodes?: RAGGraphNode[];
  graph_context?: string;
  context_preview?: string;
  context_length?: number;
  enriched_chunks?: number;
  citations_count?: number;
  query?: string;
  orchestration_reasoning?: RagContextOrchestrationReasoning;
}

// === ORCHESTRATION REASONING TYPES ===

export interface GraphInsight {
  type: string;
  summary: string;
  magnitude?: string;
  confidence: 'high' | 'medium' | 'low';
  time_period?: string;
  source?: string;
  why_matters: string;
}

export interface PersonaReasoning {
  // === NOWE POLA (segment-based) ===
  segment_name?: string;  // Np. "Młodzi Prekariusze"
  segment_id?: string;
  segment_description?: string;
  segment_social_context?: string;  // Kontekst dla TEJ grupy (500-800 znaków)

  // === AKTUALNE POLA ===
  orchestration_brief?: string;
  graph_insights: GraphInsight[];
  allocation_reasoning?: string;
  demographics?: Record<string, any>;
  overall_context?: string;  // Legacy, używamy segment_social_context teraz
}
