/**
 * Survey Types
 *
 * Wszystkie typy związane z ankietami, pytaniami i wynikami.
 */

// ============================================================================
// CORE SURVEY TYPES
// ============================================================================

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

// ============================================================================
// SURVEY RESULTS & ANALYTICS
// ============================================================================

export interface QuestionAnalytics {
  question_id: string;
  question_text: string;
  question_type: 'rating_scale' | 'single_choice' | 'multiple_choice' | 'open_text';
  total_responses: number;
  response_rate: number;
  distribution: Record<string, number>;
  stats: {
    mean: number;
    median: number;
    std_dev: number;
    min: number;
    max: number;
  } | null;
}

export interface SurveyResults {
  question_analytics: QuestionAnalytics[];
  demographic_breakdown: {
    by_age: Record<string, { count: number; avg_rating: number }>;
    by_gender: Record<string, { count: number; avg_rating: number }>;
    by_education: Record<string, { count: number; avg_rating: number }>;
  };
  completion_rate: number;
  average_response_time_ms: number;
  total_personas: number;
  responding_personas: number;
}
