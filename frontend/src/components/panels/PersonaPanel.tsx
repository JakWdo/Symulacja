import { motion } from 'framer-motion';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { personasApi } from '@/lib/api';
import type { GeneratePersonasPayload, PersonaAdvancedOptions } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import {
  User,
  Users,
  Plus,
  Loader2,
  ShieldHalf,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Search,
  Sparkles,
  MapPin,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn, getPersonalityColor } from '@/lib/utils';
import { toast } from '@/components/ui/toastStore';
import type { Persona } from '@/types';
import { PersonaGenerationWizard } from '@/components/personas/PersonaGenerationWizard';

const NAME_FROM_STORY_REGEX = /^(?<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s/;

type DistributionRecord = Record<string, number>;

function guessNameFromStory(story?: string | null) {
  if (!story) return null;
  const match = story.trim().match(NAME_FROM_STORY_REGEX);
  return match?.groups?.name ?? null;
}

function getPersonaDisplayName(persona: Persona) {
  if (persona.full_name && persona.full_name.trim().length > 0) {
    return persona.full_name.trim();
  }
  const inferred = guessNameFromStory(persona.background_story);
  if (inferred) {
    return inferred;
  }
  const genderLabel = persona.gender ? `${persona.gender.charAt(0).toUpperCase()}${persona.gender.slice(1)}` : 'Persona';
  return `${genderLabel} ${persona.age}`;
}

function extractStorySummary(story?: string | null) {
  if (!story) return null;
  const trimmed = story.trim();
  if (!trimmed) return null;
  const match = trimmed.match(/[^.!?]+[.!?]/);
  return (match ? match[0] : trimmed).trim();
}

function formatLocation(location?: string | null) {
  if (!location) return 'Lokalizacja nieznana';
  return location;
}

function parseDistributionInput(raw: string): DistributionRecord | null {
  if (!raw.trim()) {
    return null;
  }

  const entries = raw
    .split(/[,\n]/)
    .map((entry) => entry.trim())
    .filter(Boolean);

  const distribution: DistributionRecord = {};

  entries.forEach((entry) => {
    const [labelRaw, valueRaw] = entry.split(/[:=]/).map((part) => part.trim());
    if (!labelRaw || !valueRaw) {
      return;
    }
    const normalizedLabel = labelRaw.replace(/\s+/g, ' ');
    const sanitized = valueRaw.replace(/%/g, '');
    const numeric = Number.parseFloat(sanitized);
    if (Number.isFinite(numeric) && numeric > 0) {
      distribution[normalizedLabel] = numeric;
    }
  });

  const total = Object.values(distribution).reduce((acc, value) => acc + value, 0);
  if (total <= 0) {
    return null;
  }

  const normalized: DistributionRecord = {};
  Object.entries(distribution).forEach(([label, value]) => {
    normalized[label] = value / total;
  });
  return normalized;
}

interface DistributionInputProps {
  label: string;
  placeholder?: string;
  helper?: string;
  value: string;
  onChange: (value: string) => void;
}

function DistributionInput({ label, placeholder, helper, value, onChange }: DistributionInputProps) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-slate-700">{label}</label>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={3}
        placeholder={placeholder ?? 'np. 18-24:40, 25-34:35, 35-44:25'}
        className="w-full resize-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      />
      {helper && <p className="text-xs text-slate-500">{helper}</p>}
    </div>
  );
}

function StatBadge({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-900">{value}</p>
      </div>
    </div>
  );
}

function TagPill({ children, tone = 'primary' }: { children: React.ReactNode; tone?: 'primary' | 'accent' | 'slate' }) {
  const palette = {
    primary: 'border-primary-200 bg-primary-50 text-primary-700',
    accent: 'border-accent-200 bg-accent-50 text-accent-700',
    slate: 'border-slate-200 bg-slate-100 text-slate-600',
  };

  return (
    <span className={cn('rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide', palette[tone])}>
      {children}
    </span>
  );
}

function OptionChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors',
        active
          ? 'border-primary-500 bg-primary-100 text-primary-700 shadow-sm'
          : 'border-slate-200 text-slate-600 hover:border-primary-200 hover:text-primary-600'
      )}
    >
      {label}
    </button>
  );
}

