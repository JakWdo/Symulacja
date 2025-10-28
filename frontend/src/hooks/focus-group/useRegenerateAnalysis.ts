import { useMutation, useQueryClient } from '@tanstack/react-query';
import { analysisApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';
import type { AISummary } from '@/types';

/**
 * Hook do regeneracji analizy AI dla focus group
 *
 * @returns Mutation hook do generowania AI summary
 */
export function useRegenerateAnalysis() {
  const queryClient = useQueryClient();

  return useMutation<AISummary, Error, { focusGroupId: string; useProModel?: boolean }>({
    mutationFn: ({ focusGroupId, useProModel = false }) =>
      analysisApi.generateAISummary(focusGroupId, useProModel, true),
    onSuccess: (data, variables) => {
      // Invalidate cache dla tego focus group
      queryClient.setQueryData(
        ['focus-group', variables.focusGroupId, 'ai-summary'],
        data
      );
      queryClient.invalidateQueries({
        queryKey: ['focus-group', variables.focusGroupId, 'ai-summary'],
      });
      toast.success(
        'Analiza AI została wygenerowana',
        'Podsumowanie zostało pomyślnie utworzone'
      );
    },
    onError: (error) => {
      console.error('Failed to generate AI summary:', error);
      toast.error(
        'Nie udało się wygenerować analizy',
        error.message || 'Spróbuj ponownie później'
      );
    },
  });
}
