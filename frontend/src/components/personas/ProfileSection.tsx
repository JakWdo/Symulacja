import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { PersonaDetailsResponse } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { normalizeMarkdown } from '@/lib/markdown';

interface ProfileSectionProps {
  persona: PersonaDetailsResponse;
}

/**
 * Sekcja profilu persony - demografia, wartości i zainteresowania, historia
 *
 * Wyświetla:
 * - Podstawowe dane demograficzne (wiek, płeć, lokalizacja, wykształcenie, dochód)
 * - Wartości i zainteresowania
 * - Background story
 */
export function ProfileSection({ persona }: ProfileSectionProps) {
  const { t } = useTranslation('personas');

  // Extract persona uniqueness from rag_context_details
  const personaUniqueness = useMemo(() => {
    const ragDetails = (persona.rag_context_details ?? {}) as Record<string, unknown>;
    const orchestration = (ragDetails['orchestration_reasoning'] ?? {}) as Record<string, unknown>;

    // persona_uniqueness będzie stringiem
    const uniqueness = orchestration['persona_uniqueness'];
    if (typeof uniqueness === 'string' && uniqueness.trim().length > 0) {
      return uniqueness.trim();
    }
    return null;
  }, [persona.rag_context_details]);

  return (
    <div className="space-y-6">
      {/* Values & Interests Card */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('details.profile.valuesAndInterests.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Values */}
            {persona.values && persona.values.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">{t('details.profile.valuesAndInterests.values')}</p>
                <div className="flex flex-wrap gap-2">
                  {persona.values.map((value, idx) => (
                    <div key={idx}>
                      <Badge
                        variant="outline"
                        className="border-primary text-primary hover:bg-primary/10 transition-colors cursor-default"
                      >
                        {value}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Interests */}
            {persona.interests && persona.interests.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">{t('details.profile.valuesAndInterests.interests')}</p>
                <div className="flex flex-wrap gap-2">
                  {persona.interests.map((interest, idx) => (
                    <div key={idx}>
                      <Badge
                        variant="secondary"
                        className="bg-secondary/50 hover:bg-secondary transition-colors cursor-default"
                      >
                        {interest}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Background Story Card */}
      {persona.background_story && (
        <div>
          <Card className="border-l-4 border-l-primary">
            <CardHeader>
              <CardTitle className="text-base">{t('details.profile.backgroundStory.title')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none text-foreground">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {normalizeMarkdown(persona.background_story)}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Persona Uniqueness Card - NEW */}
      {personaUniqueness && (
        <div>
          <Card className="border-l-4 border-l-accent bg-accent/5">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-accent" />
                <CardTitle className="text-base">
                  {persona.full_name?.split(' ')[0]
                    ? t('details.profile.uniqueness.title', { name: persona.full_name.split(' ')[0] })
                    : t('details.profile.uniqueness.titleDefault')}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="prose prose-sm max-w-none text-foreground">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {normalizeMarkdown(personaUniqueness)}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
