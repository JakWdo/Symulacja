import { Card, CardContent } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ArrowUp, ArrowDown, Minus, HelpCircle } from 'lucide-react';
import type { MetricCard as MetricCardType } from '@/types/dashboard';

interface MetricCardProps {
  metric: MetricCardType;
}

export function MetricCard({ metric }: MetricCardProps) {
  const TrendIcon =
    metric.trend?.direction === 'up'
      ? ArrowUp
      : metric.trend?.direction === 'down'
        ? ArrowDown
        : Minus;

  const trendColor =
    metric.trend?.direction === 'up'
      ? 'text-green-600'
      : metric.trend?.direction === 'down'
        ? 'text-red-600'
        : 'text-gray-400';

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{metric.label}</p>
            <p className="text-2xl font-bold">{metric.value}</p>
          </div>
          {metric.tooltip && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <HelpCircle className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <div className="max-w-xs text-sm space-y-1">
                    <p>{metric.tooltip}</p>
                    {metric.p90 && (
                      <p className="text-muted-foreground">
                        P90: {metric.p90.toFixed(1)} min
                      </p>
                    )}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        {metric.trend && (
          <div className={`mt-2 flex items-center text-sm ${trendColor}`}>
            <TrendIcon className="mr-1 h-4 w-4" />
            <span>{Math.abs(metric.trend.change_percent).toFixed(1)}%</span>
            <span className="ml-1 text-muted-foreground">vs last week</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
