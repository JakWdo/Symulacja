/**
 * Funkcje pomocnicze do szacowania czasu generacji Focus Group i formatowania czasu.
 *
 * Focus Group generation jest znacznie wolniejsza niż Persona generation,
 * ponieważ każda persona musi odpowiedzieć na każde pytanie (N × M wywołań LLM).
 */

export interface FocusGroupGenerationOptions {
  numPersonas?: number;
  numQuestions?: number;
  useAI?: boolean;
}

/**
 * Szacuje czas generacji focus group z realistycznymi overhead'ami.
 *
 * Formula:
 * - Base time: numPersonas × numQuestions × 3s (LLM call per persona per question)
 * - AI moderation overhead: +10s (jeśli useAI)
 * - Batch overhead: +5s
 * - Safety margin: 20%
 *
 * @param options - Opcje generacji (liczba person, pytań, AI moderation)
 * @returns Szacowany czas w ms
 */
export function estimateFocusGroupDuration(
  options: FocusGroupGenerationOptions = {}
): number {
  const {
    numPersonas = 20,
    numQuestions = 4,
    useAI = true,
  } = options;

  // Base time per response (persona + question combination)
  // Gemini 2.5 Flash: ~2-3s per response, używamy 3s dla bezpieczeństwa
  const baseTimePerResponse = 3000; // ms (~3s per response)

  // Total responses = personas × questions
  // Np. 20 person × 4 pytania = 80 odpowiedzi = ~240s base time
  const totalResponses = numPersonas * numQuestions;

  // AI moderation overhead (summary, analysis, key themes extraction)
  // To jest dodatkowo po wszystkich odpowiedziach
  const aiOverhead = useAI ? 10000 : 0; // 10s dla AI summary

  // Batch processing overhead (DB writes, indexing, cleanup)
  const batchOverhead = 5000; // 5s

  const totalTime =
    (baseTimePerResponse * totalResponses) +
    aiOverhead +
    batchOverhead;

  // Safety margin 20% (kolejki, network latency, rate limits)
  return Math.round(totalTime * 1.2);
}

/**
 * Formatuje czas w ms do czytelnego stringa (np. "45s", "2m 15s", "4m")
 */
export function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return remainingSeconds > 0
    ? `${minutes}m ${remainingSeconds}s`
    : `${minutes}m`;
}
