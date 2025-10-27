import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';

export function useNotifications(unreadOnly: boolean = false, limit: number = 20) {
  return useQuery({
    queryKey: ['dashboard', 'notifications', unreadOnly, limit],
    queryFn: () => dashboardApi.getNotifications(unreadOnly, limit),
    staleTime: 30000, // 30s cache
    refetchInterval: 60000, // Auto-refresh every 60s
  });
}
