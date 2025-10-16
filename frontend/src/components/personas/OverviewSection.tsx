import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
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
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: 'easeOut',
      },
    },
  };

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
      fromRecord(orchestration, 'segment_name'),
      fromRecord(ragDetails, 'segment_name'),
      persona.segment_name,
    );

    const segmentId = resolveString(
      fromRecord(orchestration, 'segment_id'),
      fromRecord(ragDetails, 'segment_id'),
      persona.segment_id,
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
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Basic Info Card */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Podstawowe informacje</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Imię i nazwisko</p>
                <p className="text-foreground font-medium">{persona.full_name || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Wiek</p>
                <p className="text-foreground font-medium">{persona.age} lat</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Lokalizacja</p>
                <p className="text-foreground font-medium">{persona.location || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Zawód</p>
                <p className="text-foreground font-medium">{persona.occupation || 'Nie podano'}</p>
              </div>
              {segmentInfo.segmentName && (
                <div>
                  <p className="text-sm text-muted-foreground">Segment społeczny</p>
                  <p className="text-foreground font-medium">
                    {segmentInfo.segmentName}
                  </p>
                </div>
              )}
            </div>
            {persona.headline && (
              <div className="rounded-lg bg-muted/30 border border-border/40 p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                  Nagłówek persony
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {persona.headline}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Segment Context Card */}
      {segmentInfo.segmentName && (segmentInfo.segmentSocialContext || segmentInfo.segmentDescription) && (
        <motion.div variants={itemVariants}>
          <Card className="border-l-4 border-l-primary">
            <CardHeader className="pb-2 space-y-2">
              <div className="flex flex-wrap items-center gap-3">
                <CardTitle className="text-2xl font-bold text-foreground">
                  {segmentInfo.segmentName}
                </CardTitle>
                {segmentInfo.segmentId && (
                  <Badge variant="outline" className="text-xs uppercase tracking-wide">
                    Segment {segmentInfo.segmentId}
                  </Badge>
                )}
              </div>
              {segmentInfo.segmentDescription && (
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {segmentInfo.segmentDescription}
                </p>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {segmentInfo.segmentSocialContext && (
                <p className="text-base text-foreground leading-relaxed">
                  {segmentInfo.segmentSocialContext}
                </p>
              )}

              {segmentInfo.segmentCharacteristics.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    Kluczowe cechy segmentu
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
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
