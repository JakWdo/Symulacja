import { useRef, useEffect, useState, useCallback } from 'react';
import { Badge } from './ui/badge';

interface Node {
  id: string;
  name: string;
  type: 'persona' | 'concept' | 'emotion' | 'message';
  group: number;
  size: number;
  sentiment?: number;
  color?: string;
  x: number;
  y: number;
}

interface Link {
  source: string;
  target: string;
  strength: number;
  type: 'agrees' | 'disagrees' | 'mentions' | 'feels';
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

interface NetworkGraphProps {
  filter?: string;
  selectedConcept?: string | null;
  onNodeClick?: (node: Node) => void;
  className?: string;
}

export function NetworkGraph({ filter = 'all', selectedConcept, onNodeClick, className }: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [simulation, setSimulation] = useState<any>(null);

  // Mock data z pozycjami procentowymi (będziemy skalować dynamicznie)
  const [graphData] = useState<GraphData>({
    nodes: [
      // Personas - centrum lewy
      { id: 'alex', name: 'Alex Chen', type: 'persona', group: 1, size: 15, sentiment: 0.7, color: '#F27405', x: 0.2, y: 0.25 },
      { id: 'sarah', name: 'Sarah Johnson', type: 'persona', group: 1, size: 12, sentiment: 0.3, color: '#F27405', x: 0.2, y: 0.5 },
      { id: 'mike', name: 'Mike Davis', type: 'persona', group: 1, size: 14, sentiment: 0.8, color: '#F27405', x: 0.2, y: 0.75 },
      { id: 'emma', name: 'Emma Wilson', type: 'persona', group: 1, size: 11, sentiment: 0.5, color: '#F27405', x: 0.2, y: 0.625 },
      
      // Concepts - centrum
      { id: 'price', name: 'Price', type: 'concept', group: 2, size: 18, color: '#F29F05', x: 0.5, y: 0.3 },
      { id: 'design', name: 'Design', type: 'concept', group: 2, size: 16, color: '#F29F05', x: 0.5, y: 0.5 },
      { id: 'usability', name: 'Usability', type: 'concept', group: 2, size: 17, color: '#F29F05', x: 0.5, y: 0.7 },
      { id: 'features', name: 'Features', type: 'concept', group: 2, size: 15, color: '#F29F05', x: 0.5, y: 0.4 },
      
      // Emotions - prawy
      { id: 'satisfied', name: 'Satisfied', type: 'emotion', group: 3, size: 10, color: '#28a745', x: 0.8, y: 0.25 },
      { id: 'frustrated', name: 'Frustrated', type: 'emotion', group: 3, size: 9, color: '#dc3545', x: 0.8, y: 0.5 },
      { id: 'excited', name: 'Excited', type: 'emotion', group: 3, size: 8, color: '#17a2b8', x: 0.8, y: 0.75 },
      { id: 'concerned', name: 'Concerned', type: 'emotion', group: 3, size: 11, color: '#ffc107', x: 0.8, y: 0.625 }
    ],
    links: [
      // Persona - Concept connections
      { source: 'alex', target: 'price', strength: 0.8, type: 'mentions' },
      { source: 'alex', target: 'design', strength: 0.9, type: 'mentions' },
      { source: 'sarah', target: 'price', strength: 0.6, type: 'mentions' },
      { source: 'sarah', target: 'usability', strength: 0.7, type: 'mentions' },
      { source: 'mike', target: 'features', strength: 0.8, type: 'mentions' },
      { source: 'emma', target: 'design', strength: 0.5, type: 'mentions' },
      
      // Persona - Emotion connections
      { source: 'alex', target: 'satisfied', strength: 0.7, type: 'feels' },
      { source: 'sarah', target: 'frustrated', strength: 0.8, type: 'feels' },
      { source: 'mike', target: 'excited', strength: 0.9, type: 'feels' },
      { source: 'emma', target: 'concerned', strength: 0.6, type: 'feels' },
      
      // Concept - Emotion connections
      { source: 'price', target: 'concerned', strength: 0.7, type: 'mentions' },
      { source: 'design', target: 'satisfied', strength: 0.8, type: 'mentions' },
      { source: 'usability', target: 'frustrated', strength: 0.6, type: 'mentions' },
      { source: 'features', target: 'excited', strength: 0.9, type: 'mentions' }
    ]
  });

  // Funkcja filtrowania danych
  const getFilteredData = useCallback(() => {
    let filteredNodes = [...graphData.nodes];
    let filteredLinks = [...graphData.links];

    if (selectedConcept) {
      const relatedNodeIds = new Set([selectedConcept]);
      filteredLinks.forEach(link => {
        if (link.source === selectedConcept || link.target === selectedConcept) {
          relatedNodeIds.add(link.source);
          relatedNodeIds.add(link.target);
        }
      });
      filteredNodes = graphData.nodes.filter(node => relatedNodeIds.has(node.id));
      filteredLinks = graphData.links.filter(link => 
        relatedNodeIds.has(link.source) && relatedNodeIds.has(link.target)
      );
    }

    if (filter !== 'all') {
      switch (filter) {
        case 'positive':
          filteredNodes = filteredNodes.filter(node => 
            node.type !== 'persona' || (node.sentiment && node.sentiment > 0.6)
          );
          break;
        case 'negative':
          filteredNodes = filteredNodes.filter(node => 
            node.type !== 'persona' || (node.sentiment && node.sentiment < 0.4)
          );
          break;
        case 'influence':
          filteredLinks = filteredLinks.filter(link => link.strength > 0.7);
          break;
      }
    }

    return { nodes: filteredNodes, links: filteredLinks };
  }, [graphData, filter, selectedConcept]);

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

  const filteredData = getFilteredData();

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
          {filteredData.links.map((link, index) => {
            const sourceNode = filteredData.nodes.find(n => n.id === link.source);
            const targetNode = filteredData.nodes.find(n => n.id === link.target);
            
            if (!sourceNode || !targetNode) return null;

            let linkColor = '#cccccc';
            if (link.type === 'agrees') linkColor = '#28a745';
            else if (link.type === 'disagrees') linkColor = '#dc3545';
            else if (link.type === 'mentions') linkColor = '#F29F05';
            else if (link.type === 'feels') linkColor = '#17a2b8';

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
                opacity={isHighlighted ? 0.8 : 0.4}
                className="transition-all duration-200"
              />
            );
          })}
        </g>

