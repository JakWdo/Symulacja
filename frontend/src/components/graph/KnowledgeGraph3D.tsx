import { useRef, useMemo, memo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force';
import type { GraphData, GraphNode } from '@/types';

// Color mapping for different node types
const NODE_COLORS = {
  persona: '#0ea5e9',    // Blue
  concept: '#8b5cf6',    // Purple
  emotion: '#f59e0b',    // Amber
};

// Sentiment-based coloring
function getSentimentColor(sentiment?: number): string {
  if (sentiment === undefined || sentiment === null) return NODE_COLORS.persona;
  if (sentiment > 0.5) return '#10b981';  // Green - positive
  if (sentiment < -0.3) return '#ef4444'; // Red - negative
  return '#6b7280';  // Gray - neutral
}

// Memoized Node component for better performance
const Node = memo(({ node, onClick }: { node: GraphNode; onClick?: (node: GraphNode) => void }) => {
  const ref = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const color = node.type === 'persona'
    ? getSentimentColor(node.sentiment)
    : NODE_COLORS[node.type] || '#0ea5e9';

  return (
    <mesh
      ref={ref}
      position={[node.x || 0, node.y || 0, node.z || 0]}
      onClick={() => onClick?.(node)}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <sphereGeometry args={[node.size || 0.5, 32, 32]} />
      <meshStandardMaterial
        color={color}
        emissive={hovered ? color : '#000000'}
        emissiveIntensity={hovered ? 0.3 : 0}
      />
      {(hovered || node.size && node.size > 0.7) && (
        <Text
          position={[0, (node.size || 0.5) + 0.4, 0]}
          fontSize={0.3}
          color="white"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.05}
          outlineColor="#000000"
        >
          {node.name || node.label || node.id.slice(0, 8)}
        </Text>
      )}
    </mesh>
  );
});

Node.displayName = 'Node';

function Graph({
  graphData,
  onNodeClick
}: {
  graphData: GraphData;
  onNodeClick?: (node: GraphNode) => void;
}) {
  const { nodes, links } = graphData;

  // Memoize simulation to prevent re-running on every render
  const simulatedNodes = useMemo(() => {
    if (!nodes || nodes.length === 0) return [];

    // Create a copy to avoid mutating original data
    const nodesCopy = nodes.map(n => ({ ...n, x: 0, y: 0, z: 0 }));

    // Ensure links is a valid array
    const validLinks = Array.isArray(links) ? links : [];

    const simulation = forceSimulation(nodesCopy)
      .force('link', forceLink(validLinks).id((d: any) => d.id).distance(5).strength(0.3))
      .force('charge', forceManyBody().strength(-30))
      .force('center', forceCenter(0, 0))
      .force('collision', forceCollide().radius(1.5))
      .stop();

    // Run simulation for stable layout
    for (let i = 0; i < 100; i++) {
      simulation.tick();
    }

    return simulation.nodes() as GraphNode[];
  }, [nodes, links]);

  // Memoize node map
  const nodeMap = useMemo(() => {
    return new Map(simulatedNodes.map(node => [node.id, node]));
  }, [simulatedNodes]);

  // Limit number of links for performance (only show strong connections)
  const visibleLinks = useMemo(() => {
    if (!Array.isArray(links) || links.length === 0) return [];
    if (links.length <= 100) return links;

    // Sort by strength and take top 100 connections
    return [...links]
      .sort((a, b) => (b.strength || b.value || 0) - (a.strength || a.value || 0))
      .slice(0, 100);
  }, [links]);

  // Color links by sentiment or type
  const getLinkColor = (link: typeof links[0]) => {
    if (link.sentiment !== undefined) {
      if (link.sentiment > 0.5) return '#10b981'; // Positive - green
      if (link.sentiment < -0.3) return '#ef4444'; // Negative - red
      return '#6b7280'; // Neutral - gray
    }
    if (link.type === 'disagrees') return '#ef4444';
    if (link.type === 'agrees') return '#10b981';
    return '#cbd5e1'; // Default
  };

  return (
    <>
      {simulatedNodes.map((node) => (
        <Node key={node.id} node={node} onClick={onNodeClick} />
      ))}
      {visibleLinks.map((link, i) => {
        const source = nodeMap.get(typeof link.source === 'string' ? link.source : link.source.id);
        const target = nodeMap.get(typeof link.target === 'string' ? link.target : link.target.id);
        if (!source || !target) return null;

        return (
          <Line
            key={i}
            points={[
              [source.x || 0, source.y || 0, source.z || 0],
              [target.x || 0, target.y || 0, target.z || 0]
            ]}
            color={getLinkColor(link)}
            transparent
            opacity={0.4}
            lineWidth={1}
          />
        );
      })}
    </>
  );
}

export function KnowledgeGraph3D({
  graphData,
  onNodeClick
}: {
  graphData: GraphData | null;
  onNodeClick?: (node: GraphNode) => void;
}) {
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <p>No graph data available. Build the knowledge graph first.</p>
      </div>
    );
  }

  try {
    return (
      <Canvas
        camera={{ position: [0, 0, 30], fov: 50 }}
        gl={{ antialias: true, alpha: false }}
        dpr={[1, 2]}
        onCreated={({ gl }) => {
          gl.setClearColor('#0a0a0a', 1);
        }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Graph graphData={graphData} onNodeClick={onNodeClick} />
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          maxDistance={100}
          minDistance={10}
        />
      </Canvas>
    );
  } catch (error) {
    console.error('Failed to render Canvas:', error);
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <div className="text-center p-8">
          <p className="text-red-500 mb-2">Failed to initialize 3D renderer</p>
          <p className="text-sm">Your browser may not support WebGL.</p>
        </div>
      </div>
    );
  }
}
