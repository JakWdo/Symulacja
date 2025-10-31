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
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation('projects');
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
          <AlertDialogTitle>{t('delete.dialogTitle')}</AlertDialogTitle>
          <AlertDialogDescription dangerouslySetInnerHTML={{ __html: t('delete.confirmation', { name: project?.name || t('delete.unknown') }) }} />
          <AlertDialogDescription>
            {t('delete.recoverable')}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* Cascade Warning */}
        {isLoadingImpact ? (
          <div className="flex items-center justify-center py-6">
            <Logo className="w-6 h-6" spinning />
            <span className="ml-2 text-sm text-muted-foreground">
              {t('delete.checking')}
            </span>
          </div>
        ) : deleteImpact && (
          <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="space-y-2 flex-1">
                <p className="font-medium text-destructive">
                  {t('delete.cascadeWarning')}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t('delete.cascadeMessage')}
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                  {deleteImpact.personas_count > 0 && (
                    <li dangerouslySetInnerHTML={{ __html: t('delete.cascadeItems.personas', { count: deleteImpact.personas_count }) }} />
                  )}
                  {deleteImpact.focus_groups_count > 0 && (
                    <li dangerouslySetInnerHTML={{ __html: t('delete.cascadeItems.focusGroups', { count: deleteImpact.focus_groups_count }) }} />
                  )}
                  {deleteImpact.surveys_count > 0 && (
                    <li dangerouslySetInnerHTML={{ __html: t('delete.cascadeItems.surveys', { count: deleteImpact.surveys_count }) }} />
                  )}
                  {deleteImpact.total_responses_count > 0 && (
                    <li dangerouslySetInnerHTML={{ __html: t('delete.cascadeItems.responses', { count: deleteImpact.total_responses_count }) }} />
                  )}
                </ul>
                <p className="text-xs text-muted-foreground mt-2">
                  {t('delete.recoveryNote')}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4 py-4">
          {/* Reason Dropdown */}
          <div className="space-y-2">
            <Label htmlFor="delete-reason">{t('delete.reasons.label')}</Label>
            <Select value={reason} onValueChange={setReason}>
              <SelectTrigger id="delete-reason">
                <SelectValue placeholder={t('delete.reasons.placeholder')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="duplicate">{t('delete.reasons.duplicate')}</SelectItem>
                <SelectItem value="outdated">{t('delete.reasons.outdated')}</SelectItem>
                <SelectItem value="test_data">{t('delete.reasons.testData')}</SelectItem>
                <SelectItem value="other">{t('delete.reasons.other')}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Reason Detail Textarea (visible when "other" selected) */}
          {reason === 'other' && (
            <div className="space-y-2">
              <Label htmlFor="reason-detail">{t('delete.reasonDetail.label')}</Label>
              <Textarea
                id="reason-detail"
                placeholder={t('delete.reasonDetail.placeholder')}
                value={reasonDetail}
                onChange={(e) => setReasonDetail(e.target.value)}
                rows={3}
              />
            </div>
          )}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteMutation.isPending}>
            {t('delete.cancelButton')}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleteDisabled}
            className="bg-destructive hover:bg-destructive/90"
          >
            {deleteMutation.isPending ? (
              <>
                <Logo className="w-4 h-4 mr-2" spinning />
                {t('delete.deletingButton')}
              </>
            ) : (
              t('delete.deleteButton')
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
