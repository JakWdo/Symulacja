import { api } from './client';
import type { Survey, SurveyResults, Question } from '@/types';

export const surveysApi = {
  getByProject: async (projectId: string): Promise<Survey[]> => {
    const { data } = await api.get<Survey[]>(`/projects/${projectId}/surveys`);
    return data;
  },

  create: async (
    projectId: string,
    payload: {
      title: string;
      description?: string;
      questions: Question[];
      target_responses?: number;
    }
  ): Promise<Survey> => {
    const { data } = await api.post<Survey>(
      `/projects/${projectId}/surveys`,
      payload
    );
    return data;
  },

  get: async (surveyId: string): Promise<Survey> => {
    const { data } = await api.get<Survey>(`/surveys/${surveyId}`);
    return data;
  },

  run: async (surveyId: string): Promise<void> => {
    await api.post(`/surveys/${surveyId}/run`);
  },

  getResults: async (surveyId: string): Promise<SurveyResults> => {
    const { data} = await api.get<SurveyResults>(
      `/surveys/${surveyId}/results`
    );
    return data;
  },

  delete: async (surveyId: string): Promise<void> => {
    await api.delete(`/surveys/${surveyId}`);
  },
};
