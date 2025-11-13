/**
 * Study Designer React Hooks
 *
 * TanStack Query hooks dla Study Designer Chat.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createSession,
  getSession,
  sendMessage,
  sendMessageStream,
  approvePlan,
  cancelSession,
  listSessions,
  type SessionCreateRequest,
} from '../api/studyDesigner';

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
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data?: SessionCreateRequest) => createSession(data),
    onSuccess: (response) => {
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: studyDesignerKeys.sessions() });

      // Note: Navigation is handled by the calling component (StudyDesignerView)
      // by checking mutation.data and rendering ChatInterface conditionally
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

/**
 * Hook do streaming messages (SSE version)
 * Używa async generator do real-time updates
 */
export function useSendMessageStream(sessionId: string) {
  const queryClient = useQueryClient();
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedMessage, setStreamedMessage] = useState('');
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = async (message: string) => {
    setIsStreaming(true);
    setStreamedMessage('');
    setError(null);

    try {
      for await (const chunk of sendMessageStream(sessionId, message)) {
        if (chunk.is_complete) {
          // Stream zakończony
          setIsStreaming(false);
          setStreamedMessage('');

          // Odśwież session data z serwera
          queryClient.invalidateQueries({
            queryKey: studyDesignerKeys.session(sessionId),
          });
        } else {
          // Akumuluj content
          setStreamedMessage((prev) => {
            // Jeśli to nowy message (różny od poprzedniego)
            if (!prev || chunk.content.startsWith(prev)) {
              return chunk.content;
            }
            return prev + chunk.content;
          });
        }
      }
    } catch (err) {
      console.error('Stream error:', err);
      setError(err as Error);
      setIsStreaming(false);
      throw err;
    }
  };

  return {
    sendMessage,
    isStreaming,
    streamedMessage,
    error,
  };
}
