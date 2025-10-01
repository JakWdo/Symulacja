import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FloatingControls } from '@/components/layout/FloatingControls';
import { ImprovedDashboard } from '@/components/layout/ImprovedDashboard';
import { ProjectPanel } from '@/components/panels/ProjectPanel';
import { PersonaPanel } from '@/components/panels/PersonaPanel';
import { FocusGroupPanel } from '@/components/panels/FocusGroupPanel';
import { AnalysisPanel } from '@/components/panels/AnalysisPanel';
import { ToastContainer } from '@/components/ui/Toast';
import { useAppStore } from '@/store/appStore';
import { personasApi } from '@/lib/api';

export default function App() {
  const {
    selectedProject,
    setPersonas,
    setSelectedPersona,
  } = useAppStore();

  // Fetch personas for selected project
  useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      const data = await personasApi.getByProject(selectedProject.id);
      setPersonas(data);
      return data;
    },
    enabled: !!selectedProject,
  });

  // Sync fetched personas with the global store
  useEffect(() => {
    if (!selectedProject) {
      setPersonas([]);
      setSelectedPersona(null);
    }
  }, [selectedProject, setPersonas, setSelectedPersona]);

  return (
    <div className="relative w-full h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-white to-slate-100">
      {/* Main Dashboard */}
      <ImprovedDashboard />

      {/* Floating UI Elements */}
      <FloatingControls />
      <ToastContainer />

      {/* Panels */}
      <ProjectPanel />
      <PersonaPanel />
      <FocusGroupPanel />
      <AnalysisPanel />
    </div>
  );
}
