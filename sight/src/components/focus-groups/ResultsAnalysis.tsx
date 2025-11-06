import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Button } from '../ui/button';
import { Brain, FileText, RotateCcw } from 'lucide-react';
import { AISummarySection } from './AISummarySection';
import { RawResponsesSection } from './RawResponsesSection';
import { ResultsEmpty } from './ResultsEmpty';
import { ResultsLoading } from './ResultsLoading';
import { ResultsError } from './ResultsError';

interface ResultsAnalysisProps {
  discussionComplete: boolean;
  aiSummaryGenerated: boolean;
  isLoading?: boolean;
  error?: string | null;
  onGenerateSummary?: () => void;
  onRegenerateSummary?: () => void;
  onStartDiscussion?: () => void;
  metadata?: {
    model: string;
    generatedAt: string;
    responseCount: number;
    participantCount: number;
    questionCount: number;
  };
}

export function ResultsAnalysis({
  discussionComplete,
  aiSummaryGenerated,
  isLoading = false,
  error = null,
  onGenerateSummary,
  onRegenerateSummary,
  onStartDiscussion,
  metadata
}: ResultsAnalysisProps) {
  const [activeView, setActiveView] = useState<'summary' | 'responses'>('summary');

  // Empty state - no discussion run yet
  if (!discussionComplete) {
    return <ResultsEmpty onStartDiscussion={onStartDiscussion} />;
  }

  // Error state
  if (error) {
    return <ResultsError error={error} onRetry={onGenerateSummary} />;
  }

  // Loading state - discussion complete, generating AI summary
  if (discussionComplete && !aiSummaryGenerated && isLoading) {
    return <ResultsLoading />;
  }

  // Discussion complete but AI summary not generated yet
  if (discussionComplete && !aiSummaryGenerated) {
    return (
      <div className="bg-card border border-border rounded-lg shadow-sm">
        <div className="text-center py-16 px-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand-orange/10 mb-6">
            <Brain className="w-8 h-8 text-brand-orange" />
          </div>
          <h3 className="text-foreground mb-2">Discussion Complete</h3>
          <p className="text-muted-foreground max-w-md mx-auto mb-8">
            The focus group simulation has finished successfully. Generate AI insights to analyze the results and discover key findings.
          </p>
          <Button 
            onClick={onGenerateSummary}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            <Brain className="w-4 h-4 mr-2" />
            Generate AI Summary
          </Button>
        </div>
      </div>
    );
  }

  // Results view - AI summary generated
  return (
    <div className="space-y-6">
      {/* Header with metadata and actions */}
      <div className="bg-card border border-border rounded-lg shadow-sm p-6">
        <div className="flex items-start justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-foreground">Analysis Results</h2>
              <div className="px-2 py-1 bg-chart-1/10 border border-chart-1/20 rounded text-chart-1 text-xs">
                Completed
              </div>
            </div>
            {metadata && (
              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <span className="text-foreground">{metadata.participantCount}</span> participants
                </div>
                <span>•</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-foreground">{metadata.questionCount}</span> questions
                </div>
                <span>•</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-foreground">{metadata.responseCount}</span> responses
                </div>
                <span>•</span>
                <div className="flex items-center gap-1.5">
                  Generated {new Date(metadata.generatedAt).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
            )}
          </div>
          <Button 
            variant="outline"
            onClick={onRegenerateSummary}
            className="shrink-0"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Regenerate
          </Button>
        </div>
      </div>

      {/* View Tabs */}
      <Tabs value={activeView} onValueChange={(v) => setActiveView(v as 'summary' | 'responses')} className="w-full">
        <TabsList className="bg-muted border border-border shadow-sm">
          <TabsTrigger 
            value="summary" 
            className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm"
          >
            <Brain className="w-4 h-4 mr-2" />
            AI Summary
          </TabsTrigger>
          <TabsTrigger 
            value="responses" 
            className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm"
          >
            <FileText className="w-4 h-4 mr-2" />
            Raw Responses
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-6">
          <AISummarySection metadata={metadata} />
        </TabsContent>

        <TabsContent value="responses" className="mt-6">
          <RawResponsesSection />
        </TabsContent>
      </Tabs>
    </div>
  );
}
