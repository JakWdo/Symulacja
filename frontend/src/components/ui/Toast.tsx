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
      gradient: 'from-[#FFF5EB] via-[#FFFFFF] to-[#FFFDF8]',
      border: 'border-[#F5B97F]',
      text: 'text-[#4A3828]',
      icon: 'text-[#F27405] bg-[#F27405]/15',
    },
    error: {
      gradient: 'from-[#FFEAE3] via-[#FFF5F1] to-[#FFFFFF]',
      border: 'border-[#F59B7F]',
      text: 'text-[#4A2A26]',
      icon: 'text-[#D64545] bg-[#D64545]/15',
    },
    info: {
      gradient: 'from-[#FFF3E6] via-[#FFFFFF] to-[#FFFDF8]',
      border: 'border-[#F5C67F]',
      text: 'text-[#433027]',
      icon: 'text-[#F29F05] bg-[#F29F05]/15',
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
      <span className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-brand-orange to-brand-gold" aria-hidden />
      <div className="flex items-start gap-3 p-4">
        <div className={`h-9 w-9 rounded-full flex items-center justify-center ${palette.icon}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold tracking-tight text-base">{toast.title}</h4>
          {toast.message && (
            <p className="text-sm opacity-80 mt-1 leading-relaxed">{toast.message}</p>
          )}
        </div>
        <button
          onClick={() => removeToast(toast.id)}
          className="p-1 rounded-lg bg-white/40 hover:bg-white/60 transition-colors text-slate-500 hover:text-slate-700"
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
