/**
 * ValidationDialog - Modal wyświetlający wyniki walidacji workflow
 *
 * Pokazuje:
 * - Errors (blokują execution)
 * - Warnings (nie blokują, ale warto naprawić)
 * - Info messages (sugestie)
 *
 * @example
 * <ValidationDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   validationResult={validationResult}
 *   onExecute={() => executeWorkflow()}
 * />
 */

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, CheckCircle2, Play } from 'lucide-react';

interface ValidationIssue {
  type: 'error' | 'warning' | 'info';
  message: string;
  node_ids?: string[];
}

interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

interface ValidationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  validationResult?: ValidationResult;
  onExecute: () => void;
}

/**
 * Convert API validation result to display format
 */
function formatValidationIssues(
  result?: ValidationResult
): ValidationIssue[] {
  if (!result) return [];

  const issues: ValidationIssue[] = [];

  // Add errors
  result.errors.forEach((error) => {
    issues.push({
      type: 'error',
      message: error,
    });
  });

  // Add warnings
  result.warnings.forEach((warning) => {
    issues.push({
      type: 'warning',
      message: warning,
    });
  });

  // Add success message if valid
  if (result.is_valid && issues.length === 0) {
    issues.push({
      type: 'info',
      message: '✓ Workflow is valid and ready to execute!',
    });
  }

  return issues;
}

/**
 * ValidationDialog Component
 */
export function ValidationDialog({
  open,
  onOpenChange,
  validationResult,
  onExecute,
}: ValidationDialogProps) {
  const issues = formatValidationIssues(validationResult);
  const hasErrors = validationResult?.errors && validationResult.errors.length > 0;
  const canExecute = validationResult?.is_valid || false;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Workflow Validation</DialogTitle>
          <DialogDescription>
            Review validation results for your workflow
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-96">
          <div className="space-y-2">
            {issues.length === 0 ? (
              <Alert className="bg-blue-500/10 border-blue-500/30">
                <AlertCircle className="w-4 h-4 text-blue-600" />
                <AlertDescription className="text-blue-600">
                  No validation results yet. Click "Validate" to check your workflow.
                </AlertDescription>
              </Alert>
            ) : (
              issues.map((issue, index) => (
                <Alert
                  key={index}
                  className={
                    issue.type === 'error'
                      ? 'bg-destructive/10 border-destructive/30'
                      : issue.type === 'warning'
                      ? 'bg-orange-500/10 border-orange-500/30'
                      : 'bg-green-500/10 border-green-500/30'
                  }
                >
                  {issue.type === 'info' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertCircle
                      className={`w-4 h-4 ${
                        issue.type === 'error'
                          ? 'text-destructive'
                          : issue.type === 'warning'
                          ? 'text-orange-600'
                          : 'text-blue-600'
                      }`}
                    />
                  )}
                  <AlertDescription
                    className={
                      issue.type === 'error'
                        ? 'text-destructive'
                        : issue.type === 'warning'
                        ? 'text-orange-600'
                        : 'text-green-600'
                    }
                  >
                    {issue.message}
                  </AlertDescription>
                </Alert>
              ))
            )}
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {canExecute && !hasErrors && (
            <Button
              onClick={() => {
                onOpenChange(false);
                onExecute();
              }}
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
            >
              <Play className="w-4 h-4 mr-2" />
              Execute Workflow
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
