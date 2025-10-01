import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Lightbulb,
  AlertTriangle,
  Users,
  Target,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  Loader2,
  Zap,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/Button';
import { toast } from '@/components/ui/toastStore';
import axios from 'axios';

interface AISummary {
  executive_summary: string;
  key_insights: string[];
  surprising_findings: string[];
  segment_analysis: Record<string, string>;
  recommendations: string[];
  sentiment_narrative: string;
  full_analysis: string;
  metadata: {
    focus_group_id: string;
    focus_group_name: string;
    generated_at: string;
    model_used: string;
    total_responses: number;
    total_participants: number;
  };
}

interface AISummaryPanelProps {
  focusGroupId: string;
  focusGroupName: string;
}

export function AISummaryPanel({ focusGroupId, focusGroupName }: AISummaryPanelProps) {
  const [useProModel, setUseProModel] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['executive', 'insights'])
  );

  const {
    data: summary,
    isLoading,
    error,
    refetch,
  } = useQuery<AISummary>({
    queryKey: ['ai-summary', focusGroupId, useProModel],
    queryFn: async () => {
      const response = await axios.post(
        `/api/v1/focus-groups/${focusGroupId}/ai-summary`,
        {},
        {
          params: {
            use_pro_model: useProModel,
            include_recommendations: true,
          },
        }
      );
      return response.data;
    },
    enabled: false, // Manual trigger only
    staleTime: 1000 * 60 * 10, // Cache for 10 minutes
  });

  const handleGenerate = async () => {
    try {
      await refetch();
      toast.success(
        'AI Summary Generated',
        `Summary created using ${useProModel ? 'Gemini 2.5 Pro' : 'Gemini 2.0 Flash'}`
      );
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || err.message
        : 'Failed to generate summary';
      toast.error('Generation Failed', message);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const SectionHeader = ({
    id,
    icon: Icon,
    title,
    count,
  }: {
    id: string;
    icon: React.ElementType;
    title: string;
    count?: number;
  }) => {
    const isExpanded = expandedSections.has(id);

    return (
      <button
        onClick={() => toggleSection(id)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 rounded-lg transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          {count !== undefined && (
            <span className="text-xs px-2 py-1 rounded-full bg-primary-100 text-primary-700 font-medium">
              {count}
            </span>
          )}
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-5 h-5 text-slate-400" />
        </motion.div>
      </button>
    );
  };

  if (!summary && !isLoading) {
    return (
      <div className="floating-panel p-8">
        <div className="text-center max-w-2xl mx-auto">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-primary-600" />
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-3">AI-Powered Discussion Summary</h2>
          <p className="text-slate-600 mb-6 leading-relaxed">
            Generate an intelligent summary of your focus group discussion using advanced AI.
            Get executive summaries, key insights, surprising findings, and strategic recommendations
            in seconds.
          </p>

          <div className="bg-slate-50 rounded-xl p-4 mb-6 border border-slate-200">
            <div className="flex items-center justify-between">
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-900">Model Selection</p>
                <p className="text-xs text-slate-600 mt-1">
                  {useProModel
                    ? 'Gemini 2.5 Pro - Highest quality, slower (~30s)'
                    : 'Gemini 2.0 Flash Exp - Fast & good quality (~10s)'}
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={useProModel}
                  onChange={(e) => setUseProModel(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                <span className="ml-3 text-sm font-medium text-slate-700">Pro Mode</span>
              </label>
            </div>
          </div>

          <Button onClick={handleGenerate} disabled={isLoading} className="gap-2" size="lg">
            <Sparkles className="w-5 h-5" />
            Generate AI Summary
          </Button>

          <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
            <div className="flex flex-col items-center gap-2 p-3 bg-slate-50 rounded-lg">
              <Lightbulb className="w-5 h-5 text-primary-600" />
              <span className="font-medium text-slate-700">Key Insights</span>
            </div>
            <div className="flex flex-col items-center gap-2 p-3 bg-slate-50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-accent-600" />
              <span className="font-medium text-slate-700">Surprising Finds</span>
            </div>
            <div className="flex flex-col items-center gap-2 p-3 bg-slate-50 rounded-lg">
              <Target className="w-5 h-5 text-green-600" />
              <span className="font-medium text-slate-700">Recommendations</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="floating-panel p-12">
        <div className="text-center max-w-md mx-auto">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <Loader2 className="w-20 h-20 text-primary-500 animate-spin" />
            <Sparkles className="w-8 h-8 text-accent-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Generating AI Summary...</h3>
          <p className="text-slate-600 mb-4">
            {useProModel
              ? 'Using Gemini 2.5 Pro for highest quality analysis'
              : 'Using Gemini 2.0 Flash for fast analysis'}
          </p>
          <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-primary-500 to-accent-500"
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: useProModel ? 30 : 10, ease: 'linear' }}
            />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="floating-panel p-8">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Failed to Generate Summary</h3>
          <p className="text-slate-600 mb-4">
            {axios.isAxiosError(error) ? error.response?.data?.detail || error.message : 'Unknown error'}
          </p>
          <Button onClick={handleGenerate} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with regenerate option */}
      <div className="floating-panel p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100">
              <Sparkles className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">AI Discussion Summary</h2>
              <p className="text-sm text-slate-600">
                Generated with {summary.metadata.model_used} •{' '}
                {new Date(summary.metadata.generated_at).toLocaleString()}
              </p>
            </div>
          </div>
          <Button onClick={handleGenerate} variant="outline" size="sm" className="gap-2">
            <Zap className="w-4 h-4" />
            Regenerate
          </Button>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader id="executive" icon={Sparkles} title="Executive Summary" />
        <AnimatePresence>
          {expandedSections.has('executive') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{summary.executive_summary}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Key Insights */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader
          id="insights"
          icon={Lightbulb}
          title="Key Insights"
          count={summary.key_insights.length}
        />
        <AnimatePresence>
          {expandedSections.has('insights') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="space-y-3">
                {summary.key_insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className="flex gap-3 p-4 bg-primary-50 border border-primary-200 rounded-lg"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
                      {idx + 1}
                    </div>
                    <p className="text-sm text-slate-700 leading-relaxed flex-1">{insight}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Surprising Findings */}
      {summary.surprising_findings.length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="surprising"
            icon={AlertTriangle}
            title="Surprising Findings"
            count={summary.surprising_findings.length}
          />
          <AnimatePresence>
            {expandedSections.has('surprising') && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6"
              >
                <div className="space-y-3">
                  {summary.surprising_findings.map((finding, idx) => (
                    <div
                      key={idx}
                      className="flex gap-3 p-4 bg-accent-50 border border-accent-200 rounded-lg"
                    >
                      <AlertTriangle className="w-5 h-5 text-accent-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-slate-700 leading-relaxed flex-1">{finding}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Segment Analysis */}
      {Object.keys(summary.segment_analysis).length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="segments"
            icon={Users}
            title="Segment Analysis"
            count={Object.keys(summary.segment_analysis).length}
          />
          <AnimatePresence>
            {expandedSections.has('segments') && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6"
              >
                <div className="space-y-3">
                  {Object.entries(summary.segment_analysis).map(([segment, analysis]) => (
                    <div key={segment} className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                      <h4 className="text-sm font-semibold text-slate-900 mb-2">{segment}</h4>
                      <p className="text-sm text-slate-700 leading-relaxed">{analysis}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Recommendations */}
      {summary.recommendations.length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="recommendations"
            icon={Target}
            title="Strategic Recommendations"
            count={summary.recommendations.length}
          />
          <AnimatePresence>
            {expandedSections.has('recommendations') && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6"
              >
                <div className="space-y-3">
                  {summary.recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="flex gap-3 p-4 bg-green-50 border border-green-200 rounded-lg"
                    >
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-600 text-white flex items-center justify-center text-sm font-bold">
                        {idx + 1}
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed flex-1">{rec}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Sentiment Narrative */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader id="sentiment" icon={TrendingUp} title="Sentiment Narrative" />
        <AnimatePresence>
          {expandedSections.has('sentiment') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{summary.sentiment_narrative}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
