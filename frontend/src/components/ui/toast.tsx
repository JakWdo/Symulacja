import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { useToastStore, type Toast } from './toastStore';

function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToastStore();

  const icons = {
    success: CheckCircle2,
    error: AlertCircle,
    info: Info,
  };

  const palettes = {
    success: {
      gradient: 'from-card via-card to-card',
      border: 'border-success',
      text: 'text-foreground',
      icon: 'text-brand bg-brand-muted',
    },
    error: {
      gradient: 'from-card via-card to-card',
      border: 'border-error',
      text: 'text-foreground',
      icon: 'text-error bg-error-muted',
    },
    info: {
      gradient: 'from-card via-card to-card',
      border: 'border-info',
      text: 'text-foreground',
      icon: 'text-info bg-info-muted',
    },
  };

  const Icon = icons[toast.type];
  const palette = palettes[toast.type];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={`relative overflow-hidden rounded-2xl border bg-gradient-to-br ${palette.border} ${palette.gradient} ${palette.text} shadow-lg max-w-md`}
    >
      <span className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-brand to-info" aria-hidden />
      <div className="flex items-start gap-3 p-4">
        <div className={`h-9 w-9 rounded-full flex items-center justify-center ${palette.icon}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold tracking-tight text-base">{toast.title}</h4>
          {toast.message && (
            <p className="text-sm opacity-80 mt-1 leading-relaxed">{toast.message}</p>
          )}
          {toast.actionLabel && toast.onAction && (
            <button
              onClick={() => {
                toast.onAction?.();
                removeToast(toast.id);
              }}
              className="mt-3 inline-flex items-center justify-center rounded-md bg-primary/90 px-3 py-1 text-xs font-semibold text-white shadow hover:bg-primary"
            >
              {toast.actionLabel}
            </button>
          )}
        </div>
        <button
          onClick={() => removeToast(toast.id)}
          className="p-1 rounded-lg bg-muted hover:bg-muted/80 transition-colors text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
}

export function ToastContainer() {
  const { toasts } = useToastStore();

  return (
    <div className="fixed top-20 right-6 z-50 space-y-3 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastItem toast={toast} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}

// Helper function to show toasts
