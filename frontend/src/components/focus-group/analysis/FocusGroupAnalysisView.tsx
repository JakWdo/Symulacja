import React, { Suspense, lazy } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart3, MessageSquare } from 'lucide-react';
import { AISummarySkeleton } from './AISummarySkeleton';
import { ResponsesSkeleton } from './ResponsesSkeleton';
import { RawResponsesTab } from './RawResponsesTab';
import type { Persona } from '@/types';

// Lazy load Results Analysis Tab
const ResultsAnalysisTab = lazy(() =>
  import('./ResultsAnalysisTab').then((module) => ({ default: module.ResultsAnalysisTab }))
);

interface FocusGroupAnalysisViewProps {
  focusGroupId: string;
  personas: Persona[];
  defaultTab?: 'ai-summary' | 'raw-responses';
  onTabChange?: (tab: string) => void;
}

/**
 * Main container z tab navigation dla "Wyniki i Analiza"
 *
 * Sub-taby:
 * - "Podsumowanie AI" - AI-powered analysis
 * - "Surowe Odpowiedzi" - Raw responses list
 */
export const FocusGroupAnalysisView: React.FC<FocusGroupAnalysisViewProps> = ({
  focusGroupId,
  personas,
  defaultTab = 'ai-summary',
  onTabChange,
}) => {
  const [activeTab, setActiveTab] = React.useState(defaultTab);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    onTabChange?.(tab);
  };

  return (
    <div className="w-full space-y-6">
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="bg-muted border border-border shadow-sm">
          <TabsTrigger
            value="ai-summary"
            className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            Podsumowanie AI
          </TabsTrigger>
          <TabsTrigger
            value="raw-responses"
            className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Surowe Odpowiedzi
          </TabsTrigger>
        </TabsList>

        {/* AI Summary Tab */}
        <TabsContent value="ai-summary" className="mt-6">
          <Suspense fallback={<AISummarySkeleton />}>
            <ResultsAnalysisTab focusGroupId={focusGroupId} />
          </Suspense>
        </TabsContent>

        {/* Raw Responses Tab */}
        <TabsContent value="raw-responses" className="mt-6">
          <Suspense fallback={<ResponsesSkeleton />}>
            <RawResponsesTab focusGroupId={focusGroupId} personas={personas} />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  );
};
