import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import {
  Network,
  Users,
  MessageCircle,
  Brain,
  TrendingUp,
  Heart,
  Search,
  Filter,
  BarChart3,
  Eye,
  Target,
  Lightbulb,
  Zap,
  Loader2,
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { NetworkGraph } from '@/components/analysis/NetworkGraph';
import { projectsApi, graphApi } from '@/lib/api';

export function GraphAnalysis() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [graphFilter, setGraphFilter] = useState('all');

  // Fetch projects
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  // Auto-select first project
  const firstProject = projects[0];
  const activeProjectId = selectedProjectId || firstProject?.id;

  // Fetch graph data
  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ['graph-data', activeProjectId, graphFilter],
    queryFn: () => graphApi.getGraph(activeProjectId!, graphFilter),
    enabled: !!activeProjectId,
  });

  // Fetch influential personas
  const { data: influentialPersonas = [] } = useQuery({
    queryKey: ['influential-personas', activeProjectId],
    queryFn: () => graphApi.getInfluentialPersonas(activeProjectId!),
    enabled: !!activeProjectId,
  });

  // Fetch key concepts
  const { data: keyConcepts = [] } = useQuery({
    queryKey: ['key-concepts', activeProjectId],
    queryFn: () => graphApi.getKeyConcepts(activeProjectId!),
    enabled: !!activeProjectId,
  });

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
      setSelectedConcept(node.id);
    }
  };

  const resetFilters = () => {
    setSelectedConcept(null);
    setGraphFilter('all');
    setSearchQuery('');
  };

  return (
    <TooltipProvider>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Graph Analysis</h1>
            <p className="text-muted-foreground">
              Explore dynamic networks of personas, concepts, and emotions from your research
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={activeProjectId || ''} onValueChange={setSelectedProjectId}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.name}
                  </SelectItem>
                ))}
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
                    {graphLoading ? (
                      <div className="flex items-center justify-center h-full">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                      </div>
                    ) : graphData ? (
                      <NetworkGraph
                        data={graphData}
                        filter={graphFilter}
                        selectedConcept={selectedConcept}
                        onNodeClick={handleNodeClick}
                        className="w-full h-full"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <p className="text-muted-foreground">No graph data available. Run a focus group first.</p>
                      </div>
                    )}

                    {/* Active Filters */}
                    {(selectedConcept || graphFilter !== 'all') && (
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
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                      <Input
                        placeholder="Ask a question about your research data... (e.g., 'Who was most concerned about pricing?')"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                    <Button
                      className="bg-primary hover:bg-primary/90 text-primary-foreground"
                      disabled={!searchQuery.trim()}
                    >
                      <Brain className="w-4 h-4 mr-2" />
                      Analyze
                    </Button>
                  </div>
                  <div className="mt-4 text-sm text-muted-foreground">
                    Try: "Show me controversial topics" • "Who influences others the most?" • "What emotions are linked to pricing?"
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
                      {keyConcepts.length === 0 ? (
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
                      {influentialPersonas.length === 0 ? (
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
  );
}
