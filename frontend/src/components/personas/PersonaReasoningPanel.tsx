/**
 * PersonaReasoningPanel - Wyświetla szczegółowe reasoning persony
 *
 * Panel prezentuje informacje o segmencie społecznym:
 * - Segment społeczny (nazwa, demografia, cechy, opis segmentu)
 * - Top 3 Graph Insights (najważniejsze dane z raportów)
 * - Allocation reasoning (dlaczego tyle person w tej grupie)
 *
 * Output style: Edukacyjny, konwersacyjny, production-ready
 * UX: Czytelna struktura, lepsze formatowanie markdown
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
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
import { AlertCircle, ChevronDown, Users, Sparkles, Circle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { normalizeMarkdown } from '@/lib/markdown';

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
  const { t } = useTranslation('personas');

  const [expanded, setExpanded] = useState({
    allocation: false,
    allInsights: false,
  });

  const { data: reasoning, isLoading, error } = useQuery<PersonaReasoning>({
    queryKey: ['persona-reasoning', persona.id],
    queryFn: () => analysisApi.getPersonaReasoning(persona.id),
    staleTime: 10 * 60 * 1000, // 10 minut cache
  });

  const personaStory = persona.background_story?.trim() ?? '';

  // Funkcja do tłumaczenia kluczy demografii
  const getDemographicLabel = (key: string): string => {
    const mapping: Record<string, string> = {
      'age': 'age',
      'age_range': 'ageRange',
      'gender': 'gender',
      'location': 'location',
      'education': 'education',
      'income': 'income',
      'income_range': 'incomeRange',
      'occupation': 'occupation',
    };
    const translationKey = mapping[key] || key;
    return t(`details.reasoning.demographicLabels.${translationKey}`, { defaultValue: key.replace(/_/g, ' ') });
  };

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
            : t('details.reasoning.error')}
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
      <Alert className="border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10">
        <AlertCircle className="h-4 w-4 text-yellow-600" />
        <AlertDescription className="text-yellow-800 dark:text-yellow-200">
          <div className="space-y-3">
            <p className="font-semibold text-base">Ta persona nie ma szczegółowego reasoning</p>
            <p className="text-sm">
              Persona została wygenerowana, ale orchestration service nie dodał szczegółowych wyjaśnień.
            </p>

            <div className="text-sm">
              <p className="font-medium mb-2">Możliwe przyczyny:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Orchestration był wyłączony podczas generowania (<code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded text-xs">ORCHESTRATION_ENABLED=false</code>)</li>
                <li>Wystąpił błąd połączenia z Neo4j (Graph RAG niedostępny)</li>
                <li>Timeout podczas tworzenia briefów segmentów (&gt;90s)</li>
                <li>Persona została wygenerowana z <code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded text-xs">use_rag=false</code></li>
              </ul>
            </div>

            <div className="text-sm border-t border-yellow-200 dark:border-yellow-700 pt-3 mt-3">
              <p className="font-medium mb-2">🔧 Rozwiązanie:</p>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Sprawdź logi serwera: <code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded text-xs">docker-compose logs api | grep Orchestration</code></li>
                <li>Sprawdź czy Neo4j działa: <code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded text-xs">docker-compose ps neo4j</code></li>
                <li>Sprawdź <code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded text-xs">.env</code>: Upewnij się że <code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded text-xs">ORCHESTRATION_ENABLED=true</code></li>
                <li className="font-medium">Wygeneruj persony ponownie aby zobaczyć pełne reasoning</li>
              </ol>
            </div>

            <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-2">
              💡 Więcej informacji: CLAUDE.md → "Troubleshooting: Brak Reasoning w Personach"
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
                {t(`details.reasoning.insightsSection.confidenceLevels.${insight.confidence}`)}
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
            {t('details.reasoning.ageInconsistency', {
              personaAge: persona.age,
              segmentAge: reasoning.demographics?.age_range
            })}
          </AlertDescription>
        </Alert>
      )}

      {/* === HERO: SEGMENT SPOŁECZNY === */}
      {reasoning.segment_name && (
        <Card className="bg-card border-2 border-primary/20 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-primary/10 rounded-figma-inner">
                <Users className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                  {t('details.reasoning.segmentSection.title')}
                </p>
                <h2 className="text-2xl font-bold text-foreground">
                  {reasoning.segment_name}
                </h2>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {/* Demographics Grid */}
            {reasoning.demographics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-muted/30 rounded-figma-inner">
                {Object.entries(reasoning.demographics).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      {getDemographicLabel(key)}
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
                  {t('details.reasoning.segmentSection.characteristicsTitle')}
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

            {/* Opis segmentu (orchestration_brief) */}
            {(() => {
              const orchestrationBrief = reasoning?.orchestration_brief?.trim() ?? '';
              if (!orchestrationBrief) return null;
              if (personaStory && orchestrationBrief === personaStory) return null;

              return (
                <div className="mt-6 space-y-3">
                  <h3 className="text-sm font-bold uppercase tracking-wide text-foreground">
                    {t('details.reasoning.segmentSection.descriptionTitle')}
                  </h3>
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        strong: ({children}) => <strong className="font-bold text-foreground">{children}</strong>,
                        em: ({children}) => <em className="italic text-foreground/90">{children}</em>,
                        h3: ({children}) => <h3 className="text-base font-bold mt-4 mb-2 text-foreground">{children}</h3>,
                        p: ({children}) => <p className="mb-3 leading-relaxed">{children}</p>,
                      }}
                    >
                      {normalizeMarkdown(orchestrationBrief)}
                    </ReactMarkdown>
                  </div>
                </div>
              );
            })()}
          </CardContent>
        </Card>
      )}

      {/* 2. Top 3 Graph Insights - Always visible */}
      {topInsights.length > 0 && (
        <Card className="bg-muted/30 border-border">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">
                {t('details.reasoning.insightsSection.title')}
              </CardTitle>
            </div>
            <CardDescription className="text-muted-foreground">
              {t('details.reasoning.insightsSection.subtitle')}
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
                className="w-full mt-4 border-primary text-primary hover:bg-primary/10"
              >
                {t('details.reasoning.insightsSection.showAll', { count: allInsights.length })}
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            )}

            {/* All remaining insights */}
            {expanded.allInsights && allInsights.length > 3 && (
              <div className="space-y-4 mt-4 pt-4 border-t border-border">
                <p className="text-sm font-medium text-foreground mb-3">
                  {t('details.reasoning.insightsSection.remaining')}
                </p>
                {allInsights.slice(3).map((insight, idx) => renderInsight(insight, idx + 3))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpanded(prev => ({ ...prev, allInsights: false }))}
                  className="w-full mt-2 text-primary hover:bg-primary/10"
                >
                  <ChevronDown className="mr-2 h-4 w-4 rotate-180" />
                  {t('details.reasoning.insightsSection.showLess')}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}


      {/* Allocation Reasoning - Collapsible, collapsed by default */}
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
                  aria-label={t('details.reasoning.allocationSection.toggleLabel')}
                >
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    {t('details.reasoning.allocationSection.title')}
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
                {t('details.reasoning.allocationSection.subtitle')}
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
                    {normalizeMarkdown(reasoning.allocation_reasoning)}
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
