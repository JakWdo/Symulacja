import { memo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, X } from 'lucide-react';
import { usePersonaDetails } from '@/hooks/usePersonaDetails';
import { RegenerateButton } from './RegenerateButton';
import { PersonTab } from './tabs/PersonTab';
import { SegmentTab } from './tabs/SegmentTab';
import type { NarrativeStatus } from '@/types';

interface PersonaDetailsModalProps {
  personaId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * PersonaDetailsModal - główny modal z narracjami persony
 *
 * Structure:
 * - DialogHeader: Persona name, age + RegenerateButton
 * - Tabs: "Osoba" | "Segment"
 * - DialogFooter: CTA buttons (optional)
 *
 * Responsive:
 * - Desktop: 80vw × 90vh (max-w-6xl)
 * - Tablet: 85vw
 * - Mobile: 100vw × 100vh (full-screen), sticky header/tabs/footer
 *
 * State management:
 * - React Query: usePersonaDetails hook
 * - Local state: activeTab
 *
 * Accessibility:
 * - ARIA labels (aria-labelledby, aria-describedby)
 * - Keyboard nav (Escape → close, Arrow keys → switch tabs)
 * - Focus management (auto-focus DialogTitle)
 */
export const PersonaDetailsModal = memo<PersonaDetailsModalProps>(
  ({ personaId, isOpen, onClose }) => {
    const [activeTab, setActiveTab] = useState<'person' | 'segment'>('person');
    const { data: persona, isLoading, error, refetch } = usePersonaDetails(personaId);

    const handleRetry = useCallback(() => {
      refetch();
    }, [refetch]);

    // Compute narratives status - handle offline/degraded properly
    const narrativesStatus: NarrativeStatus = isLoading
      ? 'loading'
      : !persona
      ? 'loading'
      : persona.narratives_status || 'ok';

    const showError = !!error && !isLoading;
    const showPersona = !!persona && !isLoading && !error;

    const titleText = showPersona
      ? `${persona.full_name || 'Nieznana persona'}, ${persona.age} lat`
      : showError
      ? 'Błąd'
      : 'Szczegóły persony';

    const descriptionText = showPersona
      ? `${persona.occupation || 'Zawód nieokreślony'} • ${persona.location || 'Lokalizacja nieznana'}`
      : showError
      ? 'Nie udało się załadować szczegółów persony'
      : 'Proszę czekać, pobieranie danych...';

    const titleClassName = showPersona
      ? 'text-xl font-semibold'
      : showError
      ? 'text-xl font-semibold text-destructive'
      : 'sr-only';

    const descriptionClassName = showPersona ? 'text-sm mt-1' : 'sr-only';

    return (
      <AnimatePresence>
        {isOpen && (
          <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent
              className="max-w-6xl w-[80vw] h-[90vh] md:w-[85vw] sm:w-full sm:h-full sm:max-w-full p-0 overflow-hidden flex flex-col"
              aria-labelledby="persona-modal-title"
              aria-describedby="persona-modal-description"
            >
              {/* Header - sticky on mobile */}
              <DialogHeader className="p-6 border-b border-border shrink-0 sm:sticky sm:top-0 sm:bg-background sm:z-10">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <DialogTitle id="persona-modal-title" className={titleClassName}>
                      {titleText}
                    </DialogTitle>
                    <DialogDescription
                      id="persona-modal-description"
                      className={descriptionClassName}
                    >
                      {descriptionText}
                    </DialogDescription>
                  </div>
                  {showPersona && <RegenerateButton personaId={personaId || ''} />}
                </div>
                {isLoading && (
                  <div className="space-y-2 mt-4">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-4 w-64" />
                  </div>
                )}
              </DialogHeader>

              {/* Content - scrollable */}
              <motion.div
                className="flex-1 overflow-y-auto p-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1, duration: 0.3 }}
              >
                {isLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-64 w-full" />
                    <Skeleton className="h-64 w-full" />
                  </div>
                ) : error ? (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Błąd ładowania danych</AlertTitle>
                    <AlertDescription>
                    {error instanceof Error
                      ? error.message
                      : 'Wystąpił nieoczekiwany błąd'}
                    </AlertDescription>
                    <Button
                      variant="outline"
                      onClick={handleRetry}
                      className="mt-4"
                    >
                      Spróbuj ponownie
                    </Button>
                  </Alert>
                ) : persona ? (
                  <Tabs
                    value={activeTab}
                    onValueChange={(value) =>
                      setActiveTab(value as 'person' | 'segment')
                    }
                    className="w-full"
                  >
                    {/* Tabs List - sticky on mobile */}
                    <TabsList className="w-full mb-6 bg-muted/40 p-1 rounded-lg">
                      <TabsTrigger
                        value="person"
                        className="flex-1 rounded-md data-[state=active]:bg-background data-[state=active]:shadow-sm transition-colors"
                      >
                        Osoba
                      </TabsTrigger>
                      <TabsTrigger
                        value="segment"
                        className="flex-1 rounded-md data-[state=active]:bg-background data-[state=active]:shadow-sm transition-colors"
                      >
                        Segment
                      </TabsTrigger>
                    </TabsList>

                    {/* Tab Content */}
                    <TabsContent value="person" className="mt-0">
                      <PersonTab
                        narratives={persona.narratives}
                        status={narrativesStatus}
                        onRetry={handleRetry}
                      />
                    </TabsContent>

                    <TabsContent value="segment" className="mt-0">
                      <SegmentTab
                        narratives={persona.narratives}
                        status={narrativesStatus}
                        onRetry={handleRetry}
                      />
                    </TabsContent>
                  </Tabs>
                ) : null}
              </motion.div>

              {/* Footer - sticky on mobile (optional CTA buttons) */}
              <DialogFooter className="p-6 border-t border-border shrink-0 sm:sticky sm:bottom-0 sm:bg-background sm:z-10">
                <Button variant="outline" onClick={onClose}>
                  <X className="w-4 h-4 mr-2" />
                  Zamknij
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>
    );
  }
);

PersonaDetailsModal.displayName = 'PersonaDetailsModal';
