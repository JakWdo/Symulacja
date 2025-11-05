/**
 * ExecutionHistoryItem - Pojedynczy item w historii wykonań workflow
 *
 * Features:
 * - Collapsible row (expand/collapse szczegółów)
 * - Status badge z ikoną i kolorem
 * - Formatted timestamps (date-fns)
 * - Duration calculation i formatting
 * - JSON viewer dla result_data (collapsible)
 * - Error message display dla failed executions
 * - Execution ID z możliwością kopiowania
 *
 * @example
 * <ExecutionHistoryItem
 *   execution={execution}
 *   isExpanded={expandedId === execution.id}
 *   onToggle={() => setExpandedId(expandedId === execution.id ? null : execution.id)}
 * />
 */

import { useState } from 'react';
import { format } from 'date-fns';
import { pl } from 'date-fns/locale';
import {
  Clock,
  Loader,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
} from 'lucide-react';

import type { WorkflowExecution } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

// ============================================
// HELPERS
// ============================================

/**
 * Oblicza duration wykonania w czytelnym formacie
 */
function calculateDuration(startedAt: string | null, completedAt: string | null): string {
  if (!startedAt) return 'Not started';

  const start = new Date(startedAt);
  const end = completedAt ? new Date(completedAt) : new Date();
  const durationMs = end.getTime() - start.getTime();

  const seconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

/**
 * Formatuje timestamp do czytelnej daty
 */
function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return '-';
  return format(new Date(timestamp), 'dd MMM yyyy, HH:mm:ss', { locale: pl });
}

// ============================================
// STATUS BADGE COMPONENT
// ============================================

interface StatusBadgeProps {
  status: WorkflowExecution['status'];
}

function StatusBadge({ status }: StatusBadgeProps) {
  const config = {
    pending: {
      variant: 'secondary' as const,
      icon: Clock,
      label: 'Oczekuje',
      className: 'bg-gray-100 text-gray-800 border-gray-200',
    },
    running: {
      variant: 'default' as const,
      icon: Loader,
      label: 'W trakcie',
      className: 'bg-blue-100 text-blue-800 border-blue-200',
      animate: true,
    },
    completed: {
      variant: 'default' as const,
      icon: CheckCircle,
      label: 'Zakończone',
      className: 'bg-green-100 text-green-800 border-green-200',
    },
    failed: {
      variant: 'destructive' as const,
      icon: XCircle,
      label: 'Błąd',
      className: 'bg-red-100 text-red-800 border-red-200',
    },
  };

  const { icon: Icon, label, className, animate } = config[status];

  return (
    <Badge variant="outline" className={cn('gap-1.5', className)}>
      <Icon className={cn('w-3 h-3', animate && 'animate-spin')} />
      {label}
    </Badge>
  );
}

// ============================================
// JSON VIEWER COMPONENT
// ============================================

interface JsonViewerProps {
  data: Record<string, any> | null;
}

function JsonViewer({ data }: JsonViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!data || Object.keys(data).length === 0) {
    return <p className="text-gray-400 text-sm italic">Brak danych wynikowych</p>;
  }

  return (
    <div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-blue-600 hover:text-blue-700 px-0"
      >
        {isExpanded ? (
          <>
            <ChevronDown className="w-4 h-4 mr-1" />
            Ukryj dane wynikowe
          </>
        ) : (
          <>
            <ChevronRight className="w-4 h-4 mr-1" />
            Pokaż dane wynikowe
          </>
        )}
      </Button>
      {isExpanded && (
        <pre className="mt-2 p-4 bg-gray-50 border border-gray-200 rounded-md overflow-x-auto text-xs font-mono">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

// ============================================
// COPY BUTTON COMPONENT
// ============================================

interface CopyButtonProps {
  text: string;
}

function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleCopy}
      className="h-6 px-2"
    >
      {copied ? (
        <>
          <Check className="w-3 h-3 mr-1 text-green-600" />
          <span className="text-xs text-green-600">Skopiowano!</span>
        </>
      ) : (
        <>
          <Copy className="w-3 h-3 mr-1" />
          <span className="text-xs">Kopiuj ID</span>
        </>
      )}
    </Button>
  );
}

