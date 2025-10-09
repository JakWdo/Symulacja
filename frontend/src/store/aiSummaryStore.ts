import { create } from 'zustand';

interface AISummaryState {
  generatingStatuses: Record<string, boolean>;
  setGeneratingStatus: (focusGroupId: string, isGenerating: boolean) => void;
  clearStatus: (focusGroupId: string) => void;
}

export const useAISummaryStore = create<AISummaryState>((set) => ({
  generatingStatuses: {},
  setGeneratingStatus: (focusGroupId, isGenerating) =>
    set((state) => ({
      generatingStatuses: {
        ...state.generatingStatuses,
        [focusGroupId]: isGenerating,
      },
    })),
  clearStatus: (focusGroupId) =>
    set((state) => {
      const next = { ...state.generatingStatuses };
      delete next[focusGroupId];
      return { generatingStatuses: next };
    }),
}));
