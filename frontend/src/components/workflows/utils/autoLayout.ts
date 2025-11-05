/**
 * autoLayout.ts - Dagre-based automatic layout for workflow nodes
 *
 * Provides hierarchical graph layout using Dagre algorithm.
 * Supports top-to-bottom (TB) and left-to-right (LR) layout directions.
 *
 * @example
 * ```typescript
 * const layoutedNodes = getLayoutedElements(nodes, edges, {
 *   direction: 'TB',
 *   nodeWidth: 200,
 *   nodeHeight: 80,
 * });
 * setNodes(layoutedNodes);
 * ```
 */

import dagre from 'dagre';
import { Node, Edge } from 'reactflow';

/**
 * Layout direction types
 * - TB: Top to Bottom (vertical)
 * - LR: Left to Right (horizontal)
 */
export type LayoutDirection = 'TB' | 'LR';

/**
 * Configuration options for auto-layout
 */
export interface LayoutOptions {
  /** Layout direction (default: 'TB') */
  direction?: LayoutDirection;
  /** Node width in pixels (default: 200) */
  nodeWidth?: number;
  /** Node height in pixels (default: 80) */
  nodeHeight?: number;
  /** Horizontal spacing between nodes (default: 50) */
  nodeSeparation?: number;
  /** Vertical spacing between ranks/layers (default: 100) */
  rankSeparation?: number;
}

/**
 * Default layout options
 */
const DEFAULT_OPTIONS: Required<LayoutOptions> = {
  direction: 'TB',
  nodeWidth: 200,
  nodeHeight: 80,
  nodeSeparation: 50,
  rankSeparation: 100,
};

/**
 * Apply Dagre layout algorithm to workflow nodes
 *
 * Positions nodes in a hierarchical layout that:
 * - Respects edge directions (source → target)
 * - Minimizes edge crossings
 * - Maintains consistent spacing
 * - Handles disconnected components
 *
 * @param nodes - Array of React Flow nodes
 * @param edges - Array of React Flow edges
 * @param options - Layout configuration options
 * @returns Array of nodes with updated positions
 *
 * @example
 * ```typescript
 * // Basic usage with defaults
 * const layouted = getLayoutedElements(nodes, edges);
 *
 * // Custom configuration
 * const layouted = getLayoutedElements(nodes, edges, {
 *   direction: 'LR',
 *   nodeWidth: 250,
 *   nodeHeight: 100,
 *   nodeSeparation: 80,
 *   rankSeparation: 150,
 * });
 * ```
 */
export function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
): Node[] {
  // Merge with defaults
  const config = { ...DEFAULT_OPTIONS, ...options };
  const { direction, nodeWidth, nodeHeight, nodeSeparation, rankSeparation } = config;

  // Empty graph - return as is
  if (nodes.length === 0) {
    return nodes;
  }

  // Single node - center it
  if (nodes.length === 1) {
    return [
      {
        ...nodes[0],
        position: { x: 100, y: 50 },
      },
    ];
  }

  // Create Dagre graph
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Configure graph layout
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: nodeSeparation,
    ranksep: rankSeparation,
    // Additional Dagre options
    align: 'UL', // Align nodes to upper-left
    acyclicer: 'greedy', // Handle cycles
    ranker: 'network-simplex', // Ranking algorithm
  });

  // Add nodes to Dagre graph
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  // Add edges to Dagre graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Run Dagre layout algorithm
  dagre.layout(dagreGraph);

  // Apply calculated positions to React Flow nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    // Dagre returns center coordinates, React Flow uses top-left
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return layoutedNodes;
}

/**
 * Simple grid layout fallback (if Dagre is not available)
 *
 * Arranges nodes in a grid pattern without considering connections.
 * Useful as a fallback or for quick positioning.
 *
 * @param nodes - Array of React Flow nodes
 * @param spacing - Grid spacing { x, y } (default: { x: 250, y: 150 })
 * @returns Array of nodes with grid positions
 *
 * @example
 * ```typescript
 * const gridNodes = getGridLayout(nodes, { x: 300, y: 200 });
 * ```
 */
export function getGridLayout(
  nodes: Node[],
  spacing: { x: number; y: number } = { x: 250, y: 150 }
): Node[] {
  if (nodes.length === 0) return nodes;

  const cols = Math.ceil(Math.sqrt(nodes.length));
  const startX = 50;
  const startY = 50;

  return nodes.map((node, index) => ({
    ...node,
    position: {
      x: startX + (index % cols) * spacing.x,
      y: startY + Math.floor(index / cols) * spacing.y,
    },
  }));
}

/**
 * Check if nodes have default/uninitialized positions
 *
 * Detects if all nodes are at origin (0, 0) or very close together,
 * which indicates they haven't been manually positioned.
 *
 * @param nodes - Array of React Flow nodes
 * @returns true if nodes appear to be unpositioned
 *
 * @example
 * ```typescript
 * if (hasDefaultPositions(nodes)) {
 *   // Auto-apply layout on first load
 *   const layouted = getLayoutedElements(nodes, edges);
 *   setNodes(layouted);
 * }
 * ```
 */
export function hasDefaultPositions(nodes: Node[]): boolean {
  if (nodes.length === 0) return false;

  // Check if all nodes are at (0, 0)
  const allAtOrigin = nodes.every(
    (node) => node.position.x === 0 && node.position.y === 0
  );

  if (allAtOrigin) return true;

  // Check if all nodes are very close together (within 100px)
  const positions = nodes.map((n) => n.position);
  const minX = Math.min(...positions.map((p) => p.x));
  const maxX = Math.max(...positions.map((p) => p.x));
  const minY = Math.min(...positions.map((p) => p.y));
  const maxY = Math.max(...positions.map((p) => p.y));

  const width = maxX - minX;
  const height = maxY - minY;

  // If all nodes fit in a 100x100 square, they're probably unpositioned
  return width < 100 && height < 100;
}

/**
 * Calculate bounding box of nodes
 *
 * Useful for finding the extent of the graph for viewport fitting.
 *
 * @param nodes - Array of React Flow nodes
 * @returns Bounding box { minX, maxX, minY, maxY, width, height }
 */
export function getNodesBounds(nodes: Node[]) {
  if (nodes.length === 0) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0, width: 0, height: 0 };
  }

  const positions = nodes.map((n) => n.position);
  const minX = Math.min(...positions.map((p) => p.x));
  const maxX = Math.max(...positions.map((p) => p.x));
  const minY = Math.min(...positions.map((p) => p.y));
  const maxY = Math.max(...positions.map((p) => p.y));

  return {
    minX,
    maxX,
    minY,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
  };
}
