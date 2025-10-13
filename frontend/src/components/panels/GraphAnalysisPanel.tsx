import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Filter, TrendingUp, Brain, AlertCircle } from 'lucide-react';
import { KnowledgeGraph3D } from '@/components/graph/KnowledgeGraph3D';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import {
  useGraphData,
  useKeyConcepts,
  useInfluentialPersonas,
  useControversialConcepts,
  useEmotionDistribution,
  useTraitCorrelations
} from '@/hooks/useGraphData';
import type { GraphNode } from '@/types';
import { Logo } from '@/components/ui/Logo';

interface GraphAnalysisPanelProps {
  focusGroupId: string;
}

export function GraphAnalysisPanel({ focusGroupId }: GraphAnalysisPanelProps) {
  const [filterType, setFilterType] = useState<'positive' | 'negative' | 'influence' | undefined>();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Fetch all graph data (hooks must be called unconditionally)
  const { data: graphData, isLoading: graphLoading, error: graphError } = useGraphData(focusGroupId, filterType);
  const { data: keyConcepts, isLoading: conceptsLoading } = useKeyConcepts(focusGroupId);
  const { data: influentialPersonas, isLoading: influencersLoading } = useInfluentialPersonas(focusGroupId);
  const { data: controversialConcepts, isLoading: controversialLoading } = useControversialConcepts(focusGroupId);
  const { data: emotions, isLoading: emotionsLoading } = useEmotionDistribution(focusGroupId);
  const { data: correlations, isLoading: correlationsLoading } = useTraitCorrelations(focusGroupId);

  // Validate focusGroupId after hooks
  if (!focusGroupId) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <AlertCircle className="w-16 h-16 text-destructive mb-4" />
        <h3 className="text-lg font-medium text-foreground mb-2">Invalid Focus Group</h3>
        <p className="text-muted-foreground text-center max-w-md">
          No focus group ID provided.
        </p>
      </div>
    );
  }

  const isLoading = graphLoading || conceptsLoading || influencersLoading;

  if (graphError) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <AlertCircle className="w-16 h-16 text-destructive mb-4" />
        <h3 className="text-lg font-medium text-foreground mb-2">Failed to Load Graph</h3>
        <p className="text-muted-foreground text-center max-w-md">
          The knowledge graph could not be loaded. Make sure the focus group has completed and the graph has been built.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Logo className="w-12 h-12 mb-4" spinning />
        <p className="text-muted-foreground">Loading knowledge graph...</p>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4">
      {/* Main Graph Visualization */}
      <div className="flex-1 flex flex-col gap-4">
        {/* Filter Controls */}
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">Filter View:</span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={filterType === undefined ? 'default' : 'outline'}
                  onClick={() => setFilterType(undefined)}
                  className={filterType === undefined ? 'bg-[#F27405] hover:bg-[#F27405]/90' : ''}
                >
                  All
                </Button>
                <Button
                  size="sm"
                  variant={filterType === 'positive' ? 'default' : 'outline'}
                  onClick={() => setFilterType('positive')}
                  className={filterType === 'positive' ? 'bg-green-600 hover:bg-green-700' : ''}
                >
                  Positive
                </Button>
                <Button
                  size="sm"
                  variant={filterType === 'negative' ? 'default' : 'outline'}
                  onClick={() => setFilterType('negative')}
                  className={filterType === 'negative' ? 'bg-red-600 hover:bg-red-700' : ''}
                >
                  Negative
                </Button>
                <Button
                  size="sm"
                  variant={filterType === 'influence' ? 'default' : 'outline'}
                  onClick={() => setFilterType('influence')}
                  className={filterType === 'influence' ? 'bg-purple-600 hover:bg-purple-700' : ''}
                >
                  High Influence
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3D Graph */}
        <Card className="flex-1 bg-card border border-border overflow-hidden">
          <div className="h-full">
            <ErrorBoundary
              fallback={
                <div className="flex items-center justify-center h-full">
                  <div className="text-center p-8">
                    <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">Graph Rendering Error</h3>
                    <p className="text-muted-foreground mb-4">
                      Failed to render the 3D graph. Try refreshing the page.
                    </p>
                    <Button onClick={() => window.location.reload()}>
                      Refresh Page
                    </Button>
                  </div>
                </div>
              }
            >
              {graphData && graphData.nodes && graphData.nodes.length > 0 ? (
                <KnowledgeGraph3D
                  graphData={graphData}
                  onNodeClick={(node) => setSelectedNode(node)}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center p-8">
                    <Brain className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">No Graph Data</h3>
                    <p className="text-muted-foreground">
                      The knowledge graph is empty. This may happen if the focus group has just completed.
                    </p>
                  </div>
                </div>
              )}
            </ErrorBoundary>
          </div>
        </Card>

        {/* Legend */}
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#0ea5e9]" />
                <span className="text-muted-foreground">Personas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#8b5cf6]" />
                <span className="text-muted-foreground">Concepts</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
                <span className="text-muted-foreground">Emotions</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#10b981]" />
                <span className="text-muted-foreground">Positive Sentiment</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
                <span className="text-muted-foreground">Negative Sentiment</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights Sidebar */}
      <div className="w-96 flex flex-col gap-4 overflow-y-auto">
        {/* Selected Node Info */}
        {selectedNode && (
          <Card className="bg-card border border-[#F27405] shadow-lg">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Brain className="w-4 h-4 text-[#F27405]" />
                Selected Node
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <span className="text-xs text-muted-foreground">Type:</span>
                <Badge className="ml-2 capitalize">{selectedNode.type}</Badge>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Name:</span>
                <p className="text-sm font-medium text-foreground">
                  {selectedNode.name || selectedNode.label || selectedNode.id}
                </p>
              </div>
              {selectedNode.sentiment !== undefined && (
                <div>
                  <span className="text-xs text-muted-foreground">Sentiment:</span>
                  <p className="text-sm font-medium text-foreground">
                    {selectedNode.sentiment > 0 ? '+' : ''}{(selectedNode.sentiment * 100).toFixed(0)}%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Key Concepts */}
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-sm">Key Concepts</CardTitle>
            <p className="text-xs text-muted-foreground">Most frequently mentioned topics</p>
          </CardHeader>
          <CardContent>
            {conceptsLoading ? (
              <div className="flex justify-center py-4">
                <Logo className="w-6 h-6" spinning />
              </div>
            ) : keyConcepts && keyConcepts.length > 0 ? (
              <div className="space-y-2">
                {keyConcepts.slice(0, 5).map((concept: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-muted rounded">
                    <span className="text-sm font-medium text-foreground">{concept.name}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {concept.frequency}×
                      </Badge>
                      <div
                        className={`w-2 h-2 rounded-full ${
                          concept.sentiment > 0.5 ? 'bg-green-500' :
                          concept.sentiment < -0.3 ? 'bg-red-500' : 'bg-gray-500'
                        }`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No concepts found</p>
            )}
          </CardContent>
        </Card>

        {/* Influential Personas */}
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Influential Personas
            </CardTitle>
            <p className="text-xs text-muted-foreground">Most connected participants</p>
          </CardHeader>
          <CardContent>
            {influencersLoading ? (
              <div className="flex justify-center py-4">
                <Logo className="w-6 h-6" spinning />
              </div>
            ) : influentialPersonas && influentialPersonas.length > 0 ? (
              <div className="space-y-2">
                {influentialPersonas.slice(0, 5).map((persona: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-muted rounded">
                    <span className="text-sm font-medium text-foreground truncate">
                      {persona.name}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {persona.connections} links
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data available</p>
            )}
          </CardContent>
        </Card>

        {/* Controversial Topics */}
        {!controversialLoading && controversialConcepts && controversialConcepts.length > 0 && (
          <Card className="bg-card border border-amber-500">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500" />
                Controversial Topics
              </CardTitle>
              <p className="text-xs text-muted-foreground">Polarizing concepts</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {controversialConcepts.slice(0, 3).map((concept: any, idx: number) => (
                  <div key={idx} className="p-3 bg-muted rounded-lg space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-foreground">{concept.concept}</span>
                      <Badge variant="outline" className="bg-amber-500/10 text-amber-700 border-amber-500">
                        {(concept.polarization * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-muted-foreground">{concept.supporters.length} support</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                        <span className="text-muted-foreground">{concept.critics.length} oppose</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Emotion Distribution */}
        {!emotionsLoading && emotions && emotions.length > 0 && (
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-sm">Emotion Distribution</CardTitle>
              <p className="text-xs text-muted-foreground">Emotional responses</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {emotions.slice(0, 5).map((emotion: any, idx: number) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-foreground">{emotion.emotion}</span>
                      <span className="text-muted-foreground">{emotion.percentage.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#F27405]"
                        style={{ width: `${emotion.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Age Correlations */}
        {!correlationsLoading && correlations && correlations.length > 0 && (
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-sm">Age Group Differences</CardTitle>
              <p className="text-xs text-muted-foreground">Opinion gaps by age</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {correlations.slice(0, 3).map((corr: any, idx: number) => (
                  <div key={idx} className="p-2 bg-muted rounded space-y-1">
                    <p className="text-sm font-medium text-foreground">{corr.concept}</p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Young: {corr.young_sentiment ? (corr.young_sentiment > 0 ? '+' : '') + (corr.young_sentiment * 100).toFixed(0) + '%' : 'N/A'}</span>
                      <span>Senior: {corr.senior_sentiment ? (corr.senior_sentiment > 0 ? '+' : '') + (corr.senior_sentiment * 100).toFixed(0) + '%' : 'N/A'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
