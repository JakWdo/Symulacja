/**
 * Latest Insights Section - Displays latest insights with filtering and detail view
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  AlertCircle,
  Activity,
  Eye,
  CheckCircle,
} from 'lucide-react';
import { useLatestInsights } from '@/hooks/dashboard/useLatestInsights';
import { InsightDetailModal } from './InsightDetailModal';
import type { InsightHighlight } from '@/types/dashboard';

const INSIGHT_TYPE_CONFIG = {
  opportunity: {
    icon: Lightbulb,
    color: 'bg-green-500/10 text-green-700 dark:text-green-400',
    label: 'Szansa',
  },
  risk: {
    icon: AlertCircle,
    color: 'bg-red-500/10 text-red-700 dark:text-red-400',
    label: 'Ryzyko',
  },
  trend: {
    icon: TrendingUp,
    color: 'bg-blue-500/10 text-blue-700 dark:text-blue-400',
    label: 'Trend',
  },
  pattern: {
    icon: Activity,
    color: 'bg-purple-500/10 text-purple-700 dark:text-purple-400',
    label: 'Wzorzec',
  },
};

export function LatestInsightsSection() {
  const { data: insights, isLoading, error } = useLatestInsights(10);
  const [selectedInsight, setSelectedInsight] = useState<InsightHighlight | null>(null);
  const [filter, setFilter] = useState<'all' | 'unviewed' | 'high-impact'>('all');

  if (isLoading) {
    return <LatestInsightsSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Najnowsze spostrzeżenia</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Nie udało się załadować spostrzeżeń</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!insights || insights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Najnowsze spostrzeżenia</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Lightbulb className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground font-medium mb-2">Brak spostrzeżeń</p>
            <p className="text-sm text-muted-foreground mb-4">
              Spostrzeżenia pojawią się tutaj po analizie dyskusji w grupach fokusowych
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Filter insights
  const filteredInsights = insights.filter((insight) => {
    if (filter === 'unviewed') return !insight.is_viewed;
    if (filter === 'high-impact') return insight.impact_score >= 7;
    return true;
  });

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Najnowsze spostrzeżenia</CardTitle>
            <div className="flex gap-2">
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('all')}
              >
                Wszystkie ({insights.length})
              </Button>
              <Button
                variant={filter === 'unviewed' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('unviewed')}
              >
                Nieprzeglądnięte ({insights.filter((i) => !i.is_viewed).length})
              </Button>
              <Button
                variant={filter === 'high-impact' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('high-impact')}
              >
                Wysoki wpływ ({insights.filter((i) => i.impact_score >= 7).length})
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredInsights.map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onViewDetails={() => setSelectedInsight(insight)}
              />
            ))}
            {filteredInsights.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                Brak spostrzeżeń pasujących do wybranego filtra
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedInsight && (
        <InsightDetailModal
          insightId={selectedInsight.id}
          isOpen={!!selectedInsight}
          onClose={() => setSelectedInsight(null)}
        />
      )}
    </>
  );
}

function InsightCard({
  insight,
  onViewDetails,
}: {
  insight: InsightHighlight;
  onViewDetails: () => void;
}) {
  const config = INSIGHT_TYPE_CONFIG[insight.insight_type];
  const Icon = config.icon;

  return (
    <Card className="border-l-4 border-l-blue-500 hover:bg-muted/50 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`p-2 rounded-lg ${config.color}`}>
            <Icon className="h-5 w-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="secondary" className={config.color}>
                {config.label}
              </Badge>
              <span className="text-xs text-muted-foreground">{insight.time_ago}</span>
              {!insight.is_viewed && (
                <Badge variant="default" className="text-xs">
                  Nowe
                </Badge>
              )}
              {insight.is_adopted && (
                <Badge variant="outline" className="text-xs">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Zaakceptowane
                </Badge>
              )}
            </div>

            <p className="text-sm font-medium mb-1">{insight.project_name}</p>
            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
              {insight.insight_text}
            </p>

            <div className="flex items-center justify-between">
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>
                  Pewność: <strong>{(insight.confidence_score * 100).toFixed(0)}%</strong>
                </span>
                <span>
                  Wpływ: <strong>{insight.impact_score}/10</strong>
                </span>
                <span>
                  Dowody: <strong>{insight.evidence_count}</strong>
                </span>
              </div>

              <Button size="sm" variant="outline" onClick={onViewDetails}>
                <Eye className="h-4 w-4 mr-1" />
                Zobacz szczegóły
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function LatestInsightsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
