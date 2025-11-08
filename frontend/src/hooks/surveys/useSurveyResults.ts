import { useQuery } from '@tanstack/react-query';
import { surveysApi } from '@/lib/api';
import type { SurveyResults } from '@/types';

export function useSurveyResults(surveyId: string) {
  return useQuery<SurveyResults>({
    queryKey: ['survey-results', surveyId],
    queryFn: () => surveysApi.getResults(surveyId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!surveyId, // Tylko gdy surveyId jest dostępne
  });
}
