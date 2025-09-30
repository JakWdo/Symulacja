import { useEffect } from 'react';
import { KnowledgeGraph3D } from '@/components/graph/KnowledgeGraph3D';
import { FloatingControls } from '@/components/layout/FloatingControls';
import { ProjectPanel } from '@/components/panels/ProjectPanel';
import { PersonaPanel } from '@/components/panels/PersonaPanel';
import { FocusGroupPanel } from '@/components/panels/FocusGroupPanel';
import { AnalysisPanel } from '@/components/panels/AnalysisPanel';
import { StatsOverlay } from '@/components/layout/StatsOverlay';
import { useAppStore } from '@/store/appStore';
import { useGraphData } from '@/hooks/useGraphData';

export default function App() {
  const { selectedProject, personas, graphData, setGraphData } = useAppStore();

  // Generate graph data from personas
  const generatedGraphData = useGraphData(personas);

  // Update graph data when generated
  useEffect(() => {
    if (generatedGraphData) {
      setGraphData(generatedGraphData);
    }
  }, [generatedGraphData, setGraphData]);

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Background Graph */}
      {graphData ? (
        <KnowledgeGraph3D />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center space-y-4 px-4">
            <div className="text-6xl mb-4 animate-float">🧠</div>
            <h2 className="text-3xl font-bold text-gradient">
              Market Research Platform
            </h2>
            <p className="text-slate-600 max-w-md mx-auto">
              Behavioral analytics and persona simulation with immersive 3D visualization
            </p>
            <div className="flex gap-3 justify-center mt-6">
              <div className="px-4 py-2 rounded-lg bg-white/60 backdrop-blur-md text-sm text-slate-700">
                👈 Open Projects panel
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating UI Elements */}
      <FloatingControls />
      <StatsOverlay />

      {/* Panels */}
      <ProjectPanel />
      <PersonaPanel />
      <FocusGroupPanel />
      <AnalysisPanel />

      {/* Project Info Badge */}
      {selectedProject && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-40">
          <div className="floating-panel px-6 py-3 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <h1 className="text-lg font-semibold text-slate-900">
              {selectedProject.name}
            </h1>
            {selectedProject.is_statistically_valid && (
              <span className="text-xs px-2 py-1 rounded-md bg-green-100 text-green-700 font-medium">
                ✓ Valid
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}