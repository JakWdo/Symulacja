import { useQuery } from '@tanstack/react-query';
import { analysisApi } from '@/lib/api';
import type { AISummary } from '@/types';

/**
 * Hook do pobierania analizy AI dla focus group
 *
 * @param focusGroupId - ID grupy fokusowej
 * @returns Query result z danymi AI summary
 */
export function useFocusGroupAnalysis(focusGroupId: string) {
  return useQuery<AISummary>({
    queryKey: ['focus-group', focusGroupId, 'ai-summary'],
    queryFn: () => analysisApi.getAISummary(focusGroupId),
    staleTime: 10 * 60 * 1000, // 10 min - AI summary jest immutable po wygenerowaniu
    enabled: !!focusGroupId,
    retry: 1, // Tylko jedna próba przy 404
  });
}
