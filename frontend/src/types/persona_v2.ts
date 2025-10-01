/**
 * Enhanced Persona types v2 with better structure and readability
 * Backward compatible with v1 through mappers
 */

// ============================================================================
// CORE PERSONA TYPES
// ============================================================================

export interface GeoLocation {
  city: string;
  state?: string | null;
  country: string;
  timezone?: string | null;
}

export interface EducationInfo {
  level: string;
  field?: string | null;
  institution?: string | null;
}

export interface IncomeInfo {
  bracket: string;
  currency: string;
  employment_status?: string | null;
}

export interface OccupationInfo {
  title: string;
  industry?: string | null;
  seniority_level?: string | null;
  years_of_experience?: number | null;
}

export interface PersonaDemographics {
  age: number;
  age_group: string;
  gender: string;
  location: GeoLocation;
  education: EducationInfo;
  income: IncomeInfo;
  occupation: OccupationInfo;
}

export interface BigFiveTraits {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

export interface HofstedeDimensions {
  power_distance: number;
  individualism: number;
  masculinity: number;
  uncertainty_avoidance: number;
  long_term_orientation: number;
  indulgence: number;
}

export interface CognitiveProfile {
  decision_making_style: string;
  communication_style: string;
  learning_preference?: string | null;
  risk_tolerance?: number | null;
}

export interface PersonaPsychology {
  big_five: BigFiveTraits;
  hofstede: HofstedeDimensions;
  cognitive_style: CognitiveProfile;
}

export interface LifestyleSegment {
  life_stage?: string | null;
  family_status?: string | null;
  living_situation?: string | null;
  tech_savviness?: number | null;
}

export interface PersonaProfile {
  values: string[];
  interests: string[];
  lifestyle: LifestyleSegment;
  background_story: string;
  motivations?: string[];
  pain_points?: string[];
}

export interface PersonaMetadata {
  generator_version: string;
  model_used?: string | null;
  generation_prompt?: string | null;
  quality_score?: number | null;
  diversity_score?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PersonaV2 {
  id: string;
  project_id: string;
  demographics: PersonaDemographics;
  psychology: PersonaPsychology;
  profile: PersonaProfile;
  metadata: PersonaMetadata;
  is_active: boolean;
}

// ============================================================================
// CUSTOM GENERATION REQUESTS
// ============================================================================

export interface CustomDemographicDistribution {
  age_groups?: Record<string, number> | null;
  genders?: Record<string, number> | null;
  education_levels?: Record<string, number> | null;
  income_brackets?: Record<string, number> | null;
  locations?: Record<string, number> | null;
}

export interface GeographicConstraints {
  countries?: string[] | null;
  states?: string[] | null;
  cities?: string[] | null;
  urban_rural_ratio?: number | null;
}

export interface PsychographicTargets {
  required_values?: string[] | null;
  excluded_values?: string[] | null;
  required_interests?: string[] | null;
  excluded_interests?: string[] | null;
  personality_ranges?: Record<string, [number, number]> | null;
}

export interface OccupationFilter {
  whitelist?: string[] | null;
  blacklist?: string[] | null;
  industries?: string[] | null;
  seniority_levels?: string[] | null;
}

export interface CustomPersonaGenerateRequest {
  num_personas: number;
  adversarial_mode?: boolean;
  custom_demographics?: CustomDemographicDistribution | null;
  geographic_constraints?: GeographicConstraints | null;
  psychographic_targets?: PsychographicTargets | null;
  occupation_filter?: OccupationFilter | null;
  age_range_override?: [number, number] | null;
  cultural_dimensions_target?: Record<string, number> | null;
  ensure_diversity?: boolean;
  similarity_threshold?: number;
}

// ============================================================================
// BACKWARD COMPATIBILITY MAPPERS
// ============================================================================

import type { Persona as PersonaV1 } from './index';

export function personaV1ToV2(v1: PersonaV1): PersonaV2 {
  const locationParts = (v1.location || 'Unknown, Unknown').split(',');
  const city = locationParts[0]?.trim() || 'Unknown';
  const state = locationParts[1]?.trim() || null;

  return {
    id: v1.id,
    project_id: v1.project_id,
    demographics: {
      age: v1.age,
      age_group: inferAgeGroup(v1.age),
      gender: v1.gender,
      location: {
        city,
        state,
        country: 'United States',
      },
      education: {
        level: v1.education_level || 'Unknown',
        field: null,
      },
      income: {
        bracket: v1.income_bracket || 'Unknown',
        currency: 'USD',
        employment_status: null,
      },
      occupation: {
        title: v1.occupation || 'Unknown',
        industry: null,
        seniority_level: null,
      },
    },
    psychology: {
      big_five: {
        openness: v1.openness ?? 0.5,
        conscientiousness: v1.conscientiousness ?? 0.5,
        extraversion: v1.extraversion ?? 0.5,
        agreeableness: v1.agreeableness ?? 0.5,
        neuroticism: v1.neuroticism ?? 0.5,
      },
      hofstede: {
        power_distance: v1.power_distance ?? 0.5,
        individualism: v1.individualism ?? 0.5,
        masculinity: v1.masculinity ?? 0.5,
        uncertainty_avoidance: v1.uncertainty_avoidance ?? 0.5,
        long_term_orientation: v1.long_term_orientation ?? 0.5,
        indulgence: v1.indulgence ?? 0.5,
      },
      cognitive_style: {
        decision_making_style: 'Unknown',
        communication_style: 'Unknown',
      },
    },
    profile: {
      values: v1.values || [],
      interests: v1.interests || [],
      lifestyle: {},
      background_story: v1.background_story || '',
    },
    metadata: {
      generator_version: 'v1_migrated',
      created_at: v1.created_at,
    },
    is_active: v1.is_active,
  };
}

export function personaV2ToV1(v2: PersonaV2): PersonaV1 {
  const location = v2.demographics.location.state
    ? `${v2.demographics.location.city}, ${v2.demographics.location.state}`
    : v2.demographics.location.city;

  return {
    id: v2.id,
    project_id: v2.project_id,
    age: v2.demographics.age,
    gender: v2.demographics.gender,
    location,
    education_level: v2.demographics.education.level,
    income_bracket: v2.demographics.income.bracket,
    occupation: v2.demographics.occupation.title,
    openness: v2.psychology.big_five.openness,
    conscientiousness: v2.psychology.big_five.conscientiousness,
    extraversion: v2.psychology.big_five.extraversion,
    agreeableness: v2.psychology.big_five.agreeableness,
    neuroticism: v2.psychology.big_five.neuroticism,
    power_distance: v2.psychology.hofstede.power_distance,
    individualism: v2.psychology.hofstede.individualism,
    masculinity: v2.psychology.hofstede.masculinity,
    uncertainty_avoidance: v2.psychology.hofstede.uncertainty_avoidance,
    long_term_orientation: v2.psychology.hofstede.long_term_orientation,
    indulgence: v2.psychology.hofstede.indulgence,
    values: v2.profile.values,
    interests: v2.profile.interests,
    background_story: v2.profile.background_story,
    created_at: v2.metadata.created_at || new Date().toISOString(),
    is_active: v2.is_active,
  };
}

function inferAgeGroup(age: number): string {
  if (age < 25) return '18-24';
  if (age < 35) return '25-34';
  if (age < 45) return '35-44';
  if (age < 55) return '45-54';
  if (age < 65) return '55-64';
  return '65+';
}

// ============================================================================
// UI HELPERS
// ============================================================================

export function formatPersonaName(persona: PersonaV2): string {
  return `${persona.demographics.gender}, ${persona.demographics.age}`;
}

export function getPersonaLocation(persona: PersonaV2): string {
  const { city, state } = persona.demographics.location;
  return state ? `${city}, ${state}` : city;
}

export function getPersonaSummary(persona: PersonaV2): string {
  const { occupation, education } = persona.demographics;
  return `${occupation.title} • ${education.level}`;
}

export function getPersonalityHighlight(persona: PersonaV2): { trait: string; value: number; label: string }[] {
  const traits = Object.entries(persona.psychology.big_five)
    .map(([trait, value]) => ({
      trait,
      value,
      label: formatTraitName(trait),
    }))
    .sort((a, b) => b.value - a.value);

  return traits.slice(0, 3); // Top 3 traits
}

function formatTraitName(trait: string): string {
  return trait
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// ============================================================================
// VALIDATION HELPERS
// ============================================================================

export function validateDistribution(dist: Record<string, number>): boolean {
  const total = Object.values(dist).reduce((sum, val) => sum + val, 0);
  return total >= 0.95 && total <= 1.05;
}

export function normalizeDistribution(dist: Record<string, number>): Record<string, number> {
  const total = Object.values(dist).reduce((sum, val) => sum + val, 0);
  if (total === 0) return dist;

  return Object.fromEntries(
    Object.entries(dist).map(([key, value]) => [key, value / total])
  );
}

// ============================================================================
// CONSTANTS FOR UI
// ============================================================================

export const BIG_FIVE_DESCRIPTIONS: Record<keyof BigFiveTraits, { name: string; high: string; low: string }> = {
  openness: {
    name: 'Openness',
    high: 'Creative, curious, open to new experiences',
    low: 'Practical, traditional, prefers routine',
  },
  conscientiousness: {
    name: 'Conscientiousness',
    high: 'Organized, disciplined, detail-oriented',
    low: 'Spontaneous, flexible, less structured',
  },
  extraversion: {
    name: 'Extraversion',
    high: 'Outgoing, energetic, social',
    low: 'Reserved, introspective, prefers solitude',
  },
  agreeableness: {
    name: 'Agreeableness',
    high: 'Cooperative, compassionate, empathetic',
    low: 'Competitive, direct, skeptical',
  },
  neuroticism: {
    name: 'Neuroticism',
    high: 'Anxious, sensitive, stress-prone',
    low: 'Calm, resilient, emotionally stable',
  },
};

export const HOFSTEDE_DESCRIPTIONS: Record<keyof HofstedeDimensions, { name: string; description: string }> = {
  power_distance: {
    name: 'Power Distance',
    description: 'Acceptance of hierarchical order and inequality',
  },
  individualism: {
    name: 'Individualism',
    description: 'Preference for independence vs. group cohesion',
  },
  masculinity: {
    name: 'Masculinity',
    description: 'Preference for achievement vs. caring for others',
  },
  uncertainty_avoidance: {
    name: 'Uncertainty Avoidance',
    description: 'Tolerance for ambiguity and uncertainty',
  },
  long_term_orientation: {
    name: 'Long-term Orientation',
    description: 'Focus on future rewards vs. tradition',
  },
  indulgence: {
    name: 'Indulgence',
    description: 'Gratification vs. restraint of desires',
  },
};
