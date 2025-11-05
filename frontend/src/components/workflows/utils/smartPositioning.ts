/**
 * smartPositioning.ts - Smart positioning for dropped workflow nodes
 *
 * Provides intelligent placement for newly added nodes:
 * - Avoids overlapping with existing nodes
 * - Places nodes in logical positions based on graph structure
 * - Handles empty canvas vs populated canvas
 *
 * @example
 * ```typescript
 * const smartPos = getSmartDropPosition(existingNodes, dropPosition);
 * const newNode = { ...node, position: smartPos };
 * ```
 */

import { Node, XYPosition } from 'reactflow';

/**
 * Default node dimensions (used for overlap detection)
 */
const DEFAULT_NODE_WIDTH = 200;
const DEFAULT_NODE_HEIGHT = 80;
const SPACING = 50; // Minimum spacing between nodes

/**
 * Get smart position for a newly dropped node
 *
 * Strategy:
 * 1. Empty canvas → Use drop position (viewport center)
 * 2. Has nodes → Find nearest free space without overlap
 * 3. Fallback → Offset to the right/bottom of existing nodes
 *
 * @param existingNodes - Current nodes in the canvas
 * @param defaultPosition - Desired drop position (viewport coords)
 * @param nodeWidth - Width of the new node (default: 200)
 * @param nodeHeight - Height of the new node (default: 80)
 * @returns Optimal position for the new node
 *
 * @example
 * ```typescript
 * // In onDrop handler
 * const position = reactFlowInstance.screenToFlowPosition({
 *   x: event.clientX,
 *   y: event.clientY,
 * });
 * const smartPosition = getSmartDropPosition(nodes, position);
 * ```
 */
export function getSmartDropPosition(
  existingNodes: Node[],
  defaultPosition: XYPosition,
  nodeWidth: number = DEFAULT_NODE_WIDTH,
  nodeHeight: number = DEFAULT_NODE_HEIGHT
): XYPosition {
  // Empty canvas - use default position
  if (existingNodes.length === 0) {
    return defaultPosition;
  }

  // Check if default position overlaps with existing nodes
  const overlaps = checkOverlap(
    defaultPosition,
    existingNodes,
    nodeWidth,
    nodeHeight
  );

  // No overlap - use default position
  if (!overlaps) {
    return defaultPosition;
  }

  // Find nearest free position
  const freePosition = findNearestFreePosition(
    defaultPosition,
    existingNodes,
    nodeWidth,
    nodeHeight
  );

  return freePosition;
}

/**
 * Check if a position overlaps with any existing nodes
 *
 * @param position - Position to check
 * @param existingNodes - Existing nodes
 * @param width - Node width
 * @param height - Node height
 * @returns true if position overlaps with any node
 */
function checkOverlap(
  position: XYPosition,
  existingNodes: Node[],
  width: number,
  height: number
): boolean {
  return existingNodes.some((node) => {
    const nodeWidth = node.width || DEFAULT_NODE_WIDTH;
    const nodeHeight = node.height || DEFAULT_NODE_HEIGHT;

    // Check bounding box overlap with spacing
    const horizontalOverlap =
      position.x < node.position.x + nodeWidth + SPACING &&
      position.x + width + SPACING > node.position.x;

    const verticalOverlap =
      position.y < node.position.y + nodeHeight + SPACING &&
      position.y + height + SPACING > node.position.y;

    return horizontalOverlap && verticalOverlap;
  });
}

/**
 * Find nearest free position from a starting position
 *
 * Uses a spiral search pattern to find the closest non-overlapping position.
 *
 * @param startPosition - Starting search position
 * @param existingNodes - Existing nodes
 * @param width - Node width
 * @param height - Node height
 * @returns Nearest free position
 */
function findNearestFreePosition(
  startPosition: XYPosition,
  existingNodes: Node[],
  width: number,
  height: number
): XYPosition {
  const step = 50; // Search step size
  const maxIterations = 20; // Max search iterations

  // Try positions in expanding grid pattern
  for (let i = 1; i <= maxIterations; i++) {
    const offsets = [
      { x: i * step, y: 0 }, // Right
      { x: 0, y: i * step }, // Down
      { x: -i * step, y: 0 }, // Left
      { x: 0, y: -i * step }, // Up
      { x: i * step, y: i * step }, // Diagonal down-right
      { x: -i * step, y: i * step }, // Diagonal down-left
      { x: i * step, y: -i * step }, // Diagonal up-right
      { x: -i * step, y: -i * step }, // Diagonal up-left
    ];

    for (const offset of offsets) {
      const testPosition = {
        x: startPosition.x + offset.x,
        y: startPosition.y + offset.y,
      };

      if (!checkOverlap(testPosition, existingNodes, width, height)) {
        return testPosition;
      }
    }
  }

  // Fallback: place to the right of rightmost node
  return getFallbackPosition(existingNodes, width, height);
}

