/**
 * ProgressIndicator - Wizard steps progress
 *
 * Pokazuje wizualnie w którym etapie konwersacji jesteśmy.
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
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-400'
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
                  isCurrent ? 'font-semibold text-blue-600' : 'text-gray-500'
                }`}
              >
                {stage.name}
              </p>
            </div>

            {/* Connector Line */}
            {index < STAGES.length - 1 && (
              <div
                className={`h-0.5 w-8 ${
                  isCompleted ? 'bg-green-500' : 'bg-gray-200'
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
