/**
 * ExecutionHistory - Historia wykonań workflow z auto-refresh
 *
 * Features:
 * - Lista wszystkich wykonań workflow (sorted od najnowszego)
 * - Timeline view z wizualną reprezentacją statusu
 * - Auto-polling co 5 sekund gdy któreś wykonanie ma status "running"
 * - Expandable rows - kliknięcie pokazuje szczegóły wykonania
 * - Refresh button do ręcznego odświeżania
 * - Empty state gdy brak wykonań
 * - Loading state podczas ładowania
 * - Error handling
 *
 * @example
 * // W Workflow Editor jako tab
 * <ExecutionHistory workflowId={workflowId} />
 *
 * @example
 * // W sidebar jako panel
 * <div className="w-96">
 *   <ExecutionHistory workflowId={workflowId} />
 * </div>
 */

import { useState, useEffect } from 'react';
import { RefreshCw, History, AlertCircle } from 'lucide-react';

import { useWorkflowExecutions } from '@/hooks/useWorkflowExecution';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ExecutionHistoryItem } from './ExecutionHistoryItem';

// ============================================
// PROPS INTERFACE
// ============================================

export interface ExecutionHistoryProps {
  workflowId: string;
}

// ============================================
// EMPTY STATE COMPONENT
// ============================================

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="rounded-full bg-gray-100 p-4 mb-4">
        <History className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Brak wykonań
      </h3>
      <p className="text-sm text-gray-500 max-w-sm">
        Uruchom ten workflow, aby zobaczyć historię wykonań. Wszystkie wykonania będą tutaj zapisywane.
      </p>
    </div>
  );
}

// ============================================
// ERROR STATE COMPONENT
// ============================================

interface ErrorStateProps {
  error: Error;
  onRetry: () => void;
}

function ErrorState({ error, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="rounded-full bg-red-100 p-4 mb-4">
        <AlertCircle className="w-8 h-8 text-red-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Błąd ładowania historii
      </h3>
      <p className="text-sm text-gray-500 max-w-sm mb-4">
        {error.message || 'Nie udało się pobrać historii wykonań workflow.'}
      </p>
      <Button variant="outline" onClick={onRetry}>
        <RefreshCw className="w-4 h-4 mr-2" />
        Spróbuj ponownie
      </Button>
    </div>
  );
}

// ============================================
// LOADING STATE COMPONENT
// ============================================

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mb-4" />
      <p className="text-sm text-gray-500">Ładowanie historii wykonań...</p>
    </div>
  );
}

// ============================================
// MAIN COMPONENT
// ============================================

export function ExecutionHistory({ workflowId }: ExecutionHistoryProps) {
  // ============================================
  // API Hooks
  // ============================================

  const {
    data: executions,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useWorkflowExecutions(workflowId);

  // ============================================
  // Local State
  // ============================================

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(false);

  // ============================================
  // Auto-Refresh Logic (Manual Implementation)
  // ============================================

  // useWorkflowExecutions już ma wbudowane auto-polling (refetchInterval),
  // ale tutaj dodajemy manual logic dla lepszej kontroli

  useEffect(() => {
    // Sprawdź czy są running executions
    const hasRunning = executions?.some((e) => e.status === 'running');

    if (hasRunning) {
      setIsAutoRefreshing(true);
      // TanStack Query już polluje przez refetchInterval w hook
      // Tutaj tylko ustawiamy UI state
    } else {
      setIsAutoRefreshing(false);
    }
  }, [executions]);

  // ============================================
  // Handlers
  // ============================================

  const handleRefresh = () => {
    refetch();
  };

  const handleToggleExpand = (executionId: string) => {
    setExpandedId((prev) => (prev === executionId ? null : executionId));
  };

  // ============================================
  // Render States
  // ============================================

  // Loading state (initial load)
  if (isLoading) {
    return (
      <div className="h-full flex flex-col">
        <LoadingState />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex flex-col">
        <ErrorState error={error as Error} onRetry={handleRefresh} />
      </div>
    );
  }

  // Empty state
  if (!executions || executions.length === 0) {
    return (
      <div className="h-full flex flex-col">
        <EmptyState />
      </div>
    );
  }

  // ============================================
  // Main Render
  // ============================================

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-3">
          <History className="w-5 h-5 text-gray-700" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Historia wykonań
            </h3>
            <p className="text-xs text-gray-500">
              {executions.length} {executions.length === 1 ? 'wykonanie' : 'wykonań'}
            </p>
          </div>
        </div>

        {/* Refresh Button */}
        <div className="flex items-center gap-2">
          {isAutoRefreshing && (
            <span className="text-xs text-blue-600 font-medium flex items-center gap-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              Auto-refresh włączony
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isFetching}
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`}
            />
            Odśwież
          </Button>
        </div>
      </div>

      {/* Execution List */}
      <ScrollArea className="flex-1">
        <div className="divide-y divide-gray-200">
          {executions.map((execution) => (
            <ExecutionHistoryItem
              key={execution.id}
              execution={execution}
              isExpanded={expandedId === execution.id}
              onToggle={() => handleToggleExpand(execution.id)}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Footer Info */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-500 text-center">
          {isAutoRefreshing
            ? 'Historia jest automatycznie odświeżana co 2 sekundy podczas trwania wykonania'
            : 'Wykonaj workflow, aby zobaczyć nowe wykonania w historii'}
        </p>
      </div>
    </div>
  );
}
