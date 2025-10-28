import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';
import type { ProjectDeleteResponse } from '@/types';
import { useUndoDeleteProject } from './useUndoDeleteProject';

interface DeleteProjectParams {
  projectId: string;
  reason: string;
  reasonDetail?: string;
}

/**
 * Hook do usuwania projektu z audytem i kaskadowym usuwaniem
 *
 * Wykorzystuje React Query Mutation do obsługi DELETE request.
 * Po sukcesie invaliduje cache projektów, aby odświeżyć listę.
 * Wyświetla toast z możliwością cofnięcia w ciągu 7 dni.
 *
 * @returns Mutation object z funkcją mutate do wywołania usunięcia
 */
export function useDeleteProject() {
  const queryClient = useQueryClient();
  const undoMutation = useUndoDeleteProject();

  return useMutation<ProjectDeleteResponse, Error, DeleteProjectParams>({
    mutationFn: async ({ projectId, reason, reasonDetail }: DeleteProjectParams) => {
      return projectsApi.delete(projectId, reason, reasonDetail);
    },
    onSuccess: (data) => {
      // Invalidate projects list cache
      queryClient.invalidateQueries({ queryKey: ['projects'], refetchType: 'all' });

      // Remove specific project from cache
      queryClient.removeQueries({
        queryKey: ['projects', data.project_id]
      });

      // Aggressively invalidate personas and focus groups cache
      // Use refetchType: 'all' to force refetch of ALL queries (including inactive)
      // This ensures dashboard charts update immediately after delete
      queryClient.invalidateQueries({ queryKey: ['personas'], refetchType: 'all' });
      queryClient.invalidateQueries({ queryKey: ['focusGroups'], refetchType: 'all' });

      toast.success('Projekt usunięty', data.message, {
        duration: 30000, // 30 seconds to show undo button
        actionLabel: 'Cofnij',
        onAction: () => undoMutation.mutate({ projectId: data.project_id }),
      });
    },
    onError: (error: Error) => {
      console.error('Failed to delete project:', error);
      toast.error(`Nie udało się usunąć projektu: ${error.message}`);
    },
  });
}
