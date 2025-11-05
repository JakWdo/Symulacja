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
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
  MarkerType,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
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
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  Layers,
  Pause,
  Play,
  Save,
  History,
  Sparkles,
} from 'lucide-react';

import { WorkflowNode } from './nodes/WorkflowNode';
import { PropertyPanel } from './PropertyPanel';
import { NodeTemplatesSidebar } from './NodeTemplatesSidebar';
import { ValidationDialog } from './ValidationDialog';
import { SaveWorkflowDialog } from './SaveWorkflowDialog';
import { ExecutionHistory } from './ExecutionHistory';
import { nodeTemplates } from './nodeTemplates';
import {
  getLayoutedElements,
  hasDefaultPositions,
  LayoutDirection,
} from './utils/autoLayout';
import { getSmartDropPosition } from './utils/smartPositioning';

// Register custom node types
const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNode,
};

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
      {/* Top Bar */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-background">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
          >
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
              <Button variant="outline" size="sm" onClick={handleValidate}>
                <AlertCircle className="w-4 h-4 mr-2" />
                Validate
              </Button>

              {/* Layout Direction Selector */}
              <Select
                value={layoutDirection}
                onValueChange={(value) => setLayoutDirection(value as LayoutDirection)}
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
                      onClick={handleAutoLayout}
                      disabled={isLayouting || nodes.length === 0}
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

              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm" onClick={handleSave}>
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
              onClick={handleExecute}
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
          <div className="flex-1 flex overflow-hidden">
            {/* Left Sidebar - Node Templates */}
            <NodeTemplatesSidebar onAddNode={addNode} />

            {/* Canvas */}
            <div className="flex-1 relative">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={handleNodesChange}
                onEdgesChange={handleEdgesChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                onEdgeClick={onEdgeClick}
                onInit={(instance) => {
                  reactFlowInstance.current = instance;
                }}
                nodeTypes={nodeTypes}
                fitView
                className="bg-background"
              >
                <Background
                  variant={BackgroundVariant.Dots}
                  gap={16}
                  size={1}
                  color="var(--border)"
                />
                <Controls className="bg-background border border-border" />
                <MiniMap
                  className="bg-background border border-border"
                  nodeColor={(node) => {
                    switch (node.data.type) {
                      case 'persona':
                        return 'var(--chart-1)';
                      case 'survey':
                        return 'var(--chart-2)';
                      case 'focus-group':
                        return 'var(--chart-3)';
                      case 'analysis':
                        return '#F27405';
                      case 'insights':
                        return '#F29F05';
                      case 'goal':
                        return 'var(--chart-4)';
                      default:
                        return 'var(--muted)';
                    }
                  }}
                />
              </ReactFlow>
            </div>

            {/* Right Sidebar - Property Panel */}
            {selectedNode && isConfigOpen && (
              <PropertyPanel
                node={selectedNode}
                onClose={() => {
                  setIsConfigOpen(false);
                  setSelectedNode(null);
                }}
                onUpdate={(config) => {
                  if (selectedNode) {
                    updateNodeConfig(selectedNode.id, config);
                  }
                }}
                onDelete={() => {
                  if (selectedNode) {
                    deleteNode(selectedNode.id);
                  }
                }}
              />
            )}
          </div>
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
