import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useInsightAnalytics() {
  return useQuery({
    queryKey: ['dashboard', 'insightAnalytics'],
    queryFn: dashboardApi.getInsightAnalytics,
    staleTime: 60000, // 1 min cache
  });
}
