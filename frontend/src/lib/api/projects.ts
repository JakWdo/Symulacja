import { api } from './client';
import type {
  Project,
  ProjectDeleteResponse,
  ProjectUndoDeleteResponse,
  ProjectDeleteImpact,
} from '@/types';

export interface CreateProjectPayload {
  name: string;
  description?: string | null;
  target_demographics: Record<string, Record<string, number>>;
  target_sample_size: number;
  environment_id?: string | null;
}

export interface ListProjectsFilters {
  teamId?: string;
  environmentId?: string;
}

export const projectsApi = {
  getAll: async (filters?: ListProjectsFilters): Promise<Project[]> => {
    const params: Record<string, string> = {};
    if (filters?.teamId) {
      params.team_id = filters.teamId;
    }
    if (filters?.environmentId) {
      params.environment_id = filters.environmentId;
    }

    const { data } = await api.get<Project[]>('/projects', { params });
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
  delete: async (
    projectId: string,
    reason: string,
    reasonDetail?: string,
  ): Promise<ProjectDeleteResponse> => {
    const { data } = await api.delete<ProjectDeleteResponse>(`/projects/${projectId}`, {
      data: {
        reason,
        reason_detail: reasonDetail,
      },
    });
    return data;
  },
  undoDelete: async (projectId: string): Promise<ProjectUndoDeleteResponse> => {
    const { data } = await api.post<ProjectUndoDeleteResponse>(`/projects/${projectId}/undo-delete`);
    return data;
  },
  getDeleteImpact: async (projectId: string): Promise<ProjectDeleteImpact> => {
    const { data } = await api.get<ProjectDeleteImpact>(`/projects/${projectId}/delete-impact`);
    return data;
  },
};
