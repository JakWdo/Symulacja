import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NumberedBadge } from './NumberedBadge';
import ReactMarkdown from 'react-markdown';

interface KeyInsightsGridProps {
  insights: string[];
  className?: string;
}

/**
 * Grid 2x2 z kluczowymi wnioskami (numbered badges)
 */
export const KeyInsightsGrid: React.FC<KeyInsightsGridProps> = ({
  insights,
  className = '',
}) => {
  return (
    <Card className={`bg-card border border-border shadow-sm ${className}`}>
      <CardHeader>
        <CardTitle className="text-card-foreground font-crimson text-xl">
          Kluczowe Wnioski
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Najważniejsze odkrycia z dyskusji
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insights.slice(0, 4).map((insight, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-4 bg-muted/30 rounded-figma-inner border border-border/50"
            >
              <NumberedBadge number={index + 1} />
              <div className="flex-1 prose prose-sm max-w-none text-muted-foreground">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <span className="leading-relaxed">{children}</span>,
                    strong: ({ children }) => <strong className="text-card-foreground font-semibold">{children}</strong>,
                  }}
                >
                  {insight}
                </ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
