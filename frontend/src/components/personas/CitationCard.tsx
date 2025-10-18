import { memo } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText } from 'lucide-react';
import type { Citation } from '@/types';

interface CitationCardProps {
  citation: Citation;
  index: number;
}

/**
 * CitationCard - wyświetla pojedynczą cytację z dokumentu RAG
 *
 * - Document title jako nagłówek
 * - Relevance score jako badge
 * - Fragment tekstu z dokumentu
 * - Animacja wejścia (fade-in z delay)
 */
export const CitationCard = memo<CitationCardProps>(({ citation, index }) => {
  const getRelevanceColor = (score: number): string => {
    if (score >= 0.8) {
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    }
    if (score >= 0.6) {
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    }
    return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
  };

  const documentTitle =
    (citation.document_title && citation.document_title.trim()) ||
    (citation.source && citation.source.trim()) ||
    'Źródło nieznane';

  const excerpt =
    (citation.chunk_text && citation.chunk_text.trim()) ||
    (citation.insight && citation.insight.trim()) ||
    'Brak dostępnego fragmentu.';

  const numericScore =
    typeof citation.relevance_score === 'number' ? citation.relevance_score : null;
  const relevanceNote =
    typeof citation.relevance === 'string' && citation.relevance.trim().length > 0
      ? citation.relevance.trim()
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05, ease: 'easeOut' }}
    >
      <Card className="border border-border hover:border-primary/50 transition-colors">
        <CardHeader className="pb-3 space-y-2">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-2 flex-1 min-w-0">
              <FileText className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
              <CardTitle className="text-sm font-medium leading-tight break-words">
                {documentTitle}
              </CardTitle>
            </div>
            {numericScore !== null ? (
              <Badge
                variant="secondary"
                className={`shrink-0 text-xs ${getRelevanceColor(numericScore)}`}
              >
                {(numericScore * 100).toFixed(0)}%
              </Badge>
            ) : relevanceNote ? (
              <Badge variant="outline" className="shrink-0 text-xs">
                {relevanceNote}
              </Badge>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground leading-relaxed">
            {excerpt}
          </p>
          {relevanceNote && (
            <p className="text-xs text-muted-foreground mt-2">
              <span className="font-medium text-foreground">Dlaczego istotne:</span>{' '}
              {relevanceNote}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
});

CitationCard.displayName = 'CitationCard';
