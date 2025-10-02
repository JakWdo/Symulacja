import { useAppStore } from '@/store/appStore';
import { Users, MessageSquare, BarChart3, Clock, Zap, Plus, Gauge } from 'lucide-react';
import { motion } from 'framer-motion';

function MiniStatCard({
  icon: Icon,
  label,
  value,
  color = "blue"
}: {
  icon: any;
  label: string;
  value: string | number;
  color?: string;
}) {
  const colorClasses = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-green-600 bg-green-50",
    purple: "text-purple-600 bg-purple-50",
    orange: "text-orange-600 bg-orange-50",
  }[color];

  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-200 hover:shadow-md transition-shadow">
      <div className={`p-3 rounded-lg ${colorClasses}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-xs text-slate-600">{label}</p>
      </div>
    </div>
  );
}

function PersonaPreviewCard({ persona }: { persona: any }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-xl bg-gradient-to-br from-white to-slate-50 border border-slate-200 hover:border-primary-300 transition-all cursor-pointer"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-primary-100 text-primary-700">
          <Users className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-slate-900 text-sm">
            {persona.gender}, {persona.age}
          </h4>
          <p className="text-xs text-slate-600 mt-1">
            {persona.occupation || 'Professional'}
          </p>
          {persona.location && (
            <p className="text-xs text-slate-500 mt-1">📍 {persona.location}</p>
          )}
        </div>
      </div>

      {/* Mini traits preview */}
      <div className="mt-3 flex gap-1">
        {[
          { label: 'O', value: persona.openness },
          { label: 'C', value: persona.conscientiousness },
          { label: 'E', value: persona.extraversion },
        ]
          .filter(t => t.value != null)
          .map((trait, idx) => (
            <div
              key={idx}
              className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden"
              title={`${trait.label}: ${Math.round(trait.value * 100)}%`}
            >
              <div
                className="h-full bg-gradient-to-r from-primary-400 to-primary-600"
                style={{ width: `${trait.value * 100}%` }}
              />
            </div>
          ))}
      </div>
    </motion.div>
  );
}

function FocusGroupPreviewCard({
  focusGroup,
  onOpenAnalysis,
}: {
  focusGroup: any;
  onOpenAnalysis: (focusGroupId: string) => void;
}) {
  const statusColors = {
    completed: "text-green-700 bg-green-100",
    running: "text-blue-700 bg-blue-100",
    pending: "text-slate-700 bg-slate-100",
    failed: "text-red-700 bg-red-100",
  };

  const ideaScore = focusGroup.polarization_score != null
    ? (focusGroup.polarization_score * 100).toFixed(1)
    : null;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onClick={() => onOpenAnalysis(focusGroup.id)}
      className="p-4 rounded-xl bg-white border border-slate-200 hover:border-accent-300 transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-accent-100 text-accent-700">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-semibold text-slate-900 text-sm">
              {focusGroup.name}
            </h4>
            <p className="text-xs text-slate-600 mt-1">
              {focusGroup.persona_ids.length} participants • {focusGroup.questions.length} questions
            </p>
            {ideaScore && (
              <p className="text-xs text-primary-600 mt-1 font-medium">Idea Score: {ideaScore}</p>
            )}
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded-md font-medium ${statusColors[focusGroup.status]}`}>
          {focusGroup.status}
        </span>
      </div>
    </motion.div>
  );
}

