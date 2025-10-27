/**
 * Insight Analytics Charts - Bar chart (top concepts) + Pie chart (sentiment distribution)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#6b7280',
  mixed: '#f59e0b',
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
            <CardTitle>Top Concepts</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>Failed to load concept data</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>Failed to load sentiment data</AlertDescription>
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

  // Transform sentiment data for pie chart
  const sentimentData = hasSentimentData
    ? Object.entries(data.sentiment_distribution).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        originalName: name as keyof typeof SENTIMENT_COLORS,
      }))
    : [];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Top Concepts Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Top Concepts</CardTitle>
        </CardHeader>
        <CardContent>
          {hasTopConcepts ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.top_concepts.slice(0, 10)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis
                  dataKey="concept"
                  type="category"
                  width={100}
                  tick={{ fontSize: 11 }}
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
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px]">
              <p className="text-center text-muted-foreground">
                No concept data available yet
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sentiment Distribution Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Sentiment Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {hasSentimentData ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={SENTIMENT_COLORS[entry.originalName]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px' }}
                  iconType="circle"
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px]">
              <p className="text-center text-muted-foreground">
                No sentiment data available yet
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
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
