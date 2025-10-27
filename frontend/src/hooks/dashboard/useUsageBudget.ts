import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useUsageBudget() {
  return useQuery({
    queryKey: ['dashboard', 'usageBudget'],
    queryFn: dashboardApi.getUsageBudget,
    staleTime: 60000, // 1 min cache
  });
}
