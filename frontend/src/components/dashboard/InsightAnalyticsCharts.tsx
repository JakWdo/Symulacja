/**
 * Insight Analytics Charts - Bar chart (top concepts) + Pie chart (sentiment distribution)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useInsightAnalytics } from '@/hooks/dashboard/useInsightAnalytics';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const SENTIMENT_COLORS = {
  positive: '#28a745',
  negative: '#dc3545',
  neutral: '#6b7280',
  mixed: '#f59e0b',
};

const INSIGHT_TYPE_COLORS = {
  opportunity: '#28a745', // Figma green
  risk: '#dc3545', // Figma red
  trend: '#f59e0b', // Figma yellow/amber
  pattern: '#3b82f6', // blue
};

export function InsightAnalyticsCharts() {
  const { t } = useTranslation('dashboard');
  const { data, isLoading, error } = useInsightAnalytics();

  if (isLoading) {
    return <InsightAnalyticsSkeleton />;
  }

  if (error) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('insightAnalytics.topConcepts.title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{t('insightAnalytics.topConcepts.error')}</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t('insightAnalytics.sentiment.title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{t('insightAnalytics.sentiment.error')}</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const hasTopConcepts = data.top_concepts && data.top_concepts.length > 0;
  const hasSentimentData =
    data.sentiment_distribution &&
    Object.values(data.sentiment_distribution).some((val) => val > 0);

  const hasInsightTypesData =
    data.insight_types &&
    Object.values(data.insight_types).some((val) => val > 0);

  // Transform sentiment data for pie chart
  const sentimentData = hasSentimentData
    ? Object.entries(data.sentiment_distribution).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        originalName: name as keyof typeof SENTIMENT_COLORS,
      }))
    : [];

  // Transform insight types data for pie chart
  const insightTypesData = hasInsightTypesData
    ? Object.entries(data.insight_types).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        originalName: name as keyof typeof INSIGHT_TYPE_COLORS,
      }))
    : [];

  return (
    <Card className="border-border rounded-figma-card">
      <CardHeader className="px-6 pt-6 pb-4">
        <CardTitle className="text-base font-normal text-foreground leading-[16px]">
          {t('insightAnalytics.topConcepts.title')}
        </CardTitle>
        <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
          {t('insightAnalytics.topConcepts.subtitle')}
        </p>
      </CardHeader>
      <CardContent className="px-6 pb-6">
        {hasTopConcepts ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.top_concepts.slice(0, 5)} layout="vertical">
              <XAxis
                type="number"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                dataKey="concept"
                type="category"
                width={150}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="count" fill="#F27405" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[280px]">
            <p className="text-center text-muted-foreground">
              {t('insightAnalytics.topConcepts.noData')}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function InsightAnalyticsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    </div>
  );
}
