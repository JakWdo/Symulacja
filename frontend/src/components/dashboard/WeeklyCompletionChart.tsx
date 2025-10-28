/**
 * Weekly Completion Chart - Line chart showing research activity over time
 *
 * Shows 4 metrics (Figma design):
 * - Personas generated
 * - Focus groups completed
 * - Surveys completed
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
          <CardTitle>Aktywność tygodniowa</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Nie udało się załadować danych o aktywności tygodniowej</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.weeks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Aktywność tygodniowa</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-8">
            Brak jeszcze danych o aktywności
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
    surveys: data.surveys[index],
    insights: data.insights[index],
  }));

  // Calculate totals
  const totalPersonas = data.personas.reduce((sum, val) => sum + val, 0);
  const totalFocusGroups = data.focus_groups.reduce((sum, val) => sum + val, 0);
  const totalSurveys = data.surveys.reduce((sum, val) => sum + val, 0);
  const totalInsights = data.insights.reduce((sum, val) => sum + val, 0);

  return (
    <Card className="border-border rounded-figma-card">
      <CardHeader className="px-6 pt-6 pb-4">
        <CardTitle className="text-base font-normal text-foreground leading-[16px]">
          Trend aktywności tygodniowej
        </CardTitle>
        <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
          Generowanie person, grup fokusowych i spostrzeżeń
        </p>
      </CardHeader>
      <CardContent className="px-6 pb-6">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
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
              wrapperStyle={{ fontSize: '16px', paddingTop: '16px' }}
              iconType="line"
              align="center"
              verticalAlign="bottom"
            />
            <Line
              type="monotone"
              dataKey="personas"
              stroke="#F27405"
              strokeWidth={2}
              dot={{ fill: '#F27405', r: 4 }}
              activeDot={{ r: 6 }}
              name="Persony"
            />
            <Line
              type="monotone"
              dataKey="focusGroups"
              stroke="#F29F05"
              strokeWidth={2}
              dot={{ fill: '#F29F05', r: 4 }}
              activeDot={{ r: 6 }}
              name="Grupy fokusowe"
            />
            <Line
              type="monotone"
              dataKey="insights"
              stroke="#28a745"
              strokeWidth={2}
              dot={{ fill: '#28a745', r: 4 }}
              activeDot={{ r: 6 }}
              name="Spostrzeżenia"
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
