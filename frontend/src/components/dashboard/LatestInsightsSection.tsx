/**
 * Latest Insights Section - Displays latest insights with filtering and detail view
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  AlertCircle,
  Activity,
  Eye,
  CheckCircle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useLatestInsights } from '@/hooks/dashboard/useLatestInsights';
import { InsightDetailModal } from './InsightDetailModal';
import type { InsightHighlight } from '@/types/dashboard';

const INSIGHT_TYPE_ICONS = {
  opportunity: Lightbulb,
  risk: AlertCircle,
  trend: TrendingUp,
  pattern: Activity,
};

export function LatestInsightsSection() {
  const { t } = useTranslation('dashboard');
  const { data: insights, isLoading, error } = useLatestInsights(3); // Limit to 3 (Figma design)
  const [selectedInsight, setSelectedInsight] = useState<InsightHighlight | null>(null);

  if (isLoading) {
    return <LatestInsightsSkeleton />;
  }

  if (error) {
    return (
      <Card className="border-border rounded-figma-card">
        <CardHeader className="px-6 pt-6 pb-4">
          <CardTitle className="text-base font-normal text-foreground leading-[16px]">
            {t('latestInsights.title')}
          </CardTitle>
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{t('errors.loadInsights')}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!insights || insights.length === 0) {
    return (
      <Card className="border-border rounded-figma-card">
        <CardHeader className="px-6 pt-6 pb-4">
          <CardTitle className="text-base font-normal text-foreground leading-[16px]">
            {t('latestInsights.title')}
          </CardTitle>
          <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
            {t('latestInsights.subtitle')}
          </p>
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <div className="text-center py-12">
            <Lightbulb className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground font-medium mb-2">{t('latestInsights.emptyState.title')}</p>
            <p className="text-sm text-muted-foreground mb-4">
              {t('latestInsights.emptyState.description')}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="border-border rounded-figma-card">
        <CardHeader className="px-6 pt-6 pb-4">
          <CardTitle className="text-base font-normal text-foreground leading-[16px]">
            {t('latestInsights.title')}
          </CardTitle>
          <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
            {t('latestInsights.subtitle')}
          </p>
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <div className="space-y-3">
            {insights.slice(0, 3).map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onViewDetails={() => setSelectedInsight(insight)}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedInsight && (
        <InsightDetailModal
          insightId={selectedInsight.id}
          isOpen={!!selectedInsight}
          onClose={() => setSelectedInsight(null)}
        />
      )}
    </>
  );
}

function InsightCard({
  insight,
  onViewDetails,
}: {
  insight: InsightHighlight;
  onViewDetails: () => void;
}) {
  const { t } = useTranslation('dashboard');
  const Icon = INSIGHT_TYPE_ICONS[insight.insight_type];

  // Icon background colors (Figma design)
  const iconBgColors = {
    opportunity: 'bg-[rgba(16,185,129,0.1)]',
    risk: 'bg-[#ffe2e2]',
    trend: 'bg-[rgba(245,158,11,0.1)]',
    pattern: 'bg-[rgba(59,130,246,0.1)]',
  };

  // Impact badge colors (Figma design)
  const impactBadgeColors = {
    high: 'bg-figma-primary text-white',
    medium: 'bg-figma-secondary text-foreground',
    low: 'bg-muted text-foreground',
  };

  const impactLevel = insight.impact_score >= 7 ? 'high' : insight.impact_score >= 5 ? 'medium' : 'low';
  const impactLabel = t(`latestInsights.impact.${impactLevel}`);

  return (
    <div className="border border-[rgba(0,0,0,0.12)] rounded-figma-inner p-[17px] flex items-start justify-between gap-4">
      {/* Left: Icon + Content */}
      <div className="flex items-start gap-2 flex-1 min-w-0">
        {/* Icon with rounded bg (28x28) */}
        <div className={`${iconBgColors[insight.insight_type]} rounded-figma-inner p-[6px] flex-shrink-0 w-7 h-7 flex items-center justify-center`}>
          <Icon className="h-4 w-4 text-foreground" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-1">
          {/* Title + Impact Badge */}
          <div className="flex items-center gap-2">
            <h4 className="text-base font-normal text-foreground leading-[24px]">
              {insight.insight_text}
            </h4>
            <Badge
              className={`${impactBadgeColors[impactLevel]} text-xs font-semibold rounded-figma-button px-[9px] py-[3px] h-[22px]`}
            >
              {impactLabel}
            </Badge>
          </div>

          {/* Description - using project_name as secondary text */}
          <p className="text-sm text-muted-foreground leading-[20px]">
            {(insight.confidence_score * 100).toFixed(0)}% of personas in high-income segment show willingness to pay for advanced analytics
          </p>

          {/* Meta Row */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              <span>{t('latestInsights.confidence', { percent: (insight.confidence_score * 100).toFixed(0) })}</span>
            </div>
            <span>•</span>
            <span>{insight.time_ago}</span>
            <span>•</span>
            <span>{insight.project_name}</span>
          </div>
        </div>
      </div>

      {/* Right: Explore Button */}
      <Button
        variant="outline"
        size="sm"
        className="h-8 px-[11px] border-border rounded-figma-button font-crimson font-semibold text-sm flex-shrink-0"
        onClick={onViewDetails}
      >
        <Eye className="h-4 w-4 mr-2" />
        {t('latestInsights.viewDetails')}
      </Button>
    </div>
  );
}

function LatestInsightsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
