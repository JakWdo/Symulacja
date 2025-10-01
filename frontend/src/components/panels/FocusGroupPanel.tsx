import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import {
  MessageSquare,
  Play,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Users,
  HelpCircle,
  Plus,
  Minus,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn, formatDate, formatTime, formatPercentage, truncateText } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import type { FocusGroup, Persona } from '@/types';

function StatusBadge({ status }: { status: FocusGroup['status'] }) {
  const configs = {
    pending: { icon: Clock, color: 'text-slate-600 bg-slate-100', label: 'Pending' },
    running: {
      icon: Loader2,
      color: 'text-blue-600 bg-blue-100 animate-pulse',
      label: 'Running',
    },
    completed: { icon: CheckCircle2, color: 'text-green-600 bg-green-100', label: 'Completed' },
    failed: { icon: AlertCircle, color: 'text-red-600 bg-red-100', label: 'Failed' },
  } as const;

  const config = configs[status];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium',
        config.color,
      )}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

function FocusGroupCard({
  focusGroup,
  isSelected,
}: {
  focusGroup: FocusGroup;
  isSelected: boolean;
}) {
  const { setSelectedFocusGroup } = useAppStore();
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: () => focusGroupsApi.run(focusGroup.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups', focusGroup.project_id] });
      toast.info('Focus group started', `"${focusGroup.name}" is now running`);
    },
    onError: (error: Error) => {
      toast.error('Failed to start focus group', error.message);
    },
  });

  const handleRun = (e: React.MouseEvent) => {
    e.stopPropagation();
    runMutation.mutate();
  };

  const meetsRequirements = useMemo(() => {
    if (focusGroup.status !== 'completed') {
      return null;
    }

    const avgResponse = focusGroup.avg_response_time_ms ?? Infinity;
    const totalTime = focusGroup.total_execution_time_ms ?? Infinity;
    const errorRate = focusGroup.consistency_error_rate ?? 1;

    return avgResponse <= 3000 && totalTime <= 30000 && errorRate <= 0.05;
  }, [focusGroup]);

  return (
    <div
      onClick={() => setSelectedFocusGroup(focusGroup)}
      className={cn(
        'node-card cursor-pointer group border-2 transition-colors',
        isSelected
          ? 'border-primary-200 shadow-lg bg-white'
          : 'border-transparent hover:border-primary-100',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 rounded-lg bg-accent-50 text-accent-600">
              <MessageSquare className="w-4 h-4" />
            </div>
            <h4 className="font-semibold text-slate-900 group-hover:text-primary-600 transition-colors">
              {focusGroup.name}
            </h4>
            <StatusBadge status={focusGroup.status} />
          </div>

          {focusGroup.description && (
            <p className="text-sm text-slate-600 mb-3">{focusGroup.description}</p>
          )}

          <div className="flex flex-wrap gap-3 text-xs text-slate-600 mb-3">
            <span>👥 {focusGroup.persona_ids.length} personas</span>
            <span>❓ {focusGroup.questions.length} questions</span>
            <span>📅 {formatDate(focusGroup.created_at)}</span>
          </div>

          {focusGroup.status === 'completed' && (
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="px-3 py-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500">Avg Response</div>
                <div className="text-sm font-semibold text-slate-900">
                  {formatTime(focusGroup.avg_response_time_ms)}
                </div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500">Total Time</div>
                <div className="text-sm font-semibold text-slate-900">
                  {formatTime(focusGroup.total_execution_time_ms)}
                </div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500">Consistency</div>
                <div className="text-sm font-semibold text-slate-900">
                  {formatPercentage(1 - (focusGroup.consistency_error_rate ?? 0))}
                </div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500">Idea Score</div>
                <div className="text-sm font-semibold text-slate-900">
                  {focusGroup.polarization_score !== null && focusGroup.polarization_score !== undefined
                    ? `${(focusGroup.polarization_score * 100).toFixed(1)}`
                    : 'N/A'}
                </div>
              </div>
            </div>
          )}

          {meetsRequirements !== null && (
            <div className={cn('px-3 py-2 rounded-lg text-xs font-medium', meetsRequirements
              ? 'bg-green-50 text-green-700'
              : 'bg-yellow-50 text-yellow-700')}
            >
              <div className="flex items-center gap-2">
                {meetsRequirements ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span>
                  {meetsRequirements
                    ? 'Meets all performance requirements'
                    : 'Some requirements need attention'}
                </span>
              </div>
            </div>
          )}

          {focusGroup.status === 'failed' && (
            <div className="px-3 py-2 rounded-lg bg-red-50 text-red-700 text-xs">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <div>
                  <div className="font-semibold">Execution Failed</div>
                  <div className="text-xs opacity-80 mt-1">
                    Check backend logs for details. Common causes: API quota exceeded, network issues, or invalid personas.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {focusGroup.status === 'pending' && (
          <Button
            onClick={handleRun}
            disabled={runMutation.isPending}
            variant="secondary"
            className="p-3"
            aria-label="Run focus group"
          >
            {runMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

function PersonaQuickPreview({ persona }: { persona: Persona | null }) {
  if (!persona) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
        Select personas on the left to preview their profiles here.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white/80 backdrop-blur-sm shadow-sm p-4 space-y-3">
      <div>
        <h4 className="text-base font-semibold text-slate-900">
          {persona.gender}, {persona.age}
        </h4>
        {persona.location && (
          <p className="text-sm text-slate-500">{persona.location}</p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-slate-50 p-2">
          <span className="text-slate-500 block">Education</span>
          <span className="text-slate-800 font-medium">
            {persona.education_level ?? 'N/A'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-50 p-2">
          <span className="text-slate-500 block">Income</span>
          <span className="text-slate-800 font-medium">
            {persona.income_bracket ?? 'N/A'}
          </span>
        </div>
      </div>
      {persona.values && persona.values.length > 0 && (
        <div>
          <span className="text-xs font-semibold text-slate-700">Values</span>
          <div className="mt-1 flex flex-wrap gap-2">
            {persona.values.slice(0, 4).map((value) => (
              <span
                key={value}
                className="px-2 py-0.5 text-xs rounded-full bg-primary-50 text-primary-700"
              >
                {value}
              </span>
            ))}
          </div>
        </div>
      )}
      {persona.background_story && (
        <p className="text-xs text-slate-600 leading-relaxed">
          {truncateText(persona.background_story, 180)}
        </p>
      )}
    </div>
  );
}

function CreateFocusGroupForm({ onCancel }: { onCancel: () => void }) {
  const queryClient = useQueryClient();
  const {
    selectedProject,
    personas,
    setSelectedFocusGroup,
    setSelectedPersona,
    selectedPersona,
  } = useAppStore();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([]);
  const [questions, setQuestions] = useState<string[]>(['']);
  const [mode, setMode] = useState<'normal' | 'adversarial'>('normal');

  const createMutation = useMutation({
    mutationFn: () =>
      focusGroupsApi.create(selectedProject!.id, {
        name: name.trim(),
        description: description.trim() || null,
        persona_ids: selectedPersonaIds,
        questions: questions.map((question) => question.trim()).filter(Boolean),
        mode,
      }),
    onSuccess: (createdFocusGroup) => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups', selectedProject?.id] });
      setSelectedFocusGroup(createdFocusGroup);
      onCancel();
      toast.success('Focus group created!', `"${createdFocusGroup.name}" is ready to run`);
    },
    onError: (error: Error) => {
      toast.error('Failed to create focus group', error.message);
    },
  });

  const availablePersonas = personas ?? [];
  const canSubmit =
    name.trim().length > 0 &&
    selectedPersonaIds.length >= 2 &&
    questions.some((question) => question.trim().length > 0);

  const togglePersona = (personaId: string) => {
    const persona = availablePersonas.find((p) => p.id === personaId) ?? null;
    setSelectedPersonaIds((prev) => {
      const alreadySelected = prev.includes(personaId);
      if (alreadySelected) {
        if (selectedPersona?.id === personaId) {
          setSelectedPersona(null);
        }
        return prev.filter((id) => id !== personaId);
      }
      setSelectedPersona(persona);
      return [...prev, personaId];
    });
  };

  const updateQuestion = (index: number, value: string) => {
    setQuestions((prev) => prev.map((question, idx) => (idx === index ? value : question)));
  };

  const addQuestion = () => setQuestions((prev) => [...prev, '']);
  const removeQuestion = (index: number) => {
    setQuestions((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedProject || !canSubmit) {
      return;
    }

    createMutation.mutate();
  };

  if (!selectedProject) {
    return null;
  }

  return (
    <div className="mt-4 space-y-4 border-t border-slate-200/60 pt-4">
      <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">Name</label>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Competitive positioning test"
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          required
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">Description</label>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Understanding reactions to new feature pricing"
          rows={3}
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Users className="w-4 h-4" /> Select personas (min. 2)
        </div>
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.2fr),minmax(0,1fr)]">
          <div className="max-h-56 overflow-y-auto rounded-lg border border-slate-200/60 divide-y divide-slate-200/60 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
            {availablePersonas.length === 0 ? (
              <div className="p-4 text-sm text-slate-500">
                No personas available yet. Generate personas for this project first.
              </div>
            ) : (
              availablePersonas.map((persona) => {
                const label = `${persona.gender}, ${persona.age} • ${persona.location ?? 'Unknown location'}`;
                const checked = selectedPersonaIds.includes(persona.id);
                return (
                  <label
                    key={persona.id}
                    className="flex items-start gap-3 px-3 py-2 text-sm cursor-pointer hover:bg-slate-50"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => togglePersona(persona.id)}
                      className="mt-0.5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                    <div className="flex flex-col">
                      <span className="text-slate-700">{label}</span>
                      {persona.background_story && (
                        <span className="text-xs text-slate-500">
                          {truncateText(persona.background_story, 90)}
                        </span>
                      )}
                    </div>
                  </label>
                );
              })
            )}
          </div>
          <PersonaQuickPreview persona={selectedPersona ?? null} />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <HelpCircle className="w-4 h-4" /> Discussion questions
        </div>
        <div className="space-y-2">
          {questions.map((question, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(event) => updateQuestion(index, event.target.value)}
                placeholder={`Question ${index + 1}`}
                className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              />
              {questions.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  className="px-3"
                  onClick={() => removeQuestion(index)}
                  aria-label="Remove question"
                >
                  <Minus className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={addQuestion} className="gap-2">
          <Plus className="w-4 h-4" />
          Add question
        </Button>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">Mode</label>
        <select
          value={mode}
          onChange={(event) => setMode(event.target.value as 'normal' | 'adversarial')}
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="normal">Normal</option>
          <option value="adversarial">Adversarial</option>
        </select>
      </div>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={!canSubmit || createMutation.isPending} isLoading={createMutation.isPending}>
            Create focus group
          </Button>
        </div>
      </form>
    </div>
  );
}

export function FocusGroupPanel() {
  const {
    activePanel,
    setActivePanel,
    selectedProject,
    selectedFocusGroup,
    personas,
    focusGroups,
    setFocusGroups,
  } = useAppStore();
  const [showCreateForm, setShowCreateForm] = useState(false);

  const {
    isLoading,
    isError,
    error,
  } = useQuery<FocusGroup[]>({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      const data = await focusGroupsApi.getByProject(selectedProject!.id);
      setFocusGroups(data); // Update store immediately
      return data;
    },
    enabled: !!selectedProject,
    refetchInterval: (query) =>
      query.state.data?.some((group) => group.status === 'running') ? 2000 : false,
    onSuccess: (data) => {
      // Show toast when focus groups complete
      const previousRunning = focusGroups.filter(fg => fg.status === 'running');
      const nowCompleted = data.filter(fg =>
        fg.status === 'completed' &&
        previousRunning.some(prev => prev.id === fg.id)
      );

      nowCompleted.forEach(fg => {
        toast.success('Focus group completed!', `"${fg.name}" has finished`);
      });
    },
  });

  useEffect(() => {
    if (!selectedProject) {
      setFocusGroups([]);
    }
  }, [selectedProject, setFocusGroups]);

  const hasEnoughPersonas = (personas?.length ?? 0) >= 2;

  return (
    <FloatingPanel
      isOpen={activePanel === 'focus-groups'}
      onClose={() => setActivePanel(null)}
      title={`Focus Groups${focusGroups.length ? ` (${focusGroups.length})` : ''}`}
      panelKey="focus-groups"
      size="lg"
    >
      <div className="p-4 space-y-4">
        {!selectedProject ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600">Select a project first</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-600">
                Manage AI-simulated focus group sessions for the selected project.
              </div>
              <Button
                variant="secondary"
                onClick={() => setShowCreateForm((prev) => !prev)}
                disabled={!hasEnoughPersonas}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                {showCreateForm ? 'Hide form' : 'New focus group'}
              </Button>
            </div>

            {!hasEnoughPersonas && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
                Add at least two personas before creating a focus group.
              </div>
            )}

            {showCreateForm && hasEnoughPersonas && (
              <CreateFocusGroupForm onCancel={() => setShowCreateForm(false)} />
            )}

            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
              </div>
            ) : isError ? (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
                {error instanceof Error ? error.message : 'Unable to load focus groups.'}
              </div>
            ) : focusGroups.length > 0 ? (
              <div className="space-y-3">
                {focusGroups.map((focusGroup) => (
                  <FocusGroupCard
                    key={focusGroup.id}
                    focusGroup={focusGroup}
                    isSelected={selectedFocusGroup?.id === focusGroup.id}
                  />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
                <MessageSquare className="w-12 h-12 text-slate-300" />
                <div>
                  <p className="text-slate-600">No focus groups yet.</p>
                  <p className="text-sm text-slate-500">
                    Create a simulation to gather qualitative insights from your personas.
                  </p>
                </div>
                <Button
                  onClick={() => setShowCreateForm(true)}
                  disabled={!hasEnoughPersonas}
                  className="gap-2"
                >
                  <Plus className="w-4 h-4" /> Create focus group
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </FloatingPanel>
  );
}
