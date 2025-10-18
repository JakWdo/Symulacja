import { PersonaDetailsResponse } from '@/types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FileText, Sparkles, AlertCircle } from 'lucide-react';

interface MethodologySectionProps {
  persona: PersonaDetailsResponse;
}

/**
 * MethodologySection - wyświetla metadane generacji + źródła danych + ograniczenia.
 *
 * Zawiera:
 * - Źródła danych (RAG documents, focus groups)
 * - Metadane generacji (timestamp, model, confidence score)
 * - Ograniczenia interpretacji (disclaimer)
 */
export function MethodologySection({ persona }: MethodologySectionProps) {
  const ragCitationsCount = persona.rag_citations?.length || 0;
  const ragDetailsNodes = persona.rag_context_details?.graph_nodes_count || 0;

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pl-PL', {
      dateStyle: 'long',
      timeStyle: 'short',
    }).format(date);
  };

  return (
    <div className="space-y-6">
      {/* Data Sources */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-muted-foreground" />
            <CardTitle>Źródła Danych</CardTitle>
          </div>
          <CardDescription>
            Dane użyte do wygenerowania tej persony
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">RAG Documents</dt>
              <dd className="mt-1 text-sm">
                {ragCitationsCount > 0 ? (
                  <span>
                    {ragCitationsCount} {ragCitationsCount === 1 ? 'dokument' : 'dokumenty'}
                  </span>
                ) : (
                  <span className="text-muted-foreground">Brak</span>
                )}
              </dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-muted-foreground">Graph RAG Nodes</dt>
              <dd className="mt-1 text-sm">
                {ragDetailsNodes > 0 ? (
                  <span>{ragDetailsNodes} węzłów</span>
                ) : (
                  <span className="text-muted-foreground">Brak</span>
                )}
              </dd>
            </div>

            {persona.rag_context_details?.search_type && (
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Typ Wyszukiwania</dt>
                <dd className="mt-1 text-sm capitalize">
                  {persona.rag_context_details.search_type.replace('_', ' ')}
                </dd>
              </div>
            )}
          </dl>

          {!persona.rag_context_used && (
            <Alert className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                Ta persona została wygenerowana bez użycia RAG context.
                Dane mogą być mniej szczegółowe.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Generation Metadata */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-muted-foreground" />
            <CardTitle>Metadane Generacji</CardTitle>
          </div>
          <CardDescription>
            Informacje techniczne o procesie generacji
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Data utworzenia</dt>
              <dd className="mt-1 text-sm">{formatDate(persona.created_at)}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-muted-foreground">Ostatnia aktualizacja</dt>
              <dd className="mt-1 text-sm">
                {persona.updated_at
                  ? formatDate(persona.updated_at)
                  : formatDate(persona.created_at)}
              </dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-muted-foreground">Model LLM</dt>
              <dd className="mt-1 text-sm">
                Google Gemini 2.5 (Flash + Pro)
              </dd>
            </div>

            {persona.narratives_status && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Status Narracji</dt>
                <dd className="mt-1 text-sm">
                  {persona.narratives_status === 'ok' && (
                    <span className="text-green-600">✓ Kompletne</span>
                  )}
                  {persona.narratives_status === 'degraded' && (
                    <span className="text-yellow-600">⚠ Częściowe</span>
                  )}
                  {persona.narratives_status === 'offline' && (
                    <span className="text-red-600">✗ Niedostępne</span>
                  )}
                  {persona.narratives_status === 'pending' && (
                    <span className="text-muted-foreground">⏳ Oczekujące</span>
                  )}
                </dd>
              </div>
            )}

            {persona.rag_context_details?.orchestration_reasoning && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Confidence Score</dt>
                <dd className="mt-1 text-sm">
                  {/* Możemy dodać confidence_score do backend w przyszłości */}
                  N/A
                </dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Limitations Disclaimer */}
      <Card className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/20">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Ograniczenia Interpretacji
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Persona została wygenerowana na podstawie danych agregowanych i nie reprezentuje
            konkretnej osoby. Wyniki powinny być traktowane jako <strong>hipotezy wymagające walidacji</strong>
            {' '}w badaniach jakościowych i ilościowych.
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed mt-3">
            Model LLM (Gemini 2.5) może wprowadzać własne założenia i uprzedzenia.
            Rekomendujemy <strong>krytyczną ocenę</strong> wygenerowanych insightów i weryfikację
            z rzeczywistymi użytkownikami przed podejmowaniem decyzji biznesowych.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