// ============================================
// MAIN COMPONENT
// ============================================

export interface ExecutionHistoryItemProps {
  execution: WorkflowExecution;
  isExpanded: boolean;
  onToggle: () => void;
}

export function ExecutionHistoryItem({
  execution,
  isExpanded,
  onToggle,
}: ExecutionHistoryItemProps) {
  const duration = calculateDuration(execution.started_at, execution.completed_at);
  const isRunning = execution.status === 'running';

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      {/* Header Row (always visible) */}
      <CollapsibleTrigger asChild>
        <div
          className={cn(
            'flex items-center justify-between p-4 border-b border-gray-200 cursor-pointer',
            'hover:bg-gray-50 transition-colors',
            isExpanded && 'bg-gray-50'
          )}
        >
          <div className="flex items-center gap-4 flex-1">
            {/* Expand/Collapse Icon */}
            <div className="text-gray-400">
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </div>

            {/* Status Badge */}
            <StatusBadge status={execution.status} />

            {/* Started At */}
            <div className="flex flex-col">
              <span className="text-sm text-gray-600">
                {formatTimestamp(execution.started_at)}
              </span>
              {execution.started_at && (
                <span className="text-xs text-gray-400">
                  Rozpoczęte
                </span>
              )}
            </div>

            {/* Duration */}
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-gray-900">
                {duration}
              </span>
              <span className="text-xs text-gray-400">
                {isRunning ? 'Trwa...' : 'Czas trwania'}
              </span>
            </div>
          </div>

          {/* Current Step Indicator (if running) */}
          {isRunning && execution.current_step_id && (
            <div className="text-xs text-gray-500 mr-4">
              Krok: <span className="font-mono">{execution.current_step_id}</span>
            </div>
          )}
        </div>
      </CollapsibleTrigger>

      {/* Expanded Details */}
      <CollapsibleContent>
        <div className="p-6 bg-gray-50 border-b border-gray-200 space-y-4">
          {/* Execution ID */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">
                Execution ID
              </span>
              <p className="text-sm font-mono text-gray-700 mt-0.5">
                {execution.id}
              </p>
            </div>
            <CopyButton text={execution.id} />
          </div>

          {/* Timestamps Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">
                Rozpoczęte
              </span>
              <p className="text-sm text-gray-700 mt-0.5">
                {formatTimestamp(execution.started_at)}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">
                Zakończone
              </span>
              <p className="text-sm text-gray-700 mt-0.5">
                {formatTimestamp(execution.completed_at)}
              </p>
            </div>
          </div>

          {/* Triggered By */}
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wide">
              Uruchomione przez
            </span>
            <p className="text-sm text-gray-700 mt-0.5">
              {execution.triggered_by}
            </p>
          </div>

          {/* Error Message (if failed) */}
          {execution.status === 'failed' && execution.error_message && (
            <div>
              <span className="text-xs text-red-600 uppercase tracking-wide font-semibold">
                Błąd
              </span>
              <div className="mt-2 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-700 font-mono whitespace-pre-wrap">
                  {execution.error_message}
                </p>
              </div>
            </div>
          )}

          {/* Result Data (if completed) */}
          {execution.status === 'completed' && (
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">
                Dane wynikowe
              </span>
              <div className="mt-2">
                <JsonViewer data={execution.result_data} />
              </div>
            </div>
          )}

          {/* Current Step (if running) */}
          {execution.status === 'running' && execution.current_step_id && (
            <div>
              <span className="text-xs text-blue-600 uppercase tracking-wide font-semibold">
                Aktualny krok
              </span>
              <p className="text-sm text-gray-700 mt-0.5 font-mono">
                {execution.current_step_id}
              </p>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
