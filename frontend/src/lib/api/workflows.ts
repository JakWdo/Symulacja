import { api } from './client';
import type {
  Workflow,
  WorkflowExecution,
  ValidationResult,
  WorkflowTemplate,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  ExecuteWorkflowRequest,
  InstantiateTemplateRequest,
  DeleteWorkflowResponse,
  CanvasData,
} from '@/types';

export const workflowsApi = {
  /**
   * Tworzy nowy workflow
   */
  create: async (payload: CreateWorkflowRequest): Promise<Workflow> => {
    const { data } = await api.post<Workflow>('/workflows/', payload);
    return data;
  },

  /**
   * Lista workflows użytkownika
   * @param projectId - Filter po projekcie (optional)
   * @param includeTemplates - Czy dołączyć templates (default: false)
   */
  list: async (
    projectId?: string,
    includeTemplates = false
  ): Promise<Workflow[]> => {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (includeTemplates) params.append('include_templates', 'true');

    const { data } = await api.get<Workflow[]>(
      `/workflows/${params.toString() ? `?${params.toString()}` : ''}`
    );
    return data;
  },

  /**
   * Pobiera workflow po ID
   */
  get: async (workflowId: string): Promise<Workflow> => {
    const { data } = await api.get<Workflow>(`/workflows/${workflowId}`);
    return data;
  },

  /**
   * Aktualizuje workflow (partial update)
   */
  update: async (
    workflowId: string,
    payload: UpdateWorkflowRequest
  ): Promise<Workflow> => {
    const { data } = await api.put<Workflow>(
      `/workflows/${workflowId}`,
      payload
    );
    return data;
  },

  /**
   * Soft delete workflow
   */
  delete: async (workflowId: string): Promise<DeleteWorkflowResponse> => {
    const { data } = await api.delete<DeleteWorkflowResponse>(
      `/workflows/${workflowId}`
    );
    return data;
  },

  /**
   * Quick save canvas state (optimizacja dla auto-save)
   */
  saveCanvas: async (
    workflowId: string,
    canvasData: CanvasData
  ): Promise<Workflow> => {
    const { data } = await api.patch<Workflow>(
      `/workflows/${workflowId}/canvas`,
      { canvas_data: canvasData }
    );
    return data;
  },

  /**
   * Pre-flight validation workflow
   */
  validate: async (workflowId: string): Promise<ValidationResult> => {
    const { data } = await api.post<ValidationResult>(
      `/workflows/${workflowId}/validate`
    );
    return data;
  },

  /**
   * Wykonuje workflow
   * UWAGA: Długo działająca operacja (może trwać 3-10 minut)
   */
  execute: async (
    workflowId: string,
    payload?: ExecuteWorkflowRequest
  ): Promise<WorkflowExecution> => {
    const { data } = await api.post<WorkflowExecution>(
      `/workflows/${workflowId}/execute`,
      payload || {}
    );
    return data;
  },

  /**
   * Pobiera historię wykonań workflow
   */
  getExecutions: async (workflowId: string): Promise<WorkflowExecution[]> => {
    const { data } = await api.get<WorkflowExecution[]>(
      `/workflows/${workflowId}/executions`
    );
    return data;
  },

  /**
   * Pobiera listę workflow templates
   */
  getTemplates: async (): Promise<WorkflowTemplate[]> => {
    const { data } = await api.get<WorkflowTemplate[]>('/workflows/templates');
    return data;
  },

  /**
   * Tworzy workflow z template
   */
  instantiateTemplate: async (
    templateId: string,
    payload: InstantiateTemplateRequest
  ): Promise<Workflow> => {
    const { data } = await api.post<Workflow>(
      `/workflows/templates/${templateId}/instantiate`,
      payload
    );
    return data;
  },
};
