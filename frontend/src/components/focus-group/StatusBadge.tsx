import { Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { cn } from '@/lib/utils';
import type { FocusGroup } from '@/types';

export function StatusBadge({ status }: { status: FocusGroup['status'] }) {
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
