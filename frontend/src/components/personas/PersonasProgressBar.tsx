import React from 'react';
import { Progress } from '@/components/ui/progress';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { Info } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { formatDuration } from '@/lib/personaGeneration';

interface PersonasProgressBarProps {
  generationProgress: number;
  progressMeta: {
    duration: number;
    targetCount: number;
  };
  newlyGeneratedCount: number;
  requestedCount: number;
}

export function PersonasProgressBar({
  generationProgress,
  progressMeta,
  newlyGeneratedCount,
  requestedCount,
}: PersonasProgressBarProps) {
  const { t } = useTranslation('personas');

  return (
    <div className="rounded-lg border border-border bg-card/80 p-4 space-y-3 shadow-sm">
      {/* Header z czasem */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <SpinnerLogo className="w-4 h-4" />
          <span className="font-medium text-card-foreground">
            {t('page.generating')}
          </span>
        </div>

        {/* Szacowany czas */}
        <div className="text-xs text-muted-foreground tabular-nums">
          Czas: ~{formatDuration(progressMeta.duration)}
          {newlyGeneratedCount > 0 && (
            <span className="ml-2 text-primary font-medium">
              {newlyGeneratedCount}/{requestedCount}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <Progress value={Math.min(generationProgress, 100)} className="h-2" />

      {/* Info tooltip */}
      <div className="flex items-start gap-2 text-xs text-muted-foreground bg-muted/30 rounded p-2">
        <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
        <p className="leading-tight">
          <strong>Generowanie person trwa dłużej niż zwykle</strong> gdy używasz RAG
          (wyszukiwanie demograficzne + tworzenie briefów segmentów).
          Możesz kontynuować pracę - otrzymasz powiadomienie po zakończeniu.
        </p>
      </div>
    </div>
  );
}
