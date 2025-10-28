/**
 * Sight Dashboard - Production Dashboard with KPIs and Next Best Actions
 *
 * Phase 2 Complete - All sections:
 * - Overview Section (4 main metrics + 4 extensions)
 * - Quick Actions Section (Next Best Action)
 * - Active Projects Section
 * - Research Activity Charts (Weekly Completion + Insight Analytics)
 * - Latest Insights Section (with Detail Modal)
 * - Health & Blockers Section
 * - Usage & Budget Section
 * - Notifications Section
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  AlertTriangle,
  Users,
  MessageSquare,
  Lightbulb,
  TrendingUp,
  Rocket,
  PlayCircle,
  Plus,
  ArrowUp,
  ArrowDown,
  Minus,
  HelpCircle,
  Clock,
  Target,
  AlertCircle,
} from 'lucide-react';
import { useDashboardOverview } from '@/hooks/dashboard/useDashboardOverview';
import { useQuickActions } from '@/hooks/dashboard/useQuickActions';
import { useExecuteAction } from '@/hooks/dashboard/useExecuteAction';
import { PageHeader } from '@/components/layout/PageHeader';
import { ActiveProjectsSection } from '@/components/dashboard/ActiveProjectsSection';
import { WeeklyCompletionChart } from '@/components/dashboard/WeeklyCompletionChart';
import { InsightAnalyticsCharts } from '@/components/dashboard/InsightAnalyticsCharts';
import { InsightTypesChart } from '@/components/dashboard/InsightTypesChart';
import { LatestInsightsSection } from '@/components/dashboard/LatestInsightsSection';
import { HealthBlockersSection } from '@/components/dashboard/HealthBlockersSection';
import { UsageBudgetSection } from '@/components/dashboard/UsageBudgetSection';
import { NotificationsSection } from '@/components/dashboard/NotificationsSection';
import { useDashboardNavigation } from '@/hooks/dashboard/useDashboardNavigation';
import type { MetricCard as MetricCardType, QuickAction } from '@/types/dashboard';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface SightDashboardProps {
  onNavigate?: (view: string) => void;
}

export function SightDashboard({ onNavigate }: SightDashboardProps) {
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useDashboardOverview();
  const { data: actions, isLoading: actionsLoading } = useQuickActions(4);
  const navigateTo = useDashboardNavigation(onNavigate);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1920px] w-full mx-auto p-4 md:p-6">
      {/* Dashboard Header */}
      <PageHeader
        title="Panel główny"
        subtitle="Śledź spostrzeżenia, akcje i postęp badań w czasie rzeczywistym"
      />

      {/* Overview Section - 4 KPI Cards (Figma Design) */}
      <div className="space-y-6 mb-8">
        {overviewLoading ? (
          <OverviewSkeleton />
        ) : overviewError ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Nie udało się załadować przeglądu. Spróbuj ponownie.
            </AlertDescription>
          </Alert>
        ) : overview ? (
          <>
            {/* 4 KPI Cards (Figma Design Node 62:152) */}
            <div className="grid gap-4 grid-cols-4">
              {/* Time-to-Insight */}
              <MetricCard
                metric={overview.time_to_insight}
                icon={Clock}
              />
              {/* Insight Adoption */}
              <MetricCard
                metric={overview.insight_adoption_rate}
                icon={Target}
              />
              {/* Persona Coverage */}
              <MetricCard
                metric={overview.persona_coverage}
                icon={Users}
              />
              {/* Active Blockers */}
              <MetricCard
                metric={overview.blockers_count}
                icon={AlertCircle}
              />
            </div>
          </>
        ) : null}
      </div>

      {/* Quick Actions Section */}
      <div className="space-y-6 mb-8">
        <h2 className="text-xl font-semibold">Szybkie akcje</h2>

        {actionsLoading ? (
          <QuickActionsSkeleton />
        ) : actions && actions.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {actions.map((action) => (
              <ActionCard
                key={action.action_id}
                action={action}
                onNavigate={navigateTo}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Brak oczekujących akcji. Świetna robota! 🎉
            </CardContent>
          </Card>
        )}
      </div>

      {/* Active Projects Section */}
      <div className="mb-8">
        <ActiveProjectsSection onNavigate={navigateTo} />
      </div>

      <Separator className="my-8" />

      {/* Row: Weekly Activity Trend + Top Insight Concepts (Figma Design) */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="col-span-2">
          <WeeklyCompletionChart weeks={8} />
        </div>
        <div className="col-span-1">
          <InsightAnalyticsCharts />
        </div>
      </div>

      <Separator className="my-8" />

      {/* Row: Insight Types Pie + Latest Insights (Figma Design) */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="col-span-1">
          <InsightTypesChart />
        </div>
        <div className="col-span-2">
          <LatestInsightsSection />
        </div>
      </div>

      <Separator className="my-8" />

      {/* Row: Health & Blockers + Usage & Budget (Figma Design) */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="col-span-2">
          <HealthBlockersSection onFixBlocker={navigateTo} />
        </div>
        <div className="col-span-1">
          <UsageBudgetSection />
        </div>
      </div>

      <Separator className="my-8" />

      {/* Notifications Section */}
      <div className="space-y-6 mb-8">
        <h2 className="text-xl font-semibold">Powiadomienia</h2>
        <NotificationsSection />
      </div>
      </div>
    </div>
  );
}

// ========== COMPONENTS ==========

function MetricCard({ metric, icon: Icon }: { metric: MetricCardType; icon?: React.ComponentType<{ className?: string }> }) {
  const TrendIcon =
    metric.trend?.direction === 'up'
      ? ArrowUp
      : metric.trend?.direction === 'down'
      ? ArrowDown
      : Minus;

  const trendColor =
    metric.trend?.direction === 'up'
      ? 'text-figma-green'
      : metric.trend?.direction === 'down'
      ? 'text-figma-red'
      : 'text-gray-400';

  // Dynamic trend text based on metric type
  const getTrendText = () => {
    if (!metric.trend) return '';
    const isTimeMetric = metric.label.toLowerCase().includes('czas');
    const direction = metric.trend.direction;

    if (isTimeMetric) {
      return direction === 'up' ? 'szybciej' : direction === 'down' ? 'wolniej' : '';
    } else {
      return direction === 'up' ? 'wyższy' : direction === 'down' ? 'niższy' : '';
    }
  };

  return (
    <Card className="border-border rounded-figma-card">
      <CardHeader className="pb-6 px-6 pt-6 flex flex-row items-start justify-between">
        <div className="flex-1">
          <CardTitle className="text-sm font-normal text-figma-muted dark:text-muted-foreground leading-[20px]">
            {metric.label}
          </CardTitle>
        </div>
        {Icon && (
          <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        )}
      </CardHeader>
      <CardContent className="px-6 pb-6 pt-0">
        <div className="space-y-2">
          <p className="text-2xl font-normal leading-[32px] text-foreground">{metric.value}</p>
          {metric.trend && (
            <div className={`flex items-center text-xs ${trendColor}`}>
              <TrendIcon className="mr-1 h-3 w-3" />
              <span>{Math.abs(metric.trend.change_percent).toFixed(1)}%</span>
              {getTrendText() && <span className="ml-1">{getTrendText()}</span>}
              {metric.p90 && (
                <span className="ml-1 text-muted-foreground">(P90: {metric.p90})</span>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ActionCard({
  action,
  onNavigate,
}: {
  action: QuickAction;
  onNavigate?: (url: string) => void | Promise<void>;
}) {
  const executeAction = useExecuteAction();

  const priorityColors = {
    high: 'border-red-500 bg-red-50 dark:bg-red-950',
    medium: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
    low: 'border-blue-500 bg-blue-50 dark:bg-blue-950',
  };

  const priorityBadgeColors = {
    high: 'bg-red-500 text-white',
    medium: 'bg-yellow-500 text-white',
    low: 'bg-blue-500 text-white',
  };

  const handleExecute = async () => {
    try {
      const result = await executeAction.mutateAsync(action.action_id);
      if (result?.status === 'redirect' && result.redirect_url) {
        await onNavigate?.(result.redirect_url);
      } else if (result?.status === 'success' && action.cta_url) {
        await onNavigate?.(action.cta_url);
      }
    } catch (error) {
      console.error('Failed to execute dashboard action', error);
    }
  };

  const getIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      AlertTriangle,
      Users,
      MessageSquare,
      Lightbulb,
      TrendingUp,
      Rocket,
      PlayCircle,
      Plus,
    };
    const Icon = icons[iconName] || AlertTriangle;
    return <Icon className="h-5 w-5" />;
  };

  const priorityLabels = {
    high: 'Wysoki',
    medium: 'Średni',
    low: 'Niski',
  };

  return (
    <Card className={`border-l-4 ${priorityColors[action.priority]}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {getIcon(action.icon)}
            <CardTitle className="text-base">{action.title}</CardTitle>
          </div>
          <Badge className={priorityBadgeColors[action.priority]} variant="secondary">
            {priorityLabels[action.priority]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">{action.description}</p>
        <Button
          onClick={handleExecute}
          disabled={executeAction.isPending}
          className="w-full"
        >
          {executeAction.isPending ? 'Wykonywanie...' : action.cta_label}
        </Button>
      </CardContent>
    </Card>
  );
}

// ========== SKELETONS ==========

function OverviewSkeleton() {
  return (
    <div className="grid gap-4 grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <Skeleton key={i} className="h-[170px] rounded-figma-card" />
      ))}
    </div>
  );
}

function QuickActionsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {[...Array(3)].map((_, i) => (
        <Skeleton key={i} className="h-48" />
      ))}
    </div>
  );
}
