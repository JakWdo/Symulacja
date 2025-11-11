/**
 * WorkflowToolbar - Górny toolbar dla Workflow Editor
 *
 * Zawiera:
 * - Tytuł i opis workflow
 * - Badges z błędami walidacji
 * - Akcje: Validate, Auto Layout, Export, Save, Execute
 * - Selektor kierunku layoutu
 * - Progress bar wykonywania
 *
 * @example
 * <WorkflowToolbar
 *   workflow={workflow}
 *   validationResult={validationResult}
 *   isExecuting={isExecuting}
 *   executionProgress={75}
 *   onBack={() => navigate(-1)}
 *   onValidate={handleValidate}
 *   onExport={handleExport}
 *   onSave={handleSave}
 *   onExecute={handleExecute}
 * />
 */

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  AlertCircle,
  ArrowLeft,
  Download,
  Pause,
  Play,
  Save,
  Sparkles,
} from 'lucide-react';
import { LayoutDirection } from './utils/autoLayout';

export interface ValidationResult {
  is_valid: boolean;
  errors: Array<{ message: string }>;
  warnings: Array<{ message: string }>;
}

interface WorkflowToolbarProps {
  workflow: {
    name: string;
    description?: string;
  };
  validationResult?: ValidationResult | null;
  isExecuting: boolean;
  executionProgress: number;
  activeTab: 'canvas' | 'history';
  layoutDirection: LayoutDirection;
  isLayouting: boolean;
  nodesCount: number;
  onBack?: () => void;
  onValidate: () => void;
  onAutoLayout: () => void;
  onExport: () => void;
  onSave: () => void;
  onExecute: () => void;
  onLayoutDirectionChange: (direction: LayoutDirection) => void;
}

/**
 * WorkflowToolbar Component
 */
export function WorkflowToolbar({
  workflow,
  validationResult,
  isExecuting,
  executionProgress,
  activeTab,
  layoutDirection,
  isLayouting,
  nodesCount,
  onBack,
  onValidate,
  onAutoLayout,
  onExport,
  onSave,
  onExecute,
  onLayoutDirectionChange,
}: WorkflowToolbarProps) {
  return (
    <>
      {/* Top Bar */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-background">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h2 className="text-foreground text-lg font-semibold">
              {workflow.name}
            </h2>
            {workflow.description && (
              <p className="text-xs text-muted-foreground">
                {workflow.description}
              </p>
            )}
          </div>
          {validationResult && !validationResult.is_valid && (
            <>
              {validationResult.errors.length > 0 && (
                <Badge variant="outline" className="border-destructive text-destructive">
                  {validationResult.errors.length} errors
                </Badge>
              )}
              {validationResult.warnings.length > 0 && (
                <Badge variant="outline" className="border-orange-500 text-orange-600">
                  {validationResult.warnings.length} warnings
                </Badge>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Show canvas actions only when on canvas tab */}
          {activeTab === 'canvas' && (
            <>
              <Button variant="outline" size="sm" onClick={onValidate}>
                <AlertCircle className="w-4 h-4 mr-2" />
                Validate
              </Button>

              {/* Layout Direction Selector */}
              <Select
                value={layoutDirection}
                onValueChange={(value) =>
                  onLayoutDirectionChange(value as LayoutDirection)
                }
              >
                <SelectTrigger className="w-[130px] h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="TB">Top → Bottom</SelectItem>
                  <SelectItem value="LR">Left → Right</SelectItem>
                </SelectContent>
              </Select>

              {/* Auto-Layout Button */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onAutoLayout}
                      disabled={isLayouting || nodesCount === 0}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Auto Layout
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Automatically arrange nodes in hierarchical layout</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <Button variant="outline" size="sm" onClick={onExport}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm" onClick={onSave}>
                <Save className="w-4 h-4 mr-2" />
                Save
              </Button>
            </>
          )}
          {isExecuting ? (
            <Button variant="outline" size="sm" disabled>
              <Pause className="w-4 h-4 mr-2" />
              Executing...
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={onExecute}
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
            >
              <Play className="w-4 h-4 mr-2" />
              Execute
            </Button>
          )}
        </div>
      </div>

      {/* Execution Progress Bar */}
      {isExecuting && (
        <div className="px-4 py-2 bg-brand-orange/10 border-b border-brand-orange/20">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-foreground">Executing workflow...</span>
            <span className="text-sm text-muted-foreground">
              {Math.round(executionProgress)}%
            </span>
          </div>
          <Progress value={executionProgress} className="h-2" />
        </div>
      )}
    </>
  );
}
