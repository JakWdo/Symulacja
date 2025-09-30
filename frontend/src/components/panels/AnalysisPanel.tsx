import { useQuery, useMutation } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { analysisApi, focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { BarChart3, TrendingUp, Users, Zap, AlertTriangle } from 'lucide-react';
import { getPolarizationLevel, generateColorScale, truncateText } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function PolarizationScore({ score }: { score: number }) {
  const { level, color } = getPolarizationLevel(score);

  return (
    <div className="floating-panel p-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center">
            <div className="text-3xl font-bold text-slate-900">
              {(score * 100).toFixed(0)}
            </div>
          </div>
          <div className="absolute inset-0 rounded-full border-4 border-primary-200 animate-pulse-slow" />
        </div>

        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            Polarization Score
          </h3>
          <div className={`text-sm font-medium ${color}`}>{level}</div>
          <p className="text-xs text-slate-600 mt-2">
            Measures opinion divergence across the audience
          </p>
        </div>
      </div>
    </div>
  );
}

function ClusterVisualization({ clusters }: { clusters: any[] }) {
  const colors = generateColorScale(clusters.length);

  const data = clusters.map((cluster, idx) => ({
    name: `Cluster ${cluster.cluster_id + 1}`,
    size: cluster.size,
    sentiment: cluster.avg_sentiment,
    fill: colors[idx],
  }));

  return (
    <div className="floating-panel p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Users className="w-5 h-5 text-primary-600" />
        Opinion Clusters
      </h3>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => `${entry.name} (${entry.size})`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="size"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 space-y-3">
        {clusters.map((cluster, idx) => (
          <div key={cluster.cluster_id} className="p-3 rounded-lg bg-slate-50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[idx] }}
                />
                <span className="font-medium text-slate-900">
                  Cluster {cluster.cluster_id + 1}
                </span>
              </div>
              <span className="text-sm text-slate-600">{cluster.size} personas</span>
            </div>

            <p className="text-xs text-slate-600 line-clamp-2">
              {truncateText(cluster.representative_response, 120)}
            </p>

            <div className="mt-2 flex items-center gap-2">
              <div className="text-xs text-slate-500">Sentiment:</div>
              <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all"
                  style={{
                    width: `${((cluster.avg_sentiment + 1) / 2) * 100}%`,
                    backgroundColor:
                      cluster.avg_sentiment > 0 ? '#10b981' : '#ef4444',
                  }}
                />
              </div>
              <div className="text-xs font-medium text-slate-700">
                {cluster.avg_sentiment > 0 ? '+' : ''}
                {cluster.avg_sentiment.toFixed(2)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuestionAnalysis({ questions }: { questions: any[] }) {
  const chartData = questions.map((q, idx) => ({
    question: `Q${idx + 1}`,
    polarization: q.polarization_score * 100,
    clusters: q.num_clusters,
  }));

  return (
    <div className="floating-panel p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-accent-600" />
        Question-by-Question Analysis
      </h3>

      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="question" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
              }}
            />
            <Bar dataKey="polarization" fill="#0ea5e9" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-3">
        {questions.slice(0, 3).map((q, idx) => (
          <div key={idx} className="p-3 rounded-lg bg-slate-50">
            <div className="flex items-start justify-between gap-3 mb-2">
              <p className="text-sm font-medium text-slate-900 flex-1">
                {truncateText(q.question, 80)}
              </p>
              <span
                className={`text-xs px-2 py-1 rounded-md font-medium ${
                  getPolarizationLevel(q.polarization_score).color
                }`}
              >
                {(q.polarization_score * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex gap-4 text-xs text-slate-600">
              <span>🎯 {q.num_clusters} clusters</span>
              <span>💬 {q.num_responses} responses</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalysisPanel() {
  const { activePanel, setActivePanel, selectedFocusGroup } = useAppStore();

  const analyzeMutation = useMutation({
    mutationFn: () => analysisApi.analyzePolarization(selectedFocusGroup!.id),
  });

  const { data: responses } = useQuery({
    queryKey: ['responses', selectedFocusGroup?.id],
    queryFn: async () => {
      if (!selectedFocusGroup) return null;
      return focusGroupsApi.getResponses(selectedFocusGroup.id);
    },
    enabled: !!selectedFocusGroup && selectedFocusGroup.status === 'completed',
  });

  const handleAnalyze = () => {
    if (selectedFocusGroup) {
      analyzeMutation.mutate();
    }
  };

  const analysis = analyzeMutation.data;

  return (
    <FloatingPanel
      isOpen={activePanel === 'analysis'}
      onClose={() => setActivePanel(null)}
      title="Analysis & Insights"
      position="right"
      size="xl"
    >
      <div className="p-4 space-y-4">
        {!selectedFocusGroup ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <BarChart3 className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600">Select a completed focus group to analyze</p>
          </div>
        ) : selectedFocusGroup.status !== 'completed' ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-12 h-12 text-yellow-400 mb-3" />
            <p className="text-slate-600 mb-2">Focus group not completed yet</p>
            <p className="text-sm text-slate-500">
              Wait for the simulation to finish before analyzing
            </p>
          </div>
        ) : !analysis ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <TrendingUp className="w-12 h-12 text-primary-400 mb-3" />
            <p className="text-slate-600 mb-4">Ready to analyze results</p>
            <button
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending}
              className="floating-button px-6 py-3 flex items-center gap-2"
            >
              {analyzeMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Analyze Polarization
                </>
              )}
            </button>
          </div>
        ) : (
          <>
            <PolarizationScore score={analysis.overall_polarization_score} />

            {analysis.questions[0]?.clusters && (
              <ClusterVisualization clusters={analysis.questions[0].clusters} />
            )}

            <QuestionAnalysis questions={analysis.questions} />

            {/* Response Preview */}
            {responses && (
              <div className="floating-panel p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">
                  Sample Responses
                </h3>
                <div className="space-y-3">
                  {Object.entries(responses.responses_by_question)
                    .slice(0, 2)
                    .map(([question, resps]: [string, any]) => (
                      <div key={question} className="p-3 rounded-lg bg-slate-50">
                        <p className="text-sm font-medium text-slate-900 mb-2">
                          {truncateText(question, 80)}
                        </p>
                        <div className="space-y-2">
                          {resps.slice(0, 2).map((resp: any, idx: number) => (
                            <div
                              key={idx}
                              className="text-xs text-slate-600 pl-3 border-l-2 border-primary-200"
                            >
                              {truncateText(resp.response, 100)}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </FloatingPanel>
  );
}