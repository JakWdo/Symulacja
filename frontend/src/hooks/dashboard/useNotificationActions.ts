import { useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';
import { toast } from 'sonner';

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => dashboardApi.markNotificationRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'notifications'] });
    },
    onError: (error) => {
      toast.error('Failed to mark notification as read');
      console.error('Notification read error:', error);
    },
  });
}

export function useMarkNotificationDone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => dashboardApi.markNotificationDone(notificationId),
    onSuccess: () => {
      toast.success('Notification marked as done');
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'notifications'] });
    },
    onError: (error) => {
      toast.error('Failed to mark notification as done');
      console.error('Notification done error:', error);
    },
  });
}
