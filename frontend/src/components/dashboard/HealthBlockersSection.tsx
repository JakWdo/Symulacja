/**
 * Health & Blockers Section - Shows project health summary and list of blockers
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  XCircle,
  Wrench,
  Activity,
} from 'lucide-react';
import { useHealthBlockers } from '@/hooks/dashboard/useHealthBlockers';
import type { BlockerWithFix } from '@/types/dashboard';

const HEALTH_STATUS_CONFIG = {
  on_track: {
    icon: CheckCircle,
    label: 'On Track',
    color: 'text-green-600',
    bgColor: 'bg-green-500/10',
  },
  at_risk: {
    icon: AlertCircle,
    label: 'At Risk',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-500/10',
  },
  blocked: {
    icon: XCircle,
    label: 'Blocked',
    color: 'text-red-600',
    bgColor: 'bg-red-500/10',
  },
};

const SEVERITY_CONFIG = {
  critical: { color: 'bg-red-500', label: 'Critical' },
  high: { color: 'bg-orange-500', label: 'High' },
  medium: { color: 'bg-yellow-500', label: 'Medium' },
  low: { color: 'bg-blue-500', label: 'Low' },
};

export function HealthBlockersSection() {
  const { data, isLoading, error } = useHealthBlockers();

  if (isLoading) {
    return <HealthBlockersSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Project Health</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Failed to load health data</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const totalProjects =
    data.summary.on_track + data.summary.at_risk + data.summary.blocked;
  const hasBlockers = data.blockers.length > 0;

  return (
    <div className="space-y-4">
      {/* Health Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <HealthSummaryCard
          status="on_track"
          count={data.summary.on_track}
          total={totalProjects}
        />
        <HealthSummaryCard
          status="at_risk"
          count={data.summary.at_risk}
          total={totalProjects}
        />
        <HealthSummaryCard
          status="blocked"
          count={data.summary.blocked}
          total={totalProjects}
        />
      </div>

      {/* Blockers List */}
      {hasBlockers ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Active Blockers</CardTitle>
              <Badge variant="destructive">{data.blockers.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.blockers
                .sort((a, b) => {
                  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
                  return severityOrder[a.severity] - severityOrder[b.severity];
                })
                .map((blocker, index) => (
                  <BlockerCard key={index} blocker={blocker} />
                ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
            <p className="font-medium text-lg mb-2">All Clear!</p>
            <p className="text-sm text-muted-foreground">
              No active blockers. All projects are on track.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function HealthSummaryCard({
  status,
  count,
  total,
}: {
  status: 'on_track' | 'at_risk' | 'blocked';
  count: number;
  total: number;
}) {
  const config = HEALTH_STATUS_CONFIG[status];
  const Icon = config.icon;
  const percentage = total > 0 ? ((count / total) * 100).toFixed(0) : '0';

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`h-6 w-6 ${config.color}`} />
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{count}</div>
            <div className="text-xs text-muted-foreground">{percentage}%</div>
          </div>
        </div>
        <div className="text-sm font-medium">{config.label}</div>
        <div className="text-xs text-muted-foreground">
          {count} of {total} projects
        </div>
      </CardContent>
    </Card>
  );
}

function BlockerCard({ blocker }: { blocker: BlockerWithFix }) {
  const severityConfig = SEVERITY_CONFIG[blocker.severity];

  const handleFix = () => {
    if (blocker.fix_url) {
      window.location.href = blocker.fix_url;
    }
  };

  return (
    <Card className="border-l-4 border-l-red-500">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Severity Indicator */}
          <div className="flex-shrink-0">
            <div className={`w-2 h-2 rounded-full ${severityConfig.color} mt-2`} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="destructive" className="text-xs">
                {severityConfig.label}
              </Badge>
              <span className="text-xs text-muted-foreground">{blocker.type}</span>
            </div>

            <p className="text-sm font-medium mb-1">{blocker.project_name}</p>
            <p className="text-sm text-muted-foreground mb-3">{blocker.message}</p>

            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                Action: {blocker.fix_action}
              </span>
              {blocker.fix_url && (
                <Button size="sm" variant="outline" onClick={handleFix}>
                  <Wrench className="h-4 w-4 mr-1" />
                  Fix
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function HealthBlockersSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(2)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
