import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Plus, Users, Filter, AlertCircle } from 'lucide-react';
import { PersonaGenerationWizard, type PersonaGenerationConfig } from '@/components/personas/PersonaGenerationWizard';
import { PersonaDetailsDrawer } from '@/components/personas/PersonaDetailsDrawer';
import { DeletePersonaDialog } from '@/components/personas/DeletePersonaDialog';
import { projectsApi, personasApi } from '@/lib/api';
import type { GeneratePersonasPayload } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { Persona as APIPersona } from '@/types';
import { toast } from '@/components/ui/toastStore';
import { estimateGenerationDuration, transformWizardConfigToPayload } from '@/lib/personaGeneration';
import { useTranslation } from 'react-i18next';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { transformPersona, type DisplayPersona } from '@/components/personas/helpers/transformers';
import { PersonaFilters } from '@/components/personas/PersonaFilters';
import { PersonasList } from '@/components/personas/PersonasList';
import { PersonasHeader } from '@/components/personas/PersonasHeader';
import { PersonasProgressBar } from '@/components/personas/PersonasProgressBar';
import { PersonasStats } from '@/components/personas/PersonasStats';

export function Personas() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const selectedProject = useAppStore(state => state.selectedProject);
  const setGlobalProject = useAppStore(state => state.setSelectedProject);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const { t } = useTranslation('personas');

  const projectLabel = selectedProject?.name || t('page.generationToast.unknownProject');
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

  // Mobile filters state
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Delete dialog state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [personaToDelete, setPersonaToDelete] = useState<DisplayPersona | null>(null);

  // Orchestration warning state
  const [orchestrationWarning, setOrchestrationWarning] = useState<string | null>(null);

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

  // Keyboard navigation for personas carousel
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Ignore if user is typing in input field
    if ((e.target as HTMLElement).tagName === 'INPUT' ||
        (e.target as HTMLElement).tagName === 'TEXTAREA') {
      return;
    }

    switch (e.key) {
      case 'ArrowLeft':
        // Previous persona
        e.preventDefault();
        setCurrentPersonaIndex((prev) => Math.max(0, prev - 1));
        break;

      case 'ArrowRight':
        // Next persona
        e.preventDefault();
        setCurrentPersonaIndex((prev) =>
          Math.min(filteredPersonas.length - 1, prev + 1)
        );
        break;

      case 'Home':
        // First persona
        e.preventDefault();
        setCurrentPersonaIndex(0);
        break;

      case 'End':
        // Last persona
        e.preventDefault();
        setCurrentPersonaIndex(filteredPersonas.length - 1);
        break;
    }
  }, [filteredPersonas.length]);

  // Attach keyboard listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Calculate population statistics based on filtered personas (OPTIMIZED with useMemo)
  const ageGroups = useMemo(() => {
    return filteredPersonas.reduce((acc, persona) => {
      const ageGroup = persona.age < 25 ? '18-24' :
                      persona.age < 35 ? '25-34' :
                      persona.age < 45 ? '35-44' :
                      persona.age < 55 ? '45-54' : '55+';
      acc[ageGroup] = (acc[ageGroup] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [filteredPersonas]);

  // Top interests computation (OPTIMIZED with useMemo)
  const topInterests = useMemo(() => {
    return filteredPersonas.flatMap(p => p.interests)
      .reduce((acc, interest) => {
        acc[interest] = (acc[interest] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
  }, [filteredPersonas]);

  const sortedInterests = useMemo(() => {
    return Object.entries(topInterests)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);
  }, [topInterests]);

  const baselineCount = progressMeta?.baselineCount ?? 0;
  const requestedCount = progressMeta?.targetCount ?? 0;
  const newlyGeneratedCount = Math.max(0, apiPersonas.length - baselineCount);
  const hasReachedTarget = Boolean(progressMeta && requestedCount > 0 && newlyGeneratedCount >= requestedCount);
  const isCurrentProjectGenerating =
    activeGenerationProjectId !== null && activeGenerationProjectId === selectedProject?.id;

  const generateMutation = useMutation({
    mutationFn: (payload: GeneratePersonasPayload) =>
      personasApi.generate(selectedProject!.id, payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['personas', selectedProject?.id] });
      queryClient.invalidateQueries({ queryKey: ['personas', 'all'] });

      // Zapisz warning jeśli orchestration wyłączone
      if (data.warning) {
        setOrchestrationWarning(data.warning);
        // Auto-clear po 30 sekundach
        setTimeout(() => setOrchestrationWarning(null), 30000);
      }

      const modeCopy = variables.adversarial_mode ? t('page.generationToast.adversarialMode') : t('page.generationToast.standardMode');
      toast.info(
        t('page.generationToast.started'),
        `${projectLabel} • ${modeCopy}, ${t('page.generationToast.personasInBackground', { count: variables.num_personas })}.`,
      );
    },
    onError: (error: Error) => {
      setGenerationProgress(0);
      setProgressMeta(null);
      setShowPersonaWizard(true);
      setActiveGenerationProjectId(null);
      toast.error(t('page.generationToast.stopped'), `${projectLabel} • ${error.message}`);
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
          t('page.generationToast.stillRunning'),
          `${projectLabel} • ${t('page.generationToast.takingLonger')}`,
        );
      }
    }, timeoutMs);

    return () => clearTimeout(timer);
  }, [isGenerating, progressMeta, hasReachedTarget]);

  const handleGeneratePersonas = (config: PersonaGenerationConfig) => {
    if (!selectedProject) {
      toast.error(t('page.generationToast.selectProject'));
      return;
    }

    const payload = transformWizardConfigToPayload(config);
    const baselineCount = apiPersonas.length;
    setActiveGenerationProjectId(selectedProject.id);
    setShowPersonaWizard(false);
    timeoutWarningIssued.current = false;
    setProgressMeta({
        start: Date.now(),
        duration: estimateGenerationDuration(payload.num_personas, {
          useRag: payload.use_rag,
          adversarialMode: payload.adversarial_mode,
        }),
        targetCount: payload.num_personas,
        baselineCount,
      });
    setGenerationProgress(5);
    generateMutation.mutate(payload);
  };

  const showProgressBar =
    activeGenerationProjectId === selectedProject?.id && generationProgress > 0;

  return (
    <ErrorBoundary>
      <div className="w-full h-full overflow-y-auto">
        <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
      {/* Header */}
      <PersonasHeader
        selectedProject={selectedProject}
        projects={projects}
        projectsLoading={projectsLoading}
        onProjectChange={(value) => {
          const project = projects.find(p => p.id === value);
          if (project) setGlobalProject(project);
        }}
        onGenerateClick={() => setShowPersonaWizard(true)}
        onRagDocumentsClick={() => setActivePanel('rag')}
      />

      {showProgressBar && progressMeta && (
        <PersonasProgressBar
          generationProgress={generationProgress}
          progressMeta={progressMeta}
          newlyGeneratedCount={newlyGeneratedCount}
          requestedCount={requestedCount}
        />
      )}

      {/* Stats Overview */}
      <PersonasStats
        filteredPersonas={filteredPersonas}
        ageGroups={ageGroups}
        sortedInterests={sortedInterests}
      />

      {/* Persona Carousel */}
      <div className="space-y-4">
        <h2 className="text-xl text-foreground">{t('page.designPersonas')}</h2>

        {apiPersonas.length === 0 ? (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">{t('page.emptyState.title')}</h3>
              <p className="text-muted-foreground mb-4">
                {t('page.emptyState.description')}
              </p>
              <Button
                onClick={() => setShowPersonaWizard(true)}
                className="bg-brand hover:bg-brand/90 text-brand-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                {t('page.emptyState.generateButton')}
              </Button>
            </CardContent>
          </Card>
        ) : filteredPersonas.length === 0 ? (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <Filter className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">{t('page.noResults.title')}</h3>
              <p className="text-muted-foreground mb-4">
                {t('page.noResults.description')}
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
                {t('page.noResults.clearButton')}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Warning Banner - Orchestration Disabled */}
            {orchestrationWarning && (
              <Alert className="mb-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <AlertDescription className="text-yellow-800 dark:text-yellow-200">
                  <strong className="font-semibold">Uwaga:</strong> {orchestrationWarning}
                  <br />
                  <span className="text-sm mt-1 block">
                    Persony zostały wygenerowane w trybie podstawowym bez szczegółowych analiz.
                    Sprawdź logi serwera: <code className="bg-yellow-100 dark:bg-yellow-800 px-1 rounded">docker-compose logs api | grep Orchestration</code>
                  </span>
                </AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Filters Sidebar */}
              <PersonaFilters
                selectedGenders={selectedGenders}
                onGendersChange={setSelectedGenders}
                ageRange={ageRange}
                onAgeRangeChange={setAgeRange}
                selectedOccupations={selectedOccupations}
                onOccupationsChange={setSelectedOccupations}
                filtersExpanded={filtersExpanded}
                onToggleExpanded={() => setFiltersExpanded(!filtersExpanded)}
              />

              {/* Persona Carousel */}
              <PersonasList
                filteredPersonas={filteredPersonas}
                currentPersonaIndex={currentPersonaIndex}
                onIndexChange={setCurrentPersonaIndex}
                onViewDetails={setSelectedPersonaForDetails}
                onDelete={(persona) => {
                  setPersonaToDelete(persona);
                  setShowDeleteDialog(true);
                }}
              />
          </div>
          </>
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
    </ErrorBoundary>
  );
}
