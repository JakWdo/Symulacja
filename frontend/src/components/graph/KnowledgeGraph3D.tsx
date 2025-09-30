import { useRef, useMemo, memo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force';
import type { GraphData, GraphNode } from '@/types';

// Memoized Node component for better performance
const Node = memo(({ node }: { node: GraphNode }) => {
  const ref = useRef<THREE.Mesh>(null);
  return (
    <mesh ref={ref} position={[node.x || 0, node.y || 0, node.z || 0]}>
      <sphereGeometry args={[node.size || 0.5, 32, 32]} />
      <meshStandardMaterial color={node.color || '#0ea5e9'} />
      <Text
        position={[0, (node.size || 0.5) + 0.3, 0]}
        fontSize={0.3}
        color="black"
        anchorX="center"
        anchorY="middle"
      >
        {node.label}
      </Text>
    </mesh>
  );
});

Node.displayName = 'Node';

function Graph({ graphData }: { graphData: GraphData }) {
  const { nodes, links } = graphData;

  // Memoize simulation to prevent re-running on every render
  const simulatedNodes = useMemo(() => {
    if (!nodes || nodes.length === 0) return [];

    // Create a copy to avoid mutating original data
    const nodesCopy = nodes.map(n => ({ ...n, x: 0, y: 0, z: 0 }));

    const simulation = forceSimulation(nodesCopy)
      .force('link', forceLink(links).id((d: any) => d.id).distance(5).strength(0.3))
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
    if (links.length <= 100) return links;

    // Sort by value and take top 100 connections
    return [...links]
      .sort((a, b) => (b.value || 0) - (a.value || 0))
      .slice(0, 100);
  }, [links]);

  return (
    <>
      {simulatedNodes.map((node) => (
        <Node key={node.id} node={node} />
      ))}
      {visibleLinks.map((link, i) => {
        const source = nodeMap.get(link.source as string);
        const target = nodeMap.get(link.target as string);
        if (!source || !target) return null;

        return (
          <Line
            key={i}
            points={[
              [source.x || 0, source.y || 0, source.z || 0],
              [target.x || 0, target.y || 0, target.z || 0]
            ]}
            color="#cbd5e1"
            transparent
            opacity={0.3}
            lineWidth={1}
          />
        );
      })}
    </>
  );
}


export function KnowledgeGraph3D({ graphData }: { graphData: GraphData | null }) {
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <p>No personas to display. Generate personas to see the graph.</p>
      </div>
    );
  }

  return (
    <Canvas camera={{ position: [0, 0, 30], fov: 50 }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <Graph graphData={graphData} />
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        maxDistance={100}
        minDistance={10}
      />
    </Canvas>
  );
}