import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, Trash2, RefreshCw, Search, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FloatingPanel } from '@/components/ui/floating-panel';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { ragApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { RAGDocument, RAGQueryResponse } from '@/types';
import { toast } from '@/components/ui/toastStore';

const ACCEPTED_FILE_TYPES =
  'application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document';

function formatStatus(status: RAGDocument['status']) {
  switch (status) {
    case 'completed':
      return { label: 'Zaindeksowano', className: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800' };
    case 'processing':
      return { label: 'Przetwarzanie', className: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800' };
    case 'failed':
      return { label: 'Błąd', className: 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800' };
    default:
      return { label: status, className: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700' };
  }
}

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString('pl-PL', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch (error) {
    return value;
  }
}

export function RAGManagementPanel() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const activePanel = useAppStore(state => state.activePanel);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentTitle, setDocumentTitle] = useState('');
  const [country, setCountry] = useState('Poland');
  const [testQuery, setTestQuery] = useState('');
  const [topK, setTopK] = useState(3);
  const [lastQueryResult, setLastQueryResult] = useState<RAGQueryResponse | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: documents = [], isLoading, isFetching } = useQuery({
    queryKey: ['rag-documents'],
    queryFn: ragApi.listDocuments,
    refetchInterval: (query) => {
      const docs = query.state.data as RAGDocument[] | undefined;
      const hasProcessing = docs?.some((doc) => doc.status === 'processing');
      return hasProcessing ? 5000 : false;
    },
  });

  const sortedDocuments = useMemo(
    () => [...documents].sort((a, b) => (a.created_at < b.created_at ? 1 : -1)),
    [documents],
  );

  const uploadMutation = useMutation({
    mutationFn: async ({ file, title, country: uploadCountry }: { file: File; title: string; country: string }) => {
      return ragApi.uploadDocument(file, title, uploadCountry);
    },
    onSuccess: () => {
      toast.success('Dokument przesłany', 'Rozpoczęto indeksowanie w bazie wiedzy RAG.');
      setSelectedFile(null);
      setDocumentTitle('');
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] });
    },
    onError: (error: Error) => {
      toast.error('Nie udało się przesłać dokumentu', error.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      setDeletingId(documentId);
      return ragApi.deleteDocument(documentId);
    },
    onSuccess: () => {
      toast.success('Dokument usunięty', 'Plik został wyłączony z wyszukiwania kontekstowego.');
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] });
    },
    onError: (error: Error) => {
      toast.error('Nie udało się usunąć dokumentu', error.message);
    },
    onSettled: () => setDeletingId(null),
  });

  const queryMutation = useMutation({
    mutationFn: async ({ query, limit }: { query: string; limit: number }) => {
      return ragApi.query({ query, top_k: limit });
    },
    onSuccess: (data) => {
      setLastQueryResult(data);
      toast.success('Zapytanie wykonane', 'Pobrano fragmenty wiedzy z silnika RAG.');
    },
    onError: (error: Error) => {
      toast.error('Nie udało się wykonać zapytania', error.message);
    },
  });

  const handleUpload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      toast.error('Brak pliku', 'Wybierz dokument PDF lub DOCX do przesłania.');
      return;
    }
    if (!documentTitle.trim()) {
      toast.error('Brak tytułu', 'Nadaj dokumentowi krótką, opisową nazwę.');
      return;
    }
    uploadMutation.mutate({ file: selectedFile, title: documentTitle.trim(), country });
  };

  const handleQuery = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedQuery = testQuery.trim();
    if (!cleanedQuery) {
      toast.error('Brak zapytania', 'Wpisz pytanie lub frazę badawczą.');
      return;
    }
    setLastQueryResult(null);
    queryMutation.mutate({ query: cleanedQuery, limit: Math.max(1, topK) });
  };

  const isUploading = uploadMutation.isPending;
  const isQuerying = queryMutation.isPending;

  return (
    <FloatingPanel
      isOpen={activePanel === 'rag'}
      onClose={() => setActivePanel(null)}
      title="Centrum wiedzy RAG"
      panelKey="rag"
      size="lg"
    >
      <div className="space-y-6">
        <section className="rounded-2xl border border-slate-200/80 dark:border-slate-700/80 bg-white/80 dark:bg-slate-800/80 p-4 space-y-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary-50 dark:bg-primary-900/30 p-2">
              <Upload className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">Dodaj nowy dokument źródłowy</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Wspierane formaty: PDF oraz DOCX. Dokumenty są analizowane i indeksowane semantycznie.
              </p>
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleUpload}>
            <div className="space-y-2">
              <Label htmlFor="rag-title">Tytuł dokumentu</Label>
              <Input
                id="rag-title"
                value={documentTitle}
                onChange={(event) => setDocumentTitle(event.target.value)}
                placeholder="np. Diagnoza Społeczna 2024"
                disabled={isUploading}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rag-country">Kraj</Label>
                <Input
                  id="rag-country"
                  value={country}
                  onChange={(event) => setCountry(event.target.value)}
                  disabled={isUploading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rag-file">Plik</Label>
                <Input
                  id="rag-file"
                  type="file"
                  accept={ACCEPTED_FILE_TYPES}
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    setSelectedFile(file);
                  }}
                  disabled={isUploading}
                />
                {selectedFile && (
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Wybrano: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={isUploading} className="gap-2">
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                Prześlij do RAG
              </Button>
            </div>
          </form>
        </section>

        <section className="rounded-2xl border border-slate-200/80 dark:border-slate-700/80 bg-white/80 dark:bg-slate-800/80 p-4 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-slate-100 dark:bg-slate-700 p-2">
                <FileText className="w-5 h-5 text-slate-600 dark:text-slate-300" />
              </div>
              <div>
                <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">Indeksowane dokumenty</h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Monitoruj status przetwarzania oraz usuwaj nieaktualne materiały badawcze.
                </p>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['rag-documents'] })}
              title="Odśwież listę"
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-sm text-slate-500 dark:text-slate-400">
              <SpinnerLogo className="w-6 h-6 mr-2" /> Wczytywanie dokumentów...
            </div>
          ) : sortedDocuments.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 p-6 text-sm text-slate-500 dark:text-slate-400 text-center">
              Brak dokumentów w bazie RAG. Dodaj raport lub badanie, aby wzbogacić generowane persony.
            </div>
          ) : (
            <div className="space-y-3">
              {sortedDocuments.map((document) => {
                const status = formatStatus(document.status);
                const isDeleting = deletingId === document.id && deleteMutation.isPending;
                return (
                  <div
                    key={document.id}
                    className="flex flex-col gap-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50 p-4 md:flex-row md:items-center md:justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{document.title}</p>
                        <Badge className={`${status.className} border`}>{status.label}</Badge>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Dodano {formatDate(document.created_at)} • {document.file_type.toUpperCase()} • {document.num_chunks} segmentów
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="text-rose-600 hover:text-rose-700"
                        disabled={isDeleting}
                        onClick={() => deleteMutation.mutate(document.id)}
                        title="Usuń dokument z RAG"
                      >
                        {isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200/80 dark:border-slate-700/80 bg-white/80 dark:bg-slate-800/80 p-4 space-y-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-accent-50 dark:bg-accent-900/30 p-2">
              <Search className="w-5 h-5 text-accent-600 dark:text-accent-400" />
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">Przetestuj wyszukiwanie kontekstowe</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Sprawdź, jakie fragmenty raportów trafią do generatora person dla konkretnego pytania badawczego.
              </p>
            </div>
          </div>

          <form className="space-y-3" onSubmit={handleQuery}>
            <Textarea
              value={testQuery}
              onChange={(event) => setTestQuery(event.target.value)}
              placeholder="Jakie są największe obawy młodych rodziców w średnich miastach?"
              disabled={isQuerying}
              rows={3}
            />
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <Label htmlFor="rag-topk" className="text-xs text-slate-500 dark:text-slate-400">
                  Liczba fragmentów
                </Label>
                <Input
                  id="rag-topk"
                  type="number"
                  min={1}
                  max={10}
                  value={topK}
                  onChange={(event) => setTopK(Number(event.target.value))}
                  className="w-20"
                  disabled={isQuerying}
                />
              </div>
              <Button type="submit" disabled={isQuerying} className="gap-2">
                {isQuerying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Wykonaj zapytanie
              </Button>
            </div>
          </form>

          {lastQueryResult && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-800/50 p-4 space-y-3">
              <div>
                <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Zsyntetyzowany kontekst</h5>
                <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                  {lastQueryResult.context}
                </p>
              </div>
              <div className="space-y-2">
                <h6 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Cytowania</h6>
                {lastQueryResult.citations.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Brak szczegółowych cytowań dla tego zapytania.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {lastQueryResult.citations.map((citation, index) => (
                      <div key={`${citation.document_title}-${index}`} className="rounded-lg bg-white/90 dark:bg-slate-700/50 p-3 shadow-sm">
                        <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">{citation.document_title}</p>
                        <p className="text-sm text-slate-700 dark:text-slate-300 mt-1 leading-relaxed">{citation.chunk_text}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">trafność {Math.round(citation.relevance_score * 100)}%</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </FloatingPanel>
  );
}
