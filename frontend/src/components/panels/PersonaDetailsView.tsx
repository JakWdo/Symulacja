/**
 * PersonaDetailsView - Szczegółowy widok persony
 *
 * Wyświetla pełne informacje o wybranej personie:
 * - Podstawowe dane (imię, wiek, lokalizacja, zawód)
 * - Profil osobowości (Big Five)
 * - Wartości i zainteresowania
 * - Historia (background story)
 * - Źródła RAG (jeśli wykorzystano)
 *
 * @example
 * <PersonaDetailsView persona={selectedPersona} />
 */

import { Quote } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { getPersonalityColor } from '@/lib/utils';
import type { Persona } from '@/types';

const NAME_FROM_STORY_REGEX = /^(?<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s/;

function guessNameFromStory(story?: string | null) {
  if (!story) return null;
  const match = story.trim().match(NAME_FROM_STORY_REGEX);
  return match?.groups?.name ?? null;
}

function getPersonaDisplayName(persona: Persona) {
  if (persona.full_name && persona.full_name.trim().length > 0) {
    return persona.full_name.trim();
  }
  const inferred = guessNameFromStory(persona.background_story);
  if (inferred) {
    return inferred;
  }
  const genderLabel = persona.gender ? `${persona.gender.charAt(0).toUpperCase()}${persona.gender.slice(1)}` : 'Persona';
  return `${genderLabel} ${persona.age}`;
}

function extractStorySummary(story?: string | null) {
  if (!story) return null;
  const trimmed = story.trim();
  if (!trimmed) return null;
  const match = trimmed.match(/[^.!?]+[.!?]/);
  return (match ? match[0] : trimmed).trim();
}

function formatLocation(location?: string | null) {
  if (!location) return 'Lokalizacja nieznana';
  return location;
}

interface PersonaDetailsViewProps {
  persona: Persona | null;
}

/**
 * PersonaDetailsView Component
 */
export function PersonaDetailsView({ persona }: PersonaDetailsViewProps) {
  if (!persona) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-slate-500">
        Wybierz personę, aby zobaczyć jej szczegóły.
      </div>
    );
  }

  const displayName = getPersonaDisplayName(persona);
  const subtitle = persona.persona_title?.trim() || persona.occupation?.trim() || 'Profil persony';
  const locationLabel = formatLocation(persona.location);
  const headline = (persona.headline && persona.headline.trim()) || extractStorySummary(persona.background_story);
  const ragCitations = persona.rag_citations ?? [];
  const ragContextUsed = persona.rag_context_used;
  const showRagSection = ragContextUsed || ragCitations.length > 0;

  const personalityTraits: Array<{ label: string; value: number | null | undefined }> = [
    { label: 'Otwartość', value: persona.openness },
    { label: 'Sumienność', value: persona.conscientiousness },
    { label: 'Ekstrawersja', value: persona.extraversion },
    { label: 'Ugodowość', value: persona.agreeableness },
    { label: 'Neurotyczność', value: persona.neuroticism },
  ];

  return (
    <div className="h-full space-y-6 overflow-y-auto rounded-2xl border border-slate-200/60 bg-white/80 p-8 shadow-sm backdrop-blur-sm scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
      {/* Header */}
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <h4 className="text-2xl font-bold text-slate-900 mb-1">{displayName}</h4>
          <p className="text-base text-slate-600 mb-2">{subtitle}</p>
          {headline && (
            <p className="mt-3 text-sm leading-relaxed text-slate-700">{headline}</p>
          )}
        </div>
        <div className="text-right text-sm text-slate-600 space-y-1 flex-shrink-0">
          <p className="font-bold text-slate-800 text-lg">{persona.age} lat</p>
          <p className="text-xs">{locationLabel}</p>
        </div>
      </div>

      {/* Najważniejsze fakty */}
      <section>
        <h5 className="text-base font-bold text-slate-900 mb-3">Najważniejsze fakty</h5>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl border-2 border-slate-200 bg-slate-50 p-4">
            <span className="block text-slate-600 mb-1.5 font-medium text-xs">Wykształcenie</span>
            <span className="text-slate-900 font-semibold text-sm">
              {persona.education_level ?? '—'}
            </span>
          </div>
          <div className="rounded-xl border-2 border-slate-200 bg-slate-50 p-4">
            <span className="block text-slate-600 mb-1.5 font-medium text-xs">Dochód</span>
            <span className="text-slate-900 font-semibold text-sm">
              {persona.income_bracket ?? '—'}
            </span>
          </div>
          <div className="col-span-2 rounded-xl border-2 border-slate-200 bg-slate-50 p-4">
            <span className="block text-slate-600 mb-1.5 font-medium text-xs">Stanowisko</span>
            <span className="text-slate-900 font-semibold text-sm">
              {persona.occupation ?? 'Brak danych'}
            </span>
          </div>
        </div>
      </section>

      {/* Profil osobowości */}
      <section>
        <h5 className="text-base font-bold text-slate-900 mb-3">Profil osobowości</h5>
        <div className="space-y-3">
          {personalityTraits.map(({ label, value }) => (
            <div key={label} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm text-slate-700">
                <span className="font-medium">{label}</span>
                <span className="font-bold text-slate-900">
                  {value !== null && value !== undefined ? `${Math.round(value * 100)}%` : '—'}
                </span>
              </div>
              <div className="h-2.5 rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.max(0, Math.min(1, value ?? 0)) * 100}%`,
                    backgroundColor: getPersonalityColor(label, value ?? 0),
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Kluczowe wartości */}
      {(persona.values && persona.values.length > 0) && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Kluczowe wartości</h5>
          <div className="flex flex-wrap gap-2">
            {persona.values.map((value) => (
              <span key={value} className="px-3 py-1.5 text-xs font-semibold rounded-full border-2 border-primary-200 bg-primary-50 text-primary-700">
                {value}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Zainteresowania */}
      {(persona.interests && persona.interests.length > 0) && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Zainteresowania</h5>
          <div className="flex flex-wrap gap-2">
            {persona.interests.map((interest) => (
              <span key={interest} className="px-3 py-1.5 text-xs font-semibold rounded-full border-2 border-accent-200 bg-accent-50 text-accent-700">
                {interest}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Historia */}
      {persona.background_story && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Historia</h5>
          <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-line">
            {persona.background_story}
          </p>
        </section>
      )}

      {/* Źródła wiedzy (RAG) */}
      {showRagSection && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Źródła wiedzy (RAG)</h5>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            {ragContextUsed ? (
              <Badge className="bg-emerald-100 text-emerald-700 border border-emerald-200">Wykorzystano kontekst RAG</Badge>
            ) : (
              <Badge className="bg-slate-100 text-slate-600 border border-slate-200">Brak kontekstu RAG</Badge>
            )}
            {ragCitations.length === 0 && ragContextUsed && (
              <span className="text-xs text-slate-500">Brak zwróconych cytowań do wyświetlenia.</span>
            )}
          </div>
          {ragCitations.length > 0 && (
            <div className="space-y-3">
              {ragCitations.map((citation, index) => (
                <div
                  key={`${citation.document_title}-${index}`}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-4 space-y-2"
                >
                  <div className="flex items-start gap-2">
                    <Quote className="w-4 h-4 text-slate-400 mt-1" />
                    <div className="space-y-1">
                      <p className="text-sm text-slate-700 leading-relaxed">{citation.chunk_text}</p>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        <span className="font-semibold text-slate-600">{citation.document_title}</span>
                        <span>•</span>
                        <span>trafność {Math.round(citation.relevance_score * 100)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
