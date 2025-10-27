/**
 * Weekly Completion Chart - Line chart showing research activity over time
 *
 * Shows 3 metrics:
 * - Personas generated
 * - Focus groups completed
 * - Insights extracted
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { useWeeklyCompletion } from '@/hooks/dashboard/useWeeklyCompletion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface WeeklyCompletionChartProps {
  weeks?: number;
}

export function WeeklyCompletionChart({ weeks = 8 }: WeeklyCompletionChartProps) {
  const { data, isLoading, error } = useWeeklyCompletion(weeks);

  if (isLoading) {
    return <WeeklyCompletionSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Weekly Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Failed to load weekly activity data</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.weeks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Weekly Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-8">
            No activity data available yet
          </p>
        </CardContent>
      </Card>
    );
  }

  // Transform data for recharts
  const chartData = data.weeks.map((week, index) => ({
    week,
    personas: data.personas[index],
    focusGroups: data.focus_groups[index],
    insights: data.insights[index],
  }));

  // Calculate totals
  const totalPersonas = data.personas.reduce((sum, val) => sum + val, 0);
  const totalFocusGroups = data.focus_groups.reduce((sum, val) => sum + val, 0);
  const totalInsights = data.insights.reduce((sum, val) => sum + val, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Activity</CardTitle>
        <div className="flex gap-6 mt-2 text-sm text-muted-foreground">
          <span>
            <span className="font-medium text-blue-600">{totalPersonas}</span> personas
          </span>
          <span>
            <span className="font-medium text-green-600">{totalFocusGroups}</span> focus groups
          </span>
          <span>
            <span className="font-medium text-purple-600">{totalInsights}</span> insights
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="week"
              className="text-xs"
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              className="text-xs"
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
            <Legend
              wrapperStyle={{ fontSize: '12px' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey="personas"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
              name="Personas"
            />
            <Line
              type="monotone"
              dataKey="focusGroups"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: '#10b981', r: 4 }}
              activeDot={{ r: 6 }}
              name="Focus Groups"
            />
            <Line
              type="monotone"
              dataKey="insights"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={{ fill: '#8b5cf6', r: 4 }}
              activeDot={{ r: 6 }}
              name="Insights"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function WeeklyCompletionSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64 mt-2" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-[300px] w-full" />
      </CardContent>
    </Card>
  );
}
