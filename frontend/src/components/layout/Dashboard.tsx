import { motion } from 'framer-motion';
import { useAppStore } from '@/store/appStore';
import {
  Users,
  MessageSquare,
  BarChart3,
  Clock,
  CheckCircle2,
  TrendingUp,
  Sparkles,
  Play,
  Target,
} from 'lucide-react';

function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  gradient = 'from-primary-500 to-primary-600',
  delay = 0,
}: {
  icon: any;
  label: string;
  value: string | number;
  trend?: string;
  gradient?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="relative overflow-hidden rounded-2xl bg-white border-2 border-slate-200 p-6 hover:border-primary-200 hover:shadow-xl transition-all duration-300"
    >
      {/* Background gradient blob */}
      <div className={`absolute -right-8 -top-8 w-32 h-32 bg-gradient-to-br ${gradient} opacity-10 rounded-full blur-2xl`} />

      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-600 mb-1">{label}</p>
          <p className="text-3xl font-bold text-slate-900">{value}</p>
          {trend && (
            <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-green-600" />
              {trend}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
}

function QuickAction({
  icon: Icon,
  label,
  description,
  onClick,
  disabled = false,
  gradient = 'from-primary-500 to-accent-500',
  delay = 0,
}: {
  icon: any;
  label: string;
  description: string;
  onClick: () => void;
  disabled?: boolean;
  gradient?: string;
  delay?: number;
}) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      whileHover={!disabled ? { scale: 1.02, y: -4 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      onClick={onClick}
      disabled={disabled}
      className={`relative overflow-hidden text-left p-6 rounded-2xl border-2 transition-all duration-300 ${
        disabled
          ? 'opacity-50 cursor-not-allowed border-slate-200 bg-slate-50'
          : 'border-slate-200 bg-white hover:border-primary-300 hover:shadow-xl cursor-pointer'
      }`}
    >
      {/* Gradient overlay on hover */}
      {!disabled && (
        <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 hover:opacity-5 transition-opacity duration-300`} />
      )}

      <div className="relative flex items-start gap-4">
        <div className={`flex-shrink-0 p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-bold text-slate-900 mb-1">{label}</h4>
          <p className="text-sm text-slate-600">{description}</p>
        </div>
      </div>
    </motion.button>
  );
}

function RecentActivity({ activities }: { activities: any[] }) {
  if (activities.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-sm text-slate-500">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {activities.map((activity, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="flex items-start gap-3 p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors"
        >
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center">
            <activity.icon className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900">{activity.title}</p>
            <p className="text-xs text-slate-500 mt-0.5">{activity.time}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { selectedProject, personas, focusGroups, setActivePanel } = useAppStore();

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md px-6"
        >
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mx-auto mb-6">
            <Target className="w-12 h-12 text-primary-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-3">Welcome to Market Research</h2>
          <p className="text-slate-600 mb-6">
            Select or create a project to start running AI-powered focus groups
          </p>
          <button
            onClick={() => setActivePanel('projects')}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg transition-shadow"
          >
            <Sparkles className="w-4 h-4 inline mr-2" />
            Get Started
          </button>
        </motion.div>
      </div>
    );
  }

  const completedFocusGroups = focusGroups.filter((fg) => fg.status === 'completed').length;
  const runningFocusGroups = focusGroups.filter((fg) => fg.status === 'running').length;
  const pendingFocusGroups = focusGroups.filter((fg) => fg.status === 'pending').length;

  // Mock recent activities
  const recentActivities = [
    ...(runningFocusGroups > 0
      ? [{ icon: Play, title: `${runningFocusGroups} focus group(s) running`, time: 'In progress' }]
      : []),
    ...(completedFocusGroups > 0
      ? [
          {
            icon: CheckCircle2,
            title: `${completedFocusGroups} focus group(s) completed`,
            time: 'Recently',
          },
        ]
      : []),
    ...(personas.length > 0
      ? [{ icon: Users, title: `${personas.length} personas generated`, time: 'Today' }]
      : []),
  ];

  return (
    <div className="h-full overflow-auto p-8 bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-slate-900 mb-2">{selectedProject.name}</h1>
          <p className="text-slate-600">{selectedProject.description || 'Market research project'}</p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={Users}
            label="Total Personas"
            value={personas.length}
            trend={personas.length > 0 ? 'Active' : undefined}
            gradient="from-blue-500 to-indigo-600"
            delay={0.1}
          />
          <StatCard
            icon={MessageSquare}
            label="Focus Groups"
            value={focusGroups.length}
            trend={runningFocusGroups > 0 ? `${runningFocusGroups} running` : undefined}
            gradient="from-purple-500 to-pink-600"
            delay={0.2}
          />
          <StatCard
            icon={CheckCircle2}
            label="Completed"
            value={completedFocusGroups}
            trend={completedFocusGroups > 0 ? 'Ready for analysis' : undefined}
            gradient="from-green-500 to-emerald-600"
            delay={0.3}
          />
          <StatCard
            icon={BarChart3}
            label="Insights"
            value={completedFocusGroups}
            trend={completedFocusGroups > 0 ? 'Available' : 'Pending'}
            gradient="from-orange-500 to-red-600"
            delay={0.4}
          />
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <QuickAction
              icon={Users}
              label="Generate Personas"
              description="Create AI-powered synthetic personas for research"
              onClick={() => setActivePanel('personas')}
              gradient="from-blue-500 to-indigo-600"
              delay={0.5}
            />
            <QuickAction
              icon={MessageSquare}
              label="Start Focus Group"
              description="Run AI-simulated focus group sessions"
              onClick={() => setActivePanel('focus-groups')}
              disabled={personas.length < 2}
              gradient="from-purple-500 to-pink-600"
              delay={0.6}
            />
            <QuickAction
              icon={BarChart3}
              label="View Analysis"
              description="Analyze completed focus group results with AI"
              onClick={() => setActivePanel('analysis')}
              disabled={completedFocusGroups === 0}
              gradient="from-green-500 to-emerald-600"
              delay={0.7}
            />
            <QuickAction
              icon={Sparkles}
              label="AI Insights"
              description="Get AI-powered insights and recommendations"
              onClick={() => setActivePanel('analysis')}
              disabled={completedFocusGroups === 0}
              gradient="from-orange-500 to-red-600"
              delay={0.8}
            />
          </div>
        </div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="bg-white rounded-2xl border-2 border-slate-200 p-6"
        >
          <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary-600" />
            Recent Activity
          </h3>
          <RecentActivity activities={recentActivities} />
        </motion.div>
      </div>
    </div>
  );
}
