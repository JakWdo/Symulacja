/**
 * Graph Types
 *
 * Wszystkie typy związane z wizualizacją grafową, węzłami i połączeniami.
 */

// ============================================================================
// GRAPH STRUCTURE
// ============================================================================

export interface ClusterDetail {
  id: string;
  name: string;
  size: number;
  description?: string;
}

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
  data?: any; // Persona | ClusterDetail | any - unikamy circular dependency
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

// ============================================================================
// GRAPH INSIGHTS
// ============================================================================

export interface GraphInsight {
  type: string;
  summary: string;
  magnitude?: string;
  confidence: 'high' | 'medium' | 'low';
  time_period?: string;
  source?: string;
  why_matters: string;
}

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

// ============================================================================
// GRAPH QUERIES
// ============================================================================

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

// ============================================================================
// UI STATE TYPES
// ============================================================================

export interface FloatingPanelState {
  isOpen: boolean;
  position: { x: number; y: number };
  size: { width: number; height: number };
}

export interface ViewState {
  selectedProject: any | null;
  selectedPersona: any | null;
  selectedFocusGroup: any | null;
  graphData: GraphData | null;
  filterMode: 'all' | 'selected' | 'cluster';
}
