import React from 'react';
import { Badge } from '@/components/ui/badge';
import ReactMarkdown from 'react-markdown';

interface RecommendationItemProps {
  recommendation: string;
  priority?: 'high' | 'medium' | 'low';
  className?: string;
}

/**
 * Pojedyncza rekomendacja strategiczna z priority badge
 */
export const RecommendationItem: React.FC<RecommendationItemProps> = ({
  recommendation,
  priority,
  className = '',
}) => {
  const priorityColors = {
    high: 'bg-figma-red/10 text-figma-red border-figma-red/30',
    medium: 'bg-figma-yellow/10 text-figma-yellow border-figma-yellow/30',
    low: 'bg-figma-green/10 text-figma-green border-figma-green/30',
  };

  const priorityLabels = {
    high: 'Wysoki priorytet',
    medium: 'Średni priorytet',
    low: 'Niski priorytet',
  };

  return (
    <div className={`flex items-start gap-3 p-4 bg-muted/50 rounded-figma-inner border border-border/50 ${className}`}>
      <div className="flex-1 prose prose-sm max-w-none text-muted-foreground">
        <ReactMarkdown
          components={{
            p: ({ children }) => <span className="leading-relaxed">{children}</span>,
            strong: ({ children }) => <strong className="text-card-foreground font-semibold">{children}</strong>,
          }}
        >
          {recommendation}
        </ReactMarkdown>
      </div>
      {priority && (
        <Badge variant="outline" className={`rounded-figma-inner shrink-0 text-xs ${priorityColors[priority]}`}>
          {priorityLabels[priority]}
        </Badge>
      )}
    </div>
  );
};
