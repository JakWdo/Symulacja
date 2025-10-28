/**
 * Insight Analytics Charts - Bar chart (top concepts) + Pie chart (sentiment distribution)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle } from 'lucide-react';
import { useInsightAnalytics } from '@/hooks/dashboard/useInsightAnalytics';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
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
  const { data, isLoading, error } = useInsightAnalytics();

  if (isLoading) {
    return <InsightAnalyticsSkeleton />;
  }

  if (error) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Najczęstsze koncepcje</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>Nie udało się załadować danych o koncepcjach</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Rozkład sentymentu</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>Nie udało się załadować danych o sentymencie</AlertDescription>
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
    <Card className="border-border rounded-[12px]">
      <CardHeader>
        <CardTitle className="text-base font-normal text-foreground">Najczęstsze koncepcje w spostrzeżeniach</CardTitle>
        <p className="text-base text-muted-foreground">Najczęściej omawiane tematy</p>
      </CardHeader>
      <CardContent>
        {hasTopConcepts ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.top_concepts.slice(0, 5)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-border" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis
                dataKey="concept"
                type="category"
                width={120}
                tick={{ fontSize: 12 }}
                tickLine={false}
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
              Brak jeszcze danych o koncepcjach
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
