import { PersonaDetailsResponse } from '@/types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import { Users } from 'lucide-react';

interface SegmentSectionProps {
  persona: PersonaDetailsResponse;
}

/**
 * SegmentSection - wyświetla segment persony + rules + similar personas.
 *
 * Zawiera:
 * - Segment name + description
 * - Social context (z orchestration_reasoning)
 * - Segment rules (age_range, gender, locations, values)
 * - "Dlaczego ta persona?" - brief z orchestration
 * - Lista podobnych person (ten sam segment_id)
 */
export function SegmentSection({ persona }: SegmentSectionProps) {
  const orchestrationReasoning = persona.rag_context_details?.orchestration_reasoning;
  const segmentRules = persona.segment_rules;
  const similarPersonas = persona.similar_personas || [];

  return (
    <div className="space-y-6">
      {/* Segment Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-muted-foreground" />
            <CardTitle>{persona.segment_name || 'Segment nieokreślony'}</CardTitle>
          </div>
          {orchestrationReasoning?.segment_description && (
            <CardDescription>{orchestrationReasoning.segment_description}</CardDescription>
          )}
        </CardHeader>

        {orchestrationReasoning?.segment_social_context && (
          <CardContent>
            <div>
              <h4 className="text-sm font-semibold mb-2">Kontekst Społeczny</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {orchestrationReasoning.segment_social_context}
              </p>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Segment Rules */}
      {segmentRules && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Reguły Segmentu</CardTitle>
            <CardDescription>Kryteria definiujące ten segment</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {segmentRules.age_range && (
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Wiek</dt>
                  <dd className="mt-1 text-sm">{segmentRules.age_range} lat</dd>
                </div>
              )}

              {segmentRules.gender_options && segmentRules.gender_options.length > 0 && (
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Płeć</dt>
                  <dd className="mt-1 text-sm">{segmentRules.gender_options.join(', ')}</dd>
                </div>
              )}

              {segmentRules.location_filters && segmentRules.location_filters.length > 0 && (
                <div className="sm:col-span-2">
                  <dt className="text-sm font-medium text-muted-foreground">Lokalizacje</dt>
                  <dd className="mt-1 flex flex-wrap gap-1">
                    {segmentRules.location_filters.map((loc, idx) => (
                      <Badge key={idx} variant="secondary">
                        {loc}
                      </Badge>
                    ))}
                  </dd>
                </div>
              )}

              {segmentRules.required_values && segmentRules.required_values.length > 0 && (
                <div className="sm:col-span-2">
                  <dt className="text-sm font-medium text-muted-foreground">Kluczowe Wartości</dt>
                  <dd className="mt-1 flex flex-wrap gap-1">
                    {segmentRules.required_values.map((value, idx) => (
                      <Badge key={idx} variant="outline">
                        {value}
                      </Badge>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          </CardContent>
        </Card>
      )}

      {/* Why This Persona */}
      {orchestrationReasoning?.brief && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dlaczego ta persona?</CardTitle>
            <CardDescription>Uzasadnienie wyboru z orchestration</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{orchestrationReasoning.brief}</p>
          </CardContent>
        </Card>
      )}

      {/* Similar Personas */}
      {similarPersonas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Podobne Persony</CardTitle>
            <CardDescription>
              Inne persony z segmentu "{persona.segment_name || 'tego segmentu'}"
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {similarPersonas.map((similar) => (
                <li key={similar.id} className="flex items-start gap-3 text-sm">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/personas/${similar.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {similar.name}
                    </Link>
                    <p className="text-muted-foreground text-xs mt-0.5">
                      {similar.distinguishing_trait}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!segmentRules && similarPersonas.length === 0 && !orchestrationReasoning?.brief && (
        <Card className="border-dashed">
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center space-y-2">
              <Users className="w-12 h-12 text-muted-foreground mx-auto" />
              <p className="text-sm text-muted-foreground">
                Brak danych segmentowych dla tej persony
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
