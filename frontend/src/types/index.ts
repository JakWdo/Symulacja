// API Types
export interface Project {
  id: string;
  name: string;
  description: string | null;
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
}

export interface FocusGroup {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  persona_ids: string[];
  questions: string[];
  mode: 'normal' | 'adversarial';
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_execution_time_ms: number | null;
  avg_response_time_ms: number | null;
  max_response_time_ms: number | null;
  overall_consistency_score: number | null;
  consistency_errors_count: number | null;
  consistency_error_rate: number | null;
  polarization_score: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface PersonaResponse {
  persona_id: string;
  response: string;
  response_time_ms: number;
  consistency_score: number;
  contradictions: any[];
  context_used: number;
}

export interface PolarizationAnalysis {
  focus_group_id: string;
  overall_polarization_score: number;
  polarization_level: string;
  questions: QuestionAnalysis[];
}

export interface QuestionAnalysis {
  question: string;
  polarization_score: number;
  num_clusters: number;
  clusters: ClusterDetail[];
  sentiment_divergence: number;
  num_responses: number;
}

export interface ClusterDetail {
  cluster_id: number;
  size: number;
  persona_ids: string[];
  representative_response: string;
  avg_sentiment: number;
}

// Graph Types
export interface GraphNode {
  id: string;
  label: string;
  type: 'persona' | 'cluster' | 'topic' | 'project';
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  vz?: number;
  data: Persona | ClusterDetail | any;
  color?: string;
  size?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  value: number;
  type: 'similarity' | 'cluster' | 'response';
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
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