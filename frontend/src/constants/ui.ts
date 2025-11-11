/**
 * Constants for UI components - colors, sizes, animations, and common labels
 */

// Focus Group statuses
export const FOCUS_GROUP_STATUSES = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export type FocusGroupStatus = typeof FOCUS_GROUP_STATUSES[keyof typeof FOCUS_GROUP_STATUSES];

// Focus Group status labels (Polish)
export const FOCUS_GROUP_STATUS_LABELS: Record<FocusGroupStatus, string> = {
  [FOCUS_GROUP_STATUSES.PENDING]: 'Oczekująca',
  [FOCUS_GROUP_STATUSES.RUNNING]: 'W trakcie',
  [FOCUS_GROUP_STATUSES.COMPLETED]: 'Zakończona',
  [FOCUS_GROUP_STATUSES.FAILED]: 'Błąd',
};

// Survey statuses
export const SURVEY_STATUSES = {
  DRAFT: 'draft',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  ARCHIVED: 'archived',
} as const;

export type SurveyStatus = typeof SURVEY_STATUSES[keyof typeof SURVEY_STATUSES];

// Survey status labels (Polish)
export const SURVEY_STATUS_LABELS: Record<SurveyStatus, string> = {
  [SURVEY_STATUSES.DRAFT]: 'Szkic',
  [SURVEY_STATUSES.ACTIVE]: 'Aktywna',
  [SURVEY_STATUSES.COMPLETED]: 'Zakończona',
  [SURVEY_STATUSES.ARCHIVED]: 'Zarchiwizowana',
};

// Panel keys for FloatingPanel system
export const PANEL_KEYS = {
  PROJECTS: 'projects',
  PERSONAS: 'personas',
  FOCUS_GROUPS: 'focus-groups',
  ANALYSIS: 'analysis',
  RAG: 'rag',
} as const;

export type PanelKey = typeof PANEL_KEYS[keyof typeof PANEL_KEYS];

// Animation durations (ms)
export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

// Toast durations (ms)
export const TOAST_DURATIONS = {
  SHORT: 3000,
  NORMAL: 5000,
  LONG: 10000,
  INFINITE: Infinity,
} as const;

// Common UI labels (Polish)
export const UI_LABELS = {
  SAVE: 'Zapisz',
  CANCEL: 'Anuluj',
  DELETE: 'Usuń',
  EDIT: 'Edytuj',
  CREATE: 'Utwórz',
  CLOSE: 'Zamknij',
  BACK: 'Wróć',
  NEXT: 'Dalej',
  PREVIOUS: 'Wstecz',
  LOADING: 'Ładowanie...',
  NO_DATA: 'Brak danych',
  ERROR: 'Błąd',
  SUCCESS: 'Sukces',
  CONFIRM: 'Potwierdź',
} as const;

// Personality score thresholds
export const PERSONALITY_THRESHOLDS = {
  HIGH: 0.7,
  MEDIUM: 0.4,
} as const;

// Personality score color classes
export const PERSONALITY_COLORS = {
  HIGH: 'bg-green-100 text-green-700',
  MEDIUM: 'bg-yellow-100 text-yellow-700',
  LOW: 'bg-red-100 text-red-700',
} as const;

// Helper function to get personality color
export function getPersonalityColor(score: number): string {
  if (score >= PERSONALITY_THRESHOLDS.HIGH) return PERSONALITY_COLORS.HIGH;
  if (score >= PERSONALITY_THRESHOLDS.MEDIUM) return PERSONALITY_COLORS.MEDIUM;
  return PERSONALITY_COLORS.LOW;
}

// Graph layouts
export const GRAPH_LAYOUTS = {
  TWO_D: '2d',
  THREE_D: '3d',
} as const;

export type GraphLayout = typeof GRAPH_LAYOUTS[keyof typeof GRAPH_LAYOUTS];

// Default panel positions (for FloatingPanel)
export const DEFAULT_PANEL_POSITIONS = {
  [PANEL_KEYS.PROJECTS]: { x: 80, y: 140 },
  [PANEL_KEYS.PERSONAS]: { x: 440, y: 160 },
  [PANEL_KEYS.FOCUS_GROUPS]: { x: 820, y: 180 },
  [PANEL_KEYS.ANALYSIS]: { x: 1200, y: 160 },
  [PANEL_KEYS.RAG]: { x: 1260, y: 420 },
} as const;

// Default trigger positions (for FloatingPanel triggers)
export const DEFAULT_TRIGGER_POSITIONS = {
  [PANEL_KEYS.PROJECTS]: { x: 40, y: 200 },
  [PANEL_KEYS.PERSONAS]: { x: 40, y: 320 },
  [PANEL_KEYS.FOCUS_GROUPS]: { x: 40, y: 440 },
  [PANEL_KEYS.ANALYSIS]: { x: 40, y: 560 },
  [PANEL_KEYS.RAG]: { x: 40, y: 680 },
} as const;
