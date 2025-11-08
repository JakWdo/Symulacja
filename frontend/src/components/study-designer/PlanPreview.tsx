/**
 * PlanPreview - Wyświetla wygenerowany plan badania
 *
 * Pokazuje plan w markdown z estymacjami i przyciskami approve/modify.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import ReactMarkdown from 'react-markdown';
import { CheckCircle, Edit, Clock, DollarSign } from 'lucide-react';
import { useApprovePlan } from '../../hooks/useStudyDesigner';
import type { GeneratedPlan } from '../../api/studyDesigner';

interface Props {
  plan: GeneratedPlan;
  sessionId: string;
}

export const PlanPreview: React.FC<Props> = ({ plan, sessionId }) => {
  const approveMutation = useApprovePlan(sessionId);

  const handleApprove = async () => {
    try {
      await approveMutation.mutateAsync();
    } catch (err) {
      console.error('Failed to approve plan:', err);
    }
  };

  const estimatedMinutes = Math.ceil(plan.estimated_time_seconds / 60);

  return (
    <Card className="border-2 border-green-500 shadow-lg">
      <CardHeader className="bg-green-50">
        <CardTitle className="text-xl font-bold flex items-center gap-2 text-green-900">
          <CheckCircle className="w-6 h-6" />
          ✅ Plan Badania Gotowy!
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Plan Content (Markdown) */}
        <div className="prose prose-sm max-w-none max-h-[500px] overflow-y-auto border border-gray-200 rounded-lg p-4 bg-white">
          <ReactMarkdown>{plan.markdown_summary}</ReactMarkdown>
        </div>

        {/* Estimates Grid */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-3 rounded-full">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Szacowany czas</p>
              <p className="text-lg font-semibold text-gray-900">
                ~{estimatedMinutes} minut
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-green-100 p-3 rounded-full">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Szacowany koszt</p>
              <p className="text-lg font-semibold text-gray-900">
                ${plan.estimated_cost_usd.toFixed(2)} USD
              </p>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">
            💡 <strong>Czy zatwierdzasz ten plan?</strong> Po zatwierdzeniu badanie
            zostanie automatycznie uruchomione. Możesz też wrócić do konfiguracji jeśli
            chcesz coś zmienić.
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex gap-3 justify-end bg-gray-50">
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            // TODO: Handle modification (send message "modyfikuj")
            window.location.reload(); // Temporary
          }}
        >
          <Edit className="w-4 h-4 mr-2" />
          Modyfikuj
        </Button>

        <Button
          size="lg"
          className="bg-green-600 hover:bg-green-700"
          onClick={handleApprove}
          disabled={approveMutation.isPending}
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          {approveMutation.isPending ? 'Zatwierdzanie...' : 'Zatwierdź i uruchom'}
        </Button>
      </CardFooter>
    </Card>
  );
};
