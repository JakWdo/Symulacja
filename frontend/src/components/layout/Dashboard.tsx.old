import { useAppStore } from '@/store/appStore';
import { Users, MessageSquare, BarChart3, Clock, CheckCircle2, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  color = "primary"
}: {
  icon: any;
  label: string;
  value: string | number;
  trend?: string;
  color?: string;
}) {
  const colorMap = {
    primary: "from-primary-100 to-primary-50 text-primary-700 border-primary-200",
    accent: "from-accent-100 to-accent-50 text-accent-700 border-accent-200",
    green: "from-green-100 to-green-50 text-green-700 border-green-200",
    blue: "from-blue-100 to-blue-50 text-blue-700 border-blue-200",
  };
  const colorClasses = colorMap[color] || colorMap.primary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`floating-panel p-6 bg-gradient-to-br ${colorClasses} border-2`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium opacity-80 mb-1">{label}</p>
          <p className="text-3xl font-bold">{value}</p>
          {trend && (
            <p className="text-xs opacity-70 mt-2 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </p>
          )}
        </div>
        <div className="p-3 rounded-xl bg-white/50">
          <Icon className="w-6 h-6" />
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
  disabled = false
}: {
  icon: any;
  label: string;
  description: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={`floating-panel p-5 text-left transition-all ${
        disabled
          ? 'opacity-50 cursor-not-allowed'
          : 'hover:shadow-xl hover:border-primary-300 cursor-pointer'
      }`}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100">
          <Icon className="w-5 h-5 text-primary-700" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-slate-900 mb-1">{label}</h4>
          <p className="text-sm text-slate-600">{description}</p>
        </div>
      </div>
    </motion.button>
  );
}

function RecentActivity({ activities }: { activities: any[] }) {
  if (activities.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-slate-500">
        No recent activity
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
          className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
        >
          <div className={`p-2 rounded-lg ${
            activity.type === 'persona' ? 'bg-primary-100 text-primary-700' :
            activity.type === 'focus-group' ? 'bg-accent-100 text-accent-700' :
            'bg-green-100 text-green-700'
          }`}>
            {activity.type === 'persona' && <Users className="w-4 h-4" />}
            {activity.type === 'focus-group' && <MessageSquare className="w-4 h-4" />}
            {activity.type === 'analysis' && <BarChart3 className="w-4 h-4" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900">{activity.title}</p>
            <p className="text-xs text-slate-600">{activity.description}</p>
            <p className="text-xs text-slate-500 mt-1">{activity.time}</p>
          </div>
          {activity.status && (
            <span className={`text-xs px-2 py-1 rounded-md font-medium ${
              activity.status === 'completed' ? 'bg-green-100 text-green-700' :
              activity.status === 'running' ? 'bg-blue-100 text-blue-700' :
              'bg-slate-200 text-slate-700'
            }`}>
              {activity.status}
            </span>
          )}
        </motion.div>
      ))}
    </div>
  );
}

export function Dashboard() {
  const { selectedProject, setActivePanel, personas, focusGroups } = useAppStore();

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4 px-4">
          <div className="text-6xl mb-4 animate-float">🧠</div>
          <h2 className="text-3xl font-bold text-gradient">
            Market Research Platform
          </h2>
          <p className="text-slate-600 max-w-md mx-auto">
            AI-powered persona simulation and behavioral analytics platform
          </p>
          <div className="flex gap-3 justify-center mt-6">
            <button
              onClick={() => setActivePanel('projects')}
              className="floating-button px-6 py-3 text-sm"
            >
              👈 Open Projects Panel
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Calculate stats
  const completedFocusGroups = focusGroups.filter(fg => fg.status === 'completed').length;
  const runningFocusGroups = focusGroups.filter(fg => fg.status === 'running').length;

  // Generate recent activities
  const recentActivities = [
    ...personas.slice(0, 2).map(p => ({
      type: 'persona',
      title: `New persona created`,
      description: `${p.gender}, ${p.age} - ${p.location}`,
      time: 'Just now',
      status: null,
    })),
    ...focusGroups.slice(0, 2).map(fg => ({
      type: 'focus-group',
      title: fg.name,
      description: `${fg.persona_ids.length} personas, ${fg.questions.length} questions`,
      time: new Date(fg.created_at).toLocaleDateString(),
      status: fg.status,
    })),
  ].slice(0, 5);

  return (
    <div className="w-full h-full overflow-auto p-8 space-y-6">
      {/* Project Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="floating-panel p-6"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1">
              {selectedProject.name}
            </h1>
            {selectedProject.description && (
              <p className="text-slate-600">{selectedProject.description}</p>
            )}
          </div>
          {selectedProject.is_statistically_valid && (
            <div className="px-4 py-2 rounded-lg bg-green-100 text-green-700 font-medium flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5" />
              Statistically Valid
            </div>
          )}
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Total Personas"
          value={personas.length}
          trend={`${personas.length} active`}
          color="primary"
        />
        <StatCard
          icon={MessageSquare}
          label="Focus Groups"
          value={focusGroups.length}
          trend={`${completedFocusGroups} completed`}
          color="accent"
        />
        <StatCard
          icon={BarChart3}
          label="Analyses"
          value={completedFocusGroups}
          trend={completedFocusGroups > 0 ? "Ready to export" : "None yet"}
          color="green"
        />
        <StatCard
          icon={Clock}
          label="In Progress"
          value={runningFocusGroups}
          trend={runningFocusGroups > 0 ? "Running now" : "None running"}
          color="blue"
        />
      </div>

      {/* Quick Actions & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="floating-panel p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <QuickAction
              icon={Users}
              label="Generate Personas"
              description="Create new synthetic personas for this project"
              onClick={() => setActivePanel('personas')}
            />
            <QuickAction
              icon={MessageSquare}
              label="Create Focus Group"
              description="Start a new AI-simulated focus group session"
              onClick={() => setActivePanel('focus-groups')}
              disabled={personas.length < 2}
            />
            <QuickAction
              icon={BarChart3}
              label="View Analysis"
              description="Analyze completed focus group results"
              onClick={() => setActivePanel('analysis')}
              disabled={completedFocusGroups === 0}
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="floating-panel p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
          <RecentActivity activities={recentActivities} />
        </div>
      </div>

      {/* Project Stats Details */}
      {selectedProject.is_statistically_valid && selectedProject.p_values && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="floating-panel p-6"
        >
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Statistical Validation</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(selectedProject.p_values).map(([key, value]) => (
              <div key={key} className="p-3 rounded-lg bg-slate-50">
                <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                  {key}
                </div>
                <div className="text-lg font-bold text-slate-900">
                  {typeof value === 'number' ? value.toFixed(3) : 'N/A'}
                </div>
                <div className={`text-xs mt-1 ${
                  typeof value === 'number' && value > 0.05
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}>
                  {typeof value === 'number' && value > 0.05 ? '✓ Valid' : '✗ Invalid'}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
