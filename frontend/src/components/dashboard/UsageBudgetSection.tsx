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
  const { data, isLoading, error } = useUsageBudget();
  const { data: breakdown, isLoading: isLoadingBreakdown } = useUsageBreakdown();

  if (isLoading) {
    return <UsageBudgetSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Zużycie i budżet</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Nie udało się załadować danych o zużyciu</AlertDescription>
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
    <Card className="border-border rounded-[12px]">
      <CardHeader>
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-foreground" />
          <CardTitle className="text-base font-normal text-foreground">Zużycie i budżet</CardTitle>
        </div>
        <p className="text-base text-muted-foreground">Monitorowanie zużycia tokenów i kosztów</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Bieżące zużycie</span>
            <span className="text-base font-normal text-foreground">
              ${data.total_cost.toFixed(2)} / ${data.budget_limit?.toFixed(2) || '100.00'}
            </span>
          </div>
          <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(budgetPercentage, 100)}%`,
                backgroundColor: getProgressColor(),
              }}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {(data.total_tokens / 1_000_000).toFixed(1)}M tokenów zużytych
          </p>
        </div>

        {/* Separator */}
        <div className="h-px bg-border" />

        {/* Forecast + Alert Threshold */}
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Prognoza (koniec miesiąca)</p>
            <p className="text-lg font-semibold text-foreground">
              ${data.forecast_month_end.toFixed(2)}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Próg alertu</p>
            <div className="flex items-center gap-2">
              <p className="text-lg font-semibold text-foreground">
                {(warning * 100).toFixed(0)}% / {(critical * 100).toFixed(0)}%
              </p>
              <span className="text-xs text-muted-foreground">(ostrzeż. / kryt.)</span>
            </div>
          </div>
        </div>

        {/* Budget Alert */}
        {hasAlerts && (
          <div className="border border-border rounded-[8px] p-[17px]">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-4 w-4 text-foreground mt-0.5" />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-foreground tracking-tight">
                  Alert budżetowy
                </p>
                <p className="text-sm text-muted-foreground">
                  {data.alerts[0]?.message || 'Zużycie na poziomie 93% - rozważ optymalizację'}
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
              <p className="text-sm font-semibold text-foreground">Zużycie według typu operacji</p>

              {/* Persona Generation */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Generowanie person</span>
                  <span className="text-xs text-foreground">
                    {breakdown.persona_generation.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-figma-primary transition-all duration-300"
                    style={{ width: `${breakdown.persona_generation.percentage}%` }}
                  />
                </div>
              </div>

              {/* Focus Group */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Grupy fokusowe</span>
                  <span className="text-xs text-foreground">
                    {breakdown.focus_group.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-figma-primary transition-all duration-300"
                    style={{ width: `${breakdown.focus_group.percentage}%` }}
                  />
                </div>
              </div>

              {/* RAG Query */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">RAG i analiza</span>
                  <span className="text-xs text-foreground">
                    {breakdown.rag_query.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-figma-primary transition-all duration-300"
                    style={{ width: `${breakdown.rag_query.percentage}%` }}
                  />
                </div>
              </div>

              {/* Other */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Inne operacje</span>
                  <span className="text-xs text-foreground">
                    {breakdown.other.percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-figma-primary transition-all duration-300"
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
