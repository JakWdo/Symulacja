# Workflow Utils - Auto-Layout System

Utilities dla automatycznego pozycjonowania workflow nodes.

## Pliki

### `autoLayout.ts`

Implementacja hierarchicznego layoutu używając algorytmu Dagre.

**Główne funkcje:**
- `getLayoutedElements(nodes, edges, options)` - Aplikuje Dagre layout
- `getGridLayout(nodes, spacing)` - Prosty grid layout (fallback)
- `hasDefaultPositions(nodes)` - Detects unpositioned nodes
- `getNodesBounds(nodes)` - Calculates bounding box

**Przykład użycia:**
```typescript
import { getLayoutedElements } from './autoLayout';

const layoutedNodes = getLayoutedElements(nodes, edges, {
  direction: 'TB',
  nodeWidth: 200,
  nodeHeight: 80,
});
setNodes(layoutedNodes);
```

### `smartPositioning.ts`

Inteligentne pozycjonowanie dla nowych nodów (drag & drop).

**Główne funkcje:**
- `getSmartDropPosition(existingNodes, defaultPosition)` - Znajdź wolne miejsce
- `getStructuredPosition(existingNodes, edges, parentId?)` - Position based on graph structure
- `hasDefaultPositions(nodes)` - Check if nodes unpositioned

**Przykład użycia:**
```typescript
import { getSmartDropPosition } from './smartPositioning';

const smartPos = getSmartDropPosition(nodes, dropPosition);
const newNode = { ...node, position: smartPos };
```

## Dependency

System wymaga:
- `reactflow` - React Flow library
- `dagre` - Graph layout algorithm
- `@types/dagre` - TypeScript types

**Instalacja:**
```bash
npm install reactflow dagre @types/dagre
```

## Dokumentacja

Pełna dokumentacja: `/docs/WORKFLOW_AUTO_LAYOUT.md`
