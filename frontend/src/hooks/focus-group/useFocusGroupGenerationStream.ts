import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Server-Sent Events progress data dla Focus Group generation.
 *
 * NOTE: Wymaga backend endpoint: /api/v1/focus-groups/{id}/generate/stream
 * Obecnie backend nie ma tego endpointu - to jest future enhancement.
 */
export interface FocusGroupGenerationProgress {
  stage: 'initializing' | 'generating_responses' | 'ai_moderation' | 'saving' | 'completed' | 'failed';
  progress_percent: number;
  message: string;
  responses_generated: number;
  total_responses: number;
  error?: string;
}

export interface UseFocusGroupGenerationStreamOptions {
  onCompleted?: () => void;
  onError?: (error: string) => void;
}

/**
 * Hook do streamowania real-time progress Focus Group generation przez SSE.
 *
 * **UWAGA**: To jest future enhancement. Backend obecnie nie ma endpointu SSE
 * dla Focus Group generation. Użyj polling (istniejący useQuery z refetchInterval).
 *
 * @param focusGroupId - ID grupy fokusowej
 * @param options - Callbacks dla completed/error
 * @returns progress state i funkcja startStream
 */
export function useFocusGroupGenerationStream(
  focusGroupId: string | null,
  options?: UseFocusGroupGenerationStreamOptions
) {
  const [progress, setProgress] = useState<FocusGroupGenerationProgress | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startStream = useCallback(() => {
    if (!focusGroupId) {
      console.warn('useFocusGroupGenerationStream: No focusGroupId provided');
      return;
    }

    // Cleanup existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = `/api/v1/focus-groups/${focusGroupId}/generate/stream`;
    console.info(`Starting SSE stream: ${url}`);

    const eventSource = new EventSource(url, { withCredentials: true });
    eventSourceRef.current = eventSource;
    setIsStreaming(true);

    eventSource.addEventListener('progress', (event) => {
      try {
        const data: FocusGroupGenerationProgress = JSON.parse(event.data);
        setProgress(data);

        if (data.stage === 'completed') {
          eventSource.close();
          setIsStreaming(false);
          options?.onCompleted?.();
        } else if (data.stage === 'failed') {
          eventSource.close();
          setIsStreaming(false);
          options?.onError?.(data.error || 'Unknown error');
        }
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    });

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
      setIsStreaming(false);
      options?.onError?.('Connection lost');
    };
  }, [focusGroupId, options]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return { progress, isStreaming, startStream };
}
