import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { normalizeMarkdown } from '@/lib/markdown';

interface SurprisingFindingsCardProps {
  findings: string[];
  className?: string;
}

/**
 * Surprising Findings Card Component
 * Displays unexpected insights and patterns from focus group discussion
 */
export const SurprisingFindingsCard: React.FC<SurprisingFindingsCardProps> = ({
  findings,
  className = '',
}) => {
  const { t } = useTranslation('focusGroups');

  if (!findings || findings.length === 0) {
    return null;
  }

  return (
    <Card className={`bg-card border border-border shadow-sm ${className}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-figma-yellow" />
          <CardTitle className="text-card-foreground font-crimson text-xl">
            {t('analysis.surprisingFindings.title')}
          </CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          {t('analysis.surprisingFindings.description')}
        </p>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {findings.map((finding, index) => (
            <li
              key={index}
              className="flex items-start gap-3 p-4 bg-figma-yellow/5 rounded-figma-inner border border-figma-yellow/20"
            >
              <div className="w-2 h-2 rounded-full bg-figma-yellow shrink-0 mt-2" />
              <div className="flex-1 prose prose-sm max-w-none text-muted-foreground">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <span className="leading-relaxed">{children}</span>,
                    strong: ({ children }) => <strong className="text-card-foreground font-semibold">{children}</strong>,
                  }}
                >
                  {normalizeMarkdown(finding)}
                </ReactMarkdown>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
};
