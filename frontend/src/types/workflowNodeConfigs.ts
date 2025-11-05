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
 */
export const DEFAULT_NODE_CONFIGS: Record<string, Partial<NodeConfig>> = {
  start: {
    trigger_type: 'manual',
  } as StartNodeConfig,

  end: {
    success_message: 'Workflow completed successfully',
  } as EndNodeConfig,

  decision: {
    condition: 'true',
    true_branch_label: 'Yes',
    false_branch_label: 'No',
  } as DecisionNodeConfig,

  generate_personas: {
    count: 20,
    demographic_preset: 'poland_general',
    advanced_options: {
      diversity_level: 'medium',
      include_edge_cases: false,
    },
  } as GeneratePersonasNodeConfig,

  create_survey: {
    survey_name: 'New Survey',
    questions: [],
    ai_generate_questions: false,
    target_personas: 'all',
  } as CreateSurveyNodeConfig,

  run_focus_group: {
    focus_group_title: 'New Focus Group',
    topics: [],
    moderator_style: 'neutral',
    rounds: 3,
  } as RunFocusGroupNodeConfig,

  analyze_results: {
    analysis_type: 'summary',
    input_source: 'focus_group',
  } as AnalyzeResultsNodeConfig,

  generate_insights: {
    insight_focus: ['pain_points', 'opportunities'],
    output_format: 'summary',
    include_quotes: true,
  } as GenerateInsightsNodeConfig,

  export_report: {
    report_name: 'Research Report',
    format: 'pdf',
    sections: ['personas', 'survey_results', 'focus_group_summary'],
    include_raw_data: false,
  } as ExportReportNodeConfig,

  create_project: {
    project_name: 'New Project',
  } as CreateProjectNodeConfig,

  compare_groups: {
    group_a_source: '',
    group_b_source: '',
    comparison_metrics: [],
  } as CompareGroupsNodeConfig,

  filter_data: {
    filter_expression: 'true',
    data_source: '',
  } as FilterDataNodeConfig,

  loop_start: {
    iteration_variable: 'item',
    items_source: 'items',
    max_iterations: 100,
  } as LoopStartNodeConfig,

  loop_end: {
    loop_start_node_id: '',
  } as LoopEndNodeConfig,
};
