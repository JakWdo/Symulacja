import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';

interface UndoDeleteParams {
  projectId: string;
}

export function useUndoDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ projectId }: UndoDeleteParams) => {
      return projectsApi.undoDelete(projectId);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.removeQueries({ queryKey: ['projects', data.project_id] });
      toast.success('Przywrócono projekt', `${data.name ?? 'Projekt'} ponownie dostępny.`);
    },
    onError: (error: Error) => {
      toast.error('Nie udało się przywrócić projektu', error.message);
    },
  });
}
