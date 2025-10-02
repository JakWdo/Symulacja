/**
 * BusinessMetricsOverview
 *
 * Displays AI-generated business metrics from focus group analysis:
 * - Market Fit Score (0-100)
 * - Readiness Level (not_ready → high_confidence)
 * - Risk Profile (low/medium/high)
 * - Opportunity Score (0-100, top opportunity)
 */

import { useMemo } from 'react';
import {
  TrendingUp,
  Rocket,
  AlertTriangle,
  Lightbulb,
  ChevronRight,
  Info,
} from 'lucide-react';
import type { BusinessInsights } from '@/types';
import { cn } from '@/lib/utils';

interface BusinessMetricsOverviewProps {
  insights: BusinessInsights | null;
  isLoading: boolean;
}

interface MetricCardProps {
  icon: React.ElementType;
  label: string;
  value: string | number;
  score?: number; // Optional 0-100 score for progress bar
  variant: 'success' | 'warning' | 'danger' | 'info' | 'default';
  subtitle?: string;
  onClick?: () => void;
  isClickable?: boolean;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  score,
  variant,
  subtitle,
  onClick,
  isClickable = true,
}: MetricCardProps) {
  const variantStyles = {
    success: {
      border: 'border-green-200',
      bg: 'bg-gradient-to-br from-green-50 to-emerald-50',
      icon: 'text-green-600',
      text: 'text-green-900',
      accent: 'bg-green-500',
    },
    warning: {
      border: 'border-amber-200',
      bg: 'bg-gradient-to-br from-amber-50 to-yellow-50',
      icon: 'text-amber-600',
      text: 'text-amber-900',
      accent: 'bg-amber-500',
    },
    danger: {
      border: 'border-red-200',
      bg: 'bg-gradient-to-br from-red-50 to-rose-50',
      icon: 'text-red-600',
      text: 'text-red-900',
      accent: 'bg-red-500',
    },
    info: {
      border: 'border-purple-200',
      bg: 'bg-gradient-to-br from-purple-50 to-violet-50',
      icon: 'text-purple-600',
      text: 'text-purple-900',
      accent: 'bg-purple-500',
    },
    default: {
      border: 'border-slate-200',
      bg: 'bg-gradient-to-br from-slate-50 to-gray-50',
      icon: 'text-slate-600',
      text: 'text-slate-900',
      accent: 'bg-slate-500',
    },
  };

  const styles = variantStyles[variant];

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!isClickable}
      className={cn(
        'group relative flex flex-col gap-4 rounded-2xl border p-6 shadow-sm transition-all',
        styles.border,
        styles.bg,
        isClickable && 'cursor-pointer hover:shadow-lg hover:scale-[1.02]',
        !isClickable && 'cursor-default'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={cn('flex h-12 w-12 items-center justify-center rounded-xl bg-white/80 shadow-sm', styles.icon)}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="text-left">
            <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
            <p className={cn('text-3xl font-bold', styles.text)}>{value}</p>
          </div>
        </div>
        {isClickable && (
          <ChevronRight className="h-5 w-5 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
        )}
      </div>

      {subtitle && (
        <p className="text-sm text-slate-600 leading-relaxed line-clamp-2">{subtitle}</p>
      )}

      {typeof score === 'number' && (
        <div className="h-2 rounded-full bg-white/60">
          <div
            className={cn('h-full rounded-full transition-all', styles.accent)}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
      )}

      {/* AI Generated Badge */}
      <div className="absolute top-2 right-2">
        <span className="flex items-center gap-1 rounded-full bg-purple-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-purple-700">
          <Info className="h-3 w-3" />
          AI
        </span>
      </div>
    </button>
  );
}

export function BusinessMetricsOverview({ insights, isLoading }: BusinessMetricsOverviewProps) {
  // Determine variants based on scores
  const marketFitVariant = useMemo(() => {
    if (!insights) return 'default';
    const score = insights.market_fit.score;
    if (score >= 71) return 'success';
    if (score >= 51) return 'info';
    if (score >= 31) return 'warning';
    return 'danger';
  }, [insights]);

  const readinessVariant = useMemo(() => {
    if (!insights) return 'default';
    const level = insights.readiness.level;
    if (level === 'high_confidence') return 'success';
    if (level === 'ready') return 'info';
    if (level === 'needs_work') return 'warning';
    return 'danger';
  }, [insights]);

  const riskVariant = useMemo(() => {
    if (!insights) return 'default';
    const level = insights.risk_profile.overall_risk_level;
    if (level === 'low') return 'success';
    if (level === 'medium') return 'warning';
    return 'danger';
  }, [insights]);

  const opportunityVariant = useMemo(() => {
    if (!insights) return 'default';
    const topOpportunity = insights.opportunities.opportunities[0];
    if (!topOpportunity) return 'default';
    const score = topOpportunity.impact_score;
    if (score >= 75) return 'success';
    if (score >= 50) return 'info';
    return 'warning';
  }, [insights]);

  // Format readiness level for display
  const readinessLabel = useMemo(() => {
    if (!insights) return '—';
    const level = insights.readiness.level;
    const labels = {
      not_ready: 'Not Ready',
      needs_work: 'Needs Work',
      ready: 'Ready',
      high_confidence: 'High Confidence',
    };
    return labels[level];
  }, [insights]);

  // Get top opportunity
  const topOpportunity = useMemo(() => {
    if (!insights) return null;
    return insights.opportunities.opportunities[0] || null;
  }, [insights]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-48 rounded-2xl bg-slate-100" />
          </div>
        ))}
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p className="text-sm text-slate-600">
          Generate AI Business Insights to see key metrics
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Info className="h-5 w-5 text-purple-600" />
          AI Business Metrics
        </h3>
        <p className="text-xs text-slate-500">
          Generated: {new Date(insights.generated_at).toLocaleString()}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Market Fit Score */}
        <MetricCard
          icon={TrendingUp}
          label="Market Fit"
          value={insights.market_fit.score}
          score={insights.market_fit.score}
          variant={marketFitVariant}
          subtitle={insights.market_fit.rationale.slice(0, 80) + '...'}
          isClickable={false}
        />

        {/* Readiness Level */}
        <MetricCard
          icon={Rocket}
          label="Readiness"
          value={readinessLabel}
          score={insights.readiness.score}
          variant={readinessVariant}
          subtitle={insights.readiness.recommendation.slice(0, 80) + '...'}
          isClickable={false}
        />

        {/* Risk Profile */}
        <MetricCard
          icon={AlertTriangle}
          label="Risk Level"
          value={insights.risk_profile.overall_risk_level.toUpperCase()}
          variant={riskVariant}
          subtitle={insights.risk_profile.risk_summary.slice(0, 80) + '...'}
          isClickable={false}
        />

        {/* Top Opportunity */}
        <MetricCard
          icon={Lightbulb}
          label="Top Opportunity"
          value={topOpportunity ? topOpportunity.impact_score : '—'}
          score={topOpportunity?.impact_score}
          variant={opportunityVariant}
          subtitle={topOpportunity ? topOpportunity.description.slice(0, 80) + '...' : 'No opportunities identified'}
          isClickable={false}
        />
      </div>
    </div>
  );
}
