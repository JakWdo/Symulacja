import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { focusGroupsApi, personasApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
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

interface FocusGroupFormProps {
  mode: 'create' | 'edit';
  focusGroup?: FocusGroup;
  onCancel: () => void;
  onSaved: (group: FocusGroup) => void;
}

export function FocusGroupForm({
  mode,
  focusGroup,
  onCancel,
  onSaved,
}: FocusGroupFormProps) {
  const { selectedProject, setSelectedFocusGroup } = useAppStore();
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
