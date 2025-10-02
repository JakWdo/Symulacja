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
import { Button } from '@/components/ui/Button';
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

function PersonaCard({ persona, isSelected }: { persona: Persona; isSelected: boolean }) {
  const { setSelectedPersona } = useAppStore();

  const displayName = getPersonaDisplayName(persona);
  const subtitle = persona.persona_title?.trim() || persona.occupation?.trim() || 'Persona';
  const headline = (persona.headline && persona.headline.trim()) || extractStorySummary(persona.background_story);
  const locationLabel = formatLocation(persona.location);

  const topValues = persona.values?.slice(0, 3) ?? [];
  const topInterests = persona.interests?.slice(0, 2) ?? [];

  const initials = displayName
    .split(' ')
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join('')
    .toUpperCase();

  return (
    <button
      type="button"
      onClick={() => setSelectedPersona(persona)}
      className={cn(
        'relative flex h-full w-full flex-col overflow-hidden rounded-3xl border transition-all duration-200',
        isSelected
          ? 'border-primary-500 shadow-xl ring-4 ring-primary-100'
          : 'border-slate-200 hover:border-primary-200 hover:shadow-lg'
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-accent-50 opacity-60" />
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-primary-200/40 blur-3xl" />
      <div className="relative z-10 flex flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 to-accent-500 text-base font-semibold text-white shadow-md">
              {initials || <User className="h-5 w-5" />}
            </div>
            <div className="space-y-1 text-left">
              <h4 className="text-lg font-semibold text-slate-900">{displayName}</h4>
              <p className="text-sm text-slate-500">{subtitle}</p>
            </div>
          </div>
          <div className="text-right text-xs text-slate-500">
            <span className="inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1 font-semibold text-slate-700 shadow-sm">
              {persona.age} lat
            </span>
            <p className="mt-2 inline-flex items-center gap-1 text-slate-500">
              <MapPin className="h-3.5 w-3.5" />
              {locationLabel}
            </p>
          </div>
        </div>

        {headline && (
          <p className="text-sm leading-relaxed text-slate-600">
            {headline}
          </p>
        )}

        <div className="mt-auto space-y-2">
          {topValues.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {topValues.map((value) => (
                <TagPill key={value}>{value}</TagPill>
              ))}
            </div>
          )}
          {topInterests.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {topInterests.map((interest) => (
                <TagPill key={interest} tone="accent">
                  {interest}
                </TagPill>
              ))}
            </div>
          )}
        </div>
      </div>
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
    <div className="h-full space-y-5 overflow-y-auto rounded-2xl border border-slate-200/60 bg-white/80 p-6 shadow-sm backdrop-blur-sm scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-xl font-semibold text-slate-900">{displayName}</h4>
          <p className="text-sm text-slate-500">{subtitle}</p>
          {headline && (
            <p className="mt-3 text-sm leading-relaxed text-slate-600">{headline}</p>
          )}
        </div>
        <div className="text-right text-sm text-slate-500 space-y-1">
          <p className="font-semibold text-slate-700">{persona.age} lat</p>
          <p>{locationLabel}</p>
        </div>
      </div>

      <section>
        <h5 className="text-sm font-semibold text-slate-800 mb-2">Najważniejsze fakty</h5>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="block text-slate-500">Wykształcenie</span>
            <span className="text-slate-800 font-medium">
              {persona.education_level ?? '—'}
            </span>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="block text-slate-500">Dochód</span>
            <span className="text-slate-800 font-medium">
              {persona.income_bracket ?? '—'}
            </span>
          </div>
          <div className="col-span-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="block text-slate-500">Stanowisko</span>
            <span className="text-slate-800 font-medium">
              {persona.occupation ?? 'Brak danych'}
            </span>
          </div>
        </div>
      </section>

      <section>
        <h5 className="text-sm font-semibold text-slate-800 mb-2">Profil osobowości</h5>
        <div className="space-y-2">
          {personalityTraits.map(({ label, value }) => (
            <div key={label} className="space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-600">
                <span>{label}</span>
                <span className="font-semibold text-slate-900">
                  {value !== null && value !== undefined ? `${Math.round(value * 100)}%` : '—'}
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-100">
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
          <h5 className="text-sm font-semibold text-slate-800 mb-2">Kluczowe wartości</h5>
          <div className="flex flex-wrap gap-2">
            {persona.values.map((value) => (
              <TagPill key={value}>{value}</TagPill>
            ))}
          </div>
        </section>
      )}

      {(persona.interests && persona.interests.length > 0) && (
        <section>
          <h5 className="text-sm font-semibold text-slate-800 mb-2">Zainteresowania</h5>
          <div className="flex flex-wrap gap-2">
            {persona.interests.map((interest) => (
              <TagPill key={interest} tone="accent">
                {interest}
              </TagPill>
            ))}
          </div>
        </section>
      )}

      {persona.background_story && (
        <section>
          <h5 className="text-sm font-semibold text-slate-800 mb-2">Historia</h5>
          <p className="text-sm leading-relaxed text-slate-600 whitespace-pre-line">
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
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [numPersonas, setNumPersonas] = useState(10);
  const [adversarialMode, setAdversarialMode] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [advancedOptions, setAdvancedOptions] = useState({
    ageFocus: 'balanced',
    genderBalance: 'balanced',
    urbanicity: 'any',
    targetCities: '',
    targetCountries: '',
    industries: '',
    requiredValues: '',
    excludedValues: '',
    requiredInterests: '',
    excludedInterests: '',
    ageMin: '',
    ageMax: '',
    customAge: '',
    customGender: '',
    customLocation: '',
    customEducation: '',
    customIncome: '',
  });
  const queryClient = useQueryClient();
  const [generationProgress, setGenerationProgress] = useState(0);
  const [progressMeta, setProgressMeta] = useState<{ start: number; duration: number } | null>(null);
  const updateAdvancedOption = (key: keyof typeof advancedOptions, value: string) => {
    setAdvancedOptions((prev) => ({ ...prev, [key]: value }));
  };
  const resetAdvanced = () => {
    setAdvancedOptions({
      ageFocus: 'balanced',
      genderBalance: 'balanced',
      urbanicity: 'any',
      targetCities: '',
      targetCountries: '',
      industries: '',
      requiredValues: '',
      excludedValues: '',
      requiredInterests: '',
      excludedInterests: '',
      ageMin: '',
      ageMax: '',
      customAge: '',
      customGender: '',
      customLocation: '',
      customEducation: '',
      customIncome: '',
    });
  };
  const parseList = (value: string) =>
    value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

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

  const handleGenerate = () => {
    if (!selectedProject) {
      return;
    }

    const payload: GeneratePersonasPayload = {
      num_personas: numPersonas,
      adversarial_mode: adversarialMode,
    };

    if (showAdvancedOptions) {
      const advancedPayload: PersonaAdvancedOptions = {};

      if (advancedOptions.ageFocus !== 'balanced') {
        advancedPayload.age_focus = advancedOptions.ageFocus as PersonaAdvancedOptions['age_focus'];
      }
      if (advancedOptions.genderBalance !== 'balanced') {
        advancedPayload.gender_balance = advancedOptions.genderBalance as PersonaAdvancedOptions['gender_balance'];
      }
      if (advancedOptions.urbanicity !== 'any') {
        advancedPayload.urbanicity = advancedOptions.urbanicity as PersonaAdvancedOptions['urbanicity'];
      }

      const cities = parseList(advancedOptions.targetCities);
      if (cities.length > 0) {
        advancedPayload.target_cities = cities;
      }

      const countries = parseList(advancedOptions.targetCountries);
      if (countries.length > 0) {
        advancedPayload.target_countries = countries;
      }

      const industries = parseList(advancedOptions.industries);
      if (industries.length > 0) {
        advancedPayload.industries = industries;
      }

      const requiredValues = parseList(advancedOptions.requiredValues);
      if (requiredValues.length > 0) {
        advancedPayload.required_values = requiredValues;
      }

      const excludedValues = parseList(advancedOptions.excludedValues);
      if (excludedValues.length > 0) {
        advancedPayload.excluded_values = excludedValues;
      }

      const requiredInterests = parseList(advancedOptions.requiredInterests);
      if (requiredInterests.length > 0) {
        advancedPayload.required_interests = requiredInterests;
      }

      const excludedInterests = parseList(advancedOptions.excludedInterests);
      if (excludedInterests.length > 0) {
        advancedPayload.excluded_interests = excludedInterests;
      }

      const ageMinNumber = advancedOptions.ageMin ? Number(advancedOptions.ageMin) : undefined;
      const ageMaxNumber = advancedOptions.ageMax ? Number(advancedOptions.ageMax) : undefined;
      if (
        typeof ageMinNumber === 'number' &&
        !Number.isNaN(ageMinNumber) &&
        typeof ageMaxNumber === 'number' &&
        !Number.isNaN(ageMaxNumber) &&
        ageMinNumber <= ageMaxNumber
      ) {
        advancedPayload.age_min = ageMinNumber;
        advancedPayload.age_max = ageMaxNumber;
      }

      if (Object.keys(advancedPayload).length > 0) {
        payload.advanced_options = advancedPayload;
      }
    }

    setProgressMeta({ start: Date.now(), duration: Math.max(5000, numPersonas * 2500) });
    setGenerationProgress(5);
    generateMutation.mutate(payload);
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
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="flex items-center gap-2">
            <ShieldHalf className="w-4 h-4 text-accent-600" />
            <div>
              <p className="text-sm font-medium text-slate-700">Adversarial mode</p>
              <p className="text-xs text-slate-500">
                Generates contrarian personas for stress-testing messaging.
              </p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={adversarialMode}
              onChange={(e) => setAdversarialMode(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-500" />
          </label>
        </div>

        <div className="border border-slate-200 rounded-xl bg-white">
          <button
            type="button"
            onClick={() => setShowAdvancedOptions((prev) => !prev)}
            className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-t-xl"
          >
            <span className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-primary-600" />
              Advanced targeting
            </span>
            {showAdvancedOptions ? (
              <ChevronUp className="w-4 h-4 text-slate-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-500" />
            )}
          </button>
          {showAdvancedOptions && (
            <div className="px-3 pb-3 pt-2 space-y-3 text-sm text-slate-600">
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Age focus</span>
                  <select
                    value={advancedOptions.ageFocus}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, ageFocus: e.target.value }))
                    }
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="balanced">Balanced distribution</option>
                    <option value="young_adults">Young adopters (18-34)</option>
                    <option value="experienced_leaders">Experienced leaders (35+)</option>
                  </select>
                </label>
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Gender balance</span>
                  <select
                    value={advancedOptions.genderBalance}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, genderBalance: e.target.value }))
                    }
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="balanced">Balanced</option>
                    <option value="female_skew">Female leaning</option>
                    <option value="male_skew">Male leaning</option>
                  </select>
                </label>
              </div>

              <label className="flex flex-col gap-1">
                <span className="font-medium text-slate-700">Urbanicity</span>
                <select
                  value={advancedOptions.urbanicity}
                  onChange={(e) =>
                    setAdvancedOptions((prev) => ({ ...prev, urbanicity: e.target.value }))
                  }
                  className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="any">Any location mix</option>
                  <option value="urban">Urban (city-centric)</option>
                  <option value="suburban">Suburban mix</option>
                  <option value="rural">Rural leaning</option>
                </select>
              </label>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Target cities</span>
                  <input
                    type="text"
                    value={advancedOptions.targetCities}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, targetCities: e.target.value }))
                    }
                    placeholder="e.g. San Francisco, New York"
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <span className="text-xs text-slate-500">Comma-separated list. Leave blank for any.</span>
                </label>
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Target countries</span>
                  <input
                    type="text"
                    value={advancedOptions.targetCountries}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, targetCountries: e.target.value }))
                    }
                    placeholder="e.g. United States, Canada"
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
              </div>

              <label className="flex flex-col gap-1">
                <span className="font-medium text-slate-700">Industry focus</span>
                <input
                  type="text"
                  value={advancedOptions.industries}
                  onChange={(e) =>
                    setAdvancedOptions((prev) => ({ ...prev, industries: e.target.value }))
                  }
                  placeholder="e.g. Technology, Finance"
                  className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </label>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Required values</span>
                  <input
                    type="text"
                    value={advancedOptions.requiredValues}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, requiredValues: e.target.value }))
                    }
                    placeholder="innovation, sustainability"
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Exclude values</span>
                  <input
                    type="text"
                    value={advancedOptions.excludedValues}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, excludedValues: e.target.value }))
                    }
                    placeholder="tradition"
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Required interests</span>
                  <input
                    type="text"
                    value={advancedOptions.requiredInterests}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, requiredInterests: e.target.value }))
                    }
                    placeholder="AI, design thinking"
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Exclude interests</span>
                  <input
                    type="text"
                    value={advancedOptions.excludedInterests}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, excludedInterests: e.target.value }))
                    }
                    placeholder="legacy systems"
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Minimum age</span>
                  <input
                    type="number"
                    min={18}
                    max={90}
                    value={advancedOptions.ageMin}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, ageMin: e.target.value }))
                    }
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="font-medium text-slate-700">Maximum age</span>
                  <input
                    type="number"
                    min={18}
                    max={90}
                    value={advancedOptions.ageMax}
                    onChange={(e) =>
                      setAdvancedOptions((prev) => ({ ...prev, ageMax: e.target.value }))
                    }
                    className="border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </label>
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setShowGenerateForm(false);
              setShowAdvancedOptions(false);
            }}
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
            onClick={() => setShowWizard(true)}
            variant="primary"
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700"
          >
            <Sparkles className="w-5 h-5" />
            Advanced Wizard
          </Button>
          <Button
            onClick={() => setShowGenerateForm((prev) => !prev)}
            variant={showGenerateForm ? 'outline' : 'secondary'}
            className="flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            {showGenerateForm ? 'Hide quick generator' : 'Quick generate'}
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
          <div className="flex gap-3">
            <Button onClick={() => setShowWizard(true)} variant="primary" className="gap-2 bg-purple-600 hover:bg-purple-700">
              <Sparkles className="w-5 h-5" />
              Advanced Wizard
            </Button>
            <Button onClick={() => setShowGenerateForm(true)} variant="secondary" className="gap-2">
              <Plus className="w-5 h-5" />
              Quick Generate
            </Button>
          </div>
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
