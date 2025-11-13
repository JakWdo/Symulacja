/**
 * Workflow Constants - Centralized workflow configuration constants
 *
 * Contains default node configurations, template metadata, and workflow-related constants.
 * Consolidated from:
 * - types/workflowNodeConfigs.ts (DEFAULT_NODE_CONFIGS)
 * - components/workflows/templateMetadata.ts (TEMPLATE_METADATA, CATEGORY_LABELS, templates)
 */

import {
  Microscope,
  Layers,
  RefreshCw,
  Heart,
  Map,
  ListChecks,
  LucideIcon,
} from 'lucide-react';
import type {
  NodeConfig,
  StartNodeConfig,
  EndNodeConfig,
  DecisionNodeConfig,
  GeneratePersonasNodeConfig,
  CreateSurveyNodeConfig,
  RunFocusGroupNodeConfig,
  AnalyzeResultsNodeConfig,
  GenerateInsightsNodeConfig,
  ExportReportNodeConfig,
  CreateProjectNodeConfig,
  CompareGroupsNodeConfig,
  FilterDataNodeConfig,
  LoopStartNodeConfig,
  LoopEndNodeConfig,
} from '../types/workflowNodeConfigs';

// ==================== DEFAULT NODE CONFIGS ====================

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

// ==================== WORKFLOW TEMPLATES ====================

export type TemplateCategory = 'research' | 'analysis' | 'validation';

export interface TemplateMetadata {
  icon: LucideIcon;
  estimatedTime: string;
  tags: string[];
  category: TemplateCategory;
  color: string; // Border/accent color
}

/**
 * Metadata dla 6 predefiniowanych szablonów workflow
 */
export const TEMPLATE_METADATA: Record<string, TemplateMetadata> = {
  basic_research: {
    icon: Microscope,
    estimatedTime: '~30 min',
    tags: ['Research', 'Quick Start'],
    category: 'research',
    color: '#3b82f6', // blue
  },
  deep_dive: {
    icon: Layers,
    estimatedTime: '~60 min',
    tags: ['Deep Analysis', 'Comprehensive'],
    category: 'research',
    color: '#8b5cf6', // purple
  },
  iterative_validation: {
    icon: RefreshCw,
    estimatedTime: '~45 min',
    tags: ['Iterative', 'Validation'],
    category: 'validation',
    color: '#10b981', // green
  },
  brand_perception: {
    icon: Heart,
    estimatedTime: '~40 min',
    tags: ['Brand', 'Perception'],
    category: 'analysis',
    color: '#ec4899', // pink
  },
  user_journey: {
    icon: Map,
    estimatedTime: '~50 min',
    tags: ['Journey', 'UX'],
    category: 'analysis',
    color: '#f59e0b', // amber
  },
  feature_prioritization: {
    icon: ListChecks,
    estimatedTime: '~35 min',
    tags: ['Prioritization', 'Decision'],
    category: 'analysis',
    color: '#14b8a6', // teal
  },
};

/**
 * Helper - pobiera metadata dla template
 */
export function getTemplateMetadata(
  templateId: string
): TemplateMetadata | undefined {
  return TEMPLATE_METADATA[templateId];
}

/**
 * Category labels dla UI
 */
export const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  research: 'Research',
  analysis: 'Analysis',
  validation: 'Validation',
};

/**
 * Workflow Templates dla tabs UI (Figma design)
 *
 * WAŻNE: IDs muszą być zsynchronizowane z backendem!
 * Backend templates: app/services/workflows/templates/template_crud.py (TEMPLATES dict)
 *
 * Używamy underscores (nie dashes) aby pasować do backend template IDs.
 */
export interface WorkflowTemplateCard {
  id: string;
  name: string;
  description: string;
  category?: string;
  nodeCount: number;
}

export const WORKFLOW_TEMPLATES: WorkflowTemplateCard[] = [
  {
    id: 'basic_research',
    name: 'Basic Research',
    description:
      'Prosty przepływ badawczy: personas → survey → analiza. Idealny dla początkujących.',
    category: 'Research',
    nodeCount: 5,
  },
  {
    id: 'deep_dive',
    name: 'Deep Dive Research',
    description:
      'Głęboka analiza z focus group: personas → survey → focus group → analiza. Dla zaawansowanych badań.',
    category: 'Research',
    nodeCount: 6,
  },
  {
    id: 'iterative_validation',
    name: 'Iterative Validation',
    description:
      'Iteracja z decision points: sprawdź positive feedback, jeśli <70% → generuj więcej person. Dla testów A/B.',
    category: 'Validation',
    nodeCount: 5,
  },
  {
    id: 'brand_perception',
    name: 'Brand Perception Study',
    description:
      'Badanie percepcji marki: personas → survey (brand awareness + sentiment) → analiza. Dla działów marketingu.',
    category: 'Brand',
    nodeCount: 5,
  },
  {
    id: 'user_journey',
    name: 'User Journey Mapping',
    description:
      'Customer journey analysis: personas → focus group (journey topics) → analiza → export PDF. Dla UX/product teams.',
    category: 'UX',
    nodeCount: 6,
  },
  {
    id: 'feature_prioritization',
    name: 'Feature Prioritization',
    description:
      'Feature voting + prioritization: personas → survey (feature rating) → analiza → decision (top 3 features) → end. Dla product teams.',
    category: 'Product',
    nodeCount: 6,
  },
];
