import { create } from 'zustand';
import type { Project, Persona, FocusGroup, GraphData, GraphQueryResponse } from '@/types';
import {
  type PanelKey,
  type GraphLayout,
  DEFAULT_PANEL_POSITIONS,
  DEFAULT_TRIGGER_POSITIONS,
  GRAPH_LAYOUTS
} from '@/constants/ui';

// Re-export for backward compatibility
export type { PanelKey };

type Position = {
  x: number;
  y: number;
};

interface AppState {
  // Selected entities (UI state only - data comes from TanStack Query)
  selectedProject: Project | null;
  selectedPersona: Persona | null;
  selectedFocusGroup: FocusGroup | null;

  // Graph data (not duplicated by TanStack Query)
  graphData: GraphData | null;
  graphAsk: GraphAskState;

  // UI State
  activePanel: PanelKey | null;
  isLoading: boolean;
  error: string | null;
  panelPositions: Record<PanelKey, Position>;
  triggerPositions: Record<PanelKey, Position>;
  shouldOpenProjectCreation: boolean;

  // Graph View State
  hoveredNode: string | null;
  selectedNodes: string[];
  graphLayout: GraphLayout;
  showLabels: boolean;

  // Actions
  setSelectedProject: (project: Project | null) => void;
  setSelectedPersona: (persona: Persona | null) => void;
  setSelectedFocusGroup: (focusGroup: FocusGroup | null) => void;
  setGraphData: (data: GraphData | null) => void;
  setActivePanel: (panel: AppState['activePanel']) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setHoveredNode: (nodeId: string | null) => void;
  toggleNodeSelection: (nodeId: string) => void;
  clearSelection: () => void;
  setGraphLayout: (layout: '2d' | '3d') => void;
  toggleLabels: () => void;
  setPanelPosition: (panel: PanelKey, position: Position) => void;
  setTriggerPosition: (panel: PanelKey, position: Position) => void;
  setGraphAskQuestion: (question: string) => void;
  setGraphAskResult: (result: GraphQueryResponse | null) => void;
  setGraphAskStatus: (status: GraphAskState['status'], error?: string | null) => void;
  setGraphAskFocusGroup: (focusGroupId: string | null) => void;
  resetGraphAsk: (focusGroupId?: string | null) => void;
  triggerProjectCreation: () => void;
  clearProjectCreationTrigger: () => void;
}

interface GraphAskState {
  focusGroupId: string | null;
  question: string;
  status: 'idle' | 'loading' | 'success' | 'error';
  result: GraphQueryResponse | null;
  error: string | null;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  selectedProject: null,
  selectedPersona: null,
  selectedFocusGroup: null,
  graphData: null,
  graphAsk: {
    focusGroupId: null,
    question: '',
    status: 'idle',
    result: null,
    error: null,
  },
  activePanel: null,
  isLoading: false,
  error: null,
  shouldOpenProjectCreation: false,
  hoveredNode: null,
  selectedNodes: [],
  graphLayout: GRAPH_LAYOUTS.THREE_D,
  showLabels: true,
  panelPositions: DEFAULT_PANEL_POSITIONS as Record<PanelKey, Position>,
  triggerPositions: DEFAULT_TRIGGER_POSITIONS as Record<PanelKey, Position>,

  // Actions
  setSelectedProject: (project) => set({ selectedProject: project }),
  setSelectedPersona: (persona) => set({ selectedPersona: persona }),
  setSelectedFocusGroup: (focusGroup) => set({ selectedFocusGroup: focusGroup }),
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
  setPanelPosition: (panel, position) =>
    set((state) => ({
      panelPositions: { ...state.panelPositions, [panel]: position },
    })),
  setTriggerPosition: (panel, position) =>
    set((state) => ({
      triggerPositions: { ...state.triggerPositions, [panel]: position },
    })),
  setGraphAskQuestion: (question) =>
    set((state) => ({
      graphAsk: {
        ...state.graphAsk,
        question,
      },
    })),
  setGraphAskResult: (result) =>
    set((state) => ({
      graphAsk: {
        ...state.graphAsk,
        result,
      },
    })),
  setGraphAskStatus: (status, error = null) =>
    set((state) => ({
      graphAsk: {
        ...state.graphAsk,
        status,
        error,
      },
    })),
  setGraphAskFocusGroup: (focusGroupId) =>
    set((state) => ({
      graphAsk: {
        ...state.graphAsk,
        focusGroupId,
      },
    })),
  resetGraphAsk: (focusGroupId = null) =>
    set(() => ({
      graphAsk: {
        focusGroupId,
        question: '',
        status: 'idle',
        result: null,
        error: null,
      },
    })),
  triggerProjectCreation: () => set({ shouldOpenProjectCreation: true }),
  clearProjectCreationTrigger: () => set({ shouldOpenProjectCreation: false }),
}));
