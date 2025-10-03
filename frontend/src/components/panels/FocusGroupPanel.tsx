import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
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
  Plus,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn, formatDate, formatTime } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import type { FocusGroup } from '@/types';

function StatusBadge({ status }: { status: FocusGroup['status'] }) {
  const configs = {
    pending: {
      icon: Clock,
      gradient: 'from-slate-500 to-slate-600',
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      label: 'Pending',
    },
    running: {
      icon: Loader2,
      gradient: 'from-blue-500 to-indigo-600',
      bg: 'bg-blue-100',
      text: 'text-blue-700',
      label: 'Running',
      animate: true,
    },
    completed: {
      icon: CheckCircle2,
      gradient: 'from-green-500 to-emerald-600',
      bg: 'bg-green-100',
      text: 'text-green-700',
      label: 'Completed',
    },
    failed: {
      icon: AlertCircle,
      gradient: 'from-red-500 to-rose-600',
      bg: 'bg-red-100',
      text: 'text-red-700',
      label: 'Failed',
    },
  } as const;

  const config = configs[status];
  const Icon = config.icon;

  return (
    <div className={cn('inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full', config.bg)}>
      <Icon className={cn('w-3.5 h-3.5', config.text, config.animate && 'animate-spin')} />
      <span className={cn('text-xs font-semibold', config.text)}>{config.label}</span>
    </div>
  );
}

function FocusGroupCard({
  focusGroup,
  isSelected,
  index,
}: {
  focusGroup: FocusGroup;
  isSelected: boolean;
  index: number;
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

  const canRun = focusGroup.status === 'pending';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      onClick={() => setSelectedFocusGroup(focusGroup)}
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
              {focusGroup.persona_ids.length} personas
            </span>
            <span className="flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5" />
              {focusGroup.questions.length} questions
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
                <div className="text-xs text-slate-500 mb-1">Avg Response</div>
                <div className="text-sm font-bold text-slate-900">
                  {formatTime(focusGroup.avg_response_time_ms)}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200">
                <div className="text-xs text-slate-500 mb-1">Total Time</div>
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
                  <div className="font-semibold mb-1">Execution Failed</div>
                  <div className="text-red-600">
                    Check logs. Common: API quota, network issues, invalid personas.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action button */}
        {canRun && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRun}
            disabled={runMutation.isPending}
            className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {runMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
          </motion.button>
        )}
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

function CreateFocusGroupForm({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const { selectedProject, personas } = useAppStore();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [questions, setQuestions] = useState(['']);
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([]);

  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string; questions: string[]; persona_ids: string[] }) =>
      focusGroupsApi.create(selectedProject!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups'] });
      toast.success('Focus group created', 'Successfully created new focus group');
      onSuccess();
      onClose();
    },
    onError: (error: Error) => {
      toast.error('Failed to create focus group', error.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validQuestions = questions.filter((q) => q.trim().length > 0);
    createMutation.mutate({
      name,
      description: description || undefined,
      questions: validQuestions,
      persona_ids: selectedPersonas,
    });
  };

  const canSubmit = name.trim() && questions.some((q) => q.trim()) && selectedPersonas.length >= 2;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Focus Group Name *
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-primary-400 focus:ring-4 focus:ring-primary-100 transition-all outline-none"
          placeholder="e.g., Product Feedback Session"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Description (optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-primary-400 focus:ring-4 focus:ring-primary-100 transition-all outline-none resize-none"
          placeholder="Brief description of this focus group..."
        />
      </div>

      {/* Questions */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Questions *
        </label>
        <div className="space-y-2">
          {questions.map((q, idx) => (
            <div key={idx} className="flex gap-2">
              <input
                type="text"
                value={q}
                onChange={(e) => {
                  const newQuestions = [...questions];
                  newQuestions[idx] = e.target.value;
                  setQuestions(newQuestions);
                }}
                className="flex-1 px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-primary-400 focus:ring-4 focus:ring-primary-100 transition-all outline-none"
                placeholder={`Question ${idx + 1}`}
              />
              {questions.length > 1 && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setQuestions(questions.filter((_, i) => i !== idx))}
                >
                  Remove
                </Button>
              )}
            </div>
          ))}
          <Button
            type="button"
            variant="secondary"
            onClick={() => setQuestions([...questions, ''])}
            className="w-full"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Question
          </Button>
        </div>
      </div>

      {/* Persona Selection */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Select Personas * (min. 2)
        </label>
        <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto p-2 rounded-xl border-2 border-slate-200">
          {personas.map((persona) => (
            <label
              key={persona.id}
              className={cn(
                'flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all',
                selectedPersonas.includes(persona.id)
                  ? 'bg-primary-100 border-2 border-primary-400'
                  : 'bg-slate-50 border-2 border-transparent hover:border-slate-300'
              )}
            >
              <input
                type="checkbox"
                checked={selectedPersonas.includes(persona.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedPersonas([...selectedPersonas, persona.id]);
                  } else {
                    setSelectedPersonas(selectedPersonas.filter((id) => id !== persona.id));
                  }
                }}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-sm text-slate-700 truncate">
                {persona.full_name || `${persona.age}y ${persona.gender}`}
              </span>
            </label>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Selected: {selectedPersonas.length} / {personas.length}
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={!canSubmit || createMutation.isPending}
          isLoading={createMutation.isPending}
          className="flex-1"
        >
          Create Focus Group
        </Button>
      </div>
    </form>
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

  const { isLoading, isError, error } = useQuery<FocusGroup[]>({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      const data = await focusGroupsApi.getByProject(selectedProject!.id);
      setFocusGroups(data);
      return data;
    },
    enabled: !!selectedProject,
    refetchInterval: (query) =>
      query.state.data?.some((group) => group.status === 'running') ? 2000 : false,
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
      {!selectedProject ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center mb-6">
            <MessageSquare className="w-10 h-10 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Project Selected</h3>
          <p className="text-sm text-slate-500">Select a project to view focus groups</p>
        </div>
      ) : showCreateForm ? (
        <CreateFocusGroupForm
          onClose={() => setShowCreateForm(false)}
          onSuccess={() => setShowCreateForm(false)}
        />
      ) : (
        <>
          {/* Header */}
          <div className="mb-6">
            <Button
              onClick={() => setShowCreateForm(true)}
              disabled={!hasEnoughPersonas}
              className="w-full bg-gradient-to-r from-primary-500 to-accent-500 hover:from-primary-600 hover:to-accent-600"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Create New Focus Group
            </Button>
            {!hasEnoughPersonas && (
              <p className="text-xs text-amber-600 mt-2">
                Need at least 2 personas to create a focus group
              </p>
            )}
          </div>

          {/* Focus Groups List */}
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin mb-4" />
              <p className="text-sm text-slate-600">Loading focus groups...</p>
            </div>
          ) : isError ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-sm text-red-600">{error?.message || 'Failed to load focus groups'}</p>
            </div>
          ) : focusGroups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-primary-600" />
              </div>
              <p className="text-sm text-slate-500">No focus groups yet</p>
              <p className="text-xs text-slate-400 mt-1">Create your first one above</p>
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
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </>
      )}
    </FloatingPanel>
  );
}
