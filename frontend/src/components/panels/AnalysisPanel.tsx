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
} from 'lucide-react';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { analysisApi, focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { FocusGroupInsights, FocusGroupResponses, Persona } from '@/types';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { formatTime } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import { PersonaInsightDrawer } from '@/components/analysis/PersonaInsightDrawer';

function IdeaScoreGauge({ score, grade }: { score: number; grade: string }) {
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
          Miara łącząca sentyment uczestników i poziom konsensusu.
        </p>
      </div>
    </div>
  );
}

function MetricCard({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-xl font-semibold text-slate-900 mt-1">{value}</p>
      {helper && <p className="text-[11px] text-slate-500 mt-1">{helper}</p>}
    </div>
  );
}

function KeyThemes({ themes }: { themes: FocusGroupInsights['key_themes'] }) {
  if (!themes || themes.length === 0) {
    return null;
  }
  return (
    <div className="floating-panel p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary-500" />
        Najważniejsze motywy
      </h3>
      <div className="space-y-3">
        {themes.map((theme) => (
          <div key={theme.keyword} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
            <p className="text-sm font-medium text-slate-900">
              {theme.keyword} <span className="text-xs text-slate-500">({theme.mentions} wzm.)</span>
            </p>
            {theme.representative_quote && (
              <p className="text-xs text-slate-600 mt-2 italic">“{theme.representative_quote}”</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function QuestionBreakdown({ questions }: { questions: FocusGroupInsights['question_breakdown'] }) {
  if (!questions || questions.length === 0) {
    return null;
  }

  const chartData = questions.map((q, idx) => ({
    name: `Q${idx + 1}`,
    idea: q.idea_score,
    consensus: q.consensus * 100,
  }));

  return (
    <div className="floating-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-accent-600" />
          Szczegóły pytań
        </h3>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              formatter={(value: number, name: string) =>
                name === 'idea' ? `${value.toFixed(1)}` : `${value.toFixed(0)}%`
              }
              labelStyle={{ fontSize: 12, color: '#0f172a' }}
              contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: 8, border: '1px solid #e2e8f0' }}
            />
            <Bar dataKey="idea" name="Idea Score" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-3">
        {questions.map((q, idx) => (
          <div key={idx} className="p-3 rounded-lg border border-slate-200 bg-white">
            <p className="text-sm font-medium text-slate-900">{q.question}</p>
            <div className="flex flex-wrap gap-4 text-xs text-slate-600 mt-2">
              <span>Idea Score: <strong>{q.idea_score.toFixed(1)}</strong></span>
              <span>Konsensus: <strong>{(q.consensus * 100).toFixed(0)}%</strong></span>
              <span>Sentyment: <strong>{q.avg_sentiment.toFixed(2)}</strong></span>
              <span>Odpowiedzi: <strong>{q.response_count}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function InsightRecommendations({ insights }: { insights: FocusGroupInsights }) {
  const recommendations: string[] = [];
  const { metrics } = insights;

  if (metrics.consensus < 0.55) {
    recommendations.push('Niski konsensus – rozważ doprecyzowanie propozycji wartości i sprawdź, które persony wyrażają wątpliwości.');
  }
  if (metrics.sentiment_summary.negative_ratio > 0.25) {
    recommendations.push('Ponad 25% odpowiedzi jest negatywnych. Zbierz wątki krytyczne i przygotuj scenariusze zmian produktu.');
  }
  if ((metrics.engagement.completion_rate ?? 0) < 0.7) {
    recommendations.push('Completion rate poniżej 70%. Sprawdź, czy liczba pytań lub forma scenariusza nie przeciąża uczestników.');
  }
  if (insights.key_themes.length > 0) {
    const topTheme = insights.key_themes[0];
    recommendations.push(`Najczęściej pojawia się temat „${topTheme.keyword}”. Zaplanuj działania testujące ten motyw w następnych iteracjach.`);
  }

  if (recommendations.length === 0) {
    recommendations.push('Wyniki wyglądają stabilnie – możesz przejść do walidacji koncepcji na szerszej grupie person.');
  }

  return (
    <div className="floating-panel p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-green-600" />
        Następne kroki
      </h3>
      <ul className="list-disc list-inside text-sm text-slate-600 space-y-2">
        {recommendations.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function PersonaEngagement({
  personas,
  personaStats,
  onSelect,
}: {
  personas: Persona[];
  personaStats: FocusGroupInsights['persona_engagement'];
  onSelect: (personaId: string) => void;
}) {
  const personaMap = useMemo(() => new Map(personas.map((p) => [p.id, p])), [personas]);

  if (!personaStats || personaStats.length === 0) {
    return null;
  }

  const formatLabel = (personaId: string) => {
    const persona = personaMap.get(personaId);
    if (!persona) return `Persona ${personaId.slice(0, 6)}`;
    return `${persona.gender}, ${persona.age} • ${persona.location ?? 'brak lokalizacji'}`;
  };

  return (
    <div className="floating-panel p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Users className="w-5 h-5 text-primary-600" />
        Aktywność person
      </h3>
      <div className="space-y-3">
        {personaStats.map((persona) => (
          <button
            key={persona.persona_id}
            onClick={() => onSelect(persona.persona_id)}
            className="w-full text-left p-3 rounded-lg border border-slate-200 hover:border-primary-300 hover:bg-primary-50 transition"
          >
            <p className="text-sm font-medium text-slate-900">{formatLabel(persona.persona_id)}</p>
            <div className="flex flex-wrap gap-4 text-xs text-slate-600 mt-1">
              <span>Wkład: <strong>{persona.contribution_count}</strong></span>
              <span>Sentyment: <strong>{persona.avg_sentiment.toFixed(2)}</strong></span>
              <span>Śr. czas: <strong>{persona.average_response_time_ms.toFixed(0)} ms</strong></span>
              <span>Ostatnia aktywność: <strong>{persona.last_activity ? new Date(persona.last_activity).toLocaleString() : '—'}</strong></span>
            </div>
          </button>
        ))}
      </div>
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
                  {response.contradicts_events && Array.isArray(response.contradicts_events) && response.contradicts_events.length > 0 && (
                    <p className="text-xs text-red-500 mt-2">⚠️ Sprzeczności z pamięcią persony</p>
                  )}
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
            ) : (
              <div className="space-y-4">
                {insights && (
                  <>
                    <IdeaScoreGauge score={insights.idea_score} grade={insights.idea_grade} />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <MetricCard
                        label="Konsensus"
                        value={`${(insights.metrics.consensus * 100).toFixed(1)}%`}
                        helper="Im wyżej, tym mniejsze rozbieżności w opiniach."
                      />
                      <MetricCard
                        label="Średni sentyment"
                        value={insights.metrics.average_sentiment.toFixed(2)}
                        helper="Dodatnie wartości oznaczają pozytywny odbiór."
                      />
                      <MetricCard
                        label="Pozytywne odpowiedzi"
                        value={`${(insights.metrics.sentiment_summary.positive_ratio * 100).toFixed(1)}%`}
                        helper={`Negatywne: ${(insights.metrics.sentiment_summary.negative_ratio * 100).toFixed(1)}%`}
                      />
                      <MetricCard
                        label="Completion rate"
                        value={`${(insights.metrics.engagement.completion_rate * 100).toFixed(1)}%`}
                      />
                      <MetricCard
                        label="Śr. czas odpowiedzi"
                        value={insights.metrics.engagement.average_response_time_ms ? `${insights.metrics.engagement.average_response_time_ms.toFixed(0)} ms` : 'N/A'}
                      />
                      <MetricCard
                        label="Spójność person"
                        value={insights.metrics.engagement.consistency_score ? insights.metrics.engagement.consistency_score.toFixed(2) : 'N/A'}
                      />
                    </div>
                    <KeyThemes themes={insights.key_themes} />
                    <InsightRecommendations insights={insights} />
                    <QuestionBreakdown questions={insights.question_breakdown} />
                    <PersonaEngagement
                      personas={personas}
                      personaStats={insights.persona_engagement}
                      onSelect={handlePersonaSelect}
                    />
                  </>
                )}

                {!insights && (
                  <div className="floating-panel p-6 flex items-center gap-4">
                    <TrendingUp className="w-8 h-8 text-primary-400" />
                    <div>
                      <p className="text-sm font-semibold text-slate-900">Brak zapisanych insightów</p>
                      <p className="text-xs text-slate-600">Użyj przycisku „Odśwież analizę”, aby wyliczyć ocenę pomysłu na podstawie zebranych odpowiedzi.</p>
                    </div>
                  </div>
                )}

                <ResponseExplorer
                  personas={personas}
                  responses={responsesQuery.data}
                  onPersonaClick={handlePersonaSelect}
                />
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
