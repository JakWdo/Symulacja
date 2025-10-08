import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { FigmaDashboard } from '@/components/layout/FigmaDashboard';
import { Projects } from '@/components/layout/Projects';
import { ProjectDetail } from '@/components/layout/ProjectDetail';
import { FocusGroups } from '@/components/layout/FocusGroups';
import { FocusGroupBuilder } from '@/components/layout/FocusGroupBuilder';
import { FocusGroupView } from '@/components/layout/FocusGroupView';
import { Personas } from '@/components/layout/Personas';
import { Surveys } from '@/components/layout/Surveys';
import { SurveyBuilder } from '@/components/layout/SurveyBuilder';
import { SurveyResults } from '@/components/layout/SurveyResults';
import { GraphAnalysis } from '@/components/layout/GraphAnalysis';
import { Settings } from '@/components/Settings';
import { ProjectPanel } from '@/components/panels/ProjectPanel';
import { PersonaPanel } from '@/components/panels/PersonaPanel';
import { FocusGroupPanel } from '@/components/panels/FocusGroupPanel';
import { AnalysisPanel } from '@/components/panels/AnalysisPanel';
import { ToastContainer } from '@/components/ui/Toast';
import { useAppStore } from '@/store/appStore';
import { personasApi, focusGroupsApi } from '@/lib/api';
import { useTheme } from '@/hooks/use-theme';
import type { Project, FocusGroup, Survey } from '@/types';

export default function App() {
  // Initialize theme
  useTheme();
  const {
    selectedProject,
    setPersonas,
    setSelectedPersona,
  } = useAppStore();

  const [currentView, setCurrentView] = useState('dashboard');
  const [viewProject, setViewProject] = useState<Project | null>(null);
  const [viewFocusGroup, setViewFocusGroup] = useState<FocusGroup | null>(null);
  const [viewSurvey, setViewSurvey] = useState<Survey | null>(null);

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

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <FigmaDashboard
            onNavigate={setCurrentView}
            onSelectProject={(project) => {
              setViewProject(project);
              setCurrentView('project-detail');
            }}
          />
        );
      case 'projects':
        return (
          <Projects
            onSelectProject={(project) => {
              setViewProject(project);
              setCurrentView('project-detail');
            }}
          />
        );
      case 'project-detail':
        return viewProject ? (
          <ProjectDetail
            project={viewProject}
            onBack={() => setCurrentView('projects')}
            onNavigate={setCurrentView}
            onSelectFocusGroup={(focusGroup) => {
              setViewFocusGroup(focusGroup);
              setCurrentView('focus-group-detail');
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No project selected</p>
          </div>
        );
      case 'focus-groups':
        return (
          <FocusGroups
            onCreateFocusGroup={() => setCurrentView('focus-group-builder')}
            onSelectFocusGroup={(focusGroup) => {
              setViewFocusGroup(focusGroup);
              setCurrentView('focus-group-detail');
            }}
            showCreateDialog={false}
            onCreateDialogChange={() => {}}
          />
        );
      case 'focus-group-builder':
        return (
          <FocusGroupBuilder
            onBack={() => setCurrentView('focus-groups')}
            onSave={async (focusGroupData) => {
              try {
                if (!selectedProject) return;

                // Konwertuj dane z buildera do formatu API
                const payload = {
                  name: focusGroupData.title,
                  description: focusGroupData.description || null,
                  persona_ids: [], // Builder nie wybiera person - musimy to obsłużyć w FocusGroupView
                  questions: focusGroupData.researchQuestions || [],
                  mode: 'normal' as const,
                  target_participants: focusGroupData.targetParticipants || 10,
                };

                const createdFocusGroup = await focusGroupsApi.create(selectedProject.id, payload);

                setViewFocusGroup(createdFocusGroup);
                setCurrentView('focus-group-detail');
                return createdFocusGroup;
              } catch (error) {
                console.error('Failed to create focus group:', error);
                // TODO: Dodać toast notification o błędzie
                throw error;
              }
            }}
          />
        );
      case 'focus-group-detail':
        return viewFocusGroup ? (
          <FocusGroupView
            focusGroup={viewFocusGroup}
            onBack={() => setCurrentView('focus-groups')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No focus group selected</p>
          </div>
        );
      case 'personas':
        return <Personas />;
      case 'graph-analysis':
        return <GraphAnalysis />;
      case 'surveys':
        return (
          <Surveys
            onCreateSurvey={() => setCurrentView('survey-builder')}
            onSelectSurvey={(survey) => {
              setViewSurvey(survey);
              setCurrentView('survey-results');
            }}
          />
        );
      case 'survey-builder':
        return (
          <SurveyBuilder
            onBack={() => setCurrentView('surveys')}
            onSave={() => setCurrentView('surveys')}
          />
        );
      case 'survey-results':
        return viewSurvey ? (
          <SurveyResults
            survey={viewSurvey}
            onBack={() => setCurrentView('surveys')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No survey selected</p>
          </div>
        );
      case 'settings':
        return (
          <div className="h-full overflow-y-auto p-6">
            <Settings />
          </div>
        );
      default:
        return <FigmaDashboard onNavigate={setCurrentView} />;
    }
  };

  return (
    <div className="h-screen bg-background text-foreground">
      <SidebarProvider className="h-full">
        <div className="flex w-full h-full min-h-0">
          <AppSidebar currentView={currentView} onNavigate={setCurrentView} />
          <main className="flex flex-1 min-h-0 bg-[rgba(232,233,236,0.3)] overflow-hidden">
            <div className="flex-1 min-h-0 h-full">
              {renderContent()}
            </div>
          </main>
        </div>
      </SidebarProvider>

      {/* Preserve existing panels for workflows */}
      <ToastContainer />
      <ProjectPanel />
      <PersonaPanel />
      <FocusGroupPanel />
      <AnalysisPanel />
    </div>
  );
}
