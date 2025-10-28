import React, { useState, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  MoreVertical,
  Plus,
  Users,
  Eye,
  TrendingUp,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Filter,
  Database,
  Trash2,
} from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { PersonaGenerationWizard, type PersonaGenerationConfig } from '@/components/personas/PersonaGenerationWizard';
import { PersonaDetailsDrawer } from '@/components/personas/PersonaDetailsDrawer';
import { DeletePersonaDialog } from '@/components/DeletePersonaDialog';
import { PageHeader } from '@/components/layout/PageHeader';
import { projectsApi, personasApi } from '@/lib/api';
import type { GeneratePersonasPayload } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { Persona as APIPersona } from '@/types';
import { toast } from '@/components/ui/toastStore';
import { estimateGenerationDuration, transformWizardConfigToPayload } from '@/lib/personaGeneration';
import { SpinnerLogo } from '@/components/ui/spinner-logo';


// Display-friendly Persona interface
interface DisplayPersona {
  id: string;
  name: string;
  age: number;
  occupation: string;
  interests: string[];
  background: string;
  demographics: {
    gender: string;
    location: string;
    income: string;
    education: string;
  };
  psychographics: {
    personality: string[];
    values: string[];
    lifestyle: string;
  };
  createdAt: string;
  projectId: string;
}

/**
 * Transform API Persona to display-friendly format
 */

// Mapowania i pomocnicze funkcje do polonizacji danych wyświetlanych w UI
const GENDER_LABELS: Record<string, string> = {
  female: 'Kobieta',
  kobieta: 'Kobieta',
  male: 'Mężczyzna',
  mężczyzna: 'Mężczyzna',
  man: 'Mężczyzna',
  woman: 'Kobieta',
  'non-binary': 'Osoba niebinarna',
  nonbinary: 'Osoba niebinarna',
  other: 'Osoba niebinarna',
};

const EDUCATION_LABELS: Record<string, string> = {
  'high school': 'Średnie ogólnokształcące',
  'some college': 'Policealne',
  "bachelor's degree": 'Wyższe licencjackie',
  "master's degree": 'Wyższe magisterskie',
  "masters degree": 'Wyższe magisterskie',
  doctorate: 'Doktorat',
  phd: 'Doktorat',
  'technical school': 'Średnie techniczne',
  'trade school': 'Zasadnicze zawodowe',
  vocational: 'Zasadnicze zawodowe',
};

const INCOME_LABELS: Record<string, string> = {
  '< $25k': '< 3 000 zł',
  '$25k-$50k': '3 000 - 5 000 zł',
  '$50k-$75k': '5 000 - 7 500 zł',
  '$75k-$100k': '7 500 - 10 000 zł',
  '$100k-$150k': '10 000 - 15 000 zł',
  '> $150k': '> 15 000 zł',
  '$150k+': '> 15 000 zł',
};

const POLISH_CITY_NAMES = [
  'Warszawa',
  'Kraków',
  'Wrocław',
  'Gdańsk',
  'Poznań',
  'Łódź',
  'Katowice',
  'Szczecin',
  'Lublin',
  'Białystok',
  'Bydgoszcz',
  'Gdynia',
  'Częstochowa',
  'Radom',
  'Toruń',
  'Inne miasta',
];

const POLISH_CITY_LOOKUP: Record<string, string> = POLISH_CITY_NAMES.reduce((acc, city) => {
  acc[normalizeText(city)] = city;
  return acc;
}, {} as Record<string, string>);

const LOCATION_ALIASES: Record<string, string> = {
  warsaw: 'Warszawa',
  krakow: 'Kraków',
  wroclaw: 'Wrocław',
  poznan: 'Poznań',
  lodz: 'Łódź',
  gdansk: 'Gdańsk',
  gdynia: 'Gdynia',
  szczecin: 'Szczecin',
  lublin: 'Lublin',
  bialystok: 'Białystok',
  bydgoszcz: 'Bydgoszcz',
  katowice: 'Katowice',
  czestochowa: 'Częstochowa',
  torun: 'Toruń',
  radom: 'Radom',
};

