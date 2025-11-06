/**
 * Shared TypeScript types for Persona components
 */

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
  createdAt: string;
  projectId: number;
}

export interface JobToBeDone {
  statement: string;
  priority: number;
  frequency: string;
  difficulty: string;
  quotes: string[];
}

export interface DesiredOutcome {
  statement: string;
  opportunityScore: number;
  importance: number;
  satisfaction: number;
  measurable: boolean;
}

export interface PainPoint {
  title: string;
  description: string;
  severity: 'Krytyczny' | 'Wysoki' | 'Średni' | 'Niski';
  frequency: string;
  affects: string;
  quotes?: string[];
  solutions: string[];
}

export interface SegmentData {
  name: string;
  tagline: string;
  characteristics: string[];
  ageRange: { min: number; max: number };
  demographics: {
    gender?: string;
    location?: string;
    education?: string;
    income?: string;
  };
}

export interface SegmentInsight {
  magnitude: 'Wysoka' | 'Średnia' | 'Niska';
  summary: string;
  whyMatters: string;
  source: string;
  period: string;
  confidence: 'Wysoka' | 'Średnia' | 'Niska';
}

export interface AllocationReasoning {
  personaCount: number;
  reason: string;
  confidence: number;
}

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  user: string;
  changes?: string[];
  source: 'Manual' | 'AI' | 'System';
}

export interface RAGContext {
  source: string;
  sourceType: 'Graph' | 'Vector' | 'Structured';
  relevanceScore: number;
  summary: string;
  url?: string;
  timestamp?: string;
}

export interface PersonaDetailsAPI {
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
  createdAt: string;
  projectId: number;
  needs_and_pains?: {
    jobs_to_be_done: JobToBeDone[];
    desired_outcomes: DesiredOutcome[];
    pain_points: PainPoint[];
  };
  rag_context_details?: RAGContext[];
  audit_log?: AuditLogEntry[];
  segment?: {
    name: string;
    tagline: string;
    characteristics: string[];
    age_range: { min: number; max: number };
    demographics: SegmentData['demographics'];
    insights: SegmentInsight[];
    allocation: AllocationReasoning;
  };
}
