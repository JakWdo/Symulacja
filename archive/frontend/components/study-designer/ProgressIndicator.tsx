/**
 * ProgressIndicator - Wizard steps progress
 *
 * Redesigned zgodnie z Sight Design System:
 * - Success colors dla completed steps (zamiast hardcoded green)
 * - Brand colors dla current step (zamiast hardcoded blue)
 * - Muted colors dla pending steps (zamiast hardcoded gray)
 * - Consistent spacing i typography
 */

import React from 'react';
import { CheckCircle, Circle } from 'lucide-react';

interface Props {
  currentStage: string;
}

const STAGES = [
  { id: 'welcome', name: 'Start', order: 1 },
  { id: 'gather_goal', name: 'Cel', order: 2 },
  { id: 'define_audience', name: 'Grupa docelowa', order: 3 },
  { id: 'select_method', name: 'Metoda', order: 4 },
  { id: 'configure_details', name: 'Szczegóły', order: 5 },
  { id: 'generate_plan', name: 'Plan', order: 6 },
  { id: 'await_approval', name: 'Zatwierdzenie', order: 7 },
];

export const ProgressIndicator: React.FC<Props> = ({ currentStage }) => {
  const currentOrder =
    STAGES.find((s) => s.id === currentStage)?.order || 1;

  return (
    <div className="flex items-center gap-2">
      {STAGES.map((stage, index) => {
        const isCompleted = stage.order < currentOrder;
        const isCurrent = stage.order === currentOrder;

        return (
          <React.Fragment key={stage.id}>
            {/* Step Circle */}
            <div className="flex flex-col items-center">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full ${
                  isCompleted
                    ? 'bg-success text-white'
                    : isCurrent
                    ? 'bg-brand text-white'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <Circle className="w-4 h-4" />
                )}
              </div>

              {/* Step Name */}
              <p
                className={`text-xs mt-1 hidden sm:block ${
                  isCurrent ? 'font-semibold text-brand' : 'text-muted-foreground'
                }`}
              >
                {stage.name}
              </p>
            </div>

            {/* Connector Line */}
            {index < STAGES.length - 1 && (
              <div
                className={`h-0.5 w-8 ${
                  isCompleted ? 'bg-success' : 'bg-muted'
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
