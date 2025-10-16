import React, { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useDeletePersona } from '@/hooks/useDeletePersona';
import type { PersonaDetailsResponse } from '@/types';

interface DeletePersonaDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  persona: PersonaDetailsResponse | null;
  onSuccess?: () => void;
}

/**
 * Modal potwierdzenia usunięcia persony z dropdown reason + textarea
 *
 * Reasons:
 * - duplicate - Duplikat (persona już istnieje)
 * - outdated - Nieaktualna (dane przestarzałe)
 * - test_data - Dane testowe
 * - other - Inny powód (wymaga reason_detail)
 */
export function DeletePersonaDialog({
  open,
  onOpenChange,
  persona,
  onSuccess,
}: DeletePersonaDialogProps) {
  const [reason, setReason] = useState<string>('');
  const [reasonDetail, setReasonDetail] = useState<string>('');
  const deleteMutation = useDeletePersona();

  const handleDelete = async () => {
    if (!persona || !reason) return;

    // Validate "other" reason requires detail
    if (reason === 'other' && !reasonDetail.trim()) {
      return;
    }

    deleteMutation.mutate(
      {
        personaId: persona.id,
        reason,
        reasonDetail: reason === 'other' ? reasonDetail : undefined,
      },
      {
        onSuccess: () => {
          onOpenChange(false);
          setReason('');
          setReasonDetail('');
          if (onSuccess) onSuccess();
        },
      }
    );
  };

  const isDeleteDisabled =
    !reason || (reason === 'other' && !reasonDetail.trim()) || deleteMutation.isPending;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Usuń personę?</AlertDialogTitle>
          <AlertDialogDescription>
            Zamierzasz usunąć personę <strong>{persona?.full_name || 'Nieznana'}</strong>.
            Ta operacja jest nieodwracalna i zostanie zapisana w logach audytu.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4 py-4">
          {/* Reason Dropdown */}
          <div className="space-y-2">
            <Label htmlFor="delete-reason">Powód usunięcia *</Label>
            <Select value={reason} onValueChange={setReason}>
              <SelectTrigger id="delete-reason">
                <SelectValue placeholder="Wybierz powód..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="duplicate">Duplikat</SelectItem>
                <SelectItem value="outdated">Nieaktualna</SelectItem>
                <SelectItem value="test_data">Dane testowe</SelectItem>
                <SelectItem value="other">Inny powód</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Reason Detail Textarea (visible when "other" selected) */}
          {reason === 'other' && (
            <div className="space-y-2">
              <Label htmlFor="reason-detail">Szczegóły *</Label>
              <Textarea
                id="reason-detail"
                placeholder="Opisz powód usunięcia..."
                value={reasonDetail}
                onChange={(e) => setReasonDetail(e.target.value)}
                rows={3}
              />
            </div>
          )}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel
            onClick={() => {
              setReason('');
              setReasonDetail('');
            }}
            disabled={deleteMutation.isPending}
          >
            Anuluj
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleteDisabled}
            className="bg-destructive hover:bg-destructive/90"
          >
            {deleteMutation.isPending ? 'Usuwanie...' : 'Usuń'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
