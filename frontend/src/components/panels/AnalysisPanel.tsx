import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  BarChart3,
  TrendingUp,
  Users,
  Zap,
  Download,
  FileText,
  Sparkles,
  MessageSquare,
  Clock3,
  Gauge,
  CheckCircle2,
  HeartPulse,
  Brain,
  Activity,
  Layers,
  AlertTriangle,
  ShieldCheck,
  Lightbulb,
  Quote,
  LayoutDashboard,
  PieChart,
  CheckSquare,
  Settings,
} from 'lucide-react';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { analysisApi, focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type {
  FocusGroupInsights,
  FocusGroupResponses,
  Persona,
  MetricExplanationsResponse,
  HealthCheck,
  AdvancedInsights,
  HealthAssessment,
  DemographicCorrelations,
  TemporalAnalysis,
  BehavioralSegmentation,
  QualityMetrics,
  ComparativeAnalysis,
  OutlierDetection,
  EngagementPatterns,
  BusinessInsights,
} from '@/types';
// Removed unused Recharts imports - charts moved to dedicated components
import { formatTime } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import { PersonaInsightDrawer } from '@/components/analysis/PersonaInsightDrawer';
import { AISummaryPanel } from '@/components/analysis/AISummaryPanel';
import { MetricCardWithExplanation } from '@/components/analysis/MetricCardWithExplanation';
import { BusinessMetricsOverview } from '@/components/analysis/BusinessMetricsOverview';
import { Tabs, type TabItem } from '@/components/ui/Tabs';

function IdeaScoreGauge({
  score,
  grade,
  confidence,
  rationale,
}: {
  score: number;
  grade: string;
  confidence?: number;
  rationale?: string;
}) {
  return (
    <div className="floating-panel p-6 flex items-center gap-6">
      <div className="relative w-28 h-28">
        <div className="w-full h-full rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center">
          <span className="text-3xl font-bold text-slate-900">{score.toFixed(1)}</span>
        </div>
        <Gauge className="w-6 h-6 text-primary-400 absolute -bottom-2 -right-2" />
      </div>
      <div>
        <p className="text-sm text-slate-500 uppercase tracking-wide">Idea Score</p>
        <p className="text-lg font-semibold text-slate-900">{grade}</p>
        <p className="text-xs text-slate-500 mt-1">
          Ocena ekspercka modelu w skali 1-100 bazująca na jakości odpowiedzi.
        </p>
        {typeof confidence === 'number' && (
          <p className="text-xs text-slate-500 mt-2">
            Pewność modelu: {(confidence * 100).toFixed(0)}%
          </p>
        )}
        {rationale && (
          <p className="text-sm text-slate-600 mt-3 leading-relaxed">
            {rationale}
          </p>
        )}
      </div>
    </div>
  );
}

function QuickStatCard({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-xl font-semibold text-slate-900 mt-1">{value}</p>
      {helper && <p className="text-[11px] text-slate-500 mt-1">{helper}</p>}
    </div>
  );
}

function SignalBreakdownSection({ signals }: { signals?: FocusGroupInsights['signal_breakdown'] }) {
  if (!signals) {
    return null;
  }

  const sections: Array<{
    key: keyof NonNullable<FocusGroupInsights['signal_breakdown']>;
    label: string;
    icon: JSX.Element;
    empty: string;
  }> = [
    {
      key: 'strengths',
      label: 'Najsilniejsze sygnały',
      icon: <ShieldCheck className="w-4 h-4 text-emerald-600" />,
      empty: 'Brak wyróżniających pozytywnych sygnałów.',
    },
    {
      key: 'opportunities',
      label: 'Szanse do wykorzystania',
      icon: <Lightbulb className="w-4 h-4 text-amber-500" />,
      empty: 'Brak wyraźnych szans do opisania.',
    },
    {
      key: 'risks',
      label: 'Ryzyka i bariery',
      icon: <AlertTriangle className="w-4 h-4 text-red-500" />,
      empty: 'Nie znaleziono poważnych ryzyk.',
    },
  ];

  const hasContent = sections.some((section) => (signals?.[section.key] ?? []).length > 0);
  if (!hasContent) {
    return null;
  }

  return (
    <div className="floating-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900">Strategiczne odczyty</h3>
        <p className="text-xs text-slate-500">Wnioski łączące ocenę 1-100 z komentarzami uczestników.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sections.map((section) => {
          const entries = signals?.[section.key] ?? [];
          return (
            <div key={section.key} className="border border-slate-200 rounded-xl bg-white p-4 space-y-3 shadow-sm">
              <div className="flex items-center gap-2">
                {section.icon}
                <p className="text-sm font-semibold text-slate-900">{section.label}</p>
              </div>
              {entries.length === 0 ? (
                <p className="text-xs text-slate-500">{section.empty}</p>
              ) : (
                <ul className="space-y-3">
                  {entries.map((entry, idx) => (
                    <li key={`${section.key}-${idx}`} className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                      <p className="text-sm font-medium text-slate-900">{entry.title}</p>
                      {entry.summary && (
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">{entry.summary}</p>
                      )}
                      {entry.evidence && (
                        <p className="text-xs text-slate-500 mt-2 italic">„{entry.evidence}”</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PersonaPatternsSection({
  personas,
  patterns,
  onSelect,
}: {
  personas: Persona[];
  patterns?: FocusGroupInsights['persona_patterns'];
  onSelect: (personaId: string) => void;
}) {
  const personaMap = useMemo(() => new Map(personas.map((p) => [p.id, p])), [personas]);
  const items = patterns ?? [];

  if (items.length === 0) {
    return null;
  }

  const classificationStyles: Record<string, string> = {
    champion: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    detractor: 'bg-rose-100 text-rose-700 border-rose-200',
    low_engagement: 'bg-amber-100 text-amber-700 border-amber-200',
    neutral: 'bg-slate-100 text-slate-600 border-slate-200',
  };

  const classificationLabel: Record<string, string> = {
    champion: 'Champion',
    detractor: 'Detraktor',
    low_engagement: 'Niska aktywność',
    neutral: 'Neutralny',
  };

  const formatPersona = (id: string) => {
    const persona = personaMap.get(id);
    if (!persona) return `Persona ${id.slice(0, 6)}`;
    const location = persona.location ?? 'brak lokalizacji';
    return `${persona.gender}, ${persona.age} • ${location}`;
  };

  return (
    <div className="floating-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900">Zachowania person</h3>
        <p className="text-xs text-slate-500">Kliknij, żeby podejrzeć pełny profil i historię odpowiedzi.</p>
      </div>
      <div className="space-y-3">
        {items.map((pattern) => (
          <button
            key={pattern.persona_id}
            onClick={() => onSelect(pattern.persona_id)}
            className="w-full text-left p-4 rounded-xl border border-slate-200 hover:border-primary-300 hover:bg-primary-50 transition"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-slate-900">{formatPersona(pattern.persona_id)}</p>
                <p className="text-xs text-slate-500 mt-1">Persona ID: {pattern.persona_id.slice(0, 8)}</p>
              </div>
              <span
                className={`px-2 py-1 text-[11px] font-semibold rounded-full border ${classificationStyles[pattern.classification] ?? classificationStyles.neutral}`}
              >
                {classificationLabel[pattern.classification] ?? classificationLabel.neutral}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mt-3">
              <span>Sentyment: <strong>{pattern.avg_sentiment.toFixed(2)}</strong></span>
              <span>Wkład: <strong>{pattern.contribution_count}</strong></span>
              {pattern.last_activity && (
                <span>Ostatnia aktywność: <strong>{new Date(pattern.last_activity).toLocaleString()}</strong></span>
              )}
            </div>
            {pattern.summary && (
              <p className="text-sm text-slate-600 mt-3 leading-relaxed">{pattern.summary}</p>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

function EvidenceFeedSection({
  personas,
  evidence,
  onPersonaClick,
}: {
  personas: Persona[];
  evidence?: FocusGroupInsights['evidence_feed'];
  onPersonaClick: (personaId: string) => void;
}) {
  const personaMap = useMemo(() => new Map(personas.map((p) => [p.id, p])), [personas]);
  const positives = evidence?.positives ?? [];
  const negatives = evidence?.negatives ?? [];

  if (positives.length === 0 && negatives.length === 0) {
    return null;
  }

  const renderPersona = (personaId: string | null) => {
    if (!personaId) return 'Nieznana persona';
    const persona = personaMap.get(personaId);
    if (!persona) return `Persona ${personaId.slice(0, 6)}`;
    return `${persona.gender}, ${persona.age}`;
  };

  const QuoteCard = ({
    tone,
    entry,
  }: {
    tone: 'positive' | 'negative';
    entry: NonNullable<FocusGroupInsights['evidence_feed']>['positives'][number];
  }) => {
    const isPositive = tone === 'positive';
    const accent = isPositive
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : 'border-rose-200 bg-rose-50 text-rose-700';

    return (
      <div className={`rounded-xl border p-4 space-y-3 ${accent}`}>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Quote className="w-4 h-4" />
          <span>{isPositive ? 'Pozytywny sygnał' : 'Ostrzeżenie'}</span>
        </div>
        <p className="text-sm leading-relaxed text-slate-900">„{entry.response}”</p>
        <div className="text-[11px] text-slate-600 space-y-1">
          <p>
            Persona:{' '}
            {entry.persona_id ? (
              <button
                type="button"
                className="underline decoration-dotted decoration-slate-500 hover:text-slate-900"
                onClick={() => onPersonaClick(entry.persona_id!)}
              >
                {renderPersona(entry.persona_id)}
              </button>
            ) : (
              <span>{renderPersona(entry.persona_id ?? null)}</span>
            )}
          </p>
          <p>Sentyment: {entry.sentiment.toFixed(2)}</p>
          {entry.question && <p>Pytanie: {entry.question}</p>}
          {entry.created_at && <p>Czas: {new Date(entry.created_at).toLocaleString()}</p>}
        </div>
        {typeof entry.consistency_score === 'number' && (
          <p className="text-[11px] text-slate-500">Spójność odpowiedzi: {entry.consistency_score.toFixed(2)}</p>
        )}
      </div>
    );
  };

  return (
    <div className="floating-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900">Evidence Feed</h3>
        <p className="text-xs text-slate-500">Najważniejsze cytaty wspierające ocenę.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {positives.slice(0, 4).map((entry, idx) => (
          <QuoteCard tone="positive" entry={entry} key={`pos-${idx}`} />
        ))}
        {negatives.slice(0, 4).map((entry, idx) => (
          <QuoteCard tone="negative" entry={entry} key={`neg-${idx}`} />
        ))}
      </div>
    </div>
  );
}

const metricIconMap: Record<string, JSX.Element> = {
  idea_score: <TrendingUp className="w-5 h-5" />,
  consensus: <Users className="w-5 h-5" />,
  sentiment: <Sparkles className="w-5 h-5" />,
  completion_rate: <CheckCircle2 className="w-5 h-5" />,
  consistency_score: <Gauge className="w-5 h-5" />,
  response_time: <Clock3 className="w-5 h-5" />,
};

function getMetricVariant(
  metricKey: string,
  insights: FocusGroupInsights | null
): 'success' | 'warning' | 'danger' | 'default' {
  if (!insights) {
    return 'default';
  }

  switch (metricKey) {
    case 'idea_score': {
      const score = insights.idea_score ?? 0;
      if (score >= 85) return 'success';
      if (score >= 60) return 'default';
      if (score >= 45) return 'warning';
      return 'danger';
    }
    case 'consensus': {
      const value = insights.metrics.consensus ?? 0;
      if (value >= 0.7) return 'success';
      if (value >= 0.55) return 'default';
      if (value >= 0.4) return 'warning';
      return 'danger';
    }
    case 'sentiment': {
      const value = insights.metrics.average_sentiment ?? 0;
      if (value >= 0.25) return 'success';
      if (value >= 0.1) return 'default';
      if (value >= -0.1) return 'warning';
      return 'danger';
    }
    case 'completion_rate': {
      const value = insights.metrics.engagement.completion_rate ?? 0;
      if (value >= 0.9) return 'success';
      if (value >= 0.75) return 'default';
      if (value >= 0.6) return 'warning';
      return 'danger';
    }
    case 'consistency_score': {
      const value = insights.metrics.engagement.consistency_score;
      if (value === null || value === undefined) return 'warning';
      if (value >= 0.85) return 'success';
      if (value >= 0.7) return 'default';
      if (value >= 0.55) return 'warning';
      return 'danger';
    }
    case 'response_time': {
      const value = insights.metrics.engagement.average_response_time_ms;
      if (value === null || value === undefined) return 'default';
      if (value <= 2500) return 'success';
      if (value <= 4000) return 'default';
      if (value <= 6000) return 'warning';
      return 'danger';
    }
    default:
      return 'default';
  }
}

function MetricInsightsSection({
  explanations,
  insights,
}: {
  explanations?: MetricExplanationsResponse['explanations'];
  insights: FocusGroupInsights | null;
}) {
  if (!explanations || Object.keys(explanations).length === 0) {
    return null;
  }

  return (
    <div className="floating-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Gauge className="w-5 h-5 text-primary-500" />
          Interpretacja metryk
        </h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(explanations).map(([metricKey, explanation]) => (
          <MetricCardWithExplanation
            key={metricKey}
            metricKey={metricKey}
            explanation={explanation}
            variant={getMetricVariant(metricKey, insights)}
            icon={metricIconMap[metricKey] ?? <Sparkles className="w-5 h-5" />}
          />
        ))}
      </div>
    </div>
  );
}

function HealthOverview({ assessment }: { assessment?: HealthAssessment }) {
  if (!assessment) {
    return null;
  }

  const healthStyles: Record<string, { badge: string; accent: string }> = {
    healthy: {
      badge: 'bg-green-100 text-green-700',
      accent: 'border-green-200',
    },
    good: {
      badge: 'bg-blue-100 text-blue-700',
      accent: 'border-blue-200',
    },
    fair: {
      badge: 'bg-yellow-100 text-yellow-700',
      accent: 'border-yellow-200',
    },
    poor: {
      badge: 'bg-red-100 text-red-700',
      accent: 'border-red-200',
    },
  };

  const styles = healthStyles[assessment.status] ?? {
    badge: 'bg-slate-100 text-slate-700',
    accent: 'border-slate-200',
  };

  return (
    <div className={`floating-panel p-6 border ${styles.accent} space-y-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <HeartPulse className="w-5 h-5 text-red-500" />
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Health score</p>
            <p className="text-2xl font-semibold text-slate-900">
              {assessment.health_score.toFixed(1)} / 100
            </p>
          </div>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full font-semibold ${styles.badge}`}>
          {assessment.status_label}
        </span>
      </div>

      <p className="text-sm text-slate-700 leading-relaxed">{assessment.message}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Mocne strony</p>
          {assessment.strengths.length > 0 ? (
            <ul className="space-y-1 text-sm text-green-700">
              {assessment.strengths.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500">Brak wyraźnych przewag.</p>
          )}
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Ryzyka</p>
          {assessment.concerns.length > 0 ? (
            <ul className="space-y-1 text-sm text-amber-700">
              {assessment.concerns.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500">Brak krytycznych ostrzeżeń.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function AdvancedInsightsSection({
  insights,
  isFetching,
  onGenerate,
  hasData,
  disabled,
  hasRequested,
}: {
  insights?: AdvancedInsights;
  isFetching: boolean;
  onGenerate: () => void;
  hasData: boolean;
  disabled: boolean;
  hasRequested: boolean;
}) {
  if (disabled) {
    return null;
  }

  const demographic = (insights?.demographic_correlations ?? {}) as DemographicCorrelations;
  const temporal = insights?.temporal_analysis as TemporalAnalysis | undefined;
  const segments = (
    insights?.behavioral_segments as BehavioralSegmentation | undefined
  )?.segments ?? [];
  const quality = (insights?.quality_metrics ?? {}) as QualityMetrics;
  const comparison = (insights?.comparative_analysis ?? {}) as ComparativeAnalysis;
  const outliers = (insights?.outlier_detection ?? {}) as OutlierDetection;
  const engagement = (insights?.engagement_patterns ?? {}) as EngagementPatterns;

  return (
    <div className="floating-panel p-6 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-500" />
          Zaawansowana analityka
        </h3>
        <button
          type="button"
          onClick={onGenerate}
          disabled={isFetching || disabled}
          className="floating-button px-4 py-2 flex items-center gap-2 text-sm"
        >
          {isFetching ? (
            <>
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-slate-600" />
              Analizuję...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              {hasData ? 'Odśwież analizę' : 'Uruchom analizę' }
            </>
          )}
        </button>
      </div>

      {!hasData ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600">
          {hasRequested ? (
            <p>Analiza w toku – odśwież za chwilę, aby zobaczyć wyniki.</p>
          ) : (
            <p>
              Wygeneruj głęboką analizę korelacji demograficznych, segmentacji behawioralnej i dynamiki w czasie.
              Proces może potrwać kilka sekund.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-5">
          <section className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary-500" />
              Korelacje demograficzne
            </h4>
            <ul className="space-y-2 text-sm text-slate-600">
              {demographic && 'age_sentiment' in demographic && demographic.age_sentiment ? (
                <li>
                  <strong>Wiek:</strong> {demographic.age_sentiment.interpretation} (r = {demographic.age_sentiment.correlation.toFixed(2)})
                </li>
              ) : null}
              {demographic && 'gender_sentiment' in demographic && demographic.gender_sentiment ? (
                <li>
                  <strong>Płeć:</strong> {demographic.gender_sentiment.interpretation}
                </li>
              ) : null}
              {demographic && 'education_sentiment' in demographic && demographic.education_sentiment ? (
                <li>
                  <strong>Edukacja:</strong> Najlepszy segment: {demographic.education_sentiment.top_segment ?? '—'};
                  najsłabszy: {demographic.education_sentiment.bottom_segment ?? '—'}
                </li>
              ) : null}
              {demographic && 'personality_sentiment' in demographic && demographic.personality_sentiment ? (
                <li>
                  <strong>Cechy osobowości:</strong> {Object.entries(demographic.personality_sentiment)
                    .slice(0, 3)
                    .map(([trait, value]) => `${trait}: r=${value.correlation.toFixed(2)}`)
                    .join(', ')}
                </li>
              ) : null}
              {(!demographic || Object.keys(demographic).length === 0) && (
                <li>Brak wykrytych zależności demograficznych.</li>
              )}
            </ul>
          </section>

          <section className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Activity className="w-4 h-4 text-accent-500" />
              Trendy w czasie
            </h4>
            {temporal?.overall_trend ? (
              <div className="text-sm text-slate-600 space-y-1">
                <p>
                  Kierunek: <strong>{temporal.overall_trend.direction === 'improving' ? 'rosnący' : temporal.overall_trend.direction === 'declining' ? 'spadkowy' : 'stabilny'}</strong>
                  {temporal.overall_trend.significant ? ' (istotny statystycznie)' : ''}
                </p>
                <p>
                  Początek vs koniec sentymentu:{' '}
                  {temporal.sentiment_trajectory?.initial_sentiment !== undefined
                    ? temporal.sentiment_trajectory.initial_sentiment.toFixed(2)
                    : '—'}{' '}
                  →{' '}
                  {temporal.sentiment_trajectory?.final_sentiment !== undefined
                    ? temporal.sentiment_trajectory.final_sentiment.toFixed(2)
                    : '—'}
                </p>
                {temporal.fatigue_analysis && (
                  <p>{temporal.fatigue_analysis.interpretation}</p>
                )}
                {temporal.momentum_shifts && temporal.momentum_shifts.length > 0 && (
                  <ul className="list-disc list-inside text-xs text-slate-500">
                    {temporal.momentum_shifts.map((shift, idx) => (
                      <li key={idx}>
                        Q{shift.index + 1}: zmiana sentymentu {shift.sentiment_change.toFixed(2)} ({shift.question})
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Brak danych do analizy trendów.</p>
            )}
          </section>

          <section className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Users className="w-4 h-4 text-primary-600" />
              Segmentacja behawioralna
            </h4>
            {segments && segments.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {segments.map((segment) => (
                  <div key={segment.segment_id} className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-slate-900">{segment.label}</p>
                      <span className="text-xs text-slate-500">{segment.percentage.toFixed(0)}% ({segment.size})</span>
                    </div>
                    <p className="text-xs text-slate-500">Śr. sentyment: {segment.characteristics.avg_sentiment.toFixed(2)}</p>
                    <p className="text-xs text-slate-500">Śr. długość odpowiedzi: {segment.characteristics.avg_response_length.toFixed(0)} słów</p>
                    <p className="text-xs text-slate-500">Dominująca edukacja: {segment.demographics.top_education}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Zbyt mało danych, by utworzyć segmenty.</p>
            )}
          </section>

          <section className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              Jakość odpowiedzi
            </h4>
            {quality && Object.keys(quality).length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-slate-600">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Ogólna jakość</p>
                  <p className="text-lg font-semibold text-slate-900">{(quality.overall_quality ?? 0).toFixed(2)}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Głębokość</p>
                  <p className="text-lg font-semibold text-slate-900">{(quality.depth_score ?? 0).toFixed(2)}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Konstruktywność</p>
                  <p className="text-lg font-semibold text-slate-900">{(quality.constructiveness_score ?? 0).toFixed(2)}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Brak dodatkowych metryk jakości.</p>
            )}
          </section>

          <section className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-accent-600" />
              Porównanie pytań
            </h4>
            {comparison && (comparison.best_questions?.length || comparison.worst_questions?.length) ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-slate-600">
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Top 3 pytania</p>
                  <ul className="space-y-1">
                    {comparison.best_questions?.map((item, idx) => (
                      <li key={`${item.question}-${idx}`}>
                        <strong>{item.avg_sentiment.toFixed(2)}</strong> – {item.question}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Najtrudniejsze pytania</p>
                  <ul className="space-y-1">
                    {comparison.worst_questions?.map((item, idx) => (
                      <li key={`${item.question}-${idx}`}>
                        <strong>{item.avg_sentiment.toFixed(2)}</strong> – {item.question}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Brak wystarczających danych do porównań.</p>
            )}
          </section>

          <section className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-slate-600">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">Wykryte odchylenia</p>
              <p>Sentiment: {outliers.sentiment_outliers ?? 0}</p>
              <p>Długość wypowiedzi: {outliers.length_outliers ?? 0}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">Zaangażowanie</p>
              <p>Wysoko zaangażowani: {engagement.high_engagers ?? 0}</p>
              <p>Nisko zaangażowani: {engagement.low_engagers ?? 0}</p>
              <p>Śr. czas odpowiedzi: {engagement.avg_response_time ? `${engagement.avg_response_time.toFixed(0)} ms` : '—'}</p>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function ResponseExplorer({
  responses,
  personas,
  onPersonaClick,
}: {
  responses: FocusGroupResponses | undefined;
  personas: Persona[];
  onPersonaClick: (personaId: string) => void;
}) {
  const personaMap = useMemo(() => new Map(personas.map((p) => [p.id, p])), [personas]);

  if (!responses || responses.questions.length === 0) {
    return null;
  }

  const formatPersona = (personaId: string) => {
    const persona = personaMap.get(personaId);
    if (!persona) return `Persona ${personaId.slice(0, 6)}`;
    return `${persona.gender}, ${persona.age}`;
  };

  return (
    <div className="floating-panel p-6 space-y-4">
      <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-accent-500" />
        Wszystkie odpowiedzi ({responses.total_responses})
      </h3>
      <div className="space-y-4">
        {responses.questions.map((questionBlock, idx) => (
          <details key={idx} className="rounded-xl border border-slate-200 bg-white" open={idx === 0}>
            <summary className="cursor-pointer select-none px-4 py-3 flex items-center justify-between gap-4">
              <span className="text-sm font-medium text-slate-900">{questionBlock.question}</span>
              <span className="text-xs text-slate-500">{questionBlock.responses.length} odpowiedzi</span>
            </summary>
            <div className="px-4 pb-4 space-y-3">
              {questionBlock.responses.map((response, ridx) => (
                <div
                  key={`${response.persona_id}-${ridx}`}
                  className="p-3 rounded-lg bg-slate-50 border border-slate-200"
                >
                  <div className="flex items-center justify-between gap-3">
                    <button
                      onClick={() => onPersonaClick(response.persona_id)}
                      className="text-sm font-semibold text-primary-600 hover:text-primary-700"
                    >
                      {formatPersona(response.persona_id)}
                    </button>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>Sentyment: {response.sentiment.toFixed(2)}</span>
                      {response.response_time_ms && (
                        <span>
                          <Clock3 className="inline w-3 h-3 mr-1" />
                          {formatTime(response.response_time_ms)}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-slate-700 mt-2 leading-relaxed">
                    {response.response}
                  </p>
                  {(() => {
                    const contradicts = response.contradicts_events;
                    return contradicts && Array.isArray(contradicts) && contradicts.length > 0 ? (
                      <p className="text-xs text-red-500 mt-2">⚠️ Sprzeczności z pamięcią persony</p>
                    ) : null;
                  })()}
                  <p className="text-[10px] text-slate-400 mt-2">
                    {new Date(response.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}

export function AnalysisPanel() {
  const {
    activePanel,
    setActivePanel,
    selectedFocusGroup,
    setSelectedFocusGroup,
    focusGroups,
    personas,
  } = useAppStore();
  const queryClient = useQueryClient();
  const [activePersonaId, setActivePersonaId] = useState<string | null>(null);
  const [hasRequestedAdvanced, setHasRequestedAdvanced] = useState(false);
  const [isExportingEnhanced, setIsExportingEnhanced] = useState(false);

  const completedFocusGroups = useMemo(
    () => focusGroups.filter((fg) => fg.status === 'completed'),
    [focusGroups],
  );

  useEffect(() => {
    if (activePanel === 'analysis' && (!selectedFocusGroup || selectedFocusGroup.status !== 'completed')) {
      const firstCompleted = completedFocusGroups[0] ?? null;
      setSelectedFocusGroup(firstCompleted ?? null);
    }
  }, [activePanel, selectedFocusGroup, completedFocusGroups, setSelectedFocusGroup]);

  const selectedId = selectedFocusGroup?.id ?? null;
  const isCompleted = selectedFocusGroup?.status === 'completed';

  const insightsQuery = useQuery<FocusGroupInsights | null>({
    queryKey: ['focus-group-insights', selectedId],
    queryFn: async () => {
      if (!selectedId || !isCompleted) return null;
      try {
        return await analysisApi.getInsights(selectedId);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled: Boolean(selectedId && isCompleted),
    staleTime: 1000 * 30,
  });

  const refreshInsights = useMutation({
    mutationFn: async () => {
      if (!selectedId) return null;
      const data = await analysisApi.generateInsights(selectedId);
      queryClient.setQueryData(['focus-group-insights', selectedId], data);
      return data;
    },
    onSuccess: () => {
      toast.success('Analiza odświeżona', 'Nowe metryki są już dostępne.');
      if (selectedId) {
        queryClient.invalidateQueries({ queryKey: ['focus-group-metric-explanations', selectedId] });
        queryClient.invalidateQueries({ queryKey: ['focus-group-health-check', selectedId] });
      }
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? error.message
        : 'Nie udało się odświeżyć analizy.';
      toast.error('Błąd analizy', message);
    },
  });

  const responsesQuery = useQuery<FocusGroupResponses | undefined>({
    queryKey: ['focus-group-responses', selectedId],
    queryFn: async () => {
      if (!selectedId || !isCompleted) return undefined;
      return focusGroupsApi.getResponses(selectedId);
    },
    enabled: Boolean(selectedId && isCompleted),
  });

  const metricExplanationsQuery = useQuery<MetricExplanationsResponse>({
    queryKey: ['focus-group-metric-explanations', selectedId],
    queryFn: () => analysisApi.getMetricExplanations(selectedId!),
    enabled: Boolean(selectedId && isCompleted),
    staleTime: 1000 * 60 * 5,
  });

  const healthCheckQuery = useQuery<HealthCheck>({
    queryKey: ['focus-group-health-check', selectedId],
    queryFn: () => analysisApi.getHealthCheck(selectedId!),
    enabled: Boolean(selectedId && isCompleted),
    staleTime: 1000 * 60 * 5,
  });

  const advancedInsightsQuery = useQuery<AdvancedInsights>({
    queryKey: ['focus-group-advanced-insights', selectedId],
    queryFn: () => analysisApi.getAdvancedInsights(selectedId!),
    enabled: false,
  });

  // AI Business Insights Query (manual trigger only - expensive operation)
  const businessInsightsQuery = useQuery<BusinessInsights>({
    queryKey: ['focus-group-business-insights', selectedId],
    queryFn: () => analysisApi.generateBusinessInsights(selectedId!),
    enabled: false, // Only fetch when explicitly requested
    staleTime: 1000 * 60 * 15, // Cache for 15 minutes (expensive to regenerate)
  });

  const personaInsightsQuery = useQuery({
    queryKey: ['persona-insights', activePersonaId],
    queryFn: () => analysisApi.getPersonaInsights(activePersonaId!),
    enabled: Boolean(activePersonaId),
  });

  const personaHistoryQuery = useQuery({
    queryKey: ['persona-history', activePersonaId],
    queryFn: () => analysisApi.getPersonaHistory(activePersonaId!),
    enabled: Boolean(activePersonaId),
  });

  const insights = insightsQuery.data ?? null;
  const metricExplanations = metricExplanationsQuery.data;
  const healthCheck = healthCheckQuery.data;
  const advancedInsights = advancedInsightsQuery.data;
  const isAdvancedFetching = advancedInsightsQuery.isFetching;
  const isAdvancedDisabled = !isCompleted || !selectedId;
  const healthAssessment = metricExplanations?.health_assessment ?? healthCheck;
  const metricExplanationError = metricExplanationsQuery.error;
  const metricExplanationErrorMessage = metricExplanationError
    ? axios.isAxiosError(metricExplanationError)
      ? metricExplanationError.response?.data?.detail ?? metricExplanationError.message
      : 'Nie udało się pobrać interpretacji metryk.'
    : null;

  useEffect(() => {
    setHasRequestedAdvanced(false);
  }, [selectedId]);

  const hasAdvancedResults = useMemo(() => {
    if (!advancedInsights) return false;
    const {
      demographic_correlations,
      temporal_analysis,
      behavioral_segments,
      quality_metrics,
      comparative_analysis,
      outlier_detection,
      engagement_patterns,
    } = advancedInsights;

    if (demographic_correlations && Object.keys(demographic_correlations).length > 0) {
      return true;
    }

    if (
      temporal_analysis &&
      (
        Boolean(temporal_analysis.overall_trend) ||
        Boolean(temporal_analysis.momentum_shifts && temporal_analysis.momentum_shifts.length > 0)
      )
    ) {
      return true;
    }

    if (
      behavioral_segments?.segments &&
      behavioral_segments.segments.length > 0
    ) {
      return true;
    }

    if (quality_metrics && Object.keys(quality_metrics).length > 0) {
      return true;
    }

    if (
      comparative_analysis &&
      ((comparative_analysis.best_questions?.length ?? 0) > 0 ||
        (comparative_analysis.worst_questions?.length ?? 0) > 0)
    ) {
      return true;
    }

    if (
      outlier_detection &&
      ((outlier_detection.sentiment_outliers ?? 0) > 0 || (outlier_detection.length_outliers ?? 0) > 0)
    ) {
      return true;
    }

    if (engagement_patterns && Object.keys(engagement_patterns).length > 0) {
      return true;
    }

    return false;
  }, [advancedInsights]);

  const handleAdvancedInsightsGenerate = async () => {
    if (!selectedId || !isCompleted) {
      return;
    }
    setHasRequestedAdvanced(true);
    try {
      await advancedInsightsQuery.refetch({ throwOnError: true });
      toast.success('Zaawansowana analiza gotowa', 'Sekcja została zaktualizowana.');
    } catch (error) {
      setHasRequestedAdvanced(false);
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? error.message
        : 'Nie udało się wygenerować zaawansowanej analizy.';
      toast.error('Błąd analizy', message);
    }
  };

  const handleBusinessInsightsGenerate = async () => {
    if (!selectedId || !isCompleted) {
      return;
    }
    try {
      await businessInsightsQuery.refetch({ throwOnError: true });
      toast.success('AI Business Insights gotowe', 'Metryki biznesowe zostały wygenerowane.');
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? error.message
        : 'Nie udało się wygenerować AI Business Insights.';
      toast.error('Błąd AI Insights', message);
    }
  };

  const handleEnhancedReportExport = async () => {
    if (!selectedFocusGroup) {
      return;
    }
    setIsExportingEnhanced(true);
    try {
      const blob = await analysisApi.exportEnhancedPDF(
        selectedFocusGroup.id,
        true,
        true,
        false
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `enhanced_report_${selectedFocusGroup.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Raport pobrany', 'Rozszerzony PDF został zapisany lokalnie.');
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? error.message
        : 'Nie udało się wygenerować rozszerzonego raportu.';
      toast.error('Błąd eksportu', message);
    } finally {
      setIsExportingEnhanced(false);
    }
  };

  const handleFocusGroupChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const id = event.target.value;
    const fg = focusGroups.find((item) => item.id === id) ?? null;
    setSelectedFocusGroup(fg);
  };

  const handlePersonaSelect = (personaId: string) => {
    setActivePersonaId(personaId);
  };

  const closePersonaDrawer = () => {
    setActivePersonaId(null);
  };

  // Tabs configuration
  const analysisTabs = useMemo((): TabItem[] => {
    if (!insights) return [];

    return [
      {
        id: 'overview',
        label: 'Overview',
        icon: <LayoutDashboard className="w-4 h-4" />,
        content: (
          <div className="space-y-4">
            {/* AI Summary */}
            {isCompleted && selectedFocusGroup && (
              <AISummaryPanel
                focusGroupId={selectedFocusGroup.id}
                focusGroupName={selectedFocusGroup.name}
              />
            )}

            {/* AI Business Metrics */}
            <BusinessMetricsOverview
              insights={businessInsightsQuery.data || null}
              isLoading={businessInsightsQuery.isFetching}
            />

            {/* Idea Score */}
            <IdeaScoreGauge
              score={insights.idea_score}
              grade={insights.idea_grade}
              confidence={insights.llm_confidence}
              rationale={insights.llm_rationale}
            />

            {/* Key Metrics (without response_time) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <QuickStatCard
                label="Konsensus"
                value={`${(insights.metrics.consensus * 100).toFixed(1)}%`}
                helper="Im wyżej, tym mniejsze rozbieżności w opiniach."
              />
              <QuickStatCard
                label="Średni sentyment"
                value={insights.metrics.average_sentiment.toFixed(2)}
                helper="Dodatnie wartości oznaczają pozytywny odbiór."
              />
            </div>

            {/* Signal Breakdown */}
            <SignalBreakdownSection signals={insights.signal_breakdown} />

            {/* Health Overview */}
            <HealthOverview assessment={healthAssessment} />
          </div>
        ),
      },
      {
        id: 'demographics',
        label: 'Demographics',
        icon: <PieChart className="w-4 h-4" />,
        content: (
          <div className="space-y-4">
            {/* Persona Patterns */}
            <PersonaPatternsSection
              personas={personas}
              patterns={insights.persona_patterns}
              onSelect={handlePersonaSelect}
            />

            {/* Evidence Feed */}
            <EvidenceFeedSection
              personas={personas}
              evidence={insights.evidence_feed}
              onPersonaClick={handlePersonaSelect}
            />

            {/* Metric Explanations */}
            {metricExplanationsQuery.isLoading && (
              <div className="floating-panel p-6 text-sm text-slate-600">
                Ładowanie interpretacji metryk...
              </div>
            )}

            {metricExplanationsQuery.isError && metricExplanationErrorMessage && (
              <div className="floating-panel p-6 border border-red-200 bg-red-50 text-sm text-red-700">
                {metricExplanationErrorMessage}
              </div>
            )}

            <MetricInsightsSection
              explanations={metricExplanations?.explanations}
              insights={insights}
            />
          </div>
        ),
      },
      {
        id: 'quality',
        label: 'Quality & Engagement',
        icon: <CheckSquare className="w-4 h-4" />,
        content: (
          <div className="space-y-4">
            {/* Quality metrics would go here */}
            <div className="floating-panel p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-green-600" />
                Response Quality
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <QuickStatCard
                  label="Completion Rate"
                  value={`${((insights.metrics.engagement?.completion_rate || 0) * 100).toFixed(1)}%`}
                  helper="Percentage of questions answered by participants."
                />
                <QuickStatCard
                  label="Avg. Consistency"
                  value={(insights.metrics.engagement?.consistency_score || 0).toFixed(2)}
                  helper="How consistent responses are with persona profiles."
                />
              </div>
            </div>

            {/* Response Explorer */}
            <ResponseExplorer
              personas={personas}
              responses={responsesQuery.data}
              onPersonaClick={handlePersonaSelect}
            />
          </div>
        ),
      },
      {
        id: 'advanced',
        label: 'Advanced Analytics',
        icon: <Settings className="w-4 h-4" />,
        content: (
          <div className="space-y-4">
            {/* Advanced Insights Section */}
            <AdvancedInsightsSection
              insights={advancedInsights}
              isFetching={isAdvancedFetching}
              onGenerate={handleAdvancedInsightsGenerate}
              hasData={hasAdvancedResults}
              disabled={isAdvancedDisabled}
              hasRequested={hasRequestedAdvanced}
            />
          </div>
        ),
      },
    ];
  }, [
    insights,
    selectedFocusGroup,
    isCompleted,
    businessInsightsQuery.data,
    businessInsightsQuery.isFetching,
    personas,
    healthAssessment,
    metricExplanationsQuery.isLoading,
    metricExplanationsQuery.isError,
    metricExplanationErrorMessage,
    metricExplanations,
    responsesQuery.data,
    advancedInsights,
    isAdvancedFetching,
    hasAdvancedResults,
    isAdvancedDisabled,
    hasRequestedAdvanced,
    handlePersonaSelect,
    handleAdvancedInsightsGenerate,
  ]);

  return (
    <FloatingPanel
      isOpen={activePanel === 'analysis'}
      onClose={() => setActivePanel(null)}
      title="Analiza & Insights"
      panelKey="analysis"
      size="xl"
    >
      <div className="p-4 space-y-4">
        {completedFocusGroups.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <TrendingUp className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600">Ukończ najpierw sesję focus group, aby zobaczyć analizę.</p>
          </div>
        ) : !selectedFocusGroup ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <BarChart3 className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600">Wybierz focus group do analizy.</p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <label className="text-sm text-slate-600" htmlFor="analysis-focus-group">
                  Wybierz focus group:
                </label>
                <select
                  id="analysis-focus-group"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                  value={selectedFocusGroup.id}
                  onChange={handleFocusGroupChange}
                >
                  {completedFocusGroups.map((fg) => (
                    <option key={fg.id} value={fg.id}>
                      {fg.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleBusinessInsightsGenerate}
                  disabled={businessInsightsQuery.isFetching || !isCompleted}
                  className="floating-button px-4 py-2 flex items-center gap-2 text-sm bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {businessInsightsQuery.isFetching ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
                      Generating AI Insights...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      {businessInsightsQuery.data ? 'Refresh AI Insights' : 'Generate AI Insights'}
                    </>
                  )}
                </button>
                <button
                  onClick={() => refreshInsights.mutate()}
                  disabled={refreshInsights.isPending || !isCompleted}
                  className="floating-button px-4 py-2 flex items-center gap-2 text-sm"
                >
                  {refreshInsights.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-slate-600" />
                      Analizuję...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Odśwież analizę
                    </>
                  )}
                </button>
                <button
                  onClick={() => analysisApi.exportPDF(selectedFocusGroup.id).then((blob) => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `analysis_${selectedFocusGroup.id}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                  })}
                  className="floating-button px-3 py-2 text-sm flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  PDF
                </button>
                <button
                  onClick={handleEnhancedReportExport}
                  disabled={isExportingEnhanced}
                  className="floating-button px-3 py-2 text-sm flex items-center gap-2"
                >
                  {isExportingEnhanced ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-slate-600" />
                      Generuję...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Raport AI
                    </>
                  )}
                </button>
                <button
                  onClick={() => analysisApi.exportCSV(selectedFocusGroup.id).then((blob) => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `analysis_${selectedFocusGroup.id}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                  })}
                  className="floating-button px-3 py-2 text-sm flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  CSV/XLSX
                </button>
              </div>
            </div>

            {selectedFocusGroup.status !== 'completed' ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <TrendingUp className="w-12 h-12 text-slate-300 mb-3" />
                <p className="text-slate-600">Sesja wciąż trwa. Wróć po zakończeniu, aby zobaczyć wyniki.</p>
              </div>
            ) : insightsQuery.isLoading && !insights ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <TrendingUp className="w-12 h-12 text-primary-300 mb-3 animate-spin" />
                <p className="text-slate-600">Ładowanie insightów...</p>
              </div>
            ) : insights ? (
              <Tabs tabs={analysisTabs} defaultTab="overview" />
            ) : (
              <div className="space-y-4">
                {/* Show Business Metrics even without insights */}
                <BusinessMetricsOverview
                  insights={businessInsightsQuery.data || null}
                  isLoading={businessInsightsQuery.isFetching}
                />

                <div className="floating-panel p-6 flex items-center gap-4">
                  <TrendingUp className="w-8 h-8 text-primary-400" />
                  <div>
                    <p className="text-sm font-semibold text-slate-900">Brak zapisanych insightów</p>
                    <p className="text-xs text-slate-600">Użyj przycisku „Odśwież analizę", aby wyliczyć ocenę pomysłu na podstawie zebranych odpowiedzi.</p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <PersonaInsightDrawer
        persona={personas.find((p) => p.id === activePersonaId) ?? null}
        insight={personaInsightsQuery.data}
        history={personaHistoryQuery.data}
        loading={personaInsightsQuery.isLoading}
        historyLoading={personaHistoryQuery.isLoading}
        onClose={closePersonaDrawer}
      />
    </FloatingPanel>
  );
}
