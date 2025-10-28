import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { useDeleteProject } from '@/hooks/useDeleteProject';
import { projectsApi } from '@/lib/api';
import type { Project } from '@/types';
import { AlertCircle } from 'lucide-react';
import { Logo } from '@/components/ui/logo';

interface DeleteProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: Project | null;
  onSuccess?: () => void;
}

/**
 * Modal potwierdzenia usunięcia projektu z kaskadowym usuwaniem
 *
 * Najpierw pobiera informacje o wpływie usunięcia (ile person, grup, ankiet zostanie usuniętych)
 * Wyświetla ostrzeżenie o kaskadowym usunięciu z liczbami
 *
 * Reasons:
 * - duplicate - Duplikat (projekt już istnieje)
 * - outdated - Nieaktualny (dane przestarzałe)
 * - test_data - Dane testowe
 * - other - Inny powód (wymaga reason_detail)
 */
export function DeleteProjectDialog({
  open,
  onOpenChange,
  project,
  onSuccess,
}: DeleteProjectDialogProps) {
  const [reason, setReason] = useState<string>('');
  const [reasonDetail, setReasonDetail] = useState<string>('');
  const deleteMutation = useDeleteProject();

  // Fetch delete impact when dialog opens
  const { data: deleteImpact, isLoading: isLoadingImpact } = useQuery({
    queryKey: ['projects', project?.id, 'delete-impact'],
    queryFn: () => projectsApi.getDeleteImpact(project!.id),
    enabled: open && !!project,
  });

  // Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setReason('');
      setReasonDetail('');
    }
  }, [open]);

  const handleDelete = async () => {
    if (!project || !reason) return;

    // Validate "other" reason requires detail
    if (reason === 'other' && !reasonDetail.trim()) {
      return;
    }

    deleteMutation.mutate(
      {
        projectId: project.id,
        reason,
        reasonDetail: reason === 'other' ? reasonDetail : undefined,
      },
      {
        onSuccess: () => {
          onOpenChange(false);
          if (onSuccess) onSuccess();
        },
      }
    );
  };

  const isDeleteDisabled =
    !reason ||
    (reason === 'other' && !reasonDetail.trim()) ||
    deleteMutation.isPending ||
    isLoadingImpact;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle>Usuń projekt?</AlertDialogTitle>
          <AlertDialogDescription>
            Zamierzasz usunąć projekt <strong>{project?.name || 'Nieznany'}</strong>.
            Ta operacja jest odwracalna w ciągu 7 dni.
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* Cascade Warning */}
        {isLoadingImpact ? (
          <div className="flex items-center justify-center py-6">
            <Logo className="w-6 h-6" spinning />
            <span className="ml-2 text-sm text-muted-foreground">
              Sprawdzanie wpływu usunięcia...
            </span>
          </div>
        ) : deleteImpact && (
          <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="space-y-2 flex-1">
                <p className="font-medium text-destructive">
                  Ostrzeżenie o kaskadowym usunięciu
                </p>
                <p className="text-sm text-muted-foreground">
                  Usunięcie tego projektu spowoduje również usunięcie:
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                  {deleteImpact.personas_count > 0 && (
                    <li>
                      <strong>{deleteImpact.personas_count}</strong> person
                    </li>
                  )}
                  {deleteImpact.focus_groups_count > 0 && (
                    <li>
                      <strong>{deleteImpact.focus_groups_count}</strong> grup fokusowych
                    </li>
                  )}
                  {deleteImpact.surveys_count > 0 && (
                    <li>
                      <strong>{deleteImpact.surveys_count}</strong> ankiet
                    </li>
                  )}
                  {deleteImpact.total_responses_count > 0 && (
                    <li>
                      <strong>{deleteImpact.total_responses_count}</strong> odpowiedzi
                    </li>
                  )}
                </ul>
                <p className="text-xs text-muted-foreground mt-2">
                  Wszystkie encje mogą zostać przywrócone w ciągu 7 dni poprzez cofnięcie usunięcia projektu.
                </p>
              </div>
            </div>
          </div>
        )}

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
                <SelectItem value="outdated">Nieaktualny</SelectItem>
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
          <AlertDialogCancel disabled={deleteMutation.isPending}>
            Anuluj
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleteDisabled}
            className="bg-destructive hover:bg-destructive/90"
          >
            {deleteMutation.isPending ? (
              <>
                <Logo className="w-4 h-4 mr-2" spinning />
                Usuwanie...
              </>
            ) : (
              'Usuń projekt'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
