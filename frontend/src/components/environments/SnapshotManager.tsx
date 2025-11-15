/**
 * Snapshot Manager Component
 *
 * UI do zarządzania snapshotami zasobów projektu.
 * Wspiera:
 * - Tworzenie snapshotów (personas, workflows)
 * - Listowanie snapshotów
 * - Preview resource IDs
 */

import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createProjectSnapshot,
  listProjectSnapshots,
  type SnapshotCreate,
} from '../../api/environments';

interface SnapshotManagerProps {
  projectId: string;
  className?: string;
}

export const SnapshotManager: React.FC<SnapshotManagerProps> = ({
  projectId,
  className = '',
}) => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [snapshotName, setSnapshotName] = useState('');
  const [resourceType, setResourceType] = useState<'persona' | 'workflow'>('persona');
  const [expandedSnapshot, setExpandedSnapshot] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch snapshots
  const { data: snapshots = [], isLoading } = useQuery({
    queryKey: ['projectSnapshots', projectId],
    queryFn: () => listProjectSnapshots(projectId),
    enabled: !!projectId,
  });

  // Create snapshot mutation
  const createMutation = useMutation({
    mutationFn: (data: SnapshotCreate) => createProjectSnapshot(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectSnapshots', projectId] });
      setShowCreateDialog(false);
      setSnapshotName('');
    },
  });

  const handleCreateSnapshot = () => {
    if (!snapshotName) return;

    createMutation.mutate({
      name: snapshotName,
      resource_type: resourceType,
    });
  };

  const toggleExpand = (snapshotId: string) => {
    setExpandedSnapshot(expandedSnapshot === snapshotId ? null : snapshotId);
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Snapshoty projektu</h3>
          <button
            onClick={() => setShowCreateDialog(!showCreateDialog)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
          >
            + Utwórz snapshot
          </button>
        </div>

        {/* Create Snapshot Dialog */}
        {showCreateDialog && (
          <div className="border rounded-lg p-4 bg-gray-50">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Nowy snapshot</h4>

            <div className="space-y-3">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nazwa snapshotu
                </label>
                <input
                  type="text"
                  value={snapshotName}
                  onChange={(e) => setSnapshotName(e.target.value)}
                  placeholder="np. Initial Research Snapshot"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              {/* Resource Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Typ zasobu
                </label>
                <select
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value as 'persona' | 'workflow')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="persona">Persony</option>
                  <option value="workflow">Workflows</option>
                </select>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={handleCreateSnapshot}
                  disabled={!snapshotName || createMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Tworzenie...' : 'Utwórz'}
                </button>
                <button
                  onClick={() => {
                    setShowCreateDialog(false);
                    setSnapshotName('');
                  }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  Anuluj
                </button>
              </div>

              {/* Error */}
              {createMutation.error && (
                <div className="text-sm text-red-600">
                  Błąd: {(createMutation.error as Error).message}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Snapshots List */}
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Ładowanie snapshotów...</div>
        ) : snapshots.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            Brak snapshotów. Utwórz pierwszy snapshot aby „zamrozić" aktualny stan zasobów.
          </div>
        ) : (
          <div className="space-y-3">
            {snapshots.map((snapshot) => (
              <div key={snapshot.id} className="border rounded-lg overflow-hidden">
                {/* Snapshot Header */}
                <button
                  onClick={() => toggleExpand(snapshot.id)}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left flex items-center justify-between"
                >
                  <div>
                    <div className="font-medium text-gray-900">{snapshot.name}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      {snapshot.resource_type === 'persona' ? 'Persony' : 'Workflows'} •{' '}
                      {snapshot.resource_ids.length} zasobów •{' '}
                      {new Date(snapshot.created_at).toLocaleDateString('pl-PL')}
                    </div>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-400 transform transition-transform ${
                      expandedSnapshot === snapshot.id ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {/* Snapshot Details (Expanded) */}
                {expandedSnapshot === snapshot.id && (
                  <div className="px-4 py-3 bg-white border-t">
                    <div className="text-sm text-gray-600 mb-2">Resource IDs:</div>
                    <div className="max-h-40 overflow-y-auto bg-gray-50 rounded p-2">
                      <pre className="text-xs text-gray-700 font-mono">
                        {JSON.stringify(snapshot.resource_ids, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
