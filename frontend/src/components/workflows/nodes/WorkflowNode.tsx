/**
 * WorkflowNode - Custom node component dla React Flow
 *
 * Wyświetla node z:
 * - Icon według typu (persona, survey, focus-group, etc.)
 * - Status badge (configured/not configured)
 * - Execution status (running/completed/error)
 * - Group badge
 * - Estimated time
 * - Multi-directional handles (top, bottom, left, right)
 *
 * @example
 * // Registered in nodeTypes
 * const nodeTypes = {
 *   workflowNode: WorkflowNode
 * };
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import {
  Users,
  MessageSquare,
  FileText,
  Brain,
  BarChart3,
  Target,
  GitBranch,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface WorkflowNodeData {
  label: string;
  type: string;
  description?: string;
  configured?: boolean;
  executionStatus?: 'running' | 'completed' | 'error';
  estimatedTime?: string;
  group?: string;
}

interface WorkflowNodeProps {
  data: WorkflowNodeData;
  selected: boolean;
}

/**
 * Get icon component based on node type
 */
function getIcon(type: string) {
  switch (type) {
    case 'persona':
      return <Users className="w-5 h-5" />;
    case 'survey':
      return <FileText className="w-5 h-5" />;
    case 'focus-group':
      return <MessageSquare className="w-5 h-5" />;
    case 'analysis':
      return <Brain className="w-5 h-5" />;
    case 'insights':
      return <BarChart3 className="w-5 h-5" />;
    case 'goal':
      return <Target className="w-5 h-5" />;
    case 'decision':
      return <GitBranch className="w-5 h-5" />;
    default:
      return <Target className="w-5 h-5" />;
  }
}

/**
 * Get color classes based on node type
 */
function getColorClasses(type: string) {
  switch (type) {
    case 'persona':
      return 'bg-chart-1/10 border-chart-1';
    case 'survey':
      return 'bg-chart-2/10 border-chart-2';
    case 'focus-group':
      return 'bg-chart-3/10 border-chart-3';
    case 'analysis':
      return 'bg-brand-orange/10 border-brand-orange';
    case 'insights':
      return 'bg-brand-gold/10 border-brand-gold';
    case 'goal':
      return 'bg-chart-4/10 border-chart-4';
    case 'decision':
      return 'bg-chart-5/10 border-chart-5';
    default:
      return 'bg-muted border-border';
  }
}

/**
 * Get execution status ring classes
 */
function getExecutionStatusClasses(status?: string) {
  switch (status) {
    case 'running':
      return 'ring-2 ring-brand-orange animate-pulse';
    case 'completed':
      return 'ring-2 ring-green-500';
    case 'error':
      return 'ring-2 ring-destructive';
    default:
      return '';
  }
}

/**
 * WorkflowNode Component
 */
export const WorkflowNode = memo(({ data, selected }: WorkflowNodeProps) => {
  const colorClasses = getColorClasses(data.type);
  const executionClasses = getExecutionStatusClasses(data.executionStatus);

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-card shadow-lg min-w-[200px] transition-all relative
        ${colorClasses}
        ${selected ? 'ring-2 ring-brand-orange ring-offset-2' : ''}
        ${executionClasses}
      `}
    >
      {/* Group Badge */}
      {data.group && (
        <div className="absolute -top-2 -left-2">
          <Badge variant="outline" className="text-xs bg-background">
            {data.group}
          </Badge>
        </div>
      )}

      {/* Input Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-brand-orange border-2 border-white hover:scale-125 transition-transform cursor-crosshair"
        style={{ top: -6 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-brand-orange border-2 border-white hover:scale-125 transition-transform cursor-crosshair"
        style={{ left: -6 }}
      />

      {/* Content */}
      <div className="flex items-center gap-2 mb-2">
        <div className="text-foreground">{getIcon(data.type)}</div>
        <div className="text-foreground font-medium">{data.label}</div>
      </div>

      {data.description && (
        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
          {data.description}
        </p>
      )}

      {/* Status Badges */}
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {data.configured ? (
          <Badge
            variant="outline"
            className="text-xs border-green-500/30 text-green-600 bg-green-500/5"
          >
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Configured
          </Badge>
        ) : (
          <Badge
            variant="outline"
            className="text-xs border-orange-500/30 text-orange-600 bg-orange-500/5"
          >
            <AlertCircle className="w-3 h-3 mr-1" />
            Not Set
          </Badge>
        )}

        {data.executionStatus === 'running' && (
          <Badge className="text-xs bg-brand-orange text-white">Running</Badge>
        )}

        {data.executionStatus === 'completed' && (
          <Badge className="text-xs bg-green-500 text-white">Done</Badge>
        )}

        {data.executionStatus === 'error' && (
          <Badge className="text-xs bg-destructive text-white">Error</Badge>
        )}

        {data.estimatedTime && (
          <Badge variant="outline" className="text-xs">
            ~{data.estimatedTime}
          </Badge>
        )}
      </div>

      {/* Output Handles */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-brand-orange border-2 border-white hover:scale-125 transition-transform cursor-crosshair"
        style={{ bottom: -6 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-brand-orange border-2 border-white hover:scale-125 transition-transform cursor-crosshair"
        style={{ right: -6 }}
      />
    </div>
  );
});

WorkflowNode.displayName = 'WorkflowNode';
