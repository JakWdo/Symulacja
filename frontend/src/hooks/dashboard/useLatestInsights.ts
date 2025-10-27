import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useLatestInsights(limit: number = 10) {
  return useQuery({
    queryKey: ['dashboard', 'latestInsights', limit],
    queryFn: () => dashboardApi.getLatestInsights(limit),
    staleTime: 30000, // 30s cache
    refetchInterval: 60000, // Auto-refresh every 60s
  });
}
