import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatePresence } from 'framer-motion';
import { FloatingPanel } from '@/components/ui/floating-panel';
import { focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { MessageSquare, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { FocusGroup } from '@/types';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { FocusGroupCard } from '@/components/focus-group/FocusGroupCard';
import { FocusGroupForm } from '@/components/focus-group/FocusGroupForm';

export function FocusGroupPanel() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const activePanel = useAppStore(state => state.activePanel);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const selectedProject = useAppStore(state => state.selectedProject);
  const selectedFocusGroup = useAppStore(state => state.selectedFocusGroup);
  const personas = useAppStore(state => state.personas);
  const focusGroups = useAppStore(state => state.focusGroups);
  const setFocusGroups = useAppStore(state => state.setFocusGroups);
  const setSelectedFocusGroup = useAppStore(state => state.setSelectedFocusGroup);
  const [formState, setFormState] = useState<
    | { mode: 'create' }
    | { mode: 'edit'; focusGroup: FocusGroup }
    | null
  >(null);

  const { isLoading, isError, error } = useQuery<FocusGroup[]>({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      const data = await focusGroupsApi.getByProject(selectedProject!.id);
      setFocusGroups(data);
      return data;
    },
    enabled: !!selectedProject,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: (query) =>
      query.state.data?.some((group) => group.status === 'running') ? 2000 : false,
    refetchIntervalInBackground: true,
  });

  useEffect(() => {
    if (!selectedProject) {
      setFocusGroups([]);
    }
  }, [selectedProject, setFocusGroups]);

  const handleFormSaved = (group: FocusGroup) => {
    setFormState(null);
    setSelectedFocusGroup(group);
  };

  return (
    <FloatingPanel
      isOpen={activePanel === 'focus-groups'}
      onClose={() => setActivePanel(null)}
      title={`Grupy fokusowe${focusGroups.length ? ` (${focusGroups.length})` : ''}`}
      panelKey="focus-groups"
      size="lg"
    >
      {!selectedProject ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center mb-6">
            <MessageSquare className="w-10 h-10 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Nie wybrano projektu</h3>
          <p className="text-sm text-slate-500">Wybierz projekt, aby zobaczyć grupy fokusowe</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <Button
              onClick={() => setFormState({ mode: 'create' })}
              className="w-full bg-gradient-to-r from-primary-500 to-accent-500 hover:from-primary-600 hover:to-accent-600"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Utwórz nową grupę fokusową
            </Button>
            {(personas?.length ?? 0) < 2 && (
              <p className="text-xs text-amber-600 mt-2">
                Dostępne mniej niż dwie persony. Możesz utworzyć szkic teraz i uruchomić, gdy persony będą gotowe.
              </p>
            )}
          </div>

          {formState ? (
            <FocusGroupForm
              mode={formState.mode}
              focusGroup={formState.mode === 'edit' ? formState.focusGroup : undefined}
              onCancel={() => setFormState(null)}
              onSaved={handleFormSaved}
            />
          ) : null}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <SpinnerLogo className="w-8 h-8 mb-4" />
              <p className="text-sm text-slate-600">Ładowanie grup fokusowych...</p>
            </div>
          ) : isError ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-sm text-red-600">{error?.message || 'Nie udało się załadować grup fokusowych'}</p>
            </div>
          ) : focusGroups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-primary-600" />
              </div>
              <p className="text-sm text-slate-500">Brak grup fokusowych</p>
              <p className="text-xs text-slate-400 mt-1">Utwórz pierwszą powyżej</p>
            </div>
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {focusGroups.map((fg, idx) => (
                  <FocusGroupCard
                    key={fg.id}
                    focusGroup={fg}
                    isSelected={selectedFocusGroup?.id === fg.id}
                    index={idx}
                    onEdit={() => setFormState({ mode: 'edit', focusGroup: fg })}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      )}
    </FloatingPanel>
  );
}
