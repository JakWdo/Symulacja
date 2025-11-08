import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Plus, Users, MessageSquare, Eye, Settings, Trash2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageHeader } from '@/components/layout/PageHeader';
import { focusGroupsApi, projectsApi } from '@/lib/api';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { toast } from '@/components/ui/toastStore';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { FocusGroup } from '@/types';
import type { TFunction } from 'i18next';

interface FocusGroupsProps {
  onCreateFocusGroup: () => void;
  onSelectFocusGroup: (focusGroup: FocusGroup) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

const getStatusBadge = (focusGroup: FocusGroup, t: TFunction) => {
  switch (focusGroup.status) {
    case 'completed':
      return <Badge className="bg-brand-muted text-brand dark:text-brand">{t('status.completed')}</Badge>;
    case 'running':
      return (
        <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400 flex items-center gap-1.5">
          <SpinnerLogo className="w-3.5 h-3.5" />
          {t('status.running')}
        </Badge>
      );
    case 'failed':
      return (
        <Badge className="bg-red-100 text-red-700 dark:bg-red-400/10 dark:text-red-400">
          {t('status.failed')}
        </Badge>
      );
    case 'pending':
      if ((focusGroup.persona_ids?.length || 0) === 0 || (focusGroup.questions?.length || 0) === 0) {
        return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">{t('status.draft')}</Badge>;
      }
      return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">{t('status.ready')}</Badge>;
    default:
      return null;
  }
};

export function FocusGroups({ onCreateFocusGroup, onSelectFocusGroup }: FocusGroupsProps) {
  const { t } = useTranslation('focusGroups');
  // Use Zustand selectors to prevent unnecessary re-renders
  const selectedProject = useAppStore(state => state.selectedProject);
  const setSelectedProject = useAppStore(state => state.setSelectedProject);
  const queryClient = useQueryClient();
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; focusGroup: FocusGroup | null }>({
    open: false,
    focusGroup: null,
  });

  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  const { data: focusGroups = [], isLoading } = useQuery({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await focusGroupsApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: (query) => {
      // Poll every 2s if any focus group is running
      const data = query.state.data as FocusGroup[] | undefined;
      const hasRunningFG = data?.some((fg) => fg.status === 'running');
      return hasRunningFG ? 2000 : false;
    },
    refetchIntervalInBackground: true,
  });

