import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Eye, User, Users, HeartPulse, Sparkles } from 'lucide-react';
import { usePersonaDetails } from '@/hooks/usePersonaDetails';
import { OverviewSection } from './OverviewSection';
import { ProfileSection } from './ProfileSection';
import { NeedsDashboard } from './NeedsDashboard';
import { PersonaReasoningPanel } from './PersonaReasoningPanel';

interface PersonaDetailsDrawerProps {
  personaId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * PersonaDetailsDrawer - pełny widok persony z nawigacją w formie tabów.
 *
 * Tabs:
 * - "Osoba" - Przegląd, Profil, Potrzeby i bóle (dashboard view)
 * - "Segment" - Wnioski o segmencie i dane kontekstowe
 */
export function PersonaDetailsDrawer({
  personaId,
  isOpen,
  onClose,
}: PersonaDetailsDrawerProps) {
  const { t } = useTranslation('personas');
  // Only fetch when drawer is actually open
  const { data: persona, isLoading, error } = usePersonaDetails(isOpen ? personaId : null);

  // Cleanup: close any nested dialogs when main drawer closes
  useEffect(() => {
    if (!isOpen) {
      // Allow nested dialogs to cleanup
      const timer = setTimeout(() => {
        if (typeof document !== 'undefined') {
          document.body.style.pointerEvents = '';
          document.body.style.overflow = '';
          document.body.style.removeProperty('padding-right');
          document.body.removeAttribute('data-scroll-locked');
          const inertElements = document.querySelectorAll('[inert]');
          inertElements.forEach((element) => {
            element.removeAttribute('inert');
          });
        }
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      {isOpen && (
        <DialogContent className="max-w-[90vw] w-full h-[90vh] p-0 overflow-hidden flex flex-col min-h-0">
            {/* Header */}
            <DialogHeader className="p-6 border-b border-border shrink-0">
              {isLoading ? (
                <>
                  <DialogTitle className="sr-only">{t('drawer.accessibility.loadingTitle')}</DialogTitle>
                  <DialogDescription className="sr-only">{t('drawer.accessibility.loadingDescription')}</DialogDescription>
                  <div className="space-y-2">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-4 w-64" />
                  </div>
                </>
              ) : error ? (
                <>
                  <DialogTitle className="text-destructive">Błąd</DialogTitle>
                  <DialogDescription>
                    Nie udało się załadować szczegółów persony
                  </DialogDescription>
                </>
              ) : persona ? (
                <>
                  <DialogTitle className="text-xl">
                    {persona.full_name || 'Nieznana persona'}, {persona.age} lat
                  </DialogTitle>
                  <DialogDescription className="text-sm">
                    {persona.occupation || 'Zawód nieokreślony'} •{' '}
                    {persona.location || 'Lokalizacja nieznana'}
                  </DialogDescription>
                </>
              ) : (
                <>
                  <DialogTitle className="sr-only">{t('drawer.accessibility.detailsTitle')}</DialogTitle>
                  <DialogDescription className="sr-only">{t('drawer.accessibility.noDataDescription')}</DialogDescription>
                </>
              )}
            </DialogHeader>

            {/* Content with Tabs */}
            {isLoading ? (
              <div className="flex-1 overflow-y-auto p-6">
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-64 w-full" />
                  <Skeleton className="h-64 w-full" />
                </div>
              </div>
            ) : error ? (
              <div className="flex-1 overflow-y-auto p-6">
                <div className="text-center py-12">
                  <p className="text-destructive mb-4">
                    {error instanceof Error ? error.message : 'Wystąpił błąd'}
                  </p>
                  <Button variant="outline" onClick={onClose}>
                    Zamknij
                  </Button>
                </div>
              </div>
            ) : persona ? (
              <div className="flex-1 flex flex-col min-h-0">
                <Tabs defaultValue="osoba" className="flex-1 flex flex-col min-h-0">
                  <div className="px-6 pt-4 pb-2 border-b border-border shrink-0 bg-muted/30">
                    <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
                      <TabsTrigger value="osoba" className="gap-2">
                        <User className="w-4 h-4" />
                        Osoba
                      </TabsTrigger>
                      <TabsTrigger value="segment" className="gap-2">
                        <Users className="w-4 h-4" />
                        Segment
                      </TabsTrigger>
                    </TabsList>
                  </div>

                  <TabsContent value="osoba" className="flex-1 overflow-y-auto p-6 space-y-8 mt-0 min-h-0">
                    <div className="space-y-8">
                      {/* Przegląd Section */}
                      <section id="przeglad">
                        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                          <Eye className="w-5 h-5 text-primary" />
                          Przegląd
                        </h2>
                        <OverviewSection persona={persona} />
                      </section>

                      {/* Profil Section */}
                      <section id="profil">
                        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                          <User className="w-5 h-5 text-primary" />
                          Profil
                        </h2>
                        <ProfileSection persona={persona} />
                      </section>

                      {/* Potrzeby i bóle Section (Dashboard) */}
                      <section id="potrzeby-i-bole">
                        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                          <HeartPulse className="w-5 h-5 text-primary" />
                          Potrzeby i bóle
                        </h2>
                        <NeedsDashboard data={persona.needs_and_pains} />
                      </section>
                    </div>
                  </TabsContent>

                  <TabsContent value="segment" className="flex-1 overflow-y-auto p-6 space-y-8 mt-0 min-h-0">
                    <div className="space-y-8">
                      {/* Segment context section */}
                      <section id="kontekst-rag">
                        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-primary" />
                          Segment społeczny i wnioski
                        </h2>
                        <PersonaReasoningPanel persona={persona} />
                      </section>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            ) : null}
        </DialogContent>
      )}
    </Dialog>
  );
}
