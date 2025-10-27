import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useWeeklyCompletion(weeks: number = 8) {
  return useQuery({
    queryKey: ['dashboard', 'weeklyCompletion', weeks],
    queryFn: () => dashboardApi.getWeeklyCompletion(weeks),
    staleTime: 60000, // 1 min cache (less frequent updates)
  });
}
