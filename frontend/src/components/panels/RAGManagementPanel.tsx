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

function formatStatus(status: RAGDocument['status'], t: any) {
  switch (status) {
    case 'completed':
      return { label: t('formatStatus.indexed'), className: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800' };
    case 'processing':
      return { label: t('formatStatus.processing'), className: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800' };
    case 'failed':
      return { label: t('formatStatus.error'), className: 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800' };
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
  const { t } = useTranslation('rag');
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
      toast.success(t('upload.success'), t('upload.successDescription'));
      setSelectedFile(null);
      setDocumentTitle('');
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] });
    },
    onError: (error: Error) => {
      toast.error(t('upload.error'), error.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      setDeletingId(documentId);
      return ragApi.deleteDocument(documentId);
    },
    onSuccess: () => {
      toast.success(t('delete.success'), t('delete.successDescription'));
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] });
    },
    onError: (error: Error) => {
      toast.error(t('delete.error'), error.message);
    },
    onSettled: () => setDeletingId(null),
  });

  const queryMutation = useMutation({
    mutationFn: async ({ query, limit }: { query: string; limit: number }) => {
      return ragApi.query({ query, top_k: limit });
    },
    onSuccess: (data) => {
      setLastQueryResult(data);
      toast.success(t('search.success'), t('search.successDescription'));
    },
    onError: (error: Error) => {
      toast.error(t('search.error'), error.message);
    },
  });

  const handleUpload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      toast.error(t('upload.errorNoFile'), t('upload.errorNoFileDescription'));
      return;
    }
    if (!documentTitle.trim()) {
      toast.error(t('upload.errorNoTitle'), t('upload.errorNoTitleDescription'));
      return;
    }
    uploadMutation.mutate({ file: selectedFile, title: documentTitle.trim(), country });
  };

  const handleQuery = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedQuery = testQuery.trim();
    if (!cleanedQuery) {
      toast.error(t('search.errorNoQuery'), t('search.errorNoQueryDescription'));
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
      title={t('panel.title')}
      panelKey="rag"
      size="lg"
    >
      <div className="space-y-6">
        <section className="rounded-figma-card border border-border bg-card p-4 space-y-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-figma-inner bg-primary-50 dark:bg-primary-900/30 p-2">
              <Upload className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h4 className="text-base font-normal text-foreground leading-[16px]">{t('upload.title')}</h4>
              <p className="text-xs text-muted-foreground">
                {t('upload.description')}
              </p>
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleUpload}>
            <div className="space-y-2">
              <Label htmlFor="rag-title">{t('upload.titleLabel')}</Label>
              <Input
                id="rag-title"
                value={documentTitle}
                onChange={(event) => setDocumentTitle(event.target.value)}
                placeholder={t('upload.titlePlaceholder')}
                disabled={isUploading}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rag-country">{t('upload.countryLabel')}</Label>
                <Input
                  id="rag-country"
                  value={country}
                  onChange={(event) => setCountry(event.target.value)}
                  disabled={isUploading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rag-file">{t('upload.fileLabel')}</Label>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => document.getElementById('rag-file')?.click()}
                    disabled={isUploading}
                    className="flex-shrink-0"
                  >
                    {selectedFile ? t('upload.changeFile') : t('upload.selectFile')}
                  </Button>
                  {selectedFile && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                      {t('upload.fileSelected', { name: selectedFile.name, size: Math.round(selectedFile.size / 1024) })}
                    </p>
                  )}
                </div>
                <Input
                  id="rag-file"
                  type="file"
                  accept={ACCEPTED_FILE_TYPES}
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    setSelectedFile(file);
                  }}
                  disabled={isUploading}
                  className="hidden"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={isUploading} className="gap-2">
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                {t('upload.uploadToRag')}
              </Button>
            </div>
          </form>
        </section>

        <section className="rounded-figma-card border border-border bg-card p-4 space-y-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="rounded-figma-inner bg-muted/30 p-2">
                <FileText className="w-5 h-5 text-muted-foreground" />
              </div>
              <div>
                <h4 className="text-base font-normal text-foreground leading-[16px]">{t('list.title')}</h4>
                <p className="text-xs text-muted-foreground">
                  {t('list.description')}
                </p>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['rag-documents'] })}
              title={t('list.refreshTitle')}
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
              <SpinnerLogo className="w-6 h-6 mr-2" /> {t('list.loading')}
            </div>
          ) : sortedDocuments.length === 0 ? (
            <div className="rounded-figma-inner border border-dashed border-border bg-muted/30 p-6 text-sm text-muted-foreground text-center">
              {t('list.empty')}
            </div>
          ) : (
            <div className="space-y-3">
              {sortedDocuments.map((document) => {
                const status = formatStatus(document.status, t);
                const isDeleting = deletingId === document.id && deleteMutation.isPending;
                return (
                  <div
                    key={document.id}
                    className="flex flex-col gap-3 rounded-figma-inner border border-border bg-muted/30 p-4 md:flex-row md:items-center md:justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-normal text-foreground">{document.title}</p>
                        <Badge className={`${status.className} border`}>{status.label}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {t('list.added')} {formatDate(document.created_at)} • {document.file_type.toUpperCase()} • {document.num_chunks} {t('list.segments')}
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
                        title={t('list.deleteButton')}
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

        <section className="rounded-figma-card border border-border bg-card p-4 space-y-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-figma-inner bg-accent-50 dark:bg-accent-900/30 p-2">
              <Search className="w-5 h-5 text-accent-600 dark:text-accent-400" />
            </div>
            <div>
              <h4 className="text-base font-normal text-foreground leading-[16px]">{t('search.title')}</h4>
              <p className="text-xs text-muted-foreground">
                {t('search.description')}
              </p>
            </div>
          </div>

          <form className="space-y-3" onSubmit={handleQuery}>
            <Textarea
              value={testQuery}
              onChange={(event) => setTestQuery(event.target.value)}
              placeholder={t('search.queryPlaceholder')}
              disabled={isQuerying}
              rows={3}
            />
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <Label htmlFor="rag-topk" className="text-xs text-slate-500 dark:text-slate-400">
                  {t('search.topKLabel')}
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
                {t('search.executeQuery')}
              </Button>
            </div>
          </form>

          {lastQueryResult && (
            <div className="rounded-figma-inner border border-border bg-muted/30 p-4 space-y-3">
              <div>
                <h5 className="text-sm font-normal text-foreground">{t('search.resultsTitle')}</h5>
                <p className="text-sm text-foreground whitespace-pre-line leading-relaxed">
                  {lastQueryResult.context}
                </p>
              </div>
              <div className="space-y-2">
                <h6 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t('search.citationsTitle')}</h6>
                {lastQueryResult.citations.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    {t('search.noCitations')}
                  </p>
                ) : (
                  <div className="space-y-2">
                    {lastQueryResult.citations.map((citation, index) => (
                      <div key={`${citation.document_title}-${index}`} className="rounded-figma-inner bg-card p-3 shadow-sm border border-border">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide">{citation.document_title}</p>
                        <p className="text-sm text-foreground mt-1 leading-relaxed">{citation.chunk_text}</p>
                        <p className="text-xs text-muted-foreground mt-2">{t('search.relevance', { score: Math.round(citation.relevance_score * 100) })}</p>
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
