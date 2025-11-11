/**
 * TanStack Query hooks dla workflow templates
 *
 * Zapewnia reaktywne zarządzanie stanem szablonów workflow:
 * - Query hooks (useWorkflowTemplates)
 * - Mutation hooks (useInstantiateTemplate)
 *
 * @example
 * // Lista templates
 * const { data: templates, isLoading } = useWorkflowTemplates();
 *
 * @example
 * // Utwórz workflow z template
 * const { mutate: instantiateTemplate } = useInstantiateTemplate();
 * instantiateTemplate({
 *   templateId: "template_123",
 *   data: { project_id: projectId, workflow_name: "My Research" }
 * });
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/lib/api';
import type { InstantiateTemplateRequest } from '@/types';
import { workflowKeys } from './useWorkflowCrud';

// ============================================
// QUERY HOOKS (GET requests)
// ============================================

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
// MUTATION HOOKS (POST requests)
// ============================================

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
