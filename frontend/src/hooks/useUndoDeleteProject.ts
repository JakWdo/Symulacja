import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';
import { useTranslation } from 'react-i18next';

interface UndoDeleteParams {
  projectId: string;
}

export function useUndoDeleteProject() {
  const queryClient = useQueryClient();
  const { t } = useTranslation('projects');

  return useMutation({
    mutationFn: async ({ projectId }: UndoDeleteParams) => {
      return projectsApi.undoDelete(projectId);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.removeQueries({ queryKey: ['projects', data.project_id] });
      const projectName =
        data.name ?? t('delete.unknown');

      toast.success(
        t('toast.undoSuccess'),
        t('toast.undoSuccessDescription', { name: projectName })
      );
    },
    onError: (error: Error) => {
      toast.error(
        t('toast.undoError'),
        error.message || t('toast.undoErrorDescription')
      );
    },
  });
}
