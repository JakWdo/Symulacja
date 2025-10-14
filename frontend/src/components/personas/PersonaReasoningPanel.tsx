/**
 * PersonaReasoningPanel - Wyświetla szczegółowe reasoning persony
 *
 * Panel prezentuje edukacyjne wyjaśnienia:
 * - Orchestration brief (2000-3000 znaków) od Gemini 2.5 Pro
 * - Graph insights z wskaźnikami i wyjaśnieniami
 * - Allocation reasoning
 * - Overall context Polski
 *
 * Output style: Edukacyjny, konwersacyjny, production-ready
 */

import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Persona, PersonaReasoning } from '@/types';
import { analysisApi } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, BarChart3, Lightbulb, TrendingUp } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PersonaReasoningPanelProps {
  persona: Persona;
}

export function PersonaReasoningPanel({ persona }: PersonaReasoningPanelProps) {
  const { data: reasoning, isLoading, error } = useQuery<PersonaReasoning>({
    queryKey: ['persona-reasoning', persona.id],
    queryFn: () => analysisApi.getPersonaReasoning(persona.id),
    staleTime: 10 * 60 * 1000, // 10 minut cache
  });

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
              💡 Rozwiązanie: Wygeneruj nowe persony aby zobaczyć pełne reasoning.
            </p>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Orchestration Brief - DŁUGI brief od Gemini 2.5 Pro */}
      {reasoning.orchestration_brief && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-primary" />
              Dlaczego {persona.full_name}?
            </CardTitle>
            <CardDescription>
              Szczegółowa analiza demograficzna i społeczna od orchestration agent (Gemini 2.5 Pro)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reasoning.orchestration_brief}
              </ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overall Context Polski */}
      {reasoning.overall_context && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Kontekst Społeczny Polski
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reasoning.overall_context}
              </ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Graph Insights - Wskaźniki z wyjaśnieniami */}
      {reasoning.graph_insights && reasoning.graph_insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Wskaźniki z Grafu Wiedzy
            </CardTitle>
            <CardDescription>
              Dane z raportów o polskim społeczeństwie (z wyjaśnieniami dlaczego to ważne)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {reasoning.graph_insights.map((insight, idx) => (
              <div
                key={idx}
                className="border-l-4 border-primary pl-4 py-2 space-y-2"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge
                    variant={insight.type === 'Indicator' ? 'default' : 'secondary'}
                  >
                    {insight.type}
                  </Badge>
                  {insight.magnitude && (
                    <span className="text-lg font-bold text-primary">
                      {insight.magnitude}
                    </span>
                  )}
                  <Badge
                    variant="outline"
                    className={
                      insight.confidence === 'high'
                        ? 'border-green-500 text-green-500'
                        : insight.confidence === 'medium'
                        ? 'border-yellow-500 text-yellow-500'
                        : 'border-gray-500 text-gray-500'
                    }
                  >
                    {insight.confidence} confidence
                  </Badge>
                  {insight.time_period && (
                    <Badge variant="outline">{insight.time_period}</Badge>
                  )}
                  {insight.source && (
                    <Badge variant="outline" className="text-xs">
                      {insight.source}
                    </Badge>
                  )}
                </div>

                <p className="font-medium text-foreground">{insight.summary}</p>

                {insight.why_matters && (
                  <div className="text-sm text-muted-foreground">
                    <strong>Dlaczego to ważne:</strong>{' '}
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <span>{children}</span>,
                      }}
                    >
                      {insight.why_matters}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Allocation Reasoning */}
      {reasoning.allocation_reasoning && (
        <Card>
          <CardHeader>
            <CardTitle>Uzasadnienie Alokacji</CardTitle>
            <CardDescription>
              Dlaczego ta grupa demograficzna i dlaczego tyle person?
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reasoning.allocation_reasoning}
              </ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Demographics Target */}
      {reasoning.demographics && (
        <Card>
          <CardHeader>
            <CardTitle>Grupa Demograficzna</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(reasoning.demographics).map(([key, value]) => (
                <div key={key}>
                  <p className="text-sm text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className="font-medium">{String(value)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
