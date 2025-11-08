/**
 * WorkflowsListPage - Strona listy workflows z designem Figmy
 *
 * Features:
 * - Tabs: "My Workflows" i "Templates"
 * - Lista workflows użytkownika
 * - Template library z kategoriami
 * - Copy i Delete buttons
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Plus,
  FolderOpen,
  Copy,
  Trash2,
  AlertCircle,
  Sparkles,
  Layers,
} from 'lucide-react';

import { useWorkflows, useDeleteWorkflow, useDuplicateWorkflow } from '@/hooks/useWorkflows';
import { TemplateSelectionDialog } from './TemplateSelectionDialog';
import { workflowTemplates } from './templateMetadata';
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
  const { mutate: duplicateWorkflow } = useDuplicateWorkflow();

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

  const handleDuplicateWorkflow = (workflow: Workflow) => {
    duplicateWorkflow(workflow.id, {
      onSuccess: () => {
        toast.success('Workflow duplicated');
      },
      onError: (error: any) => {
        toast.error(`Failed to duplicate workflow: ${error.message}`);
      },
    });
  };

  const handleCreateFromTemplate = (templateId: string) => {
    setIsDialogOpen(true);
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
    <Card className="bg-card border border-border">
      <CardContent className="py-12 text-center">
        <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-foreground mb-2">No workflows yet</p>
        <p className="text-sm text-muted-foreground mb-4">
          Create your first workflow or start from a template
        </p>
        <div className="flex gap-2 justify-center">
          <Button
            onClick={() => setIsDialogOpen(true)}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            Create Workflow
          </Button>
          <Button
            variant="outline"
            onClick={() => setIsDialogOpen(true)}
          >
            Browse Templates
          </Button>
        </div>
      </CardContent>
    </Card>
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
            className="bg-card border border-border hover:shadow-lg transition-shadow"
          >
            <CardHeader>
              <CardTitle className="text-foreground flex items-start justify-between">
                <span>{workflow.name}</span>
                <Badge variant="outline" className="ml-2 shrink-0">
                  {(workflow.canvas_data as any)?.nodes?.length || 0} nodes
                </Badge>
              </CardTitle>
              {workflow.description && (
                <p className="text-sm text-muted-foreground mt-2">
                  {workflow.description}
                </p>
              )}
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground mb-4">
                Updated {new Date(workflow.updated_at).toLocaleDateString()}
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => handleOpenWorkflow(workflow)}
                  size="sm"
                  className="flex-1 bg-brand-orange hover:bg-brand-orange/90 text-white"
                >
                  Open
                </Button>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDuplicateWorkflow(workflow);
                  }}
                  size="sm"
                  variant="outline"
                >
                  <Copy className="w-4 h-4" />
                </Button>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteWorkflow(workflow);
                  }}
                  size="sm"
                  variant="outline"
                  disabled={deletingId === workflow.id}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
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
    <div className="h-screen flex flex-col max-w-[1920px] mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-foreground mb-2">Research Workflows</h1>
        <p className="text-muted-foreground">
          Design and manage your research workflows with AI-powered automation
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="workflows" className="flex-1">
        <TabsList className="mb-4">
          <TabsTrigger value="workflows">My Workflows</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        {/* My Workflows Tab */}
        <TabsContent value="workflows" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              {workflows?.length || 0} workflow{workflows?.length !== 1 ? 's' : ''}
            </p>
            <Button
              onClick={() => setIsDialogOpen(true)}
              className="bg-brand-orange hover:bg-brand-orange/90 text-white gap-2"
            >
              <Plus className="w-4 h-4" />
              New Workflow
            </Button>
          </div>

          {isLoading && renderLoading()}
          {error && renderError()}
          {!isLoading && !error && renderWorkflows()}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              {workflowTemplates.length} ready-to-use templates
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflowTemplates.map((template) => (
              <Card
                key={template.id}
                className="bg-card border border-border hover:shadow-lg transition-shadow"
              >
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <CardTitle className="text-foreground">{template.name}</CardTitle>
                    {template.category && (
                      <Badge variant="outline" className="shrink-0 ml-2">
                        {template.category}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {template.description}
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 mb-4 text-xs text-muted-foreground">
                    <Layers className="w-4 h-4" />
                    <span>{template.nodeCount} activities</span>
                  </div>
                  <Button
                    onClick={() => handleCreateFromTemplate(template.id)}
                    size="sm"
                    className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white"
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Use Template
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

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
