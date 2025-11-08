import type { GeneratePersonasPayload, PersonaAdvancedOptions } from '@/lib/api';
import type { PersonaGenerationConfig } from '@/components/personas/PersonaGenerationWizard';

/**
 * Transformuje uproszczoną konfigurację wizarda na payload API.
 * Nowa wersja - tylko ogólniki, demografia pochodzi z RAG (zawsze włączony).
 */
export function transformWizardConfigToPayload(
  config: PersonaGenerationConfig,
): GeneratePersonasPayload {
  const advancedOptions: Partial<PersonaAdvancedOptions> = {};

  // Dodaj target audience jeśli podany
  if (config.targetAudience?.trim()) {
    advancedOptions.target_audience_description = config.targetAudience.trim();
  }

  // Dodaj focus area jako kontekst (z normalizacją ID dla backend compatibility)
  if (config.focusArea) {
    // Mapuj frontend ID → backend ID
    const focusAreaMapping: Record<string, string> = {
      'technology': 'tech',
      'healthcare': 'healthcare',
      'finance': 'finance',
      'education': 'education',
      'retail': 'retail',
      'manufacturing': 'manufacturing',
      'services': 'services',
      'entertainment': 'entertainment',
      'lifestyle': 'lifestyle',
      'shopping': 'shopping',
      'general': 'general',
    };
    advancedOptions.focus_area = focusAreaMapping[config.focusArea] || config.focusArea;
  }

  // Dodaj demographic preset jako hint (z normalizacją myślników → underscores)
  if (config.demographicPreset) {
    // Backend oczekuje snake_case (gen_z, nie gen-z)
    advancedOptions.demographic_preset = config.demographicPreset.replace(/-/g, '_');
  }

  // Usuń puste opcje
  const cleanedOptions = Object.entries(advancedOptions).filter(([, value]) => {
    if (value === undefined || value === null) return false;
    if (typeof value === 'string') return value.length > 0;
    return true;
  });

  return {
    num_personas: config.personaCount,
    adversarial_mode: config.adversarialMode,
    use_rag: true, // ZAWSZE włączony RAG
    advanced_options: cleanedOptions.length > 0 ? Object.fromEntries(cleanedOptions) as PersonaAdvancedOptions : undefined,
  };
}

export interface GenerationOptions {
  useRag?: boolean;
  adversarialMode?: boolean;
}

/**
 * Szacuje czas generacji person z realistycznymi overhead'ami.
 *
 * @param numPersonas Liczba person do wygenerowania
 * @param options Opcje generacji (RAG, adversarial mode)
 * @returns Szacowany czas w ms
 */
export function estimateGenerationDuration(
  numPersonas: number,
  options: GenerationOptions = {}
): number {
  // Base time per persona (LLM call + DB write)
  const baseTimePerPersona = 2500; // ms (~2.5s per persona)

  // Overhead dla orchestration (segment briefs z Graph RAG)
  const orchestrationOverhead = options.useRag ? 15000 : 5000; // 15s z RAG, 5s bez

  // Adversarial mode ma bardziej złożone prompty
  const adversarialMultiplier = options.adversarialMode ? 1.3 : 1.0;

  // Batch overhead (walidacja, zapis do DB, indexing)
  const batchOverhead = 5000; // 5s

  // Total time
  const totalTime =
    orchestrationOverhead +
    (baseTimePerPersona * numPersonas * adversarialMultiplier) +
    batchOverhead;

  // Safety margin 20% (queue delays, network latency, etc.)
  return Math.round(totalTime * 1.2);
}

/**
 * Formatuje czas w ms do czytelnego stringa (np. "45s", "2m 15s")
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
