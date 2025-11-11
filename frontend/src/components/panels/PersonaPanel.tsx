import { motion } from 'framer-motion';
import { useEffect, useState, useRef, type ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/floating-panel';
import { personasApi } from '@/lib/api';
import type { GeneratePersonasPayload } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { User, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toastStore';
import { PersonaGenerationWizard, type PersonaGenerationConfig } from '@/components/personas/PersonaGenerationWizard';
import { estimateGenerationDuration, transformWizardConfigToPayload } from '@/lib/personaGeneration';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { PersonaList } from './PersonaList';
import { PersonaDetailsView } from './PersonaDetailsView';

export function PersonaPanel() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const activePanel = useAppStore(state => state.activePanel);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const selectedProject = useAppStore(state => state.selectedProject);
  const selectedPersona = useAppStore(state => state.selectedPersona);
  const setPersonas = useAppStore(state => state.setPersonas);
  const setSelectedPersona = useAppStore(state => state.setSelectedPersona);
  const [showWizard, setShowWizard] = useState(false);
  const queryClient = useQueryClient();
  const [generationProgress, setGenerationProgress] = useState(0);
  const [progressMeta, setProgressMeta] = useState<{ start: number; duration: number } | null>(null);
  const [activeGenerationProjectId, setActiveGenerationProjectId] = useState<string | null>(null);
  const projectLabel = selectedProject?.name ?? 'Unknown project';

  const { data: personas, isLoading, isFetching } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await personasApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
    refetchInterval: (query) => {
      // Refetch every 5s if project exists but no personas yet (generation in progress)
      // Only refetch if we're actively generating for this project
      if (!selectedProject || activeGenerationProjectId !== selectedProject.id) {
        return false;
      }
      const data = query.state.data;
      return (!data || data.length === 0) ? 5000 : false;
    },
  });

  // Sync personas to global store
  useEffect(() => {
    if (personas) {
      setPersonas(personas);
    }
  }, [personas, setPersonas]);

  // Track previous personas length for toast notification
  const prevPersonasLength = useRef<number>(0);

  // Show toast when personas generation completes
  useEffect(() => {
    if (personas && personas.length > 0 && prevPersonasLength.current === 0) {
      toast.success(
        'Personas generated',
        `${projectLabel} • ${personas.length} personas ready`
      );
    }
    prevPersonasLength.current = personas?.length ?? 0;
  }, [personas, projectLabel]);

  const isAwaitingPersonas = !personas || personas.length === 0;
  const isCurrentProjectGenerating =
    activeGenerationProjectId !== null && activeGenerationProjectId === selectedProject?.id;

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

  useEffect(() => {
    if (!selectedProject) {
      setActiveGenerationProjectId(null);
      setGenerationProgress(0);
      setProgressMeta(null);
    }
  }, [selectedProject]);

  const generateMutation = useMutation({
    mutationFn: (payload: GeneratePersonasPayload) =>
      personasApi.generate(selectedProject!.id, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['personas', selectedProject?.id] });
      const modeLabel = variables.adversarial_mode ? 'Adversarial' : 'Standard';
      toast.info(
        'Generation started',
        `${projectLabel} • ${modeLabel} cohort queued (${variables.num_personas} personas).`
      );
    },
    onError: (error: Error) => {
      setGenerationProgress(0);
      setProgressMeta(null);
      setShowWizard(true);
      setActiveGenerationProjectId(null);
      toast.error('Generation failed', `${projectLabel} • ${error.message}`);
    },
  });

  const handleWizardSubmit = (config: PersonaGenerationConfig) => {
    if (!selectedProject) {
      return;
    }

    const payload = transformWizardConfigToPayload(config);
    setActiveGenerationProjectId(selectedProject.id);
    setShowWizard(false);
    setProgressMeta({ start: Date.now(), duration: estimateGenerationDuration(payload.num_personas) });
    setGenerationProgress(5);
    generateMutation.mutate(payload);
  };

  const isGenerating =
    isCurrentProjectGenerating &&
    (generateMutation.isPending ||
      (generateMutation.isSuccess && isAwaitingPersonas) ||
      ((isLoading || isFetching) && isAwaitingPersonas));

  useEffect(() => {
    if (!isGenerating) {
      if (generationProgress > 0) {
        setGenerationProgress(100);
        const timeout = setTimeout(() => {
          setGenerationProgress(0);
          setProgressMeta(null);
          setActiveGenerationProjectId(null);
        }, 800);
        return () => clearTimeout(timeout);
      }
      if (generationProgress === 0 && activeGenerationProjectId !== null) {
        setActiveGenerationProjectId(null);
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
  }, [isGenerating, progressMeta, generationProgress, activeGenerationProjectId, selectedProject?.id]);

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
        <SpinnerLogo className="w-8 h-8" />
      </div>
    );
  } else if (personas && personas.length > 0) {
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
          <PersonaList personas={personas} selectedPersona={selectedPersona} />
          <div className="overflow-y-auto px-6">
            <PersonaDetailsView persona={selectedPersona ?? null} />
          </div>
        </div>
      </div>
    );
  } else if (isGenerating) {
    content = (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <SpinnerLogo className="w-12 h-12 mb-3" />
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

  const showProgressBar =
    activeGenerationProjectId === selectedProject?.id && generationProgress > 0;
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
            <SpinnerLogo className="w-4 h-4" />
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
      <PersonaGenerationWizard
        open={showWizard}
        onOpenChange={setShowWizard}
        onGenerate={handleWizardSubmit}
      />
    </FloatingPanel>
  );
}
