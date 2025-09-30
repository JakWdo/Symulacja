# Market Research Platform - Frontend

Immersive behavioral analytics dashboard with floating UI and 3D knowledge graph visualization.

## Features

### Immersive 3D Knowledge Graph
- **Interactive 3D visualization** powered by Three.js and React Three Fiber
- **Force-directed layout** showing persona relationships and clusters
- **Real-time interaction** with hover effects, selections, and animations
- **Smooth camera controls** with OrbitControls for exploration

### Floating UI Design
- **Minimalist interface** with floating panels positioned around edges
- **Glass morphism effects** with backdrop blur and transparency
- **Smooth animations** using Framer Motion
- **Context-sensitive panels** that appear/disappear based on actions

### Core Functionality
- **Project Management** - Create and manage research projects
- **Persona Visualization** - View synthetic personas in network graph
- **Focus Group Simulation** - Run and monitor focus group sessions
- **Polarization Analysis** - Visualize opinion clusters and sentiment
- **Real-time Updates** - WebSocket support for live data streaming

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Three.js** - 3D graphics
- **React Three Fiber** - React renderer for Three.js
- **D3** - Data visualization
- **Framer Motion** - Animations
- **Zustand** - State management
- **React Query** - Server state
- **Axios** - HTTP client

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The app will be available at `http://localhost:3000`

## Project Structure

```
src/
├── components/
│   ├── graph/          # 3D graph visualizations
│   ├── ui/             # Reusable UI components
│   ├── layout/         # Layout components
│   └── panels/         # Floating panels
├── hooks/              # Custom React hooks
├── lib/                # Utilities and API client
├── services/           # Business logic
├── store/              # Zustand state management
├── types/              # TypeScript definitions
└── styles/             # Global styles
```

## Key Components

### KnowledgeGraph3D
3D force-directed graph showing persona networks with:
- Nodes representing personas, clusters, topics
- Links showing relationships and similarities
- Interactive hover and selection
- Smooth animations and transitions

### FloatingControls
Main navigation with floating action buttons:
- Projects panel
- Personas panel
- Focus Groups panel
- Analysis panel
- View controls (2D/3D, labels)

### FloatingPanel
Reusable panel component with:
- Position presets (left, right, top, bottom, center)
- Size presets (sm, md, lg, xl)
- Smooth entry/exit animations
- Glass morphism styling

### StatsOverlay
Real-time statistics display showing:
- Number of personas
- Network connections
- Active focus groups

## Styling System

### Design Tokens
- **Primary**: Blue shades (sky-blue palette)
- **Accent**: Purple shades (fuchsia palette)
- **Background**: Gradient from slate to blue to indigo
- **Glass Effect**: White with 60-80% opacity + backdrop blur

### Custom Animations
- `float` - Gentle vertical movement
- `pulse-slow` - Slow pulsing effect
- `glow` - Opacity fade in/out
- `pulse-ring` - Expanding ring effect

### Utility Classes
- `.floating-panel` - Main panel styling
- `.glass-effect` - Glass morphism
- `.floating-button` - Interactive buttons
- `.node-card` - Graph node cards
- `.stat-card` - Statistics cards
- `.text-gradient` - Gradient text effect

## API Integration

The frontend connects to the backend API at `/api/v1`:

```typescript
// Example: Fetch projects
import { projectsApi } from '@/lib/api';

const { data } = await projectsApi.getAll();
```

### Endpoints Used
- `GET /projects` - List projects
- `POST /projects/{id}/personas/generate` - Generate personas
- `POST /projects/{id}/focus-groups` - Create focus group
- `POST /focus-groups/{id}/run` - Execute simulation
- `POST /focus-groups/{id}/analyze-polarization` - Analyze results

## State Management

Using Zustand for global state:

```typescript
import { useAppStore } from '@/store/appStore';

const {
  selectedProject,
  graphData,
  setActivePanel
} = useAppStore();
```

### Store Structure
- **Selected entities**: project, persona, focus group
- **Data collections**: projects, personas, focus groups
- **UI state**: active panel, loading, errors
- **Graph state**: hovered nodes, selections, layout mode

## Development

### Adding New Panels

1. Create component in `src/components/panels/`
2. Use `FloatingPanel` wrapper
3. Add to `FloatingControls` navigation
4. Connect to store for state management

### Custom Graph Nodes

1. Extend `GraphNode` type in `types/index.ts`
2. Create mesh component in `graph/`
3. Add to `Scene` rendering logic

### Styling

Use Tailwind utility classes:
```tsx
<div className="floating-panel p-4 space-y-2">
  <button className="floating-button">
    Click me
  </button>
</div>
```

## Performance

### Optimization Strategies
- React.memo for expensive components
- useMemo for computed values
- Debounced graph updates
- Virtualization for long lists
- Code splitting with lazy loading

### 3D Performance
- LOD (Level of Detail) for distant nodes
- Frustum culling
- Instanced meshes for similar objects
- Optimized geometry (low-poly spheres)

## Accessibility

- Keyboard navigation support
- ARIA labels on interactive elements
- Focus management in panels
- Screen reader friendly
- High contrast mode compatible

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- WebGL 2.0 required for 3D graphics

## Building for Production

```bash
# Build optimized bundle
npm run build

# Output in dist/
# Serve with any static file server
```

### Environment Variables (Production)
```env
VITE_API_URL=https://api.yourproduction.com/api/v1
VITE_WS_URL=wss://api.yourproduction.com
```

## Troubleshooting

### Graph not rendering
- Check WebGL support in browser
- Verify API returns valid graph data
- Check console for Three.js errors

### Panels not opening
- Verify Zustand store is properly initialized
- Check `activePanel` state updates
- Ensure no conflicting animations

### Slow performance
- Reduce number of graph nodes
- Disable labels for large graphs
- Use 2D mode instead of 3D
- Check for memory leaks in DevTools

## Future Enhancements

- [ ] Real-time collaboration
- [ ] Advanced graph layouts (hierarchical, circular)
- [ ] Export visualizations as images/videos
- [ ] Custom color schemes
- [ ] Touch gestures for mobile
- [ ] VR mode for immersive exploration

## License

MIT