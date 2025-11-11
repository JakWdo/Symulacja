import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart3, Plus } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageHeader } from '@/components/layout/PageHeader';
import { surveysApi, projectsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { Survey } from '@/types';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { useState } from 'react';
import { toast } from '@/components/ui/toastStore';
import { useTranslation } from 'react-i18next';
import { SurveysSkeleton } from '@/components/surveys/SurveysSkeleton';
import { SurveysList } from '@/components/surveys/SurveysList';

interface SurveysProps {
  onCreateSurvey: () => void;
  onSelectSurvey: (survey: Survey) => void;
}

export function Surveys({ onCreateSurvey, onSelectSurvey }: SurveysProps) {
  const { t } = useTranslation('surveys');
  const { selectedProject, setSelectedProject } = useAppStore();
  const queryClient = useQueryClient();
  const [launchDialog, setLaunchDialog] = useState<{ open: boolean; survey: Survey | null }>({
    open: false,
    survey: null,
  });
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; survey: Survey | null }>({
    open: false,
    survey: null,
  });

  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  const { data: surveys = [], isLoading } = useQuery({
    queryKey: ['surveys', selectedProject?.id],
    queryFn: () => surveysApi.getByProject(selectedProject!.id),
    enabled: !!selectedProject,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasRunningSurvey = data?.some((s: Survey) => s.status === 'running');
      return hasRunningSurvey ? 3000 : false;
    },
    refetchIntervalInBackground: true,
  });

  const runMutation = useMutation({
    mutationFn: surveysApi.run,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['surveys', selectedProject?.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: surveysApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['surveys', selectedProject?.id] });
    },
  });

  const handleRunSurvey = (survey: Survey) => {
    setLaunchDialog({ open: true, survey });
  };

  const confirmLaunch = () => {
    const surveyToLaunch = launchDialog.survey;
    if (!surveyToLaunch) {
      return;
    }

    runMutation.mutate(surveyToLaunch.id, {
      onSuccess: () => {
        toast.success(t('launch.success'), `${surveyToLaunch.title} · ${selectedProject?.name || t('launchDialog.unknownProject')}`);
      },
      onError: (error) => {
        const message = error instanceof Error ? error.message : t('launch.unknownError');
        toast.error(t('launch.error'), `${surveyToLaunch.title} · ${selectedProject?.name || t('launchDialog.unknownProject')} • ${message}`);
      },
    });

    setLaunchDialog({ open: false, survey: null });
  };

  const handleDeleteSurvey = (survey: Survey) => {
    setDeleteDialog({ open: true, survey });
  };

  const confirmDelete = () => {
    const surveyToDelete = deleteDialog.survey;
    if (!surveyToDelete) {
      return;
    }

    deleteMutation.mutate(surveyToDelete.id, {
      onSuccess: () => {
        toast.success(t('delete.success'), `${surveyToDelete.title} · ${selectedProject?.name || t('deleteDialog.unknownProject')}`);
      },
      onError: (error) => {
        const message = error instanceof Error ? error.message : t('delete.unknownError');
        toast.error(t('delete.error'), `${surveyToDelete.title} · ${selectedProject?.name || t('deleteDialog.unknownProject')} • ${message}`);
      },
    });

    setDeleteDialog({ open: false, survey: null });
  };

  let bodyContent;

  if (!selectedProject) {
    bodyContent = (
      <Card className="bg-card border border-border">
        <CardContent className="py-12 text-center space-y-4">
          <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto" />
          <h3 className="text-lg text-card-foreground">{t('page.noProjectSelected')}</h3>
          <p className="text-sm text-muted-foreground">
            {t('page.selectProjectDescription')}
          </p>
        </CardContent>
      </Card>
    );
  } else if (isLoading) {
    bodyContent = <SurveysSkeleton />;
  } else {
    bodyContent = (
      <SurveysList
        surveys={surveys}
        onCreateSurvey={onCreateSurvey}
        onSelectSurvey={onSelectSurvey}
        onRunSurvey={handleRunSurvey}
        onDeleteSurvey={handleDeleteSurvey}
        isRunning={runMutation.isPending}
      />
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
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
                onClick={onCreateSurvey}
                className="bg-brand hover:bg-brand/90 text-brand-foreground"
                disabled={!selectedProject}
              >
                <Plus className="w-4 h-4 mr-2" />
                {t('page.createButton')}
              </Button>
            </>
          }
        />

        {bodyContent}
      </div>

      <ConfirmDialog
        open={launchDialog.open}
        onOpenChange={(open) => setLaunchDialog({ open, survey: null })}
        title={t('launchDialog.title', { title: launchDialog.survey?.title || '' })}
        description={t('launchDialog.description', { count: launchDialog.survey?.target_responses || 0 })}
        confirmText={t('launchDialog.confirmButton')}
        cancelText={t('launchDialog.cancelText')}
        onConfirm={confirmLaunch}
      />

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, survey: null })}
        title={t('deleteDialog.title', { title: deleteDialog.survey?.title || '' })}
        description={t('deleteDialog.description')}
        confirmText={t('deleteDialog.confirmButton')}
        cancelText={t('deleteDialog.cancelText')}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
