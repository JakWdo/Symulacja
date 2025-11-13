/**
 * Assistant API Client
 *
 * HTTP client dla Product Assistant endpoints.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1`
    : '/api/v1',
});

// Auth interceptor - dodaje token do każdego requesta
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// === TYPES ===

export interface ChatRequest {
  message: string;
  conversation_history: Array<{ role: string; content: string }>;
  include_user_context?: boolean;
}

export interface ChatResponse {
  message: string;
  suggestions: string[];
}

// === API FUNCTIONS ===

/**
 * Wysyła wiadomość do Product Assistant
 *
 * @param request - ChatRequest z wiadomością, historią i flagą kontekstu
 * @returns ChatResponse z odpowiedzią asystenta i sugestiami
 */
export async function sendAssistantMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/assistant/chat', request);
  return response.data;
}
