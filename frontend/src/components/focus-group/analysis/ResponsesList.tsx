import React, { useMemo } from 'react';
import { ResponseCard } from './ResponseCard';
import type { Persona, FocusGroupResponses } from '@/types';

interface ResponsesListProps {
  responses: FocusGroupResponses;
  personas: Persona[];
  searchQuery: string;
  selectedPersonaId: string;
  selectedQuestionIndex: string;
  className?: string;
}

/**
 * Lista odpowiedzi z filtrowaniem
 */
export const ResponsesList: React.FC<ResponsesListProps> = ({
  responses,
  personas,
  searchQuery,
  selectedPersonaId,
  selectedQuestionIndex,
  className = '',
}) => {
  const filteredResponses = useMemo(() => {
    let filtered = responses.questions;

    // Filtruj po pytaniu
    if (selectedQuestionIndex !== 'all') {
      const index = parseInt(selectedQuestionIndex, 10);
      filtered = [filtered[index]];
    }

    // Filtruj po personie i search query
    return filtered.map((q) => ({
      ...q,
      responses: q.responses.filter((r) => {
        // Filtr persony
        if (selectedPersonaId !== 'all' && r.persona_id !== selectedPersonaId) {
          return false;
        }

        // Filtr search query
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          const personaMatch = personas
            .find((p) => p.id === r.persona_id)
            ?.full_name?.toLowerCase()
            .includes(query);
          const responseMatch = r.response.toLowerCase().includes(query);
          return personaMatch || responseMatch;
        }

        return true;
      }),
    })).filter((q) => q.responses.length > 0); // Usuń pytania bez odpowiedzi
  }, [responses, selectedPersonaId, selectedQuestionIndex, searchQuery, personas]);

  if (filteredResponses.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">
          Brak odpowiedzi spełniających kryteria filtrowania
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {filteredResponses.map((question, qIdx) => (
        <div key={qIdx} className="space-y-4">
          {/* Question Header */}
          <div className="flex items-center gap-3">
            <div className="bg-figma-primary/10 border border-figma-primary/30 rounded px-3 py-1">
              <span className="text-sm font-semibold text-figma-primary">Q{qIdx + 1}</span>
            </div>
            <h4 className="text-card-foreground font-semibold">{question.question}</h4>
          </div>

          {/* Responses */}
          <div className="ml-0 md:ml-12 space-y-3">
            {question.responses.map((response, rIdx) => {
              const persona = personas.find((p) => p.id === response.persona_id);
              const initials =
                persona?.full_name
                  ?.split(' ')
                  .map((n) => n[0])
                  .join('') || 'P';
              const personaName =
                persona?.full_name || `Persona ${response.persona_id.slice(0, 8)}`;

              return (
                <ResponseCard
                  key={`${response.persona_id}-${rIdx}`}
                  personaName={personaName}
                  personaInitials={initials}
                  response={response.response}
                  timestamp={response.created_at}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
