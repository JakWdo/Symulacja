import { motion } from 'framer-motion';
import {
  FolderOpen,
  Users,
  MessageSquare,
  BarChart3,
  Grid3X3,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useAppStore, PanelKey } from '@/store/appStore';
import { cn } from '@/lib/utils';

const controls: Array<{ id: PanelKey; icon: typeof FolderOpen; label: string }> = [
  { id: 'projects', icon: FolderOpen, label: 'Projects' },
  { id: 'personas', icon: Users, label: 'Personas' },
  { id: 'focus-groups', icon: MessageSquare, label: 'Focus Groups' },
  { id: 'analysis', icon: BarChart3, label: 'Analysis' },
];

export function FloatingControls() {
  const {
    activePanel,
    setActivePanel,
    showLabels,
    toggleLabels,
    graphLayout,
    setGraphLayout,
  } = useAppStore();

  const handleToggle = (panel: PanelKey) => {
    setActivePanel(activePanel === panel ? null : panel);
  };

  return (
    <>
      <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="fixed left-6 top-1/2 -translate-y-1/2 z-60"
      >
        <div className="floating-panel p-2 space-y-2">
          {controls.map(({ id, icon: Icon, label }, index) => (
            <motion.button
              key={id}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              onClick={() => handleToggle(id)}
              className={cn(
                'w-12 h-12 rounded-xl flex items-center justify-center transition-all',
                'hover:bg-primary-50 hover:text-primary-600',
                activePanel === id ? 'bg-primary-500 text-white shadow-lg' : 'text-slate-600'
              )}
              title={label}
            >
              <Icon className="w-5 h-5" />
              <span className="sr-only">{label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>

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
