import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';
import { SegmentCard } from './SegmentCard';
import { useTranslation } from 'react-i18next';

interface SegmentAnalysisSectionProps {
  segmentAnalysis: Record<string, string>;
  totalParticipants?: number;
  className?: string;
}

/**
 * Sekcja z analizą segmentów (3 karty)
 */
export const SegmentAnalysisSection: React.FC<SegmentAnalysisSectionProps> = ({
  segmentAnalysis,
  totalParticipants,
  className = '',
}) => {
  const { t } = useTranslation('focusGroups');
  const segments = Object.entries(segmentAnalysis);

  if (segments.length === 0) {
    return null;
  }

  // Oblicz przybliżony procent dla każdego segmentu (równomiernie rozdzielone)
  const percentagePerSegment = totalParticipants && segments.length > 0
    ? Math.round(100 / segments.length)
    : undefined;

  return (
    <Card className={`bg-card border border-border shadow-sm ${className}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-figma-primary" />
          <CardTitle className="text-card-foreground font-crimson text-xl">
            {t('analysis.segments.title')}
          </CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          {t('analysis.segments.description')}
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {segments.map(([segmentName, analysis], index) => (
            <SegmentCard
              key={index}
              segmentName={segmentName}
              analysis={analysis}
              percentage={percentagePerSegment}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
