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
} from 'lucide-react';
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
import type { QuickAction } from '@/types/dashboard';

interface SightDashboardProps {
  onNavigate?: (view: string) => void;
}

export function SightDashboard({ onNavigate }: SightDashboardProps) {
  const { data: actions, isLoading: actionsLoading } = useQuickActions(4);
  const navigateTo = useDashboardNavigation(onNavigate);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1920px] w-full mx-auto p-4 md:p-6">
      {/* Dashboard Header */}
      <PageHeader
        title="Panel główny"
        subtitle="Przegląd Twoich projektów i działań badawczych"
      />

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

  return (
    <Card className={`border-l-4 ${priorityColors[action.priority]}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          {getIcon(action.icon)}
          <CardTitle className="text-base">{action.title}</CardTitle>
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

function QuickActionsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {[...Array(3)].map((_, i) => (
        <Skeleton key={i} className="h-48" />
      ))}
    </div>
  );
}
