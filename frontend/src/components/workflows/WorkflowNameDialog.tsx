/**
 * WorkflowNameDialog - Prosty dialog do nazwania workflow z template
 *
 * Features:
 * - Pokazuje nazwę wybranego template
 * - Input dla custom workflow name (optional)
 * - Instant instantiate - bez ponownego wyboru template
 * - Loading state podczas tworzenia
 *
 * @example
 * <WorkflowNameDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   templateId="brand_perception"
 *   templateName="Brand Perception Study"
 *   projectId={projectId}
 *   onWorkflowCreated={(workflow) => navigate(`/workflows/${workflow.id}`)}
 * />
 */

import { useState } from 'react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';

import { useInstantiateTemplate } from '@/hooks/useWorkflows';
import type { Workflow } from '@/types';

interface WorkflowNameDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateId: string;
  templateName: string;
  projectId: string;
  onWorkflowCreated?: (workflow: Workflow) => void;
}

/**
 * WorkflowNameDialog Component
 */
export function WorkflowNameDialog({
  open,
  onOpenChange,
  templateId,
  templateName,
  projectId,
  onWorkflowCreated,
}: WorkflowNameDialogProps) {
  // ============================================
  // State
  // ============================================

  const [workflowName, setWorkflowName] = useState('');

  // ============================================
  // API Hook
  // ============================================

  const { mutate: instantiateTemplate, isPending: isCreating } =
    useInstantiateTemplate();

  // ============================================
  // Handlers
  // ============================================

  /**
   * Handle workflow creation
   */
  const handleCreate = () => {
    if (!projectId || !templateId) {
      toast.error('Missing project or template ID');
      return;
    }

    const name = workflowName.trim();

    instantiateTemplate(
      {
        templateId,
        data: {
          project_id: projectId,
          ...(name && { workflow_name: name }), // Only include if provided
        },
      },
      {
        onSuccess: (workflow) => {
          toast.success(`Workflow "${workflow.name}" created!`);
          onOpenChange(false);
          setWorkflowName(''); // Reset for next time
          if (onWorkflowCreated) {
            onWorkflowCreated(workflow);
          }
        },
        onError: (error: any) => {
          toast.error(`Failed to create workflow: ${error.message}`);
        },
      }
    );
  };

  /**
   * Handle dialog close
   */
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && !isCreating) {
      setWorkflowName('');
    }
    onOpenChange(newOpen);
  };

  /**
   * Handle Enter key in input
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isCreating) {
      handleCreate();
    }
  };

  // ============================================
  // Render
  // ============================================

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create Workflow from Template</DialogTitle>
          <DialogDescription>
            Creating workflow from: <strong>{templateName}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="workflow-name">
              Workflow Name
              <span className="text-muted-foreground text-xs ml-2">(optional)</span>
            </Label>
            <Input
              id="workflow-name"
              placeholder={templateName}
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isCreating}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              Leave blank to use template name: "{templateName}"
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isCreating}
          >
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={isCreating}>
            {isCreating && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Create Workflow
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
