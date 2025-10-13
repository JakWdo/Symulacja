import type { GeneratePersonasPayload, PersonaAdvancedOptions } from '@/lib/api';
import type { PersonaGenerationConfig } from '@/components/personas/PersonaGenerationWizard';

/**
 * Transformuje uproszczoną konfigurację wizarda na payload API.
 * Nowa wersja - tylko ogólniki, demografia pochodzi z RAG.
 */
export function transformWizardConfigToPayload(
  config: PersonaGenerationConfig,
  _useRag: boolean = true, // RAG zawsze włączony (unused parameter for compatibility)
): GeneratePersonasPayload {
  const advancedOptions: Partial<PersonaAdvancedOptions> = {};

  // Dodaj target audience jeśli podany
  if (config.targetAudience?.trim()) {
    advancedOptions.target_audience_description = config.targetAudience.trim();
  }

  // Dodaj focus area jako kontekst
  if (config.focusArea) {
    advancedOptions.focus_area = config.focusArea;
  }

  // Dodaj demographic preset jako hint
  if (config.demographicPreset) {
    advancedOptions.demographic_preset = config.demographicPreset;
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

/**
 * Szacuje przewidywany czas generowania (ms) na podstawie liczby person.
 * Używane do prezentacji progress barów.
 */
export function estimateGenerationDuration(numPersonas: number): number {
  return Math.max(5000, numPersonas * 2500);
}
