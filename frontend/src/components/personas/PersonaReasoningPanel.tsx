/**
 * PersonaReasoningPanel - Wyświetla szczegółowe reasoning persony
 *
 * Panel prezentuje edukacyjne wyjaśnienia:
 * - Demographics (always visible, compact)
 * - Top 3 Graph Insights (always visible)
 * - Orchestration brief (collapsible)
 * - Overall context Polski (collapsible)
 * - Allocation reasoning (collapsible)
 *
 * Output style: Edukacyjny, konwersacyjny, production-ready
 * UX: Progressive disclosure, collapsible sections, mobile-friendly
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Persona, PersonaReasoning } from '@/types';
import { analysisApi } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { AlertCircle, Lightbulb, ChevronDown, Users, Sparkles, Circle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

interface PersonaReasoningPanelProps {
  persona: Persona;
}

interface GraphInsight {
  type: string;
  magnitude?: string;
  confidence: 'high' | 'medium' | 'low';
  time_period?: string;
  source?: string;
  summary: string;
  why_matters?: string;
}

export function PersonaReasoningPanel({ persona }: PersonaReasoningPanelProps) {
  const [expanded, setExpanded] = useState({
    brief: false,
    allocation: false,
    allInsights: false,
  });

  const { data: reasoning, isLoading, error } = useQuery<PersonaReasoning>({
    queryKey: ['persona-reasoning', persona.id],
    queryFn: () => analysisApi.getPersonaReasoning(persona.id),
    staleTime: 10 * 60 * 1000, // 10 minut cache
  });

  // Get top 3 high-confidence insights
  const topInsights = useMemo(() => {
    if (!reasoning?.graph_insights) return [];
    const confidenceOrder: Record<string, number> = { high: 3, medium: 2, low: 1 };
    const sorted = [...reasoning.graph_insights].sort((a, b) => {
      return (confidenceOrder[b.confidence] || 0) - (confidenceOrder[a.confidence] || 0);
    });
    return sorted.slice(0, 3);
  }, [reasoning?.graph_insights]);

  const allInsights = useMemo(() => {
    if (!reasoning?.graph_insights) return [];
    return reasoning.graph_insights;
  }, [reasoning?.graph_insights]);

  const segmentContext = useMemo(() => {
    if (!reasoning) return null;
    return reasoning.segment_social_context || reasoning.overall_context || null;
  }, [reasoning]);

  // Validation: check if persona age matches segment
  // IMPORTANT: This hook must be called BEFORE any early returns (React Rules of Hooks)
  const isAgeConsistent = useMemo(() => {
    if (!reasoning?.demographics?.age_range || !persona.age) return true;

    const parseAgeRange = (range: string): [number, number] => {
      const match = range.match(/(\d+)-(\d+)/);
      if (!match) return [0, 100];
      return [parseInt(match[1]), parseInt(match[2])];
    };

    const [minAge, maxAge] = parseAgeRange(reasoning.demographics.age_range);
    return persona.age >= minAge && persona.age <= maxAge;
  }, [reasoning, persona]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          {error instanceof Error
            ? error.message
            : 'Błąd podczas ładowania reasoning data'}
        </AlertDescription>
      </Alert>
    );
  }

  // Check if reasoning is empty (no orchestration data)
  if (!reasoning || (!reasoning.orchestration_brief &&
                     reasoning.graph_insights.length === 0 &&
                     !reasoning.allocation_reasoning &&
                     !reasoning.overall_context)) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <div className="space-y-2">
            <p className="font-medium">Ta persona nie ma szczegółowego reasoning</p>
            <p className="text-sm text-muted-foreground">
              Persona została wygenerowana, ale orchestration service nie dodał szczegółowych wyjaśnień.
              Możliwe przyczyny:
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
              <li>Orchestration failował podczas generowania (sprawdź logi API)</li>
              <li>Gemini 2.5 Pro nie zwrócił poprawnego JSON</li>
              <li>Persona została wygenerowana przed włączeniem orchestration</li>
            </ul>
            <p className="text-sm font-medium mt-4">
              Rozwiązanie: Wygeneruj nowe persony aby zobaczyć pełne reasoning.
            </p>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  const renderInsight = (insight: GraphInsight, index: number) => (
    <div key={index} className="flex gap-3 text-sm">
      <Circle className="w-1.5 h-1.5 mt-1.5 flex-shrink-0 fill-current text-amber-600" />
      <div className="flex-1 space-y-1">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            {insight.magnitude && (
              <span className="font-bold text-amber-900 dark:text-amber-100 mr-2">
                {insight.magnitude}
              </span>
            )}
            <span className="text-foreground font-medium">
              {insight.summary}
            </span>
          </div>
          {insight.source && (
            <Badge variant="outline" className="text-[10px] shrink-0 border-amber-300 text-amber-700">
              {insight.source}
            </Badge>
          )}
        </div>
        {insight.why_matters && (
          <p className="text-xs text-muted-foreground leading-relaxed">
            {insight.why_matters}
          </p>
        )}
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          {insight.time_period && (
            <span>{insight.time_period}</span>
          )}
          {insight.confidence && (
            <>
              {insight.time_period && <span>•</span>}
              <Badge
                variant="outline"
                className={cn(
                  "text-[10px] h-4 px-1.5",
                  insight.confidence === 'high' && 'border-green-500 text-green-700',
                  insight.confidence === 'medium' && 'border-yellow-500 text-yellow-700',
                  insight.confidence === 'low' && 'border-gray-400 text-gray-600'
                )}
              >
                {insight.confidence === 'high' ? 'Wysoka pewność' :
                 insight.confidence === 'medium' ? 'Średnia pewność' : 'Niska pewność'}
              </Badge>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Validation Alert */}
      {!isAgeConsistent && (
        <Alert className="border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20">
          <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
          <AlertDescription className="text-yellow-900 dark:text-yellow-100">
            Uwaga: Wiek persony ({persona.age}) nie pasuje do zakresu grupy demograficznej
            ({reasoning.demographics?.age_range}). To może oznaczać problem w orchestration.
          </AlertDescription>
        </Alert>
      )}

      {/* === HERO: SEGMENT SPOŁECZEŃSTWA === */}
      {reasoning.segment_name && (
        <Card className="bg-gradient-to-br from-primary/5 via-background to-background border-2 border-primary/20">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Users className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                  Segment Społeczeństwa
                </p>
                <h2 className="text-2xl font-bold text-foreground">
                  {reasoning.segment_name}
                </h2>
              </div>
            </div>
            {reasoning.segment_description && (
              <p className="text-sm text-muted-foreground mt-2">
                {reasoning.segment_description}
              </p>
            )}
          </CardHeader>

          <CardContent>
            {segmentContext && (
              <div className="prose prose-sm dark:prose-invert max-w-none mb-4">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {segmentContext}
                </ReactMarkdown>
              </div>
            )}
            {/* Demographics Grid */}
            {reasoning.demographics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-muted/30 rounded-lg">
                {Object.entries(reasoning.demographics).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <p className="text-xs text-muted-foreground capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-sm font-semibold text-foreground">
                      {String(value)}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Segment Characteristics */}
            {reasoning.segment_characteristics && reasoning.segment_characteristics.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">
                  Kluczowe cechy segmentu
                </p>
                <div className="flex flex-wrap gap-2">
                  {reasoning.segment_characteristics.map((characteristic, idx) => (
                    <Badge
                      key={idx}
                      variant="outline"
                      className="border-primary/40 text-primary bg-primary/5 hover:bg-primary/10 transition-colors text-sm px-3 py-1"
                    >
                      {characteristic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 2. Top 3 Graph Insights - Always visible */}
      {topInsights.length > 0 && (
        <Card className="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-amber-600" />
              <CardTitle className="text-base font-semibold text-amber-900 dark:text-amber-100">
                Kluczowe Spostrzeżenia AI
              </CardTitle>
            </div>
            <CardDescription className="text-amber-700 dark:text-amber-300">
              Najważniejsze dane z raportów o polskim społeczeństwie
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {topInsights.map((insight, idx) => renderInsight(insight, idx))}

            {/* Show All Insights button */}
            {!expanded.allInsights && allInsights.length > 3 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setExpanded(prev => ({ ...prev, allInsights: true }))}
                className="w-full mt-4 border-amber-300 text-amber-700 hover:bg-amber-100 dark:hover:bg-amber-900/40"
              >
                Pokaż wszystkie wskaźniki ({allInsights.length})
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            )}

            {/* All remaining insights */}
            {expanded.allInsights && allInsights.length > 3 && (
              <div className="space-y-4 mt-4 pt-4 border-t border-amber-200 dark:border-amber-800">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-3">
                  Pozostałe wskaźniki:
                </p>
                {allInsights.slice(3).map((insight, idx) => renderInsight(insight, idx + 3))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpanded(prev => ({ ...prev, allInsights: false }))}
                  className="w-full mt-2 text-amber-700 hover:bg-amber-100 dark:hover:bg-amber-900/40"
                >
                  <ChevronDown className="mr-2 h-4 w-4 rotate-180" />
                  Zwiń wskaźniki
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 3. Orchestration Brief - Collapsible, collapsed by default */}
      {reasoning.orchestration_brief && (
        <Card>
          <Collapsible
            open={expanded.brief}
            onOpenChange={(open) => setExpanded(prev => ({ ...prev, brief: open }))}
          >
            <CardHeader className="pb-3">
              <CollapsibleTrigger asChild>
                <button
                  className="flex w-full items-center justify-between text-left hover:opacity-80 transition-opacity"
                  aria-label="Pokaż szczegółową analizę"
                >
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-primary" />
                    Dlaczego {persona.full_name}?
                  </CardTitle>
                  <ChevronDown
                    className={cn(
                      "h-5 w-5 transition-transform duration-200 text-muted-foreground",
                      expanded.brief && "rotate-180"
                    )}
                  />
                </button>
              </CollapsibleTrigger>
              <CardDescription>
                Szczegółowa analiza demograficzna i społeczna
              </CardDescription>
            </CardHeader>

            <CardContent>
              {!expanded.brief && (
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {reasoning.orchestration_brief?.slice(0, 180)}...
                </p>
              )}

              <CollapsibleContent className="space-y-2">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {reasoning.orchestration_brief}
                  </ReactMarkdown>
                </div>
              </CollapsibleContent>
            </CardContent>
          </Collapsible>
        </Card>
      )}

      {/* 4. Allocation Reasoning - Collapsible, collapsed by default */}
      {reasoning.allocation_reasoning && (
        <Card>
          <Collapsible
            open={expanded.allocation}
            onOpenChange={(open) => setExpanded(prev => ({ ...prev, allocation: open }))}
          >
            <CardHeader className="pb-3">
              <CollapsibleTrigger asChild>
                <button
                  className="flex w-full items-center justify-between text-left hover:opacity-80 transition-opacity"
                  aria-label="Pokaż uzasadnienie alokacji"
                >
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    Uzasadnienie Alokacji
                  </CardTitle>
                  <ChevronDown
                    className={cn(
                      "h-5 w-5 transition-transform duration-200 text-muted-foreground",
                      expanded.allocation && "rotate-180"
                    )}
                  />
                </button>
              </CollapsibleTrigger>
              <CardDescription>
                Dlaczego ta grupa demograficzna i dlaczego tyle person?
              </CardDescription>
            </CardHeader>

            <CardContent>
              {!expanded.allocation && (
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {reasoning.allocation_reasoning?.slice(0, 180)}...
                </p>
              )}

              <CollapsibleContent className="space-y-2">
                <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {reasoning.allocation_reasoning}
                  </ReactMarkdown>
                </div>
              </CollapsibleContent>
            </CardContent>
          </Collapsible>
        </Card>
      )}
    </div>
  );
}
