import React from 'react';
import { Database, Quote, Sparkles, Network } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Persona, RagContextDetails, RAGGraphNode, RAGCitation } from '@/types';

interface PersonaRAGPanelProps {
  persona: Persona;
}

function formatSearchType(searchType?: string): string {
  if (!searchType) return 'brak danych';
  const normalized = searchType.replace(/\+/g, ' + ').replace(/_/g, ' ');
  return normalized.toLowerCase();
}

function formatConfidence(confidence?: string): { label: string; variant: 'default' | 'secondary' | 'outline' } {
  switch ((confidence || '').toLowerCase()) {
    case 'high':
      return { label: 'Wysoka pewność', variant: 'default' };
    case 'low':
      return { label: 'Niska pewność', variant: 'outline' };
    default:
      return { label: 'Średnia pewność', variant: 'secondary' };
  }
}

function GraphNodeList({ nodes }: { nodes: RAGGraphNode[] }) {
  if (!nodes.length) return null;

  return (
    <div className="space-y-3">
      {nodes.map((node, idx) => {
        const confidenceMeta = formatConfidence(
          typeof node.confidence === 'string' ? node.confidence : typeof node.pewnosc === 'string' ? node.pewnosc : undefined,
        );
        const summary = node.summary || node.streszczenie || 'Insight z grafu';
        const magnitude = node.magnitude || node.skala;
        const whyMatters = node.why_matters || node.kluczowe_fakty;
        const source = node.source || node.document_title;
        const timePeriod = node.time_period || node.okres_czasu;

        return (
          <div key={idx} className="rounded-lg border bg-card text-card-foreground p-4">
            <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                {node.type && (
                  <Badge variant="outline" className="uppercase tracking-wide text-xs">
                    {node.type}
                  </Badge>
                )}
                {source && (
                  <Badge variant="secondary" className="text-xs">
                    {source}
                  </Badge>
                )}
                {timePeriod && (
                  <Badge variant="outline" className="text-xs">
                    {timePeriod}
                  </Badge>
                )}
              </div>
              <Badge variant={confidenceMeta.variant} className="text-xs">
                {confidenceMeta.label}
              </Badge>
            </div>

            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                {magnitude && (
                  <span className="text-lg font-semibold text-primary">{magnitude}</span>
                )}
                <p className="text-sm font-medium leading-snug">{summary}</p>
              </div>
              {whyMatters && (
                <p className="text-sm text-muted-foreground leading-relaxed">{whyMatters}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CitationsList({ citations }: { citations: RAGCitation[] }) {
  if (!citations.length) return (
    <div className="text-sm text-muted-foreground py-4 text-center">
      Brak cytowań z bazy wiedzy RAG dla tej persony.
    </div>
  );

  return (
    <div className="space-y-4">
      {citations.map((citation, idx) => (
        <Card key={`${citation.document_title}-${idx}`}>
          <CardContent className="pt-4">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div>
                <p className="font-medium text-sm">{citation.document_title}</p>
                <p className="text-xs text-muted-foreground">
                  Trafność: {(citation.relevance_score * 100).toFixed(0)}%
                </p>
              </div>
              <Badge variant="outline">#{idx + 1}</Badge>
            </div>
            <p className="text-sm text-muted-foreground whitespace-pre-line leading-relaxed">
              {citation.chunk_text}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function PersonaRAGPanel({ persona }: PersonaRAGPanelProps) {
  const context: RagContextDetails | null | undefined = persona.rag_context_details;
  const citations = persona.rag_citations ?? [];
  const hasAnyContext =
    persona.rag_context_used || (context && (
      Boolean(context.graph_context) ||
      Boolean(context.context_preview) ||
      Boolean(context.graph_nodes && context.graph_nodes.length) ||
      Boolean(citations.length)
    ));

  if (!hasAnyContext) {
    return (
      <div className="text-sm text-muted-foreground text-center py-8">
        Ta persona została wygenerowana bez wykorzystania bazy wiedzy RAG.
      </div>
    );
  }

  const searchTypeLabel = formatSearchType(context?.search_type);
  const graphNodes = context?.graph_nodes ?? [];
  const graphContext = context?.context_preview || context?.graph_context;
  const contextLength = context?.context_length ?? (graphContext ? graphContext.length : undefined);
  const graphNodeCount = context?.graph_nodes_count ?? graphNodes.length;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            Parametry wyszukiwania RAG
          </CardTitle>
          <CardDescription>
            Jakie źródła i strategia zostały użyte do wzbogacenia tej persony
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Tryb wyszukiwania</p>
              <p className="font-medium capitalize">{searchTypeLabel}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Wyniki</p>
              <p className="font-medium">{context?.num_results ?? citations.length ?? 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Wzbogacone fragmenty</p>
              <p className="font-medium">{context?.enriched_chunks ?? 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Węzły z grafu</p>
              <p className="font-medium">{graphNodeCount}</p>
            </div>
          </div>
          {context?.query && (
            <div className="mt-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Zapytanie RAG</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{context.query}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {graphContext && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Kontekst wzbogacający personę
            </CardTitle>
            {contextLength && (
              <CardDescription>
                Fragment bazujący na dokumentach i grafie (≈ {contextLength} znaków)
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <div className="rounded-md border bg-muted/50 p-3">
              <pre className="whitespace-pre-wrap text-xs leading-relaxed text-muted-foreground">
                {graphContext}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {graphNodes.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5 text-primary" />
              Kluczowe sygnały z grafu
            </CardTitle>
            <CardDescription>
              Najważniejsze wskaźniki i spostrzeżenia powiązane z tym segmentem
            </CardDescription>
          </CardHeader>
          <CardContent>
            <GraphNodeList nodes={graphNodes.slice(0, 6)} />
            {graphNodes.length > 6 && (
              <p className="text-xs text-muted-foreground mt-3">
                Pokazano 6 z {graphNodes.length} węzłów. Pozostałe dostępne są w bazie grafowej.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Quote className="h-5 w-5 text-primary" />
            Cytowania z dokumentów
          </CardTitle>
          <CardDescription>
            Fragmenty źródłowe, na których oparto profil tej persony
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CitationsList citations={citations} />
        </CardContent>
      </Card>
    </div>
  );
}
