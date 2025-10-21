import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Sparkles, Share2, Scale, Trash2, FileDown } from 'lucide-react';
import type { PersonaDetailsResponse } from '@/types';
import { DeletePersonaDialog } from './DeletePersonaDialog';

interface PersonaActionsRailProps {
  persona: PersonaDetailsResponse;
  onGenerateMessaging: () => void;
  onCompare: () => void;
  onExport: () => void;
  onDeleteSuccess: () => void;
}

export function PersonaActionsRail({
  persona,
  onGenerateMessaging,
  onCompare,
  onExport,
  onDeleteSuccess,
}: PersonaActionsRailProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  return (
    <aside className="hidden xl:flex xl:w-56 xl:flex-col xl:gap-3 xl:pl-6 border-l border-border/60">
      <div className="sticky top-24 space-y-3">
        <div className="space-y-2">
          <Button variant="secondary" className="w-full justify-start gap-2" onClick={onCompare}>
            <Scale className="h-4 w-4" />
            Porównaj
          </Button>
          <Button variant="secondary" className="w-full justify-start gap-2" onClick={onGenerateMessaging}>
            <Sparkles className="h-4 w-4" />
            Generuj messaging
          </Button>
          <Button variant="secondary" className="w-full justify-start gap-2" onClick={onExport}>
            <FileDown className="h-4 w-4" />
            Eksportuj
          </Button>
          <Button variant="secondary" className="w-full justify-start gap-2" onClick={() => window.open(`/personas/${persona.id}/share`, '_blank')}>
            <Share2 className="h-4 w-4" />
            Udostępnij
          </Button>
        </div>

        <Separator className="my-3" />

        <Button
          variant="destructive"
          className="w-full justify-start gap-2"
          onClick={() => setShowDeleteDialog(true)}
        >
          <Trash2 className="h-4 w-4" />
          Usuń personę
        </Button>
      </div>

      <DeletePersonaDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        persona={persona}
        onSuccess={onDeleteSuccess}
      />
    </aside>
  );
}
