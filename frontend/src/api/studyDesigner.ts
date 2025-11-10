/**
 * Study Designer API Client
 *
 * API functions dla komunikacji z backendem Study Designer Chat.
 */

import axios from 'axios';

// Utwórz axios instance z konfiguracją (baseURL, auth interceptor)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1`
    : '/api/v1',
});

// Add auth interceptor - attach JWT token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Add Accept-Language header
  const language = localStorage.getItem('i18nextLng') || 'pl';
  const normalizedLang = language.split('-')[0];
  config.headers['Accept-Language'] = normalizedLang;

  return config;
});

// Handle 401 errors globally - redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

const API_BASE = '/study-designer';

// === TYPES ===

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface GeneratedPlan {
  markdown_summary: string;
  estimated_time_seconds: number;
  estimated_cost_usd: number;
  estimated_tokens?: number;
}

export interface Session {
  id: string;
  user_id: string;
  project_id?: string;
  status: string; // 'active' | 'plan_ready' | 'approved' | 'executing' | 'completed' | 'cancelled'
  current_stage: string;
  generated_plan?: GeneratedPlan;
  created_workflow_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  messages: Message[];
}

export interface SessionCreateRequest {
  project_id?: string;
}

export interface SessionCreateResponse {
  session: Session;
  welcome_message: string;
}

export interface MessageSendRequest {
  message: string;
}

export interface MessageSendResponse {
  session: Session;
  new_messages: Message[];
  plan_ready: boolean;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
}

// === API FUNCTIONS ===

/**
 * Rozpoczyna nową sesję Study Designer Chat
 */
export async function createSession(
  data: SessionCreateRequest = {}
): Promise<SessionCreateResponse> {
  const response = await api.post<SessionCreateResponse>(`${API_BASE}/sessions`, data);
  return response.data;
}

/**
 * Pobiera sesję z pełną historią wiadomości
 */
export async function getSession(sessionId: string): Promise<Session> {
  const response = await api.get<Session>(`${API_BASE}/sessions/${sessionId}`);
  return response.data;
}

/**
 * Wysyła wiadomość do Study Designer
 */
export async function sendMessage(
  sessionId: string,
  message: string
): Promise<MessageSendResponse> {
  const response = await api.post<MessageSendResponse>(
    `${API_BASE}/sessions/${sessionId}/message`,
    { message }
  );
  return response.data;
}

/**
 * Zatwierdza wygenerowany plan
 */
export async function approvePlan(sessionId: string): Promise<Session> {
  const response = await api.post<Session>(
    `${API_BASE}/sessions/${sessionId}/approve`,
    { approved: true }
  );
  return response.data;
}

/**
 * Anuluje sesję
 */
export async function cancelSession(sessionId: string): Promise<void> {
  await api.delete(`${API_BASE}/sessions/${sessionId}`);
}

/**
 * Pobiera listę sesji użytkownika
 */
export async function listSessions(
  limit: number = 20,
  offset: number = 0
): Promise<SessionListResponse> {
  const response = await api.get<SessionListResponse>(`${API_BASE}/sessions`, {
    params: { limit, offset },
  });
  return response.data;
}
