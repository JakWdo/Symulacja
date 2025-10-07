import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Plus, Users, Eye, BarChart3, Play, Trash2, Clock, Loader2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { surveysApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { Survey } from '@/types';

interface SurveysProps {
  onCreateSurvey: () => void;
  onSelectSurvey: (survey: Survey) => void;
}

export function Surveys({ onCreateSurvey, onSelectSurvey }: SurveysProps) {
  const { selectedProject } = useAppStore();
  const queryClient = useQueryClient();

  // Fetch surveys for selected project
  const { data: surveys = [], isLoading } = useQuery({
    queryKey: ['surveys', selectedProject?.id],
    queryFn: () => surveysApi.getByProject(selectedProject!.id),
    enabled: !!selectedProject,
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
    if (confirm(`Launch survey "${survey.title}"? This will generate responses from all personas in the project.`)) {
      runMutation.mutate(survey.id);
    }
  };

  const handleDeleteSurvey = (survey: Survey) => {
    if (confirm(`Delete survey "${survey.title}"? This action cannot be undone.`)) {
      deleteMutation.mutate(survey.id);
    }
  };

  const getStatusBadge = (status: Survey['status']) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500/10 text-green-700 dark:text-green-400">Completed</Badge>;
      case 'running':
        return <Badge className="bg-blue-500/10 text-blue-700 dark:text-blue-400">Running</Badge>;
      case 'draft':
        return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">Draft</Badge>;
      case 'failed':
        return <Badge className="bg-red-500/10 text-red-700 dark:text-red-400">Failed</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Please select a project to view surveys</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Synthetic Surveys</h1>
          <p className="text-muted-foreground">
            Generate quantitative insights from virtual respondents perfectly matched to your target audience
          </p>
        </div>
        <Button
          onClick={onCreateSurvey}
          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create New Survey
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-card border border-border shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Surveys</p>
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
                <p className="text-sm text-muted-foreground">Total Responses</p>
                <p className="text-2xl font-bold text-[#F27405]">
                  {surveys.reduce((sum, survey) => sum + survey.actual_responses, 0).toLocaleString()}
                </p>
              </div>
              <Users className="w-8 h-8 text-[#F27405]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Surveys List */}
      <div className="space-y-4">
        <h2 className="text-xl text-foreground">Your Surveys</h2>

        {isLoading ? (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <p className="text-muted-foreground">Loading surveys...</p>
            </CardContent>
          </Card>
        ) : surveys.length === 0 ? (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">No surveys yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first synthetic survey to start collecting quantitative data
              </p>
              <Button
                onClick={onCreateSurvey}
                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Survey
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {surveys.map((survey) => {
              const progress = survey.target_responses > 0
                ? (survey.actual_responses / survey.target_responses) * 100
                : 0;

              return (
                <Card key={survey.id} className="bg-card border border-border hover:shadow-md transition-shadow shadow-sm">
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
                              {survey.questions.length} question{survey.questions.length !== 1 ? 's' : ''}
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
                                  View Results
                                </DropdownMenuItem>
                              )}
                              {survey.status === 'draft' && (
                                <DropdownMenuItem onClick={() => handleRunSurvey(survey)}>
                                  <Play className="w-4 h-4 mr-2" />
                                  Launch Survey
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem
                                onClick={() => handleDeleteSurvey(survey)}
                                className="text-red-600 dark:text-red-400"
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>

                        {/* Progress and Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Progress</span>
                              <span className="text-card-foreground">
                                {survey.actual_responses.toLocaleString()} / {survey.target_responses.toLocaleString()}
                              </span>
                            </div>
                            <Progress value={progress} className="h-2" />
                            <p className="text-xs text-muted-foreground">
                              {Math.round(progress)}% Complete
                            </p>
                          </div>

                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">Execution Time</p>
                            <div className="space-y-1">
                              {survey.total_execution_time_ms ? (
                                <>
                                  <p className="text-xs text-card-foreground">
                                    Total: {(survey.total_execution_time_ms / 1000).toFixed(1)}s
                                  </p>
                                  {survey.avg_response_time_ms && (
                                    <p className="text-xs text-card-foreground">
                                      Avg: {(survey.avg_response_time_ms / 1000).toFixed(2)}s per response
                                    </p>
                                  )}
                                </>
                              ) : (
                                <p className="text-xs text-card-foreground">
                                  {survey.status === 'running'
                                    ? 'In progress...'
                                    : survey.status === 'draft'
                                    ? 'Not started'
                                    : 'N/A'
                                  }
                                </p>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 pt-2">
                          {survey.status === 'completed' && (
                            <Button
                              size="sm"
                              onClick={() => onSelectSurvey(survey)}
                              className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View Results
                            </Button>
                          )}
                          {survey.status === 'draft' && (
                            <Button
                              size="sm"
                              onClick={() => handleRunSurvey(survey)}
                              disabled={runMutation.isPending}
                              className="bg-green-600 hover:bg-green-700 text-white"
                            >
                              <Play className="w-4 h-4 mr-2" />
                              {runMutation.isPending ? 'Launching...' : 'Launch'}
                            </Button>
                          )}
                          {survey.status === 'running' && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled
                              className="border-border"
                            >
                              <Clock className="w-4 h-4 mr-2 animate-spin" />
                              Running...
                            </Button>
                          )}
                          <p className="text-xs text-muted-foreground ml-auto">
                            Created {new Date(survey.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
