import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { FloatingPanel } from '@/components/ui/floating-panel';
import { focusGroupsApi, personasApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import {
  MessageSquare,
  Play,
  Clock,
  CheckCircle2,
  AlertCircle,
  Users,
  Plus,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn, formatDate, formatTime } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import type { FocusGroup } from '@/types';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { CreateFocusGroupPayload } from '@/lib/api';
import { composeTargetContext, parseTargetContext } from '@/lib/focusGroupUtils';

function StatusBadge({ status }: { status: FocusGroup['status'] }) {
  const configs = {
    pending: {
      icon: Clock,
      gradient: 'from-slate-500 to-slate-600',
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      label: 'Oczekujące',
    },
    running: {
      icon: SpinnerLogo,
      gradient: 'from-blue-500 to-indigo-600',
      bg: 'bg-blue-100',
      text: 'text-blue-700',
      label: 'W trakcie',
      animate: true,
    },
    completed: {
      icon: CheckCircle2,
      gradient: 'from-green-500 to-emerald-600',
      bg: 'bg-green-100',
      text: 'text-green-700',
      label: 'Zakończone',
    },
    failed: {
      icon: AlertCircle,
      gradient: 'from-red-500 to-rose-600',
      bg: 'bg-red-100',
      text: 'text-red-700',
      label: 'Nieudane',
    },
  } as const;

  const config = configs[status];
  const Icon = config.icon;

  return (
    <div className={cn('inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full', config.bg)}>
      {status === 'running' ? (
        <SpinnerLogo className="w-3.5 h-3.5" />
      ) : (
        <Icon className={cn('w-3.5 h-3.5', config.text)} />
      )}
      <span className={cn('text-xs font-semibold', config.text)}>{config.label}</span>
    </div>
  );
}

function FocusGroupCard({
  focusGroup,
  isSelected,
  index,
  onEdit,
}: {
  focusGroup: FocusGroup;
  isSelected: boolean;
  index: number;
  onEdit: () => void;
}) {
  // Use Zustand selector to prevent unnecessary re-renders
  const setSelectedFocusGroup = useAppStore(state => state.setSelectedFocusGroup);
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: () => focusGroupsApi.run(focusGroup.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups', focusGroup.project_id] });
      queryClient.invalidateQueries({ queryKey: ['focus-group', focusGroup.id] });
      toast.info('Grupa fokusowa rozpoczęta', `"${focusGroup.name}" jest teraz w trakcie realizacji`);
    },
    onError: (error: Error) => {
      toast.error('Nie udało się uruchomić grupy fokusowej', error.message);
    },
  });

  const isLaunchReady = focusGroup.persona_ids.length >= 2 && focusGroup.questions.length >= 1;
  const canEdit = focusGroup.status === 'pending';

  const handleRun = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isLaunchReady) {
      toast.error('Dodaj więcej szczegółów', 'Potrzeba co najmniej 2 person i 1 pytania przed uruchomieniem.');
      return;
    }
    runMutation.mutate();
  };

  const canRun = focusGroup.status === 'pending';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      onClick={() => {
        setSelectedFocusGroup(focusGroup);
        onEdit();
      }}
      className={cn(
        'relative p-5 rounded-2xl cursor-pointer transition-all duration-300',
        'border-2 bg-white',
        isSelected
          ? 'border-primary-400 shadow-xl shadow-primary-100 scale-[1.02]'
          : 'border-slate-200 hover:border-primary-200 hover:shadow-lg'
      )}
    >
      {/* Selection indicator */}
      {isSelected && (
        <motion.div
          layoutId="selected-focus-group"
          className="absolute inset-0 bg-gradient-to-br from-primary-50 to-accent-50 rounded-2xl -z-10"
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        />
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start gap-3 mb-3">
            <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center shadow-lg">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-slate-900 text-lg mb-1 truncate">
                {focusGroup.name}
              </h3>
              <StatusBadge status={focusGroup.status} />
            </div>
          </div>

          {/* Description */}
          {focusGroup.description && (
            <p className="text-sm text-slate-600 mb-3 line-clamp-2">
              {focusGroup.description}
            </p>
          )}

          {/* Metadata */}
          <div className="flex flex-wrap gap-3 text-xs text-slate-500 mb-3">
            <span className="flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              {focusGroup.persona_ids.length} person
            </span>
            <span className="flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5" />
              {focusGroup.questions.length} pytań
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatDate(focusGroup.created_at)}
            </span>
          </div>

          {/* Performance metrics */}
          {focusGroup.status === 'completed' && (
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200">
                <div className="text-xs text-slate-500 mb-1">Śr. odpowiedź</div>
                <div className="text-sm font-bold text-slate-900">
                  {formatTime(focusGroup.avg_response_time_ms)}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200">
                <div className="text-xs text-slate-500 mb-1">Całkowity czas</div>
                <div className="text-sm font-bold text-slate-900">
                  {formatTime(focusGroup.total_execution_time_ms)}
                </div>
              </div>
            </div>
          )}

          {/* Failed status message */}
          {focusGroup.status === 'failed' && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-red-700">
                  <div className="font-semibold mb-1">Wykonanie nie powiodło się</div>
                  <div className="text-red-600">
                    Sprawdź logi. Typowe przyczyny: quota API, problemy z siecią, nieprawidłowe persony.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col items-end gap-2">
          {canEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              className="w-24"
            >
              Edytuj
            </Button>
          )}
          {canRun && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleRun}
              disabled={runMutation.isPending || !isLaunchReady}
              className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
              title={
                !isLaunchReady
                  ? 'Dodaj co najmniej 2 persony i 1 pytanie przed uruchomieniem.'
                  : undefined
              }
            >
              {runMutation.isPending ? (
                <SpinnerLogo className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
            </motion.button>
          )}
        </div>
      </div>

      {/* Selected indicator arrow */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="absolute right-4 top-1/2 -translate-y-1/2"
        >
          <ArrowRight className="w-5 h-5 text-primary-500" />
        </motion.div>
      )}
    </motion.div>
  );
}

