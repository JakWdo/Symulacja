import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { PersonaDetailsResponse } from '@/types';

interface OverviewSectionProps {
  persona: PersonaDetailsResponse;
}

/**
 * Sekcja Overview - podstawowe informacje persony z segment info
 */
export function OverviewSection({ persona }: OverviewSectionProps) {
  const { t } = useTranslation('personas');

  const segmentInfo = useMemo(() => {
    const ragDetails = (persona.rag_context_details ?? {}) as Record<string, unknown>;
    const orchestration = (ragDetails['orchestration_reasoning'] ?? {}) as Record<string, unknown>;

    const fromRecord = (source: Record<string, unknown>, key: string): unknown => {
      return Object.prototype.hasOwnProperty.call(source, key) ? source[key] : undefined;
    };

    const resolveString = (...candidates: Array<unknown>): string | null => {
      for (const candidate of candidates) {
        if (typeof candidate === 'string' && candidate.trim().length > 0) {
          return candidate.trim();
        }
      }
      return null;
    };

    const resolveArray = (...candidates: Array<unknown>): string[] => {
      for (const candidate of candidates) {
        if (Array.isArray(candidate) && candidate.length > 0) {
          return candidate.map((item) => String(item));
        }
      }
      return [];
    };

    const segmentName = resolveString(
      persona.segment_name,
      fromRecord(orchestration, 'segment_name'),
      fromRecord(ragDetails, 'segment_name'),
    );

    const segmentId = resolveString(
      persona.segment_id,
      fromRecord(orchestration, 'segment_id'),
      fromRecord(ragDetails, 'segment_id'),
    );

    const segmentDescription = resolveString(
      fromRecord(orchestration, 'segment_description'),
      fromRecord(ragDetails, 'segment_description'),
      persona.persona_title,
    );

    const segmentSocialContext = resolveString(
      fromRecord(orchestration, 'segment_social_context'),
      fromRecord(ragDetails, 'segment_social_context'),
      fromRecord(ragDetails, 'segment_context'),
      fromRecord(ragDetails, 'overall_context'),
      fromRecord(ragDetails, 'graph_context'),
    );

    const segmentCharacteristics = resolveArray(
      fromRecord(orchestration, 'segment_characteristics'),
      fromRecord(ragDetails, 'segment_characteristics'),
    );

    return {
      segmentName,
      segmentId,
      segmentDescription,
      segmentSocialContext,
      segmentCharacteristics,
    };
  }, [persona]);

  return (
    <div className="space-y-6">
      {/* Basic Info Card */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('details.overview.basicInfo')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">{t('details.overview.fullName')}</p>
                <p className="text-foreground font-medium">{persona.full_name || t('details.overview.notSpecified')}</p>
              </div>
              {segmentInfo.segmentName && (
                <div>
                  <p className="text-sm text-muted-foreground">{t('details.overview.socialSegment')}</p>
                  <p className="text-foreground font-medium">
                    {segmentInfo.segmentName}
                  </p>
                </div>
              )}
            </div>
            {persona.headline && (
              <div className="rounded-lg bg-muted/30 border border-border/40 p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                  {t('details.overview.headline')}
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {persona.headline}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Segment Badge Card - Simplified */}
      {segmentInfo.segmentName && (
        <div>
          <Card className="border border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-xl font-bold text-foreground">
                {segmentInfo.segmentName}
              </CardTitle>
            </CardHeader>
            {segmentInfo.segmentCharacteristics.length > 0 && (
              <CardContent>
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    {t('details.reasoning.segmentSection.characteristicsTitle')}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {segmentInfo.segmentCharacteristics.map((characteristic, idx) => (
                      <Badge
                        key={`${characteristic}-${idx}`}
                        variant="secondary"
                        className="bg-primary/10 text-primary border-primary/30"
                      >
                        {characteristic}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
