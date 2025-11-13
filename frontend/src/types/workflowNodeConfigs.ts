/**
 * TypeScript interfaces dla workflow node configurations
 *
 * Mapuje backend Pydantic schemas z app/schemas/workflow.py
 * Każdy z 14 typów nodów ma dedykowany config interface.
 *
 * Używane przez:
 * - Property Panels (forms)
 * - Node executors (validation)
 * - WorkflowEditor (state management)
 */

// ==================== CONTROL FLOW NODES ====================

/**
 * START Node - Entry point workflow
 */
export interface StartNodeConfig {
  trigger_type?: 'manual';
}

/**
 * END Node - Completion point
 */
export interface EndNodeConfig {
  success_message?: string;
}

/**
 * DECISION Node - Conditional branching (if/else)
 */
export interface DecisionNodeConfig {
  condition: string; // Python expression
  true_branch_label?: string;
  false_branch_label?: string;
}

/**
 * LOOP_START Node - Begin loop iteration
 */
export interface LoopStartNodeConfig {
  iteration_variable: string; // e.g., "persona"
  items_source: string; // e.g., "personas", "survey_results"
  max_iterations?: number;
}

/**
 * LOOP_END Node - End loop iteration
 */
export interface LoopEndNodeConfig {
  loop_start_node_id: string; // ID of corresponding LOOP_START
}

// ==================== DATA GENERATION NODES ====================

/**
 * CREATE_PROJECT Node - Tworzy nowy projekt badawczy
 */
export interface CreateProjectNodeConfig {
  project_name: string;
  project_description?: string;
  target_demographics?: {
    age_min?: number;
    age_max?: number;
    gender?: string[];
    location?: string[];
  };
}

/**
 * GENERATE_PERSONAS Node - Generuje AI personas
 */
export interface GeneratePersonasNodeConfig {
  count: number; // 1-100
  demographic_preset?: string; // "gen_z", "millennials", etc.
  target_audience_description?: string;
  advanced_options?: {
    diversity_level?: 'low' | 'medium' | 'high';
    include_edge_cases?: boolean;
    age_focus?: string; // e.g., "18-25", "30-45"
    gender_balance?: Record<string, number>; // {"male": 40, "female": 50, "non-binary": 10}
    urbanicity?: 'urban' | 'suburban' | 'rural' | 'mixed';
    industries?: string[];
  };
}

/**
 * Survey Question - pojedyncze pytanie w ankiecie
 */
export interface SurveyQuestion {
  text: string;
  type: 'single' | 'multiple' | 'text' | 'scale';
  options?: string[]; // Dla single/multiple choice
  scale_min?: number; // Dla scale (default: 1)
  scale_max?: number; // Dla scale (default: 5)
  required?: boolean;
}

/**
 * CREATE_SURVEY Node - Tworzy ankietę
 */
export interface CreateSurveyNodeConfig {
  survey_name: string;
  survey_description?: string;
  template_id?: string; // "nps", "satisfaction", etc.
  questions?: SurveyQuestion[];
  ai_generate_questions?: boolean;
  ai_prompt?: string; // Required if ai_generate_questions=true
  target_personas?: string; // "all" lub filter expression
}

// ==================== ANALYSIS NODES ====================

/**
 * RUN_FOCUS_GROUP Node - Przeprowadza symulowaną dyskusję
 */
export interface RunFocusGroupNodeConfig {
  focus_group_title: string;
  topics: string[]; // Lista pytań do dyskusji (1-10)
  participant_ids?: string[]; // UUIDs person (null = use previous node)
  moderator_style?: 'neutral' | 'probing' | 'directive';
  rounds?: number; // 1-5, default: 3
}

/**
 * ANALYZE_RESULTS Node - AI analysis wyników
 */
export interface AnalyzeResultsNodeConfig {
  analysis_type: 'summary' | 'sentiment' | 'themes' | 'insights';
  input_source: 'focus_group' | 'survey' | 'personas';
  prompt_template?: string; // Custom prompt dla LLM
}

/**
 * GENERATE_INSIGHTS Node - Generuje głębokie insights
 */
export interface GenerateInsightsNodeConfig {
  insight_focus: string[]; // ["pain_points", "opportunities", "trends"]
  output_format: 'summary' | 'detailed' | 'bullet_points';
  include_quotes?: boolean;
}

/**
 * COMPARE_GROUPS Node - Porównuje dwie grupy
 */
export interface CompareGroupsNodeConfig {
  group_a_source: string; // Node ID
  group_b_source: string; // Node ID
  comparison_metrics: string[];
}

// ==================== OUTPUT NODES ====================

/**
 * FILTER_DATA Node - Filtruje dane według warunków
 */
export interface FilterDataNodeConfig {
  filter_expression: string; // Python expression
  data_source: string; // Node ID
}

/**
 * EXPORT_REPORT Node - Eksportuje raport
 */
export interface ExportReportNodeConfig {
  report_name: string;
  format: 'pdf' | 'docx' | 'json' | 'csv';
  sections: string[]; // Co zawrzeć w raporcie
  include_raw_data?: boolean;
}

// ==================== UNION TYPE ====================

/**
 * NodeConfig - Union type dla wszystkich możliwych configs
 */
export type NodeConfig =
  | StartNodeConfig
  | EndNodeConfig
  | DecisionNodeConfig
  | LoopStartNodeConfig
  | LoopEndNodeConfig
  | CreateProjectNodeConfig
  | GeneratePersonasNodeConfig
  | CreateSurveyNodeConfig
  | RunFocusGroupNodeConfig
  | AnalyzeResultsNodeConfig
  | GenerateInsightsNodeConfig
  | CompareGroupsNodeConfig
  | FilterDataNodeConfig
  | ExportReportNodeConfig;

// ==================== TYPE GUARDS ====================

/**
 * Type guard functions dla runtime type checking
 */
export function isGeneratePersonasConfig(
  config: NodeConfig
): config is GeneratePersonasNodeConfig {
  return 'count' in config;
}

export function isCreateSurveyConfig(
  config: NodeConfig
): config is CreateSurveyNodeConfig {
  return 'survey_name' in config;
}

export function isRunFocusGroupConfig(
  config: NodeConfig
): config is RunFocusGroupNodeConfig {
  return 'focus_group_title' in config;
}

export function isDecisionConfig(
  config: NodeConfig
): config is DecisionNodeConfig {
  return 'condition' in config && 'true_branch_label' in config;
}

export function isAnalyzeResultsConfig(
  config: NodeConfig
): config is AnalyzeResultsNodeConfig {
  return 'analysis_type' in config && 'input_source' in config;
}

export function isExportReportConfig(
  config: NodeConfig
): config is ExportReportNodeConfig {
  return 'report_name' in config && 'format' in config;
}

// ==================== DEFAULT CONFIGS ====================

/**
 * Default config values dla każdego typu node
 *
 * NOTE: Moved to constants/workflows.ts for better organization
 * Re-exported here for backward compatibility
 */
export { DEFAULT_NODE_CONFIGS } from '../constants/workflows';
