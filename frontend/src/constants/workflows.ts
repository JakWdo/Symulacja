/**
 * Constants for Workflows component - status labels, node types, and default values
 */

// Workflow execution statuses
export const WORKFLOW_STATUSES = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export type WorkflowStatus = typeof WORKFLOW_STATUSES[keyof typeof WORKFLOW_STATUSES];

// Status labels (Polish)
export const WORKFLOW_STATUS_LABELS: Record<WorkflowStatus, string> = {
  [WORKFLOW_STATUSES.PENDING]: 'Oczekujący',
  [WORKFLOW_STATUSES.RUNNING]: 'W trakcie',
  [WORKFLOW_STATUSES.COMPLETED]: 'Zakończony',
  [WORKFLOW_STATUSES.FAILED]: 'Błąd',
  [WORKFLOW_STATUSES.CANCELLED]: 'Anulowany',
};

// Node dimensions for layout (from smartPositioning.ts)
export const NODE_DIMENSIONS = {
  DEFAULT_WIDTH: 200,
  DEFAULT_HEIGHT: 80,
  SPACING_X: 250,
  SPACING_Y: 150,
} as const;

// Workflow node types
export const NODE_TYPES = {
  START: 'start',
  END: 'end',
  DECISION: 'decision',
  GENERATE_PERSONAS: 'generate_personas',
  CREATE_SURVEY: 'create_survey',
  RUN_FOCUS_GROUP: 'run_focus_group',
  ANALYZE_RESULTS: 'analyze_results',
  EXPORT_DATA: 'export_data',
} as const;

export type NodeType = typeof NODE_TYPES[keyof typeof NODE_TYPES];

// Node type labels (Polish)
export const NODE_TYPE_LABELS: Record<NodeType, string> = {
  [NODE_TYPES.START]: 'Start',
  [NODE_TYPES.END]: 'Koniec',
  [NODE_TYPES.DECISION]: 'Decyzja',
  [NODE_TYPES.GENERATE_PERSONAS]: 'Generuj persony',
  [NODE_TYPES.CREATE_SURVEY]: 'Utwórz ankietę',
  [NODE_TYPES.RUN_FOCUS_GROUP]: 'Uruchom grupę fokusową',
  [NODE_TYPES.ANALYZE_RESULTS]: 'Analizuj wyniki',
  [NODE_TYPES.EXPORT_DATA]: 'Eksportuj dane',
};

// Workflow polling interval (ms) when execution is running
export const WORKFLOW_POLLING_INTERVAL = 5000;

// Max execution time before timeout warning (ms)
export const WORKFLOW_MAX_EXECUTION_TIME = 1000 * 60 * 30; // 30 minutes
