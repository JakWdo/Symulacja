/**
 * Usage & Budget Section - Token usage, costs, 30-day history, and budget alerts
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  DollarSign,
  Zap,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { useUsageBudget } from '@/hooks/dashboard/useUsageBudget';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export function UsageBudgetSection() {
  const { data, isLoading, error } = useUsageBudget();

  if (isLoading) {
    return <UsageBudgetSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage & Budget</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Failed to load usage data</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const budgetPercentage = data.budget_limit
    ? (data.total_cost / data.budget_limit) * 100
    : 0;
  const forecastPercentage = data.budget_limit
    ? (data.forecast_month_end / data.budget_limit) * 100
    : 0;

  const hasAlerts = data.alerts.length > 0;

  // Transform history for chart (last 7 days for better visibility)
  const chartData = data.history.slice(-7).map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    cost: item.total_cost,
    tokens: item.total_tokens,
  }));

  return (
    <div className="space-y-4">
      {/* Budget Alerts */}
      {hasAlerts && (
        <div className="space-y-2">
          {data.alerts.map((alert, index) => (
            <Alert
              key={index}
              variant={alert.alert_type === 'exceeded' ? 'destructive' : 'default'}
            >
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="h-5 w-5 text-muted-foreground" />
              <Badge variant={budgetPercentage > 90 ? 'destructive' : 'secondary'}>
                {budgetPercentage.toFixed(0)}%
              </Badge>
            </div>
            <div className="text-2xl font-bold">${data.total_cost.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">
              Current spend
              {data.budget_limit && ` of $${data.budget_limit.toFixed(2)}`}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
              <Badge variant={forecastPercentage > 100 ? 'destructive' : 'secondary'}>
                {forecastPercentage.toFixed(0)}%
              </Badge>
            </div>
            <div className="text-2xl font-bold">
              ${data.forecast_month_end.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground">
              Forecast (month end)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <Zap className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-2xl font-bold">
              {(data.total_tokens / 1000).toFixed(1)}K
            </div>
            <div className="text-xs text-muted-foreground">
              Total tokens (this month)
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 7-Day History Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Usage (Last 7 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  className="text-xs"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  className="text-xs"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                  formatter={(value: number, name: string) => [
                    name === 'cost' ? `$${value.toFixed(2)}` : `${(value / 1000).toFixed(1)}K`,
                    name === 'cost' ? 'Cost' : 'Tokens',
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="cost"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                  name="cost"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[250px]">
              <p className="text-center text-muted-foreground">
                No usage data available yet
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Budget Information */}
      {data.budget_limit && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Monthly Budget</span>
              <span className="font-medium">${data.budget_limit.toFixed(2)}</span>
            </div>
            <div className="mt-2">
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    budgetPercentage > 90
                      ? 'bg-red-500'
                      : budgetPercentage > 75
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(budgetPercentage, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function UsageBudgetSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    </div>
  );
}
