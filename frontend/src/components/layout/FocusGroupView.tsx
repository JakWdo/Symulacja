import { useState, useEffect, useRef, useMemo, Suspense, lazy } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Settings as SettingsIcon, MessageSquare, BarChart3, AlertCircle } from 'lucide-react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { focusGroupsApi, personasApi, analysisApi } from '@/lib/api';
import { estimateFocusGroupDuration } from '@/lib/focusGroupGeneration';
import { Logo } from '@/components/ui/logo';
import { toast } from '@/components/ui/toastStore';
import type { FocusGroup } from '@/types';
import type { AISummaryResponse } from '@/types/ai-summary';
import { useAppStore } from '@/store/appStore';
import { FocusGroupHeader } from '@/components/focus-group/FocusGroupHeader';
import { FocusGroupSetupTab } from '@/components/focus-group/FocusGroupSetupTab';
import { FocusGroupDiscussionTab } from '@/components/focus-group/FocusGroupDiscussionTab';

// Lazy load Analysis View
const FocusGroupAnalysisView = lazy(() =>
  import('@/components/focus-group/analysis/FocusGroupAnalysisView').then((module) => ({
    default: module.FocusGroupAnalysisView,
  }))
);

interface FocusGroupViewProps {
  focusGroup: FocusGroup;
  onBack: () => void;
}

interface ChatMessage {
  id: number;
  persona: string;
  message: string;
  timestamp: string;
}

const mockChatMessages: ChatMessage[] = [
  { id: 1, persona: 'Sarah Johnson', message: 'I really appreciate tools that integrate well with my existing workflow. Time-saving is key for me.', timestamp: '14:32' },
  { id: 2, persona: 'Michael Chen', message: 'For me, the technical aspects matter most. I need flexibility and customization options.', timestamp: '14:33' },
  { id: 3, persona: 'Emily Rodriguez', message: 'Cost is definitely a factor for small businesses like mine. But reliability is even more important.', timestamp: '14:34' },
  { id: 4, persona: 'David Kim', message: 'The user interface needs to be intuitive. I don\'t want to spend hours learning a new tool.', timestamp: '14:35' },
];

const arraysEqual = (a: string[], b: string[]) => {
  if (a.length !== b.length) return false;
  const sortedA = [...a].sort();
  const sortedB = [...b].sort();
  return sortedA.every((value, index) => value === sortedB[index]);
};

const sanitizeQuestions = (list: string[]) =>
  list.map((question) => question.trim()).filter((question) => question.length > 0);

