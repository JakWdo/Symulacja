import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { ArrowLeft, Settings as SettingsIcon, MessageSquare, BarChart3, Play, Loader2, Clock, CheckCircle, Plus, Trash2, Brain, Network, GitGraph, Edit as EditIcon, CheckSquare } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { focusGroupsApi, personasApi, graphApi, analysisApi } from '@/lib/api';
import { Logo } from '@/components/ui/Logo';
import { ScoreChart } from '@/components/ui/ScoreChart';
import { GraphAnalysisPanel } from '@/components/panels/GraphAnalysisPanel';
import { getTargetParticipants } from '@/lib/focusGroupUtils';
import { SpinnerLogo } from '@/components/ui/SpinnerLogo';
import { toast } from '@/components/ui/toastStore';
import type { FocusGroup, FocusGroupResponses } from '@/types';
import { motion } from 'framer-motion';

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

export function FocusGroupView({ focusGroup: initialFocusGroup, onBack }: FocusGroupViewProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [discussionProgress, setDiscussionProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('setup');
  const [aiSummaryGenerated, setAiSummaryGenerated] = useState(false);
  const [generatingAiSummary, setGeneratingAiSummary] = useState(false);
  const [newQuestion, setNewQuestion] = useState('');
  const [questions, setQuestions] = useState<string[]>(initialFocusGroup.questions || []);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [graphBuilt, setGraphBuilt] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isEditMode, setIsEditMode] = useState(initialFocusGroup.status === 'pending');
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>(initialFocusGroup.persona_ids || []);

  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (payload: { persona_ids?: string[]; questions?: string[] }) =>
      focusGroupsApi.update(initialFocusGroup.id, payload as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups'] });
      queryClient.invalidateQueries({ queryKey: ['focus-group', initialFocusGroup.id] });
      setIsEditMode(false);
    },
  });

  // Fetch focus group status in real-time
  const { data: focusGroup = initialFocusGroup } = useQuery({
    queryKey: ['focus-group', initialFocusGroup.id],
    queryFn: () => focusGroupsApi.get(initialFocusGroup.id),
    refetchInterval: (data) => {
      // Poll every 2s when running, stop when completed
      return data?.status === 'running' ? 2000 : false;
    },
    initialData: initialFocusGroup,
  });

  // Fetch personas for this project
  const { data: personas = [] } = useQuery({
    queryKey: ['personas', focusGroup.project_id],
    queryFn: () => personasApi.getByProject(focusGroup.project_id),
    enabled: !!focusGroup.project_id,
  });

  const { data: responses, isLoading: responsesLoading } = useQuery<FocusGroupResponses>({
    queryKey: ['focus-group-responses', focusGroup.id],
    queryFn: () => focusGroupsApi.getResponses(focusGroup.id),
    enabled: focusGroup.status === 'completed',
    refetchInterval: focusGroup.status === 'running' ? 3000 : false, // Poll every 3s when running
  });

  // Fetch AI insights
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['focus-group-insights', focusGroup.id],
    queryFn: () => analysisApi.getInsights(focusGroup.id),
    enabled: focusGroup.status === 'completed' && aiSummaryGenerated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const runMutation = useMutation({
    mutationFn: () => focusGroupsApi.run(focusGroup.id),
    onSuccess: () => {
      setIsRunning(true);
      setDiscussionProgress(0);
      setChatMessages([]);

      // Simulate progress with chat messages
      const interval = setInterval(() => {
        setDiscussionProgress((prev) => {
          // Add chat messages during progress
          if (prev === 15 && chatMessages.length === 0) {
            setChatMessages([mockChatMessages[0]]);
          }
          if (prev === 35 && chatMessages.length === 1) {
            setChatMessages(prev => [...prev, mockChatMessages[1]]);
          }
          if (prev === 55 && chatMessages.length === 2) {
            setChatMessages(prev => [...prev, mockChatMessages[2]]);
          }
          if (prev === 75 && chatMessages.length === 3) {
            setChatMessages(prev => [...prev, mockChatMessages[3]]);
          }

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

  const handleBuildGraph = async () => {
    setBuildingGraph(true);
    try {
      await graphApi.buildGraph(focusGroup.id);
      setGraphBuilt(true);
      queryClient.invalidateQueries({ queryKey: ['graph-data', focusGroup.id] });
    } catch (error) {
      console.error('Failed to build graph:', error);
    } finally {
      setBuildingGraph(false);
    }
  };

  const addQuestion = () => {
    if (newQuestion.trim()) {
      setQuestions([...questions, newQuestion.trim()]);
      setNewQuestion('');
    }
  };

  const removeQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleGenerateAiSummary = async () => {
    setGeneratingAiSummary(true);

    try {
      await analysisApi.generateInsights(focusGroup.id);
      setGeneratingAiSummary(false);
      setAiSummaryGenerated(true);
      queryClient.invalidateQueries({ queryKey: ['focus-group-insights', focusGroup.id] });
      setActiveTab('results');
    } catch (error) {
      console.error('Failed to generate AI summary:', error);
      setGeneratingAiSummary(false);
      // TODO: Show error toast
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/30';
      case 'running':
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/30';
      case 'pending':
        return 'bg-muted text-muted-foreground border-border';
      case 'failed':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const discussionComplete = focusGroup.status === 'completed';

  // Sprawdź czy to draft (brak person lub pytań)
  const isDraft = focusGroup.status === 'pending' &&
    (focusGroup.persona_ids.length === 0 || focusGroup.questions.length === 0);

  // Automatycznie włącz tryb edycji dla nowych draftów (pustych)
  useEffect(() => {
    if (isDraft && selectedPersonaIds.length === 0 && questions.length === 0) {
      setIsEditMode(true);
    }
  }, [isDraft]); // eslint-disable-line react-hooks/exhaustive-deps

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
              {focusGroup.status}
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
          {discussionComplete && (
            <TabsTrigger value="graph" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
              <GitGraph className="w-4 h-4 mr-2" />
              Graph Analysis
            </TabsTrigger>
          )}
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="setup" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Questions */}
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-card-foreground">Discussion Questions</CardTitle>
                <p className="text-muted-foreground">Questions that will be asked during the focus group session</p>
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
                        {isEditMode && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeQuestion(index)}
                            className="text-muted-foreground hover:text-destructive"
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

                {isEditMode && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <div className="flex gap-2">
                      <div className="flex-1">
                        <Label htmlFor="new-question" className="sr-only">Add Question</Label>
                        <Input
                          id="new-question"
                          placeholder="Enter a new discussion question..."
                          value={newQuestion}
                          onChange={(e) => setNewQuestion(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && addQuestion()}
                        />
                      </div>
                      <Button
                        onClick={addQuestion}
                        disabled={!newQuestion.trim()}
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
                <CardTitle className="text-card-foreground">Participants</CardTitle>
                <p className="text-muted-foreground">
                  {isEditMode ? 'Select personas for this session' : `${selectedPersonaIds.length} personas selected for this session`}
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {isEditMode ? (
                    // Tryb edycji - pokaż wszystkie persony z checkboxami
                    personas.map((persona) => (
                      <div key={persona.id} className="flex items-center space-x-3 p-3 bg-muted rounded-lg border border-border">
                        <Checkbox
                          checked={selectedPersonaIds.includes(persona.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedPersonaIds([...selectedPersonaIds, persona.id]);
                            } else {
                              setSelectedPersonaIds(selectedPersonaIds.filter(id => id !== persona.id));
                            }
                          }}
                        />
                        <div className="flex-1">
                          <p className="text-card-foreground font-medium">{persona.full_name || `Persona ${persona.id.slice(0, 8)}`}</p>
                          <p className="text-sm text-muted-foreground">{persona.age} years old • {persona.occupation || 'No occupation'}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    // Tryb przeglądania - pokaż tylko wybrane persony
                    selectedPersonaIds.length === 0 ? (
                      <p className="text-muted-foreground text-center py-4">No personas selected</p>
                    ) : (
                      personas
                        .filter(p => selectedPersonaIds.includes(p.id))
                        .map((persona, index) => (
                          <div key={persona.id} className="flex items-center space-x-3 p-3 bg-muted rounded-lg border border-border">
                            <Checkbox
                              checked={true}
                              disabled
                            />
                            <div className="flex-1">
                              <p className="text-card-foreground font-medium">{persona.full_name || `Persona ${index + 1}`}</p>
                              <p className="text-sm text-muted-foreground">{persona.age} years old • {persona.occupation || 'No occupation'}</p>
                            </div>
                          </div>
                        ))
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Draft Actions */}
          {isDraft && (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-card-foreground mb-2">Draft Focus Group</h3>
                    <p className="text-sm text-muted-foreground">
                      {selectedPersonaIds.length === 0 && questions.length === 0
                        ? 'Add questions and select personas to complete setup'
                        : selectedPersonaIds.length === 0
                        ? 'Select at least 2 personas to complete setup'
                        : questions.length === 0
                        ? 'Add at least 1 question to complete setup'
                        : 'Ready to complete setup and run the focus group'}
                    </p>
                  </div>
                  <div className="flex gap-3">
                    {!isEditMode ? (
                      <>
                        <Button
                          variant="outline"
                          onClick={() => setIsEditMode(true)}
                          className="border-border text-card-foreground"
                        >
                          <EditIcon className="w-4 h-4 mr-2" />
                          Edit
                        </Button>
                        <Button
                          onClick={() => {
                            updateMutation.mutate({
                              persona_ids: selectedPersonaIds,
                              questions: questions.filter(q => q.trim() !== ''),
                            });
                          }}
                          disabled={selectedPersonaIds.length < 2 || questions.length === 0 || updateMutation.isPending}
                          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                        >
                          {updateMutation.isPending ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <CheckSquare className="w-4 h-4 mr-2" />
                          )}
                          Complete Setup
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setIsEditMode(false);
                            setSelectedPersonaIds(focusGroup.persona_ids);
                            setQuestions(focusGroup.questions);
                          }}
                          className="border-border text-card-foreground"
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={() => {
                            updateMutation.mutate({
                              persona_ids: selectedPersonaIds,
                              questions: questions.filter(q => q.trim() !== ''),
                            });
                          }}
                          disabled={updateMutation.isPending}
                          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                        >
                          {updateMutation.isPending ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : null}
                          Save Changes
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
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
                  <CheckCircle className="w-12 h-12 text-[#F27405] mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-[#F27405] mb-2">Discussion Complete</h3>
                  <p className="text-muted-foreground mb-4">
                    The focus group simulation has finished. Generate AI insights to analyze the results.
                  </p>
                  <Button
                    onClick={handleGenerateAiSummary}
                    disabled={generatingAiSummary}
                    className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                  >
                    {generatingAiSummary ? (
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
                  <CheckCircle className="w-12 h-12 text-[#F27405] mx-auto mb-4" />
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
                    {!graphBuilt && (
                      <Button
                        onClick={handleBuildGraph}
                        disabled={buildingGraph}
                        className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                      >
                        {buildingGraph ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Building Graph...
                          </>
                        ) : (
                          <>
                            <Network className="w-4 h-4 mr-2" />
                            Build Knowledge Graph
                          </>
                        )}
                      </Button>
                    )}
                    {graphBuilt && (
                      <Button
                        onClick={() => window.location.hash = '#graph-analysis'}
                        className="bg-green-600 hover:bg-green-700 text-white"
                      >
                        <Network className="w-4 h-4 mr-2" />
                        View Graph Analysis
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {discussionComplete ? (
            <>
              {/* AI Summary Card */}
              {insightsLoading ? (
                <Card className="bg-card border border-border shadow-sm">
                  <CardContent className="py-12 flex flex-col items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
                    <p className="text-muted-foreground">Loading AI insights...</p>
                  </CardContent>
                </Card>
              ) : insights ? (
                <Card className="bg-card border border-border shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-card-foreground flex items-center gap-2">
                      <Logo className="w-5 h-5" />
                      AI Summary
                    </CardTitle>
                    <p className="text-muted-foreground">Key insights generated by AI analysis</p>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {/* Executive Summary */}
                      <div className="bg-muted border border-border rounded-lg p-4 space-y-2">
                        <h4 className="font-semibold text-card-foreground">Executive Summary</h4>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          {insights.llm_rationale || 'Participants showed strong interest in ease-of-use features and integration capabilities. Pricing concerns were raised by multiple participants, suggesting value proposition optimization.'}
                        </p>
                      </div>

                      {/* Key Insights */}
                      <div className="bg-muted border border-border rounded-lg p-4 space-y-2">
                        <h4 className="font-semibold text-card-foreground">Key Insights</h4>
                        <ul className="space-y-1">
                          {insights.signal_breakdown?.strengths.slice(0, 4).map((item, idx) => (
                            <li key={idx} className="text-sm text-muted-foreground">• {item.title}</li>
                          )) || (
                            <>
                              <li className="text-sm text-muted-foreground">• Usability is the primary concern</li>
                              <li className="text-sm text-muted-foreground">• Mobile access is highly valued</li>
                              <li className="text-sm text-muted-foreground">• Integration needs vary by role</li>
                              <li className="text-sm text-muted-foreground">• Price sensitivity across segments</li>
                            </>
                          )}
                        </ul>
                      </div>

                      {/* Recommendations */}
                      <div className="bg-muted border border-border rounded-lg p-4 space-y-2">
                        <h4 className="font-semibold text-card-foreground">Recommendations</h4>
                        <ul className="space-y-1">
                          {insights.signal_breakdown?.opportunities.slice(0, 4).map((item, idx) => (
                            <li key={idx} className="text-sm text-muted-foreground">• {item.title}</li>
                          )) || (
                            <>
                              <li className="text-sm text-muted-foreground">• Prioritize UX improvements</li>
                              <li className="text-sm text-muted-foreground">• Develop mobile-first approach</li>
                              <li className="text-sm text-muted-foreground">• Create tiered pricing model</li>
                              <li className="text-sm text-muted-foreground">• Focus on integration features</li>
                            </>
                          )}
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-card border border-border shadow-sm">
                  <CardContent className="py-12 text-center">
                    <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No insights available. Generate AI summary first.</p>
                  </CardContent>
                </Card>
              )}

              {/* Sentiment & Score Analysis */}
              {insights && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Sentiment Analysis */}
                  <Card className="bg-card border border-border shadow-sm">
                    <CardHeader>
                      <CardTitle className="text-card-foreground">Sentiment Analysis</CardTitle>
                      <p className="text-muted-foreground">Overall sentiment distribution</p>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-col items-center space-y-6">
                        {/* Doughnut Chart */}
                        <div className="relative w-64 h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={[
                                  { name: 'Very Positive', value: Math.round(insights.metrics.sentiment_summary.positive_ratio * 35), color: '#10B981' },
                                  { name: 'Positive', value: Math.round(insights.metrics.sentiment_summary.positive_ratio * 65), color: '#34D399' },
                                  { name: 'Neutral', value: Math.round(insights.metrics.sentiment_summary.neutral_ratio * 100), color: '#6B7280' },
                                  { name: 'Negative', value: Math.round(insights.metrics.sentiment_summary.negative_ratio * 100), color: '#F59E0B' },
                                  { name: 'Very Negative', value: Math.round(insights.metrics.sentiment_summary.negative_ratio * 25), color: '#EF4444' }
                                ]}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                dataKey="value"
                                startAngle={90}
                                endAngle={450}
                              >
                                {[
                                  { name: 'Very Positive', value: Math.round(insights.metrics.sentiment_summary.positive_ratio * 35), color: '#10B981' },
                                  { name: 'Positive', value: Math.round(insights.metrics.sentiment_summary.positive_ratio * 65), color: '#34D399' },
                                  { name: 'Neutral', value: Math.round(insights.metrics.sentiment_summary.neutral_ratio * 100), color: '#6B7280' },
                                  { name: 'Negative', value: Math.round(insights.metrics.sentiment_summary.negative_ratio * 100), color: '#F59E0B' },
                                  { name: 'Very Negative', value: Math.round(insights.metrics.sentiment_summary.negative_ratio * 25), color: '#EF4444' }
                                ].map((entry, index) => (
                                  <Cell
                                    key={`cell-${index}`}
                                    fill={entry.color}
                                    stroke={hoveredIndex === index ? "#333333" : entry.color}
                                    strokeWidth={hoveredIndex === index ? 3 : 0}
                                    style={{
                                      cursor: 'pointer',
                                      filter: hoveredIndex === index ? 'drop-shadow(0px 4px 8px rgba(0,0,0,0.15))' : 'none',
                                      transition: 'all 0.2s ease'
                                    }}
                                    onMouseEnter={() => setHoveredIndex(index)}
                                    onMouseLeave={() => setHoveredIndex(null)}
                                  />
                                ))}
                              </Pie>
                              <Tooltip
                                content={({ active, payload }) => {
                                  if (active && payload && payload.length) {
                                    const data = payload[0].payload;
                                    return (
                                      <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
                                        <p className="text-popover-foreground font-medium">{data.name}</p>
                                        <p className="text-popover-foreground text-sm">{data.value}%</p>
                                      </div>
                                    );
                                  }
                                  return null;
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>

                        {/* Legend */}
                        <div className="flex flex-wrap gap-4 justify-center">
                          {[
                            { name: 'Very Positive', color: '#10B981' },
                            { name: 'Positive', color: '#34D399' },
                            { name: 'Neutral', color: '#6B7280' },
                            { name: 'Negative', color: '#F59E0B' },
                            { name: 'Very Negative', color: '#EF4444' }
                          ].map((entry, index) => (
                            <div key={index} className="flex items-center gap-2">
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: entry.color }}
                              />
                              <span className="text-sm text-card-foreground">{entry.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Score Analysis */}
                  <Card className="bg-card border border-border shadow-sm">
                    <CardHeader>
                      <CardTitle className="text-card-foreground">Score Analysis</CardTitle>
                      <p className="text-muted-foreground">Overall participant satisfaction score</p>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-center py-8">
                        <ScoreChart score={Math.round(insights.idea_score)} />
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Raw Responses */}
              {responsesLoading ? (
                <Card className="bg-card border border-border shadow-sm">
                  <CardContent className="py-12 flex flex-col items-center justify-center">
                    <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
                    <p className="text-sm text-muted-foreground">Loading responses...</p>
                  </CardContent>
                </Card>
              ) : responses && responses.questions.length > 0 ? (
                <Card className="bg-card border border-border shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-card-foreground">Raw Responses</CardTitle>
                    <p className="text-muted-foreground">Detailed responses from each participant</p>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {responses.questions.map((q, qIdx) => (
                        <div key={qIdx} className="space-y-4">
                          {/* Question Header */}
                          <div className="flex items-center gap-3">
                            <div className="bg-muted border border-border rounded px-3 py-1">
                              <span className="text-sm font-semibold text-card-foreground">Q{qIdx + 1}</span>
                            </div>
                            <h4 className="text-card-foreground font-semibold">{q.question}</h4>
                          </div>

                          {/* Responses */}
                          <div className="ml-12 space-y-3">
                            {q.responses.slice(0, 3).map((r, rIdx) => {
                              const persona = personas.find(p => p.id === r.persona_id);
                              const initials = persona?.full_name?.split(' ').map(n => n[0]).join('') || 'P';

                              return (
                                <div key={`${r.persona_id}-${rIdx}`} className="bg-muted border border-border rounded-lg p-4 space-y-2">
                                  <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-gradient-to-br from-[#F27405] to-[#F29F05] rounded-full flex items-center justify-center shrink-0">
                                      <span className="text-white text-xs font-semibold">{initials}</span>
                                    </div>
                                    <div>
                                      <p className="text-card-foreground font-medium text-sm">{persona?.full_name || `Persona ${rIdx + 1}`}</p>
                                    </div>
                                  </div>
                                  <p className="text-sm text-muted-foreground leading-relaxed ml-11">
                                    {r.response || <span className="italic">No response recorded</span>}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-card border border-border">
                  <CardContent className="text-center py-12">
                    <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-sm text-muted-foreground">No responses available</p>
                  </CardContent>
                </Card>
              )}
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

        {/* Graph Analysis Tab */}
        <TabsContent value="graph" className="space-y-6">
          {discussionComplete ? (
            <div className="h-[calc(100vh-300px)]">
              <GraphAnalysisPanel focusGroupId={focusGroup.id} />
            </div>
          ) : (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="text-center py-12">
                <Network className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">Graph Not Available</h3>
                <p className="text-muted-foreground">
                  Complete the discussion first to build the knowledge graph.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
      </div>
    </div>
  );
}
