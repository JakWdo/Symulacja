import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Tooltip } from 'recharts';
import { X, Sparkles, Clock, BookOpen } from 'lucide-react';
import type { Persona, PersonaInsight } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { normalizeMarkdown } from '@/lib/markdown';

const NAME_FROM_STORY_REGEX = /^(?<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s/;

function guessNameFromStory(story?: string | null) {
  if (!story) return null;
  const match = story.trim().match(NAME_FROM_STORY_REGEX);
  return match?.groups?.name ?? null;
}

function getPersonaDisplayName(persona: Persona) {
  if (persona.full_name && persona.full_name.trim()) {
    return persona.full_name.trim();
  }
  const inferred = guessNameFromStory(persona.background_story);
  if (inferred) {
    return inferred;
  }
  const genderLabel = persona.gender ? `${persona.gender.charAt(0).toUpperCase()}${persona.gender.slice(1)}` : 'Persona';
  return `${genderLabel} ${persona.age}`;
}

function formatLocationLabel(location?: string | null) {
  return location ?? 'lokalizacja nieznana';
}

interface PersonaHistory {
  persona_id: string;
  total_events: number;
  events: Array<{
    id: string;
    event_type: string;
    event_data: Record<string, unknown>;
    timestamp: string;
    focus_group_id: string | null;
  }>;
}

interface PersonaInsightDrawerProps {
  persona: Persona | null;
  insight: PersonaInsight | undefined;
  history: PersonaHistory | undefined;
  loading: boolean;
  historyLoading: boolean;
  onClose: () => void;
}

export function PersonaInsightDrawer({
  persona,
  insight,
  history,
  loading,
  historyLoading,
  onClose,
}: PersonaInsightDrawerProps) {
  if (!persona) {
    return null;
  }

  const displayName = getPersonaDisplayName(persona);
  const subtitle = persona.persona_title?.trim() || persona.occupation?.trim();
  const locationLabel = formatLocationLabel(persona.location);
  const headline = persona.headline?.trim();

  const traitScores = Object.entries(insight?.trait_scores ?? {}).map(([trait, value]) => ({
    trait: trait.replace(/_/g, ' '),
    value: Math.round((value ?? 0) * 100),
  }));

  const expectations = insight?.expectations ?? [];

  const expectationItems = expectations.length > 0 ? expectations : [
    'Brak dodatkowych oczekiwań – skup się na spójności narracji.',
  ];

  return (
    <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white shadow-2xl border-l border-slate-200 flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{displayName}</h3>
          <p className="text-xs text-slate-500">
            {persona.age} lat • {locationLabel}
          </p>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
          )}
          {headline && (
            <p className="text-xs text-slate-500 mt-1 italic">{headline}</p>
          )}
        </div>
        <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100" aria-label="Zamknij panel">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        <section>
          <h4 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary-500" />
            Oczekiwania i motywacje
          </h4>
          {loading ? (
            <p className="text-xs text-slate-500">Ładowanie...</p>
          ) : (
            <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
              {expectationItems.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Cechy psychograficzne</h4>
          {traitScores.length > 0 ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={traitScores} outerRadius="80%">
                  <PolarGrid stroke="#cbd5f5" />
                  <PolarAngleAxis dataKey="trait" tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(value: number) => `${value}%`} />
                  <Radar
                    name="Intensywność"
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Brak danych o cechach.</p>
          )}
        </section>

        <section>
          <h4 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-accent-500" />
            Tło i zainteresowania
          </h4>
          <div className="text-xs text-slate-600 space-y-2">
            {persona.background_story && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 leading-relaxed prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {normalizeMarkdown(persona.background_story)}
                </ReactMarkdown>
              </div>
            )}
            {persona.values && persona.values.length > 0 && (
              <p><span className="font-semibold">Wartości:</span> {persona.values.join(', ')}</p>
            )}
            {persona.interests && persona.interests.length > 0 && (
              <p><span className="font-semibold">Zainteresowania:</span> {persona.interests.join(', ')}</p>
            )}
          </div>
        </section>

        <section>
          <h4 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-500" />
            Historia interakcji
          </h4>
          {historyLoading ? (
            <p className="text-xs text-slate-500">Ładowanie historii...</p>
          ) : history && history.events.length > 0 ? (
            <ol className="space-y-3 text-xs text-slate-600">
              {history.events.map((event) => (
                <li key={event.id} className="border-l-2 border-primary-200 pl-3">
                  <p className="font-medium text-slate-800 capitalize">{event.event_type.replace(/_/g, ' ')}</p>
                  {'question' in event.event_data && (
                    <p className="mt-1">{(event.event_data as any).question}</p>
                  )}
                  {'response' in event.event_data && (
                    <p className="italic text-slate-500">{(event.event_data as any).response}</p>
                  )}
                  <p className="text-[10px] text-slate-400 mt-1">{new Date(event.timestamp).toLocaleString()}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-xs text-slate-500">Brak zarejestrowanych zdarzeń.</p>
          )}
        </section>
      </div>
    </aside>
  );
}
