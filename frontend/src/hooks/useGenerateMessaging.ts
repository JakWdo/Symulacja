import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { personasApi } from '@/lib/api';
import type { PersonaMessagingPayload, PersonaMessagingResponse } from '@/types';
import { toast } from '@/components/ui/toastStore';

interface GenerateMessagingParams extends PersonaMessagingPayload {
  personaId: string;
}

export function useGenerateMessaging() {
  const { t } = useTranslation('personas');

  return useMutation<PersonaMessagingResponse, Error, GenerateMessagingParams>({
    mutationFn: async ({ personaId, ...payload }) => {
      return personasApi.generateMessaging(personaId, payload);
    },
    onError: (error: Error) => {
      toast.error(
        t('toast.messagingError'),
        error.message
      );
    },
  });
}
