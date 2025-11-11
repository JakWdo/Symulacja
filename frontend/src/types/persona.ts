/**
 * Persona Types
 *
 * Wszystkie typy związane z personami, ich detalami, analizami i operacjami.
 */

import type { RAGCitation, RagContextDetails } from './rag';
import type { GraphInsight } from './graph';

// ============================================================================
// CORE PERSONA TYPES
// ============================================================================

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

// ============================================================================
// ORCHESTRATION & REASONING TYPES
// ============================================================================

export interface PersonaReasoning {
  // === NOWE POLA (segment-based) ===
  segment_name?: string;  // Np. "Młodzi Prekariusze"
  segment_id?: string;
  segment_description?: string;
  segment_social_context?: string;  // Kontekst dla TEJ grupy (500-800 znaków)
  segment_characteristics?: string[];  // 4-6 kluczowych cech segmentu

  // === AKTUALNE POLA ===
  orchestration_brief?: string;
  graph_insights: GraphInsight[];
  allocation_reasoning?: string;
  demographics?: Record<string, any>;
  overall_context?: string;  // Legacy, używamy segment_social_context teraz
}

// ============================================================================
// PERSONA DETAILS & AUDIT
// ============================================================================

export interface PersonaAuditEntry {
  action: string;
  timestamp: string;
  user_id?: string;
  details?: Record<string, any>;
}

export interface PersonaDetailsResponse extends Persona {
  // Additional fields for details view
  needs_and_pains?: NeedsAndPains | null;
  audit_log: PersonaAuditEntry[];
}

// ============================================================================
// DELETE & RESTORE OPERATIONS
// ============================================================================

export interface PersonaDeleteResponse {
  persona_id: string;
  full_name: string | null;
  status: 'deleted';
  deleted_at: string;
  deleted_by: string;
  undo_available_until: string;
  permanent_deletion_scheduled_at?: string | null;
  message: string;
}

export interface PersonaUndoDeleteResponse {
  persona_id: string;
  full_name: string | null;
  status: 'active';
  restored_at: string;
  restored_by: string;
  message: string;
}

// ============================================================================
// JTBD (Jobs To Be Done)
// ============================================================================

export interface JTBDJob {
  job_statement: string;
  priority_score?: number;
  frequency?: string;
  difficulty?: string;
  quotes?: string[];
}

export interface DesiredOutcome {
  outcome_statement: string;
  importance?: number;
  satisfaction_current_solutions?: number;
  opportunity_score?: number;
  is_measurable?: boolean;
}

export interface PainPoint {
  pain_title: string;
  pain_description?: string;
  severity?: number;
  frequency?: string;
  percent_affected?: number;
  quotes?: string[];
  potential_solutions?: string[];
}

export interface NeedsAndPains {
  jobs_to_be_done: JTBDJob[];
  desired_outcomes: DesiredOutcome[];
  pain_points: PainPoint[];
  generated_at?: string;
  generated_by?: string;
}

// ============================================================================
// MESSAGING & COMMUNICATION
// ============================================================================

export interface MessagingVariant {
  variant_id: number;
  headline: string;
  subheadline?: string;
  body: string;
  cta: string;
}

export interface PersonaMessagingResponse {
  variants: MessagingVariant[];
  generated_at: string;
  generated_by?: string;
}

export interface PersonaMessagingPayload {
  tone: 'friendly' | 'professional' | 'urgent' | 'empathetic';
  type: 'email' | 'ad' | 'landing_page' | 'social_post';
  num_variants?: number;
  context?: string;
}

// ============================================================================
// PERSONA COMPARISON
// ============================================================================

export interface PersonaComparisonValue {
  persona_id: string;
  value: string | number | boolean | string[] | null;
}

export interface PersonaDifference {
  field: string;
  values: PersonaComparisonValue[];
}

export interface PersonaComparisonPersona {
  id: string;
  full_name?: string | null;
  age: number;
  gender: string;
  location?: string | null;
  occupation?: string | null;
  education_level?: string | null;
  income_bracket?: string | null;
  segment_id?: string | null;
  segment_name?: string | null;
  values: string[];
  interests: string[];
  big_five: Record<string, number | null | undefined>;
  kpi_snapshot?: Record<string, any> | null;
}

export interface PersonaComparisonResponse {
  personas: PersonaComparisonPersona[];
  differences: PersonaDifference[];
  similarity: Record<string, Record<string, number>>;
}

// ============================================================================
// PERSONA EXPORT
// ============================================================================

export interface PersonaExportResponse {
  format: 'json';
  sections: string[];
  content: Record<string, any>;
}
