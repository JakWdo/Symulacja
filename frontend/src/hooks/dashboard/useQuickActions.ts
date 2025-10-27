import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useQuickActions(limit: number = 4) {
  return useQuery({
    queryKey: ['dashboard', 'quickActions', limit],
    queryFn: () => dashboardApi.getQuickActions(limit),
    staleTime: 30000, // 30s cache
    refetchInterval: 60000, // Auto-refresh every 60s
  });
}
