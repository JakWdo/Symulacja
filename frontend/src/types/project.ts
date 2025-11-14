/**
 * Project Types
 *
 * Wszystkie typy związane z projektami, ich zarządzaniem i operacjami.
 */

// ============================================================================
// CORE PROJECT TYPES
// ============================================================================

export interface Project {
  id: string;
  environment_id: string | null;
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

// ============================================================================
// PROJECT DELETE & RESTORE OPERATIONS
// ============================================================================

export interface ProjectDeleteResponse {
  project_id: string;
  name: string;
  status: 'deleted';
  deleted_at: string;
  deleted_by: string;
  undo_available_until: string;
  permanent_deletion_scheduled_at?: string | null;
  message: string;
  cascaded_entities: {
    personas_count: number;
    focus_groups_count: number;
    surveys_count: number;
  };
}

export interface ProjectUndoDeleteResponse {
  project_id: string;
  name: string;
  status: 'active';
  restored_at: string;
  restored_by: string;
  message: string;
  restored_entities: {
    personas_count: number;
    focus_groups_count: number;
    surveys_count: number;
  };
}

export interface ProjectDeleteImpact {
  project_id: string;
  personas_count: number;
  focus_groups_count: number;
  surveys_count: number;
  total_responses_count: number;
  warning: string;
}
