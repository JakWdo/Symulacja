import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import ReactMarkdown from 'react-markdown';
import { normalizeMarkdown } from '@/lib/markdown';

interface SegmentCardProps {
  segmentName: string;
  analysis: string;
  percentage?: number;
  className?: string;
}

/**
 * Segment Card Component
 * Displays individual segment analysis with participant percentage
 */
export const SegmentCard: React.FC<SegmentCardProps> = ({
  segmentName,
  analysis,
  percentage,
  className = '',
}) => {
  const { t } = useTranslation('focusGroups');

  return (
    <Card className={`rounded-figma-inner border-border ${className}`}>
      <CardContent className="pt-6 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-crimson text-lg font-semibold text-card-foreground">
            {segmentName}
          </h3>
          {percentage !== undefined && (
            <Badge variant="outline" className="rounded-figma-inner shrink-0">
              {t('analysis.segments.participantPercentage', { percentage })}
            </Badge>
          )}
        </div>
        <div className="prose prose-sm max-w-none text-muted-foreground">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="leading-relaxed mb-2">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-5 space-y-1">{children}</ul>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            }}
          >
            {normalizeMarkdown(analysis)}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
};
