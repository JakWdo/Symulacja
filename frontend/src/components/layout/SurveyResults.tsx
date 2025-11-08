import { Button } from '@/components/ui/button';
import { ArrowLeft, Download } from 'lucide-react';
import { SurveyResults as SurveyResultsContent } from '@/components/surveys/SurveyResults';
import type { Survey } from '@/types';

interface SurveyResultsProps {
  survey: Survey;
  onBack: () => void;
}

export function SurveyResults({ survey, onBack }: SurveyResultsProps) {
  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting survey results for:', survey.id);
  };

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-foreground">{survey.title}</h1>
              <p className="text-muted-foreground">Survey Results & Analytics</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Results Content */}
        {survey.status === 'completed' ? (
          <SurveyResultsContent surveyId={survey.id} />
        ) : (
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">
              {survey.status === 'running'
                ? 'Survey is currently running. Results will be available when completed.'
                : 'No results available yet.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
