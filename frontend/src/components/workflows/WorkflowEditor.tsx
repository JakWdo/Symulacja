/**
 * WorkflowEditor - Główny komponent visual workflow builder oparty na React Flow
 *
 * Features:
 * - Visual drag-and-drop canvas z React Flow
 * - Custom node types (persona, survey, focus-group, analysis, etc.)
 * - Auto-save canvas state (debounced)
 * - Node configuration panel
 * - Workflow validation
 * - Integration z backend API
 *
 * @example
 * // Basic usage
 * <Route path="/workflows/:workflowId/edit" element={<WorkflowEditor />} />
 *
 * @example
 * // W projekcie
 * <Route path="/projects/:projectId/workflows/:workflowId" element={<WorkflowEditor />} />
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  applyNodeChanges,
  applyEdgeChanges,
  ReactFlowInstance,
} from 'reactflow';
import { useDebouncedCallback } from 'use-debounce';
import { toast } from 'sonner';

import {
  useWorkflow,
  useUpdateWorkflow,
  useSaveCanvas,
  useValidateWorkflow,
  useExecuteWorkflow,
} from '@/hooks/useWorkflows';

import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Layers, History } from 'lucide-react';

import { ValidationDialog } from './ValidationDialog';
import { SaveWorkflowDialog } from './SaveWorkflowDialog';
import { ExecutionHistory } from './ExecutionHistory';
import { WorkflowToolbar } from './WorkflowToolbar';
import { WorkflowCanvas } from './WorkflowCanvas';
import { nodeTemplates } from './nodeTemplates';
import {
  getLayoutedElements,
  hasDefaultPositions,
  LayoutDirection,
} from './utils/autoLayout';
import { getSmartDropPosition } from './utils/smartPositioning';

interface WorkflowEditorProps {
  workflowId: string;
  onBack?: () => void;
}

/**
 * WorkflowEditor Component
 */
