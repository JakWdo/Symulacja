/**
 * Dashboard Types - mirror backend schemas
 */

export interface TrendData {
  value: number;
  change_percent: number;
  direction: 'up' | 'down' | 'stable';
}

export interface MetricCard {
  label: string;
  value: string; // formatted (e.g., "2.5 min")
  raw_value: number | string | null;
  p90?: number; // P90 value (for TTI metric)
  trend?: TrendData;
  tooltip?: string;
}

export interface OverviewResponse {
  active_research: MetricCard;
  pending_actions: MetricCard;
  insights_ready: MetricCard;
  this_week_activity: MetricCard;
  time_to_insight: MetricCard;
  insight_adoption_rate: MetricCard;
  persona_coverage: MetricCard;
  blockers_count: MetricCard;
}

export interface ActionContext {
  project_id?: string;
  project_name?: string;
  blocker_count?: number;
  blockers?: Array<{ type: string; severity: string; message: string }>;
  target_count?: number;
  persona_count?: number;
  insight_count?: number;
}

export interface QuickAction {
  action_id: string;
  action_type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  icon: string; // Lucide icon name
  context: ActionContext;
  cta_label: string;
  cta_url: string;
}

export interface ActionExecutionResult {
  status: 'success' | 'redirect' | 'error';
  message: string;
  redirect_url?: string;
}

export interface HealthStatus {
  status: 'on_track' | 'at_risk' | 'blocked';
  score: number; // 0-100
  color: string; // 'green', 'yellow', 'red'
}

export interface ProgressStages {
  demographics: boolean;
  personas: boolean;
  focus: boolean;
  analysis: boolean;
  current_stage: string;
}

export interface ProjectWithHealth {
  id: string;
  name: string;
  research_type: string;
  status: 'running' | 'paused' | 'completed' | 'blocked';
  health: HealthStatus;
  progress: ProgressStages;
  insights_count: number;
  new_insights_count: number;
  last_activity: string; // ISO datetime
  cta_label: string;
  cta_url: string;
}

export interface WeeklyCompletionData {
  weeks: string[]; // ["2025-W01", ...]
  personas: number[];
  focus_groups: number[];
  surveys: number[];
  insights: number[];
}

export interface ConceptData {
  concept: string;
  count: number;
}

export interface SentimentData {
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
}

export interface InsightTypesData {
  opportunity: number;
  risk: number;
  trend: number;
  pattern: number;
}

export interface InsightAnalyticsData {
  top_concepts: ConceptData[];
  sentiment_distribution: SentimentData;
  insight_types: InsightTypesData;
  response_patterns: Array<{ pattern: string; count: number }>;
}

export interface InsightEvidenceItem {
  type: 'quote' | 'snippet' | 'concept';
  text: string;
  source: string;
  source_id?: string;
}

export interface InsightProvenance {
  model_version: string;
  prompt_hash: string;
  sources: Array<{ type: string; id: string }>;
  created_at: string;
}

export interface InsightHighlight {
  id: string;
  project_id: string;
  project_name: string;
  insight_type: 'opportunity' | 'risk' | 'trend' | 'pattern';
  insight_text: string;
  confidence_score: number;
  impact_score: number;
  time_ago: string;
  evidence_count: number;
  is_viewed: boolean;
  is_adopted: boolean;
}

export interface InsightDetail extends InsightHighlight {
  evidence: InsightEvidenceItem[];
  provenance: InsightProvenance;
  concepts: string[];
  sentiment: string;
}

export interface Blocker {
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  fix_action: string;
  fix_url?: string;
  focus_group_id?: string;
}

export interface BlockerWithFix extends Blocker {
  project_id: string;
  project_name: string;
}

export interface HealthBlockersResponse {
  summary: Record<string, number>; // { on_track: 5, at_risk: 2, blocked: 1 }
  blockers: BlockerWithFix[];
}

export interface UsageHistory {
  date: string;
  total_tokens: number;
  total_cost: number;
}

export interface BudgetAlert {
  alert_type: 'warning' | 'exceeded';
  message: string;
  threshold: number; // 0.9 or 1.0
  current: number; // 0-1
}

export interface UsageBudgetResponse {
  total_tokens: number;
  total_cost: number;
  forecast_month_end: number;
  budget_limit?: number;
  alert_thresholds?: {
    warning: number;
    critical: number;
  };
  alerts: BudgetAlert[];
  history: UsageHistory[];
}

export interface Notification {
  id: string;
  notification_type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  message: string;
  time_ago: string;
  is_read: boolean;
  is_done: boolean;
  action_label?: string;
  action_url?: string;
  created_at: string;
}

export interface UsageCategoryBreakdown {
  tokens: number;
  cost: number;
  percentage: number; // 0-100
}

export interface UsageBreakdownResponse {
  persona_generation: UsageCategoryBreakdown;
  focus_group: UsageCategoryBreakdown;
  rag_query: UsageCategoryBreakdown;
  other: UsageCategoryBreakdown;
  total_tokens: number;
  total_cost: number;
}
