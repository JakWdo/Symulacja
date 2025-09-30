import { useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import { useAppStore } from '@/store/appStore';
import type { GraphNode, GraphLink } from '@/types';

interface NodeMeshProps {
  node: GraphNode;
  isSelected: boolean;
  isHovered: boolean;
  onClick: () => void;
  onHover: (hovering: boolean) => void;
}

function NodeMesh({ node, isSelected, isHovered, onClick, onHover }: NodeMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const showLabels = useAppStore((state) => state.showLabels);

  const color = useMemo(() => {
    if (isSelected) return '#e879f9'; // accent-400
    if (isHovered) return '#38bdf8'; // primary-400
    return node.color || '#94a3b8'; // slate-400
  }, [isSelected, isHovered, node.color]);

  const size = useMemo(() => {
    return node.size || (isSelected ? 1.2 : isHovered ? 1 : 0.8);
  }, [node.size, isSelected, isHovered]);

  useFrame((state) => {
    if (meshRef.current) {
      // Gentle floating animation
      meshRef.current.position.y = node.y! + Math.sin(state.clock.elapsedTime + node.x!) * 0.1;

      // Rotate when hovered or selected
      if (isHovered || isSelected) {
        meshRef.current.rotation.y += 0.01;
      }
    }
  });

  return (
    <group position={[node.x!, node.y!, node.z!]}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(true);
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          onHover(false);
          document.body.style.cursor = 'default';
        }}
      >
        <sphereGeometry args={[size, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isSelected ? 0.5 : isHovered ? 0.3 : 0.1}
          metalness={0.3}
          roughness={0.4}
        />
      </mesh>

      {/* Glow effect */}
      {(isSelected || isHovered) && (
        <mesh position={[0, 0, 0]} scale={size * 1.5}>
          <sphereGeometry args={[1, 32, 32]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.2}
            side={THREE.BackSide}
          />
        </mesh>
      )}

      {/* Label */}
      {showLabels && (isSelected || isHovered) && (
        <Text
          position={[0, size + 0.5, 0]}
          fontSize={0.3}
          color="#1e293b"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.02}
          outlineColor="#ffffff"
        >
          {node.label}
        </Text>
      )}
    </group>
  );
}

interface LinkLineProps {
  link: GraphLink;
  nodes: Map<string, GraphNode>;
}

function LinkLine({ link, nodes }: LinkLineProps) {
  const sourceNode = nodes.get(
    typeof link.source === 'string' ? link.source : link.source.id
  );
  const targetNode = nodes.get(
    typeof link.target === 'string' ? link.target : link.target.id
  );

  if (!sourceNode || !targetNode) return null;

  const points = useMemo<[number, number, number][]>(
    () => [
      [sourceNode.x!, sourceNode.y!, sourceNode.z!],
      [targetNode.x!, targetNode.y!, targetNode.z!],
    ],
    [sourceNode, targetNode],
  );

  return (
    <Line
      points={points}
      color="#cbd5e1"
      transparent
      opacity={0.3}
      lineWidth={1}
    />
  );
}

function Scene() {
  const { camera } = useThree();
  const graphData = useAppStore((state) => state.graphData);
  const selectedNodes = useAppStore((state) => state.selectedNodes);
  const hoveredNode = useAppStore((state) => state.hoveredNode);
  const setHoveredNode = useAppStore((state) => state.setHoveredNode);
  const toggleNodeSelection = useAppStore((state) => state.toggleNodeSelection);

  const nodesMap = useMemo(() => {
    const map = new Map<string, GraphNode>();
    graphData?.nodes.forEach((node) => map.set(node.id, node));
    return map;
  }, [graphData]);

  useEffect(() => {
    // Set initial camera position
    camera.position.set(0, 0, 50);
  }, [camera]);

  if (!graphData) return null;

  return (
    <>
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <pointLight position={[-10, -10, -10]} intensity={0.3} />

      {/* Render links */}
      {graphData.links.map((link, idx) => (
        <LinkLine key={idx} link={link} nodes={nodesMap} />
      ))}

      {/* Render nodes */}
      {graphData.nodes.map((node) => (
        <NodeMesh
          key={node.id}
          node={node}
          isSelected={selectedNodes.includes(node.id)}
          isHovered={hoveredNode === node.id}
          onClick={() => toggleNodeSelection(node.id)}
          onHover={(hovering) => setHoveredNode(hovering ? node.id : null)}
        />
      ))}

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        rotateSpeed={0.5}
        zoomSpeed={0.8}
        minDistance={10}
        maxDistance={200}
      />
    </>
  );
}

export function KnowledgeGraph3D() {
  return (
    <div className="absolute inset-0 w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 50], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
      >
        <color attach="background" args={['#f8fafc']} />
        <fog attach="fog" args={['#f8fafc', 50, 200]} />
        <Scene />
      </Canvas>
    </div>
  );
}