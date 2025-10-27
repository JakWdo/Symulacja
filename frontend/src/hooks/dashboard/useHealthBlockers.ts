import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useHealthBlockers() {
  return useQuery({
    queryKey: ['dashboard', 'healthBlockers'],
    queryFn: dashboardApi.getHealthBlockers,
    staleTime: 30000, // 30s cache
    refetchInterval: 60000, // Auto-refresh every 60s
  });
}
