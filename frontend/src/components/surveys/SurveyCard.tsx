import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Eye, Play, Trash2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { useTranslation } from 'react-i18next';
import type { Survey } from '@/types';

interface SurveyCardProps {
  survey: Survey;
  onSelectSurvey: (survey: Survey) => void;
  onRunSurvey: (survey: Survey) => void;
  onDeleteSurvey: (survey: Survey) => void;
  isRunning?: boolean;
}

export function SurveyCard({
  survey,
  onSelectSurvey,
  onRunSurvey,
  onDeleteSurvey,
  isRunning = false,
}: SurveyCardProps) {
  const { t } = useTranslation('surveys');

  const getStatusBadge = (status: Survey['status']) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-brand-muted text-brand dark:text-brand">{t('status.completed')}</Badge>;
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

  const progress = survey.target_responses > 0
    ? (survey.actual_responses / survey.target_responses) * 100
    : 0;

  const questionsText = survey.questions.length === 1
    ? 'pytanie'
    : survey.questions.length < 5
    ? 'pytania'
    : 'pytań';

  return (
    <Card
      className={`bg-card border hover:shadow-md transition-shadow shadow-sm ${
        survey.status === 'running'
          ? 'border-brand/50 shadow-[0_0_0_1px_rgba(242,116,5,0.08)]'
          : 'border-border'
      }`}
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
                  {survey.questions.length} {questionsText}
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
                    <DropdownMenuItem onClick={() => onRunSurvey(survey)}>
                      <Play className="w-4 h-4 mr-2" />
                      {t('list.card.launch')}
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    onClick={() => onDeleteSurvey(survey)}
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
                  className="bg-brand hover:bg-brand/90 text-brand-foreground"
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
                    className="bg-brand hover:bg-brand/90 text-brand-foreground"
                    onClick={() => onRunSurvey(survey)}
                    disabled={isRunning}
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
}
