import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Plus, Users, Eye, BarChart3, Play, Trash2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
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

  // Fetch surveys for selected project
  const { data: surveys = [], isLoading } = useQuery({
    queryKey: ['surveys', selectedProject?.id],
    queryFn: () => surveysApi.getByProject(selectedProject!.id),
    enabled: !!selectedProject,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
    refetchOnReconnect: 'always',
    refetchInterval: (query) => {
      // Poll every 3s if any survey is running
      const data = query.state.data;
      const hasRunningSurvey = data?.some((s: Survey) => s.status === 'running');
      return hasRunningSurvey ? 3000 : false;
    },
    refetchIntervalInBackground: true,
  });

  // Run survey mutation
  const runMutation = useMutation({
    mutationFn: surveysApi.run,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['surveys', selectedProject?.id] });
    },
  });

  // Delete survey mutation
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

  const getStatusBadge = (status: Survey['status']) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-[#F27405]/10 text-[#F27405] dark:text-[#F27405]">{t('status.completed')}</Badge>;
      case 'running':
        return (
          <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400 flex items-center gap-1.5">
            <SpinnerLogo className="w-3.5 h-3.5" />
            {t('status.running')}
          </Badge>
        );
      case 'draft':
        return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">{t('status.draft')}</Badge>;
      case 'failed':
        return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">{t('status.failed')}</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const statsSection = (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('tabs.all')}</p>
              <p className="text-2xl font-bold text-[#F27405]">{surveys.length}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-[#F27405]" />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('tabs.allResponses')}</p>
              <p className="text-2xl font-bold text-[#F27405]">
                {surveys.reduce((sum, survey) => sum + survey.actual_responses, 0).toLocaleString()}
              </p>
            </div>
            <Users className="w-8 h-8 text-[#F27405]" />
          </div>
        </CardContent>
      </Card>
    </div>
  );

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
    bodyContent = (
      <>
        {statsSection}
        <div className="space-y-4">
          <h2 className="text-xl text-foreground">{t('list.title')}</h2>
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <p className="text-muted-foreground">{t('list.loading')}</p>
            </CardContent>
          </Card>
        </div>
      </>
    );
  } else if (surveys.length === 0) {
    bodyContent = (
      <>
        {statsSection}
        <div className="space-y-4">
          <h2 className="text-xl text-foreground">{t('list.title')}</h2>
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">{t('list.empty.title')}</h3>
              <p className="text-muted-foreground mb-4">
                {t('list.empty.description')}
              </p>
              <Button
                onClick={onCreateSurvey}
                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                {t('list.empty.action')}
              </Button>
            </CardContent>
          </Card>
        </div>
      </>
    );
  } else {
    bodyContent = (
      <>
        {statsSection}
        <div className="space-y-4">
          <h2 className="text-xl text-foreground">{t('list.title')}</h2>
          <div className="grid grid-cols-1 gap-4">
            {surveys.map((survey) => {
              const progress = survey.target_responses > 0
                ? (survey.actual_responses / survey.target_responses) * 100
                : 0;

              return (
                <Card
                  key={survey.id}
                  className={`bg-card border hover:shadow-md transition-shadow shadow-sm ${survey.status === 'running' ? 'border-[#F27405]/50 shadow-[0_0_0_1px_rgba(242,116,5,0.08)]' : 'border-border'}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-4">
                        {/* Header */}
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="text-lg text-card-foreground">{survey.title}</h3>
                              {getStatusBadge(survey.status)}
                            </div>
                            {survey.description && (
                              <p className="text-sm text-muted-foreground mb-2">
                                {survey.description}
                              </p>
                            )}
                            <p className="text-xs text-muted-foreground">
                              {survey.questions.length} {survey.questions.length === 1 ? 'pytanie' : survey.questions.length < 5 ? 'pytania' : 'pytań'}
                            </p>
                          </div>

                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent>
                              {survey.status === 'completed' && (
                                <DropdownMenuItem onClick={() => onSelectSurvey(survey)}>
                                  <Eye className="w-4 h-4 mr-2" />
                                  {t('list.card.viewResults')}
                                </DropdownMenuItem>
                              )}
                              {survey.status === 'draft' && (
                                <DropdownMenuItem onClick={() => handleRunSurvey(survey)}>
                                  <Play className="w-4 h-4 mr-2" />
                                  {t('list.card.launch')}
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem
                                onClick={() => handleDeleteSurvey(survey)}
                                className="text-red-600 dark:text-red-400"
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                {t('list.card.delete')}
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>

                        {/* Progress and Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">{t('list.card.progress')}</span>
                              <span className="text-card-foreground">
                                {survey.actual_responses.toLocaleString()} / {survey.target_responses.toLocaleString()}
                              </span>
                            </div>
                            <Progress value={progress} className="h-2" />
                            <p className="text-xs text-muted-foreground">
                              {t('list.card.completed', { progress: Math.round(progress) })}
                            </p>
                          </div>

                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">{t('list.card.executionTime')}</p>
                            <div className="space-y-1">
                              {survey.total_execution_time_ms ? (
                                <>
                                  <p className="text-xs text-card-foreground">
                                    {t('list.card.total')}: {(survey.total_execution_time_ms / 1000).toFixed(1)}s
                                  </p>
                                  {survey.avg_response_time_ms && (
                                    <p className="text-xs text-card-foreground">
                                      {t('list.card.average')}: {(survey.avg_response_time_ms / 1000).toFixed(2)}s {t('list.card.perResponse')}
                                    </p>
                                  )}
                                </>
                              ) : (
                                <p className="text-xs text-card-foreground">
                                  {survey.status === 'running'
                                    ? t('list.card.running')
                                    : survey.status === 'draft'
                                    ? t('list.card.notStarted')
                                    : t('list.card.na')}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Actions */}
                        {survey.status === 'completed' ? (
                          <div className="flex items-center gap-2 pt-2">
                            <Button
                              size="sm"
                              onClick={() => onSelectSurvey(survey)}
                              className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              {t('list.card.viewResults')}
                            </Button>
                            <p className="text-xs text-muted-foreground ml-auto">
                              {t('list.card.created', { date: new Date(survey.created_at).toLocaleDateString() })}
                            </p>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 pt-2">
                            {survey.status === 'draft' && (
                              <Button
                                size="sm"
                                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                                onClick={() => handleRunSurvey(survey)}
                                disabled={runMutation.isPending}
                              >
                                <Play className="w-4 h-4 mr-2" />
                                {t('list.card.launch')}
                              </Button>
                            )}
                            <p className="text-xs text-muted-foreground ml-auto">
                              {t('list.card.created', { date: new Date(survey.created_at).toLocaleDateString() })}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </>
    );
  }

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
                <SelectTrigger className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-0 rounded-md px-3.5 py-2 h-9 hover:bg-[#f0f1f2] dark:hover:bg-[#333333] transition-colors w-56">
                  <SelectValue
                    placeholder={t('page.selectProject')}
                    className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] leading-5"
                  />
                </SelectTrigger>
                <SelectContent className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-border">
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
                        className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] focus:bg-[#e9ecef] dark:focus:bg-[#333333]"
                      >
                        {project.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              <Button
                onClick={onCreateSurvey}
                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
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
