import React, { useMemo } from 'react';
import { Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { PersonaDetailsResponse } from '@/types';

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
      {/* Demographics Card */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dane demograficzne</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Wiek</p>
                <p className="text-foreground font-medium">{persona.age} lat</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Płeć</p>
                <p className="text-foreground font-medium">{persona.gender || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Lokalizacja</p>
                <p className="text-foreground font-medium">{persona.location || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Wykształcenie</p>
                <p className="text-foreground font-medium">{persona.education_level || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Dochód</p>
                <p className="text-foreground font-medium">{persona.income_bracket || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Zawód</p>
                <p className="text-foreground font-medium">{persona.occupation || 'Nie podano'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Values & Interests Card */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Wartości i zainteresowania</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Values */}
            {persona.values && persona.values.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">Wartości</p>
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
                <p className="text-sm text-muted-foreground mb-2">Zainteresowania</p>
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
              <CardTitle className="text-base">Historia</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {persona.background_story.split('\n\n').map((paragraph, idx) => (
                  <p
                    key={idx}
                    className="text-sm text-foreground leading-relaxed"
                  >
                    {paragraph.trim()}
                  </p>
                ))}
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
                  Dlaczego {persona.full_name?.split(' ')[0] || 'ta osoba'} jest wyjątkowa/y w swoim segmencie
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="space-y-3">
                {personaUniqueness.split('\n\n').map((paragraph, idx) => (
                  <p
                    key={idx}
                    className="text-sm text-foreground leading-relaxed"
                  >
                    {paragraph.trim()}
                  </p>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