function normalizeText(value?: string | null): string {
  if (!value) return '';
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function detectCityFromStory(story?: string | null): string | null {
  if (!story) return null;
  const normalizedStory = normalizeText(story);
  for (const city of POLISH_CITY_NAMES) {
    const normalizedCity = normalizeText(city);
    if (!normalizedCity) continue;
    if (normalizedStory.includes(normalizedCity)) return city;
    if (normalizedStory.includes(`${normalizedCity}u`)) return city;
    if (normalizedStory.includes(`${normalizedCity}ie`)) return city;
    if (normalizedStory.includes(`${normalizedCity}iu`)) return city;
  }
  return null;
}

function polishifyLocation(location?: string | null, story?: string | null): string {
  const normalized = normalizeText(location);
  if (normalized) {
    if (POLISH_CITY_LOOKUP[normalized]) {
      return POLISH_CITY_LOOKUP[normalized];
    }
    if (LOCATION_ALIASES[normalized]) {
      return LOCATION_ALIASES[normalized];
    }
    const parts = normalized.split(/[,/]/).map(part => part.trim());
    for (const part of parts) {
      if (POLISH_CITY_LOOKUP[part]) return POLISH_CITY_LOOKUP[part];
      if (LOCATION_ALIASES[part]) return LOCATION_ALIASES[part];
    }
  }
  const fromStory = detectCityFromStory(story);
  if (fromStory) return fromStory;
  return 'Warszawa';
}

function polishifyGender(gender?: string | null): string {
  const normalized = normalizeText(gender);
  return GENDER_LABELS[normalized] ?? (gender ? gender : 'Kobieta');
}

function polishifyEducation(education?: string | null): string {
  const normalized = normalizeText(education);
  if (normalized && EDUCATION_LABELS[normalized]) {
    return EDUCATION_LABELS[normalized];
  }
  return education ?? 'Średnie ogólnokształcące';
}

function polishifyIncome(income?: string | null): string {
  if (!income) return '5 000 - 7 500 zł';
  const normalized = income.replace(/\s/g, '');
  if (INCOME_LABELS[income]) return INCOME_LABELS[income];
  if (INCOME_LABELS[normalized]) return INCOME_LABELS[normalized];
  return income;
}

function formatAge(age: number): string {
  const mod10 = age % 10;
  const mod100 = age % 100;
  if (mod10 === 1 && mod100 !== 11) return `${age} rok`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${age} lata`;
  return `${age} lat`;
}

function extractFirstName(fullName?: string | null): string {
  if (!fullName) return 'Persona';
  const parts = fullName.trim().split(/\s+/);
  return parts.length > 0 ? parts[0] : fullName;
}

function transformPersona(apiPersona: APIPersona): DisplayPersona {
  // Zbuduj opis tła i zadbaj o brakujące dane
  const background = (apiPersona.background_story || apiPersona.headline || 'Brak opisu persony').trim();

  // Cechy osobowości Big Five w uproszczonym języku polskim
  const personality: string[] = [];
  if (apiPersona.openness && apiPersona.openness > 0.6) personality.push('Otwartość na zmiany');
  if (apiPersona.conscientiousness && apiPersona.conscientiousness > 0.6) personality.push('Wysoka sumienność');
  if (apiPersona.extraversion && apiPersona.extraversion > 0.6) personality.push('Ekstrawersja');
  if (apiPersona.agreeableness && apiPersona.agreeableness > 0.6) personality.push('Ugodowość');
  if (apiPersona.neuroticism && apiPersona.neuroticism < 0.4) personality.push('Spokój emocjonalny');

  // Styl życia zależny od poziomu indywidualizmu
  let lifestyle = 'Zrównoważony styl życia';
  if (apiPersona.individualism && apiPersona.individualism > 0.7) {
    lifestyle = 'Niezależny i samodzielny styl życia';
  } else if (apiPersona.individualism && apiPersona.individualism < 0.3) {
    lifestyle = 'Skupienie na społeczności i współpracy';
  }

  const gender = polishifyGender(apiPersona.gender);
  const education = polishifyEducation(apiPersona.education_level);
  const income = polishifyIncome(apiPersona.income_bracket);
  const location = polishifyLocation(apiPersona.location, background);

  return {
    id: apiPersona.id,
    name: apiPersona.full_name || apiPersona.persona_title || 'Nieznana persona',
    age: apiPersona.age,
    occupation: apiPersona.occupation || apiPersona.persona_title || 'Zawód nieokreślony',
    interests: Array.isArray(apiPersona.interests) ? apiPersona.interests : [],
    background,
    demographics: {
      gender,
      location,
      income,
      education,
    },
    psychographics: {
      personality,
      values: Array.isArray(apiPersona.values) ? apiPersona.values : [],
      lifestyle,
    },
    createdAt: apiPersona.created_at,
    projectId: apiPersona.project_id,
  };
}


export function Personas() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const selectedProject = useAppStore(state => state.selectedProject);
  const setGlobalProject = useAppStore(state => state.setSelectedProject);
  const setActivePanel = useAppStore(state => state.setActivePanel);

  const projectLabel = selectedProject?.name || 'Nieznany projekt';
  const [selectedPersonaForDetails, setSelectedPersonaForDetails] = useState<string | null>(null);
  const [showPersonaWizard, setShowPersonaWizard] = useState(false);
  const [currentPersonaIndex, setCurrentPersonaIndex] = useState(0);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [progressMeta, setProgressMeta] = useState<{
    start: number;
    duration: number;
    targetCount: number;
    baselineCount: number;
  } | null>(null);
  const [activeGenerationProjectId, setActiveGenerationProjectId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const timeoutWarningIssued = React.useRef(false);

  // Filter states
  const [selectedGenders, setSelectedGenders] = useState<string[]>([]);
  const [ageRange, setAgeRange] = useState<[number, number]>([18, 65]);
  const [selectedOccupations, setSelectedOccupations] = useState<string[]>([]);

  // Delete dialog state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [personaToDelete, setPersonaToDelete] = useState<DisplayPersona | null>(null);

  // Fetch all projects
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  // Fetch personas for selected project and transform to display format
  const { data: apiPersonas = [] } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await personasApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
    refetchInterval: (query) => {
      // Explicit guards to prevent unnecessary refetching
      if (!selectedProject) return false;
      if (!progressMeta) return false;
      if (activeGenerationProjectId !== selectedProject.id) return false;
      if (progressMeta.targetCount <= 0) return false;

      const data = query.state.data as APIPersona[] | undefined;
      const currentCount = Array.isArray(data) ? data.length : 0;
      const baseline = progressMeta.baselineCount;
      const expectedTotal = baseline + progressMeta.targetCount;

      // Stop refetching once we reach the target
      if (currentCount >= expectedTotal) return false;

      // Refetch every 3 seconds while generating (increased from 2s for better performance)
      return 3000;
    },
  });

  // CRITICAL FIX: Memoize transform separately to avoid recalculating on every filter change
  // transformPersona is expensive (regex, normalization, mapping), so we only do it when apiPersonas changes
  const transformedPersonas = useMemo(
    () => apiPersonas.map(transformPersona),
    [apiPersonas] // Only recalculate when API data changes!
  );

  // Now apply filters - this is fast (just array filtering)
  const filteredPersonas = useMemo(() => {
    let personas = transformedPersonas;

    // Apply gender filter
    if (selectedGenders.length > 0) {
      personas = personas.filter(p => selectedGenders.includes(p.demographics.gender));
    }

    // Apply age range filter
    personas = personas.filter(p => p.age >= ageRange[0] && p.age <= ageRange[1]);

    // Apply occupation filter
    if (selectedOccupations.length > 0) {
      personas = personas.filter(p => selectedOccupations.some(occ => p.occupation.toLowerCase().includes(occ.toLowerCase())));
    }

    return personas;
  }, [transformedPersonas, selectedGenders, ageRange, selectedOccupations]);

  // Reset carousel index when filtered personas change
  const prevFilteredLength = React.useRef(filteredPersonas.length);
  React.useEffect(() => {
    if (filteredPersonas.length !== prevFilteredLength.current) {
      setCurrentPersonaIndex(0);
      prevFilteredLength.current = filteredPersonas.length;
    }
  }, [filteredPersonas.length]);

  React.useEffect(() => {
    if (!selectedProject) {
      setActiveGenerationProjectId(null);
      setGenerationProgress(0);
      setProgressMeta(null);
    }
  }, [selectedProject]);

  // Calculate population statistics based on filtered personas
  const ageGroups = filteredPersonas.reduce((acc, persona) => {
    const ageGroup = persona.age < 25 ? '18-24' :
                    persona.age < 35 ? '25-34' :
                    persona.age < 45 ? '35-44' :
                    persona.age < 55 ? '45-54' : '55+';
    acc[ageGroup] = (acc[ageGroup] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const currentPersona = filteredPersonas[currentPersonaIndex] ?? null;
  const currentPersonaName = currentPersona ? extractFirstName(currentPersona.name) : '';
  const currentPersonaAgeLabel = currentPersona ? formatAge(currentPersona.age) : '';


  const topInterests = filteredPersonas.flatMap(p => p.interests)
    .reduce((acc, interest) => {
      acc[interest] = (acc[interest] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

  const sortedInterests = Object.entries(topInterests)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5);

  const baselineCount = progressMeta?.baselineCount ?? 0;
  const requestedCount = progressMeta?.targetCount ?? 0;
  const newlyGeneratedCount = Math.max(0, apiPersonas.length - baselineCount);
  const hasReachedTarget = Boolean(progressMeta && requestedCount > 0 && newlyGeneratedCount >= requestedCount);
  const isCurrentProjectGenerating =
    activeGenerationProjectId !== null && activeGenerationProjectId === selectedProject?.id;

  const generateMutation = useMutation({
    mutationFn: (payload: GeneratePersonasPayload) =>
      personasApi.generate(selectedProject!.id, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['personas', selectedProject?.id] });
      queryClient.invalidateQueries({ queryKey: ['personas', 'all'] });
      const modeCopy = variables.adversarial_mode ? 'Tryb Adversarial' : 'Tryb Standard';
      toast.info(
        'Generowanie uruchomione',
        `${projectLabel} • ${modeCopy}, ${variables.num_personas} personas w tle.`,
      );
    },
    onError: (error: Error) => {
      setGenerationProgress(0);
      setProgressMeta(null);
      setShowPersonaWizard(true);
      setActiveGenerationProjectId(null);
      toast.error('Generowanie zatrzymane', `${projectLabel} • ${error.message}`);
    },
  });

  const isGenerating = Boolean(isCurrentProjectGenerating && progressMeta && !hasReachedTarget);

  React.useEffect(() => {
    if (!progressMeta || !isCurrentProjectGenerating) {
      return;
    }

    if (hasReachedTarget) {
      setGenerationProgress(100);
      const timeout = setTimeout(() => {
        setGenerationProgress(0);
        setProgressMeta(null);
        setActiveGenerationProjectId(null);
      }, 800);
      return () => clearTimeout(timeout);
    }

    if (!isGenerating) {
      return;
    }

    if (progressMeta.targetCount > 0 && newlyGeneratedCount > 0) {
      const ratio = Math.min(newlyGeneratedCount / progressMeta.targetCount, 0.99);
      setGenerationProgress((prev) => Math.max(prev, Math.max(5, ratio * 100)));
      return;
    }

    const interval = setInterval(() => {
      setGenerationProgress((prev) => {
        const elapsed = Date.now() - progressMeta.start;
        const ratio = Math.min(elapsed / progressMeta.duration, 0.97);
        const target = 5 + ratio * 90;
        return prev + (target - prev) * 0.35;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [
    isGenerating,
    progressMeta,
    newlyGeneratedCount,
    hasReachedTarget,
    isCurrentProjectGenerating,
  ]);

  React.useEffect(() => {
    if (!isGenerating || !progressMeta) {
      timeoutWarningIssued.current = false;
      return;
    }

    const timeoutMs = Math.max(20000, progressMeta.duration * 2);
    const timer = setTimeout(() => {
      if (!hasReachedTarget && !timeoutWarningIssued.current) {
        timeoutWarningIssued.current = true;
        toast.info(
          'Generowanie nadal trwa',
          `${projectLabel} • Proces trwa dłużej niż zwykle — sprawdź logi serwera, jeśli nic się nie zmieni.`,
        );
      }
    }, timeoutMs);

    return () => clearTimeout(timer);
  }, [isGenerating, progressMeta, hasReachedTarget]);

  const handleGeneratePersonas = (config: PersonaGenerationConfig) => {
    if (!selectedProject) {
      toast.error('Wybierz projekt, aby wygenerować persony.');
      return;
    }

    const payload = transformWizardConfigToPayload(config);
    const baselineCount = apiPersonas.length;
    setActiveGenerationProjectId(selectedProject.id);
    setShowPersonaWizard(false);
    timeoutWarningIssued.current = false;
    setProgressMeta({
        start: Date.now(),
        duration: estimateGenerationDuration(payload.num_personas),
        targetCount: payload.num_personas,
        baselineCount,
      });
    setGenerationProgress(5);
    generateMutation.mutate(payload);
  };

  const showProgressBar =
    activeGenerationProjectId === selectedProject?.id && generationProgress > 0;

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
      {/* Header */}
      <PageHeader
        title="Persony"
        subtitle="Zarządzaj personami wygenerowanymi przez AI dla swoich projektów badawczych"
        actions={
          <>
            <Button
              type="button"
              variant="outline"
              className="border-border text-card-foreground"
              onClick={() => setActivePanel('rag')}
            >
              <Database className="w-4 h-4 mr-2" />
              Dokumenty RAG
            </Button>
            <Select
              value={selectedProject?.id || ''}
              onValueChange={(value) => {
                const project = projects.find(p => p.id === value);
                if (project) setGlobalProject(project);
              }}
            >
              <SelectTrigger className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-0 rounded-md px-3.5 py-2 h-9 hover:bg-[#f0f1f2] dark:hover:bg-[#333333] transition-colors">
                <SelectValue
                  placeholder="Wybierz projekt"
                  className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] leading-5"
                />
              </SelectTrigger>
              <SelectContent className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-border">
                {projectsLoading ? (
                  <div className="flex items-center justify-center p-2">
                    <SpinnerLogo className="w-4 h-4" />
                  </div>
                ) : projects.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">Nie znaleziono projektów</div>
                ) : (
                  projects.map((project) => (
                    <SelectItem
                      key={project.id}
                      value={project.id}
                      className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] focus:bg-[#e9ecef] dark:focus:bg-[#333333]"
                    >
                      {project.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            <Button
              onClick={() => setShowPersonaWizard(true)}
              className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              Generuj persony
            </Button>
          </>
        }
      />

      {showProgressBar && (
        <div className="rounded-lg border border-border bg-card/80 p-4 space-y-2 shadow-sm">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <SpinnerLogo className="w-4 h-4" />
            <span className="font-medium text-card-foreground">Generowanie person...</span>
          </div>
          <Progress value={Math.min(generationProgress, 100)} />
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Wszystkie persony</p>
                <p className="text-2xl brand-orange">{filteredPersonas.length}</p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Przedział wieku</p>
                <p className="text-2xl brand-orange">
                  {filteredPersonas.length > 0 ? `${Math.min(...filteredPersonas.map(p => p.age))} - ${Math.max(...filteredPersonas.map(p => p.age))}` : 'N/A'}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Główne zainteresowanie</p>
                <p className="text-2xl brand-orange">
                  {sortedInterests[0]?.[0] || 'N/A'}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Population Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Rozkład wieku</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(ageGroups).map(([ageGroup, count]) => (
              <div key={ageGroup} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{ageGroup}</span>
                  <span className="text-card-foreground">{count} ({Math.round((count / filteredPersonas.length) * 100)}%)</span>
                </div>
                <Progress value={(count / filteredPersonas.length) * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Główne zainteresowania</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sortedInterests.map(([interest, count]) => (
              <div key={interest} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{interest}</span>
                  <span className="text-card-foreground">{count} person</span>
                </div>
                <Progress value={(count / filteredPersonas.length) * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Persona Carousel */}
      <div className="space-y-4">
        <h2 className="text-xl text-foreground">Projektuj persony</h2>

        {apiPersonas.length === 0 ? (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">Brak wygenerowanych person</h3>
              <p className="text-muted-foreground mb-4">
                Uruchom generator, aby poznać swoją grupę docelową na podstawie sztucznej inteligencji
              </p>
              <Button
                onClick={() => setShowPersonaWizard(true)}
                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Wygeneruj pierwsze persony
              </Button>
            </CardContent>
          </Card>
        ) : filteredPersonas.length === 0 ? (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <Filter className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">Brak person spełniających obecne filtry</h3>
              <p className="text-muted-foreground mb-4">
                Zmień ustawienia filtrów, aby zobaczyć więcej wyników
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedGenders([]);
                  setAgeRange([18, 65]);
                  setSelectedOccupations([]);
                }}
                className="border-border"
              >
                Wyczyść filtry
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-12 gap-6 max-h-[600px]">
            {/* Filters Sidebar */}
            <div className="col-span-12 lg:col-span-4">
              <Card className="bg-card border border-border overflow-y-auto" style={{ maxHeight: '600px' }}>
                <CardHeader>
                  <CardTitle className="text-card-foreground flex items-center gap-2">
                    <Filter className="w-5 h-5" />
                    Filtry i segmenty
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Gender Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm">Płeć</Label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="gender-female"
                          checked={selectedGenders.includes('Kobieta')}
                          onCheckedChange={(checked) => {
                            setSelectedGenders(checked
                              ? [...selectedGenders, 'Kobieta']
                              : selectedGenders.filter(g => g !== 'Kobieta')
                            );
                          }}
                        />
                        <label htmlFor="gender-female" className="text-sm text-card-foreground">
                          Kobieta
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="gender-male"
                          checked={selectedGenders.includes('Mężczyzna')}
                          onCheckedChange={(checked) => {
                            setSelectedGenders(checked
                              ? [...selectedGenders, 'Mężczyzna']
                              : selectedGenders.filter(g => g !== 'Mężczyzna')
                            );
                          }}
                        />
                        <label htmlFor="gender-male" className="text-sm text-card-foreground">
                          Mężczyzna
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="gender-other"
                          checked={selectedGenders.includes('Osoba niebinarna')}
                          onCheckedChange={(checked) => {
                            setSelectedGenders(checked
                              ? [...selectedGenders, 'Osoba niebinarna']
                              : selectedGenders.filter(g => g !== 'Osoba niebinarna')
                            );
                          }}
                        />
                        <label htmlFor="gender-other" className="text-sm text-card-foreground">
                          Osoba niebinarna
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Age Range Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm">Przedział wieku</Label>
                    <div className="px-2">
                      <Slider
                        value={ageRange}
                        onValueChange={(value) => setAgeRange(value as [number, number])}
                        min={18}
                        max={65}
                        step={1}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>{ageRange[0]}</span>
                        <span>{ageRange[1]}</span>
                      </div>
                    </div>
                  </div>

                  {/* Occupation Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm">Zawód</Label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-tech" />
                        <label htmlFor="occupation-tech" className="text-sm text-card-foreground">
                          Technology (35%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-healthcare" />
                        <label htmlFor="occupation-healthcare" className="text-sm text-card-foreground">
                          Healthcare (25%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-education" />
                        <label htmlFor="occupation-education" className="text-sm text-card-foreground">
                          Education (20%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-business" />
                        <label htmlFor="occupation-business" className="text-sm text-card-foreground">
                          Business (20%)
                        </label>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => {
                      setSelectedGenders([]);
                      setAgeRange([18, 65]);
                      setSelectedOccupations([]);
                    }}
                  >
                    Wyczyść filtry
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Persona Carousel */}
            <div className="col-span-12 lg:col-span-8">
              <Card className="bg-card border border-border overflow-y-auto" style={{ maxHeight: '600px' }}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPersonaIndex(Math.max(0, currentPersonaIndex - 1))}
                        disabled={currentPersonaIndex === 0}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        {currentPersonaIndex + 1} z {filteredPersonas.length}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPersonaIndex(Math.min(filteredPersonas.length - 1, currentPersonaIndex + 1))}
                        disabled={currentPersonaIndex === filteredPersonas.length - 1}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    <div className="flex gap-2">
                      {filteredPersonas.map((_, index) => (
                        <button
                          key={index}
                          className={`w-2 h-2 rounded-full transition-colors ${
                            index === currentPersonaIndex ? 'bg-primary' : 'bg-muted'
                          }`}
                          onClick={() => setCurrentPersonaIndex(index)}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Aktualnie wybrana persona */}
                  {currentPersona && (
                    <div className="space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-xl text-card-foreground mb-1">
                            {currentPersonaName ? `${currentPersonaName}, ${currentPersonaAgeLabel}` : `${currentPersona.name}`}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {currentPersona.occupation}
                          </p>
                          <p className="text-muted-foreground">
                            {currentPersona.demographics.location}
                          </p>
                        </div>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => setSelectedPersonaForDetails(currentPersona.id)}>
                              <Eye className="w-4 h-4 mr-2" />
                              Szczegóły persony
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                setPersonaToDelete(currentPersona);
                                setShowDeleteDialog(true);
                              }}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Usuń personę
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>

                      {/* Background */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-semibold text-card-foreground">Kontekst</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                          {currentPersona.background}
                        </p>
                      </div>

                      {/* Demographics Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="space-y-0.5">
                          <p className="text-xs text-muted-foreground">Płeć</p>
                          <p className="text-sm text-card-foreground">{currentPersona.demographics.gender}</p>
                        </div>
                        <div className="space-y-0.5">
                          <p className="text-xs text-muted-foreground">Wykształcenie</p>
                          <p className="text-sm text-card-foreground">{currentPersona.demographics.education}</p>
                        </div>
                        <div className="space-y-0.5">
                          <p className="text-xs text-muted-foreground">Dochód</p>
                          <p className="text-sm text-card-foreground">{currentPersona.demographics.income}</p>
                        </div>
                        <div className="space-y-0.5">
                          <p className="text-xs text-muted-foreground">Styl życia</p>
                          <p className="text-sm text-card-foreground line-clamp-1">{currentPersona.psychographics.lifestyle}</p>
                        </div>
                      </div>

                      {/* Interests */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-semibold text-card-foreground">Zainteresowania i wartości</h4>
                        <div className="space-y-1.5">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Zainteresowania</p>
                            <div className="flex flex-wrap gap-1.5">
                              {currentPersona.interests.slice(0, 5).map((interest, index) => (
                                <Badge key={index} variant="secondary" className="bg-primary/10 text-primary border-primary/20 text-xs py-0">
                                  {interest}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Wartości</p>
                            <div className="flex flex-wrap gap-1.5">
                              {currentPersona.psychographics.values.slice(0, 5).map((value, index) => (
                                <Badge key={index} variant="outline" className="border-secondary text-secondary text-xs py-0">
                                  {value}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Creation Date */}
                      <div className="pt-2">
                        <p className="text-xs text-muted-foreground text-right">
                          Utworzono {new Date(filteredPersonas[currentPersonaIndex].createdAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>

      {/* Persona Details Drawer */}
      <PersonaDetailsDrawer
        personaId={selectedPersonaForDetails}
        isOpen={!!selectedPersonaForDetails}
        onClose={() => setSelectedPersonaForDetails(null)}
      />

      {/* Persona Generation Wizard */}
      <PersonaGenerationWizard
        open={showPersonaWizard}
        onOpenChange={setShowPersonaWizard}
        onGenerate={handleGeneratePersonas}
      />

      {/* Delete Persona Dialog */}
      <DeletePersonaDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        personaId={personaToDelete?.id || ''}
        personaName={personaToDelete?.name || ''}
        onSuccess={() => {
          setShowDeleteDialog(false);
          setPersonaToDelete(null);
        }}
      />
      </div>
    </div>
  );
}
