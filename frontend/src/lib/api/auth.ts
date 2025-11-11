import { api } from './client';

// === AUTH TYPES ===
export interface User {
  id: string;
  email: string;
  full_name: string;
  role?: string;
  company?: string;
  avatar_url?: string;
  plan: string;
  is_verified: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  company?: string;
  role?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// === SETTINGS TYPES ===
export interface AccountStats {
  plan: string;
  projects_count: number;
  personas_count: number;
  focus_groups_count: number;
  surveys_count: number;
}

export interface BudgetSettings {
  budget_limit: number | null;
  warning_threshold: number;
  critical_threshold: number;
}

export interface BudgetSettingsUpdate {
  budget_limit?: number | null;
  warning_threshold?: number;
  critical_threshold?: number;
}

// === AUTH API ===
export const authApi = {
  register: async (data: RegisterData): Promise<TokenResponse> => {
    const { data: response } = await api.post<TokenResponse>('/auth/register', data);
    return response;
  },

  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const { data } = await api.post<TokenResponse>('/auth/login', credentials);
    return data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  me: async (): Promise<User> => {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },
};

// === SETTINGS API ===
export const settingsApi = {
  getProfile: async (): Promise<User> => {
    const { data } = await api.get<User>('/settings/profile');
    return data;
  },

  updateProfile: async (payload: Partial<User>): Promise<{ message: string; user: User }> => {
    const { data } = await api.put('/settings/profile', payload);
    return data;
  },

  uploadAvatar: async (formData: FormData): Promise<{ message: string; avatar_url: string }> => {
    const { data } = await api.post('/settings/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  deleteAvatar: async (): Promise<{ message: string }> => {
    const { data } = await api.delete('/settings/avatar');
    return data;
  },

  getStats: async (): Promise<AccountStats> => {
    const { data } = await api.get<AccountStats>('/settings/stats');
    return data;
  },

  getBudgetSettings: async (): Promise<BudgetSettings> => {
    const { data } = await api.get<BudgetSettings>('/settings/budget');
    return data;
  },

  updateBudgetSettings: async (payload: BudgetSettingsUpdate): Promise<BudgetSettings> => {
    const { data } = await api.put<BudgetSettings>('/settings/budget', payload);
    return data;
  },

  deleteAccount: async (): Promise<void> => {
    await api.delete('/settings/account');
  },
};