  const { mutateAsync: deleteFocusGroup, isPending: isDeleting } = useMutation({
    mutationFn: (focusGroupId: string) => focusGroupsApi.remove(focusGroupId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['focus-groups', selectedProject?.id] });
      toast.success(t('delete.success'), t('delete.successDescription'));
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : t('delete.unknownError');
      toast.error(t('delete.error'), message);
    },
  });

  const handleDelete = (focusGroup: FocusGroup) => {
    if (isDeleting) return;
    setDeleteDialog({ open: true, focusGroup });
  };

  const confirmDelete = async () => {
    if (deleteDialog.focusGroup) {
      await deleteFocusGroup(deleteDialog.focusGroup.id);
      setDeleteDialog({ open: false, focusGroup: null });
    }
  };

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
      {/* Header */}
      <PageHeader
        title={t('page.title')}
        subtitle={t('page.subtitle')}
        actions={
          <>
            <Select
              value={selectedProject?.id || ''}
              onValueChange={(value) => {
                const project = projects.find((p) => p.id === value);
                if (project) setSelectedProject(project);
              }}
            >
              <SelectTrigger className="bg-muted border-0 rounded-md px-3.5 py-2 h-9 hover:bg-muted/80 transition-colors w-56">
                <SelectValue
                  placeholder={t('page.selectProject')}
                  className="font-['Crimson_Text',_serif] text-[14px] text-foreground leading-5"
                />
              </SelectTrigger>
              <SelectContent className="bg-muted border-border">
                {projectsLoading ? (
                  <div className="flex items-center justify-center p-2">
                    <SpinnerLogo className="w-4 h-4" />
                  </div>
                ) : projects.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">{t('page.noProjectsFound')}</div>
                ) : (
                  projects.map((project) => (
                    <SelectItem
                      key={project.id}
                      value={project.id}
                      className="font-['Crimson_Text',_serif] text-[14px] text-foreground focus:bg-accent"
                    >
                      {project.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            <Button
              onClick={onCreateFocusGroup}
              className="bg-brand hover:bg-brand/90 text-brand-foreground"
              disabled={!selectedProject}
            >
              <Plus className="w-4 h-4 mr-2" />
              {t('page.createButton')}
            </Button>
          </>
        }
      />

      {!selectedProject ? (
        <Card className="bg-card border border-border">
          <CardContent className="py-12 text-center space-y-4">
            <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto" />
            <h3 className="text-lg text-card-foreground">{t('page.noProjectSelected')}</h3>
            <p className="text-sm text-muted-foreground">
              {t('page.selectProjectDescription')}
            </p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="flex items-center justify-center h-[400px]">
          <SpinnerLogo className="w-10 h-10" />
        </div>
      ) : focusGroups.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[400px] space-y-3">
          <MessageSquare className="w-12 h-12 text-muted-foreground" />
          <h2 className="text-lg font-medium text-foreground">{t('list.empty.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('list.empty.description')}</p>
          <Button
            className="bg-brand hover:bg-brand/90 text-brand-foreground mt-2"
            onClick={onCreateFocusGroup}
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('list.empty.action')}
          </Button>
        </div>
      ) : (
        <>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-card border border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{t('tabs.all')}</p>
                    <p className="text-2xl brand-orange">{focusGroups.length}</p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{t('tabs.allParticipants')}</p>
                    <p className="text-2xl brand-orange">
                      {focusGroups.reduce((sum, fg) => sum + (fg.persona_ids?.length || 0), 0)}
                    </p>
                  </div>
                  <Users className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Focus Groups List */}
          <div className="space-y-4">
            <h2 className="text-xl text-foreground">{t('list.title')}</h2>

            <div className="grid grid-cols-1 gap-4">
              {focusGroups.map((focusGroup) => (
            <Card
              key={focusGroup.id}
              className={`bg-card border hover:shadow-md transition-shadow shadow-sm ${focusGroup.status === 'running' ? 'border-brand/50 shadow-[0_0_0_1px_rgba(242,116,5,0.08)]' : 'border-border'}`}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-card-foreground">{focusGroup.name}</h3>
                          {getStatusBadge(focusGroup, t)}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {focusGroup.description || t('list.card.noDescription')}
                        </p>
                        <p className="text-xs text-muted-foreground mb-2">
                          {focusGroup.questions?.length || 0} {(focusGroup.questions?.length || 0) === 1 ? 'pytanie' : (focusGroup.questions?.length || 0) < 5 ? 'pytania' : 'pytań'} • {focusGroup.persona_ids?.length || 0} {(focusGroup.persona_ids?.length || 0) === 1 ? 'uczestnik' : (focusGroup.persona_ids?.length || 0) < 5 ? 'uczestników' : 'uczestników'}
                        </p>
                      </div>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={() => onSelectFocusGroup(focusGroup)}>
                            <Eye className="w-4 h-4 mr-2" />
                            {t('list.card.viewDetails')}
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDelete(focusGroup)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            {t('list.card.delete')}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Progress and Details */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{t('list.card.participants')}</span>
                          <span className="text-card-foreground">
                            {focusGroup.persona_ids?.length || 0} / {focusGroup.target_participants || 10}
                          </span>
                        </div>
                        <Progress
                          value={focusGroup.target_participants ? Math.min((focusGroup.persona_ids?.length || 0) / focusGroup.target_participants * 100, 100) : 0}
                          className="h-2"
                        />
                        <p className="text-xs text-muted-foreground">
                          {focusGroup.target_participants
                            ? `${Math.round(Math.min((focusGroup.persona_ids?.length || 0) / focusGroup.target_participants * 100, 100))}%`
                            : '0%'}
                        </p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">{t('list.card.topics')}</p>
                        <div className="flex flex-wrap gap-1">
                          {focusGroup.questions?.slice(0, 2).map((question, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              P{index + 1}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">{t('list.card.status')}</p>
                        <div className="text-xs text-card-foreground flex items-center gap-2">
                          {focusGroup.status === 'running' && <SpinnerLogo className="w-3 h-3" />}
                          <span>
                            {focusGroup.status === 'completed'
                              ? t('status.completed')
                              : focusGroup.status === 'running'
                              ? t('list.card.runningWithCount', { count: focusGroup.persona_ids?.length || 0 })
                              : focusGroup.status === 'pending' && (focusGroup.persona_ids?.length === 0 || focusGroup.questions?.length === 0)
                              ? t('status.draft')
                              : focusGroup.status === 'pending'
                              ? t('status.ready')
                              : t('status.failed')}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      <Button
                        size="sm"
                        onClick={() => onSelectFocusGroup(focusGroup)}
                        className="bg-brand hover:bg-brand/90 text-brand-foreground"
                      >
                        <Settings className="w-4 h-4 mr-2" />
                        {t('list.card.manage')}
                      </Button>
                      <p className="text-xs text-muted-foreground ml-auto">
                        {t('list.card.created', { date: new Date(focusGroup.created_at).toLocaleDateString() })}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
              ))}
            </div>
          </div>
        </>
      )}
      </div>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, focusGroup: null })}
        title={t('delete.dialogTitle', { name: deleteDialog.focusGroup?.name || '' })}
        description={t('delete.dialogDescription')}
        confirmText={t('delete.confirmText')}
        cancelText={t('delete.cancelText')}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
