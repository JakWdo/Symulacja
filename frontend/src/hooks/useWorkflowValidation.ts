/**
 * TanStack Query hooks dla walidacji i zapisu canvas workflow
 *
 * Zapewnia reaktywne zarządzanie walidacją i auto-save workflow:
 * - Mutation hooks (useValidateWorkflow, useSaveCanvas)
 * - Optimistic updates dla auto-save (silent background operation)
 *
 * @example
 * // Waliduj workflow przed wykonaniem
 * const { mutate: validate, data: validationResult } = useValidateWorkflow();
 * validate(workflowId, {
 *   onSuccess: (result) => {
 *     if (result.is_valid) {
 *       execute(workflowId);
 *     } else {
 *       toast.error(`Validation failed: ${result.errors.join(', ')}`);
 *     }
 *   }
 * });
 *
 * @example
 * // Auto-save canvas (debounced)
 * import { useDebouncedCallback } from 'use-debounce';
 *
 * const { mutate: saveCanvas } = useSaveCanvas();
 * const debouncedSave = useDebouncedCallback(
 *   (canvasData) => saveCanvas({ workflowId, canvasData }),
 *   1000
 * );
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/lib/api';
import type { CanvasData } from '@/types';
import { workflowKeys } from './useWorkflowCrud';

// ============================================
// MUTATION HOOKS (POST/PUT requests)
// ============================================

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
