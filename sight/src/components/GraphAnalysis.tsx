import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

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
  Zap
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { NetworkGraph } from './NetworkGraph';

interface GraphAnalysisProps {}

// Mock data for demonstration
const mockProjects = [
  { id: 1, name: "Mobile App Launch Research" },
  { id: 2, name: "Product Development Study" },
  { id: 3, name: "Marketing Research" }
];

const mockKeyConcepts = [
  { 
    name: "Price", 
    frequency: 127, 
    sentiment: 0.3, 
    personas: ["Sarah Johnson", "Emily Rodriguez", "David Kim"],
    relatedTopics: ["Affordability", "Value", "Budget"]
  },
  { 
    name: "Design", 
    frequency: 89, 
    sentiment: 0.8, 
    personas: ["David Kim", "Michael Chen"],
    relatedTopics: ["Visual Appeal", "User Interface", "Aesthetics"]
  },
  { 
    name: "Security", 
    frequency: 76, 
    sentiment: 0.6, 
    personas: ["Michael Chen", "Sarah Johnson"],
    relatedTopics: ["Privacy", "Data Protection", "Trust"]
  },
  { 
    name: "User Experience", 
    frequency: 64, 
    sentiment: 0.9, 
    personas: ["David Kim", "Sarah Johnson"],
    relatedTopics: ["Usability", "Navigation", "Accessibility"]
  },
  { 
    name: "Performance", 
    frequency: 52, 
    sentiment: 0.4, 
    personas: ["Michael Chen", "Emily Rodriguez"],
    relatedTopics: ["Speed", "Reliability", "Efficiency"]
  }
];

const mockInfluentialPersonas = [
  { 
    name: "Sarah Johnson", 
    influence: 94, 
    connections: 23, 
    sentiment: 0.7,
    keyTopics: ["Price", "Security", "User Experience"]
  },
  { 
    name: "Michael Chen", 
    influence: 87, 
    connections: 19, 
    sentiment: 0.8,
    keyTopics: ["Design", "Security", "Performance"]
  },
  { 
    name: "David Kim", 
    influence: 76, 
    connections: 15, 
    sentiment: 0.9,
    keyTopics: ["Design", "User Experience"]
  },
  { 
    name: "Emily Rodriguez", 
    influence: 68, 
    connections: 12, 
    sentiment: 0.6,
    keyTopics: ["Price", "Performance"]
  }
];

const mockEmotions = [
  { emotion: "Satisfaction", count: 145, percentage: 32 },
  { emotion: "Excitement", count: 89, percentage: 20 },
  { emotion: "Concern", count: 76, percentage: 17 },
  { emotion: "Frustration", count: 64, percentage: 14 },
  { emotion: "Curiosity", count: 52, percentage: 12 },
  { emotion: "Disappointment", count: 23, percentage: 5 }
];

const mockInsights = [
  {
    type: "controversy",
    title: "Price Polarization Detected",
    description: "The concept 'pricing' creates strong positive sentiment among budget-conscious personas but negative sentiment among premium users.",
    affected: ["Emily Rodriguez", "Sarah Johnson"]
  },
  {
    type: "influence",
    title: "Design Leader Identified",
    description: "David Kim's positive comments about UX consistently influence other participants' opinions in the same direction.",
    affected: ["Sarah Johnson", "Michael Chen"]
  },
  {
    type: "pattern",
    title: "Security-Performance Correlation",
    description: "Personas concerned about security typically also express performance-related worries.",
    affected: ["Michael Chen", "Emily Rodriguez"]
  }
];

