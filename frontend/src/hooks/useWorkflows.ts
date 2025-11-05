/**
 * TanStack Query hooks dla Workflow Builder API
 *
 * Zapewnia reaktywne zarządzanie stanem dla workflows:
 * - Query hooks (useWorkflows, useWorkflow, useWorkflowExecutions, useWorkflowTemplates)
 * - Mutation hooks (useCreateWorkflow, useUpdateWorkflow, useDeleteWorkflow, etc.)
 * - Optimistic updates dla lepszego UX
 * - Auto-polling dla running executions
 *
 * @example
 * // Lista workflows
 * const { data: workflows, isLoading } = useWorkflows(projectId);
 *
 * @example
 * // Utwórz workflow
 * const { mutate: createWorkflow } = useCreateWorkflow();
 * createWorkflow({ name: "My Workflow", project_id: projectId });
 *
 * @example
 * // Auto-save canvas (debounced)
 * const { mutate: saveCanvas } = useSaveCanvas();
 * const debouncedSave = useDebouncedCallback(
 *   (canvasData) => saveCanvas({ workflowId, canvasData }),
 *   1000
 * );
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/lib/api';
import type {
  WorkflowExecution,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  CanvasData,
  ExecuteWorkflowRequest,
  InstantiateTemplateRequest,
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

/**
 * Hook do pobierania historii wykonań workflow
 *
 * Automatycznie polluje co 2s jeśli jest running execution.
 *
 * @param workflowId - UUID workflow
 * @param enabled - Czy query ma być active (default: true if workflowId provided)
 *
 * @returns TanStack Query result z listą executions
 *
 * @example
 * const { data: executions, isLoading } = useWorkflowExecutions(workflowId);
 *
 * @example
 * // Sprawdź czy jest running execution
 * const { data: executions } = useWorkflowExecutions(workflowId);
 * const isRunning = executions?.some(e => e.status === 'running');
 */
export function useWorkflowExecutions(
  workflowId: string | undefined,
  enabled = true
) {
  return useQuery({
    queryKey: workflowKeys.executions(workflowId!),
    queryFn: async () => {
      if (!workflowId) throw new Error('workflowId is required');
      return workflowsApi.getExecutions(workflowId);
    },
    enabled: !!workflowId && enabled,
    staleTime: 0, // Always fresh (executions update frequently)
    refetchInterval: (query) => {
      // Poll co 2s jeśli jest running execution
      const hasRunning = query.state.data?.some((e: WorkflowExecution) => e.status === 'running');
      return hasRunning ? 2000 : false;
    },
  });
}

/**
 * Hook do pobierania workflow templates
 *
 * Templates są cache'owane na 5 min (zmian się rzadko).
 *
 * @returns TanStack Query result z listą templates
 *
 * @example
 * const { data: templates, isLoading } = useWorkflowTemplates();
 */
export function useWorkflowTemplates() {
  return useQuery({
    queryKey: workflowKeys.templates(),
    queryFn: async () => {
      return workflowsApi.getTemplates();
    },
    staleTime: 5 * 60 * 1000, // 5 min (templates rarely change)
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
 * Hook do quick save canvas state (optimizacja dla auto-save)
 *
 * Używaj z debounce dla auto-save functionality.
 * Silent update - nie invaliduje queries, tylko aktualizuje cache.
 *
 * @returns TanStack Query mutation
 *
 * @example
 * import { useDebouncedCallback } from 'use-debounce';
 *
 * const { mutate: saveCanvas } = useSaveCanvas();
 *
 * const debouncedSave = useDebouncedCallback(
 *   (canvasData: CanvasData) => {
 *     saveCanvas({ workflowId, canvasData });
 *   },
 *   1000 // 1s debounce
 * );
 *
 * // W React Flow onChange handler
 * const onNodesChange = useCallback((changes) => {
 *   const newNodes = applyNodeChanges(changes, nodes);
 *   setNodes(newNodes);
 *   debouncedSave({ nodes: newNodes, edges });
 * }, [nodes, edges, debouncedSave]);
 */
export function useSaveCanvas() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      workflowId,
      canvasData,
    }: {
      workflowId: string;
      canvasData: CanvasData;
    }) => {
      return workflowsApi.saveCanvas(workflowId, canvasData);
    },
    onSuccess: (updatedWorkflow) => {
      // Silent update - tylko cache, bez invalidation (no refetch)
      queryClient.setQueryData(
        workflowKeys.detail(updatedWorkflow.id),
        updatedWorkflow
      );
    },
    // No toast notification for auto-save (silent background operation)
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
 * Hook do walidacji workflow przed execution
 *
 * Nie modyfikuje cache - zwraca tylko validation result.
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: validate, isPending: isValidating } = useValidateWorkflow();
 *
 * const handleValidateAndExecute = () => {
 *   validate(
 *     workflowId,
 *     {
 *       onSuccess: (result) => {
 *         if (result.is_valid) {
 *           execute(workflowId);
 *         } else {
 *           toast.error(
 *             `Validation failed: ${result.errors.join(', ')}`
 *           );
 *           if (result.warnings.length > 0) {
 *             toast.warning(`Warnings: ${result.warnings.join(', ')}`);
 *           }
 *         }
 *       },
 *       onError: (error) => toast.error(error.message)
 *     }
 *   );
 * };
 */
