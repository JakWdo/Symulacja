import { useState, useEffect, useRef, useMemo, Suspense, lazy } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { ArrowLeft, Settings as SettingsIcon, MessageSquare, BarChart3, Play, Clock, CheckCircle, Plus, Trash2, Brain, AlertCircle } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { focusGroupsApi, personasApi, analysisApi, projectsApi } from '@/lib/api';
import { Logo } from '@/components/ui/logo';
import { ScoreChart } from '@/components/ui/score-chart';
import { toast } from '@/components/ui/toastStore';
import type { FocusGroup, FocusGroupResponses } from '@/types';
import type { AISummaryResponse } from '@/types/ai-summary';
import { motion } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { useAppStore } from '@/store/appStore';

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

  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (payload: {
      name: string;
      description: string | null;
      project_context: string | null;
      persona_ids: string[];
      questions: string[];
      mode: 'normal' | 'adversarial';
    }) => focusGroupsApi.update(initialFocusGroup.id, payload as any),
    onSuccess: (updated) => {
      setQuestions(updated.questions || []);
      setSelectedPersonaIds(updated.persona_ids || []);
      queryClient.setQueryData(['focus-group', initialFocusGroup.id], updated);
      queryClient.invalidateQueries({ queryKey: ['focus-groups', updated.project_id] });
      queryClient.invalidateQueries({ queryKey: ['focus-group', initialFocusGroup.id] });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to save changes', message);
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
      toast.success('Focus group launched', contextLabel);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to launch focus group', `${contextLabel} • ${message}`);
    },
  });

  const handleRunDiscussion = () => {
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
      toast.success('AI Summary generated successfully', contextLabel);
    } catch (error) {
      console.error('Failed to generate AI summary:', error);
      setGeneratingAiSummary(false);
      setSummaryPending(focusGroup.id, false);
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to generate AI summary', `${contextLabel} • ${message}`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-[#F27405]/10 text-[#F27405] dark:text-[#F27405] border-[#F27405]/30';
      case 'running':
        return 'bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/30';
      case 'pending':
        return 'bg-muted text-muted-foreground border-border';
      case 'failed':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      case 'pending':
        return 'Pending';
      case 'failed':
        return 'Failed';
      default:
        return status;
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
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Focus Groups
        </Button>
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">{focusGroup.name}</h1>
          <div className="flex items-center gap-3">
            <Badge className={getStatusColor(focusGroup.status)}>
              {getStatusText(focusGroup.status)}
            </Badge>
            <span className="text-muted-foreground">•</span>
            <span className="text-muted-foreground">{focusGroup.questions.length} questions</span>
            <span className="text-muted-foreground">•</span>
            <span className="text-muted-foreground">{focusGroup.persona_ids.length} participants</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-muted border border-border shadow-sm">
          <TabsTrigger value="setup" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <SettingsIcon className="w-4 h-4 mr-2" />
            Konfiguracja
          </TabsTrigger>
          <TabsTrigger value="discussion" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <MessageSquare className="w-4 h-4 mr-2" />
            Dyskusja
          </TabsTrigger>
          <TabsTrigger value="results" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            Wyniki i Analiza
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="setup" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Questions */}
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-card-foreground">Discussion Questions</CardTitle>
                    <p className="text-muted-foreground">
                      {canModifyConfig
                        ? 'Adjust the prompts for your discussion. Changes save automatically.'
                        : 'These are the prompts used during the session.'}
                    </p>
                  </div>
                  {updateMutation.isPending && (
                    <Badge variant="outline" className="text-xs">
                      Saving...
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {questions.map((question: string, index: number) => (
                    <div key={index} className="p-3 bg-muted rounded-lg border border-border">
                      <div className="flex items-start gap-3">
                        <span className="text-sm font-medium text-[#F27405] bg-[#F27405]/10 px-2 py-1 rounded">
                          Q{index + 1}
                        </span>
                        <p className="text-foreground flex-1">{question}</p>
                        {canModifyConfig && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeQuestion(index)}
                            className="text-muted-foreground hover:text-destructive"
                            disabled={updateMutation.isPending}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                  {questions.length === 0 && (
                    <p className="text-muted-foreground text-center py-4">No questions configured</p>
                  )}
                </div>

                {canModifyConfig && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <div className="flex gap-2">
                      <div className="flex-1">
                        <Label htmlFor="new-question" className="sr-only">{t('focus-groups:accessibility.addQuestion')}</Label>
                        <Input
                          id="new-question"
                          placeholder="Enter a new discussion question..."
                          value={newQuestion}
                          onChange={(e) => setNewQuestion(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              addQuestion();
                            }
                          }}
                          disabled={updateMutation.isPending}
                        />
                      </div>
                      <Button
                        onClick={addQuestion}
                        disabled={!newQuestion.trim() || updateMutation.isPending}
                        className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Participants */}
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-card-foreground">Participants</CardTitle>
                    <p className="text-muted-foreground">
                      {canModifyConfig
                        ? 'Select personas for this session. Changes save automatically.'
                        : `${selectedPersonaIds.length} personas participated in this session.`}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {personas.length === 0 ? (
                    <p className="text-muted-foreground text-center py-4">No personas available</p>
                  ) : (
                    personas.map((persona) => {
                      const isSelected = selectedPersonaIds.includes(persona.id);
                      return (
                        <div
                          key={persona.id}
                          className={`flex items-center space-x-3 p-3 rounded-lg border transition-colors ${
                            isSelected
                              ? 'bg-[#F27405]/10 border-[#F27405]/40'
                              : 'bg-muted border-border'
                          }`}
                        >
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={(checked) => handlePersonaToggle(persona.id, checked === true)}
                            disabled={!canModifyConfig || updateMutation.isPending}
                          />
                          <div className="flex-1">
                            <p className="text-card-foreground font-medium">
                              {persona.full_name || `Persona ${persona.id.slice(0, 8)}`}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {persona.age} years old • {persona.occupation || 'No occupation'}
                            </p>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

        </TabsContent>

        {/* Discussion Tab */}
        <TabsContent value="discussion" className="space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-card-foreground">Run Discussion</CardTitle>
                  <p className="text-muted-foreground">Start the AI-simulated focus group discussion</p>
                </div>

                {!discussionComplete && !isRunning && focusGroup.status === 'pending' && (
                  <Button
                    onClick={handleRunDiscussion}
                    className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                    disabled={runMutation.isPending}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Discussion
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {!isRunning && !discussionComplete && focusGroup.status === 'pending' && (
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-card-foreground mb-2">Ready to Start</h3>
                  <p className="text-muted-foreground">
                    Click "Start Discussion" to begin the AI simulation with {focusGroup.persona_ids.length} participants.
                  </p>
                </div>
              )}

              {(isRunning || focusGroup.status === 'running') && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Logo className="w-5 h-5" spinning />
                    <span className="text-card-foreground">Simulation in progress...</span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Discussion Progress</span>
                      <span className="text-muted-foreground">{discussionProgress}%</span>
                    </div>
                    <Progress value={discussionProgress} className="w-full" />
                  </div>

                  <div className="bg-muted rounded-lg p-4 border border-border">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-primary" />
                        <span className="text-muted-foreground">Current Status:</span>
                      </div>
                      <p className="text-card-foreground">
                        {discussionProgress < 30 && "Participants are introducing themselves..."}
                        {discussionProgress >= 30 && discussionProgress < 60 && `Discussing question 1 of ${focusGroup.questions.length}`}
                        {discussionProgress >= 60 && discussionProgress < 90 && "Exploring follow-up questions..."}
                        {discussionProgress >= 90 && "Wrapping up discussion..."}
                      </p>
                    </div>
                  </div>

                  {/* Live Chat Messages */}
                  {chatMessages.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-4">
                      <h4 className="text-card-foreground font-medium mb-3">Live Discussion</h4>
                      <div className="space-y-3 max-h-48 overflow-y-auto">
                        {chatMessages.map((message) => (
                          <motion.div
                            key={message.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                            className="flex gap-3"
                          >
                            <div className="w-8 h-8 bg-gradient-to-br from-[#F27405] to-[#F29F05] rounded-full flex items-center justify-center shrink-0">
                              <span className="text-white text-xs font-medium">
                                {message.persona.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-card-foreground font-medium text-sm">{message.persona}</span>
                                <span className="text-muted-foreground text-xs">{message.timestamp}</span>
                              </div>
                              <div className="bg-muted/50 rounded-lg p-3 border border-border/50">
                                <p className="text-card-foreground text-sm">{message.message}</p>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {discussionComplete && !aiSummaryGenerated && (
                <div className="text-center py-8">
                  <img
                    src="/sight-logo-przezroczyste.png"
                    alt="Sight Logo"
                    className="w-16 h-16 mx-auto mb-4 object-contain"
                  />
                  <h3 className="text-lg font-medium text-[#F27405] mb-2">Discussion Complete</h3>
                  <p className="text-muted-foreground mb-4">
                    The focus group simulation has finished. Generate AI insights to analyze the results.
                  </p>
                  <Button
                    onClick={handleGenerateAiSummary}
                    disabled={summaryProcessing}
                    className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                  >
                    {summaryProcessing ? (
                      <>
                        <Logo className="w-4 h-4 mr-2" spinning />
                        Generating AI Summary...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4 mr-2" />
                        Generate AI Summary
                      </>
                    )}
                  </Button>
                </div>
              )}

              {discussionComplete && aiSummaryGenerated && (
                <div className="text-center py-8">
                  <img
                    src="/sight-logo-przezroczyste.png"
                    alt="Sight Logo"
                    className="w-16 h-16 mx-auto mb-4 object-contain"
                  />
                  <h3 className="text-lg font-medium text-[#F27405] mb-2">AI Summary Generated</h3>
                  <p className="text-muted-foreground mb-4">
                    AI insights have been generated. View the complete analysis in the "Results & Analysis" tab.
                  </p>
                  <div className="flex gap-3 justify-center">
                    <Button
                      variant="outline"
                      onClick={() => setActiveTab('results')}
                      className="border-border text-card-foreground hover:text-card-foreground"
                    >
                      View Results
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab - NEW: Using FocusGroupAnalysisView */}
        <TabsContent value="results" className="space-y-6">
          {focusGroup.status === 'pending' && !isRunning && (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">Brak wyników</h3>
                <p className="text-muted-foreground">
                  Uruchom najpierw dyskusję, aby wygenerować analizę i wnioski
                </p>
              </CardContent>
            </Card>
          )}

          {(focusGroup.status === 'running' || isRunning) && (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="py-12 flex flex-col items-center gap-4 text-center">
                <Logo className="w-8 h-8" spinning />
                <div className="space-y-1">
                  <h3 className="text-lg font-medium text-card-foreground">Dyskusja w toku</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Odpowiedzi i wnioski pojawią się tutaj automatycznie po zakończeniu symulacji
                  </p>
                </div>
                <div className="w-full max-w-sm space-y-2">
                  <Progress value={discussionProgress} className="w-full" />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{discussionProgress}% ukończono</span>
                    {totalExpectedResponses > 0 ? (
                      <span>
                        {responsesCount}/{totalExpectedResponses} odpowiedzi
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
                <h3 className="text-lg font-medium text-destructive">Uruchomienie nie powiodło się</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Nie udało się ukończyć tej symulacji. Sprawdź dziennik aktywności lub spróbuj uruchomić ponownie.
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
                    <p className="text-muted-foreground">Ładowanie analizy...</p>
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
  );
}
