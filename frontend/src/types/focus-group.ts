/**
 * Focus Group Types
 *
 * Wszystkie typy związane z grupami fokusowymi, dyskusjami i analizami.
 */

// ============================================================================
// CORE FOCUS GROUP TYPES
// ============================================================================

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

// ============================================================================
// RESPONSES & DISCUSSIONS
// ============================================================================

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

// ============================================================================
// INSIGHTS & ANALYSIS
// ============================================================================

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

// ============================================================================
// AI SUMMARY
// ============================================================================

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

// ============================================================================
// METRICS & EXPLANATIONS
// ============================================================================

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

// ============================================================================
// ADVANCED INSIGHTS
// ============================================================================

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

// ============================================================================
// BUSINESS INSIGHTS
// ============================================================================

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
