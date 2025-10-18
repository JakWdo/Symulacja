import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { usePersonaDetails } from '@/hooks/usePersonaDetails';
import { OverviewSection } from './OverviewSection';
import { ProfileSection } from './ProfileSection';
import { SegmentSection } from './SegmentSection';
import { NeedsSection } from './NeedsSection';
import { MethodologySection } from './MethodologySection';
import { DataFreshnessBadge } from './DataFreshnessBadge';

interface PersonaDetailsDrawerProps {
  personaId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * PersonaDetailsDrawer - Floating modal z pełnym widokiem persony.
 *
 * Redesign (2025-10-18):
 * - Floating modal (max-width 70%, centrowany)
 * - Horizontal tabs navigation (Overview, Profile, Segment, Needs, Metodologia)
 * - Brak akcji (read-only modal)
 * - Data freshness badge w header
 * - Mobile responsive (tabs → select, full-screen)
 */
export function PersonaDetailsDrawer({
  personaId,
  isOpen,
  onClose,
}: PersonaDetailsDrawerProps) {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const { data: persona, isLoading, error } = usePersonaDetails(personaId);

  // Reset tab when modal opens
  useEffect(() => {
    if (isOpen) {
      setActiveTab('overview');
    }
  }, [isOpen, personaId]);

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog open={isOpen} onOpenChange={onClose}>
          <DialogContent className="max-w-[70vw] sm:max-w-full sm:h-full sm:max-h-screen h-[85vh] p-0 overflow-hidden flex flex-col">
            {/* Sticky Header */}
            <DialogHeader className="sticky top-0 bg-background z-10 p-6 border-b border-border shrink-0">
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
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <DialogTitle className="text-xl">
                        {persona.occupation || 'Osoba'}, {persona.age} lat - {persona.location || 'Polska'}
                      </DialogTitle>
                      <DialogDescription className="text-sm mt-1">
                        {persona.segment_name || 'Segment nieokreślony'}
                      </DialogDescription>
                    </div>
                    <DataFreshnessBadge timestamp={persona.data_freshness || persona.updated_at || persona.created_at} />
                  </div>
                </>
              ) : (
                <>
                  <DialogTitle className="sr-only">Szczegóły persony</DialogTitle>
                  <DialogDescription className="sr-only">Brak danych do wyświetlenia</DialogDescription>
                </>
              )}
            </DialogHeader>

            {/* Tabs Navigation & Content */}
            {isLoading ? (
              <div className="flex-1 overflow-y-auto p-6">
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-64 w-full" />
                  <Skeleton className="h-64 w-full" />
                </div>
              </div>
            ) : error ? (
              <div className="flex-1 flex items-center justify-center p-6">
                <div className="text-center">
                  <p className="text-destructive mb-4">
                    {error instanceof Error ? error.message : 'Wystąpił błąd podczas ładowania danych'}
                  </p>
                </div>
              </div>
            ) : persona ? (
              <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
                {/* Mobile Select (visible on sm screens) */}
                <div className="sm:hidden px-6 pt-4">
                  <Select value={activeTab} onValueChange={setActiveTab}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="overview">Overview</SelectItem>
                      <SelectItem value="profile">Profile</SelectItem>
                      <SelectItem value="segment">Segment</SelectItem>
                      <SelectItem value="needs">Potrzeby</SelectItem>
                      <SelectItem value="methodology">Metodologia</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Desktop Horizontal Tabs */}
                <TabsList className="hidden sm:flex w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
                  <TabsTrigger value="overview" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary">
                    Overview
                  </TabsTrigger>
                  <TabsTrigger value="profile" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary">
                    Profile
                  </TabsTrigger>
                  <TabsTrigger value="segment" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary">
                    Segment
                  </TabsTrigger>
                  <TabsTrigger value="needs" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary">
                    Potrzeby
                  </TabsTrigger>
                  <TabsTrigger value="methodology" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary">
                    Metodologia
                  </TabsTrigger>
                </TabsList>

                {/* Tab Content (scrollable) */}
                <div className="flex-1 overflow-y-auto">
                  <motion.div
                    className="p-6"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2 }}
                  >
                    <TabsContent value="overview" className="mt-0">
                      <OverviewSection persona={persona} />
                    </TabsContent>

                    <TabsContent value="profile" className="mt-0">
                      <ProfileSection persona={persona} />
                    </TabsContent>

                    <TabsContent value="segment" className="mt-0">
                      <SegmentSection persona={persona} />
                    </TabsContent>

                    <TabsContent value="needs" className="mt-0">
                      <NeedsSection data={persona.needs_and_pains} />
                    </TabsContent>

                    <TabsContent value="methodology" className="mt-0">
                      <MethodologySection persona={persona} />
                    </TabsContent>
                  </motion.div>
                </div>
              </Tabs>
            ) : null}
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  );
}
