import { api } from './client';
import type {
  Persona,
  PersonaDetailsResponse,
  PersonaMessagingResponse,
  PersonaMessagingPayload,
  PersonaComparisonResponse,
  PersonaExportResponse,
  PersonaDeleteResponse,
  PersonaUndoDeleteResponse,
} from '@/types';

export interface PersonaAdvancedOptions {
  // AI Wizard fields (kafle)
  target_audience_description?: string;
  focus_area?: string;
  demographic_preset?: string;

  // Demographic fields
  age_focus?: 'balanced' | 'young_adults' | 'experienced_leaders';
  gender_balance?: 'balanced' | 'female_skew' | 'male_skew';
  urbanicity?: 'any' | 'urban' | 'suburban' | 'rural';
  target_cities?: string[];
  target_countries?: string[];

  // Professional fields
  industries?: string[];
  required_values?: string[];
  excluded_values?: string[];
  required_interests?: string[];
  excluded_interests?: string[];

  // Age constraints
  age_min?: number;
  age_max?: number;

  // Custom distributions
  custom_age_groups?: Record<string, number>;
  gender_weights?: Record<string, number>;
  location_weights?: Record<string, number>;
  education_weights?: Record<string, number>;
  income_weights?: Record<string, number>;

  // Psychological
  personality_skew?: Record<string, number>;
}

export interface GeneratePersonasPayload {
  num_personas: number;
  adversarial_mode: boolean;
  use_rag: boolean;
  advanced_options?: PersonaAdvancedOptions;
}

export interface GeneratePersonasResponse {
  message: string;
  project_id: string;
  num_personas: number;
  use_rag: boolean;
  orchestration_enabled: boolean;
  warning?: string;
}

export const personasApi = {
  getByProject: async (projectId: string): Promise<Persona[]> => {
    const { data } = await api.get<Persona[]>(
      `/projects/${projectId}/personas`,
    );
    return data;
  },
  generate: async (
    projectId: string,
    payload: GeneratePersonasPayload,
  ): Promise<GeneratePersonasResponse> => {
    const { data } = await api.post<GeneratePersonasResponse>(`/projects/${projectId}/personas/generate`, payload);
    return data;
  },
  getDetails: async (personaId: string): Promise<PersonaDetailsResponse> => {
    const { data } = await api.get<PersonaDetailsResponse>(`/personas/${personaId}/details`);
    return data;
  },
  delete: async (
    personaId: string,
    reason: string,
    reasonDetail?: string,
  ): Promise<PersonaDeleteResponse> => {
    const { data} = await api.delete<PersonaDeleteResponse>(`/personas/${personaId}`, {
      data: {
        reason,
        reason_detail: reasonDetail,
      },
    });
    return data;
  },
  undoDelete: async (personaId: string): Promise<PersonaUndoDeleteResponse> => {
    const { data } = await api.post<PersonaUndoDeleteResponse>(`/personas/${personaId}/undo-delete`);
    return data;
  },
  generateMessaging: async (
    personaId: string,
    payload: PersonaMessagingPayload,
  ): Promise<PersonaMessagingResponse> => {
    const { data } = await api.post<PersonaMessagingResponse>(
      `/personas/${personaId}/actions/messaging`,
      payload,
    );
    return data;
  },
  compare: async (
    personaId: string,
    personaIds: string[],
    sections?: string[],
  ): Promise<PersonaComparisonResponse> => {
    const { data } = await api.post<PersonaComparisonResponse>(
      `/personas/${personaId}/actions/compare`,
      {
        persona_ids: personaIds,
        sections,
      },
    );
    return data;
  },
  export: async (
    personaId: string,
    sections?: string[],
  ): Promise<PersonaExportResponse> => {
    const { data } = await api.post<PersonaExportResponse>(
      `/personas/${personaId}/actions/export`,
      {
        format: 'json',
        sections,
      },
    );
    return data;
  },
};
