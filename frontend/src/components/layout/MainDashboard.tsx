/**
 * Main Dashboard - Production Dashboard with KPIs
 *
 * Phase 2 Complete - All sections:
 * - Active Projects Section
 * - Research Activity Charts (Weekly Completion + Insight Analytics)
 * - Latest Insights Section (with Detail Modal)
 * - Health & Blockers Section
 * - Usage & Budget Section
 * - Notifications Section
 */

import { Separator } from '@/components/ui/separator';
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
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MessageSquarePlus, Sparkles } from 'lucide-react';

interface MainDashboardProps {
  onNavigate?: (view: string) => void;
}

export function MainDashboard({ onNavigate }: MainDashboardProps) {
  const navigateTo = useDashboardNavigation(onNavigate);
  const { t } = useTranslation('dashboard');

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1920px] w-full mx-auto p-4 md:p-6">
      {/* Dashboard Header */}
      <PageHeader
        title={t('header.title')}
        subtitle={t('header.subtitle')}
      />

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
        <h2 className="text-xl font-semibold">{t('notifications.title')}</h2>
        <NotificationsSection />
      </div>
      </div>
    </div>
  );
}

