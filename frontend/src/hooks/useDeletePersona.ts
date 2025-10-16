import { useMutation, useQueryClient } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';
import type { PersonaDeleteResponse } from '@/types';
import { useUndoDeletePersona } from './useUndoDeletePersona';

interface DeletePersonaParams {
  personaId: string;
  reason: string;
  reasonDetail?: string;
}

/**
 * Hook do usuwania persony z audytem
 *
 * Wykorzystuje React Query Mutation do obsługi DELETE request.
 * Po sukcesie invaliduje cache person, aby odświeżyć listę.
 *
 * @returns Mutation object z funkcją mutate do wywołania usunięcia
 */
export function useDeletePersona() {
  const queryClient = useQueryClient();
  const undoMutation = useUndoDeletePersona();

  return useMutation<PersonaDeleteResponse, Error, DeletePersonaParams>({
    mutationFn: async ({ personaId, reason, reasonDetail }: DeletePersonaParams) => {
      return personasApi.delete(personaId, reason, reasonDetail);
    },
    onSuccess: (data) => {
      // Invalidate personas list cache
      queryClient.invalidateQueries({ queryKey: ['personas'] });

      // Remove specific persona from cache
      queryClient.removeQueries({
        queryKey: ['personas', data.persona_id, 'details']
      });

      toast.success('Persona usunięta', data.message, {
        duration: 30000,
        actionLabel: 'Cofnij',
        onAction: () => undoMutation.mutate({ personaId: data.persona_id }),
      });
    },
    onError: (error: Error) => {
      console.error('Failed to delete persona:', error);
      toast.error(`Failed to delete persona: ${error.message}`);
    },
  });
}
