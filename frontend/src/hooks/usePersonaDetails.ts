import { useQuery } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import type { PersonaDetailsResponse } from '@/types';

/**
 * Hook do pobierania szczegółowych informacji o personie
 *
 * Wykorzystuje React Query do cachowania i automatycznego odświeżania danych.
 * Cache jest ważny przez 5 minut (staleTime: 5 * 60 * 1000).
 *
 * @param personaId - ID persony do pobrania
 * @returns Query object z danymi persony, stanem ładowania i ewentualnymi błędami
 */
export function usePersonaDetails(personaId: string | null) {
  return useQuery<PersonaDetailsResponse>({
    queryKey: ['personas', personaId, 'details'],
    queryFn: async () => {
      if (!personaId) {
        throw new Error('Persona ID is required');
      }
      return await personasApi.getDetails(personaId);
    },
    staleTime: 5 * 60 * 1000, // 5 minut cache
    enabled: !!personaId, // Tylko gdy personaId istnieje
    retry: 2, // Retry 2 razy w przypadku błędu
  });
}
