import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { Network, Users, MessageCircle, Brain, Search, Filter, Eye, RefreshCcw } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { NetworkGraph } from '@/components/analysis/NetworkGraph';
import { projectsApi, graphApi, focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { SpinnerLogo } from '@/components/ui/SpinnerLogo';
import { toast } from '@/components/ui/toastStore';
import type { GraphQueryResponse } from '@/types';

export function GraphAnalysis() {
  const {
    selectedProject,
    setSelectedProject,
    selectedFocusGroup,
    setSelectedFocusGroup,
    setGraphData,
    graphAsk,
    setGraphAskQuestion,
    setGraphAskResult,
    setGraphAskStatus,
    setGraphAskFocusGroup,
    resetGraphAsk,
  } = useAppStore();
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [graphFilter, setGraphFilter] = useState('all');
  const queryClient = useQueryClient();
  const question = graphAsk.question;
  const askResult = graphAsk.result;
  const askErrorMessage = graphAsk.error;
  const suggestedQueries = useMemo(
    () => [
      'Who influences others the most?',
      'Show me controversial topics.',
      'Which emotions dominate the discussion?',
      'Which concepts are rated most positively?',
    ],
    []
  );
  const {
    mutate: runAskQuestion,
    isPending: mutationPending,
    reset: resetAskMutation,
  } = useMutation<GraphQueryResponse, unknown, string>({
    mutationKey: ['graph-ask', selectedFocusGroup?.id],
    mutationFn: async (queryText: string) => {
      if (!selectedFocusGroup) {
        throw new Error('Select a completed focus group first.');
      }
      return graphApi.askQuestion(selectedFocusGroup.id, queryText);
    },
    onSuccess: (data: GraphQueryResponse) => {
      setGraphAskResult(data);
      setGraphAskStatus('success', null);
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : error instanceof Error
          ? error.message
          : 'Unknown error';
      setGraphAskStatus('error', message);
    },
  });
  const isAskPending = graphAsk.status === 'loading' || mutationPending;
  const canSubmitQuestion =
    question.trim().length > 0 && !!selectedFocusGroup && !isAskPending;
  const combinedSuggestions = useMemo(() => {
    if (!askResult?.suggested_questions?.length) {
      return suggestedQueries;
    }
    const deduped = new Set<string>([...suggestedQueries, ...askResult.suggested_questions]);
    return Array.from(deduped);
  }, [askResult?.suggested_questions, suggestedQueries]);

  // Fetch projects
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  useEffect(() => {
    if (!selectedProject && projects.length > 0) {
      setSelectedProject(projects[0]);
    }
  }, [projects, selectedProject, setSelectedProject]);

  const activeProjectId = selectedProject?.id ?? null;

  const {
    data: focusGroups = [],
    isLoading: focusGroupsLoading,
  } = useQuery({
    queryKey: ['focus-groups', activeProjectId],
    queryFn: () => focusGroupsApi.getByProject(activeProjectId!),
    enabled: !!activeProjectId,
  });

  const completedFocusGroups = useMemo(
    () => focusGroups.filter((group) => group.status === 'completed'),
    [focusGroups]
  );

  useEffect(() => {
    if (!activeProjectId) {
      if (selectedFocusGroup) {
        setSelectedFocusGroup(null);
      }
      return;
    }

    if (focusGroups.length === 0) {
      if (selectedFocusGroup) {
        setSelectedFocusGroup(null);
      }
      return;
    }

    if (selectedFocusGroup) {
      const updatedSelection = completedFocusGroups.find(
        (group) => group.id === selectedFocusGroup.id
      );

      if (updatedSelection) {
        if (updatedSelection !== selectedFocusGroup) {
          setSelectedFocusGroup(updatedSelection);
        }
        return;
      }
    }

    if (completedFocusGroups.length > 0) {
      const nextGroup = completedFocusGroups[0];
      if (nextGroup.id !== selectedFocusGroup?.id) {
        setSelectedFocusGroup(nextGroup);
      }
    } else if (selectedFocusGroup) {
      setSelectedFocusGroup(null);
    }
  }, [
    activeProjectId,
    focusGroups,
    completedFocusGroups,
    selectedFocusGroup,
    setSelectedFocusGroup,
  ]);

  useEffect(() => {
    const currentId = selectedFocusGroup?.id ?? null;
    if (graphAsk.focusGroupId === currentId) {
      return;
    }
    setSelectedConcept(null);
    setGraphFilter('all');
    resetGraphAsk(currentId);
    resetAskMutation();
  }, [graphAsk.focusGroupId, selectedFocusGroup?.id, resetGraphAsk, resetAskMutation]);

  const handleAskQuestion = () => {
    if (!question.trim()) {
      return;
    }
    if (!selectedFocusGroup) {
      toast.info('Select a focus group', 'Choose a completed focus group to analyze questions.');
      return;
    }
    if (isAskPending) {
      return;
    }
    const trimmed = question.trim();
    setGraphAskQuestion(trimmed);
    setGraphAskFocusGroup(selectedFocusGroup.id);
    setGraphAskStatus('loading', null);
    setGraphAskResult(null);
    runAskQuestion(trimmed);
  };

  // Fetch graph data for the selected focus group
  const {
    data: graphQueryData,
    isLoading: graphLoading,
    error: graphError,
    isFetching: isGraphFetching,
    refetch: refetchGraph,
  } = useQuery({
    queryKey: ['graph-data', selectedFocusGroup?.id, graphFilter],
    queryFn: () =>
      graphApi.getGraph(
        selectedFocusGroup!.id,
        graphFilter === 'all' ? undefined : graphFilter
      ),
    enabled: !!selectedFocusGroup,
    retry: 1,
  });

  useEffect(() => {
    if (!selectedFocusGroup || !graphQueryData) {
      setGraphData(null);
      return;
    }

    const hasNodes =
      Array.isArray(graphQueryData.nodes) && graphQueryData.nodes.length > 0;

    if (hasNodes) {
      setGraphData(graphQueryData);
    } else {
      setGraphData(null);
    }
  }, [graphQueryData, selectedFocusGroup, setGraphData]);

  // Fetch influential personas scoped to the selected focus group
  const { data: influentialPersonas = [] } = useQuery({
    queryKey: ['influential-personas', selectedFocusGroup?.id],
    queryFn: () => graphApi.getInfluentialPersonas(selectedFocusGroup!.id),
    enabled: !!selectedFocusGroup,
  });

  // Fetch key concepts scoped to the selected focus group
  const { data: keyConcepts = [] } = useQuery({
    queryKey: ['key-concepts', selectedFocusGroup?.id],
    queryFn: () => graphApi.getKeyConcepts(selectedFocusGroup!.id),
    enabled: !!selectedFocusGroup,
  });

  const buildGraphMutation = useMutation({
    mutationFn: () => graphApi.buildGraph(selectedFocusGroup!.id),
    onSuccess: (stats) => {
      toast.success('Graph rebuilt', `Created ${stats.relationships_created} relations`);
      queryClient.invalidateQueries({ queryKey: ['graph-data', selectedFocusGroup?.id] });
      queryClient.invalidateQueries({ queryKey: ['key-concepts', selectedFocusGroup?.id] });
      queryClient.invalidateQueries({ queryKey: ['influential-personas', selectedFocusGroup?.id] });
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : error instanceof Error
          ? error.message
          : 'Unknown error';
      toast.error('Failed to build graph', message);
    },
  });

  const graphErrorMessage = graphError
    ? axios.isAxiosError(graphError)
      ? graphError.response?.data?.detail || graphError.message
      : graphError instanceof Error
        ? graphError.message
        : 'Unknown error'
    : null;

  const hasGraphData =
    !!graphQueryData && Array.isArray(graphQueryData.nodes) && graphQueryData.nodes.length > 0;

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return 'text-green-600';
    if (sentiment >= 0.4) return 'text-amber-600';
    return 'text-red-600';
  };

  const getSentimentBg = (sentiment: number) => {
    if (sentiment >= 0.7) return 'bg-green-100';
    if (sentiment >= 0.4) return 'bg-amber-100';
    return 'bg-red-100';
  };

  const handleNodeClick = (node: any) => {
    if (node.type === 'concept') {
      const normalized =
        typeof node.name === 'string' ? node.name.toLowerCase() : String(node.id);
      setSelectedConcept((current) => (current === normalized ? null : normalized));
    }
  };

  const resetFilters = () => {
    setSelectedConcept(null);
    setGraphFilter('all');
    setSearchQuery('');
  };

  return (
    <div className="w-full h-full overflow-y-auto">
      <TooltipProvider>
        <div className="max-w-7xl mx-auto space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Graph Analysis</h1>
            <p className="text-muted-foreground">
              Explore dynamic networks of personas, concepts, and emotions from your research
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select
              value={selectedProject?.id || ''}
              onValueChange={(value) => {
                const project = projects.find((p) => p.id === value);
                if (project) setSelectedProject(project);
              }}
            >
              <SelectTrigger className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-0 rounded-md px-3.5 py-2 h-9 hover:bg-[#f0f1f2] dark:hover:bg-[#333333] transition-colors w-56">
                <SelectValue
                  placeholder="Select project"
                  className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] leading-5"
                />
              </SelectTrigger>
              <SelectContent>
                {projectsLoading ? (
                  <div className="flex items-center justify-center p-2">
                    <SpinnerLogo className="w-4 h-4" />
                  </div>
                ) : projects.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">No projects found</div>
                ) : (
                  projects.map((project) => (
                    <SelectItem
                      key={project.id}
                      value={project.id}
                      className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] focus:bg-[#e9ecef] dark:focus:bg-[#333333]"
                    >
                      {project.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            <Select
              value={selectedFocusGroup?.id || ''}
              onValueChange={(value) => {
                const focusGroup = focusGroups.find((group) => group.id === value);
                if (focusGroup) {
                  setSelectedFocusGroup(focusGroup);
                }
              }}
              disabled={!activeProjectId || focusGroupsLoading || completedFocusGroups.length === 0}
            >
              <SelectTrigger className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-0 rounded-md px-3.5 py-2 h-9 hover:bg-[#f0f1f2] dark:hover:bg-[#333333] transition-colors w-56">
                <SelectValue
                  placeholder={
                    focusGroupsLoading
                      ? 'Loading focus groups...'
                      : completedFocusGroups.length === 0
                        ? 'No completed focus groups'
                        : 'Select focus group'
                  }
                  className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] leading-5"
                />
              </SelectTrigger>
              <SelectContent>
                {focusGroupsLoading ? (
                  <div className="flex items-center justify-center p-2">
                    <SpinnerLogo className="w-4 h-4" />
                  </div>
                ) : completedFocusGroups.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">
                    Run or complete a focus group to unlock graph insights
                  </div>
                ) : (
                  completedFocusGroups.map((group) => (
                    <SelectItem
                      key={group.id}
                      value={group.id}
                      className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] focus:bg-[#e9ecef] dark:focus:bg-[#333333]"
                    >
                      {group.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
        </div>

        {!activeProjectId ? (
          <Card>
            <CardContent className="text-center py-12">
              <Network className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-card-foreground mb-2">No Project Selected</h3>
              <p className="text-muted-foreground">Please select a project to view graph analysis</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Graph Visualization */}
            <div className="xl:col-span-3">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground flex items-center gap-2">
                      <Network className="w-5 h-5 text-primary" />
                      Knowledge Network
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={!selectedFocusGroup || buildGraphMutation.isPending}
                        onClick={() => buildGraphMutation.mutate()}
                      >
                        <RefreshCcw className="w-4 h-4 mr-2" />
                        {buildGraphMutation.isPending ? 'Building...' : 'Build Graph'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowFilters(!showFilters)}
                        className={showFilters ? 'bg-primary/10 border-primary' : ''}
                      >
                        <Filter className="w-4 h-4 mr-2" />
                        Filters
                      </Button>
                      <Select value={graphFilter} onValueChange={setGraphFilter}>
                        <SelectTrigger className="w-32">
                          <Eye className="w-4 h-4 mr-2" />
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Data</SelectItem>
                          <SelectItem value="positive">Positive Only</SelectItem>
                          <SelectItem value="negative">Negative Only</SelectItem>
                          <SelectItem value="influence">High Influence</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Interactive Graph Visualization */}
                  <div className="h-[500px] bg-muted/30 rounded-lg border border-border relative overflow-hidden">
                    {!selectedFocusGroup ? (
                      <div className="flex flex-col items-center justify-center h-full text-center px-6">
                        <Network className="w-10 h-10 text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">
                          Select a completed focus group to explore its knowledge graph.
                        </p>
                      </div>
                    ) : (graphLoading && !graphQueryData) ? (
                      <div className="flex items-center justify-center h-full">
                        <SpinnerLogo className="w-8 h-8" />
                      </div>
                    ) : graphErrorMessage ? (
                      <div className="flex flex-col items-center justify-center h-full text-center px-6 space-y-3">
                        <div>
                          <p className="text-sm text-muted-foreground">
                            {graphErrorMessage}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Try rebuilding the graph or rerun the focus group.
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm" onClick={() => refetchGraph()}>
                            Retry
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => buildGraphMutation.mutate()}
                            disabled={buildGraphMutation.isPending}
                          >
                            <RefreshCcw className="w-4 h-4 mr-2" />
                            {buildGraphMutation.isPending ? 'Building...' : 'Build Graph'}
                          </Button>
                        </div>
                      </div>
                    ) : hasGraphData ? (
                      <NetworkGraph
                        data={graphQueryData}
                        filter={graphFilter}
                        selectedConcept={selectedConcept}
                        onNodeClick={handleNodeClick}
                        className="w-full h-full"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-center px-6 space-y-3">
                        <p className="text-muted-foreground">
                          No graph data available yet. Run a focus group or rebuild the graph to generate insights.
                        </p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => buildGraphMutation.mutate()}
                          disabled={buildGraphMutation.isPending}
                        >
                          <RefreshCcw className="w-4 h-4 mr-2" />
                          {buildGraphMutation.isPending ? 'Building...' : 'Build Graph'}
                        </Button>
                      </div>
                    )}

                    {/* Active Filters */}
                    {(selectedConcept || graphFilter !== 'all') && hasGraphData && (
                      <div className="absolute top-4 left-4 flex items-center gap-2 z-20">
                        <Badge variant="secondary" className="bg-primary/10 text-primary">
                          {selectedConcept ? `Filtered: ${selectedConcept}` : `Filter: ${graphFilter}`}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-6 px-2 text-xs"
                          onClick={resetFilters}
                        >
                          Clear
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Natural Language Query */}
              <Card className="bg-card border border-border mt-6">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <Brain className="w-5 h-5 text-primary" />
                    Ask Your Data
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                        <Input
                          placeholder="Ask a question about your research data (e.g., 'Who was most concerned about pricing?')"
                          value={question}
                          onChange={(e) => {
                            setGraphAskQuestion(e.target.value);
                            if (graphAsk.status === 'error') {
                              setGraphAskStatus('idle', null);
                            }
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleAskQuestion();
                            }
                          }}
                          className="pl-10"
                          disabled={!selectedFocusGroup}
                        />
                      </div>
                      <Button
                        className="bg-primary hover:bg-primary/90 text-primary-foreground"
                        disabled={!canSubmitQuestion}
                        onClick={handleAskQuestion}
                      >
                        {isAskPending ? (
                          <>
                            <SpinnerLogo className="mr-2 h-4 w-4" />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Brain className="w-4 h-4 mr-2" />
                            Analyze
                          </>
                        )}
                      </Button>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {combinedSuggestions.map((suggestion) => (
                        <Button
                          key={suggestion}
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 px-3 text-xs"
                          disabled={!selectedFocusGroup || isAskPending}
                          onClick={() => {
                            setGraphAskQuestion(suggestion);
                            if (!selectedFocusGroup) {
                              toast.info('Select a focus group', 'Choose a completed focus group to analyze questions.');
                              return;
                            }
                            if (!isAskPending) {
                              setGraphAskFocusGroup(selectedFocusGroup.id);
                              setGraphAskStatus('loading', null);
                              setGraphAskResult(null);
                              runAskQuestion(suggestion.trim());
                            }
                          }}
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>

                    {isAskPending && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <SpinnerLogo className="h-4 w-4" />
                        Analyzing graph relationships...
                      </div>
                    )}

                    {askErrorMessage && !isAskPending && (
                      <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {askErrorMessage}
                      </div>
                    )}

                    {askResult && !isAskPending && (
                      <div className="space-y-3">
                        <div className="rounded-lg border border-border bg-muted/30 p-4">
                          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                            Answer
                          </h4>
                          <p className="text-sm leading-relaxed text-card-foreground">
                            {askResult.answer}
                          </p>
                        </div>

                        {askResult.insights.length > 0 && (
                          <div className="space-y-2">
                            <h5 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                              Supporting insights
                            </h5>
                            <div className="grid gap-2 md:grid-cols-2">
                              {askResult.insights.map((insight, index) => (
                                <div
                                  key={`${insight.title}-${index}`}
                                  className="rounded-md border border-border bg-background/80 p-3"
                                >
                                  <p className="text-sm font-medium text-card-foreground">
                                    {insight.title}
                                  </p>
                                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                                    {insight.detail}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Insights Panel */}
            <div className="space-y-6">
              <Tabs defaultValue="concepts" className="w-full">
                <TabsList className="bg-muted border border-border shadow-sm w-full">
                  <TabsTrigger value="concepts" className="flex-1">
                    <MessageCircle className="w-4 h-4 mr-2" />
                    Concepts
                  </TabsTrigger>
                  <TabsTrigger value="personas" className="flex-1">
                    <Users className="w-4 h-4 mr-2" />
                    Personas
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="concepts" className="space-y-4">
                  <Card className="bg-card border border-border">
                    <CardHeader>
                      <CardTitle className="text-card-foreground flex items-center gap-2">
                        <MessageCircle className="w-5 h-5 text-primary" />
                        Key Concepts
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {!selectedFocusGroup ? (
                        <p className="text-muted-foreground text-sm">
                          Select a completed focus group to see extracted concepts.
                        </p>
                      ) : graphLoading || isGraphFetching ? (
                        <div className="flex items-center justify-center py-6">
                          <SpinnerLogo className="w-6 h-6" />
                        </div>
                      ) : keyConcepts.length === 0 ? (
                        <p className="text-muted-foreground text-sm">No concepts extracted yet</p>
                      ) : (
                        keyConcepts.map((concept: any) => (
                          <div
                            key={concept.name}
                            className={`p-3 rounded-lg border cursor-pointer transition-colors ${selectedConcept === concept.name.toLowerCase()
                                ? 'border-primary bg-primary/10'
                                : 'border-border hover:border-primary/50'
                              }`}
                            onClick={() => setSelectedConcept(selectedConcept === concept.name.toLowerCase() ? null : concept.name.toLowerCase())}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="text-card-foreground font-medium">{concept.name}</h4>
                              <Badge variant="secondary" className="bg-muted text-muted-foreground">
                                {concept.frequency}
                              </Badge>
                            </div>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">Sentiment:</span>
                                <Badge
                                  variant="secondary"
                                  className={`${getSentimentBg(concept.sentiment)} ${getSentimentColor(concept.sentiment)} border-0`}
                                >
                                  {(concept.sentiment * 100).toFixed(0)}%
                                </Badge>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {concept.personas.length} personas
                              </span>
                            </div>
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="personas" className="space-y-4">
                  <Card className="bg-card border border-border">
                    <CardHeader>
                      <CardTitle className="text-card-foreground flex items-center gap-2">
                        <Users className="w-5 h-5 text-primary" />
                        Influential Personas
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {!selectedFocusGroup ? (
                        <p className="text-muted-foreground text-sm">
                          Select a completed focus group to review persona influence.
                        </p>
                      ) : graphLoading || isGraphFetching ? (
                        <div className="flex items-center justify-center py-6">
                          <SpinnerLogo className="w-6 h-6" />
                        </div>
                      ) : influentialPersonas.length === 0 ? (
                        <p className="text-muted-foreground text-sm">No personas analyzed yet</p>
                      ) : (
                        influentialPersonas.map((persona: any, index: number) => (
                          <div key={persona.id} className="p-3 rounded-lg border border-border">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="text-card-foreground font-medium">{persona.name}</h4>
                              <Badge variant="secondary" className="bg-primary/10 text-primary">
                                #{index + 1}
                              </Badge>
                            </div>
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Influence Score:</span>
                                <span className="text-card-foreground">{persona.influence}/100</span>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Connections:</span>
                                <span className="text-card-foreground">{persona.connections}</span>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Avg Sentiment:</span>
                                <Badge
                                  variant="secondary"
                                  className={`${getSentimentBg(persona.sentiment)} ${getSentimentColor(persona.sentiment)} border-0`}
                                >
                                  {(persona.sentiment * 100).toFixed(0)}%
                                </Badge>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
        </div>
      </TooltipProvider>
    </div>
  );
}
