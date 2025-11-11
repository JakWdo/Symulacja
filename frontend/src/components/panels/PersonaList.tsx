/**
 * PersonaList - Lista person z wyszukiwarką
 *
 * Zawiera:
 * - Wyszukiwarkę person
 * - Listę person (sortowaną alfabetycznie)
 * - Selekcję aktywnej persony
 *
 * @example
 * <PersonaList
 *   personas={personas}
 *   selectedPersona={selectedPersona}
 *   onSelectPersona={setSelectedPersona}
 * />
 */

import { useMemo, useState } from 'react';
import { useAppStore } from '@/store/appStore';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Persona } from '@/types';

function guessNameFromStory(story?: string | null) {
  const NAME_FROM_STORY_REGEX = /^(?<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s/;
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

function getPersonaFirstName(persona: Persona): string {
  const fullName = getPersonaDisplayName(persona);
  // Wyciągnij tylko pierwsze imię (split po spacji, weź pierwszy element)
  const firstName = fullName.split(' ')[0];
  return firstName;
}

interface PersonaListItemProps {
  persona: Persona;
  isSelected: boolean;
}

function PersonaListItem({ persona, isSelected }: PersonaListItemProps) {
  // Use Zustand selector to prevent unnecessary re-renders
  const setSelectedPersona = useAppStore(state => state.setSelectedPersona);
  const firstName = getPersonaFirstName(persona);

  return (
    <button
      type="button"
      onClick={() => setSelectedPersona(persona)}
      className={cn(
        'w-full text-left px-4 py-3 border-l-4 transition-all hover:bg-slate-50',
        isSelected
          ? 'border-l-primary-600 bg-primary-50/50'
          : 'border-l-transparent hover:border-l-slate-300'
      )}
    >
      <p className="font-semibold text-slate-900 text-sm">{firstName}, {persona.age} lat</p>
      <p className="text-xs text-slate-500 mt-0.5">{persona.location || 'Polska'}</p>
    </button>
  );
}

interface PersonaListProps {
  personas: Persona[];
  selectedPersona: Persona | null;
}

/**
 * PersonaList Component
 */
export function PersonaList({ personas, selectedPersona }: PersonaListProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const sortedPersonas = useMemo(() => {
    if (!personas) return [];
    return [...personas].sort((a, b) => {
      const aName = (a.full_name || a.persona_title || a.occupation || '').toLowerCase();
      const bName = (b.full_name || b.persona_title || b.occupation || '').toLowerCase();
      return aName.localeCompare(bName);
    });
  }, [personas]);

  const filteredPersonas = useMemo(() => {
    if (!searchTerm.trim()) {
      return sortedPersonas;
    }
    const query = searchTerm.toLowerCase();
    return sortedPersonas.filter((persona) => {
      const haystack = [
        persona.full_name,
        persona.persona_title,
        persona.occupation,
        persona.location,
        persona.values?.join(' '),
        persona.interests?.join(' '),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [sortedPersonas, searchTerm]);

  return (
    <div className="border-r border-slate-200 flex flex-col">
      {/* Search */}
      <div className="p-3 border-b border-slate-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search personas..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
        {filteredPersonas.map((persona) => (
          <PersonaListItem
            key={persona.id}
            persona={persona}
            isSelected={selectedPersona?.id === persona.id}
          />
        ))}
      </div>
    </div>
  );
}
