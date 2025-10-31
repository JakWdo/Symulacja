import { useMutation, useQueryClient } from '@tanstack/react-query';
import { analysisApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';
import type { AISummary } from '@/types';
import { useTranslation } from 'react-i18next';

/**
 * Hook do regeneracji analizy AI dla focus group
 *
 * @returns Mutation hook do generowania AI summary
 */
export function useRegenerateAnalysis() {
  const queryClient = useQueryClient();
  const { t } = useTranslation('focusGroups');

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
        t('analysis.aiSummary.toastTitle'),
        t('analysis.aiSummary.toastDescription')
      );
    },
    onError: (error) => {
      console.error('Failed to generate AI summary:', error);
      toast.error(
        t('analysis.aiSummary.errorTitle'),
        error.message || t('analysis.aiSummary.errorUnknown')
      );
    },
  });
}