export function GraphAnalysis({}: GraphAnalysisProps) {
  const [selectedProject, setSelectedProject] = useState("1");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [graphFilter, setGraphFilter] = useState("all");

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "text-green-600";
    if (sentiment >= 0.4) return "text-amber-600";
    return "text-red-600";
  };

  const getSentimentBg = (sentiment: number) => {
    if (sentiment >= 0.7) return "bg-green-100";
    if (sentiment >= 0.4) return "bg-amber-100";
    return "bg-red-100";
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'controversy': return <Target className="w-5 h-5 text-red-600" />;
      case 'influence': return <TrendingUp className="w-5 h-5 text-blue-600" />;
      case 'pattern': return <Lightbulb className="w-5 h-5 text-amber-600" />;
      default: return <Zap className="w-5 h-5 text-purple-600" />;
    }
  };

  const handleNodeClick = (node: any) => {
    // Handle node click - could expand details, filter, etc.
    console.log('Node clicked:', node);
    if (node.type === 'concept') {
      setSelectedConcept(node.id);
    }
  };

  const resetFilters = () => {
    setSelectedConcept(null);
    setGraphFilter('all');
    setSearchQuery('');
  };

  const handleAnalyzeQuery = () => {
    if (searchQuery.trim()) {
      // Mock analysis based on query content
      const query = searchQuery.toLowerCase();
      if (query.includes('price') || query.includes('pricing')) {
        setSelectedConcept('price');
        setGraphFilter('pricing');
      } else if (query.includes('design')) {
        setSelectedConcept('design');
        setGraphFilter('design');
      } else if (query.includes('influence')) {
        setGraphFilter('influence');
      }
      // In real implementation, this would call API endpoint
    }
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
          <Select value={selectedProject} onValueChange={setSelectedProject}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              {mockProjects.map((project) => (
                <SelectItem key={project.id} value={project.id.toString()}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Main Content */}
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
                    className={showFilters ? "bg-primary/10 border-primary" : ""}
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
                      <SelectItem value="controversy">Controversial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters Panel */}
              {showFilters && (
                <div className="mb-4 p-4 bg-muted/50 rounded-lg border border-border">
                  <h4 className="text-sm text-card-foreground mb-3">Filter Options</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs text-muted-foreground mb-2 block">Sentiment Range</label>
                      <Select defaultValue="all">
                        <SelectTrigger className="h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Sentiments</SelectItem>
                          <SelectItem value="positive">Positive (70%+)</SelectItem>
                          <SelectItem value="neutral">Neutral (30-70%)</SelectItem>
                          <SelectItem value="negative">Negative (0-30%)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground mb-2 block">Node Types</label>
                      <Select defaultValue="all">
                        <SelectTrigger className="h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Types</SelectItem>
                          <SelectItem value="personas">Personas Only</SelectItem>
                          <SelectItem value="concepts">Concepts Only</SelectItem>
                          <SelectItem value="emotions">Emotions Only</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-4">
                    <Button variant="outline" size="sm" onClick={resetFilters}>
                      Reset All
                    </Button>
                    <Button size="sm" className="bg-primary hover:bg-primary/90 text-primary-foreground">
                      Apply Filters
                    </Button>
                  </div>
                </div>
              )}
              
              {/* Interactive Graph Visualization */}
              <div className="h-[500px] bg-muted/30 rounded-lg border border-border relative overflow-hidden">
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
                
                <NetworkGraph 
                  filter={graphFilter}
                  selectedConcept={selectedConcept}
                  onNodeClick={handleNodeClick}
                  className="w-full h-full"
                />
                
                {/* Instructions overlay */}
                <div className="absolute top-4 right-4 bg-card/90 border border-border rounded p-2 text-xs text-muted-foreground z-10">
                  <div>Click nodes to explore</div>
                  <div>Drag to pan • Scroll to zoom</div>
                </div>
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
                  onClick={handleAnalyzeQuery}
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

          {/* AI Insights */}
          <Card className="bg-card border border-border mt-6">
            <CardHeader>
              <CardTitle className="text-foreground flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                AI Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {mockInsights.map((insight, index) => (
                  <div key={index} className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors">
                    <div className="flex items-start gap-3">
                      {getInsightIcon(insight.type)}
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm text-card-foreground mb-2 leading-tight">{insight.title}</h4>
                        <p className="text-xs text-muted-foreground mb-3 leading-relaxed">{insight.description}</p>
                        <div className="flex flex-wrap gap-1">
                          {insight.affected.map((persona) => (
                            <Badge key={persona} variant="outline" className="text-xs">
                              {persona}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Insights Panel */}
        <div className="space-y-6">
          <Tabs defaultValue="concepts" className="w-full">
            <TabsList className="bg-muted border border-border shadow-sm">
              <TabsTrigger value="concepts" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
                <MessageCircle className="w-4 h-4 mr-2" />
                Concepts
              </TabsTrigger>
              <TabsTrigger value="personas" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
                <Users className="w-4 h-4 mr-2" />
                Personas
              </TabsTrigger>
              <TabsTrigger value="emotions" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
                <Heart className="w-4 h-4 mr-2" />
                Emotions
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
                  {mockKeyConcepts.map((concept, index) => (
                    <div 
                      key={concept.name}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedConcept === concept.name.toLowerCase() 
                          ? 'border-primary bg-primary/10' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => setSelectedConcept(selectedConcept === concept.name.toLowerCase() ? null : concept.name.toLowerCase())}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-card-foreground">{concept.name}</h4>
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
                  ))}
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
                  {mockInfluentialPersonas.map((persona, index) => (
                    <div key={persona.name} className="p-3 rounded-lg border border-border">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-card-foreground">{persona.name}</h4>
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
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="emotions" className="space-y-4">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-card-foreground flex items-center gap-2">
                    <Heart className="w-5 h-5 text-primary" />
                    Emotion Cloud
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {mockEmotions.map((emotion) => (
                    <div key={emotion.emotion} className="flex items-center justify-between p-2 rounded">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ 
                            backgroundColor: `hsl(${120 - (emotion.percentage * 2)}, 70%, 50%)` 
                          }}
                        ></div>
                        <span className="text-card-foreground">{emotion.emotion}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-card-foreground">{emotion.count}</div>
                        <div className="text-xs text-muted-foreground">{emotion.percentage}%</div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
    </TooltipProvider>
  );
}