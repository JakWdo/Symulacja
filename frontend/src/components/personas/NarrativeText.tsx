import { memo } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { AlertCircle, WifiOff, AlertTriangle, RefreshCw } from 'lucide-react';
import type { NarrativeStatus } from '@/types';

interface NarrativeTextProps {
  title: string;
  content: string | null;
  status: NarrativeStatus;
  onRetry?: () => void;
  className?: string;
}

/**
 * NarrativeText - reusable narrative display component
 *
 * Obsługuje różne stany:
 * - loading: Skeleton loader (3-5 text blocks)
 * - ok: Normalny wyświetlenie narratywu
 * - degraded: Alert warning + narratyw
 * - offline: Alert destructive + brak narratywu
 * - timeout: Alert info + retry button
 * - pending: Skeleton loader
 *
 * Animacja: fade-in z slide-up (framer-motion)
 */
export const NarrativeText = memo<NarrativeTextProps>(
  ({ title, content, status, onRetry, className = '' }) => {
    // Loading skeleton
    if (status === 'loading' || status === 'pending') {
      return (
        <Card className={`p-6 space-y-4 ${className}`}>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </Card>
      );
    }

    // Offline state
    if (status === 'offline') {
      return (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={className}
        >
          <Alert variant="destructive">
            <WifiOff className="h-4 w-4" />
            <AlertTitle>Brak połączenia</AlertTitle>
            <AlertDescription>
              Nie udało się pobrać opisu. Sprawdź połączenie z internetem i spróbuj ponownie.
            </AlertDescription>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="mt-3"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Spróbuj ponownie
              </Button>
            )}
          </Alert>
        </motion.div>
      );
    }

    // Timeout state
    if (status === 'timeout') {
      return (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={className}
        >
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Przekroczono czas oczekiwania</AlertTitle>
            <AlertDescription>
              Generowanie opisu trwało zbyt długo. Spróbuj ponownie lub skontaktuj się z
              administratorem.
            </AlertDescription>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="mt-3"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Spróbuj ponownie
              </Button>
            )}
          </Alert>
        </motion.div>
      );
    }

    const trimmedContent = content?.trim() ?? '';
    // Handle missing content
    if (!trimmedContent) {
      if (status === 'degraded') {
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className={className}
          >
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Opis częściowo niedostępny</AlertTitle>
              <AlertDescription>
                Nie udało się wygenerować tej sekcji na podstawie dostępnych źródeł.
                Spróbuj użyć opcji „Regeneruj” lub sprawdź, czy RAG ma wymagane dokumenty.
              </AlertDescription>
            </Alert>
          </motion.div>
        );
      }
      return (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={className}
        >
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Brak danych</AlertTitle>
            <AlertDescription>
              Opis nie jest jeszcze dostępny. Spróbuj wygenerować go ponownie.
            </AlertDescription>
          </Alert>
        </motion.div>
      );
    }

    // Degraded state (show content with warning)
    const showDegradedWarning = status === 'degraded';

    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className={`space-y-4 ${className}`}
      >
        {showDegradedWarning && (
          <Alert variant="default" className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
            <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
            <AlertTitle className="text-yellow-800 dark:text-yellow-200">
              Opis może być niepełny
            </AlertTitle>
            <AlertDescription className="text-yellow-700 dark:text-yellow-300">
              Część źródeł była niedostępna podczas generowania. Opis może nie zawierać
              wszystkich informacji.
            </AlertDescription>
          </Alert>
        )}

        <Card className="border border-border">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold">{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="text-base leading-relaxed text-foreground whitespace-pre-wrap">
                {content}
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }
);

NarrativeText.displayName = 'NarrativeText';
