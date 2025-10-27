import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useActiveProjects() {
  return useQuery({
    queryKey: ['dashboard', 'activeProjects'],
    queryFn: dashboardApi.getActiveProjects,
    staleTime: 30000, // 30s cache
    refetchInterval: 60000, // Auto-refresh every 60s
  });
}
