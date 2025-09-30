import { create } from 'zustand';
import type { Project, Persona, FocusGroup, GraphData } from '@/types';

interface AppState {
  // Selected entities
  selectedProject: Project | null;
  selectedPersona: Persona | null;
  selectedFocusGroup: FocusGroup | null;

  // Data
  projects: Project[];
  personas: Persona[];
  focusGroups: FocusGroup[];
  graphData: GraphData | null;

  // UI State
  activePanel: 'projects' | 'personas' | 'focus-groups' | 'analysis' | null;
  isLoading: boolean;
  error: string | null;

  // Graph View State
  hoveredNode: string | null;
  selectedNodes: string[];
  graphLayout: '2d' | '3d';
  showLabels: boolean;

  // Actions
  setSelectedProject: (project: Project | null) => void;
  setSelectedPersona: (persona: Persona | null) => void;
  setSelectedFocusGroup: (focusGroup: FocusGroup | null) => void;
  setProjects: (projects: Project[]) => void;
  setPersonas: (personas: Persona[]) => void;
  setFocusGroups: (focusGroups: FocusGroup[]) => void;
  setGraphData: (data: GraphData | null) => void;
  setActivePanel: (panel: AppState['activePanel']) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setHoveredNode: (nodeId: string | null) => void;
  toggleNodeSelection: (nodeId: string) => void;
  clearSelection: () => void;
  setGraphLayout: (layout: '2d' | '3d') => void;
  toggleLabels: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  selectedProject: null,
  selectedPersona: null,
  selectedFocusGroup: null,
  projects: [],
  personas: [],
  focusGroups: [],
  graphData: null,
  activePanel: null,
  isLoading: false,
  error: null,
  hoveredNode: null,
  selectedNodes: [],
  graphLayout: '3d',
  showLabels: true,

  // Actions
  setSelectedProject: (project) => set({ selectedProject: project }),
  setSelectedPersona: (persona) => set({ selectedPersona: persona }),
  setSelectedFocusGroup: (focusGroup) => set({ selectedFocusGroup: focusGroup }),
  setProjects: (projects) => set({ projects }),
  setPersonas: (personas) => set({ personas }),
  setFocusGroups: (focusGroups) => set({ focusGroups }),
  setGraphData: (data) => set({ graphData: data }),
  setActivePanel: (panel) => set({ activePanel: panel }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setHoveredNode: (nodeId) => set({ hoveredNode: nodeId }),
  toggleNodeSelection: (nodeId) =>
    set((state) => ({
      selectedNodes: state.selectedNodes.includes(nodeId)
        ? state.selectedNodes.filter((id) => id !== nodeId)
        : [...state.selectedNodes, nodeId],
    })),
  clearSelection: () => set({ selectedNodes: [], selectedPersona: null }),
  setGraphLayout: (layout) => set({ graphLayout: layout }),
  toggleLabels: () => set((state) => ({ showLabels: !state.showLabels })),
}));