function FocusGroupForm({
  mode,
  focusGroup,
  onCancel,
  onSaved,
}: {
  mode: 'create' | 'edit';
  focusGroup?: FocusGroup;
  onCancel: () => void;
  onSaved: (group: FocusGroup) => void;
}) {
  const { selectedProject } = useAppStore();
  const queryClient = useQueryClient();

  const { data: availablePersonas = [], isLoading: personasLoading } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: () => personasApi.getByProject(selectedProject!.id),
    enabled: !!selectedProject,
  });

  const parsedContext = parseTargetContext(focusGroup?.project_context);
  const [name, setName] = useState(focusGroup?.name ?? '');
  const [description, setDescription] = useState(focusGroup?.description ?? '');
  const [projectContext, setProjectContext] = useState(parsedContext.text);
  const [targetParticipants, setTargetParticipants] = useState(parsedContext.target);
  const [modeValue, setModeValue] = useState<'normal' | 'adversarial'>(focusGroup?.mode ?? 'normal');
  const [questions, setQuestions] = useState<string[]>(
    focusGroup?.questions?.length ? focusGroup.questions : ['']
  );
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>(focusGroup?.persona_ids ?? []);
  const [isSaving, setIsSaving] = useState(false);
  const [savingAction, setSavingAction] = useState<'save' | 'launch' | null>(null);

  useEffect(() => {
    if (mode === 'edit' && focusGroup) {
      const parsed = parseTargetContext(focusGroup.project_context);
      setName(focusGroup.name);
      setDescription(focusGroup.description ?? '');
      setProjectContext(parsed.text);
      setTargetParticipants(parsed.target);
      setModeValue(focusGroup.mode);
      setQuestions(focusGroup.questions?.length ? focusGroup.questions : ['']);
      setSelectedPersonas(focusGroup.persona_ids ?? []);
    }
  }, [mode, focusGroup]);

  useEffect(() => {
    if (mode === 'create' && availablePersonas.length >= 2 && selectedPersonas.length === 0) {
      setSelectedPersonas(
        availablePersonas.slice(0, Math.min(4, availablePersonas.length)).map((p) => p.id)
      );
    }
  }, [mode, availablePersonas, selectedPersonas.length]);

  const trimmedQuestions = questions.map((q) => q.trim()).filter(Boolean);
  const launchReady = selectedPersonas.length >= 2 && trimmedQuestions.length >= 1;

  const togglePersona = (personaId: string, checked: boolean) => {
    setSelectedPersonas((prev) =>
      checked ? [...prev, personaId] : prev.filter((id) => id !== personaId)
    );
  };

  const handleSave = async (launch: boolean) => {
    if (!selectedProject) {
      toast.error('Najpierw wybierz projekt');
      return;
    }

    if (!name.trim()) {
      toast.error('Nazwa jest wymagana');
      return;
    }

    if (launch && !launchReady) {
      toast.error('Dodaj więcej szczegółów', 'Potrzeba co najmniej 2 person i 1 pytania przed uruchomieniem.');
      return;
    }

    const payload: CreateFocusGroupPayload = {
      name: name.trim(),
      description: description.trim() ? description.trim() : undefined,
      project_context: composeTargetContext(targetParticipants, projectContext),
      persona_ids: selectedPersonas,
      questions: trimmedQuestions,
      mode: modeValue,
    };

    setIsSaving(true);
    setSavingAction(launch ? 'launch' : 'save');

    try {
      let savedGroup: FocusGroup;
      if (mode === 'create') {
        savedGroup = await focusGroupsApi.create(selectedProject.id, payload);
      } else {
        savedGroup = await focusGroupsApi.update(focusGroup!.id, payload);
      }

      if (launch) {
        await focusGroupsApi.run(savedGroup.id);
        toast.success('Grupa fokusowa uruchomiona', 'Symulacja działa w tle.');
      } else {
        toast.success(
          mode === 'create' ? 'Grupa fokusowa utworzona' : 'Zmiany zapisane',
          mode === 'create'
            ? 'Konfiguracja sesji gotowa do uruchomienia.'
            : 'Najnowsze aktualizacje zapisane pomyślnie.'
        );
      }

      await queryClient.invalidateQueries({ queryKey: ['focus-groups', selectedProject.id] });
      setSelectedFocusGroup(savedGroup);
      onSaved(savedGroup);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Nieznany błąd';
      toast.error('Nie udało się zapisać grupy fokusowej', message);
    } finally {
      setIsSaving(false);
      setSavingAction(null);
    }
  };

  const handleAddQuestion = () => setQuestions((prev) => [...prev, '']);

  const handleQuestionChange = (index: number, value: string) => {
    setQuestions((prev) => {
      const updated = [...prev];
      updated[index] = value;
      return updated;
    });
  };

  const handleRemoveQuestion = (index: number) => {
    setQuestions((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev));
  };

  const personaCount = availablePersonas.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">
            {mode === 'create' ? 'Utwórz grupę fokusową' : 'Edytuj grupę fokusową'}
          </h2>
          <p className="text-sm text-slate-500">
            {mode === 'create'
              ? 'Utwórz szkic teraz i dopracuj lub uruchom, gdy będzie gotowe.'
              : 'Zaktualizuj konfigurację przed uruchomieniem sesji.'}
          </p>
        </div>
        <Button variant="ghost" onClick={onCancel} disabled={isSaving}>
          Anuluj
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border border-border">
          <CardContent className="space-y-4 p-6">
            <div className="space-y-2">
              <Label>Nazwa grupy fokusowej *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="np. Sesja opinii o produkcie"
                maxLength={255}
              />
            </div>
            <div className="space-y-2">
              <Label>Opis</Label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Krótki opis celów grupy fokusowej"
              />
            </div>
            <div className="space-y-2">
              <Label>Kontekst projektu</Label>
              <Textarea
                value={projectContext}
                onChange={(e) => setProjectContext(e.target.value)}
                rows={3}
                placeholder="Opcjonalny kontekst przekazywany uczestnikom"
              />
            </div>
            <div className="space-y-2">
              <Label>Tryb</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={modeValue === 'normal' ? 'default' : 'outline'}
                  onClick={() => setModeValue('normal')}
                  disabled={isSaving}
                >
                  Kooperacyjny
                </Button>
                <Button
                  type="button"
                  variant={modeValue === 'adversarial' ? 'default' : 'outline'}
                  onClick={() => setModeValue('adversarial')}
                  disabled={isSaving}
                >
                  Kontrowersyjny
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Docelowa liczba uczestników</Label>
              <Select
                value={String(targetParticipants)}
                onValueChange={(value) => setTargetParticipants(Number.parseInt(value, 10))}
                disabled={isSaving}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[2, 4, 6, 8, 10, 12].map((option) => (
                    <SelectItem key={option} value={String(option)}>
                      {option} uczestników
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between">
              <Label>Pytania dyskusyjne</Label>
              <Button
                type="button"
                variant="secondary"
                onClick={handleAddQuestion}
                disabled={isSaving}
              >
                <Plus className="w-4 h-4 mr-2" />
                Dodaj pytanie
              </Button>
            </div>
            <div className="space-y-2">
              {questions.map((q, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={q}
                    onChange={(e) => handleQuestionChange(index, e.target.value)}
                    placeholder={`Pytanie ${index + 1}`}
                    disabled={isSaving}
                  />
                  {questions.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => handleRemoveQuestion(index)}
                      disabled={isSaving}
                    >
                      Usuń
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card border border-border">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Wybierz persony</Label>
              <p className="text-xs text-slate-500">
                Wybierz co najmniej dwie persony przed uruchomieniem sesji.
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setSelectedPersonas(availablePersonas.map((p) => p.id))}
                disabled={isSaving || availablePersonas.length === 0}
              >
                Zaznacz wszystkie
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setSelectedPersonas([])}
                disabled={isSaving || availablePersonas.length === 0}
              >
                Wyczyść
              </Button>
            </div>
          </div>

          {personasLoading ? (
            <div className="flex items-center justify-center py-12">
              <SpinnerLogo className="w-8 h-8" />
            </div>
          ) : personaCount === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 py-10 text-center text-sm text-slate-500">
              Brak dostępnych person. Najpierw wygeneruj persony, aby uruchomić grupę fokusową.
            </div>
          ) : (
            <>
              <div className="space-y-1 mb-3">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{selectedPersonas.length} wybrano</span>
                  <span>{targetParticipants} cel</span>
                </div>
                <Progress
                  value={Math.min((selectedPersonas.length / Math.max(1, targetParticipants)) * 100, 100)}
                  className="h-2"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-y-auto rounded-xl border border-slate-200 p-2">
                {availablePersonas.map((persona) => {
                  const checked = selectedPersonas.includes(persona.id);
                  return (
                    <label
                      key={persona.id}
                    className={cn(
                      'flex items-center gap-2 p-3 rounded-lg border transition-all cursor-pointer',
                      checked
                        ? 'border-primary-400 bg-primary-50'
                        : 'border-transparent bg-slate-50 hover:border-slate-200'
                    )}
                  >
                    <input
                      type="checkbox"
                      className="w-4 h-4"
                      checked={checked}
                      onChange={(e) => togglePersona(persona.id, e.target.checked)}
                      disabled={isSaving}
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-700">{persona.full_name ?? persona.persona_title ?? 'Persona'}</p>
                      <p className="text-xs text-slate-500">{persona.occupation ?? 'Zawód nieokreślony'}</p>
                    </div>
                    </label>
                  );
                })}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2 justify-end">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSaving}
        >
          Anuluj
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => handleSave(false)}
          disabled={isSaving || !name.trim()}
          isLoading={isSaving && savingAction === 'save'}
        >
          {mode === 'create' ? 'Utwórz grupę fokusową' : 'Zapisz zmiany'}
        </Button>
        <Button
          type="button"
          className="bg-brand hover:bg-brand/90 text-brand-foreground"
          onClick={() => handleSave(true)}
          disabled={isSaving || !name.trim() || personasLoading}
          isLoading={isSaving && savingAction === 'launch'}
        >
          Uruchom grupę fokusową
        </Button>
      </div>

      {!launchReady && (
        <p className="text-xs text-amber-600">
          Aby uruchomić, wybierz co najmniej dwie persony i dodaj przynajmniej jedno pytanie.
        </p>
      )}
    </div>
  );
}

export function FocusGroupPanel() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const activePanel = useAppStore(state => state.activePanel);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const selectedProject = useAppStore(state => state.selectedProject);
  const selectedFocusGroup = useAppStore(state => state.selectedFocusGroup);
  const setSelectedFocusGroup = useAppStore(state => state.setSelectedFocusGroup);
  const [formState, setFormState] = useState<
    | { mode: 'create' }
    | { mode: 'edit'; focusGroup: FocusGroup }
    | null
  >(null);

  // Fetch personas from TanStack Query
  const { data: personas = [] } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await personasApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
  });

  // Fetch focus groups from TanStack Query
  const { data: focusGroups = [], isLoading, isError, error } = useQuery<FocusGroup[]>({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await focusGroupsApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: (query) =>
      query.state.data?.some((group) => group.status === 'running') ? 2000 : false,
    refetchIntervalInBackground: true,
  });

  const handleFormSaved = (group: FocusGroup) => {
    setFormState(null);
    setSelectedFocusGroup(group);
  };

  return (
    <FloatingPanel
      isOpen={activePanel === 'focus-groups'}
      onClose={() => setActivePanel(null)}
      title={`Grupy fokusowe${focusGroups.length ? ` (${focusGroups.length})` : ''}`}
      panelKey="focus-groups"
      size="lg"
    >
      {!selectedProject ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center mb-6">
            <MessageSquare className="w-10 h-10 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Nie wybrano projektu</h3>
          <p className="text-sm text-slate-500">Wybierz projekt, aby zobaczyć grupy fokusowe</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <Button
              onClick={() => setFormState({ mode: 'create' })}
              className="w-full bg-gradient-to-r from-primary-500 to-accent-500 hover:from-primary-600 hover:to-accent-600"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Utwórz nową grupę fokusową
            </Button>
            {(personas?.length ?? 0) < 2 && (
              <p className="text-xs text-amber-600 mt-2">
                Dostępne mniej niż dwie persony. Możesz utworzyć szkic teraz i uruchomić, gdy persony będą gotowe.
              </p>
            )}
          </div>

          {formState ? (
            <FocusGroupForm
              mode={formState.mode}
              focusGroup={formState.mode === 'edit' ? formState.focusGroup : undefined}
              onCancel={() => setFormState(null)}
              onSaved={handleFormSaved}
            />
          ) : null}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <SpinnerLogo className="w-8 h-8 mb-4" />
              <p className="text-sm text-slate-600">Ładowanie grup fokusowych...</p>
            </div>
          ) : isError ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-sm text-red-600">{error?.message || 'Nie udało się załadować grup fokusowych'}</p>
            </div>
          ) : focusGroups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-primary-600" />
              </div>
              <p className="text-sm text-slate-500">Brak grup fokusowych</p>
              <p className="text-xs text-slate-400 mt-1">Utwórz pierwszą powyżej</p>
            </div>
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {focusGroups.map((fg, idx) => (
                  <FocusGroupCard
                    key={fg.id}
                    focusGroup={fg}
                    isSelected={selectedFocusGroup?.id === fg.id}
                    index={idx}
                    onEdit={() => setFormState({ mode: 'edit', focusGroup: fg })}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      )}
    </FloatingPanel>
  );
}
