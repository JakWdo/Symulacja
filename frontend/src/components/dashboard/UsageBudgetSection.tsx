/**
 * Usage & Budget Section - Token usage, costs, 30-day history, and budget alerts
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  DollarSign,
  Zap,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useUsageBudget } from '@/hooks/dashboard/useUsageBudget';
import { useUsageBreakdown } from '@/hooks/dashboard/useUsageBreakdown';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export function UsageBudgetSection() {
  const { t } = useTranslation('dashboard');
  const { data, isLoading, error } = useUsageBudget();
  const { data: breakdown, isLoading: isLoadingBreakdown } = useUsageBreakdown();

  if (isLoading) {
    return <UsageBudgetSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('usage.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{t('errors.loadUsage')}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const budgetPercentage = data.budget_limit
    ? (data.total_cost / data.budget_limit) * 100
    : 0;
  const forecastPercentage = data.budget_limit
    ? (data.forecast_month_end / data.budget_limit) * 100
    : 0;

  const hasAlerts = data.alerts.length > 0;

  // Get thresholds from user settings (defaults to 80/90)
  const warning = data.alert_thresholds?.warning || 0.8;
  const critical = data.alert_thresholds?.critical || 0.9;
  const percentage = budgetPercentage / 100; // 0-1

  // Figma design colors: green → yellow → orange → red
  const getProgressColor = () => {
    if (percentage >= critical) return '#dc3545'; // red (critical)
    if (percentage >= warning) return '#f27405';  // orange (warning)
    if (percentage >= 0.5) return '#ffc107';      // yellow (moderate)
    return '#00c950';                              // green (on track)
  };

  // Transform history for chart (last 7 days for better visibility)
  const chartData = data.history.slice(-7).map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    cost: item.total_cost,
    tokens: item.total_tokens,
  }));

  return (
    <Card className="border-border rounded-figma-card">
      <CardHeader className="px-6 pt-6 pb-4">
        <div className="flex items-center gap-2 mb-1.5">
          <DollarSign className="h-5 w-5 text-foreground" />
          <CardTitle className="text-base font-normal text-foreground leading-[16px]">
            {t('usage.title')}
          </CardTitle>
        </div>
        <p className="text-base text-muted-foreground leading-[24px]">
          {t('usage.subtitle')}
        </p>
      </CardHeader>
      <CardContent className="px-6 pb-6 space-y-4">
        {/* Current Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{t('usage.currentUsage')}</span>
            <span className="text-base font-normal text-foreground">
              ${data.total_cost.toFixed(2)} / ${data.budget_limit?.toFixed(2) || '100.00'}
            </span>
          </div>
          <div className="w-full h-2 bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(budgetPercentage, 100)}%`,
                backgroundColor: getProgressColor(),
              }}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {t('usage.tokensUsed', { count: Number((data.total_tokens / 1_000_000).toFixed(1)) })}
          </p>
        </div>

        {/* Separator */}
        <div className="h-px bg-border" />

        {/* Forecast + Alert Threshold (Figma Design) */}
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{t('usage.forecast')}</p>
            <p className="text-lg font-semibold text-foreground">
              ${data.forecast_month_end.toFixed(2)}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{t('usage.alertThreshold')}</p>
            <p className="text-lg font-semibold text-foreground">
              {(critical * 100).toFixed(0)}%
            </p>
          </div>
        </div>

        {/* Budget Alert (Figma Design) */}
        {hasAlerts && (
          <div className="border border-border rounded-figma-inner p-[17px]">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-4 w-4 text-foreground mt-0.5" />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-foreground tracking-tight">
                  {t('usage.budgetAlert')}
                </p>
                <p className="text-sm text-muted-foreground">
                  {data.alerts[0]?.message || t('usage.budgetAlertMessage')}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Usage Breakdown - 4 Progress Bars (Figma Design) */}
        {!isLoadingBreakdown && breakdown && (
          <>
            <div className="h-px bg-border" />
            <div className="space-y-3">
              <p className="text-sm font-semibold text-foreground">{t('usage.breakdown.title')}</p>

              {/* Persona Generation */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{t('usage.breakdown.personaGeneration')}</span>
                  <span className="text-xs text-foreground">
                    {breakdown.persona_generation.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand transition-all duration-300"
                    style={{ width: `${breakdown.persona_generation.percentage}%` }}
                  />
                </div>
              </div>

              {/* Focus Group */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{t('usage.breakdown.focusGroups')}</span>
                  <span className="text-xs text-foreground">
                    {breakdown.focus_group.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand transition-all duration-300"
                    style={{ width: `${breakdown.focus_group.percentage}%` }}
                  />
                </div>
              </div>

              {/* RAG Query */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{t('usage.breakdown.ragAnalysis')}</span>
                  <span className="text-xs text-foreground">
                    {breakdown.rag_query.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand transition-all duration-300"
                    style={{ width: `${breakdown.rag_query.percentage}%` }}
                  />
                </div>
              </div>

              {/* Other */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{t('usage.breakdown.other')}</span>
                  <span className="text-xs text-foreground">
                    {breakdown.other.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand transition-all duration-300"
                    style={{ width: `${breakdown.other.percentage}%` }}
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function UsageBudgetSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    </div>
  );
}
