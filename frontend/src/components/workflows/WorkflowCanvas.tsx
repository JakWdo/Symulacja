/**
 * WorkflowCanvas - Canvas React Flow z node'ami i edge'ami
 *
 * Zawiera:
 * - NodeTemplatesSidebar (lewy sidebar z templates)
 * - ReactFlow canvas (środek)
 * - PropertyPanel (prawy panel konfiguracji node)
 * - Background, Controls, MiniMap
 *
 * @example
 * <WorkflowCanvas
 *   nodes={nodes}
 *   edges={edges}
 *   selectedNode={selectedNode}
 *   isConfigOpen={isConfigOpen}
 *   onNodesChange={handleNodesChange}
 *   onEdgesChange={handleEdgesChange}
 *   onConnect={onConnect}
 *   onNodeClick={onNodeClick}
 *   onEdgeClick={onEdgeClick}
 *   onAddNode={addNode}
 *   onUpdateNodeConfig={updateNodeConfig}
 *   onDeleteNode={deleteNode}
 *   onCloseConfig={() => setIsConfigOpen(false)}
 *   onInit={(instance) => setReactFlowInstance(instance)}
 * />
 */

import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  BackgroundVariant,
  NodeTypes,
  ReactFlowInstance,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { WorkflowNode } from './nodes/WorkflowNode';
import { PropertyPanel } from './PropertyPanel';
import { NodeTemplatesSidebar } from './NodeTemplatesSidebar';
import { NodeTemplate } from './nodeTemplates';

// Register custom node types
const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNode,
};

interface WorkflowCanvasProps {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  isConfigOpen: boolean;
  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: any) => void;
  onNodeClick: (event: React.MouseEvent, node: Node) => void;
  onEdgeClick: (event: React.MouseEvent, edge: Edge) => void;
  onAddNode: (template: NodeTemplate) => void;
  onUpdateNodeConfig: (nodeId: string, config: any) => void;
  onDeleteNode: (nodeId: string) => void;
  onCloseConfig: () => void;
  onInit?: (instance: ReactFlowInstance) => void;
}

/**
 * WorkflowCanvas Component
 */
export function WorkflowCanvas({
  nodes,
  edges,
  selectedNode,
  isConfigOpen,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodeClick,
  onEdgeClick,
  onAddNode,
  onUpdateNodeConfig,
  onDeleteNode,
  onCloseConfig,
  onInit,
}: WorkflowCanvasProps) {
  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Left Sidebar - Node Templates */}
      <NodeTemplatesSidebar onAddNode={onAddNode} />

      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onInit={onInit}
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
          onClose={onCloseConfig}
          onUpdate={(config) => {
            if (selectedNode) {
              onUpdateNodeConfig(selectedNode.id, config);
            }
          }}
          onDelete={() => {
            if (selectedNode) {
              onDeleteNode(selectedNode.id);
            }
          }}
        />
      )}
    </div>
  );
}