        {/* Nodes */}
        <g className="nodes">
          {filteredData.nodes.map((node) => {
            const isHovered = hoveredNode?.id === node.id;
            const isConnected = hoveredNode && filteredData.links.some(link =>
              (link.source === hoveredNode.id && link.target === node.id) ||
              (link.target === hoveredNode.id && link.source === node.id)
            );

            return (
              <g key={node.id} className="node-group">
                {/* Node circle */}
                <circle
                  cx={node.x * dimensions.width}
                  cy={node.y * dimensions.height}
                  r={node.size * 0.7}
                  fill={node.color}
                  stroke={isHovered || isConnected ? '#F27405' : 'transparent'}
                  strokeWidth={isHovered || isConnected ? 3 : 0}
                  opacity={hoveredNode && !isHovered && !isConnected ? 0.3 : 1}
                  className="cursor-pointer transition-all duration-200 hover:stroke-primary"
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
      
      {/* Tooltip dla hovera */}
      {hoveredNode && (
        <div className="absolute top-4 right-4 bg-card border border-border rounded-lg p-3 shadow-lg z-10 min-w-48">
          <div className="flex items-center gap-2 mb-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: hoveredNode.color }}
            />
            <span className="text-sm text-card-foreground">{hoveredNode.name}</span>
          </div>
          <Badge variant="outline" className="text-xs">
            {hoveredNode.type}
          </Badge>
          {hoveredNode.sentiment && (
            <div className="mt-2 text-xs text-muted-foreground">
              Sentiment: {Math.round(hoveredNode.sentiment * 100)}%
            </div>
          )}
        </div>
      )}
      
      {/* Legenda */}
      <div className="absolute bottom-4 left-4 bg-card/95 border border-border rounded-lg p-3 backdrop-blur-sm">
        <div className="text-xs text-card-foreground mb-2">Node Types</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F27405' }}></div>
            <span className="text-xs text-muted-foreground">Personas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F29F05' }}></div>
            <span className="text-xs text-muted-foreground">Concepts</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-xs text-muted-foreground">Emotions</span>
          </div>
        </div>
      </div>

      {/* Connection Types Legend */}
      <div className="absolute bottom-4 right-4 bg-card/95 border border-border rounded-lg p-3 backdrop-blur-sm">
        <div className="text-xs text-card-foreground mb-2">Connection Types</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#F29F05' }}></div>
            <span className="text-xs text-muted-foreground">Mentions</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#17a2b8' }}></div>
            <span className="text-xs text-muted-foreground">Feels</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#28a745' }}></div>
            <span className="text-xs text-muted-foreground">Agrees</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ backgroundColor: '#dc3545' }}></div>
            <span className="text-xs text-muted-foreground">Disagrees</span>
          </div>
        </div>
      </div>
    </div>
  );
}