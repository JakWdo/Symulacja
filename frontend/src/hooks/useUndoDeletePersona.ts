import { useMutation, useQueryClient } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';

interface UndoDeleteParams {
  personaId: string;
}

export function useUndoDeletePersona() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ personaId }: UndoDeleteParams) => {
      return personasApi.undoDelete(personaId);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['personas'] });
      queryClient.removeQueries({ queryKey: ['personas', data.persona_id, 'details'] });
      toast.success('Przywrócono personę', `${data.full_name ?? 'Persona'} ponownie dostępna.`);
    },
    onError: (error: Error) => {
      toast.error('Nie udało się przywrócić persony', error.message);
    },
  });
}
