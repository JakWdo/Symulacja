/**
 * TemplateSelectionDialog - Dialog do wyboru workflow template
 *
 * Features:
 * - Wyświetla grid 6 predefiniowanych szablonów workflow
 * - "Start from Scratch" option (pusty workflow)
 * - Integracja z useWorkflowTemplates() i useInstantiateTemplate()
 * - Loading states, error handling
 * - Responsywny design (mobile-friendly)
 *
 * @example
 * <TemplateSelectionDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, FileText, Loader2, PlusCircle } from 'lucide-react';

import { useWorkflowTemplates, useInstantiateTemplate, useCreateWorkflow } from '@/hooks/useWorkflows';
import { TemplateCard } from './TemplateCard';
import type { WorkflowTemplate } from '@/types';

interface TemplateSelectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  onWorkflowCreated?: (workflow: any) => void; // Callback po utworzeniu workflow
}

/**
 * TemplateSelectionDialog Component
 */
export function TemplateSelectionDialog({
  open,
  onOpenChange,
  projectId,
  onWorkflowCreated,
}: TemplateSelectionDialogProps) {

  // ============================================
  // State
  // ============================================

  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('');
  const [startFromScratch, setStartFromScratch] = useState(false);

  // ============================================
  // API Hooks
  // ============================================

  const {
    data: templates,
    isLoading: templatesLoading,
    error: templatesError,
  } = useWorkflowTemplates();

  const { mutate: instantiateTemplate, isPending: isInstantiating } =
    useInstantiateTemplate();

  const { mutate: createWorkflow, isPending: isCreating } = useCreateWorkflow();

  // ============================================
  // Handlers
  // ============================================

  /**
   * Handle template selection
   */
  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    setStartFromScratch(false);
  };

  /**
   * Handle "Start from Scratch"
   */
  const handleStartFromScratch = () => {
    setStartFromScratch(true);
    setSelectedTemplateId(null);
  };

  /**
   * Handle workflow creation
   */
  const handleCreate = () => {
    if (!projectId) {
      toast.error('Project ID is required');
      return;
    }

    if (startFromScratch) {
      // Create empty workflow
      const name = workflowName.trim() || 'New Workflow';

      createWorkflow(
        {
          name,
          project_id: projectId,
          canvas_data: {
            nodes: [],
            edges: [],
          },
        },
        {
          onSuccess: (workflow) => {
            toast.success(`Workflow "${workflow.name}" created!`);
            onOpenChange(false);
            if (onWorkflowCreated) {
              onWorkflowCreated(workflow);
            }
          },
          onError: (error: any) => {
            toast.error(`Failed to create workflow: ${error.message}`);
          },
        }
      );
    } else {
      // Instantiate template
      if (!selectedTemplateId) {
        toast.error('Please select a template');
        return;
      }

      const name = workflowName.trim();

      instantiateTemplate(
        {
          templateId: selectedTemplateId,
          data: {
            project_id: projectId,
            workflow_name: name || undefined, // Backend auto-generates if empty
          },
        },
        {
          onSuccess: (workflow) => {
            toast.success(`Workflow "${workflow.name}" created from template!`);
            onOpenChange(false);
            if (onWorkflowCreated) {
              onWorkflowCreated(workflow);
            }
          },
          onError: (error: any) => {
            toast.error(`Failed to create workflow: ${error.message}`);
          },
        }
      );
    }
  };

  /**
   * Reset state on dialog close
   */
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setSelectedTemplateId(null);
      setWorkflowName('');
      setStartFromScratch(false);
    }
    onOpenChange(newOpen);
  };

  // ============================================
  // Render Helpers
  // ============================================

  /**
   * Render loading state
   */
  const renderLoading = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i} className="h-64">
          <CardHeader>
            <Skeleton className="w-12 h-12 rounded-lg mb-3" />
            <Skeleton className="h-5 w-3/4 mb-2" />
            <Skeleton className="h-4 w-full" />
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-3">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-20" />
            </div>
            <div className="flex gap-1">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-5 w-24" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  /**
   * Render error state
   */
  const renderError = () => (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <AlertCircle className="w-12 h-12 text-destructive mb-4" />
      <h3 className="text-lg font-semibold mb-2">Failed to load templates</h3>
      <p className="text-sm text-muted-foreground mb-4">
        {templatesError?.message || 'An error occurred while loading workflow templates.'}
      </p>
      <Button variant="outline" onClick={() => window.location.reload()}>
        Retry
      </Button>
    </div>
  );

  /**
   * Render templates grid
   */
  const renderTemplates = () => {
    if (!templates || templates.length === 0) {
      return (
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">No templates available</p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            selected={selectedTemplateId === template.id}
            onClick={() => handleTemplateSelect(template.id)}
          />
        ))}

        {/* Start from Scratch Card */}
        <Card
          className={`cursor-pointer transition-all hover:shadow-lg hover:scale-[1.02] border-2 ${
            startFromScratch ? 'ring-2 ring-primary shadow-lg border-primary' : 'border-dashed border-muted-foreground/30'
          }`}
          onClick={handleStartFromScratch}
        >
          <CardHeader>
            <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-3 bg-muted">
              <PlusCircle className="w-6 h-6 text-muted-foreground" />
            </div>
            <CardTitle className="text-lg">Start from Scratch</CardTitle>
            <CardDescription className="text-sm">
              Create an empty workflow and build it step by step
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary" className="text-xs">
              Custom
            </Badge>
          </CardContent>
        </Card>
      </div>
    );
  };

  // ============================================
  // Main Render
  // ============================================

  const isSubmitting = isInstantiating || isCreating;
  const canCreate = startFromScratch || selectedTemplateId !== null;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle className="text-2xl">Create New Workflow</DialogTitle>
          <DialogDescription>
            Choose a template to get started quickly, or start from scratch to build a custom workflow.
          </DialogDescription>
        </DialogHeader>

        {/* Templates Grid (scrollable) */}
        <ScrollArea className="px-6 max-h-[500px]">
          {templatesLoading && renderLoading()}
          {templatesError && renderError()}
          {!templatesLoading && !templatesError && renderTemplates()}
        </ScrollArea>

        {/* Footer - Workflow Name Input + Actions */}
        <div className="px-6 pb-6 pt-4 border-t">
          <div className="space-y-4">
            {/* Workflow Name Input */}
            <div className="space-y-2">
              <Label htmlFor="workflow-name">
                Workflow Name
                <span className="text-muted-foreground text-xs ml-2">(optional)</span>
              </Label>
              <Input
                id="workflow-name"
                placeholder={
                  selectedTemplateId
                    ? templates?.find((t) => t.id === selectedTemplateId)?.name || 'Enter workflow name'
                    : 'My Custom Workflow'
                }
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            {/* Actions */}
            <DialogFooter>
              <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!canCreate || isSubmitting}>
                {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Create Workflow
              </Button>
            </DialogFooter>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
