import axios from 'axios';
import type {
  Project,
  Persona,
  FocusGroup,
  FocusGroupInsights,
  FocusGroupResponses,
  PersonaInsight,
  AISummary,
  MetricExplanationsResponse,
  HealthCheck,
  AdvancedInsights,
  BusinessInsights,
  Survey,
  SurveyResults,
  Question,
} from '@/types';

export interface CreateProjectPayload {
  name: string;
  description?: string | null;
  target_demographics: Record<string, Record<string, number>>;
  target_sample_size: number;
}

export interface CreateFocusGroupPayload {
  name: string;
  description?: string | null;
  project_context?: string | null;
  persona_ids: string[];
  questions: string[];
  mode: 'normal' | 'adversarial';
}

export interface PersonaAdvancedOptions {
  age_focus?: 'balanced' | 'young_adults' | 'experienced_leaders';
  gender_balance?: 'balanced' | 'female_skew' | 'male_skew';
  urbanicity?: 'any' | 'urban' | 'suburban' | 'rural';
  target_cities?: string[];
  target_countries?: string[];
  industries?: string[];
  required_values?: string[];
  excluded_values?: string[];
  required_interests?: string[];
  excluded_interests?: string[];
  age_min?: number;
  age_max?: number;
  custom_age_groups?: Record<string, number>;
  gender_weights?: Record<string, number>;
  location_weights?: Record<string, number>;
  education_weights?: Record<string, number>;
  income_weights?: Record<string, number>;
  personality_skew?: Record<string, number>;
}

export interface GeneratePersonasPayload {
  num_personas: number;
  adversarial_mode: boolean;
  advanced_options?: PersonaAdvancedOptions;
}

const baseUrl = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1`
  : '/api/v1';

const api = axios.create({
  baseURL: baseUrl,
});

export const projectsApi = {
  getAll: async (): Promise<Project[]> => {
    const { data } = await api.get<Project[]>('/projects');
    return data;
  },
  create: async (payload: CreateProjectPayload): Promise<Project> => {
    const { data } = await api.post<Project>('/projects', payload);
    return data;
  },
  get: async (projectId: string): Promise<Project> => {
    const { data } = await api.get<Project>(`/projects/${projectId}`);
    return data;
  },
  update: async (
    projectId: string,
    payload: Partial<CreateProjectPayload>,
  ): Promise<Project> => {
    const { data } = await api.put<Project>(`/projects/${projectId}`, payload);
    return data;
  },
  remove: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}`);
  },
};

export const personasApi = {
  getByProject: async (projectId: string): Promise<Persona[]> => {
    const { data } = await api.get<Persona[]>(
      `/projects/${projectId}/personas`,
    );
    return data;
  },
  generate: async (
    projectId: string,
    payload: GeneratePersonasPayload,
  ): Promise<void> => {
    await api.post(`/projects/${projectId}/personas/generate`, payload);
  },
};

export const focusGroupsApi = {
  getByProject: async (projectId: string): Promise<FocusGroup[]> => {
    const { data } = await api.get<FocusGroup[]>(
      `/projects/${projectId}/focus-groups`,
    );
    return data;
  },
  create: async (
    projectId: string,
    payload: CreateFocusGroupPayload,
  ): Promise<FocusGroup> => {
    const { data } = await api.post<FocusGroup>(
      `/projects/${projectId}/focus-groups`,
      payload,
    );
    return data;
  },
  run: async (focusGroupId: string): Promise<void> => {
    await api.post(`/focus-groups/${focusGroupId}/run`);
  },
  getResponses: async (
    focusGroupId: string,
  ): Promise<FocusGroupResponses> => {
    const { data } = await api.get<FocusGroupResponses>(
      `/focus-groups/${focusGroupId}/responses`,
    );
    return data;
  },
};

