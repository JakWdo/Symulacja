import { memo } from 'react';
import { NarrativeText } from '../NarrativeText';
import type { PersonaNarratives, NarrativeStatus } from '@/types';

interface PersonTabProps {
  narratives: PersonaNarratives | undefined;
  status: NarrativeStatus;
  onRetry?: () => void;
}

/**
 * PersonTab - zakładka "Osoba" w modalu Persona Details
 *
 * Wyświetla narratywy dotyczące indywidualnej persony:
 * - person_profile: Kim jest ta osoba? (background, demographics, lifestyle)
 * - person_motivations: Co nią kieruje? (values, goals, fears, desires)
 *
 * Layout: Stack vertical (space-y-6)
 */
export const PersonTab = memo<PersonTabProps>(({ narratives, status, onRetry }) => {
  return (
    <div className="space-y-6" role="tabpanel" aria-label="Informacje o osobie">
      <NarrativeText
        title="Kim jest ta osoba?"
        content={narratives?.person_profile || null}
        status={status}
        onRetry={onRetry}
      />

      <NarrativeText
        title="Co nią kieruje?"
        content={narratives?.person_motivations || null}
        status={status}
        onRetry={onRetry}
      />
    </div>
  );
});

PersonTab.displayName = 'PersonTab';
