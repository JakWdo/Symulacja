import { useRef, useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { useTranslation } from 'react-i18next';

interface Node {
  id: string;
  name: string;
  type: 'persona' | 'concept' | 'emotion';
  group: number;
  size: number;
  sentiment?: number;
  metadata?: any;
  x: number;
  y: number;
}

interface Link {
  source: string;
  target: string;
  strength: number;
  type: 'agrees' | 'disagrees' | 'mentions' | 'feels';
  sentiment?: number;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

interface NetworkGraphProps {
  data: GraphData;
  filter?: string;
  selectedConcept?: string | null;
  onNodeClick?: (node: Node) => void;
  className?: string;
}

export function NetworkGraph({ data, onNodeClick, className }: NetworkGraphProps) {
  const { t } = useTranslation('analysis');
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);

  // Auto-layout positions for nodes (force-directed simulation)
  const [layoutNodes, setLayoutNodes] = useState<Node[]>([]);

  // Simple force-directed layout
  useEffect(() => {
    if (!data.nodes.length) return;

    // Assign positions based on type for initial layout
    const positioned = data.nodes.map((node, idx) => {
      let x = 0.5, y = 0.5;

      if (node.type === 'persona') {
        x = 0.2;
        y = 0.2 + (idx * 0.6 / Math.max(1, data.nodes.filter(n => n.type === 'persona').length - 1));
      } else if (node.type === 'concept') {
        const conceptIdx = data.nodes.filter(n => n.type === 'concept').indexOf(node);
        x = 0.5;
        y = 0.2 + (conceptIdx * 0.6 / Math.max(1, data.nodes.filter(n => n.type === 'concept').length - 1));
      } else if (node.type === 'emotion') {
        const emotionIdx = data.nodes.filter(n => n.type === 'emotion').indexOf(node);
        x = 0.8;
        y = 0.2 + (emotionIdx * 0.6 / Math.max(1, data.nodes.filter(n => n.type === 'emotion').length - 1));
      }

      return { ...node, x, y };
    });

    setLayoutNodes(positioned);
  }, [data]);

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current) {
        const rect = svgRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const handleNodeClick = (node: Node) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  const handleNodeHover = (node: Node | null) => {
    setHoveredNode(node);
  };

  const getNodeColor = (node: Node) => {
    if (node.type === 'persona') return '#F27405';
    if (node.type === 'concept') return '#F29F05';
    // Emotions - color by sentiment
    if (node.sentiment && node.sentiment > 0.6) return '#10B981';
    if (node.sentiment && node.sentiment < -0.3) return '#EF4444';
    return '#6B7280';
  };

  if (!layoutNodes.length) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <p className="text-muted-foreground">{t('graph.noData')}</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
        className="border border-border rounded-lg bg-background"
      >
        {/* Links */}
        <g className="links">
          {data.links.map((link, index) => {
            const sourceNode = layoutNodes.find(n => n.id === link.source);
            const targetNode = layoutNodes.find(n => n.id === link.target);

            if (!sourceNode || !targetNode) return null;

            let linkColor = '#cccccc';
            if (link.type === 'agrees') linkColor = '#10B981';
            else if (link.type === 'disagrees') linkColor = '#EF4444';
            else if (link.type === 'mentions') linkColor = '#F29F05';
            else if (link.type === 'feels') linkColor = '#6366F1';

            const isHighlighted = hoveredNode && (
              hoveredNode.id === link.source || hoveredNode.id === link.target
            );

            return (
              <line
                key={`${link.source}-${link.target}-${index}`}
                x1={sourceNode.x * dimensions.width}
                y1={sourceNode.y * dimensions.height}
                x2={targetNode.x * dimensions.width}
                y2={targetNode.y * dimensions.height}
                stroke={isHighlighted ? linkColor : '#e0e0e0'}
                strokeWidth={Math.max(1, link.strength * 3)}
                opacity={isHighlighted ? 0.8 : 0.3}
                className="transition-all duration-200"
              />
            );
          })}
        </g>

        {/* Nodes */}
        <g className="nodes">
          {layoutNodes.map((node) => {
            const isHovered = hoveredNode?.id === node.id;
            const isConnected = hoveredNode && data.links.some(link =>
              (link.source === hoveredNode.id && link.target === node.id) ||
              (link.target === hoveredNode.id && link.source === node.id)
            );

            const nodeColor = getNodeColor(node);

            return (
              <g key={node.id} className="node-group">
                {/* Node circle */}
                <circle
                  cx={node.x * dimensions.width}
                  cy={node.y * dimensions.height}
                  r={node.size * 0.7}
                  fill={nodeColor}
                  stroke={isHovered || isConnected ? '#F27405' : 'transparent'}
                  strokeWidth={isHovered || isConnected ? 3 : 0}
                  opacity={hoveredNode && !isHovered && !isConnected ? 0.3 : 1}
                  className="cursor-pointer transition-all duration-200"
                  onMouseEnter={() => handleNodeHover(node)}
                  onMouseLeave={() => handleNodeHover(null)}
                  onClick={() => handleNodeClick(node)}
                />

                {/* Node label */}
                <text
                  x={node.x * dimensions.width}
                  y={node.y * dimensions.height + node.size + 15}
                  textAnchor="middle"
                  className="text-xs text-foreground pointer-events-none select-none"
                  fill="currentColor"
                >
                  {node.name}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Tooltip for hover */}
      {hoveredNode && (
        <div className="absolute top-4 right-4 bg-card border border-border rounded-lg p-3 shadow-lg z-10 min-w-48">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getNodeColor(hoveredNode) }}
            />
            <span className="text-sm text-card-foreground font-medium">{hoveredNode.name}</span>
          </div>
          <Badge variant="outline" className="text-xs mb-2">
            {hoveredNode.type}
          </Badge>
          {hoveredNode.sentiment !== undefined && (
            <div className="text-xs text-muted-foreground">
              {t('graph.tooltip.sentiment', { score: Math.round(hoveredNode.sentiment * 100) })}
            </div>
          )}
          {hoveredNode.metadata && (
            <div className="mt-2 text-xs text-muted-foreground">
              {hoveredNode.metadata.age && <div>{t('graph.tooltip.age', { age: hoveredNode.metadata.age })}</div>}
              {hoveredNode.metadata.occupation && <div>{t('graph.tooltip.occupation', { occupation: hoveredNode.metadata.occupation })}</div>}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-card/95 border border-border rounded-lg p-3 backdrop-blur-sm">
        <div className="text-xs text-card-foreground mb-2 font-medium">{t('graph.legend.nodeTypes')}</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F27405' }}></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.personas')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F29F05' }}></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.concepts')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.emotions')}</span>
          </div>
        </div>
      </div>

      {/* Connection Types Legend */}
      <div className="absolute bottom-4 right-4 bg-card/95 border border-border rounded-lg p-3 backdrop-blur-sm">
        <div className="text-xs text-card-foreground mb-2 font-medium">{t('graph.legend.connectionTypes')}</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#F29F05' }}></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.mentions')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#6366F1' }}></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.feels')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#10B981' }}></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.agrees')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#EF4444' }}></div>
            <span className="text-xs text-muted-foreground">{t('graph.legend.disagrees')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
