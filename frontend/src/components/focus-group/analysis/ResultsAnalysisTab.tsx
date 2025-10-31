import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Brain, RefreshCw, AlertCircle } from 'lucide-react';
import { Logo } from '@/components/ui/logo';
import { ExecutiveSummaryCard } from './ExecutiveSummaryCard';
import { KeyInsightsGrid } from './KeyInsightsGrid';
import { SurprisingFindingsCard } from './SurprisingFindingsCard';
import { SegmentAnalysisSection } from './SegmentAnalysisSection';
import { StrategicRecommendationsCard } from './StrategicRecommendationsCard';
import { AISummarySkeleton } from './AISummarySkeleton';
import { useFocusGroupAnalysis } from '@/hooks/focus-group/useFocusGroupAnalysis';
import { useRegenerateAnalysis } from '@/hooks/focus-group/useRegenerateAnalysis';
import { useTranslation } from 'react-i18next';

interface ResultsAnalysisTabProps {
  focusGroupId: string;
}

/**
 * Tab z analizą AI (Podsumowanie AI)
 */
export const ResultsAnalysisTab: React.FC<ResultsAnalysisTabProps> = ({ focusGroupId }) => {
  const { data: aiSummary, isLoading, error } = useFocusGroupAnalysis(focusGroupId);
  const regenerateMutation = useRegenerateAnalysis();
  const { t } = useTranslation('focusGroups');

  const handleRegenerate = () => {
    regenerateMutation.mutate({ focusGroupId, useProModel: false });
  };

  // Loading state
  if (isLoading) {
    return <AISummarySkeleton />;
  }

  // Error state (404 = nie wygenerowano jeszcze)
  if (error) {
    const is404 = error instanceof Error && error.message.includes('404');

    return (
      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="py-12 text-center space-y-4">
          {is404 ? (
            <>
              <Brain className="w-12 h-12 text-muted-foreground mx-auto" />
              <h3 className="text-lg font-medium text-card-foreground">
                {t('analysis.aiSummary.notGeneratedTitle')}
              </h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                {t('analysis.aiSummary.notGeneratedDescription')}
              </p>
              <Button
                onClick={handleRegenerate}
                disabled={regenerateMutation.isPending}
                className="bg-figma-primary hover:bg-figma-primary/90 text-white"
              >
                {regenerateMutation.isPending ? (
                  <>
                    <Logo className="w-4 h-4 mr-2" spinning />
                    {t('analysis.aiSummary.generating')}
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    {t('analysis.aiSummary.generateButton')}
                  </>
                )}
              </Button>
            </>
          ) : (
            <>
              <AlertCircle className="w-12 h-12 text-destructive mx-auto" />
              <h3 className="text-lg font-medium text-destructive">
                {t('analysis.aiSummary.errorTitle')}
              </h3>
              <p className="text-sm text-muted-foreground">
                {error instanceof Error ? error.message : t('analysis.aiSummary.errorUnknown')}
              </p>
              <Button onClick={handleRegenerate} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                {t('analysis.aiSummary.retryButton')}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    );
  }

  // Success state - display AI summary
  if (!aiSummary) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header z regenerate button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-card-foreground font-crimson">
            {t('analysis.aiSummary.title')}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            {t('analysis.aiSummary.subtitle')}
          </p>
        </div>
        <Button
          onClick={handleRegenerate}
          disabled={regenerateMutation.isPending}
          variant="outline"
          size="sm"
        >
          {regenerateMutation.isPending ? (
            <>
              <Logo className="w-4 h-4 mr-2" spinning />
              {t('analysis.aiSummary.regenerateLoading')}
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              {t('analysis.aiSummary.regenerateButton')}
            </>
          )}
        </Button>
      </div>

      {/* Executive Summary */}
      <ExecutiveSummaryCard
        summary={aiSummary.executive_summary}
        metadata={aiSummary.metadata}
      />

      {/* Key Insights */}
      {aiSummary.key_insights && aiSummary.key_insights.length > 0 && (
        <KeyInsightsGrid insights={aiSummary.key_insights} />
      )}

      {/* Surprising Findings */}
      {aiSummary.surprising_findings && aiSummary.surprising_findings.length > 0 && (
        <SurprisingFindingsCard findings={aiSummary.surprising_findings} />
      )}

      {/* Segment Analysis */}
      {aiSummary.segment_analysis && Object.keys(aiSummary.segment_analysis).length > 0 && (
        <SegmentAnalysisSection
          segmentAnalysis={aiSummary.segment_analysis}
          totalParticipants={aiSummary.metadata.total_participants}
        />
      )}

      {/* Strategic Recommendations */}
      {aiSummary.recommendations && aiSummary.recommendations.length > 0 && (
        <StrategicRecommendationsCard recommendations={aiSummary.recommendations} />
      )}
    </div>
  );
};
