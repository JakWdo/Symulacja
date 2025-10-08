import { useQuery } from '@tanstack/react-query';
import { graphApi } from '@/lib/api';
import type { GraphData } from '@/types';

/**
 * Hook do pobierania danych grafu wiedzy z Neo4j
 *
 * Zamiast lokalnych obliczeń podobieństwa person, pobiera gotowy graf
 * z bazy Neo4j zawierający:
 * - Persony
 * - Koncepty (ekstraktowane przez LLM)
 * - Emocje
 * - Relacje między nimi
 */
export function useGraphData(
  focusGroupId: string | undefined,
  filterType?: 'positive' | 'negative' | 'influence'
) {
  return useQuery<GraphData>({
    queryKey: ['graph-data', focusGroupId, filterType],
    queryFn: async () => {
      if (!focusGroupId) {
        throw new Error('Focus group ID is required');
      }
      return await graphApi.getGraph(focusGroupId, filterType);
    },
    enabled: !!focusGroupId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook do pobierania kluczowych konceptów z grafu
 */
export function useKeyConcepts(focusGroupId: string | undefined) {
  return useQuery({
    queryKey: ['key-concepts', focusGroupId],
    queryFn: async () => {
      if (!focusGroupId) {
        throw new Error('Focus group ID is required');
      }
      return await graphApi.getKeyConcepts(focusGroupId);
    },
    enabled: !!focusGroupId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook do pobierania wpływowych person
 */
export function useInfluentialPersonas(focusGroupId: string | undefined) {
  return useQuery({
    queryKey: ['influential-personas', focusGroupId],
    queryFn: async () => {
      if (!focusGroupId) {
        throw new Error('Focus group ID is required');
      }
      return await graphApi.getInfluentialPersonas(focusGroupId);
    },
    enabled: !!focusGroupId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook do pobierania polaryzujących konceptów
 */
export function useControversialConcepts(focusGroupId: string | undefined) {
  return useQuery({
    queryKey: ['controversial-concepts', focusGroupId],
    queryFn: async () => {
      if (!focusGroupId) {
        throw new Error('Focus group ID is required');
      }
      return await graphApi.getControversialConcepts(focusGroupId);
    },
    enabled: !!focusGroupId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook do pobierania korelacji między cechami a opiniami
 */
export function useTraitCorrelations(focusGroupId: string | undefined) {
  return useQuery({
    queryKey: ['trait-correlations', focusGroupId],
    queryFn: async () => {
      if (!focusGroupId) {
        throw new Error('Focus group ID is required');
      }
      return await graphApi.getTraitCorrelations(focusGroupId);
    },
    enabled: !!focusGroupId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook do pobierania rozkładu emocji
 */
export function useEmotionDistribution(focusGroupId: string | undefined) {
  return useQuery({
    queryKey: ['emotion-distribution', focusGroupId],
    queryFn: async () => {
      if (!focusGroupId) {
        throw new Error('Focus group ID is required');
      }
      return await graphApi.getEmotionDistribution(focusGroupId);
    },
    enabled: !!focusGroupId,
    staleTime: 5 * 60 * 1000,
  });
}
