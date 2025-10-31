import { useMutation } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import type { PersonaComparisonResponse } from '@/types';
import { toast } from '@/components/ui/toastStore';
import { useTranslation } from 'react-i18next';

interface CompareParams {
  personaId: string;
  personaIds: string[];
  sections?: string[];
}

export function useComparePersonas() {
  const { t } = useTranslation('personas');

  return useMutation<PersonaComparisonResponse, Error, CompareParams>({
    mutationFn: async ({ personaId, personaIds, sections }) => {
      return personasApi.compare(personaId, personaIds, sections);
    },
    onError: (error: Error) => {
      toast.error(
        t('toast.compareError'),
        error.message
      );
    },
  });
}
