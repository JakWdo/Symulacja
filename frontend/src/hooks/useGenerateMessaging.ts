import { useMutation } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import type { PersonaMessagingPayload, PersonaMessagingResponse } from '@/types';
import { toast } from '@/components/ui/toastStore';

interface GenerateMessagingParams extends PersonaMessagingPayload {
  personaId: string;
}

export function useGenerateMessaging() {
  return useMutation<PersonaMessagingResponse, Error, GenerateMessagingParams>({
    mutationFn: async ({ personaId, ...payload }) => {
      return personasApi.generateMessaging(personaId, payload);
    },
    onError: (error: Error) => {
      toast.error('Nie udało się wygenerować komunikacji', error.message);
    },
  });
}
