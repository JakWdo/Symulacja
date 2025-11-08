import { useState, useEffect, useCallback, useRef } from 'react';

export interface GenerationProgress {
  stage: 'initializing' | 'orchestration' | 'generating_personas' | 'validation' | 'saving' | 'completed' | 'failed';
  progress_percent: number;
  message: string;
  personas_generated: number;
  total_personas: number;
  error?: string;
}

export interface UsePersonaGenerationStreamOptions {
  projectId: string;
  numPersonas: number;
  useRag: boolean;
  onCompleted?: () => void;
  onError?: (error: string) => void;
}

/**
 * Hook dla SSE streaming generacji person z real-time progress.
 */
export function usePersonaGenerationStream(
  options: UsePersonaGenerationStreamOptions | null
) {
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startStream = useCallback(() => {
    if (!options) return;

    // Cleanup previous stream
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const { projectId, numPersonas, useRag, onCompleted, onError } = options;

    // Build SSE URL
    const params = new URLSearchParams({
      num_personas: numPersonas.toString(),
      use_rag: useRag.toString(),
    });
    const url = `/api/v1/projects/${projectId}/personas/generate/stream?${params}`;

    // Create EventSource
    const eventSource = new EventSource(url, {
      withCredentials: true, // Include auth cookies
    });

    eventSourceRef.current = eventSource;
    setIsStreaming(true);

    // Handle progress events
    eventSource.addEventListener('progress', (event) => {
      try {
        const data: GenerationProgress = JSON.parse(event.data);
        setProgress(data);

        // Check if completed or failed
        if (data.stage === 'completed') {
          eventSource.close();
          setIsStreaming(false);
          onCompleted?.();
        } else if (data.stage === 'failed') {
          eventSource.close();
          setIsStreaming(false);
          onError?.(data.error || 'Unknown error');
        }
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    });

    // Handle errors
    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
      setIsStreaming(false);
      onError?.('Connection lost. Please refresh the page.');
    };
  }, [options]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    progress,
    isStreaming,
    startStream,
  };
}
