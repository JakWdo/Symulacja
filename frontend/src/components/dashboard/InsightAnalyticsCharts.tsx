/**
 * Insight Analytics Charts - Bar chart (top concepts) + Pie chart (sentiment distribution)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useInsightAnalytics } from '@/hooks/dashboard/useInsightAnalytics';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

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
