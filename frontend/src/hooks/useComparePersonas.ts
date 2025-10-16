import { useMutation } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import type { PersonaComparisonResponse } from '@/types';
import { toast } from '@/components/ui/toastStore';

interface CompareParams {
  personaId: string;
  personaIds: string[];
  sections?: string[];
}

export function useComparePersonas() {
  return useMutation<PersonaComparisonResponse, Error, CompareParams>({
    mutationFn: async ({ personaId, personaIds, sections }) => {
      return personasApi.compare(personaId, personaIds, sections);
    },
    onError: (error: Error) => {
      toast.error('Nie udało się porównać person', error.message);
    },
  });
}
