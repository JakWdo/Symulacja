import { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FloatingPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  position: 'left' | 'right' | 'top' | 'bottom' | 'center';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  children: ReactNode;
  className?: string;
}

const positionClasses = {
  left: 'left-6 top-1/2 -translate-y-1/2',
  right: 'right-6 top-1/2 -translate-y-1/2',
  top: 'top-6 left-1/2 -translate-x-1/2',
  bottom: 'bottom-6 left-1/2 -translate-x-1/2',
  center: 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
};

const sizeClasses = {
  sm: 'w-80 h-96',
  md: 'w-96 h-[32rem]',
  lg: 'w-[32rem] h-[40rem]',
  xl: 'w-[48rem] h-[48rem]',
};

export function FloatingPanel({
  isOpen,
  onClose,
  title,
  position,
  size = 'md',
  children,
  className,
}: FloatingPanelProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: position === 'bottom' ? 20 : -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: position === 'bottom' ? 20 : -20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={cn(
            'fixed z-50 floating-panel flex flex-col',
            positionClasses[position],
            sizeClasses[size],
            className
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-200/50">
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="Close panel"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto" style={{ maxHeight: 'calc(100% - 4rem)' }}>
            {children}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}