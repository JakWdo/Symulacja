import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Logo } from '@/components/ui/logo';
import ReactMarkdown from 'react-markdown';

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
 * Podsumowanie Zarządcze z Sight logo i metadanymi
 */
export const ExecutiveSummaryCard: React.FC<ExecutiveSummaryCardProps> = ({
  summary,
  metadata,
  className = '',
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pl-PL', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <Card className={`bg-card border border-border shadow-sm ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo className="w-6 h-6" transparent />
            <CardTitle className="text-card-foreground font-crimson text-xl">
              Podsumowanie Zarządcze
            </CardTitle>
          </div>
          {metadata && (
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>{metadata.total_participants} uczestników</span>
              <span>•</span>
              <span>{metadata.questions_asked || 0} pytań</span>
              <span>•</span>
              <span>{metadata.total_responses} odpowiedzi</span>
            </div>
          )}
        </div>
        {metadata && (
          <p className="text-xs text-muted-foreground mt-1">
            Wygenerowano {formatDate(metadata.generated_at)} • Model: {metadata.model_used}
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
            {summary}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
};
