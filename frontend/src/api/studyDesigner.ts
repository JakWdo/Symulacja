/**
 * Study Designer API Client
 *
 * API functions dla komunikacji z backendem Study Designer Chat.
 */

import axios from 'axios';

const API_BASE = '/api/v1/study-designer';

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
  const response = await axios.post<SessionCreateResponse>(`${API_BASE}/sessions`, data);
  return response.data;
}

/**
 * Pobiera sesję z pełną historią wiadomości
 */
export async function getSession(sessionId: string): Promise<Session> {
  const response = await axios.get<Session>(`${API_BASE}/sessions/${sessionId}`);
  return response.data;
}

/**
 * Wysyła wiadomość do Study Designer
 */
export async function sendMessage(
  sessionId: string,
  message: string
): Promise<MessageSendResponse> {
  const response = await axios.post<MessageSendResponse>(
    `${API_BASE}/sessions/${sessionId}/message`,
    { message }
  );
  return response.data;
}

/**
 * Zatwierdza wygenerowany plan
 */
export async function approvePlan(sessionId: string): Promise<Session> {
  const response = await axios.post<Session>(
    `${API_BASE}/sessions/${sessionId}/approve`,
    { approved: true }
  );
  return response.data;
}

/**
 * Anuluje sesję
 */
export async function cancelSession(sessionId: string): Promise<void> {
  await axios.delete(`${API_BASE}/sessions/${sessionId}`);
}

/**
 * Pobiera listę sesji użytkownika
 */
export async function listSessions(
  limit: number = 20,
  offset: number = 0
): Promise<SessionListResponse> {
  const response = await axios.get<SessionListResponse>(`${API_BASE}/sessions`, {
    params: { limit, offset },
  });
  return response.data;
}
