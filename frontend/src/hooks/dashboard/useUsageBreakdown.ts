import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useUsageBreakdown() {
  return useQuery({
    queryKey: ['dashboard', 'usageBreakdown'],
    queryFn: dashboardApi.getUsageBreakdown,
    staleTime: 300000, // 5 min cache (changes less frequently)
  });
}