export function useValidateWorkflow() {
  return useMutation({
    mutationFn: async (workflowId: string) => {
      return workflowsApi.validate(workflowId);
    },
    // No cache updates (validation is read-only operation)
  });
}

/**
 * Hook do wykonania workflow
 *
 * UWAGA: Długo działająca operacja (może trwać 3-10 minut).
 *
 * Po sukcesie:
 * - Invaliduje executions list (nowe execution dodane)
 * - Rozpoczyna auto-polling (useWorkflowExecutions hook to obsługuje)
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: execute, isPending: isExecuting } = useExecuteWorkflow();
 *
 * const handleExecute = () => {
 *   execute(
 *     workflowId,
 *     {
 *       onSuccess: (execution) => {
 *         toast.success(`Workflow started! Execution ID: ${execution.id}`);
 *         // Auto-polling handled by useWorkflowExecutions hook
 *       },
 *       onError: (error) => {
 *         toast.error(`Execution failed: ${error.message}`);
 *       }
 *     }
 *   );
 * };
 *
 * @example
 * // With execution options
 * execute(
 *   { workflowId, options: { execution_mode: 'sequential' } },
 *   { onSuccess: ... }
 * );
 */
export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      workflowId,
      options,
    }: {
      workflowId: string;
      options?: ExecuteWorkflowRequest;
    }) => {
      return workflowsApi.execute(workflowId, options);
    },
    onSuccess: (execution) => {
      // Invalidate executions list (new execution added)
      queryClient.invalidateQueries({
        queryKey: workflowKeys.executions(execution.workflow_id),
      });

      // Auto-polling starts automatically (useWorkflowExecutions refetchInterval)
    },
  });
}

/**
 * Hook do tworzenia workflow z template
 *
 * Po sukcesie:
 * - Dodaje nowy workflow do cache
 * - Invaliduje list queries
 *
 * @returns TanStack Query mutation
 *
 * @example
 * const { mutate: instantiateTemplate, isPending } = useInstantiateTemplate();
 *
 * const handleUseTemplate = (templateId: string) => {
 *   instantiateTemplate(
 *     {
 *       templateId,
 *       data: {
 *         project_id: projectId,
 *         workflow_name: "My Product Research"
 *       }
 *     },
 *     {
 *       onSuccess: (workflow) => {
 *         toast.success(`Workflow created from template!`);
 *         navigate(`/workflows/${workflow.id}`);
 *       },
 *       onError: (error) => {
 *         toast.error(`Failed to create workflow: ${error.message}`);
 *       }
 *     }
 *   );
 * };
 */
export function useInstantiateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      templateId,
      data,
    }: {
      templateId: string;
      data: InstantiateTemplateRequest;
    }) => {
      return workflowsApi.instantiateTemplate(templateId, data);
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

// ============================================
// HELPER HOOKS (convenience wrappers)
// ============================================

/**
 * Hook do sprawdzenia czy workflow ma running execution
 *
 * Convenience wrapper - łączy useWorkflow + useWorkflowExecutions.
 *
 * @param workflowId - UUID workflow
 *
 * @returns Object z workflow data i execution status
 *
 * @example
 * const { workflow, executions, isRunning, isLoading } =
 *   useWorkflowStatus(workflowId);
 *
 * return (
 *   <div>
 *     <h1>{workflow?.name}</h1>
 *     {isRunning && <Badge>Running...</Badge>}
 *     {executions?.map(e => <ExecutionCard key={e.id} execution={e} />)}
 *   </div>
 * );
 */
export function useWorkflowStatus(workflowId: string | undefined) {
  const {
    data: workflow,
    isLoading: workflowLoading,
    error: workflowError,
  } = useWorkflow(workflowId);

  const {
    data: executions,
    isLoading: executionsLoading,
    error: executionsError,
  } = useWorkflowExecutions(workflowId);

  const isRunning = executions?.some((e) => e.status === 'running') || false;
  const latestExecution = executions?.[0]; // Executions sorted by started_at desc

  return {
    workflow,
    executions,
    latestExecution,
    isRunning,
    isLoading: workflowLoading || executionsLoading,
    error: workflowError || executionsError,
  };
}
