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
    if (score >= 0.8) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
  };

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
                {citation.document_title}
              </CardTitle>
            </div>
            <Badge
              variant="secondary"
              className={`shrink-0 text-xs ${getRelevanceColor(citation.relevance_score)}`}
            >
              {(citation.relevance_score * 100).toFixed(0)}%
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground leading-relaxed">
            {citation.chunk_text}
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
});

CitationCard.displayName = 'CitationCard';
