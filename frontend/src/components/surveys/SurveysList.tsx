import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart3, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Survey } from '@/types';
import { SurveysStats } from './SurveysStats';
import { SurveyCard } from './SurveyCard';

interface SurveysListProps {
  surveys: Survey[];
  onCreateSurvey: () => void;
  onSelectSurvey: (survey: Survey) => void;
  onRunSurvey: (survey: Survey) => void;
  onDeleteSurvey: (survey: Survey) => void;
  isRunning?: boolean;
}

export function SurveysList({
  surveys,
  onCreateSurvey,
  onSelectSurvey,
  onRunSurvey,
  onDeleteSurvey,
  isRunning = false,
}: SurveysListProps) {
  const { t } = useTranslation('surveys');

  if (surveys.length === 0) {
    return (
      <>
        <SurveysStats surveys={surveys} />
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
                className="bg-brand hover:bg-brand/90 text-brand-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                {t('list.empty.action')}
              </Button>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <SurveysStats surveys={surveys} />
      <div className="space-y-4">
        <h2 className="text-xl text-foreground">{t('list.title')}</h2>
        <div className="grid grid-cols-1 gap-4">
          {surveys.map((survey) => (
            <SurveyCard
              key={survey.id}
              survey={survey}
              onSelectSurvey={onSelectSurvey}
              onRunSurvey={onRunSurvey}
              onDeleteSurvey={onDeleteSurvey}
              isRunning={isRunning}
            />
          ))}
        </div>
      </div>
    </>
  );
}
