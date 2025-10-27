import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useInsightDetail(insightId: string | null) {
  return useQuery({
    queryKey: ['dashboard', 'insightDetail', insightId],
    queryFn: () => dashboardApi.getInsightDetail(insightId!),
    enabled: !!insightId,
    staleTime: 300000, // 5 min cache (details don't change often)
  });
}
