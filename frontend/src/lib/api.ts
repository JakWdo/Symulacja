import axios from 'axios';
import type {
  Project,
  Persona,
  FocusGroup,
  PolarizationAnalysis,
  FocusGroupResponses,
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
  persona_ids: string[];
  questions: string[];
  mode: 'normal' | 'adversarial';
}

export interface GeneratePersonasPayload {
  num_personas: number;
  adversarial_mode: boolean;
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
  analyzePolarization: async (
    focusGroupId: string,
  ): Promise<PolarizationAnalysis> => {
    const { data } = await api.post<PolarizationAnalysis>(
      `/focus-groups/${focusGroupId}/analyze-polarization`,
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
};