export function FocusGroupView({ focusGroup: initialFocusGroup, onBack }: FocusGroupViewProps) {
  const { t } = useTranslation('focusGroups');
  const { selectedProject, pendingSummaries, setSummaryPending } = useAppStore((state) => ({
    selectedProject: state.selectedProject,
    pendingSummaries: state.pendingSummaries,
    setSummaryPending: state.setSummaryPending,
  }));
  const [isRunning, setIsRunning] = useState(false);
  const [discussionProgress, setDiscussionProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('setup');
  const [aiSummaryGenerated, setAiSummaryGenerated] = useState(false);
  const [generatingAiSummary, setGeneratingAiSummary] = useState(false);
  const [newQuestion, setNewQuestion] = useState('');
  const [questions, setQuestions] = useState<string[]>(initialFocusGroup.questions || []);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>(initialFocusGroup.persona_ids || []);
  const [insights, setInsights] = useState<AISummaryResponse | null>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [progressMeta, setProgressMeta] = useState<{
    start: number;
    duration: number;
    targetResponses: number;
  } | null>(null);

  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (payload: {
      name: string;
      description: string | null;
      project_context: string | null;
      persona_ids: string[];
      questions: string[];
      mode: 'normal' | 'adversarial';
    }) => focusGroupsApi.update(initialFocusGroup.id, payload),
    onSuccess: (updated) => {
      setQuestions(updated.questions || []);
      setSelectedPersonaIds(updated.persona_ids || []);
      queryClient.setQueryData(['focus-group', initialFocusGroup.id], updated);
      queryClient.invalidateQueries({ queryKey: ['focus-groups', updated.project_id] });
      queryClient.invalidateQueries({ queryKey: ['focus-group', initialFocusGroup.id] });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(t('view.toast.saveError'), message);
    },
  });

  // Fetch focus group status in real-time
  const { data: focusGroup = initialFocusGroup, isFetching: focusGroupFetching } = useQuery({
    queryKey: ['focus-group', initialFocusGroup.id],
    queryFn: () => focusGroupsApi.get(initialFocusGroup.id),
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: (data) => {
      // Poll every 2s when running, stop when completed
      return data?.status === 'running' ? 2000 : false;
    },
    refetchIntervalInBackground: true,
    keepPreviousData: true,
    initialData: initialFocusGroup,
  });

  // Fetch personas for this project
  const { data: personas = [] } = useQuery({
    queryKey: ['personas', focusGroup.project_id],
    queryFn: () => personasApi.getByProject(focusGroup.project_id),
    enabled: !!focusGroup.project_id,
  });

  useEffect(() => {
    if (updateMutation.isPending) {
      return;
    }
    const nextQuestions = focusGroup.questions || [];
    setQuestions((prev) => (arraysEqual(prev, nextQuestions) ? prev : nextQuestions));
    const nextPersonaIds = focusGroup.persona_ids || [];
    setSelectedPersonaIds((prev) => (arraysEqual(prev, nextPersonaIds) ? prev : nextPersonaIds));
  }, [focusGroup.questions, focusGroup.persona_ids, updateMutation.isPending]);

  const {
    data: responses,
    isLoading: responsesLoading,
    isFetching: responsesFetching,
  } = useQuery<FocusGroupResponses>({
    queryKey: ['focus-group-responses', focusGroup.id],
    queryFn: () => focusGroupsApi.getResponses(focusGroup.id),
    enabled: focusGroup.status !== 'pending',
    keepPreviousData: true,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: focusGroup.status === 'completed' ? false : 3000, // Keep polling while running
    refetchIntervalInBackground: true,
  });

  const { data: cachedSummary, isLoading: cachedSummaryLoading } = useQuery<AISummaryResponse | null>({
    queryKey: ['focus-group-ai-summary', focusGroup.id],
    queryFn: async () => {
      try {
        return await analysisApi.getAISummary(focusGroup.id);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          return null;
        }
        throw err;
      }
    },
    enabled: focusGroup.status === 'completed',
    staleTime: 1000 * 60 * 10,
  });

  const summaryPending = pendingSummaries[focusGroup.id] ?? false;

  useEffect(() => {
    if (cachedSummary) {
      setInsights(cachedSummary);
      setAiSummaryGenerated(true);
      if (summaryPending) {
        setSummaryPending(focusGroup.id, false);
      }
    } else if (!generatingAiSummary && !summaryPending && focusGroup.status === 'completed') {
      setInsights(null);
      setAiSummaryGenerated(false);
    }
  }, [cachedSummary, generatingAiSummary, summaryPending, focusGroup.status, focusGroup.id, setSummaryPending]);

  const { data: project } = useQuery({
    queryKey: ['project', focusGroup.project_id],
    queryFn: () => projectsApi.get(focusGroup.project_id),
    enabled: !!focusGroup.project_id,
  });

  const projectName = project?.name || selectedProject?.name || 'Unknown project';
  const contextLabel = `${focusGroup.name} · ${projectName}`;
  const summaryProcessing = summaryPending || generatingAiSummary;
  const insightsLoading = !insights && (cachedSummaryLoading || summaryProcessing);
  const responsesPending = responsesLoading || responsesFetching;

  const totalExpectedResponses = useMemo(() => {
    const totalQuestions = focusGroup.questions?.length ?? 0;
    const totalParticipants = focusGroup.persona_ids?.length ?? 0;
    return totalQuestions * totalParticipants;
  }, [focusGroup.questions, focusGroup.persona_ids]);

  const responsesCount = useMemo(() => {
    if (!responses?.questions?.length) {
      return 0;
    }
    return responses.questions.reduce((sum, question) => sum + question.responses.length, 0);
  }, [responses]);

  const responsesProgress = useMemo(() => {
    if (!totalExpectedResponses) {
      return 0;
    }
    const ratio = (responsesCount / totalExpectedResponses) * 100;
    return Math.min(Math.round(ratio), 95);
  }, [responsesCount, totalExpectedResponses]);

  useEffect(() => {
    if (!responsesProgress) {
      return;
    }
    setDiscussionProgress((prev) => (responsesProgress > prev ? responsesProgress : prev));
  }, [responsesProgress]);

  useEffect(() => {
    if (focusGroup.status === 'running') {
      setIsRunning(true);
      return;
    }

    if (focusGroup.status === 'completed') {
      setIsRunning(false);
      setDiscussionProgress(100);
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }
      return;
    }

    if (focusGroup.status === 'failed') {
      setIsRunning(false);
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }
      return;
    }

    if (focusGroup.status === 'pending') {
      if (!isRunning && discussionProgress !== 0) {
        setDiscussionProgress(0);
        setChatMessages([]);
      }
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }
    }
  }, [focusGroup.status, isRunning, discussionProgress]);

  useEffect(() => {
    return () => {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }
    };
  }, []);

  // Nowy fake progress bazowany na progressMeta (analogicznie do Personas.tsx)
  useEffect(() => {
    if (!progressMeta || !isRunning) {
      return;
    }

    // Jeśli mamy realne odpowiedzi z API, używamy responsesProgress
    if (responsesProgress > 0 && responsesCount > 0) {
      const ratio = Math.min(responsesCount / progressMeta.targetResponses, 0.99);
      setDiscussionProgress((prev) => Math.max(prev, Math.max(5, ratio * 100)));
      return;
    }

    // Fake progress based on time elapsed
    const interval = setInterval(() => {
      setDiscussionProgress((prev) => {
        const elapsed = Date.now() - progressMeta.start;
        const ratio = Math.min(elapsed / progressMeta.duration, 0.97);
        const target = 5 + ratio * 90; // 5% → 95%
        return prev + (target - prev) * 0.35; // Smooth transition
      });
    }, 200);

    return () => clearInterval(interval);
  }, [progressMeta, isRunning, responsesProgress, responsesCount]);

  // Cleanup progressMeta po zakończeniu
  useEffect(() => {
    if (focusGroup.status === 'completed' && progressMeta) {
      setDiscussionProgress(100);
      setTimeout(() => {
        setProgressMeta(null);
        setDiscussionProgress(0);
      }, 2000); // Pokaż 100% przez 2s
    }
  }, [focusGroup.status, progressMeta]);

  const runMutation = useMutation({
    mutationFn: () => focusGroupsApi.run(focusGroup.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups'] });
      queryClient.invalidateQueries({ queryKey: ['focus-group', focusGroup.id] });
      queryClient.invalidateQueries({ queryKey: ['focus-group-responses', focusGroup.id] });

      setIsRunning(true);
      setDiscussionProgress(0);
      setChatMessages([]);

      // Simulate progress with chat messages
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }

      const intervalId = setInterval(() => {
        setDiscussionProgress((prev) => {
          if (prev >= 95) {
            clearInterval(intervalId);
            progressTimerRef.current = null;
            return prev;
          }

          const next = Math.min(prev + 5, 95);

          setChatMessages((prevMessages) => {
            if (prevMessages.length === 0 && next >= 15) {
              return [mockChatMessages[0]];
            }
            if (prevMessages.length === 1 && next >= 35) {
              return [...prevMessages, mockChatMessages[1]];
            }
            if (prevMessages.length === 2 && next >= 55) {
              return [...prevMessages, mockChatMessages[2]];
            }
            if (prevMessages.length === 3 && next >= 75) {
              return [...prevMessages, mockChatMessages[3]];
            }
            return prevMessages;
          });

          return next;
        });
      }, 500);

      progressTimerRef.current = intervalId;
      toast.success(t('view.toast.launchSuccess'), contextLabel);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(t('view.toast.launchError'), `${contextLabel} • ${message}`);
    },
  });

  const handleRunDiscussion = () => {
    // Oblicz szacowany czas generacji
    const duration = estimateFocusGroupDuration({
      numPersonas: focusGroup.persona_ids?.length || 20,
      numQuestions: focusGroup.questions?.length || 4,
      useAI: true,
    });

    // Ustaw meta przed rozpoczęciem
    setProgressMeta({
      start: Date.now(),
      duration,
      targetResponses: (focusGroup.persona_ids?.length || 0) * (focusGroup.questions?.length || 0),
    });

    runMutation.mutate();
  };

  const handlePersistQuestions = async (
    nextQuestions: string[],
    previousQuestions: string[],
  ) => {
    if (focusGroup.status !== 'pending') {
      return;
    }
    if (updateMutation.isPending) {
      return;
    }
    const sanitized = sanitizeQuestions(nextQuestions);
    try {
      await updateMutation.mutateAsync(buildUpdatePayload(selectedPersonaIds, sanitized));
    } catch {
      setQuestions(previousQuestions);
    }
  };

  const addQuestion = async () => {
    const trimmed = newQuestion.trim();
    if (!trimmed || focusGroup.status !== 'pending') {
      return;
    }
    if (updateMutation.isPending) {
      return;
    }
    const previous = questions;
    const next = [...questions, trimmed];
    setQuestions(next);
    setNewQuestion('');
    await handlePersistQuestions(next, previous);
  };

  const removeQuestion = async (index: number) => {
    if (focusGroup.status !== 'pending') {
      return;
    }
    if (updateMutation.isPending) {
      return;
    }
    const previous = questions;
    const next = questions.filter((_, i) => i !== index);
    setQuestions(next);
    await handlePersistQuestions(next, previous);
  };

  const handlePersonaToggle = (personaId: string, nextChecked: boolean) => {
    if (focusGroup.status !== 'pending') {
      return;
    }
    const wasSelected = selectedPersonaIds.includes(personaId);
    if ((wasSelected && nextChecked) || (!wasSelected && !nextChecked)) {
      return;
    }

    const next = nextChecked
      ? [...selectedPersonaIds, personaId]
      : selectedPersonaIds.filter((id) => id !== personaId);

    setSelectedPersonaIds(next);

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout to save after 500ms
    saveTimeoutRef.current = setTimeout(async () => {
      try {
        const sanitizedQuestions = sanitizeQuestions(questions);
        await updateMutation.mutateAsync(buildUpdatePayload(next, sanitizedQuestions));
      } catch (error) {
        console.error('Failed to save persona selection:', error);
        // Optionally revert on error
      }
    }, 500);
  };

  const handleGenerateAiSummary = async () => {
    setGeneratingAiSummary(true);
    setSummaryPending(focusGroup.id, true);
    setAiSummaryGenerated(false);

    try {
      const generatedInsights = await analysisApi.generateAISummary(focusGroup.id, true, true);
      setInsights(generatedInsights);
      setGeneratingAiSummary(false);
      setAiSummaryGenerated(true);
      setSummaryPending(focusGroup.id, false);
      setActiveTab('results');
      await queryClient.invalidateQueries({ queryKey: ['focus-group-ai-summary', focusGroup.id] });
      toast.success(t('view.toast.summarySuccess'), contextLabel);
    } catch (error) {
      console.error('Failed to generate AI summary:', error);
      setGeneratingAiSummary(false);
      setSummaryPending(focusGroup.id, false);
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(t('view.toast.summaryError'), `${contextLabel} • ${message}`);
    }
  };

  const discussionComplete = focusGroup.status === 'completed';
  const canModifyConfig = focusGroup.status === 'pending';
  const buildUpdatePayload = (personaIds: string[], questionList: string[]) => ({
    name: focusGroup.name,
    description: focusGroup.description ?? null,
    project_context: focusGroup.project_context ?? null,
    persona_ids: personaIds,
    questions: questionList,
    mode: focusGroup.mode,
  });

  return (
    <ErrorBoundary>
      <div className="w-full h-full overflow-y-auto">
        <div className="max-w-7xl mx-auto space-y-6 p-6">
        {/* Header */}
        <FocusGroupHeader
          name={focusGroup.name}
          status={focusGroup.status}
          questionsCount={focusGroup.questions.length}
          participantsCount={focusGroup.persona_ids.length}
          onBack={onBack}
        />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-muted border border-border shadow-sm">
          <TabsTrigger value="setup" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <SettingsIcon className="w-4 h-4 mr-2" />
            {t('view.tabs.setup')}
          </TabsTrigger>
          <TabsTrigger value="discussion" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <MessageSquare className="w-4 h-4 mr-2" />
            {t('view.tabs.discussion')}
          </TabsTrigger>
          <TabsTrigger value="results" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            {t('view.tabs.results')}
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="setup" className="space-y-6">
          <FocusGroupSetupTab
            questions={questions}
            selectedPersonaIds={selectedPersonaIds}
            personas={personas}
            canModifyConfig={canModifyConfig}
            isSaving={updateMutation.isPending}
            newQuestion={newQuestion}
            onNewQuestionChange={setNewQuestion}
            onAddQuestion={addQuestion}
            onRemoveQuestion={removeQuestion}
            onPersonaToggle={handlePersonaToggle}
          />
        </TabsContent>

        {/* Discussion Tab */}
        <TabsContent value="discussion" className="space-y-6">
          <FocusGroupDiscussionTab
            isRunning={isRunning}
            discussionComplete={discussionComplete}
            status={focusGroup.status}
            personaCount={focusGroup.persona_ids.length}
            questionsCount={focusGroup.questions.length}
            discussionProgress={discussionProgress}
            chatMessages={chatMessages}
            progressMeta={progressMeta}
            responsesCount={responsesCount}
            aiSummaryGenerated={aiSummaryGenerated}
            summaryProcessing={summaryProcessing}
            onRunDiscussion={handleRunDiscussion}
            onGenerateAiSummary={handleGenerateAiSummary}
            onViewResults={() => setActiveTab('results')}
            isRunPending={runMutation.isPending}
          />
        </TabsContent>

        {/* Results Tab - NEW: Using FocusGroupAnalysisView */}
        <TabsContent value="results" className="space-y-6">
          {focusGroup.status === 'pending' && !isRunning && (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">{t('view.results.pendingTitle')}</h3>
                <p className="text-muted-foreground">
                  {t('view.results.pendingDescription')}
                </p>
              </CardContent>
            </Card>
          )}

          {(focusGroup.status === 'running' || isRunning) && (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="py-12 flex flex-col items-center gap-4 text-center">
                <Logo className="w-8 h-8" spinning />
                <div className="space-y-1">
                  <h3 className="text-lg font-medium text-card-foreground">{t('view.results.runningTitle')}</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    {t('view.results.runningDescription')}
                  </p>
                </div>
                <div className="w-full max-w-sm space-y-2">
                  <Progress value={discussionProgress} className="w-full" />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{t('view.results.progressCompleted', { percent: discussionProgress })}</span>
                    {totalExpectedResponses > 0 ? (
                      <span>
                        {t('view.results.responsesCount', { current: responsesCount, total: totalExpectedResponses })}
                      </span>
                    ) : null}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {focusGroup.status === 'failed' && (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="py-12 text-center space-y-3">
                <AlertCircle className="w-12 h-12 text-destructive mx-auto" />
                <h3 className="text-lg font-medium text-destructive">{t('view.results.failedTitle')}</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  {t('view.results.failedDescription')}
                </p>
              </CardContent>
            </Card>
          )}

          {discussionComplete && (
            <Suspense
              fallback={
                <Card className="bg-card border border-border shadow-sm">
                  <CardContent className="py-12 flex flex-col items-center justify-center">
                    <Logo className="w-8 h-8 mb-4" spinning />
                    <p className="text-muted-foreground">{t('view.results.loadingAnalysis')}</p>
                  </CardContent>
                </Card>
              }
            >
              <FocusGroupAnalysisView
                focusGroupId={focusGroup.id}
                personas={personas}
                defaultTab="ai-summary"
              />
            </Suspense>
          )}
        </TabsContent>
      </Tabs>
        </div>
      </div>
    </ErrorBoundary>
  );
}
