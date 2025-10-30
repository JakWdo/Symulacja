import { create } from 'zustand';
import type { Project, Persona, FocusGroup, GraphData, GraphQueryResponse } from '@/types';

export type PanelKey = 'projects' | 'personas' | 'focus-groups' | 'analysis' | 'rag';

type Position = {
  x: number;
  y: number;
};

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
  pendingSummaries: Record<string, boolean>;
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
  setPanelPosition: (panel: PanelKey, position: Position) => void;
  setTriggerPosition: (panel: PanelKey, position: Position) => void;
  setSummaryPending: (focusGroupId: string, pending: boolean) => void;
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
  projects: [],
  personas: [],
  focusGroups: [],
  graphData: null,
  pendingSummaries: {},
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
  graphLayout: '3d',
  showLabels: true,
  panelPositions: {
    projects: { x: 80, y: 140 },
    personas: { x: 440, y: 160 },
    'focus-groups': { x: 820, y: 180 },
    analysis: { x: 1200, y: 160 },
    rag: { x: 1260, y: 420 },
  },
  triggerPositions: {
    projects: { x: 40, y: 200 },
    personas: { x: 40, y: 320 },
    'focus-groups': { x: 40, y: 440 },
    analysis: { x: 40, y: 560 },
    rag: { x: 40, y: 680 },
  },

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
  setPanelPosition: (panel, position) =>
    set((state) => ({
      panelPositions: { ...state.panelPositions, [panel]: position },
    })),
  setTriggerPosition: (panel, position) =>
    set((state) => ({
      triggerPositions: { ...state.triggerPositions, [panel]: position },
    })),
  setSummaryPending: (focusGroupId, pending) =>
    set((state) => {
      const currentlyPending = !!state.pendingSummaries[focusGroupId];
      if (pending === currentlyPending) {
        return {};
      }

      if (pending) {
        return {
          pendingSummaries: { ...state.pendingSummaries, [focusGroupId]: true },
        };
      }

      const rest = { ...state.pendingSummaries };
      delete rest[focusGroupId];
      return { pendingSummaries: rest };
    }),
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
