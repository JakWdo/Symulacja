/**
 * Insight Types Chart - Pie chart showing insight distribution (Figma Node 62:849 left)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { useInsightAnalytics } from '@/hooks/dashboard/useInsightAnalytics';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const INSIGHT_TYPE_COLORS = {
  opportunity: '#28a745', // green
  risk: '#dc3545',        // red
  trend: '#f29f05',       // yellow/orange
  pattern: '#3b82f6',     // blue
};

const INSIGHT_TYPE_LABELS = {
  opportunity: 'Szanse',
  risk: 'Ryzyka',
  trend: 'Trendy',
  pattern: 'Wzorce',
};

export function InsightTypesChart() {
  const { data, isLoading, error } = useInsightAnalytics();

  if (isLoading) {
    return <InsightTypesChartSkeleton />;
  }

  if (error) {
    return (
      <Card className="border-border rounded-figma-card">
        <CardHeader className="px-6 pt-6 pb-4">
          <CardTitle className="text-base font-normal text-foreground leading-[16px]">
            Typy spostrzeżeń
          </CardTitle>
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Nie udało się załadować danych o typach spostrzeżeń</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.insight_types) {
    return null;
  }

  const hasInsightTypesData = Object.values(data.insight_types).some((val) => val > 0);

  // Transform insight types data for pie chart
  const chartData = hasInsightTypesData
    ? Object.entries(data.insight_types).map(([key, value]) => ({
        name: INSIGHT_TYPE_LABELS[key as keyof typeof INSIGHT_TYPE_LABELS] || key,
        value,
        color: INSIGHT_TYPE_COLORS[key as keyof typeof INSIGHT_TYPE_COLORS] || '#6b7280',
      }))
    : [];

  // Calculate total for percentages
  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  // Custom legend renderer (Figma design: colored squares + label + percentage)
  const renderLegend = (props: any) => {
    const { payload } = props;
    return (
      <div className="flex flex-col gap-2 mt-4">
        {payload.map((entry: any, index: number) => {
          const percentage = total > 0 ? ((entry.payload.value / total) * 100).toFixed(0) : '0';
          return (
            <div key={`legend-${index}`} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-[4px]"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm font-normal text-foreground">{entry.value}</span>
              </div>
              <span className="text-sm text-muted-foreground">{percentage}%</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <Card className="border-border rounded-figma-card h-[486px]">
      <CardHeader className="px-6 pt-6 pb-4">
        <CardTitle className="text-base font-normal text-foreground leading-[16px]">
          Typy spostrzeżeń
        </CardTitle>
        <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
          Rozkład według kategorii
        </p>
      </CardHeader>
      <CardContent className="px-6 pb-6">
        {hasInsightTypesData ? (
          <>
            {/* Pie Chart */}
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <ResponsiveContainer width="100%" height={76}>
              <PieChart>
                <Pie data={chartData} dataKey="value">
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Legend content={renderLegend} />
              </PieChart>
            </ResponsiveContainer>
          </>
        ) : (
          <div className="flex items-center justify-center h-[316px]">
            <p className="text-center text-muted-foreground">
              Brak jeszcze danych o typach spostrzeżeń
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function InsightTypesChartSkeleton() {
  return (
    <Card className="border-border rounded-figma-card h-[486px]">
      <CardHeader className="px-6 pt-6 pb-4">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-6 w-48 mt-1.5" />
      </CardHeader>
      <CardContent className="px-6 pb-6">
        <Skeleton className="h-[316px] w-full rounded-figma-inner" />
      </CardContent>
    </Card>
  );
}
