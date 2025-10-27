import { useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api/dashboard';
import { toast } from 'sonner';

export function useExecuteAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (actionId: string) => dashboardApi.executeAction(actionId),
    onSuccess: (result) => {
      if (result.status === 'redirect' && result.redirect_url) {
        toast.success(result.message);
        // For redirect, we'll handle navigation in the component
      } else if (result.status === 'success') {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (error) => {
      toast.error('Failed to execute action');
      console.error('Action execution error:', error);
    },
  });
}
