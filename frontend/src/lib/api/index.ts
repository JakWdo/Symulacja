// Client configuration
export { api } from './client';

// API modules
export { dashboardApi } from './dashboard';
export { personasApi } from './personas';
export { projectsApi } from './projects';
export { focusGroupsApi, analysisApi } from './focus-groups';
export { workflowsApi } from './workflows';
export { authApi, settingsApi } from './auth';
export { surveysApi } from './surveys';
export { ragApi, graphApi } from './rag';

// Types - Projects
export type { CreateProjectPayload } from './projects';

// Types - Personas
export type {
  PersonaAdvancedOptions,
  GeneratePersonasPayload,
  GeneratePersonasResponse,
} from './personas';

// Types - Focus Groups
export type { CreateFocusGroupPayload } from './focus-groups';

// Types - Auth & Settings
export type {
  User,
  LoginCredentials,
  RegisterData,
  TokenResponse,
  AccountStats,
  BudgetSettings,
  BudgetSettingsUpdate,
} from './auth';
