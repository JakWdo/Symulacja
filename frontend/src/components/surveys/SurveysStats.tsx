import { Card, CardContent } from '@/components/ui/card';
import { BarChart3, Users } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Survey } from '@/types';

interface SurveysStatsProps {
  surveys: Survey[];
}

export function SurveysStats({ surveys }: SurveysStatsProps) {
  const { t } = useTranslation('surveys');

  const totalResponses = surveys.reduce((sum, survey) => sum + survey.actual_responses, 0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('tabs.all')}</p>
              <p className="text-2xl font-bold text-brand">{surveys.length}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-brand" />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{t('tabs.allResponses')}</p>
              <p className="text-2xl font-bold text-brand">
                {totalResponses.toLocaleString()}
              </p>
            </div>
            <Users className="w-8 h-8 text-brand" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
