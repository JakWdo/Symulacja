import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Eye, User, Lightbulb, HeartPulse } from 'lucide-react';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { usePersonaDetails } from '@/hooks/usePersonaDetails';
import { OverviewSection } from './OverviewSection';
import { ProfileSection } from './ProfileSection';
import { NeedsSection } from './NeedsSection';
import { PersonaReasoningPanel } from './PersonaReasoningPanel';

interface PersonaDetailsDrawerProps {
  personaId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * PersonaDetailsDrawer - pełny widok persony z nawigacją po sekcjach i szyną akcji.
 *
 * Sekcje: Przegląd, Profil, Customer Journey, Potrzeby/Bóle, Insights.
 * Prawa szyna: akcje (porównanie, messaging, eksport, usunięcie z undo) oraz dialogi pomocnicze.
 */
export function PersonaDetailsDrawer({
  personaId,
  isOpen,
  onClose,
}: PersonaDetailsDrawerProps) {
  const [activeSection, setActiveSection] = useState<string>('overview');
  const { data: persona, isLoading, error } = usePersonaDetails(personaId);

  const sectionOptions = useMemo(
    () => [
      { id: 'overview', label: 'Przegląd', icon: Eye },
      { id: 'profile', label: 'Profil', icon: User },
      { id: 'needs', label: 'Potrzeby i bóle', icon: HeartPulse },
      { id: 'insights', label: 'Insights', icon: Lightbulb },
    ],
    []
  );

  const renderSection = () => {
    if (!persona) return null;
    switch (activeSection) {
      case 'overview':
        return <OverviewSection persona={persona} />;
      case 'profile':
        return <ProfileSection persona={persona} />;
      case 'needs':
        return <NeedsSection data={persona.needs_and_pains} />;
      case 'insights':
        return <PersonaReasoningPanel persona={persona} />;
      default:
        return null;
    }
  };

  useEffect(() => {
    if (isOpen) {
      setActiveSection('overview');
    }
  }, [isOpen, personaId]);

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog open={isOpen} onOpenChange={onClose}>
          <DialogContent className="max-w-[90vw] w-full h-[90vh] p-0 overflow-hidden flex flex-col">
            {/* Header */}
            <DialogHeader className="p-6 border-b border-border shrink-0">
              {isLoading ? (
                <>
                  <DialogTitle className="sr-only">Ładowanie szczegółów persony</DialogTitle>
                  <DialogDescription className="sr-only">Proszę czekać, pobieranie danych...</DialogDescription>
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
                  <DialogTitle className="sr-only">Szczegóły persony</DialogTitle>
                  <DialogDescription className="sr-only">Brak danych do wyświetlenia</DialogDescription>
                </>
              )}
            </DialogHeader>

            {/* Content */}
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
              <div className="text-center py-12">
                <p className="text-destructive mb-4">
                  {error instanceof Error ? error.message : 'Wystąpił błąd'}
                </p>
                <Button variant="outline" onClick={onClose}>
                  Zamknij
                </Button>
              </div>
            ) : persona ? (
              <div className="flex flex-col gap-6 lg:flex-row">
                {/* Left navigation for desktop */}
                <nav className="hidden lg:flex lg:w-52 lg:flex-col lg:gap-2">
                  {sectionOptions.map((section) => {
                    const Icon = section.icon;
                    const isActive = activeSection === section.id;
                    return (
                      <Button
                        key={section.id}
                        variant={isActive ? 'secondary' : 'ghost'}
                        className="justify-start gap-2"
                        onClick={() => setActiveSection(section.id)}
                      >
                        <Icon className="w-4 h-4" />
                        {section.label}
                      </Button>
                    );
                  })}
                </nav>

                {/* Mobile select */}
                <div className="lg:hidden">
                  <Select value={activeSection} onValueChange={setActiveSection}>
                    <SelectTrigger className="w-full mb-4">
                      <SelectValue placeholder="Wybierz sekcję" />
                    </SelectTrigger>
                    <SelectContent>
                      {sectionOptions.map((section) => (
                        <SelectItem key={section.id} value={section.id}>
                          {section.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex-1 min-w-0 space-y-6">
                  {renderSection()}
                </div>
                </div>
              ) : null}
            </motion.div>
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  );
}
