/**
 * TypeScript interfaces dla Workflow Builder API
 *
 * Mapuje backend schemas z app/schemas/workflow.py do TypeScript types.
 * Używane przez TanStack Query hooks i React komponenty.
 */

// ==================== WORKFLOW TYPES ====================

/**
 * Workflow Status - stan workflow w systemie
 */
export type WorkflowStatus = 'draft' | 'active' | 'archived';

/**
 * Workflow - główna encja workflow builder
 */
export interface Workflow {
  id: string;
  project_id: string;
  owner_id: string;
  name: string;
  description: string | null;
  canvas_data: CanvasData;
  status: WorkflowStatus;
  is_template: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Canvas Data - reprezentacja React Flow canvas
 */
export interface CanvasData {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

/**
 * Workflow Node - pojedynczy węzeł w workflow
 */
export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  position: NodePosition;
  data: NodeData;
}

/**
 * Node Position - pozycja węzła na canvas
 */
export interface NodePosition {
  x: number;
  y: number;
}

/**
 * Node Data - dane węzła
 */
export interface NodeData {
  label: string;
  config: Record<string, any>; // Specific config per node type
}

/**
 * Workflow Node Types - wszystkie dostępne typy węzłów (14 typów)
 *
 * Mapuje backend WorkflowStepTypeEnum z app/models/workflow.py
 */
export type WorkflowNodeType =
  // Control Flow
  | 'start'
  | 'end'
  | 'decision'
  | 'loop_start'
  | 'loop_end'
  // Data Generation
  | 'create_project'
  | 'generate_personas'
  | 'create_survey'
  // Analysis
  | 'run_focus_group'
  | 'analyze_results'
  | 'generate_insights'
  | 'compare_groups'
  // Output
  | 'filter_data'
  | 'export_report';

/**
 * Workflow Edge - połączenie między węzłami
 */
export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: string;
}

// ==================== EXECUTION TYPES ====================

/**
 * Execution Status - stan wykonania workflow
 */
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed';

/**
 * Workflow Execution - record wykonania workflow
 */
export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  triggered_by: string;
  status: ExecutionStatus;
  current_step_id: string | null;
  result_data: Record<string, any> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// ==================== VALIDATION TYPES ====================

/**
 * Validation Result - wynik walidacji workflow
 */
export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

// ==================== TEMPLATE TYPES ====================

/**
 * Workflow Template - predefiniowany workflow template
 */
export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  node_count: number;
  estimated_time_minutes: number | null;
  canvas_data: CanvasData;
  tags: string[];
}

// ==================== REQUEST TYPES ====================

/**
 * Create Workflow Request
 */
export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  project_id: string;
  canvas_data?: CanvasData;
}

/**
 * Update Workflow Request - wszystkie pola opcjonalne
 */
export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  canvas_data?: CanvasData;
  status?: WorkflowStatus;
}

/**
 * Save Canvas Request - tylko canvas_data
 */
export interface SaveCanvasRequest {
  canvas_data: CanvasData;
}

/**
 * Execute Workflow Request
 */
export interface ExecuteWorkflowRequest {
  execution_mode?: 'sequential' | 'parallel';
}

/**
 * Instantiate Template Request
 */
export interface InstantiateTemplateRequest {
  project_id: string;
  workflow_name?: string;
}

// ==================== RESPONSE TYPES ====================

/**
 * Delete Workflow Response
 */
export interface DeleteWorkflowResponse {
  message: string;
}

// ==================== HELPER TYPES ====================

/**
 * Workflow List Filters
 */
export interface WorkflowListFilters {
  project_id?: string;
  include_templates?: boolean;
  status?: WorkflowStatus;
}
