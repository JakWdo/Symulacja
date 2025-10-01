import { motion } from 'framer-motion';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { personasApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { User, Brain, Heart, Zap, Target, Plus, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn, getPersonalityColor } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import type { Persona } from '@/types';

function PersonaCard({ persona, isSelected }: { persona: Persona; isSelected: boolean }) {
  const { setSelectedPersona } = useAppStore();

  return (
    <div
      onClick={() => setSelectedPersona(persona)}
      className={cn(
        'rounded-2xl border-2 transition-all duration-200 cursor-pointer hover:shadow-xl bg-white p-5',
        isSelected
          ? 'border-primary-500 shadow-xl ring-4 ring-primary-100 scale-[1.02]'
          : 'border-slate-200 hover:border-primary-300',
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-4 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-primary-100 via-primary-50 to-accent-100 text-primary-700 shadow-sm">
          <User className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-lg text-slate-900 tracking-tight">
            {persona.gender}, {persona.age}
          </h4>
          {persona.location && (
            <p className="text-sm text-slate-600 flex items-center gap-1 mt-0.5">
              📍 {persona.location}
            </p>
          )}
        </div>
      </div>

      {/* Demographics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {persona.education_level && (
          <div className="px-3 py-2.5 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100">
            <div className="text-[11px] text-blue-700 font-semibold uppercase tracking-wide">Education</div>
            <div className="text-sm text-blue-900 font-semibold mt-1">
              {persona.education_level}
            </div>
          </div>
        )}
        {persona.income_bracket && (
          <div className="px-3 py-2.5 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100">
            <div className="text-[11px] text-emerald-700 font-semibold uppercase tracking-wide">Income</div>
            <div className="text-sm text-emerald-900 font-semibold mt-1">
              {persona.income_bracket}
            </div>
          </div>
        )}
      </div>

      {/* Personality Traits */}
      <div className="space-y-2.5 mb-4">
        {[
          { label: 'Openness', value: persona.openness, icon: Brain },
          { label: 'Conscientiousness', value: persona.conscientiousness, icon: Target },
          { label: 'Extraversion', value: persona.extraversion, icon: Zap },
          { label: 'Agreeableness', value: persona.agreeableness, icon: Heart },
        ]
          .filter((trait) => trait.value !== null)
          .slice(0, 3)
          .map(({ label, value, icon: Icon }) => (
            <div key={label} className="flex items-center gap-2.5">
              <Icon className="w-4 h-4 text-slate-500 flex-shrink-0" />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-700">{label}</span>
                  <span className="text-sm font-bold text-slate-900">
                    {Math.round(value! * 100)}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden shadow-inner">
                  <div
                    className="h-full transition-all duration-500 rounded-full"
                    style={{
                      width: `${value! * 100}%`,
                      backgroundColor: getPersonalityColor(label, value!),
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Values & Interests */}
      {((persona.values && persona.values.length > 0) || (persona.interests && persona.interests.length > 0)) && (
        <div className="pt-4 border-t border-slate-200">
          <div className="flex flex-wrap gap-2">
            {persona.values?.slice(0, 2).map((value) => (
              <span
                key={value}
                className="text-xs px-3 py-1.5 rounded-full bg-gradient-to-r from-primary-100 to-primary-50 text-primary-800 font-semibold border border-primary-200"
              >
                {value}
              </span>
            ))}
            {persona.interests?.slice(0, 2).map((interest) => (
              <span
                key={interest}
                className="text-xs px-3 py-1.5 rounded-full bg-gradient-to-r from-accent-100 to-accent-50 text-accent-800 font-semibold border border-accent-200"
              >
                {interest}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PersonaDetails({ persona }: { persona: Persona | null }) {
  if (!persona) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-slate-500">
        Select a persona to preview the full profile.
      </div>
    );
  }

  return (
    <div className="h-full rounded-2xl border border-slate-200/60 bg-white/80 backdrop-blur-sm shadow-sm p-4 space-y-4 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
      <div>
        <h4 className="text-lg font-semibold text-slate-900">
          {persona.gender}, {persona.age}
        </h4>
        {persona.location && (
          <p className="text-sm text-slate-500">Based in {persona.location}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="rounded-lg bg-slate-50 p-3">
          <span className="block text-slate-500">Education</span>
          <span className="text-slate-800 font-medium">
            {persona.education_level ?? 'N/A'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-50 p-3">
          <span className="block text-slate-500">Income</span>
          <span className="text-slate-800 font-medium">
            {persona.income_bracket ?? 'N/A'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-50 p-3 col-span-2">
          <span className="block text-slate-500">Occupation</span>
          <span className="text-slate-800 font-medium">
            {persona.occupation ?? 'Not specified'}
          </span>
        </div>
      </div>

      <div>
        <h5 className="text-sm font-semibold text-slate-800 mb-2">Personality Snapshot</h5>
        <div className="grid grid-cols-2 gap-3 text-xs">
          {[
            ['Openness', persona.openness],
            ['Conscientiousness', persona.conscientiousness],
            ['Extraversion', persona.extraversion],
            ['Agreeableness', persona.agreeableness],
            ['Neuroticism', persona.neuroticism],
          ].map(([label, value]) => (
            <div key={label} className="flex flex-col">
              <span className="text-slate-500">{label}</span>
              <span className="text-slate-800 font-medium">
                {value !== null && value !== undefined ? `${Math.round(value * 100)}%` : '—'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {persona.values && persona.values.length > 0 && (
        <div>
          <h5 className="text-sm font-semibold text-slate-800 mb-2">Core Values</h5>
          <div className="flex flex-wrap gap-2">
            {persona.values.map((value) => (
              <span
                key={value}
                className="px-2 py-1 text-xs bg-primary-50 text-primary-700 rounded-full"
              >
                {value}
              </span>
            ))}
          </div>
        </div>
      )}

      {persona.interests && persona.interests.length > 0 && (
        <div>
          <h5 className="text-sm font-semibold text-slate-800 mb-2">Interests</h5>
          <div className="flex flex-wrap gap-2">
            {persona.interests.map((interest) => (
              <span
                key={interest}
                className="px-2 py-1 text-xs bg-accent-50 text-accent-700 rounded-full"
              >
                {interest}
              </span>
            ))}
          </div>
        </div>
      )}

      {persona.background_story && (
        <div>
          <h5 className="text-sm font-semibold text-slate-800 mb-2">Background</h5>
          <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
            {persona.background_story}
          </p>
        </div>
      )}
    </div>
  );
}

export function PersonaPanel() {
  const {
    activePanel,
    setActivePanel,
    selectedProject,
    selectedPersona,
    setPersonas,
    setSelectedPersona,
  } = useAppStore();
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [numPersonas, setNumPersonas] = useState(10);
  const queryClient = useQueryClient();
  const [generationProgress, setGenerationProgress] = useState(0);
  const [progressMeta, setProgressMeta] = useState<{ start: number; duration: number } | null>(null);

  const { data: personas, isLoading } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      const data = await personasApi.getByProject(selectedProject.id);
      setPersonas(data); // Update store immediately
      return data;
    },
    enabled: !!selectedProject,
    refetchInterval: (query) => {
      // Refetch every 3s if project exists but no personas yet (generation in progress)
      const data = query.state.data;
      return selectedProject && (!data || data.length === 0) ? 3000 : false;
    },
    onSuccess: (data) => {
      // Show toast when personas generation completes
      if (data.length > 0 && personas && personas.length === 0) {
        toast.success(
          'Personas generated!',
          `Successfully created ${data.length} personas`
        );
      }
    },
  });

  useEffect(() => {
    if (!personas || personas.length === 0) {
      if (selectedPersona) {
        setSelectedPersona(null);
      }
      return;
    }

    const stillExists = selectedPersona
      ? personas.some((persona) => persona.id === selectedPersona.id)
      : false;

    if (!stillExists) {
      setSelectedPersona(personas[0]);
    }
  }, [personas, selectedPersona, setSelectedPersona]);

  const generateMutation = useMutation({
    mutationFn: () => personasApi.generate(selectedProject!.id, {
      num_personas: numPersonas,
      adversarial_mode: false,
    }),
    onSuccess: () => {
      setShowGenerateForm(false);
      queryClient.invalidateQueries({ queryKey: ['personas', selectedProject?.id] });
      toast.info(
        'Generation started',
        `Creating ${numPersonas} personas. This may take a few minutes...`
      );
    },
    onError: (error: Error) => {
      toast.error('Generation failed', error.message);
    },
  });

  const handleGenerate = () => {
    if (selectedProject) {
      setProgressMeta({ start: Date.now(), duration: Math.max(5000, numPersonas * 2500) });
      setGenerationProgress(5);
      generateMutation.mutate();
    }
  };

  const sortedPersonas = useMemo(() => {
    if (!personas) return [];
    return [...personas];
  }, [personas]);

  const isGenerating = generateMutation.isPending || (isLoading && sortedPersonas.length === 0);

  useEffect(() => {
    if (!isGenerating) {
      if (generationProgress > 0) {
        setGenerationProgress(100);
        const timeout = setTimeout(() => {
          setGenerationProgress(0);
          setProgressMeta(null);
        }, 800);
        return () => clearTimeout(timeout);
      }
      setProgressMeta(null);
      return;
    }

    const interval = setInterval(() => {
      setGenerationProgress((prev) => {
        if (!progressMeta) {
          return Math.min(prev + 8, 92);
        }
        const elapsed = Date.now() - progressMeta.start;
        const ratio = Math.min(elapsed / progressMeta.duration, 0.97);
        const target = 5 + ratio * 90;
        return prev + (target - prev) * 0.35;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [isGenerating, progressMeta, generationProgress]);

  const renderGenerateForm = (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 space-y-3">
      <h4 className="font-semibold text-slate-800">Generate Personas</h4>
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Number of personas (10-100)
          </label>
          <input
            type="number"
            min="10"
            max="100"
            value={numPersonas}
            onChange={(e) => setNumPersonas(Number(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <p className="text-xs text-slate-500 mt-1">
            ~{Math.round(numPersonas * 2.5)}s estimated time
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowGenerateForm(false)}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleGenerate}
            disabled={generateMutation.isPending || numPersonas < 10 || numPersonas > 100}
            isLoading={generateMutation.isPending}
            className="flex-1"
          >
            Generate
          </Button>
        </div>
      </div>
    </div>
  );

  let content: ReactNode;

  if (!selectedProject) {
    content = (
      <div className="flex flex-col items-center justify-center py-12 text-center text-sm text-slate-600">
        <User className="w-12 h-12 text-slate-300 mb-3" />
        Select a project first to start generating personas.
      </div>
    );
  } else if (isLoading) {
    content = (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  } else if (sortedPersonas.length > 0) {
    content = (
      <div className="flex h-full flex-col gap-4">
        <div className="flex flex-wrap gap-3">
          <Button
            onClick={() => setShowGenerateForm((prev) => !prev)}
            variant={showGenerateForm ? 'outline' : 'secondary'}
            className="flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            {showGenerateForm ? 'Hide generator' : 'Generate more personas'}
          </Button>
        </div>

        {showGenerateForm && renderGenerateForm}

        <div className="flex-1 grid gap-4 xl:grid-cols-[minmax(0,1.2fr),minmax(0,1fr)]">
          <div className="space-y-3 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
            {sortedPersonas.map((persona) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                isSelected={selectedPersona?.id === persona.id}
              />
            ))}
          </div>
          <PersonaDetails persona={selectedPersona ?? null} />
        </div>
      </div>
    );
  } else if (generateMutation.isPending) {
    content = (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Loader2 className="w-12 h-12 text-primary-500 mb-3 animate-spin" />
        <p className="text-slate-900 font-medium mb-1">Generating personas...</p>
        <p className="text-sm text-slate-600">
          This takes ~{Math.round(numPersonas * 2.5)}s for {numPersonas} personas
        </p>
      </div>
    );
  } else {
    content = (
      <div className="flex flex-col items-center justify-center py-12 text-center gap-4">
        <User className="w-12 h-12 text-slate-300" />
        <div>
          <p className="text-slate-600">No personas yet for this project.</p>
          <p className="text-sm text-slate-500">
            Generate a cohort to start building focus groups and analysis.
          </p>
        </div>
        {showGenerateForm ? (
          <div className="w-full max-w-sm">{renderGenerateForm}</div>
        ) : (
          <Button onClick={() => setShowGenerateForm(true)} variant="primary" className="gap-2">
            <Plus className="w-5 h-5" />
            Generate Personas
          </Button>
        )}
      </div>
    );
  }

  const showProgressBar = generationProgress > 0;
  const estimatedSeconds = progressMeta
    ? Math.max(1, Math.ceil((progressMeta.duration - (Date.now() - progressMeta.start)) / 1000))
    : Math.max(1, Math.round(numPersonas * 2.5));

  return (
    <FloatingPanel
      isOpen={activePanel === 'personas'}
      onClose={() => setActivePanel(null)}
      title={`Personas ${personas ? `(${personas.length})` : ''}`}
      panelKey="personas"
      size="lg"
    >
      {showProgressBar && (
        <div className="px-4 pt-3">
          <div className="text-xs text-slate-500 mb-2 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
            <span>
              Synthesizing personas…
              {progressMeta ? ` ~${estimatedSeconds}s remaining` : ''}
            </span>
          </div>
          <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
            <motion.div
              initial={{ width: '0%' }}
              animate={{ width: `${Math.min(generationProgress, 100).toFixed(1)}%` }}
              transition={{ ease: 'easeOut', duration: 0.25 }}
              className="h-full bg-gradient-to-r from-primary-400 via-primary-500 to-accent-400"
            />
          </div>
        </div>
      )}
      {content}
    </FloatingPanel>
  );
}