export function WorkflowEditor({ workflowId, onBack }: WorkflowEditorProps) {

  // ============================================
  // API Hooks
  // ============================================

  const { data: workflow, isLoading } = useWorkflow(workflowId);
  const { mutate: updateWorkflow } = useUpdateWorkflow();
  const { mutate: saveCanvas } = useSaveCanvas();
  const { mutate: validate, data: validationResult } = useValidateWorkflow();
  const { mutate: execute, isPending: isExecuting } = useExecuteWorkflow();

  // ============================================
  // Local State
  // ============================================

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isValidationOpen, setIsValidationOpen] = useState(false);
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [activeTab, setActiveTab] = useState<'canvas' | 'history'>('canvas');

  // Auto-layout state
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('TB');
  const [shouldAutoLayout, setShouldAutoLayout] = useState(false);
  const [isLayouting, setIsLayouting] = useState(false);
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null);

  // ============================================
  // Initialize Canvas from Workflow Data
  // ============================================

  useEffect(() => {
    if (workflow?.canvas_data) {
      const canvasData = workflow.canvas_data;
      const loadedNodes = canvasData.nodes || [];
      const loadedEdges = canvasData.edges || [];

      setNodes(loadedNodes);
      setEdges(loadedEdges);

      // Auto-layout on template load or if all nodes at (0,0)
      if (loadedNodes.length > 0 && hasDefaultPositions(loadedNodes)) {
        setShouldAutoLayout(true);
      }
    }
  }, [workflow, setNodes, setEdges]);

  // Auto-layout effect (triggered by shouldAutoLayout flag)
  useEffect(() => {
    if (shouldAutoLayout && nodes.length > 0 && !isLayouting) {
      handleAutoLayout();
      setShouldAutoLayout(false);
    }
  }, [shouldAutoLayout, nodes.length]);

  // ============================================
  // Auto-save Canvas (Debounced)
  // ============================================

  const debouncedSave = useDebouncedCallback(
    (canvasData: { nodes: Node[]; edges: Edge[] }) => {
      if (!workflowId) return;

      saveCanvas(
        {
          workflowId,
          canvasData: {
            nodes: canvasData.nodes,
            edges: canvasData.edges,
          }
        },
        {
          // Silent save - no toast
          onError: (error) => {
            console.error('Auto-save failed:', error);
          },
        }
      );
    },
    1000 // 1 second debounce
  );

  // ============================================
  // React Flow Event Handlers
  // ============================================

  const handleNodesChange = useCallback(
    (changes: any) => {
      const newNodes = applyNodeChanges(changes, nodes);
      setNodes(newNodes);
      debouncedSave({ nodes: newNodes, edges });
    },
    [nodes, edges, setNodes, debouncedSave]
  );

  const handleEdgesChange = useCallback(
    (changes: any) => {
      const newEdges = applyEdgeChanges(changes, edges);
      setEdges(newEdges);
      debouncedSave({ nodes, edges: newEdges });
    },
    [nodes, edges, setEdges, debouncedSave]
  );

  const onConnect = useCallback(
    (params: Connection) => {
      const edge = {
        ...params,
        id: `edge-${Date.now()}`,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#F27405',
        },
        style: {
          strokeWidth: 2,
          stroke: '#F27405',
        },
        type: 'smoothstep',
        animated: false,
      };
      const newEdges = addEdge(edge, edges);
      setEdges(newEdges);
      debouncedSave({ nodes, edges: newEdges });
      toast.success('Activities connected');
    },
    [edges, nodes, setEdges, debouncedSave]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setIsConfigOpen(true);
  }, []);

  const onEdgeClick = useCallback(
    (event: React.MouseEvent, edge: Edge) => {
      const newEdges = edges.filter((e) => e.id !== edge.id);
      setEdges(newEdges);
      debouncedSave({ nodes, edges: newEdges });
      toast.success('Connection removed');
    },
    [edges, nodes, setEdges, debouncedSave]
  );

  // ============================================
  // Node Management
  // ============================================

  const addNode = useCallback(
    (template: typeof nodeTemplates[0]) => {
      // Use smart positioning
      const defaultPosition = { x: 150, y: 100 };
      const smartPosition = getSmartDropPosition(nodes, defaultPosition);

      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: 'workflowNode',
        position: smartPosition,
        data: {
          label: template.label,
          type: template.type,
          description: template.description,
          configured: false,
          estimatedTime: template.estimatedTime,
          group: template.category,
        },
      };
      const newNodes = [...nodes, newNode];
      setNodes(newNodes);
      debouncedSave({ nodes: newNodes, edges });
      toast.success(`Added ${template.label}`);
    },
    [nodes, edges, setNodes, debouncedSave]
  );

  const updateNodeConfig = useCallback(
    (nodeId: string, config: any) => {
      const newNodes = nodes.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              ...config,
              configured: true,
            },
          };
        }
        return node;
      });
      setNodes(newNodes);
      debouncedSave({ nodes: newNodes, edges });
      toast.success('Node configuration saved');
    },
    [nodes, edges, setNodes, debouncedSave]
  );

  const deleteNode = useCallback(
    (nodeId: string) => {
      const newNodes = nodes.filter((n) => n.id !== nodeId);
      const newEdges = edges.filter(
        (e) => e.source !== nodeId && e.target !== nodeId
      );
      setNodes(newNodes);
      setEdges(newEdges);
      debouncedSave({ nodes: newNodes, edges: newEdges });
      setIsConfigOpen(false);
      setSelectedNode(null);
      toast.success('Node deleted');
    },
    [nodes, edges, setNodes, setEdges, debouncedSave]
  );

  // ============================================
  // Toolbar Actions
  // ============================================

  const handleSave = () => {
    if (!workflowId) return;

    updateWorkflow(
      {
        id: workflowId,
        data: {
          canvas_data: { nodes, edges },
        },
      },
      {
        onSuccess: () => toast.success('Workflow saved successfully!'),
        onError: (error: any) => toast.error(`Save failed: ${error.message}`),
      }
    );
  };

  const handleValidate = () => {
    if (!workflowId) return;

    validate(workflowId, {
      onSuccess: (result) => {
        setIsValidationOpen(true);
        if (result.is_valid) {
          toast.success('Validation passed! ✓');
        } else {
          toast.error(`Validation failed: ${result.errors.length} errors`);
        }
      },
      onError: (error: any) => {
        toast.error(`Validation failed: ${error.message}`);
      },
    });
  };

  const handleExecute = () => {
    if (!workflowId) return;

    // Validate first
    validate(workflowId, {
      onSuccess: (result) => {
        if (result.is_valid) {
          // Execute workflow
          execute(
            { workflowId },
            {
              onSuccess: (execution) => {
                toast.success('Workflow execution started!');
                setExecutionProgress(0);
                // Navigate to executions page or show progress
                // navigate(`/workflows/${workflowId}/executions`);
              },
              onError: (error: any) => {
                toast.error(`Execution failed: ${error.message}`);
              },
            }
          );
        } else {
          toast.error('Fix validation errors before running');
          setIsValidationOpen(true);
        }
      },
    });
  };

  const handleExport = () => {
    if (!workflow) return;

    const data = {
      name: workflow.name,
      description: workflow.description,
      nodes,
      edges,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflow.name}.json`;
    a.click();
    URL.revokeObjectURL(url);

    toast.success('Workflow exported');
  };

  /**
   * Handle Auto-Layout with Dagre algorithm
   */
  const handleAutoLayout = useCallback(() => {
    if (nodes.length === 0) {
      toast.error('No nodes to arrange');
      return;
    }

    setIsLayouting(true);

    try {
      // Apply Dagre layout
      const layoutedNodes = getLayoutedElements(nodes, edges, {
        direction: layoutDirection,
        nodeWidth: 200,
        nodeHeight: 80,
        nodeSeparation: 50,
        rankSeparation: 100,
      });

      setNodes(layoutedNodes);
      debouncedSave({ nodes: layoutedNodes, edges });

      // Fit view with animation after layout
      setTimeout(() => {
        if (reactFlowInstance.current) {
          reactFlowInstance.current.fitView({
            padding: 0.2,
            duration: 500,
            maxZoom: 1.5,
          });
        }
        setIsLayouting(false);
      }, 50);

      toast.success('Layout applied successfully');
    } catch (error) {
      console.error('Auto-layout failed:', error);
      toast.error('Layout failed - check console for details');
      setIsLayouting(false);
    }
  }, [nodes, edges, layoutDirection, setNodes, debouncedSave]);

  // ============================================
  // Loading & Error States
  // ============================================

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">Loading workflow...</div>
          <Progress value={undefined} className="w-64" />
        </div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Workflow not found</h2>
          <p className="text-muted-foreground mb-4">
            The workflow you're looking for doesn't exist or has been deleted.
          </p>
          <Button onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>
      </div>
    );
  }

  // ============================================
  // Render
  // ============================================

  return (
    <div className="h-screen flex flex-col max-w-[1920px] mx-auto">
      {/* Toolbar */}
      <WorkflowToolbar
        workflow={workflow}
        validationResult={validationResult}
        isExecuting={isExecuting}
        executionProgress={executionProgress}
        activeTab={activeTab}
        layoutDirection={layoutDirection}
        isLayouting={isLayouting}
        nodesCount={nodes.length}
        onBack={onBack}
        onValidate={handleValidate}
        onAutoLayout={handleAutoLayout}
        onExport={handleExport}
        onSave={handleSave}
        onExecute={handleExecute}
        onLayoutDirectionChange={setLayoutDirection}
      />

      {/* Main Content - Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as 'canvas' | 'history')}
        className="flex-1 flex flex-col overflow-hidden"
      >
        {/* Tabs Navigation */}
        <div className="px-4 pt-3 border-b border-border bg-background">
          <TabsList>
            <TabsTrigger value="canvas">
              <Layers className="w-4 h-4 mr-2" />
              Canvas
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="w-4 h-4 mr-2" />
              Historia
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Canvas Tab */}
        <TabsContent value="canvas" className="flex-1 flex overflow-hidden m-0">
          <WorkflowCanvas
            nodes={nodes}
            edges={edges}
            selectedNode={selectedNode}
            isConfigOpen={isConfigOpen}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onAddNode={addNode}
            onUpdateNodeConfig={updateNodeConfig}
            onDeleteNode={deleteNode}
            onCloseConfig={() => {
              setIsConfigOpen(false);
              setSelectedNode(null);
            }}
            onInit={(instance) => {
              reactFlowInstance.current = instance;
            }}
          />
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="flex-1 overflow-hidden m-0">
          <ExecutionHistory workflowId={workflowId} />
        </TabsContent>
      </Tabs>

      {/* Validation Dialog */}
      <ValidationDialog
        open={isValidationOpen}
        onOpenChange={setIsValidationOpen}
        validationResult={validationResult}
        onExecute={handleExecute}
      />

      {/* Save Dialog */}
      <SaveWorkflowDialog
        open={isSaveDialogOpen}
        onOpenChange={setIsSaveDialogOpen}
        workflow={workflow}
        onSave={handleSave}
      />
    </div>
  );
}