export const analysisApi = {
  getInsights: async (focusGroupId: string): Promise<FocusGroupInsights> => {
    const { data } = await api.get<FocusGroupInsights>(
      `/focus-groups/${focusGroupId}/insights`,
    );
    return data;
  },
  generateInsights: async (focusGroupId: string): Promise<FocusGroupInsights> => {
    const { data } = await api.post<FocusGroupInsights>(
      `/focus-groups/${focusGroupId}/insights`,
    );
    return data;
  },
  exportPDF: async (focusGroupId: string): Promise<Blob> => {
    const { data } = await api.get(
      `/focus-groups/${focusGroupId}/export/pdf`,
      { responseType: 'blob' }
    );
    return data;
  },
  exportCSV: async (focusGroupId: string): Promise<Blob> => {
    const { data } = await api.get(
      `/focus-groups/${focusGroupId}/export/csv`,
      { responseType: 'blob' }
    );
    return data;
  },
  getPersonaHistory: async (
    personaId: string,
    limit = 50,
  ): Promise<any> => {
    const { data } = await api.get(
      `/personas/${personaId}/history`,
      { params: { limit } }
    );
    return data;
  },
  getPersonaInsights: async (personaId: string): Promise<PersonaInsight> => {
    const { data } = await api.get<PersonaInsight>(
      `/personas/${personaId}/insights`,
    );
    return data;
  },
  // Enhanced Insights v2 API
  generateAISummary: async (
    focusGroupId: string,
    useProModel = false,
    includeRecommendations = true
  ): Promise<AISummary> => {
    const { data } = await api.post<AISummary>(
      `/focus-groups/${focusGroupId}/ai-summary`,
      {},
      {
        params: {
          use_pro_model: useProModel,
          include_recommendations: includeRecommendations,
        },
      }
    );
    return data;
  },
  getMetricExplanations: async (
    focusGroupId: string
  ): Promise<MetricExplanationsResponse> => {
    const { data } = await api.get<MetricExplanationsResponse>(
      `/focus-groups/${focusGroupId}/metric-explanations`
    );
    return data;
  },
  getHealthCheck: async (focusGroupId: string): Promise<HealthCheck> => {
    const { data } = await api.get<HealthCheck>(
      `/focus-groups/${focusGroupId}/health-check`
    );
    return data;
  },
  getAdvancedInsights: async (
    focusGroupId: string
  ): Promise<AdvancedInsights> => {
    const { data } = await api.get<AdvancedInsights>(
      `/focus-groups/${focusGroupId}/advanced-insights`
    );
    return data;
  },
  exportEnhancedPDF: async (
    focusGroupId: string,
    includeAISummary = true,
    includeAdvancedInsights = true,
    useProModel = false
  ): Promise<Blob> => {
    const { data } = await api.get(
      `/focus-groups/${focusGroupId}/enhanced-report`,
      {
        responseType: 'blob',
        params: {
          include_ai_summary: includeAISummary,
          include_advanced_insights: includeAdvancedInsights,
          use_pro_model: useProModel,
        },
      }
    );
    return data;
  },
  // AI Business Insights (new endpoint)
  generateBusinessInsights: async (
    focusGroupId: string
  ): Promise<BusinessInsights> => {
    const { data } = await api.post<BusinessInsights>(
      `/focus-groups/${focusGroupId}/ai-business-insights`
    );
    return data;
  },
};

// Surveys API
export const surveysApi = {
  getByProject: async (projectId: string): Promise<Survey[]> => {
    const { data } = await api.get<Survey[]>(`/projects/${projectId}/surveys`);
    return data;
  },

  create: async (
    projectId: string,
    payload: {
      title: string;
      description?: string;
      questions: Question[];
      target_responses?: number;
    }
  ): Promise<Survey> => {
    const { data } = await api.post<Survey>(
      `/projects/${projectId}/surveys`,
      payload
    );
    return data;
  },

  get: async (surveyId: string): Promise<Survey> => {
    const { data } = await api.get<Survey>(`/surveys/${surveyId}`);
    return data;
  },

  run: async (surveyId: string): Promise<void> => {
    await api.post(`/surveys/${surveyId}/run`);
  },

  getResults: async (surveyId: string): Promise<SurveyResults> => {
    const { data } = await api.get<SurveyResults>(
      `/surveys/${surveyId}/results`
    );
    return data;
  },

  delete: async (surveyId: string): Promise<void> => {
    await api.delete(`/surveys/${surveyId}`);
  },
};
