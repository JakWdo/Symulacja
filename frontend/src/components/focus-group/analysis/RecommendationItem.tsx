import React from 'react';
import { useTranslation } from 'react-i18next';
import { Badge } from '@/components/ui/badge';
import ReactMarkdown from 'react-markdown';
import { normalizeMarkdown } from '@/lib/markdown';

interface RecommendationItemProps {
  recommendation: string;
  priority?: 'high' | 'medium' | 'low';
  className?: string;
}

/**
 * Recommendation Item Component
 * Displays individual strategic recommendation with priority badge
 */
export const RecommendationItem: React.FC<RecommendationItemProps> = ({
  recommendation,
  priority,
  className = '',
}) => {
  const { t } = useTranslation('focusGroups');

  const priorityColors = {
    high: 'bg-error/10 text-error border-error/30',
    medium: 'bg-warning/10 text-warning border-warning/30',
    low: 'bg-success/10 text-success border-success/30',
  };

  const getPriorityLabel = (priority: 'high' | 'medium' | 'low'): string => {
    return t(`analysis.recommendations.priority.${priority}`);
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
          {normalizeMarkdown(recommendation)}
        </ReactMarkdown>
      </div>
      {priority && (
        <Badge variant="outline" className={`rounded-figma-inner shrink-0 text-xs ${priorityColors[priority]}`}>
          {getPriorityLabel(priority)}
        </Badge>
      )}
    </div>
  );
};
