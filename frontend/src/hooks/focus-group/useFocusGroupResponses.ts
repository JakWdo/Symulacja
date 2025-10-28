import { useQuery } from '@tanstack/react-query';
import { focusGroupsApi } from '@/lib/api';
import type { FocusGroupResponses } from '@/types';

/**
 * Hook do pobierania surowych odpowiedzi z focus group
 *
 * @param focusGroupId - ID grupy fokusowej
 * @returns Query result z odpowiedziami uczestników
 */
export function useFocusGroupResponses(focusGroupId: string) {
  return useQuery<FocusGroupResponses>({
    queryKey: ['focus-group', focusGroupId, 'responses'],
    queryFn: () => focusGroupsApi.getResponses(focusGroupId),
    staleTime: 3000, // 3s - odpowiedzi mogą się zmieniać podczas discussion
    enabled: !!focusGroupId,
    refetchOnWindowFocus: true,
  });
}
