/**
 * Persona Transformers - Utility functions for transforming API personas to display format
 */

import { Persona as APIPersona } from '@/types';
import {
  GENDER_LABELS,
  EDUCATION_LABELS,
  INCOME_LABELS,
  POLISH_CITY_NAMES,
  POLISH_CITY_LOOKUP,
  LOCATION_ALIASES,
  normalizeText,
} from '@/constants/personas';

// Display-friendly Persona interface
export interface DisplayPersona {
  id: string;
  name: string;
  age: number;
  occupation: string;
  interests: string[];
  headline: string | null;
  background: string;
  demographics: {
    gender: string;
    location: string;
    income: string;
    education: string;
  };
  psychographics: {
    personality: string[];
    values: string[];
    lifestyle: string;
  };
  createdAt: string;
  projectId: string;
}

function detectCityFromStory(story?: string | null): string | null {
  if (!story) return null;
  const normalizedStory = normalizeText(story);
  for (const city of POLISH_CITY_NAMES) {
    const normalizedCity = normalizeText(city);
    if (!normalizedCity) continue;
    if (normalizedStory.includes(normalizedCity)) return city;
    if (normalizedStory.includes(`${normalizedCity}u`)) return city;
    if (normalizedStory.includes(`${normalizedCity}ie`)) return city;
    if (normalizedStory.includes(`${normalizedCity}iu`)) return city;
  }
  return null;
}

function polishifyLocation(location?: string | null, story?: string | null): string {
  const normalized = normalizeText(location);
  if (normalized) {
    if (POLISH_CITY_LOOKUP[normalized]) {
      return POLISH_CITY_LOOKUP[normalized];
    }
    if (LOCATION_ALIASES[normalized]) {
      return LOCATION_ALIASES[normalized];
    }
    const parts = normalized.split(/[,/]/).map(part => part.trim());
    for (const part of parts) {
      if (POLISH_CITY_LOOKUP[part]) return POLISH_CITY_LOOKUP[part];
      if (LOCATION_ALIASES[part]) return LOCATION_ALIASES[part];
    }
  }
  const fromStory = detectCityFromStory(story);
  if (fromStory) return fromStory;
  return 'Warszawa';
}

function polishifyGender(gender?: string | null): string {
  const normalized = normalizeText(gender);
  return GENDER_LABELS[normalized] ?? (gender ? gender : 'Kobieta');
}

function polishifyEducation(education?: string | null): string {
  const normalized = normalizeText(education);
  if (normalized && EDUCATION_LABELS[normalized]) {
    return EDUCATION_LABELS[normalized];
  }
  return education ?? 'Średnie ogólnokształcące';
}

function polishifyIncome(income?: string | null): string {
  if (!income) return '5 000 - 7 500 zł';
  const normalized = income.replace(/\s/g, '');
  if (INCOME_LABELS[income]) return INCOME_LABELS[income];
  if (INCOME_LABELS[normalized]) return INCOME_LABELS[normalized];
  return income;
}

export function formatAge(age: number): string {
  const mod10 = age % 10;
  const mod100 = age % 100;
  if (mod10 === 1 && mod100 !== 11) return `${age} rok`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${age} lata`;
  return `${age} lat`;
}

export function extractFirstName(fullName?: string | null): string {
  if (!fullName) return 'Persona';
  const parts = fullName.trim().split(/\s+/);
  return parts.length > 0 ? parts[0] : fullName;
}

export function transformPersona(apiPersona: APIPersona): DisplayPersona {
  // Headline i background jako osobne pola
  const headline = apiPersona.headline || null;
  const background = (apiPersona.background_story || apiPersona.headline || 'Brak opisu persony').trim();

  // Cechy osobowości Big Five w uproszczonym języku polskim
  const personality: string[] = [];
  if (apiPersona.openness && apiPersona.openness > 0.6) personality.push('Otwartość na zmiany');
  if (apiPersona.conscientiousness && apiPersona.conscientiousness > 0.6) personality.push('Wysoka sumienność');
  if (apiPersona.extraversion && apiPersona.extraversion > 0.6) personality.push('Ekstrawersja');
  if (apiPersona.agreeableness && apiPersona.agreeableness > 0.6) personality.push('Ugodowość');
  if (apiPersona.neuroticism && apiPersona.neuroticism < 0.4) personality.push('Spokój emocjonalny');

  // Styl życia zależny od poziomu indywidualizmu
  let lifestyle = 'Zrównoważony styl życia';
  if (apiPersona.individualism && apiPersona.individualism > 0.7) {
    lifestyle = 'Niezależny i samodzielny styl życia';
  } else if (apiPersona.individualism && apiPersona.individualism < 0.3) {
    lifestyle = 'Skupienie na społeczności i współpracy';
  }

  const gender = polishifyGender(apiPersona.gender);
  const education = polishifyEducation(apiPersona.education_level);
  const income = polishifyIncome(apiPersona.income_bracket);
  const location = polishifyLocation(apiPersona.location, background);

  return {
    id: apiPersona.id,
    name: apiPersona.full_name || apiPersona.persona_title || 'Nieznana persona',
    age: apiPersona.age,
    occupation: apiPersona.occupation || apiPersona.persona_title || 'Zawód nieokreślony',
    interests: Array.isArray(apiPersona.interests) ? apiPersona.interests : [],
    headline,
    background,
    demographics: {
      gender,
      location,
      income,
      education,
    },
    psychographics: {
      personality,
      values: Array.isArray(apiPersona.values) ? apiPersona.values : [],
      lifestyle,
    },
    createdAt: apiPersona.created_at,
    projectId: apiPersona.project_id,
  };
}
