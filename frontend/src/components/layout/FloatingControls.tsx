import { motion } from 'framer-motion';
import { Grid3X3, Eye, EyeOff } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';

export function FloatingControls() {
  const {
    showLabels,
    toggleLabels,
    graphLayout,
    setGraphLayout,
  } = useAppStore();

  return (
    <>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="fixed bottom-6 right-6 z-60"
      >
        <div className="floating-panel p-2 flex gap-2">
          <button
            onClick={() => setGraphLayout(graphLayout === '2d' ? '3d' : '2d')}
            className={cn(
              'px-4 py-2 rounded-lg transition-all text-slate-700',
              'hover:bg-slate-100'
            )}
            title={`Switch to ${graphLayout === '2d' ? '3D' : '2D'} view`}
          >
            <Grid3X3 className="w-5 h-5" />
          </button>

          <button
            onClick={toggleLabels}
            className={cn(
              'px-4 py-2 rounded-lg transition-all',
              showLabels ? 'text-primary-600 hover:bg-primary-50' : 'text-slate-400 hover:bg-slate-100'
            )}
            title={showLabels ? 'Hide labels' : 'Show labels'}
          >
            {showLabels ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
          </button>
        </div>
      </motion.div>
    </>
  );
}
