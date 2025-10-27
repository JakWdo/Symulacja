import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useDashboardOverview() {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: dashboardApi.getOverview,
    staleTime: 30000, // 30s cache
    refetchInterval: 60000, // Auto-refresh every 60s
  });
}
