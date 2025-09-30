import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { MessageSquare, Play, Clock, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { formatDate, formatTime, formatPercentage } from '@/lib/utils';
import type { FocusGroup } from '@/types';

function StatusBadge({ status }: { status: FocusGroup['status'] }) {
  const configs = {
    pending: { icon: Clock, color: 'text-slate-600 bg-slate-100', label: 'Pending' },
    running: { icon: Loader2, color: 'text-blue-600 bg-blue-100 animate-pulse', label: 'Running' },
    completed: { icon: CheckCircle2, color: 'text-green-600 bg-green-100', label: 'Completed' },
    failed: { icon: AlertCircle, color: 'text-red-600 bg-red-100', label: 'Failed' },
  };

  const config = configs[status];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${config.color}`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

function FocusGroupCard({ focusGroup }: { focusGroup: FocusGroup }) {
  const { setSelectedFocusGroup } = useAppStore();
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: () => focusGroupsApi.run(focusGroup.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['focus-groups'] });
    },
  });

  const handleRun = (e: React.MouseEvent) => {
    e.stopPropagation();
    runMutation.mutate();
  };

  const meetsRequirements = focusGroup.status === 'completed' && focusGroup.avg_response_time_ms
    ? focusGroup.avg_response_time_ms <= 3000 &&
      (focusGroup.total_execution_time_ms || 0) <= 30000 &&
      (focusGroup.consistency_error_rate || 0) <= 0.05
    : null;

  return (
    <div
      onClick={() => setSelectedFocusGroup(focusGroup)}
      className="node-card cursor-pointer group"
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

          {/* Performance Metrics */}
          {focusGroup.status === 'completed' && focusGroup.avg_response_time_ms && (
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
                  {formatTime(focusGroup.total_execution_time_ms || 0)}
                </div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500">Consistency</div>
                <div className="text-sm font-semibold text-slate-900">
                  {formatPercentage(1 - (focusGroup.consistency_error_rate || 0))}
                </div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500">Polarization</div>
                <div className="text-sm font-semibold text-slate-900">
                  {focusGroup.polarization_score
                    ? (focusGroup.polarization_score * 100).toFixed(1)
                    : 'N/A'}
                </div>
              </div>
            </div>
          )}

          {/* Requirements Badge */}
          {meetsRequirements !== null && (
            <div className={`px-3 py-2 rounded-lg ${meetsRequirements ? 'bg-green-50' : 'bg-yellow-50'}`}>
              <div className="flex items-center gap-2">
                {meetsRequirements ? (
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-yellow-600" />
                )}
                <span className={`text-xs font-medium ${meetsRequirements ? 'text-green-700' : 'text-yellow-700'}`}>
                  {meetsRequirements ? 'Meets all requirements' : 'Some requirements not met'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Run Button */}
        {focusGroup.status === 'pending' && (
          <button
            onClick={handleRun}
            disabled={runMutation.isPending}
            className="floating-button p-3"
            title="Run focus group"
          >
            {runMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export function FocusGroupPanel() {
  const { activePanel, setActivePanel, selectedProject, setFocusGroups } = useAppStore();
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data: focusGroups, isLoading } = useQuery({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      const response = await focusGroupsApi.getByProject(selectedProject.id);
      return response.data;
    },
    enabled: !!selectedProject,
    refetchInterval: (data) => {
      // Refresh every 5s if any focus group is running
      const isStillRunning = data?.messages?.some(
        (message) => message.status === 'in_progress'
      );
      return isStillRunning ? 1000 : false;
    },
  });

  // Update store
  if (focusGroups) {
    setFocusGroups(focusGroups);
  }

  return (
    <FloatingPanel
      isOpen={activePanel === 'focus-groups'}
      onClose={() => setActivePanel(null)}
      title={`Focus Groups ${focusGroups ? `(${focusGroups.length})` : ''}`}
      position="left"
      size="lg"
    >
      <div className="p-4">
        {!selectedProject ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600">Select a project first</p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
          </div>
        ) : focusGroups && focusGroups.length > 0 ? (
          <div className="space-y-3">
            {focusGroups.map((focusGroup) => (
              <FocusGroupCard key={focusGroup.id} focusGroup={focusGroup} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600 mb-4">No focus groups yet</p>
            <button className="floating-button" onClick={() => setShowCreateForm(true)}>
              Create Focus Group
            </button>
          </div>
        )}
      </div>
    </FloatingPanel>
  );
}