/**
 * TanStack Query hooks dla operacji CRUD na workflows
 *
 * Zapewnia reaktywne zarządzanie stanem dla workflows:
 * - Query hooks (useWorkflows, useWorkflow)
 * - Mutation hooks (useCreateWorkflow, useUpdateWorkflow, useDeleteWorkflow, useDuplicateWorkflow)
 * - Optimistic updates dla lepszego UX
 *
 * @example
 * // Lista workflows
 * const { data: workflows, isLoading } = useWorkflows(projectId);
 *
 * @example
 * // Utwórz workflow
 * const { mutate: createWorkflow } = useCreateWorkflow();
 * createWorkflow({ name: "My Workflow", project_id: projectId });
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/lib/api';
import type {
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
} from '@/types';

// ============================================
// QUERY KEYS (for cache management)
// ============================================

/**
 * Hierarchical query keys dla workflow cache management
 *
 * Struktura:
 * - ['workflows'] - root key
 * - ['workflows', 'list'] - all list queries
 * - ['workflows', 'list', { projectId }] - filtered lists
 * - ['workflows', 'detail'] - all detail queries
 * - ['workflows', 'detail', workflowId] - single workflow
 * - ['workflows', 'detail', workflowId, 'executions'] - execution history
 * - ['workflow-templates'] - templates (separate namespace)
 */
export const workflowKeys = {
  all: ['workflows'] as const,
  lists: () => [...workflowKeys.all, 'list'] as const,
  list: (projectId?: string, includeTemplates = false) =>
    [...workflowKeys.lists(), { projectId, includeTemplates }] as const,
  details: () => [...workflowKeys.all, 'detail'] as const,
  detail: (id: string) => [...workflowKeys.details(), id] as const,
  executions: (workflowId: string) =>
    [...workflowKeys.detail(workflowId), 'executions'] as const,
  templates: () => ['workflow-templates'] as const,
};

// ============================================
// QUERY HOOKS (GET requests)
// ============================================

/**
 * Hook do pobierania listy workflows
 *
 * @param projectId - Filter po projekcie (optional)
 * @param includeTemplates - Czy dołączyć system templates (default: false)
 * @param enabled - Czy query ma być active (default: true if projectId provided)
 *
 * @returns TanStack Query result z listą workflows
 *
 * @example
 * const { data: workflows, isLoading, error } = useWorkflows(projectId);
 *
 * @example
 * // Wszystkie workflows użytkownika
 * const { data: allWorkflows } = useWorkflows();
 */
export function useWorkflows(
  projectId?: string,
  includeTemplates = false,
  enabled = true
) {
  return useQuery({
    queryKey: workflowKeys.list(projectId, includeTemplates),
    queryFn: async () => {
      return workflowsApi.list(projectId, includeTemplates);
    },
    enabled: enabled,
    staleTime: 2 * 60 * 1000, // 2 min (workflows change frequently)
  });
}

/**
 * Hook do pobierania pojedynczego workflow
 *
 * @param workflowId - UUID workflow
 * @param enabled - Czy query ma być active (default: true if workflowId provided)
 *
 * @returns TanStack Query result z workflow data
 *
 * @example
 * const { data: workflow, isLoading } = useWorkflow(workflowId);
 *
 * @example
 * // Conditional loading
 * const { data: workflow } = useWorkflow(workflowId, !!workflowId);
 */
export function useWorkflow(workflowId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: workflowKeys.detail(workflowId!),
    queryFn: async () => {
      if (!workflowId) throw new Error('workflowId is required');
      return workflowsApi.get(workflowId);
    },
    enabled: !!workflowId && enabled,
    staleTime: 1 * 60 * 1000, // 1 min (active workflows change often)
  });
}

// ============================================
// MUTATION HOOKS (POST/PUT/DELETE requests)
// ============================================

/**
 * Hook do tworzenia nowego workflow
 *
 * Po sukcesie:
 * - Invaliduje list queries (odświeża listę)
 * - Dodaje nowy workflow do cache
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: createWorkflow, isPending } = useCreateWorkflow();
 *
 * createWorkflow(
 *   {
 *     name: "Product Research",
 *     project_id: projectId,
 *     canvas_data: { nodes: [], edges: [] }
 *   },
 *   {
 *     onSuccess: (workflow) => {
 *       toast.success(`Workflow "${workflow.name}" created!`);
 *       navigate(`/workflows/${workflow.id}`);
 *     },
 *     onError: (error) => {
 *       toast.error(`Failed to create workflow: ${error.message}`);
 *     }
 *   }
 * );
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateWorkflowRequest) => {
      return workflowsApi.create(data);
    },
    onSuccess: (newWorkflow) => {
      // Invalidate all list queries
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });

      // Add to cache
      queryClient.setQueryData(
        workflowKeys.detail(newWorkflow.id),
        newWorkflow
      );
    },
  });
}

/**
 * Hook do aktualizacji workflow (partial update)
 *
 * Po sukcesie:
 * - Aktualizuje cache workflow
 * - Invaliduje list queries
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: updateWorkflow, isPending } = useUpdateWorkflow();
 *
 * updateWorkflow(
 *   {
 *     id: workflowId,
 *     data: {
 *       name: "Product Research v2",
 *       status: "active"
 *     }
 *   },
 *   {
 *     onSuccess: () => toast.success("Workflow updated!"),
 *     onError: (error) => toast.error(error.message)
 *   }
 * );
 */
export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: UpdateWorkflowRequest;
    }) => {
      return workflowsApi.update(id, data);
    },
    onSuccess: (updatedWorkflow) => {
      // Update cache
      queryClient.setQueryData(
        workflowKeys.detail(updatedWorkflow.id),
        updatedWorkflow
      );

      // Invalidate lists (name/status change may affect sorting/filtering)
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
    },
  });
}

/**
 * Hook do usuwania workflow (soft delete)
 *
 * Po sukcesie:
 * - Usuwa workflow z cache
 * - Invaliduje list queries
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: deleteWorkflow, isPending } = useDeleteWorkflow();
 *
 * const handleDelete = () => {
 *   if (confirm('Are you sure?')) {
 *     deleteWorkflow(
 *       workflowId,
 *       {
 *         onSuccess: () => {
 *           toast.success("Workflow deleted!");
 *           navigate('/workflows');
 *         },
 *         onError: (error) => toast.error(error.message)
 *       }
 *     );
 *   }
 * };
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (workflowId: string) => {
      await workflowsApi.delete(workflowId);
      return workflowId;
    },
    onSuccess: (deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: workflowKeys.detail(deletedId) });

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
    },
  });
}

/**
 * Hook do duplikowania workflow
 *
 * Tworzy kopię workflow z tym samym canvas_data ale nową nazwą.
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: duplicateWorkflow } = useDuplicateWorkflow();
 * duplicateWorkflow(workflowId, {
 *   onSuccess: () => toast.success("Workflow duplicated"),
 * });
 */
export function useDuplicateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (workflowId: string) => {
      // Pobierz oryginał
      const original = await workflowsApi.get(workflowId);

      // Utwórz kopię z nową nazwą
      return workflowsApi.create({
        name: `${original.name} (Copy)`,
        description: original.description,
        project_id: original.project_id,
        canvas_data: original.canvas_data,
        status: 'draft',
      });
    },
    onSuccess: (newWorkflow) => {
      // Add to cache
      queryClient.setQueryData(
        workflowKeys.detail(newWorkflow.id),
        newWorkflow
      );

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
    },
  });
}