export function ImprovedDashboard() {
  const { selectedProject, setActivePanel, personas, focusGroups, setSelectedFocusGroup } = useAppStore();

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full px-8">
        <div className="text-center space-y-6 max-w-2xl">
          <div className="text-7xl mb-6 animate-float">🧠</div>
          <h1 className="text-4xl font-bold text-slate-900">
            Market Research Platform
          </h1>
          <p className="text-lg text-slate-600">
            AI-powered persona simulation and behavioral analytics
          </p>
          <button
            onClick={() => setActivePanel('projects')}
            className="mt-8 floating-button px-8 py-4 text-base font-semibold"
          >
            Get Started - Select a Project
          </button>
        </div>
      </div>
    );
  }

  const completedFocusGroups = focusGroups.filter(fg => fg.status === 'completed').length;
  const runningFocusGroups = focusGroups.filter(fg => fg.status === 'running').length;
  const ideaScores = focusGroups
    .filter(fg => fg.status === 'completed' && fg.polarization_score != null)
    .map(fg => (fg.polarization_score as number) * 100);
  const averageIdeaScore = ideaScores.length > 0
    ? (ideaScores.reduce((acc, value) => acc + value, 0) / ideaScores.length).toFixed(1)
    : '—';

  const handleOpenAnalysis = (focusGroupId: string) => {
    const focusGroup = focusGroups.find(fg => fg.id === focusGroupId) ?? null;
    if (focusGroup) {
      setSelectedFocusGroup(focusGroup);
      setActivePanel('analysis');
    }
  };

  return (
    <div className="w-full h-full overflow-auto">
      {/* Header Bar */}
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-lg border-b border-slate-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              {selectedProject.name}
            </h1>
            {selectedProject.description && (
              <p className="text-sm text-slate-600 mt-1">{selectedProject.description}</p>
            )}
          </div>
          {selectedProject.is_statistically_valid && (
            <div className="px-4 py-2 rounded-lg bg-green-50 text-green-700 font-medium text-sm border border-green-200">
              ✓ Statistically Valid
            </div>
          )}
        </div>
      </div>

      <div className="p-8 space-y-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
          <MiniStatCard
            icon={Users}
            label="Total Personas"
            value={personas.length}
            color="blue"
          />
          <MiniStatCard
            icon={MessageSquare}
            label="Focus Groups"
            value={focusGroups.length}
            color="purple"
          />
          <MiniStatCard
            icon={BarChart3}
            label="Completed Analyses"
            value={completedFocusGroups}
            color="green"
          />
          <MiniStatCard
            icon={Clock}
            label="In Progress"
            value={runningFocusGroups}
            color="orange"
          />
          <MiniStatCard
            icon={Gauge}
            label="Avg Idea Score"
            value={averageIdeaScore}
            color="green"
          />
        </div>

        {/* Main Content - Two Columns */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Actions & Personas */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <div className="floating-panel p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <button
                  onClick={() => setActivePanel('personas')}
                  className="p-4 rounded-xl border-2 border-dashed border-slate-300 hover:border-primary-400 hover:bg-primary-50 transition-all text-left group"
                >
                  <Users className="w-6 h-6 text-primary-600 mb-2" />
                  <h4 className="font-semibold text-slate-900 text-sm">Generate Personas</h4>
                  <p className="text-xs text-slate-600 mt-1">
                    Create synthetic personas for research
                  </p>
                </button>

                <button
                  onClick={() => setActivePanel('focus-groups')}
                  className="p-4 rounded-xl border-2 border-dashed border-slate-300 hover:border-accent-400 hover:bg-accent-50 transition-all text-left group disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={personas.length < 2}
                >
                  <MessageSquare className="w-6 h-6 text-accent-600 mb-2" />
                  <h4 className="font-semibold text-slate-900 text-sm">New Focus Group</h4>
                  <p className="text-xs text-slate-600 mt-1">
                    Start AI-simulated discussion
                  </p>
                </button>

                <button
                  onClick={() => setActivePanel('analysis')}
                  className="p-4 rounded-xl border-2 border-dashed border-slate-300 hover:border-green-400 hover:bg-green-50 transition-all text-left group disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={completedFocusGroups === 0}
                >
                  <BarChart3 className="w-6 h-6 text-green-600 mb-2" />
                  <h4 className="font-semibold text-slate-900 text-sm">View Analysis</h4>
                  <p className="text-xs text-slate-600 mt-1">
                    Analyze completed sessions
                  </p>
                </button>
              </div>
            </div>

            {/* Recent Personas */}
            {personas.length > 0 && (
              <div className="floating-panel p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-900">Recent Personas</h3>
                  <button
                    onClick={() => setActivePanel('personas')}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    View All →
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {personas.slice(0, 4).map((persona) => (
                    <PersonaPreviewCard key={persona.id} persona={persona} />
                  ))}
                </div>
              </div>
            )}

            {/* Empty State for Personas */}
            {personas.length === 0 && (
              <div className="floating-panel p-12 text-center">
                <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No Personas Yet</h3>
                <p className="text-slate-600 mb-6">
                  Start by generating synthetic personas for your market research
                </p>
                <button
                  onClick={() => setActivePanel('personas')}
                  className="floating-button px-6 py-3"
                >
                  <Plus className="w-5 h-5 inline mr-2" />
                  Generate Personas
                </button>
              </div>
            )}
          </div>

          {/* Right Column - Focus Groups & Insights */}
          <div className="space-y-6">
            {/* Active Focus Groups */}
            {focusGroups.length > 0 && (
              <div className="floating-panel p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-900">Focus Groups</h3>
                  <button
                    onClick={() => setActivePanel('focus-groups')}
                    className="text-sm text-accent-600 hover:text-accent-700 font-medium"
                  >
                    View All →
                  </button>
                </div>
                <div className="space-y-3">
                  {focusGroups.slice(0, 3).map((fg) => (
                    <FocusGroupPreviewCard key={fg.id} focusGroup={fg} onOpenAnalysis={handleOpenAnalysis} />
                  ))}
                </div>
              </div>
            )}

            {/* Project Stats */}
            {selectedProject.is_statistically_valid && selectedProject.p_values && (
              <div className="floating-panel p-6">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-slate-900">Statistical Validation</h3>
                  <span className="text-xs text-primary-600 cursor-help" title="Chi-square test results - zobacz COMPLETE_GUIDE.md (sekcja Generowanie Person)">
                    ℹ️
                  </span>
                </div>
                <div className="text-xs text-slate-600 mb-3">
                  Chi-square p-values (threshold: 0.05)
                </div>
                <div className="space-y-3">
                  {Object.entries(selectedProject.p_values).slice(0, 3).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm text-slate-600 capitalize">{key}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono text-slate-900">
                          {typeof value === 'number' ? value.toFixed(3) : 'N/A'}
                        </span>
                        {typeof value === 'number' && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded cursor-help ${
                              value > 0.05 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}
                            title={value > 0.05 ? 'Good: personas match target distribution' : 'Poor: regenerate with more personas'}
                          >
                            {value > 0.05 ? '✓' : '✗'}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 pt-3 border-t border-slate-200 text-xs text-slate-600">
                  <strong>p &gt; 0.05</strong> = personas match target (good!)
                  <br />
                  <strong>p ≤ 0.05</strong> = regenerate with more personas
                </div>
              </div>
            )}

            {/* Getting Started Tips */}
            <div className="floating-panel p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
              <div className="flex items-start gap-3">
                <Zap className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-blue-900 text-sm mb-2">Quick Tip</h4>
                  <p className="text-xs text-blue-800 leading-relaxed">
                    Generate at least 10 personas for statistically valid results.
                    More personas = better insights from focus group simulations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
