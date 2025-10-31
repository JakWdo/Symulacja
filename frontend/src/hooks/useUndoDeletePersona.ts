import { useMutation, useQueryClient } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';
import { useTranslation } from 'react-i18next';

interface UndoDeleteParams {
  personaId: string;
}

export function useUndoDeletePersona() {
  const queryClient = useQueryClient();
  const { t } = useTranslation('personas');

  return useMutation({
    mutationFn: async ({ personaId }: UndoDeleteParams) => {
      return personasApi.undoDelete(personaId);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['personas'] });
      queryClient.removeQueries({ queryKey: ['personas', data.persona_id, 'details'] });
      const personaName = data.full_name ?? t('drawer.persona');
      toast.success(
        t('toast.undoSuccess'),
        t('toast.undoSuccessDescription', { name: personaName })
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