function PersonaListItem({ persona, isSelected }: { persona: Persona; isSelected: boolean }) {
  const { setSelectedPersona } = useAppStore();
  const displayName = getPersonaDisplayName(persona);

  return (
    <button
      type="button"
      onClick={() => setSelectedPersona(persona)}
      className={cn(
        'w-full text-left px-4 py-3 border-l-4 transition-all hover:bg-slate-50',
        isSelected
          ? 'border-l-primary-600 bg-primary-50/50'
          : 'border-l-transparent hover:border-l-slate-300'
      )}
    >
      <p className="font-semibold text-slate-900 text-sm">{displayName}</p>
      <p className="text-xs text-slate-500 mt-0.5">{persona.age} lat</p>
    </button>
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

  const displayName = getPersonaDisplayName(persona);
  const subtitle = persona.persona_title?.trim() || persona.occupation?.trim() || 'Profil persony';
  const locationLabel = formatLocation(persona.location);
  const headline = (persona.headline && persona.headline.trim()) || extractStorySummary(persona.background_story);

  const personalityTraits: Array<{ label: string; value: number | null | undefined }> = [
    { label: 'Otwartość', value: persona.openness },
    { label: 'Sumienność', value: persona.conscientiousness },
    { label: 'Ekstrawersja', value: persona.extraversion },
    { label: 'Ugodowość', value: persona.agreeableness },
    { label: 'Neurotyczność', value: persona.neuroticism },
  ];

  return (
    <div className="h-full space-y-6 overflow-y-auto rounded-2xl border border-slate-200/60 bg-white/80 p-8 shadow-sm backdrop-blur-sm scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <h4 className="text-2xl font-bold text-slate-900 mb-1">{displayName}</h4>
          <p className="text-base text-slate-600 mb-2">{subtitle}</p>
          {headline && (
            <p className="mt-3 text-sm leading-relaxed text-slate-700">{headline}</p>
          )}
        </div>
        <div className="text-right text-sm text-slate-600 space-y-1 flex-shrink-0">
          <p className="font-bold text-slate-800 text-lg">{persona.age} lat</p>
          <p className="text-xs">{locationLabel}</p>
        </div>
      </div>

      <section>
        <h5 className="text-base font-bold text-slate-900 mb-3">Najważniejsze fakty</h5>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl border-2 border-slate-200 bg-slate-50 p-4">
            <span className="block text-slate-600 mb-1.5 font-medium text-xs">Wykształcenie</span>
            <span className="text-slate-900 font-semibold text-sm">
              {persona.education_level ?? '—'}
            </span>
          </div>
          <div className="rounded-xl border-2 border-slate-200 bg-slate-50 p-4">
            <span className="block text-slate-600 mb-1.5 font-medium text-xs">Dochód</span>
            <span className="text-slate-900 font-semibold text-sm">
              {persona.income_bracket ?? '—'}
            </span>
          </div>
          <div className="col-span-2 rounded-xl border-2 border-slate-200 bg-slate-50 p-4">
            <span className="block text-slate-600 mb-1.5 font-medium text-xs">Stanowisko</span>
            <span className="text-slate-900 font-semibold text-sm">
              {persona.occupation ?? 'Brak danych'}
            </span>
          </div>
        </div>
      </section>

      <section>
        <h5 className="text-base font-bold text-slate-900 mb-3">Profil osobowości</h5>
        <div className="space-y-3">
          {personalityTraits.map(({ label, value }) => (
            <div key={label} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm text-slate-700">
                <span className="font-medium">{label}</span>
                <span className="font-bold text-slate-900">
                  {value !== null && value !== undefined ? `${Math.round(value * 100)}%` : '—'}
                </span>
              </div>
              <div className="h-2.5 rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.max(0, Math.min(1, value ?? 0)) * 100}%`,
                    backgroundColor: getPersonalityColor(label, value ?? 0),
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {(persona.values && persona.values.length > 0) && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Kluczowe wartości</h5>
          <div className="flex flex-wrap gap-2">
            {persona.values.map((value) => (
              <span key={value} className="px-3 py-1.5 text-xs font-semibold rounded-full border-2 border-primary-200 bg-primary-50 text-primary-700">
                {value}
              </span>
            ))}
          </div>
        </section>
      )}

      {(persona.interests && persona.interests.length > 0) && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Zainteresowania</h5>
          <div className="flex flex-wrap gap-2">
            {persona.interests.map((interest) => (
              <span key={interest} className="px-3 py-1.5 text-xs font-semibold rounded-full border-2 border-accent-200 bg-accent-50 text-accent-700">
                {interest}
              </span>
            ))}
          </div>
        </section>
      )}

      {persona.background_story && (
        <section>
          <h5 className="text-base font-bold text-slate-900 mb-3">Historia</h5>
          <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-line">
            {persona.background_story}
          </p>
        </section>
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
  const [showWizard, setShowWizard] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
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

  const sortedPersonas = useMemo(() => {
    if (!personas) return [];
    return [...personas].sort((a, b) => {
      const aName = (a.full_name || a.persona_title || a.occupation || '').toLowerCase();
      const bName = (b.full_name || b.persona_title || b.occupation || '').toLowerCase();
      return aName.localeCompare(bName);
    });
  }, [personas]);

  const filteredPersonas = useMemo(() => {
    if (!searchTerm.trim()) {
      return sortedPersonas;
    }
    const query = searchTerm.toLowerCase();
    return sortedPersonas.filter((persona) => {
      const haystack = [
        persona.full_name,
        persona.persona_title,
        persona.occupation,
        persona.location,
        persona.values?.join(' '),
        persona.interests?.join(' '),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [sortedPersonas, searchTerm]);

  useEffect(() => {
    if (!personas || personas.length === 0) {
      if (selectedPersona) {
        setSelectedPersona(null);
      }
      return;
    }

    if (filteredPersonas.length === 0) {
      if (selectedPersona) {
        setSelectedPersona(null);
      }
      return;
    }

    const stillExists = selectedPersona
      ? filteredPersonas.some((persona) => persona.id === selectedPersona.id)
      : false;

    if (!stillExists) {
      setSelectedPersona(filteredPersonas[0]);
    }
  }, [personas, filteredPersonas, selectedPersona, setSelectedPersona]);

  const generateMutation = useMutation({
    mutationFn: (payload: GeneratePersonasPayload) =>
      personasApi.generate(selectedProject!.id, payload),
    onSuccess: (_, variables) => {
      setShowGenerateForm(false);
      queryClient.invalidateQueries({ queryKey: ['personas', selectedProject?.id] });
      const modeLabel = variables.adversarial_mode ? 'Adversarial' : 'Standard';
      toast.info(
        'Generation started',
        `${modeLabel} cohort: ${variables.num_personas} personas queued. Generation runs in the background.`
      );
    },
    onError: (error: Error) => {
      toast.error('Generation failed', error.message);
    },
  });

  const handleWizardSubmit = (config: GeneratePersonasPayload) => {
    if (!selectedProject) {
      return;
    }

    setShowWizard(false);
    setProgressMeta({ start: Date.now(), duration: Math.max(5000, config.num_personas * 2500) });
    setGenerationProgress(5);
    generateMutation.mutate(config);
  };

  const isGenerating = generateMutation.isPending || (isLoading && sortedPersonas.length === 0);
  const totalPersonas = personas?.length ?? 0;

  const personaStats = useMemo(() => {
    if (!personas || personas.length === 0) {
      return null;
    }

    const avgAge = Math.round(
      personas.reduce((acc, item) => acc + (item.age ?? 0), 0) / personas.length
    );

    const locationCounts = new Map<string, number>();
    const valueCounts = new Map<string, number>();

    personas.forEach((persona) => {
      if (persona.location) {
        locationCounts.set(
          persona.location,
          (locationCounts.get(persona.location) ?? 0) + 1,
        );
      }
      persona.values?.forEach((value) => {
        valueCounts.set(value, (valueCounts.get(value) ?? 0) + 1);
      });
    });

    const topLocation = Array.from(locationCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'Brak danych';
    const dominantValue = Array.from(valueCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'Różnorodne';

    return {
      avgAge,
      topLocation,
      dominantValue,
    };
  }, [personas]);

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
            onClick={() => setShowWizard(true)}
            variant="primary"
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700"
          >
            <Sparkles className="w-5 h-5" />
            AI Wizard
          </Button>
        </div>

        <div className="flex-1 grid gap-4 grid-cols-[280px,1fr]">
          <div className="border-r border-slate-200 flex flex-col">
            <div className="p-3 border-b border-slate-200">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search personas..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
              {filteredPersonas.map((persona) => (
                <PersonaListItem
                  key={persona.id}
                  persona={persona}
                  isSelected={selectedPersona?.id === persona.id}
                />
              ))}
            </div>
          </div>
          <div className="overflow-y-auto px-6">
            <PersonaDetails persona={selectedPersona ?? null} />
          </div>
        </div>
      </div>
    );
  } else if (generateMutation.isPending) {
    content = (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Loader2 className="w-12 h-12 text-primary-500 mb-3 animate-spin" />
        <p className="text-slate-900 font-medium mb-1">Generating personas...</p>
        <p className="text-sm text-slate-600">
          This may take a few moments...
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
        <Button onClick={() => setShowWizard(true)} variant="primary" className="gap-2 bg-purple-600 hover:bg-purple-700">
          <Sparkles className="w-5 h-5" />
          AI Wizard
        </Button>
      </div>
    );
  }

  const showProgressBar = generationProgress > 0;
  const estimatedSeconds = progressMeta
    ? Math.max(1, Math.ceil((progressMeta.duration - (Date.now() - progressMeta.start)) / 1000))
    : 10;

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

      {/* Advanced Wizard Modal */}
      {showWizard && (
        <PersonaGenerationWizard
          onSubmit={handleWizardSubmit}
          onCancel={() => setShowWizard(false)}
          isGenerating={generateMutation.isPending}
        />
      )}
    </FloatingPanel>
  );
}
