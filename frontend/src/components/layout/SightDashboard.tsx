/**
 * Sight Dashboard - Production Dashboard with KPIs and Next Best Actions
 *
 * MVP includes:
 * - Overview Section (4 main metrics + 4 extensions)
 * - Quick Actions Section (Next Best Action)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  AlertTriangle,
  Users,
  MessageSquare,
  Lightbulb,
  TrendingUp,
  ArrowUp,
  ArrowDown,
  Minus,
  HelpCircle,
} from 'lucide-react';
import { useDashboardOverview } from '@/hooks/dashboard/useDashboardOverview';
import { useQuickActions } from '@/hooks/dashboard/useQuickActions';
import { useExecuteAction } from '@/hooks/dashboard/useExecuteAction';
import { ActiveProjectsSection } from '@/components/dashboard/ActiveProjectsSection';
import type { MetricCard as MetricCardType, QuickAction } from '@/types/dashboard';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface SightDashboardProps {
  onNavigate?: (view: string) => void;
}

export function SightDashboard({ onNavigate }: SightDashboardProps) {
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useDashboardOverview();
  const { data: actions, isLoading: actionsLoading } = useQuickActions(4);

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Track your research progress, insights, and next actions
        </p>
      </div>

      {/* Overview Section */}
      <div className="space-y-6 mb-8">
        <h2 className="text-xl font-semibold">Overview</h2>

        {overviewLoading ? (
          <OverviewSkeleton />
        ) : overviewError ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Failed to load dashboard overview. Please try again.
            </AlertDescription>
          </Alert>
        ) : overview ? (
          <>
            {/* 4 Main Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <MetricCard metric={overview.active_research} />
              <MetricCard metric={overview.pending_actions} />
              <MetricCard metric={overview.insights_ready} />
              <MetricCard metric={overview.this_week_activity} />
            </div>

            {/* 4 Extensions */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <MetricCard metric={overview.time_to_insight} />
              <MetricCard metric={overview.insight_adoption_rate} />
              <MetricCard metric={overview.persona_coverage} />
              <MetricCard metric={overview.blockers_count} />
            </div>
          </>
        ) : null}
      </div>

      {/* Quick Actions Section */}
      <div className="space-y-6 mb-8">
        <h2 className="text-xl font-semibold">Quick Actions</h2>

        {actionsLoading ? (
          <QuickActionsSkeleton />
        ) : actions && actions.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {actions.map((action) => (
              <ActionCard key={action.action_id} action={action} onNavigate={onNavigate} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No pending actions. Great job! 🎉
            </CardContent>
          </Card>
        )}
      </div>

      {/* Active Projects Section */}
      <ActiveProjectsSection />
    </div>
  );
}

// ========== COMPONENTS ==========

function MetricCard({ metric }: { metric: MetricCardType }) {
  const TrendIcon =
    metric.trend?.direction === 'up'
      ? ArrowUp
      : metric.trend?.direction === 'down'
      ? ArrowDown
      : Minus;

  const trendColor =
    metric.trend?.direction === 'up'
      ? 'text-green-600'
      : metric.trend?.direction === 'down'
      ? 'text-red-600'
      : 'text-gray-400';

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{metric.label}</p>
            <p className="text-2xl font-bold">{metric.value}</p>
          </div>
          {metric.tooltip && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <HelpCircle className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-sm">{metric.tooltip}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        {metric.trend && (
          <div className={`mt-2 flex items-center text-sm ${trendColor}`}>
            <TrendIcon className="mr-1 h-4 w-4" />
            <span>{Math.abs(metric.trend.change_percent).toFixed(1)}%</span>
            <span className="ml-1 text-muted-foreground">vs last week</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ActionCard({ action, onNavigate }: { action: QuickAction; onNavigate?: (view: string) => void }) {
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

  const handleExecute = () => {
    executeAction.mutate(action.action_id);
  };

  const getIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      AlertTriangle,
      Users,
      MessageSquare,
      Lightbulb,
      TrendingUp,
    };
    const Icon = icons[iconName] || AlertTriangle;
    return <Icon className="h-5 w-5" />;
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
            {action.priority}
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
          {executeAction.isPending ? 'Executing...' : action.cta_label}
        </Button>
      </CardContent>
    </Card>
  );
}

// ========== SKELETONS ==========

function OverviewSkeleton() {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    </>
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
