import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { MessageSquare, Play, Clock, AlertCircle, Users, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn, formatDate, formatTime } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { FocusGroup } from '@/types';
import { StatusBadge } from './StatusBadge';

interface FocusGroupCardProps {
  focusGroup: FocusGroup;
  isSelected: boolean;
  index: number;
  onEdit: () => void;
}

export function FocusGroupCard({
  focusGroup,
  isSelected,
  index,
  onEdit,
}: FocusGroupCardProps) {
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
