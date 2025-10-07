import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ArrowLeft, Settings as SettingsIcon, MessageSquare, BarChart3, Play, Loader2, Clock, CheckCircle, User, ChevronDown, ChevronUp } from 'lucide-react';
import { focusGroupsApi } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';
import { AISummaryPanel } from '@/components/analysis/AISummaryPanel';
import type { FocusGroup, FocusGroupResponses } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

interface FocusGroupViewProps {
  focusGroup: FocusGroup;
  onBack: () => void;
}

export function FocusGroupView({ focusGroup, onBack }: FocusGroupViewProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [discussionProgress, setDiscussionProgress] = useState(0);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set([0]));
  const [activeView, setActiveView] = useState<'responses' | 'ai-summary'>('responses');

  const queryClient = useQueryClient();

  const { data: responses, isLoading: responsesLoading } = useQuery<FocusGroupResponses>({
    queryKey: ['focus-group-responses', focusGroup.id],
    queryFn: () => focusGroupsApi.getResponses(focusGroup.id),
    enabled: focusGroup.status === 'completed',
  });

  const runMutation = useMutation({
    mutationFn: () => focusGroupsApi.run(focusGroup.id),
    onSuccess: () => {
      setIsRunning(true);
      setDiscussionProgress(0);

      // Simulate progress
      const interval = setInterval(() => {
        setDiscussionProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            setIsRunning(false);
            queryClient.invalidateQueries({ queryKey: ['focus-groups'] });
            queryClient.invalidateQueries({ queryKey: ['focus-group-responses', focusGroup.id] });
            return 100;
          }
          return prev + 5;
        });
      }, 500);
    },
  });

  const handleRunDiscussion = () => {
    runMutation.mutate();
  };

  const toggleQuestion = (index: number) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedQuestions(newExpanded);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-chart-1/20 text-chart-1 border-chart-1/30';
      case 'running':
        return 'bg-chart-2/20 text-chart-2 border-chart-2/30';
      case 'pending':
        return 'bg-muted text-muted-foreground border-border';
      case 'failed':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const discussionComplete = focusGroup.status === 'completed';

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={onBack}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">{focusGroup.name}</h1>
            <div className="flex items-center gap-3">
              <Badge className={getStatusColor(focusGroup.status)}>
                {focusGroup.status}
              </Badge>
              <span className="text-muted-foreground">•</span>
              <span className="text-muted-foreground">{focusGroup.questions.length} questions</span>
              <span className="text-muted-foreground">•</span>
              <span className="text-muted-foreground">{focusGroup.persona_ids.length} participants</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="configuration" className="w-full">
        <TabsList className="bg-muted border border-border shadow-sm">
          <TabsTrigger value="configuration" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <SettingsIcon className="w-4 h-4 mr-2" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="discussion" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <MessageSquare className="w-4 h-4 mr-2" />
            Discussion
          </TabsTrigger>
          <TabsTrigger value="results" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            Results & Analysis
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-card-foreground">Discussion Questions</CardTitle>
              <p className="text-muted-foreground">Questions that will be asked during the focus group session</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {focusGroup.questions.map((question, index) => (
                  <div key={index} className="p-3 bg-muted rounded-lg border border-border">
                    <div className="flex items-start gap-3">
                      <span className="text-sm font-medium text-chart-2 bg-chart-2/10 px-2 py-1 rounded">
                        Q{index + 1}
                      </span>
                      <p className="text-foreground flex-1">{question}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-card-foreground">Participants</CardTitle>
              <p className="text-muted-foreground">{focusGroup.persona_ids.length} personas selected for this session</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {focusGroup.persona_ids.map((personaId, index) => (
                  <div key={personaId} className="flex items-center gap-2 p-2 bg-muted rounded border border-border">
                    <User className="w-4 h-4 text-primary" />
                    <span className="text-sm text-foreground">Persona {index + 1}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
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
                    className="bg-green-600 hover:bg-green-700 text-white"
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
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
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
                </div>
              )}

              {discussionComplete && (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-green-600 mb-2">Discussion Complete</h3>
                  <p className="text-muted-foreground mb-4">
                    The focus group simulation has finished. View the results in the "Results & Analysis" tab.
                  </p>
                  <Button
                    variant="outline"
                    className="border-border text-card-foreground hover:text-card-foreground"
                    onClick={() => {
                      const tabTrigger = document.querySelector('[value="results"]') as HTMLElement;
                      tabTrigger?.click();
                    }}
                  >
                    View Results
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {discussionComplete ? (
            <>
              {/* View Toggle */}
              <div className="flex gap-2">
                <button
                  onClick={() => setActiveView('responses')}
                  className={cn(
                    'flex-1 py-3 px-4 rounded-xl font-medium text-sm transition-all',
                    activeView === 'responses'
                      ? 'bg-gradient-to-br from-primary-500 to-accent-500 text-white shadow-lg'
                      : 'bg-muted text-muted-foreground hover:bg-muted/70'
                  )}
                >
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  Responses
                </button>
                <button
                  onClick={() => setActiveView('ai-summary')}
                  className={cn(
                    'flex-1 py-3 px-4 rounded-xl font-medium text-sm transition-all',
                    activeView === 'ai-summary'
                      ? 'bg-gradient-to-br from-primary-500 to-accent-500 text-white shadow-lg'
                      : 'bg-muted text-muted-foreground hover:bg-muted/70'
                  )}
                >
                  <BarChart3 className="w-4 h-4 inline mr-2" />
                  AI Summary
                </button>
              </div>

              {/* Content */}
              <AnimatePresence mode="wait">
                {activeView === 'responses' && (
                  <motion.div
                    key="responses"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    {responsesLoading ? (
                      <div className="flex flex-col items-center justify-center py-12">
                        <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
                        <p className="text-sm text-muted-foreground">Loading responses...</p>
                      </div>
                    ) : !responses || responses.questions.length === 0 ? (
                      <Card className="bg-card border border-border">
                        <CardContent className="text-center py-12">
                          <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-sm text-muted-foreground">No responses available</p>
                        </CardContent>
                      </Card>
                    ) : (
                      <div className="space-y-4">
                        {responses.questions.map((q, qIdx) => {
                          const isExpanded = expandedQuestions.has(qIdx);

                          return (
                            <motion.div
                              key={qIdx}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: qIdx * 0.1 }}
                              className="border border-border rounded-xl overflow-hidden bg-card shadow-sm hover:shadow-md transition-shadow"
                            >
                              {/* Question Header */}
                              <button
                                onClick={() => toggleQuestion(qIdx)}
                                className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-muted/50 to-card hover:from-muted hover:to-muted/50 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                                    Q{qIdx + 1}
                                  </div>
                                  <div className="text-left">
                                    <h4 className="font-semibold text-foreground">{q.question}</h4>
                                    <p className="text-xs text-muted-foreground mt-0.5">{q.responses.length} responses</p>
                                  </div>
                                </div>
                                {isExpanded ? (
                                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                                ) : (
                                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                                )}
                              </button>

                              {/* Responses */}
                              <AnimatePresence>
                                {isExpanded && (
                                  <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="border-t border-border"
                                  >
                                    <div className="p-4 space-y-3">
                                      {q.responses.map((r, rIdx) => (
                                        <motion.div
                                          key={`${r.persona_id}-${rIdx}`}
                                          initial={{ opacity: 0, x: -10 }}
                                          animate={{ opacity: 1, x: 0 }}
                                          transition={{ delay: rIdx * 0.05 }}
                                          className="p-4 rounded-lg bg-gradient-to-br from-muted/50 to-card border border-border hover:border-primary/20 hover:shadow-sm transition-all"
                                        >
                                          <div className="flex items-start gap-3">
                                            <div className="flex-shrink-0">
                                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-bold text-sm shadow-md">
                                                {rIdx + 1}
                                              </div>
                                            </div>
                                            <div className="flex-1">
                                              <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-1 rounded">
                                                  {r.persona_id.slice(0, 8)}
                                                </span>
                                                <span className="text-xs text-muted-foreground">
                                                  {formatDate(r.created_at)}
                                                </span>
                                              </div>
                                              <p className="text-sm text-foreground leading-relaxed">
                                                {r.response || <span className="italic text-muted-foreground">No response recorded</span>}
                                              </p>
                                            </div>
                                          </div>
                                        </motion.div>
                                      ))}
                                    </div>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </motion.div>
                          );
                        })}
                      </div>
                    )}
                  </motion.div>
                )}

                {activeView === 'ai-summary' && (
                  <motion.div
                    key="ai-summary"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <AISummaryPanel focusGroupId={focusGroup.id} focusGroupName={focusGroup.name} />
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          ) : (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No Results Yet</h3>
                <p className="text-muted-foreground">
                  Run the discussion simulation first to generate analysis and insights.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
