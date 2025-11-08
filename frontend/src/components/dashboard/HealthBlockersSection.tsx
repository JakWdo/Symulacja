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
import { useTranslation } from 'react-i18next';
import { useHealthBlockers } from '@/hooks/dashboard/useHealthBlockers';
import type { BlockerWithFix } from '@/types/dashboard';

const HEALTH_STATUS_CONFIG = {
  on_track: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-500/10',
  },
  at_risk: {
    icon: AlertCircle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-500/10',
  },
  blocked: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-500/10',
  },
};

const SEVERITY_CONFIG = {
  critical: { color: 'bg-red-500' },
  high: { color: 'bg-orange-500' },
  medium: { color: 'bg-yellow-500' },
  low: { color: 'bg-blue-500' },
};

interface HealthBlockersSectionProps {
  onFixBlocker?: (url: string) => void | Promise<void>;
}

export function HealthBlockersSection({ onFixBlocker }: HealthBlockersSectionProps) {
  const { t } = useTranslation('dashboard');
  const { data, isLoading, error } = useHealthBlockers();

  if (isLoading) {
    return <HealthBlockersSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('health.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{t('health.error')}</AlertDescription>
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
    <Card className="border-border rounded-figma-card">
      <CardHeader className="px-6 pt-6 pb-4">
        <div className="flex items-center gap-2 mb-1.5">
          <AlertCircle className="h-5 w-5 text-foreground" />
          <CardTitle className="text-base font-normal text-foreground leading-[16px]">
            {t('health.title')}
          </CardTitle>
        </div>
        <p className="text-base text-muted-foreground leading-[24px]">
          {t('health.subtitle')}
        </p>
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
                <BlockerCard key={index} blocker={blocker} onFixBlocker={onFixBlocker} t={t} />
              ))}
          </div>
        ) : (
          <div className="py-12 text-center">
            <CheckCircle className="h-12 w-12 mx-auto text-success mb-4" />
            <p className="font-medium text-lg mb-2">{t('health.allGood.title')}</p>
            <p className="text-sm text-figma-muted">
              {t('health.allGood.description')}
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

function BlockerCard({
  blocker,
  onFixBlocker,
  t,
}: {
  blocker: BlockerWithFix;
  onFixBlocker?: (url: string) => void | Promise<void>;
  t: any;
}) {
  const handleFix = () => {
    if (!blocker.fix_url) {
      return;
    }
    if (onFixBlocker) {
      void onFixBlocker(blocker.fix_url);
    } else {
      window.location.href = blocker.fix_url;
    }
  };

  return (
    <div className="border border-red-500/20 dark:border-red-500/30 bg-red-500/5 dark:bg-red-500/10 rounded-[8px] p-[13px] flex items-start justify-between gap-4">
      {/* Left: Icon + Content */}
      <div className="flex items-start gap-3 flex-1 min-w-0">
        {/* Alert Icon */}
        <div className="flex-shrink-0">
          <AlertTriangle className="h-4 w-4 text-error" />
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
          className="bg-error hover:bg-error/90 text-white h-8 px-3 flex-shrink-0 rounded-[6px]"
        >
          {t('health.fixButton')}
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
