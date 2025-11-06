import { useState, useCallback, useEffect } from 'react';
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
  Handle,
  Position,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Plus, Play, Save, Users, MessageSquare, FileText, Brain, BarChart3, Target, Trash2, FolderOpen, Sparkles, AlertCircle, CheckCircle2, ArrowLeft, Copy, Download, GitBranch, Layers, Settings as SettingsIcon, Pause, FastForward, RotateCw } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner@2.0.3';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Slider } from './ui/slider';
import { Switch } from './ui/switch';
import { Separator } from './ui/separator';
import { Progress } from './ui/progress';
import { ScrollArea } from './ui/scroll-area';

// Custom Node Component
function WorkflowNode({ data, selected }: { data: any; selected: boolean }) {
  const getIcon = () => {
    switch (data.type) {
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
  };

  const getColor = () => {
    switch (data.type) {
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
  };

  const getExecutionColor = () => {
    switch (data.executionStatus) {
      case 'running':
        return 'ring-2 ring-brand-orange animate-pulse';
      case 'completed':
        return 'ring-2 ring-green-500';
      case 'error':
        return 'ring-2 ring-destructive';
      default:
        return '';
    }
  };

  return (
    <div className={`px-4 py-3 rounded-lg border-2 ${getColor()} ${selected ? 'ring-2 ring-brand-orange ring-offset-2' : ''} ${getExecutionColor()} bg-card shadow-lg min-w-[200px] transition-all relative`}>
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
      
      <div className="flex items-center gap-2 mb-2">
        <div className="text-foreground">{getIcon()}</div>
        <div className="text-foreground">{data.label}</div>
      </div>
      {data.description && (
        <p className="text-xs text-muted-foreground mt-1">{data.description}</p>
      )}
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {data.configured ? (
          <Badge variant="outline" className="text-xs border-green-500/30 text-green-600 bg-green-500/5">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Configured
          </Badge>
        ) : (
          <Badge variant="outline" className="text-xs border-orange-500/30 text-orange-600 bg-orange-500/5">
            <AlertCircle className="w-3 h-3 mr-1" />
            Not Set
          </Badge>
        )}
        {data.executionStatus === 'running' && (
          <Badge className="text-xs bg-brand-orange text-white">
            Running
          </Badge>
        )}
        {data.executionStatus === 'completed' && (
          <Badge className="text-xs bg-green-500 text-white">
            Done
          </Badge>
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
}

const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNode,
};

interface NodeTemplate {
  type: string;
  label: string;
  description: string;
  icon: any;
  estimatedTime?: string;
  category?: string;
}

const nodeTemplates: NodeTemplate[] = [
  { type: 'goal', label: 'Research Goal', description: 'Define objectives', icon: Target, estimatedTime: '15m', category: 'Planning' },
  { type: 'persona', label: 'Generate Personas', description: 'AI persona generation', icon: Users, estimatedTime: '30m', category: 'Data Collection' },
  { type: 'survey', label: 'Survey', description: 'Create survey', icon: FileText, estimatedTime: '2h', category: 'Data Collection' },
  { type: 'focus-group', label: 'Focus Group', description: 'Run discussion', icon: MessageSquare, estimatedTime: '90m', category: 'Data Collection' },
  { type: 'analysis', label: 'AI Analysis', description: 'Analyze results', icon: Brain, estimatedTime: '45m', category: 'Analysis' },
  { type: 'insights', label: 'Insights', description: 'Generate insights', icon: BarChart3, estimatedTime: '20m', category: 'Analysis' },
  { type: 'decision', label: 'Decision Point', description: 'Conditional logic', icon: GitBranch, estimatedTime: '5m', category: 'Logic' },
];

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  category?: string;
}

const workflowTemplates: WorkflowTemplate[] = [
  {
    id: 'product-research',
    name: 'Product Research Flow',
    description: 'Complete product research workflow with personas, surveys, and analysis',
    category: 'Product',
    nodes: [
      {
        id: '1',
        type: 'workflowNode',
        position: { x: 250, y: 50 },
        data: { label: 'Research Goal', type: 'goal', description: 'Define product research objectives', configured: false, group: 'Planning', estimatedTime: '15m' },
      },
      {
        id: '2',
        type: 'workflowNode',
        position: { x: 250, y: 170 },
        data: { label: 'Generate Personas', type: 'persona', description: 'Create target user personas', configured: false, group: 'Data Collection', estimatedTime: '30m' },
      },
      {
        id: '3',
        type: 'workflowNode',
        position: { x: 100, y: 290 },
        data: { label: 'Survey', type: 'survey', description: 'Collect quantitative data', configured: false, group: 'Data Collection', estimatedTime: '2h' },
      },
      {
        id: '4',
        type: 'workflowNode',
        position: { x: 400, y: 290 },
        data: { label: 'Focus Group', type: 'focus-group', description: 'Gather qualitative insights', configured: false, group: 'Data Collection', estimatedTime: '90m' },
      },
      {
        id: '5',
        type: 'workflowNode',
        position: { x: 250, y: 410 },
        data: { label: 'AI Analysis', type: 'analysis', description: 'Analyze all data', configured: false, group: 'Analysis', estimatedTime: '45m' },
      },
      {
        id: '6',
        type: 'workflowNode',
        position: { x: 250, y: 530 },
        data: { label: 'Insights Report', type: 'insights', description: 'Generate final insights', configured: false, group: 'Analysis', estimatedTime: '20m' },
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-4', source: '2', target: '4', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e3-5', source: '3', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e4-5', source: '4', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e5-6', source: '5', target: '6', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
    ],
  },
  {
    id: 'quick-survey',
    name: 'Quick Survey Flow',
    description: 'Simple survey-based research workflow',
    category: 'Survey',
    nodes: [
      {
        id: '1',
        type: 'workflowNode',
        position: { x: 250, y: 100 },
        data: { label: 'Research Goal', type: 'goal', description: 'Define survey objectives', configured: false, group: 'Planning', estimatedTime: '15m' },
      },
      {
        id: '2',
        type: 'workflowNode',
        position: { x: 250, y: 220 },
        data: { label: 'Survey', type: 'survey', description: 'Create and distribute survey', configured: false, group: 'Data Collection', estimatedTime: '2h' },
      },
      {
        id: '3',
        type: 'workflowNode',
        position: { x: 250, y: 340 },
        data: { label: 'AI Analysis', type: 'analysis', description: 'Analyze responses', configured: false, group: 'Analysis', estimatedTime: '45m' },
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
    ],
  },
  {
    id: 'brand-perception',
    name: 'Brand Perception Study',
    description: 'Understand how customers perceive your brand',
    category: 'Brand',
    nodes: [
      {
        id: '1',
        type: 'workflowNode',
        position: { x: 250, y: 50 },
        data: { label: 'Brand Goals', type: 'goal', description: 'Define brand perception goals', configured: false, group: 'Planning', estimatedTime: '15m' },
      },
      {
        id: '2',
        type: 'workflowNode',
        position: { x: 250, y: 170 },
        data: { label: 'Target Personas', type: 'persona', description: 'Identify target audience', configured: false, group: 'Data Collection', estimatedTime: '30m' },
      },
      {
        id: '3',
        type: 'workflowNode',
        position: { x: 250, y: 290 },
        data: { label: 'Focus Group', type: 'focus-group', description: 'Brand perception discussion', configured: false, group: 'Data Collection', estimatedTime: '90m' },
      },
      {
        id: '4',
        type: 'workflowNode',
        position: { x: 250, y: 410 },
        data: { label: 'Sentiment Analysis', type: 'analysis', description: 'Analyze brand sentiment', configured: false, group: 'Analysis', estimatedTime: '45m' },
      },
      {
        id: '5',
        type: 'workflowNode',
        position: { x: 250, y: 530 },
        data: { label: 'Brand Insights', type: 'insights', description: 'Key perception findings', configured: false, group: 'Analysis', estimatedTime: '20m' },
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e3-4', source: '3', target: '4', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e4-5', source: '4', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
    ],
  },
  {
    id: 'user-journey',
    name: 'User Journey Mapping',
    description: 'Map and optimize user experience journey',
    category: 'UX',
    nodes: [
      {
        id: '1',
        type: 'workflowNode',
        position: { x: 250, y: 50 },
        data: { label: 'Journey Goals', type: 'goal', description: 'Define UX objectives', configured: false, group: 'Planning', estimatedTime: '15m' },
      },
      {
        id: '2',
        type: 'workflowNode',
        position: { x: 250, y: 170 },
        data: { label: 'User Personas', type: 'persona', description: 'Create user profiles', configured: false, group: 'Data Collection', estimatedTime: '30m' },
      },
      {
        id: '3',
        type: 'workflowNode',
        position: { x: 100, y: 290 },
        data: { label: 'Behavior Survey', type: 'survey', description: 'Collect usage patterns', configured: false, group: 'Data Collection', estimatedTime: '2h' },
      },
      {
        id: '4',
        type: 'workflowNode',
        position: { x: 400, y: 290 },
        data: { label: 'UX Focus Group', type: 'focus-group', description: 'Discuss pain points', configured: false, group: 'Data Collection', estimatedTime: '90m' },
      },
      {
        id: '5',
        type: 'workflowNode',
        position: { x: 250, y: 410 },
        data: { label: 'Journey Analysis', type: 'analysis', description: 'Map user journey', configured: false, group: 'Analysis', estimatedTime: '45m' },
      },
      {
        id: '6',
        type: 'workflowNode',
        position: { x: 250, y: 530 },
        data: { label: 'UX Insights', type: 'insights', description: 'Optimization recommendations', configured: false, group: 'Analysis', estimatedTime: '20m' },
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-4', source: '2', target: '4', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e3-5', source: '3', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e4-5', source: '4', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e5-6', source: '5', target: '6', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
    ],
  },
  {
    id: 'competitive-analysis',
    name: 'Competitive Analysis',
    description: 'Analyze competitors and market positioning',
    category: 'Market',
    nodes: [
      {
        id: '1',
        type: 'workflowNode',
        position: { x: 250, y: 50 },
        data: { label: 'Market Goals', type: 'goal', description: 'Define competitive goals', configured: false, group: 'Planning', estimatedTime: '15m' },
      },
      {
        id: '2',
        type: 'workflowNode',
        position: { x: 250, y: 170 },
        data: { label: 'Market Personas', type: 'persona', description: 'Identify market segments', configured: false, group: 'Data Collection', estimatedTime: '30m' },
      },
      {
        id: '3',
        type: 'workflowNode',
        position: { x: 250, y: 290 },
        data: { label: 'Competitor Survey', type: 'survey', description: 'Compare features & pricing', configured: false, group: 'Data Collection', estimatedTime: '2h' },
      },
      {
        id: '4',
        type: 'workflowNode',
        position: { x: 250, y: 410 },
        data: { label: 'Market Analysis', type: 'analysis', description: 'Analyze positioning', configured: false, group: 'Analysis', estimatedTime: '45m' },
      },
      {
        id: '5',
        type: 'workflowNode',
        position: { x: 250, y: 530 },
        data: { label: 'Strategy Insights', type: 'insights', description: 'Competitive advantages', configured: false, group: 'Analysis', estimatedTime: '20m' },
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e3-4', source: '3', target: '4', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e4-5', source: '4', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
    ],
  },
  {
    id: 'feature-prioritization',
    name: 'Feature Prioritization',
    description: 'Prioritize product features based on user feedback',
    category: 'Product',
    nodes: [
      {
        id: '1',
        type: 'workflowNode',
        position: { x: 250, y: 50 },
        data: { label: 'Feature Goals', type: 'goal', description: 'Define feature objectives', configured: false, group: 'Planning', estimatedTime: '15m' },
      },
      {
        id: '2',
        type: 'workflowNode',
        position: { x: 250, y: 170 },
        data: { label: 'User Personas', type: 'persona', description: 'Target user segments', configured: false, group: 'Data Collection', estimatedTime: '30m' },
      },
      {
        id: '3',
        type: 'workflowNode',
        position: { x: 100, y: 290 },
        data: { label: 'Feature Survey', type: 'survey', description: 'Rate feature importance', configured: false, group: 'Data Collection', estimatedTime: '2h' },
      },
      {
        id: '4',
        type: 'workflowNode',
        position: { x: 400, y: 290 },
        data: { label: 'Feature Discussion', type: 'focus-group', description: 'Deep dive on needs', configured: false, group: 'Data Collection', estimatedTime: '90m' },
      },
      {
        id: '5',
        type: 'workflowNode',
        position: { x: 250, y: 410 },
        data: { label: 'Priority Analysis', type: 'analysis', description: 'Rank features', configured: false, group: 'Analysis', estimatedTime: '45m' },
      },
      {
        id: '6',
        type: 'workflowNode',
        position: { x: 250, y: 530 },
        data: { label: 'Roadmap Insights', type: 'insights', description: 'Feature roadmap', configured: false, group: 'Analysis', estimatedTime: '20m' },
      },
    ],
    edges: [
      { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e2-4', source: '2', target: '4', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e3-5', source: '3', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e4-5', source: '4', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
      { id: 'e5-6', source: '5', target: '6', markerEnd: { type: MarkerType.ArrowClosed, color: '#F27405' }, style: { strokeWidth: 2, stroke: '#F27405' } },
    ],
  },
];

interface SavedWorkflow {
  id: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  createdAt: string;
  updatedAt: string;
}

interface ValidationIssue {
  type: 'error' | 'warning' | 'info';
  message: string;
  nodeIds?: string[];
}

export function Workflow() {
  const [viewMode, setViewMode] = useState<'list' | 'canvas'>('list');
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [nodeConfig, setNodeConfig] = useState<any>({ label: '', description: '' });
  const [savedWorkflows, setSavedWorkflows] = useState<SavedWorkflow[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<SavedWorkflow | null>(null);
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [isTemplateDialogOpen, setIsTemplateDialogOpen] = useState(false);
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);
  const [isValidationOpen, setIsValidationOpen] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [currentExecutingNodeIndex, setCurrentExecutingNodeIndex] = useState(-1);
  const [showConfigPanel, setShowConfigPanel] = useState(true);

  // Load saved workflows from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sight-workflows');
    if (saved) {
      setSavedWorkflows(JSON.parse(saved));
    }
  }, []);

  // Auto-validate when nodes or edges change
  useEffect(() => {
    if (nodes.length > 0 || edges.length > 0) {
      validateWorkflow();
    }
  }, [nodes, edges]);

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
      setEdges((eds) => addEdge(edge, eds));
      toast.success('Activities connected');
    },
    [setEdges]
  );

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    setEdges((eds) => eds.filter((e) => e.id !== edge.id));
    toast.success('Connection removed');
  }, [setEdges]);

  const addNode = (template: NodeTemplate) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'workflowNode',
      position: { 
        x: Math.random() * 400 + 150, 
        y: Math.random() * 300 + 100 
      },
      data: { 
        label: template.label,
        type: template.type,
        description: template.description,
        configured: false,
        estimatedTime: template.estimatedTime,
        group: template.category,
      },
    };
    setNodes((nds) => [...nds, newNode]);
    toast.success(`Added ${template.label}`);
  };

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setNodeConfig({
      label: node.data.label,
      description: node.data.description || '',
      group: node.data.group || '',
      estimatedTime: node.data.estimatedTime || '',
      ...node.data.config || {}
    });
    setIsConfigOpen(true);
  }, []);

  const saveNodeConfig = () => {
    if (selectedNode) {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === selectedNode.id) {
            return {
              ...node,
              data: {
                ...node.data,
                label: nodeConfig.label,
                description: nodeConfig.description,
                group: nodeConfig.group,
                estimatedTime: nodeConfig.estimatedTime,
                configured: true,
                config: nodeConfig,
              },
            };
          }
          return node;
        })
      );
      toast.success('Node configuration saved');
    }
    setIsConfigOpen(false);
    setSelectedNode(null);
  };

  const deleteSelectedNode = () => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
      setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id));
      setIsConfigOpen(false);
      setSelectedNode(null);
      toast.success('Node deleted');
    }
  };

  const saveWorkflow = () => {
    if (!workflowName.trim()) {
      toast.error('Please enter a workflow name');
      return;
    }

    const workflow: SavedWorkflow = {
      id: currentWorkflow?.id || `workflow-${Date.now()}`,
      name: workflowName,
      description: workflowDescription,
      nodes,
      edges,
      createdAt: currentWorkflow?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const updatedWorkflows = currentWorkflow
      ? savedWorkflows.map((w) => (w.id === currentWorkflow.id ? workflow : w))
      : [...savedWorkflows, workflow];

    setSavedWorkflows(updatedWorkflows);
    localStorage.setItem('sight-workflows', JSON.stringify(updatedWorkflows));
    setCurrentWorkflow(workflow);
    setIsSaveDialogOpen(false);
    toast.success(currentWorkflow ? 'Workflow updated' : 'Workflow saved');
  };

  const loadWorkflow = (workflow: SavedWorkflow) => {
    setNodes(workflow.nodes);
    setEdges(workflow.edges);
    setCurrentWorkflow(workflow);
    setWorkflowName(workflow.name);
    setWorkflowDescription(workflow.description);
    setViewMode('canvas');
    toast.success('Workflow loaded');
  };

  const loadTemplate = (template: WorkflowTemplate) => {
    setNodes(template.nodes);
    setEdges(template.edges);
    setCurrentWorkflow(null);
    setWorkflowName(template.name);
    setWorkflowDescription(template.description);
    setIsTemplateDialogOpen(false);
    setViewMode('canvas');
    toast.success('Template loaded');
  };

  const createNewWorkflow = () => {
    setNodes([]);
    setEdges([]);
    setCurrentWorkflow(null);
    setWorkflowName('');
    setWorkflowDescription('');
    setViewMode('canvas');
  };

  const deleteWorkflow = (id: string) => {
    const updatedWorkflows = savedWorkflows.filter((w) => w.id !== id);
    setSavedWorkflows(updatedWorkflows);
    localStorage.setItem('sight-workflows', JSON.stringify(updatedWorkflows));
    toast.success('Workflow deleted');
  };

  const duplicateWorkflow = (workflow: SavedWorkflow) => {
    const duplicate: SavedWorkflow = {
      ...workflow,
      id: `workflow-${Date.now()}`,
      name: `${workflow.name} (Copy)`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    const updatedWorkflows = [...savedWorkflows, duplicate];
    setSavedWorkflows(updatedWorkflows);
    localStorage.setItem('sight-workflows', JSON.stringify(updatedWorkflows));
    toast.success('Workflow duplicated');
  };

  const validateWorkflow = () => {
    const issues: ValidationIssue[] = [];
    
    if (nodes.length === 0) {
      issues.push({ type: 'info', message: 'No activities in workflow. Add activities to get started.' });
      setValidationIssues(issues);
      return issues;
    }
    
    // Check for unconfigured nodes
    const unconfigured = nodes.filter(n => !n.data.configured);
    if (unconfigured.length > 0) {
      issues.push({ 
        type: 'warning', 
        message: `${unconfigured.length} activity(ies) not configured`,
        nodeIds: unconfigured.map(n => n.id)
      });
    }
    
    // Check for disconnected nodes
    const disconnected = nodes.filter(n => {
      const hasConnection = edges.some(e => e.source === n.id || e.target === n.id);
      return !hasConnection && nodes.length > 1;
    });
    if (disconnected.length > 0) {
      issues.push({ 
        type: 'warning', 
        message: `${disconnected.length} activity(ies) not connected`,
        nodeIds: disconnected.map(n => n.id)
      });
    }

    // Check for goal node
    const hasGoal = nodes.some(n => n.data.type === 'goal');
    if (!hasGoal) {
      issues.push({ 
        type: 'warning', 
        message: 'No research goal defined. Consider adding a goal node.'
      });
    }

    // Check for insights/analysis
    const hasInsights = nodes.some(n => n.data.type === 'insights' || n.data.type === 'analysis');
    if (!hasInsights && nodes.length > 2) {
      issues.push({ 
        type: 'info', 
        message: 'No analysis or insights step. Consider adding to maximize value.'
      });
    }

    // Check workflow flow (no cycles, proper connections)
    const hasStart = nodes.some(n => {
      const incomingEdges = edges.filter(e => e.target === n.id);
      return incomingEdges.length === 0;
    });
    
    if (!hasStart && nodes.length > 1) {
      issues.push({
        type: 'error',
        message: 'No starting point. All activities have incoming connections (possible cycle).'
      });
    }

    const hasEnd = nodes.some(n => {
      const outgoingEdges = edges.filter(e => e.source === n.id);
      return outgoingEdges.length === 0;
    });

    if (!hasEnd && nodes.length > 1) {
      issues.push({
        type: 'error',
        message: 'No ending point. All activities have outgoing connections (possible cycle).'
      });
    }

    if (issues.length === 0) {
      issues.push({
        type: 'info',
        message: '✓ Workflow is valid and ready to execute!'
      });
    }

    setValidationIssues(issues);
    return issues;
  };

  const autoLayoutNodes = () => {
    if (nodes.length === 0) {
      toast.error('No nodes to arrange');
      return;
    }

    // Simple hierarchical layout
    // 1. Find root nodes (no incoming edges)
    const rootNodes = nodes.filter(node => 
      !edges.some(edge => edge.target === node.id)
    );

    // 2. Build layers using BFS
    const layers: string[][] = [];
    const visited = new Set<string>();
    const queue = [...rootNodes.map(n => n.id)];
    
    while (queue.length > 0) {
      const levelSize = queue.length;
      const currentLayer: string[] = [];
      
      for (let i = 0; i < levelSize; i++) {
        const nodeId = queue.shift()!;
        if (visited.has(nodeId)) continue;
        
        visited.add(nodeId);
        currentLayer.push(nodeId);
        
        // Add children to queue
        const children = edges
          .filter(e => e.source === nodeId)
          .map(e => e.target)
          .filter(id => !visited.has(id));
        queue.push(...children);
      }
      
      if (currentLayer.length > 0) {
        layers.push(currentLayer);
      }
    }

    // 3. Position nodes
    const horizontalSpacing = 300;
    const verticalSpacing = 120;
    const startX = 100;
    const startY = 50;

    const newNodes = nodes.map(node => {
      let layerIndex = -1;
      let positionInLayer = -1;

      for (let i = 0; i < layers.length; i++) {
        const pos = layers[i].indexOf(node.id);
        if (pos !== -1) {
          layerIndex = i;
          positionInLayer = pos;
          break;
        }
      }

      if (layerIndex === -1) {
        // Node not in any layer (disconnected), place it to the side
        return {
          ...node,
          position: {
            x: startX + horizontalSpacing * 3,
            y: startY + Math.random() * 200,
          },
        };
      }

      const layerWidth = layers[layerIndex].length;
      const totalWidth = layerWidth * horizontalSpacing;
      const offsetX = (positionInLayer - (layerWidth - 1) / 2) * horizontalSpacing;

      return {
        ...node,
        position: {
          x: startX + 250 + offsetX,
          y: startY + layerIndex * verticalSpacing,
        },
      };
    });

    setNodes(newNodes);
    toast.success('Nodes arranged automatically');
  };

  const executeWorkflow = async () => {
    const issues = validateWorkflow();
    const errors = issues.filter(i => i.type === 'error');
    
    if (errors.length > 0) {
      toast.error('Cannot execute workflow', {
        description: errors.map(e => e.message).join('. '),
      });
      setIsValidationOpen(true);
      return;
    }

    setIsExecuting(true);
    setExecutionProgress(0);
    setCurrentExecutingNodeIndex(0);

    // Reset all node execution statuses
    setNodes(nds => nds.map(n => ({
      ...n,
      data: { ...n.data, executionStatus: undefined }
    })));

    // Sort nodes topologically for execution order
    const rootNodes = nodes.filter(node => 
      !edges.some(edge => edge.target === node.id)
    );

    const executionOrder: string[] = [];
    const visited = new Set<string>();
    const queue = [...rootNodes.map(n => n.id)];

    while (queue.length > 0) {
      const nodeId = queue.shift()!;
      if (visited.has(nodeId)) continue;
      
      visited.add(nodeId);
      executionOrder.push(nodeId);
      
      const children = edges
        .filter(e => e.source === nodeId)
        .map(e => e.target)
        .filter(id => !visited.has(id));
      queue.push(...children);
    }

    // Execute nodes in order
    for (let i = 0; i < executionOrder.length; i++) {
      const nodeId = executionOrder[i];
      const node = nodes.find(n => n.id === nodeId);
      
      setCurrentExecutingNodeIndex(i);
      
      // Set node as running
      setNodes(nds => nds.map(n => 
        n.id === nodeId 
          ? { ...n, data: { ...n.data, executionStatus: 'running' } }
          : n
      ));

      // Simulate execution time
      const estimatedTime = node?.data.estimatedTime || '30m';
      const minutes = parseInt(estimatedTime);
      const delay = Math.min(minutes * 100, 2000); // Max 2 seconds per node
      
      await new Promise(resolve => setTimeout(resolve, delay));

      // Set node as completed
      setNodes(nds => nds.map(n => 
        n.id === nodeId 
          ? { ...n, data: { ...n.data, executionStatus: 'completed' } }
          : n
      ));

      setExecutionProgress(((i + 1) / executionOrder.length) * 100);
    }

    setIsExecuting(false);
    toast.success('Workflow execution completed!', {
      description: `Completed ${executionOrder.length} activities successfully.`,
    });
  };

  const stopExecution = () => {
    setIsExecuting(false);
    setExecutionProgress(0);
    setCurrentExecutingNodeIndex(-1);
    
    // Reset all execution statuses
    setNodes(nds => nds.map(n => ({
      ...n,
      data: { ...n.data, executionStatus: undefined }
    })));
    
    toast.info('Workflow execution stopped');
  };

  const exportWorkflow = () => {
    const data = {
      name: workflowName || 'Untitled Workflow',
      description: workflowDescription,
      nodes,
      edges,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName || 'workflow'}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success('Workflow exported');
  };

  const saveAsTemplate = () => {
    if (!workflowName.trim()) {
      toast.error('Please name your workflow before saving as template');
      return;
    }

    toast.success('Template saved', {
      description: 'Your workflow has been saved as a reusable template',
    });
  };

  if (viewMode === 'list') {
    return (
      <div className="h-screen flex flex-col max-w-[1920px] mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-foreground mb-2">Research Workflows</h1>
          <p className="text-muted-foreground">
            Design and manage your research workflows with AI-powered automation
          </p>
        </div>

        <Tabs defaultValue="workflows" className="flex-1">
          <TabsList className="mb-4">
            <TabsTrigger value="workflows">My Workflows</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="workflows" className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {savedWorkflows.length} workflow{savedWorkflows.length !== 1 ? 's' : ''}
              </p>
              <Button 
                onClick={createNewWorkflow}
                className="bg-brand-orange hover:bg-brand-orange/90 text-white gap-2"
              >
                <Plus className="w-4 h-4" />
                New Workflow
              </Button>
            </div>

            {savedWorkflows.length === 0 ? (
              <Card className="bg-card border border-border">
                <CardContent className="py-12 text-center">
                  <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-foreground mb-2">No workflows yet</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create your first workflow or start from a template
                  </p>
                  <div className="flex gap-2 justify-center">
                    <Button 
                      onClick={createNewWorkflow}
                      className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                    >
                      Create Workflow
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => setIsTemplateDialogOpen(true)}
                    >
                      Browse Templates
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedWorkflows.map((workflow) => (
                  <Card key={workflow.id} className="bg-card border border-border hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-foreground flex items-start justify-between">
                        <span>{workflow.name}</span>
                        <Badge variant="outline" className="ml-2 shrink-0">
                          {workflow.nodes.length} nodes
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
                        Updated {new Date(workflow.updatedAt).toLocaleDateString()}
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          onClick={() => loadWorkflow(workflow)}
                          size="sm"
                          className="flex-1 bg-brand-orange hover:bg-brand-orange/90 text-white"
                        >
                          Open
                        </Button>
                        <Button
                          onClick={() => duplicateWorkflow(workflow)}
                          size="sm"
                          variant="outline"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          onClick={() => deleteWorkflow(workflow.id)}
                          size="sm"
                          variant="outline"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <div className="mb-4">
              <p className="text-sm text-muted-foreground">
                {workflowTemplates.length} ready-to-use templates
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workflowTemplates.map((template) => (
                <Card key={template.id} className="bg-card border border-border hover:shadow-lg transition-shadow">
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
                      <span>{template.nodes.length} activities</span>
                    </div>
                    <Button 
                      onClick={() => loadTemplate(template)}
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
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col max-w-[1920px] mx-auto">
      {/* Top Bar */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-background">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setViewMode('list')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h2 className="text-foreground">{workflowName || 'Untitled Workflow'}</h2>
            {workflowDescription && (
              <p className="text-xs text-muted-foreground">{workflowDescription}</p>
            )}
          </div>
          {validationIssues.some(i => i.type === 'error') && (
            <Badge variant="outline" className="border-destructive text-destructive">
              {validationIssues.filter(i => i.type === 'error').length} errors
            </Badge>
          )}
          {validationIssues.some(i => i.type === 'warning') && (
            <Badge variant="outline" className="border-orange-500 text-orange-600">
              {validationIssues.filter(i => i.type === 'warning').length} warnings
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsValidationOpen(true)}
          >
            <AlertCircle className="w-4 h-4 mr-2" />
            Validate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={autoLayoutNodes}
          >
            <Layers className="w-4 h-4 mr-2" />
            Auto-Arrange
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportWorkflow}
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsSaveDialogOpen(true)}
          >
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>
          {isExecuting ? (
            <Button
              variant="outline"
              size="sm"
              onClick={stopExecution}
            >
              <Pause className="w-4 h-4 mr-2" />
              Stop
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={executeWorkflow}
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
            <span className="text-sm text-muted-foreground">{Math.round(executionProgress)}%</span>
          </div>
          <Progress value={executionProgress} className="h-2" />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Node Templates */}
        <div className="w-64 border-r border-border bg-background p-4 overflow-y-auto">
          <h3 className="text-sm text-foreground mb-4">Add Activities</h3>
          
          {['Planning', 'Data Collection', 'Analysis', 'Logic'].map(category => {
            const categoryNodes = nodeTemplates.filter(t => t.category === category);
            if (categoryNodes.length === 0) return null;
            
            return (
              <div key={category} className="mb-6">
                <p className="text-xs text-muted-foreground mb-2">{category}</p>
                <div className="space-y-2">
                  {categoryNodes.map((template) => (
                    <button
                      key={template.type}
                      onClick={() => addNode(template)}
                      className="w-full text-left px-3 py-2 rounded-lg border border-border bg-card hover:bg-accent transition-colors"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <template.icon className="w-4 h-4 text-foreground" />
                        <span className="text-sm text-foreground">{template.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{template.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

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
            nodeTypes={nodeTypes}
            fitView
            className="bg-background"
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="var(--border)" />
            <Controls className="bg-background border border-border" />
            <MiniMap 
              className="bg-background border border-border"
              nodeColor={(node) => {
                switch (node.data.type) {
                  case 'persona': return 'var(--chart-1)';
                  case 'survey': return 'var(--chart-2)';
                  case 'focus-group': return 'var(--chart-3)';
                  case 'analysis': return '#F27405';
                  case 'insights': return '#F29F05';
                  case 'goal': return 'var(--chart-4)';
                  default: return 'var(--muted)';
                }
              }}
            />
          </ReactFlow>
        </div>

        {/* Right Sidebar - Configuration Panel */}
        {showConfigPanel && selectedNode && isConfigOpen && (
          <div className="w-80 border-l border-border bg-background overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border">
              <h3 className="text-foreground">Configure Activity</h3>
            </div>
            
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="node-label">Activity Name</Label>
                  <Input
                    id="node-label"
                    value={nodeConfig.label}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, label: e.target.value })}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="node-description">Description</Label>
                  <Textarea
                    id="node-description"
                    value={nodeConfig.description}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, description: e.target.value })}
                    className="mt-1"
                    rows={3}
                  />
                </div>

                <div>
                  <Label htmlFor="node-group">Phase/Group</Label>
                  <Select
                    value={nodeConfig.group}
                    onValueChange={(value) => setNodeConfig({ ...nodeConfig, group: value })}
                  >
                    <SelectTrigger id="node-group" className="mt-1">
                      <SelectValue placeholder="Select phase" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Planning">Planning</SelectItem>
                      <SelectItem value="Data Collection">Data Collection</SelectItem>
                      <SelectItem value="Analysis">Analysis</SelectItem>
                      <SelectItem value="Reporting">Reporting</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="node-time">Estimated Time</Label>
                  <Input
                    id="node-time"
                    value={nodeConfig.estimatedTime}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, estimatedTime: e.target.value })}
                    placeholder="e.g., 30m, 2h"
                    className="mt-1"
                  />
                </div>

                <Separator />

                {/* Type-specific configuration */}
                {selectedNode.data.type === 'persona' && (
                  <>
                    <h4 className="text-sm text-foreground">Persona Settings</h4>
                    <div>
                      <Label htmlFor="persona-count">Number of Personas</Label>
                      <Input
                        id="persona-count"
                        type="number"
                        value={nodeConfig.personaCount || 10}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, personaCount: parseInt(e.target.value) })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="persona-model">AI Model</Label>
                      <Select
                        value={nodeConfig.aiModel || 'gpt-4o'}
                        onValueChange={(value) => setNodeConfig({ ...nodeConfig, aiModel: value })}
                      >
                        <SelectTrigger id="persona-model" className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                          <SelectItem value="claude-3">Claude 3</SelectItem>
                          <SelectItem value="gemini">Gemini Pro</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}

                {selectedNode.data.type === 'survey' && (
                  <>
                    <h4 className="text-sm text-foreground">Survey Settings</h4>
                    <div>
                      <Label htmlFor="survey-responses">Target Responses</Label>
                      <Input
                        id="survey-responses"
                        type="number"
                        value={nodeConfig.targetResponses || 100}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, targetResponses: parseInt(e.target.value) })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="survey-questions">Number of Questions</Label>
                      <Input
                        id="survey-questions"
                        type="number"
                        value={nodeConfig.questionCount || 10}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, questionCount: parseInt(e.target.value) })}
                        className="mt-1"
                      />
                    </div>
                  </>
                )}

                {selectedNode.data.type === 'focus-group' && (
                  <>
                    <h4 className="text-sm text-foreground">Focus Group Settings</h4>
                    <div>
                      <Label htmlFor="fg-participants">Participants</Label>
                      <Input
                        id="fg-participants"
                        type="number"
                        value={nodeConfig.participants || 8}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, participants: parseInt(e.target.value) })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="fg-duration">Duration (minutes)</Label>
                      <Input
                        id="fg-duration"
                        type="number"
                        value={nodeConfig.duration || 90}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, duration: parseInt(e.target.value) })}
                        className="mt-1"
                      />
                    </div>
                  </>
                )}

                {selectedNode.data.type === 'analysis' && (
                  <>
                    <h4 className="text-sm text-foreground">Analysis Settings</h4>
                    <div>
                      <Label htmlFor="analysis-type">Analysis Type</Label>
                      <Select
                        value={nodeConfig.analysisType || 'comprehensive'}
                        onValueChange={(value) => setNodeConfig({ ...nodeConfig, analysisType: value })}
                      >
                        <SelectTrigger id="analysis-type" className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="comprehensive">Comprehensive</SelectItem>
                          <SelectItem value="sentiment">Sentiment Analysis</SelectItem>
                          <SelectItem value="statistical">Statistical</SelectItem>
                          <SelectItem value="thematic">Thematic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
              </div>
            </ScrollArea>

            <div className="p-4 border-t border-border space-y-2">
              <Button
                onClick={saveNodeConfig}
                className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white"
              >
                Save Configuration
              </Button>
              <Button
                onClick={deleteSelectedNode}
                variant="outline"
                className="w-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Activity
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Save Dialog */}
      <Dialog open={isSaveDialogOpen} onOpenChange={setIsSaveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Workflow</DialogTitle>
            <DialogDescription>
              Save your workflow to access it later
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="workflow-name">Workflow Name</Label>
              <Input
                id="workflow-name"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                placeholder="e.g., Product Research Q1 2024"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="workflow-description">Description</Label>
              <Textarea
                id="workflow-description"
                value={workflowDescription}
                onChange={(e) => setWorkflowDescription(e.target.value)}
                placeholder="Describe what this workflow is for..."
                className="mt-1"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSaveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveWorkflow} className="bg-brand-orange hover:bg-brand-orange/90 text-white">
              Save Workflow
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Validation Dialog */}
      <Dialog open={isValidationOpen} onOpenChange={setIsValidationOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Workflow Validation</DialogTitle>
            <DialogDescription>
              Review validation results for your workflow
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-96">
            <div className="space-y-2">
              {validationIssues.length === 0 ? (
                <Alert className="bg-green-500/10 border-green-500/30">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <AlertDescription className="text-green-600">
                    Workflow is valid and ready to execute!
                  </AlertDescription>
                </Alert>
              ) : (
                validationIssues.map((issue, index) => (
                  <Alert 
                    key={index}
                    className={
                      issue.type === 'error' 
                        ? 'bg-destructive/10 border-destructive/30'
                        : issue.type === 'warning'
                        ? 'bg-orange-500/10 border-orange-500/30'
                        : 'bg-blue-500/10 border-blue-500/30'
                    }
                  >
                    <AlertCircle className={`w-4 h-4 ${
                      issue.type === 'error'
                        ? 'text-destructive'
                        : issue.type === 'warning'
                        ? 'text-orange-600'
                        : 'text-blue-600'
                    }`} />
                    <AlertDescription className={
                      issue.type === 'error'
                        ? 'text-destructive'
                        : issue.type === 'warning'
                        ? 'text-orange-600'
                        : 'text-blue-600'
                    }>
                      {issue.message}
                    </AlertDescription>
                  </Alert>
                ))
              )}
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsValidationOpen(false)}>
              Close
            </Button>
            {validationIssues.filter(i => i.type === 'error').length === 0 && (
              <Button 
                onClick={() => {
                  setIsValidationOpen(false);
                  executeWorkflow();
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
    </div>
  );
}
