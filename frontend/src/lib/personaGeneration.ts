import type { GeneratePersonasPayload, PersonaAdvancedOptions } from '@/lib/api';
import type { PersonaGenerationConfig } from '@/components/personas/PersonaGenerationWizard';

/**
 * Normalizuje słownik procentów (np. rozkład wieku) do sumy 1.0.
 * Zwraca undefined, gdy brak sensownych wartości (np. same zera).
 */
function normalizePercentageRecord(record: Record<string, [number]>): Record<string, number> | undefined {
  const entries = Object.entries(record)
    .map(([key, values]) => {
      const value = Array.isArray(values) ? values[0] ?? 0 : 0;
      return [key, Number(value)] as const;
    })
    .filter(([, value]) => Number.isFinite(value) && value > 0);

  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  if (total <= 0) {
    return undefined;
  }

  return Object.fromEntries(entries.map(([key, value]) => [key, Number((value / total).toFixed(4))]));
}

/**
 * Normalizuje listę lokalizacji (miasto + procent) do słownika wag.
 */
function normalizeLocationDistribution(
  locations: PersonaGenerationConfig['locationDistribution'],
): Record<string, number> | undefined {
  const aggregated = locations.reduce<Record<string, number>>((acc, { city, weight }) => {
    const trimmedCity = city.trim();
    const numericWeight = Number(weight);
    if (!trimmedCity || !Number.isFinite(numericWeight) || numericWeight <= 0) {
      return acc;
    }
    acc[trimmedCity] = (acc[trimmedCity] ?? 0) + numericWeight;
    return acc;
  }, {});

  const entries = Object.entries(aggregated).filter(([, value]) => value > 0);
  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  if (total <= 0) {
    return undefined;
  }

  return Object.fromEntries(entries.map(([city, value]) => [city, Number((value / total).toFixed(4))]));
}

function parseCommaSeparatedList(value: string): string[] {
  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter((entry, index, array) => entry.length > 0 && array.indexOf(entry) === index);
}

function convertPersonalitySkew(record: Record<string, [number]>): Record<string, number> | undefined {
  const entries = Object.entries(record)
    .map(([key, values]) => {
      const value = Array.isArray(values) ? values[0] ?? 0 : 0;
      return [key, Math.min(Math.max(value / 100, 0), 1)];
    })
    .filter(([, value]) => Number.isFinite(value));

  if (entries.length === 0) {
    return undefined;
  }

  return Object.fromEntries(entries);
}

function pruneAdvancedOptions(options: Partial<PersonaAdvancedOptions>): PersonaAdvancedOptions | undefined {
  const cleaned = Object.entries(options).filter(([, value]) => {
    if (value === undefined || value === null) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0;
    return true;
  });

  if (cleaned.length === 0) {
    return undefined;
  }

  return Object.fromEntries(cleaned) as PersonaAdvancedOptions;
}

export function transformWizardConfigToPayload(config: PersonaGenerationConfig): GeneratePersonasPayload {
  const advancedOptions: Partial<PersonaAdvancedOptions> = {};

  const customAgeGroups = normalizePercentageRecord(config.ageGroups);
  if (customAgeGroups) {
    advancedOptions.custom_age_groups = customAgeGroups;
  }

  const genderWeights = normalizePercentageRecord(config.genderDistribution);
  if (genderWeights) {
    advancedOptions.gender_weights = genderWeights;
  }

  const educationWeights = normalizePercentageRecord(config.educationLevels);
  if (educationWeights) {
    advancedOptions.education_weights = educationWeights;
  }

  const incomeWeights = normalizePercentageRecord(config.incomeBrackets);
  if (incomeWeights) {
    advancedOptions.income_weights = incomeWeights;
  }

  const locationWeights = normalizeLocationDistribution(config.locationDistribution);
  if (locationWeights) {
    advancedOptions.location_weights = locationWeights;
  }

  const targetCities = parseCommaSeparatedList(config.targetCities);
  if (targetCities.length > 0) {
    advancedOptions.target_cities = targetCities;
  }

  if (config.urbanicity && config.urbanicity !== 'any') {
    advancedOptions.urbanicity = config.urbanicity as PersonaAdvancedOptions['urbanicity'];
  }

  const uniqueIndustries = config.targetIndustries
    .map((industry) => industry.trim())
    .filter((industry, index, array) => industry.length > 0 && array.indexOf(industry) === index);
  if (uniqueIndustries.length > 0) {
    advancedOptions.industries = uniqueIndustries;
  }

  const requiredValues = Array.from(new Set(config.requiredValues.map((value) => value.trim()).filter(Boolean)));
  if (requiredValues.length > 0) {
    advancedOptions.required_values = requiredValues;
  }

  const excludedValues = Array.from(new Set(config.excludedValues.map((value) => value.trim()).filter(Boolean)));
  if (excludedValues.length > 0) {
    advancedOptions.excluded_values = excludedValues;
  }

  const requiredInterests = Array.from(new Set(config.requiredInterests.map((value) => value.trim()).filter(Boolean)));
  if (requiredInterests.length > 0) {
    advancedOptions.required_interests = requiredInterests;
  }

  const excludedInterests = Array.from(new Set(config.excludedInterests.map((value) => value.trim()).filter(Boolean)));
  if (excludedInterests.length > 0) {
    advancedOptions.excluded_interests = excludedInterests;
  }

  const personalitySkew = convertPersonalitySkew(config.personalitySkew);
  if (personalitySkew) {
    const deviatesFromNeutral = Object.values(personalitySkew).some((value) => Math.abs(value - 0.5) > 0.01);
    if (deviatesFromNeutral) {
      advancedOptions.personality_skew = personalitySkew;
    }
  }

  const advanced_payload = pruneAdvancedOptions(advancedOptions);

  return {
    num_personas: config.personaCount,
    adversarial_mode: config.adversarialMode,
    advanced_options: advanced_payload,
  };
}

/**
 * Szacuje przewidywany czas generowania (ms) na podstawie liczby person.
 * Używane do prezentacji progress barów.
 */
export function estimateGenerationDuration(numPersonas: number): number {
  return Math.max(5000, numPersonas * 2500);
}
