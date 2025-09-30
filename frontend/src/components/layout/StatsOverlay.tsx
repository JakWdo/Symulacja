import { motion } from 'framer-motion';
import { useAppStore } from '@/store/appStore';
import { Users, GitBranch, Activity } from 'lucide-react';

export function StatsOverlay() {
  const { graphData, personas, focusGroups } = useAppStore();

  if (!graphData) return null;

  const stats = [
    {
      label: 'Personas',
      value: personas.length,
      icon: Users,
      color: 'text-primary-600',
      bg: 'bg-primary-50',
    },
    {
      label: 'Connections',
      value: graphData.links.length,
      icon: GitBranch,
      color: 'text-accent-600',
      bg: 'bg-accent-50',
    },
    {
      label: 'Focus Groups',
      value: focusGroups.length,
      icon: Activity,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
  ];

  return (
    <motion.div
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="fixed top-6 right-6 z-40 flex gap-3"
    >
      {stats.map((stat, idx) => (
        <motion.div
          key={stat.label}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.4 + idx * 0.1, type: 'spring' }}
          className="stat-card"
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${stat.bg}`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
              <div className="text-xs text-slate-600">{stat.label}</div>
            </div>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}