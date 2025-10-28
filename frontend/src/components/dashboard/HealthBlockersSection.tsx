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
    label: 'Na bieżąco',
    color: 'text-green-600',
    bgColor: 'bg-green-500/10',
  },
  at_risk: {
    icon: AlertCircle,
    label: 'Zagrożony',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-500/10',
  },
  blocked: {
    icon: XCircle,
    label: 'Zablokowany',
    color: 'text-red-600',
    bgColor: 'bg-red-500/10',
  },
};

const SEVERITY_CONFIG = {
  critical: { color: 'bg-red-500', label: 'Krytyczny' },
  high: { color: 'bg-orange-500', label: 'Wysoki' },
  medium: { color: 'bg-yellow-500', label: 'Średni' },
  low: { color: 'bg-blue-500', label: 'Niski' },
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
          <CardTitle>Stan projektu</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Nie udało się załadować danych o stanie</AlertDescription>
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
    <Card className="border-border rounded-[12px]">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-foreground" />
          <CardTitle className="text-base font-normal text-foreground">Stan i blokady</CardTitle>
        </div>
        <p className="text-base text-muted-foreground">Aktywne problemy wymagające uwagi</p>
      </CardHeader>
      <CardContent>
        {hasBlockers ? (
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
        ) : (
          <div className="py-12 text-center">
            <CheckCircle className="h-12 w-12 mx-auto text-figma-green mb-4" />
            <p className="font-medium text-lg mb-2">Wszystko w porządku!</p>
            <p className="text-sm text-figma-muted">
              Brak aktywnych blokad. Wszystkie projekty na bieżąco.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
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
  const handleFix = () => {
    if (blocker.fix_url) {
      window.location.href = blocker.fix_url;
    }
  };

  return (
    <div className="border border-red-500/20 dark:border-red-500/30 bg-red-500/5 dark:bg-red-500/10 rounded-[8px] p-[13px] flex items-start justify-between gap-4">
      {/* Left: Icon + Content */}
      <div className="flex items-start gap-3 flex-1 min-w-0">
        {/* Alert Icon */}
        <div className="flex-shrink-0">
          <AlertTriangle className="h-4 w-4 text-figma-red" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-1">
          <h4 className="text-sm font-normal text-foreground leading-tight">
            {blocker.project_name}
          </h4>
          <p className="text-sm text-muted-foreground leading-tight">
            {blocker.message}
          </p>
        </div>
      </div>

      {/* Right: Fix Button */}
      {blocker.fix_url && (
        <Button
          onClick={handleFix}
          size="sm"
          className="bg-figma-red hover:bg-figma-red/90 text-white h-8 px-3 flex-shrink-0 rounded-[6px]"
        >
          Napraw
        </Button>
      )}
    </div>
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
