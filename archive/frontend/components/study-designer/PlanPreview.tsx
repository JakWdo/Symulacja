/**
 * PlanPreview - Wyświetla wygenerowany plan badania
 *
 * Redesigned zgodnie z Sight Design System:
 * - Success colors z CSS variables zamiast hardcoded green
 * - Info colors dla informacji
 * - Consistent rounded corners (rounded-[8px])
 * - Icons zamiast emoji
 * - Proper muted colors dla metadanych
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import ReactMarkdown from 'react-markdown';
import { CheckCircle, Edit, Clock, DollarSign, Info } from 'lucide-react';
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
    <Card className="border-2 border-success shadow-lg rounded-[8px]">
      <CardHeader className="bg-success/10">
        <CardTitle className="text-xl font-semibold flex items-center gap-2 text-success-foreground">
          <CheckCircle className="w-6 h-6 text-success" />
          Plan Badania Gotowy!
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Plan Content (Markdown) */}
        <div className="prose prose-sm max-w-none max-h-[500px] overflow-y-auto border border-border rounded-[8px] p-4 bg-background">
          <ReactMarkdown>{plan.markdown_summary}</ReactMarkdown>
        </div>

        {/* Estimates Grid */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-[8px]">
          <div className="flex items-center gap-3">
            <div className="bg-info/20 p-3 rounded-[8px]">
              <Clock className="w-5 h-5 text-info" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Szacowany czas</p>
              <p className="text-lg font-semibold text-foreground">
                ~{estimatedMinutes} minut
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-success/20 p-3 rounded-[8px]">
              <DollarSign className="w-5 h-5 text-success" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Szacowany koszt</p>
              <p className="text-lg font-semibold text-foreground">
                ${plan.estimated_cost_usd.toFixed(2)} USD
              </p>
            </div>
          </div>
        </div>

        {/* Info Alert */}
        <Alert className="rounded-[8px] bg-info/10 border-info/20">
          <Info className="h-4 w-4 text-info" />
          <AlertDescription className="text-info-foreground">
            <strong>Czy zatwierdzasz ten plan?</strong> Po zatwierdzeniu badanie
            zostanie automatycznie uruchomione. Możesz też wrócić do konfiguracji jeśli
            chcesz coś zmienić.
          </AlertDescription>
        </Alert>
      </CardContent>

      <CardFooter className="flex gap-3 justify-end bg-muted/50 rounded-b-[8px]">
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            // TODO: Handle modification (send message "modyfikuj")
            window.location.reload(); // Temporary
          }}
          className="rounded-[6px]"
        >
          <Edit className="w-4 h-4 mr-2" />
          Modyfikuj
        </Button>

        <Button
          size="lg"
          className="bg-success hover:bg-success/90 text-white rounded-[6px]"
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