/**
 * Get fallback position when no free space is found
 *
 * Places node to the right of the rightmost node.
 *
 * @param existingNodes - Existing nodes
 * @param width - Node width
 * @param height - Node height
 * @returns Fallback position
 */
function getFallbackPosition(
  existingNodes: Node[],
  width: number,
  height: number
): XYPosition {
  // Find rightmost node
  const rightmost = Math.max(
    ...existingNodes.map((n) => n.position.x + (n.width || DEFAULT_NODE_WIDTH))
  );

  // Find average Y position for vertical centering
  const avgY =
    existingNodes.reduce((sum, n) => sum + n.position.y, 0) /
    existingNodes.length;

  return {
    x: rightmost + SPACING,
    y: avgY,
  };
}

/**
 * Get position for a new node based on graph structure
 *
 * More intelligent positioning that considers:
 * - Parent-child relationships (place child below parent)
 * - Sibling relationships (place next to siblings)
 * - Isolated nodes (place in grid)
 *
 * @param existingNodes - Existing nodes
 * @param edges - Existing edges
 * @param parentNodeId - Optional parent node ID (if connecting to parent)
 * @returns Smart position based on graph structure
 *
 * @example
 * ```typescript
 * // When adding a child node
 * const position = getStructuredPosition(nodes, edges, parentNode.id);
 * ```
 */
export function getStructuredPosition(
  existingNodes: Node[],
  edges: { source: string; target: string }[],
  parentNodeId?: string
): XYPosition {
  // Empty canvas - start at origin
  if (existingNodes.length === 0) {
    return { x: 100, y: 50 };
  }

  // If parent specified, place below parent
  if (parentNodeId) {
    const parent = existingNodes.find((n) => n.id === parentNodeId);
    if (parent) {
      // Find children of parent
      const siblings = edges
        .filter((e) => e.source === parentNodeId)
        .map((e) => e.target);

      // Place to the right of last sibling
      if (siblings.length > 0) {
        const lastSibling = existingNodes.find(
          (n) => n.id === siblings[siblings.length - 1]
        );
        if (lastSibling) {
          return {
            x: lastSibling.position.x + DEFAULT_NODE_WIDTH + SPACING,
            y: lastSibling.position.y,
          };
        }
      }

      // No siblings - place below parent
      return {
        x: parent.position.x,
        y: parent.position.y + DEFAULT_NODE_HEIGHT + SPACING * 2,
      };
    }
  }

  // No parent - place to the right of rightmost node
  const rightmost = Math.max(
    ...existingNodes.map((n) => n.position.x + (n.width || DEFAULT_NODE_WIDTH))
  );

  const avgY =
    existingNodes.reduce((sum, n) => sum + n.position.y, 0) /
    existingNodes.length;

  return {
    x: rightmost + SPACING * 2,
    y: avgY,
  };
}

/**
 * Check if all nodes have default positions (0, 0)
 *
 * Useful for detecting when auto-layout should be applied.
 *
 * @param nodes - Array of nodes to check
 * @returns true if all nodes are at (0, 0)
 */
export function hasDefaultPositions(nodes: Node[]): boolean {
  if (nodes.length === 0) return false;
  return nodes.every((node) => node.position.x === 0 && node.position.y === 0);
}

/**
 * Calculate center position of viewport
 *
 * Used for centering nodes on empty canvas.
 *
 * @param viewportWidth - Viewport width
 * @param viewportHeight - Viewport height
 * @returns Center position
 */
export function getViewportCenter(
  viewportWidth: number,
  viewportHeight: number
): XYPosition {
  return {
    x: viewportWidth / 2 - DEFAULT_NODE_WIDTH / 2,
    y: viewportHeight / 2 - DEFAULT_NODE_HEIGHT / 2,
  };
}
