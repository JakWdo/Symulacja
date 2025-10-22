import { ReactNode, useEffect } from 'react';
import { motion, AnimatePresence, useMotionValue, useDragControls } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore, PanelKey } from '@/store/appStore';

interface FloatingPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  position?: 'left' | 'right' | 'top' | 'bottom' | 'center';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  children: ReactNode;
  className?: string;
  panelKey?: PanelKey;
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
  lg: 'w-[56rem] h-[48rem]',
  xl: 'w-[64rem] h-[52rem]',
};

const sizeDimensions: Record<NonNullable<FloatingPanelProps['size']>, { width: number; height: number }> = {
  sm: { width: 320, height: 384 },
  md: { width: 384, height: 512 },
  lg: { width: 896, height: 768 },
  xl: { width: 1024, height: 832 },
};

export function FloatingPanel({
  isOpen,
  onClose,
  title,
  position = 'left',
  size = 'md',
  children,
  className,
  panelKey,
}: FloatingPanelProps) {
  const { panelPositions, setPanelPosition } = useAppStore();
  const motionX = useMotionValue(0);
  const motionY = useMotionValue(0);
  const dragControls = useDragControls();

  const supportsDrag = Boolean(panelKey);

  useEffect(() => {
    if (!panelKey) return;
    const stored = panelPositions[panelKey];
    if (!stored) {
      return;
    }

    const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 1920;
    const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 1080;
    const dims = sizeDimensions[size] ?? sizeDimensions.md;
    const safeX = clampPosition(stored.x, 12, viewportWidth - dims.width - 12);
    const safeY = clampPosition(stored.y, 12, viewportHeight - dims.height - 12);

    motionX.set(safeX);
    motionY.set(safeY);

    if (safeX !== stored.x || safeY !== stored.y) {
      setPanelPosition(panelKey, { x: safeX, y: safeY });
    }
  }, [panelKey, panelPositions, size, motionX, motionY, setPanelPosition]);

  const clampPosition = (value: number, min: number, max: number) =>
    Math.min(Math.max(value, min), max);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.92 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={cn(
            'fixed z-50 floating-panel flex flex-col pointer-events-auto',
            supportsDrag ? '' : positionClasses[position],
            sizeClasses[size],
            className
          )}
          style={
            supportsDrag
              ? ({
                  x: motionX,
                  y: motionY,
                  top: 0,
                  left: 0,
                } as const)
              : undefined
          }
          drag={supportsDrag}
          dragControls={dragControls}
          dragListener={false}
          dragMomentum={false}
          onDragEnd={(_, info) => {
            if (!panelKey) return;
            const stored = panelPositions[panelKey];
            const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 1920;
            const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 1080;
            const dims = sizeDimensions[size] ?? sizeDimensions.md;
            const newX = clampPosition(
              stored.x + info.offset.x,
              12,
              viewportWidth - dims.width - 12
            );
            const newY = clampPosition(
              stored.y + info.offset.y,
              12,
              viewportHeight - dims.height - 12
            );
            setPanelPosition(panelKey, { x: newX, y: newY });
            motionX.set(newX);
            motionY.set(newY);
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between p-4 border-b border-slate-200/60 cursor-grab active:cursor-grabbing select-none"
            onPointerDown={(event) => {
              if (!supportsDrag) return;
              dragControls.start(event);
            }}
          >
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
          <div
            className="flex-1 overflow-y-auto overscroll-contain pr-4 pl-4 pt-4 pb-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent"
            style={{ maxHeight: 'calc(100% - 4.25rem)' }}
          >
            {children}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
