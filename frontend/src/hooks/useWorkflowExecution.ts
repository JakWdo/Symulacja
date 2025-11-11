/**
 * TanStack Query hooks dla wykonywania workflows
 *
 * Zapewnia reaktywne zarządzanie stanem wykonań workflow:
 * - Query hooks (useWorkflowExecutions)
 * - Mutation hooks (useExecuteWorkflow)
 * - Helper hooks (useWorkflowStatus)
 * - Auto-polling dla running executions
 *
 * @example
 * // Historia wykonań
 * const { data: executions, isLoading } = useWorkflowExecutions(workflowId);
 *
 * @example
 * // Wykonaj workflow
 * const { mutate: execute, isPending } = useExecuteWorkflow();
 * execute({ workflowId, options: { execution_mode: 'sequential' } });
 *
 * @example
 * // Sprawdź status workflow + executions
 * const { workflow, executions, isRunning } = useWorkflowStatus(workflowId);
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/lib/api';
import type {
  WorkflowExecution,
  ExecuteWorkflowRequest,
} from '@/types';
import { workflowKeys } from './useWorkflowCrud';
import { useWorkflow } from './useWorkflowCrud';

// ============================================
// QUERY HOOKS (GET requests)
// ============================================

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

// ============================================
// MUTATION HOOKS (POST requests)
// ============================================

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
