/**
 * WorkflowsListPage - Strona listy workflows
 *
 * Features:
 * - Lista workflows użytkownika
 * - "New Workflow" button otwierający TemplateSelectionDialog
 * - Filtrowanie po projekcie
 * - Nawigacja do workflow editor
 *
 * @example
 * <WorkflowsListPage
 *   projectId={projectId}
 *   onSelectWorkflow={(workflow) => setCurrentView('workflow-editor')}
 * />
 */

import { useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  PlusCircle,
  Workflow as WorkflowIcon,
  Calendar,
  Play,
  Trash2,
  AlertCircle,
} from 'lucide-react';

import { useWorkflows, useDeleteWorkflow } from '@/hooks/useWorkflows';
import { TemplateSelectionDialog } from './TemplateSelectionDialog';
import type { Workflow } from '@/types';

interface WorkflowsListPageProps {
  projectId?: string; // Filter po projekcie (optional)
  onSelectWorkflow?: (workflow: Workflow) => void; // Handler do nawigacji
}

/**
 * WorkflowsListPage Component
 */
export function WorkflowsListPage({ projectId, onSelectWorkflow }: WorkflowsListPageProps) {

  // ============================================
  // State
  // ============================================

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // ============================================
  // API Hooks
  // ============================================

  const {
    data: workflows,
    isLoading,
    error,
  } = useWorkflows(projectId, false); // includeTemplates = false

  const { mutate: deleteWorkflow } = useDeleteWorkflow();

  // ============================================
  // Handlers
  // ============================================

  const handleOpenWorkflow = (workflow: Workflow) => {
    if (onSelectWorkflow) {
      onSelectWorkflow(workflow);
    }
  };

  const handleDeleteWorkflow = (workflow: Workflow) => {
    if (!confirm(`Are you sure you want to delete "${workflow.name}"?`)) {
      return;
    }

    setDeletingId(workflow.id);

    deleteWorkflow(workflow.id, {
      onSuccess: () => {
        toast.success(`Workflow "${workflow.name}" deleted`);
        setDeletingId(null);
      },
      onError: (error: any) => {
        toast.error(`Failed to delete workflow: ${error.message}`);
        setDeletingId(null);
      },
    });
  };

  // ============================================
  // Render Helpers
  // ============================================

  const renderLoading = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-5 w-3/4 mb-2" />
            <Skeleton className="h-4 w-full" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderError = () => (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertCircle className="w-12 h-12 text-destructive mb-4" />
      <h3 className="text-lg font-semibold mb-2">Failed to load workflows</h3>
      <p className="text-sm text-muted-foreground mb-4">
        {error?.message || 'An error occurred while loading your workflows.'}
      </p>
      <Button variant="outline" onClick={() => window.location.reload()}>
        Retry
      </Button>
    </div>
  );

  const renderEmpty = () => (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <WorkflowIcon className="w-16 h-16 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">No workflows yet</h3>
      <p className="text-sm text-muted-foreground mb-6">
        Get started by creating your first workflow from a template or from scratch.
      </p>
      <Button onClick={() => setIsDialogOpen(true)}>
        <PlusCircle className="w-4 h-4 mr-2" />
        Create Workflow
      </Button>
    </div>
  );

  const renderWorkflows = () => {
    if (!workflows || workflows.length === 0) {
      return renderEmpty();
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.map((workflow) => (
          <Card
            key={workflow.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => handleOpenWorkflow(workflow)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg line-clamp-1">{workflow.name}</CardTitle>
                  {workflow.description && (
                    <CardDescription className="line-clamp-2 mt-1">
                      {workflow.description}
                    </CardDescription>
                  )}
                </div>
                <Badge
                  variant={
                    workflow.status === 'active'
                      ? 'default'
                      : workflow.status === 'draft'
                      ? 'secondary'
                      : 'outline'
                  }
                  className="ml-2"
                >
                  {workflow.status}
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                {/* Created Date */}
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(workflow.created_at).toLocaleDateString()}</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenWorkflow(workflow);
                    }}
                  >
                    <Play className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteWorkflow(workflow);
                    }}
                    disabled={deletingId === workflow.id}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  // ============================================
  // Main Render
  // ============================================

  // Default projectId dla przykładu (można pobrać z URL lub context)
  const effectiveProjectId = projectId || 'default-project-id';

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Workflows</h1>
          <p className="text-muted-foreground">
            Create and manage your research workflows
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <PlusCircle className="w-4 h-4 mr-2" />
          New Workflow
        </Button>
      </div>

      {/* Content */}
      {isLoading && renderLoading()}
      {error && renderError()}
      {!isLoading && !error && renderWorkflows()}

      {/* Template Selection Dialog */}
      <TemplateSelectionDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        projectId={effectiveProjectId}
        onWorkflowCreated={(workflow) => {
          if (onSelectWorkflow) {
            onSelectWorkflow(workflow);
          }
        }}
      />
    </div>
  );
}
