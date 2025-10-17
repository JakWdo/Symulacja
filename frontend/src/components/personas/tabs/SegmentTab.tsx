import { memo } from 'react';
import { NarrativeText } from '../NarrativeText';
import { CitationsCollapsible } from '../CitationsCollapsible';
import type { PersonaNarratives, NarrativeStatus } from '@/types';

interface SegmentTabProps {
  narratives: PersonaNarratives | undefined;
  status: NarrativeStatus;
  onRetry?: () => void;
}

/**
 * SegmentTab - zakładka "Segment" w modalu Persona Details
 *
 * Wyświetla narratywy dotyczące segmentu społecznego:
 * - segment_hero: Wprowadzenie do segmentu (storytelling, 2-3 zdania)
 * - segment_significance: Dlaczego ten segment jest istotny? (trends, magnitude, impact)
 * - evidence_context: Kontekst dowodowy (background + key citations)
 *
 * Layout: Stack vertical (space-y-6)
 */
export const SegmentTab = memo<SegmentTabProps>(({ narratives, status, onRetry }) => {
  return (
    <div className="space-y-6" role="tabpanel" aria-label="Informacje o segmencie">
      <NarrativeText
        title="Wprowadzenie do segmentu"
        content={narratives?.segment_hero || null}
        status={status}
        onRetry={onRetry}
      />

      <NarrativeText
        title="Dlaczego ten segment jest istotny?"
        content={narratives?.segment_significance || null}
        status={status}
        onRetry={onRetry}
      />

      {narratives?.evidence_context && (
        <>
          <NarrativeText
            title="Kontekst dowodowy"
            content={narratives.evidence_context.background_narrative}
            status={status}
            onRetry={onRetry}
          />

          <CitationsCollapsible citations={narratives.evidence_context.key_citations} />
        </>
      )}
    </div>
  );
});

SegmentTab.displayName = 'SegmentTab';
