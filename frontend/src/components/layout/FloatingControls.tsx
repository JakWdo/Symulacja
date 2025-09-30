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
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';

const controls = [
  { id: 'projects', icon: FolderOpen, label: 'Projects', position: 'top' },
  { id: 'personas', icon: Users, label: 'Personas', position: 'middle' },
  { id: 'focus-groups', icon: MessageSquare, label: 'Focus Groups', position: 'middle' },
  { id: 'analysis', icon: BarChart3, label: 'Analysis', position: 'bottom' },
];

export function FloatingControls() {
  const { activePanel, setActivePanel, showLabels, toggleLabels, graphLayout, setGraphLayout } =
    useAppStore();

  return (
    <>
      {/* Main Control Bar - Left Side */}
      <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="fixed left-6 top-1/2 -translate-y-1/2 z-40"
      >
        <div className="floating-panel p-2 space-y-2">
          {controls.map((control, idx) => (
            <motion.button
              key={control.id}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3 + idx * 0.1 }}
              onClick={() =>
                setActivePanel(
                  activePanel === control.id ? null : (control.id as any)
                )
              }
              className={cn(
                'w-12 h-12 rounded-xl flex items-center justify-center transition-all',
                'hover:bg-primary-50 hover:text-primary-600',
                activePanel === control.id
                  ? 'bg-primary-500 text-white'
                  : 'text-slate-600'
              )}
              title={control.label}
            >
              <control.icon className="w-5 h-5" />
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* View Controls - Bottom Right */}
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="fixed bottom-6 right-6 z-40"
      >
        <div className="floating-panel p-2 flex gap-2">
          <button
            onClick={() => setGraphLayout(graphLayout === '2d' ? '3d' : '2d')}
            className={cn(
              'px-4 py-2 rounded-lg transition-all',
              'hover:bg-slate-100 text-slate-700'
            )}
            title={`Switch to ${graphLayout === '2d' ? '3D' : '2D'} view`}
          >
            <Grid3X3 className="w-5 h-5" />
          </button>

          <button
            onClick={toggleLabels}
            className={cn(
              'px-4 py-2 rounded-lg transition-all',
              'hover:bg-slate-100',
              showLabels ? 'text-primary-600' : 'text-slate-400'
            )}
            title={showLabels ? 'Hide labels' : 'Show labels'}
          >
            {showLabels ? (
              <Eye className="w-5 h-5" />
            ) : (
              <EyeOff className="w-5 h-5" />
            )}
          </button>
        </div>
      </motion.div>
    </>
  );
}