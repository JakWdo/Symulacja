import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Lightbulb,
  AlertTriangle,
  Users,
  Target,
  TrendingUp,
  ChevronDown,
  Zap,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toastStore';
import axios from 'axios';
import { analysisApi } from '@/lib/api';
import type { AISummary } from '@/types';
import { Logo } from '@/components/ui/logo';
import { useAISummaryStore } from '@/store/aiSummaryStore';
import { useDateFormat } from '@/hooks/useDateFormat';

import { normalizeMarkdown } from '@/lib/markdown';

interface AISummaryPanelProps {
  focusGroupId: string;
  focusGroupName: string;
  hideGenerateButton?: boolean;
  onGenerateStart?: () => void;
  onGenerateComplete?: () => void;
  triggerGenerate?: boolean;
  useProModel?: boolean;
}

const MAX_POLL_ATTEMPTS = 60; // 60 * 5 seconds = 5 minutes max
const POLL_INTERVAL_MS = 5000;

export function AISummaryPanel({
  focusGroupId,
  focusGroupName,
  hideGenerateButton = false,
  onGenerateStart,
  onGenerateComplete,
  triggerGenerate = false,
  useProModel = true,
}: AISummaryPanelProps) {
  const { t } = useTranslation('focusGroups');
  const { formatDateTime } = useDateFormat();

  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['executive', 'insights'])
  );
  const sessionTitle = focusGroupName || t('analysis.aiSummary.defaultSessionTitle');
  const [hasTriggered, setHasTriggered] = useState(false);
  const [pollCount, setPollCount] = useState(0);
  const queryClient = useQueryClient();
  const persistentGenerating = useAISummaryStore(
    (state) => state.generatingStatuses[focusGroupId] ?? false
  );
  const setPersistentGenerating = useAISummaryStore(
    (state) => state.setGeneratingStatus
  );

  // Check if responses exist before allowing generation
  const { data: responsesData } = useQuery({
    queryKey: ['focus-group-responses', focusGroupId],
    queryFn: async () => {
      try {
        return await analysisApi.getFocusGroupResponses(focusGroupId);
      } catch (err) {
        return { total_responses: 0, questions: [] };
      }
    },
    staleTime: 1000 * 30, // Cache for 30 seconds
  });

  const hasResponses = (responsesData?.total_responses ?? 0) > 0;

  const {
    data: summary,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<AISummary | null>({
    queryKey: ['ai-summary', focusGroupId],
    queryFn: async () => {
      try {
        // Increment poll count on each fetch attempt when polling
        if (persistentGenerating) {
          setPollCount((prev) => prev + 1);
        }
        return await analysisApi.getAISummary(focusGroupId);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          // 404 is expected while summary is being generated
          return null;
        }
        throw err;
      }
    },
    staleTime: 1000 * 60 * 10, // Cache for 10 minutes
    refetchInterval: persistentGenerating && pollCount < MAX_POLL_ATTEMPTS ? POLL_INTERVAL_MS : false,
    refetchIntervalInBackground: persistentGenerating && pollCount < MAX_POLL_ATTEMPTS,
  });

  const generateMutation = useMutation({
    mutationFn: () =>
      analysisApi.generateAISummary(
        focusGroupId,
        useProModel,
        true
      ),
  });

  const isGenerating = generateMutation.isPending;
  const showLoading =
    (isLoading || isFetching || persistentGenerating) && !summary;

  const handleGenerate = useCallback(async () => {
    try {
      onGenerateStart?.();
      setPollCount(0); // Reset poll counter for new generation
      setPersistentGenerating(focusGroupId, true);
      const result = await generateMutation.mutateAsync();
      await queryClient.invalidateQueries({ queryKey: ['ai-summary', focusGroupId] });
      toast.success(
        t('analysis.aiSummary.success'),
        t('analysis.aiSummary.successModel', { model: result.metadata.model_used })
      );
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || err.message
        : t('analysis.aiSummary.errorGeneric');
      toast.error(t('analysis.aiSummary.error'), message);
      setPersistentGenerating(focusGroupId, false);
      setPollCount(0); // Reset poll counter on error
    } finally {
      onGenerateComplete?.();
    }
  }, [
    focusGroupId,
    generateMutation,
    onGenerateComplete,
    onGenerateStart,
    queryClient,
    setPersistentGenerating,
    t,
  ]);

  // Trigger generation when triggerGenerate prop changes
  useEffect(() => {
    if (triggerGenerate && !hasTriggered && !summary && !showLoading && !isGenerating) {
      setHasTriggered(true);
      handleGenerate();
    }
  }, [triggerGenerate, hasTriggered, summary, showLoading, isGenerating, handleGenerate]);

  // Stop polling when summary is successfully fetched
  useEffect(() => {
    if (summary) {
      setPersistentGenerating(focusGroupId, false);
      setPollCount(0); // Reset poll counter on success
    }
  }, [summary, focusGroupId, setPersistentGenerating]);

  // Stop polling on error
  useEffect(() => {
    if (error) {
      setPersistentGenerating(focusGroupId, false);
      setPollCount(0); // Reset poll counter on error
    }
  }, [error, focusGroupId, setPersistentGenerating]);

  // Handle timeout: stop polling after MAX_POLL_ATTEMPTS
  useEffect(() => {
    if (persistentGenerating && pollCount >= MAX_POLL_ATTEMPTS) {
      setPersistentGenerating(focusGroupId, false);
      setPollCount(0);
      toast.error(
        t('analysis.aiSummary.timeout'),
        t('analysis.aiSummary.timeoutDescription')
      );
    }
  }, [persistentGenerating, pollCount, focusGroupId, setPersistentGenerating, t]);

  // Manual refetch for older polling behavior compatibility
  useEffect(() => {
    if (persistentGenerating && !isFetching && !isLoading && !summary && pollCount < MAX_POLL_ATTEMPTS) {
      refetch();
    }
  }, [persistentGenerating, isFetching, isLoading, summary, refetch, pollCount]);

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

  if (!summary && !showLoading) {
    return (
      <div className="floating-panel p-8">
        <div className="text-center max-w-2xl mx-auto">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mx-auto mb-4">
            <Logo className="w-10 h-10" transparent />
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            {t('analysis.aiSummary.emptyTitle', { sessionTitle })}
          </h2>
          <p className="text-slate-600 mb-6 leading-relaxed">
            {t('analysis.aiSummary.emptyDescription')}
          </p>

          {!hideGenerateButton && (
            <>
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || persistentGenerating || !hasResponses}
                className="gap-2"
                size="lg"
              >
                <Sparkles className="w-5 h-5" />
                {hasResponses
                  ? t('analysis.aiSummary.generateButton')
                  : t('analysis.aiSummary.waitingForResponses')}
              </Button>
              {!hasResponses && (
                <p className="text-sm text-slate-500 mt-2">
                  {t('analysis.aiSummary.completeDiscussionFirst')}
                </p>
              )}
          </>
          )}

          <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
            <div className="flex flex-col items-center gap-2 p-3 bg-slate-50 rounded-lg">
              <Lightbulb className="w-5 h-5 text-primary-600" />
              <span className="font-medium text-slate-700">{t('analysis.keyInsights.title')}</span>
            </div>
            <div className="flex flex-col items-center gap-2 p-3 bg-slate-50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-accent-600" />
              <span className="font-medium text-slate-700">{t('analysis.surprisingFindings.title')}</span>
            </div>
            <div className="flex flex-col items-center gap-2 p-3 bg-slate-50 rounded-lg">
              <Target className="w-5 h-5 text-green-600" />
              <span className="font-medium text-slate-700">{t('analysis.recommendations.title')}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (showLoading) {
    return (
      <div className="floating-panel p-12">
        <div className="text-center max-w-md mx-auto">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <Logo className="w-20 h-20" spinning />
            <Sparkles className="w-8 h-8 text-accent-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">
            {t('analysis.aiSummary.generating')}
          </h3>
          <p className="text-slate-600 mb-4">
            {useProModel
              ? t('analysis.aiSummary.usingProModel')
              : t('analysis.aiSummary.usingFlashModel')}
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
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            {t('analysis.aiSummary.errorTitle')}
          </h3>
          <p className="text-slate-600 mb-4">
            {axios.isAxiosError(error) ? error.response?.data?.detail || error.message : t('analysis.aiSummary.errorUnknown')}
          </p>
          <Button onClick={handleGenerate} variant="outline">
            {t('analysis.aiSummary.retryButton')}
          </Button>
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Header with regenerate option */}
      <div className="floating-panel p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100">
              <Logo className="w-6 h-6" transparent />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                {t('analysis.aiSummary.discussionSummary', { sessionTitle })}
              </h2>
              <p className="text-sm text-slate-600">
                {t('analysis.aiSummary.generatedBy', {
                  model: summary.metadata.model_used,
                  date: formatDateTime(summary.metadata.generated_at),
                })}
              </p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                <span className="px-2 py-1 bg-slate-100 rounded-full">
                  {t('analysis.aiSummary.responsesLabel', { count: summary.metadata.total_responses })}
                </span>
                <span className="px-2 py-1 bg-slate-100 rounded-full">
                  {t('analysis.aiSummary.participantsLabel', { count: summary.metadata.total_participants })}
                </span>
                {summary.metadata.questions_asked !== undefined && (
                  <span className="px-2 py-1 bg-slate-100 rounded-full">
                    {t('analysis.aiSummary.questionsLabel', { count: summary.metadata.questions_asked })}
                  </span>
                )}
              </div>
            </div>
          </div>
          <Button
            onClick={handleGenerate}
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={isGenerating || persistentGenerating}
          >
            <Zap className="w-4 h-4" />
            {t('analysis.aiSummary.regenerateButton')}
          </Button>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader id="executive" icon={Sparkles} title={t('analysis.executiveSummary.title')} />
        <AnimatePresence>
          {expandedSections.has('executive') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(summary.executive_summary)}</ReactMarkdown>
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
          title={t('analysis.keyInsights.title')}
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
                    <div className="text-sm text-slate-700 leading-relaxed flex-1 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(insight)}</ReactMarkdown>
                    </div>
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
            title={t('analysis.surprisingFindings.title')}
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
                    <div className="text-sm text-slate-700 leading-relaxed flex-1 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(finding)}</ReactMarkdown>
                    </div>
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
            title={t('analysis.segments.title')}
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
                      <div className="text-sm text-slate-700 leading-relaxed prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(analysis)}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Strategic Recommendations */}
      {summary.recommendations.length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="recommendations"
            icon={Target}
            title={t('analysis.recommendations.title')}
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
                    <div className="text-sm text-slate-700 leading-relaxed flex-1 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(rec)}</ReactMarkdown>
                    </div>
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
        <SectionHeader id="sentiment" icon={TrendingUp} title={t('analysis.aiSummary.sentimentNarrative')} />
        <AnimatePresence>
          {expandedSections.has('sentiment') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(summary.sentiment_narrative)}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
