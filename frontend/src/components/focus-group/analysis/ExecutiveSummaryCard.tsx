import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Logo } from '@/components/ui/logo';
import ReactMarkdown from 'react-markdown';
import { normalizeMarkdown } from '@/lib/markdown';
import { useDateFormat } from '@/hooks/useDateFormat';

interface ExecutiveSummaryCardProps {
  summary: string;
  metadata?: {
    generated_at: string;
    model_used: string;
    total_responses: number;
    total_participants: number;
    questions_asked?: number;
  };
  className?: string;
}

/**
 * Executive Summary Card with Sight logo and metadata
 * Displays AI-generated executive summary with participant stats
 */
export const ExecutiveSummaryCard: React.FC<ExecutiveSummaryCardProps> = ({
  summary,
  metadata,
  className = '',
}) => {
  const { t } = useTranslation('focusGroups');
  const { formatDate } = useDateFormat();

  return (
    <Card className={`bg-card border border-border shadow-sm ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo className="w-6 h-6" transparent />
            <CardTitle className="text-card-foreground font-crimson text-xl">
              {t('analysis.executiveSummary.title')}
            </CardTitle>
          </div>
          {metadata && (
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>
                {t('analysis.executiveSummary.participants', {
                  count: metadata.total_participants,
                })}
              </span>
              <span>•</span>
              <span>
                {t('analysis.executiveSummary.questions', {
                  count: metadata.questions_asked || 0,
                })}
              </span>
              <span>•</span>
              <span>
                {t('analysis.executiveSummary.responses', {
                  count: metadata.total_responses,
                })}
              </span>
            </div>
          )}
        </div>
        {metadata && (
          <p className="text-xs text-muted-foreground mt-1">
            {t('analysis.executiveSummary.generated', {
              date: formatDate(metadata.generated_at),
              model: metadata.model_used,
            })}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm max-w-none text-muted-foreground bg-muted/30 rounded-figma-inner p-6 border border-border/50">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="leading-relaxed mb-3 last:mb-0">{children}</p>,
              strong: ({ children }) => <strong className="text-card-foreground font-semibold">{children}</strong>,
              ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 my-2">{children}</ul>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            }}
          >
            {normalizeMarkdown(summary)}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
};
