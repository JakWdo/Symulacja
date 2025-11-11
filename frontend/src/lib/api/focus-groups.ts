import { api } from './client';
import type {
  FocusGroup,
  FocusGroupInsights,
  FocusGroupResponses,
  PersonaInsight,
  AISummary,
  MetricExplanationsResponse,
  HealthCheck,
  AdvancedInsights,
  BusinessInsights,
  PersonaReasoning,
} from '@/types';

export interface CreateFocusGroupPayload {
  name: string;
  description?: string | null;
  project_context?: string | null;
  persona_ids: string[];
  questions: string[];
  mode: 'normal' | 'adversarial';
}

export const focusGroupsApi = {
  getByProject: async (projectId: string): Promise<FocusGroup[]> => {
    const { data } = await api.get<FocusGroup[]>(
      `/projects/${projectId}/focus-groups`,
    );
    return data;
  },
  get: async (focusGroupId: string): Promise<FocusGroup> => {
    const { data } = await api.get<FocusGroup>(
      `/focus-groups/${focusGroupId}`,
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
  update: async (
    focusGroupId: string,
    payload: Partial<CreateFocusGroupPayload>,
  ): Promise<FocusGroup> => {
    const { data } = await api.put<FocusGroup>(
      `/focus-groups/${focusGroupId}`,
      payload,
    );
    return data;
  },
  remove: async (focusGroupId: string): Promise<void> => {
    await api.delete(`/focus-groups/${focusGroupId}`);
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
    const { data} = await api.get<PersonaInsight>(
      `/personas/${personaId}/insights`,
    );
    return data;
  },
  getPersonaReasoning: async (personaId: string): Promise<PersonaReasoning> => {
    const { data } = await api.get<PersonaReasoning>(
      `/personas/${personaId}/reasoning`,
    );
    return data;
  },
  // Enhanced Insights v2 API
  getAISummary: async (
    focusGroupId: string
  ): Promise<AISummary> => {
    const { data } = await api.get<AISummary>(
      `/focus-groups/${focusGroupId}/ai-summary`
    );
    return data;
  },
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
  getFocusGroupResponses: async (
    focusGroupId: string
  ): Promise<{ focus_group_id: string; total_responses: number; questions: any[] }> => {
    const { data } = await api.get(
      `/focus-groups/${focusGroupId}/responses`
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
