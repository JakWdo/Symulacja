/**
 * Study Designer React Hooks
 *
 * TanStack Query hooks dla Study Designer Chat.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createSession,
  getSession,
  sendMessage,
  approvePlan,
  cancelSession,
  listSessions,
  type SessionCreateRequest,
} from '../api/studyDesigner';
import { useNavigate } from 'react-router-dom';

// === QUERY KEYS ===

export const studyDesignerKeys = {
  all: ['study-designer'] as const,
  sessions: () => [...studyDesignerKeys.all, 'sessions'] as const,
  session: (id: string) => [...studyDesignerKeys.all, 'session', id] as const,
};

// === HOOKS ===

/**
 * Hook do tworzenia nowej sesji Study Designer
 */
export function useCreateSession() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data?: SessionCreateRequest) => createSession(data),
    onSuccess: (response) => {
      // Navigate to session
      navigate(`/study-designer/${response.session.id}`);

      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: studyDesignerKeys.sessions() });
    },
  });
}

/**
 * Hook do pobierania sesji (z auto-refresh)
 */
export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: studyDesignerKeys.session(sessionId!),
    queryFn: () => getSession(sessionId!),
    enabled: !!sessionId,
    refetchInterval: (data) => {
      // Auto-refresh co 5s jeśli sesja aktywna
      if (data?.status === 'active' || data?.status === 'plan_ready') {
        return 5000;
      }
      return false;
    },
  });
}

/**
 * Hook do wysyłania wiadomości
 */
export function useSendMessage(sessionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (message: string) => sendMessage(sessionId, message),
    onSuccess: () => {
      // Refresh session data
      queryClient.invalidateQueries({ queryKey: studyDesignerKeys.session(sessionId) });
    },
  });
}

/**
 * Hook do zatwierdzania planu
 */
export function useApprovePlan(sessionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => approvePlan(sessionId),
    onSuccess: () => {
      // Refresh session
      queryClient.invalidateQueries({ queryKey: studyDesignerKeys.session(sessionId) });
    },
  });
}

/**
 * Hook do anulowania sesji
 */
export function useCancelSession(sessionId: string) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => cancelSession(sessionId),
    onSuccess: () => {
      // Navigate back
      navigate('/dashboard');

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: studyDesignerKeys.sessions() });
      queryClient.invalidateQueries({ queryKey: studyDesignerKeys.session(sessionId) });
    },
  });
}

/**
 * Hook do listowania sesji
 */
export function useSessionsList(limit = 20, offset = 0) {
  return useQuery({
    queryKey: [...studyDesignerKeys.sessions(), limit, offset],
    queryFn: () => listSessions(limit, offset),
  });
}
