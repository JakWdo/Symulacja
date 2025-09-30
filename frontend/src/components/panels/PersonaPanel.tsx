import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { personasApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { User, Brain, Heart, Zap, Target } from 'lucide-react';
import { cn, getPersonalityColor, truncateText } from '@/lib/utils';
import type { Persona } from '@/types';

function PersonalityBar({ label, value, icon: Icon }: { label: string; value: number; icon: any }) {
  const color = getPersonalityColor(label, value);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1">
          <Icon className="w-3 h-3 text-slate-500" />
          <span className="text-slate-600">{label}</span>
        </div>
        <span className="font-medium">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full transition-all duration-500"
          style={{
            width: `${value * 100}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}

function PersonaCard({ persona, isSelected }: { persona: Persona; isSelected: boolean }) {
  const { setSelectedPersona } = useAppStore();

  return (
    <div
      onClick={() => setSelectedPersona(persona)}
      className={cn(
        'node-card cursor-pointer group border-2 transition-colors',
        isSelected
          ? 'border-primary-200 shadow-lg bg-white'
          : 'border-transparent hover:border-primary-100',
      )}
    >
      <div className="flex items-start gap-3">
        <div className="p-3 rounded-xl bg-gradient-to-br from-primary-50 to-accent-50 text-primary-600">
          <User className="w-6 h-6" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-slate-900 group-hover:text-primary-600 transition-colors">
              {persona.gender}, {persona.age}
            </h4>
          </div>

          <div className="flex flex-wrap gap-2 mb-3 text-xs text-slate-600">
            {persona.location && (
              <span className="px-2 py-0.5 rounded-md bg-slate-100">
                📍 {persona.location}
              </span>
            )}
            {persona.education_level && (
              <span className="px-2 py-0.5 rounded-md bg-slate-100">
                🎓 {persona.education_level}
              </span>
            )}
            {persona.income_bracket && (
              <span className="px-2 py-0.5 rounded-md bg-slate-100">
                💰 {persona.income_bracket}
              </span>
            )}
          </div>

          {/* Big Five Traits */}
          <div className="space-y-2">
            {persona.openness !== null && (
              <PersonalityBar label="Openness" value={persona.openness} icon={Brain} />
            )}
            {persona.conscientiousness !== null && (
              <PersonalityBar label="Conscientiousness" value={persona.conscientiousness} icon={Target} />
            )}
            {persona.extraversion !== null && (
              <PersonalityBar label="Extraversion" value={persona.extraversion} icon={Zap} />
            )}
            {persona.agreeableness !== null && (
              <PersonalityBar label="Agreeableness" value={persona.agreeableness} icon={Heart} />
            )}
          </div>

          {/* Values & Interests */}
          {(persona.values || persona.interests) && (
            <div className="mt-3 pt-3 border-t border-slate-100">
              {persona.values && persona.values.length > 0 && (
                <div className="mb-2">
                  <div className="text-xs text-slate-500 mb-1">Values:</div>
                  <div className="flex flex-wrap gap-1">
                    {persona.values.slice(0, 3).map((value) => (
                      <span
                        key={value}
                        className="text-xs px-2 py-0.5 rounded-full bg-primary-50 text-primary-700"
                      >
                        {value}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {persona.interests && persona.interests.length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-1">Interests:</div>
                  <div className="flex flex-wrap gap-1">
                    {persona.interests.slice(0, 3).map((interest) => (
                      <span
                        key={interest}
                        className="text-xs px-2 py-0.5 rounded-full bg-accent-50 text-accent-700"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Background Story */}
          {persona.background_story && (
            <div className="mt-3 pt-3 border-t border-slate-100">
              <div className="text-xs text-slate-500 mb-1">Background:</div>
              <p className="text-xs text-slate-600">
                {truncateText(persona.background_story, 160)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function PersonaPanel() {
  const { activePanel, setActivePanel, selectedProject, selectedPersona, setPersonas } =
    useAppStore();

  const { data: personas, isLoading } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return personasApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
  });

  // Update store when data changes
  useEffect(() => {
    if (personas) {
      setPersonas(personas);
    } else if (!selectedProject) {
      setPersonas([]);
    }
  }, [personas, selectedProject, setPersonas]);

  return (
    <FloatingPanel
      isOpen={activePanel === 'personas'}
      onClose={() => setActivePanel(null)}
      title={`Personas ${personas ? `(${personas.length})` : ''}`}
      position="left"
      size="lg"
    >
      <div className="p-4">
        {!selectedProject ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <User className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600">Select a project first</p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
          </div>
        ) : personas && personas.length > 0 ? (
          <div className="space-y-3">
            {personas.map((persona) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                isSelected={selectedPersona?.id === persona.id}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <User className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-slate-600 mb-4">No personas yet</p>
            <button className="floating-button">Generate Personas</button>
          </div>
        )}
      </div>
    </FloatingPanel>
  );
}