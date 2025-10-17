import { memo, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import { CitationCard } from './CitationCard';
import type { Citation } from '@/types';

interface CitationsCollapsibleProps {
  citations: Citation[];
  className?: string;
}

/**
 * CitationsCollapsible - rozwijana lista cytacji z dokumentów RAG
 *
 * - Sortowanie według relevance_score (descending)
 * - Collapsible UI (domyślnie zamknięte)
 * - Animowane rozwinięcie/zwinięcie
 * - Badge z liczbą cytacji
 * - Grid layout na większych ekranach
 */
export const CitationsCollapsible = memo<CitationsCollapsibleProps>(
  ({ citations, className = '' }) => {
    const [isOpen, setIsOpen] = useState(false);

    const sortedCitations = useMemo(() => {
      return [...citations].sort((a, b) => b.relevance_score - a.relevance_score);
    }, [citations]);

    if (!citations || citations.length === 0) {
      return null;
    }

    return (
      <Collapsible
        open={isOpen}
        onOpenChange={setIsOpen}
        className={`space-y-3 ${className}`}
      >
        <CollapsibleTrigger asChild>
          <Button
            variant="outline"
            className="w-full justify-between hover:bg-accent transition-colors"
            aria-label={isOpen ? 'Zwiń cytacje' : 'Rozwiń cytacje'}
          >
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              <span className="font-medium">Źródła i cytacje</span>
              <Badge variant="secondary" className="text-xs">
                {citations.length}
              </Badge>
            </div>
            {isOpen ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </Button>
        </CollapsibleTrigger>

        <AnimatePresence>
          {isOpen && (
            <CollapsibleContent forceMount>
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
                className="overflow-hidden"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  {sortedCitations.map((citation, index) => (
                    <CitationCard
                      key={`${citation.document_title}-${index}`}
                      citation={citation}
                      index={index}
                    />
                  ))}
                </div>
              </motion.div>
            </CollapsibleContent>
          )}
        </AnimatePresence>
      </Collapsible>
    );
  }
);

CitationsCollapsible.displayName = 'CitationsCollapsible';
